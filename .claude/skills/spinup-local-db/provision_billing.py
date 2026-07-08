"""Provision a subscription + FLOW_NODE_EXECUTIONS quota for a locally-seeded org.

`make seed-dev-data` creates the org/users/CRM data but NOT a billing subscription
or quota policy items, so running a flow fails the quota gate with
"Feature FLOW_NODE_EXECUTIONS is not available". This script fills that gap by
reusing the backend's own idempotent bootstrap helper.

Run it from the salestech-be repo so the backend package + project modules resolve:

    cd <devkit-root> && cd salestech-be && uv run python $HOME/Desktop/code/mt-devkit/.claude/skills/spinup-local-db/provision_billing.py

Defaults to the org created by `make seed-dev-data`
(00000000-0000-4000-a000-000000000001). Pass --org-id / --user-id to override.
If --user-id is omitted, any user associated with the org is used for the
created_by audit columns. Idempotent: skips if the org already has an active
subscription.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from uuid import UUID

# This file lives outside the salestech-be source tree (in the harness .claude/skills), so
# put the current working dir (the salestech-be repo) on the path to import its
# top-level `tests` / `salestech_be` packages.
sys.path.insert(0, os.getcwd())

from salestech_be.db.dao.quota_policy_repository import QuotaPolicyRepository
from salestech_be.db.dao.user_repository import UserRepository
from salestech_be.db.dbengine.core import DatabaseEngine
from salestech_be.db.models.user_organization_association import (
    UserOrganizationAssociation,
)
from salestech_be.settings import settings
from tests.smoke.bootstrap import _bootstrap_subscription_with_flow_quota

DEFAULT_ORG_ID = UUID("00000000-0000-4000-a000-000000000001")


async def _resolve_user_id(user_repository: UserRepository, org_id: UUID) -> UUID:
    assocs = await user_repository._find_by_column_values(
        UserOrganizationAssociation, organization_id=org_id
    )
    if not assocs:
        raise SystemExit(
            f"No users associated with org {org_id}. Run `make seed-dev-data` first."
        )
    return assocs[0].user_id


async def main() -> None:
    parser = argparse.ArgumentParser(description="Provision local subscription + flow quota")
    parser.add_argument("--org-id", type=UUID, default=DEFAULT_ORG_ID)
    parser.add_argument("--user-id", type=UUID, default=None)
    args = parser.parse_args()

    engine = DatabaseEngine(url=str(settings.db_url), pool_size=5, max_overflow=10)
    try:
        user_repository = UserRepository(engine=engine)
        quota_policy_repository = QuotaPolicyRepository(engine=engine)
        user_id = args.user_id or await _resolve_user_id(user_repository, args.org_id)
        await _bootstrap_subscription_with_flow_quota(
            user_repository=user_repository,
            quota_policy_repository=quota_policy_repository,
            organization_id=args.org_id,
            user_id=user_id,
        )
        print(
            f"OK: subscription + FLOW_NODE_EXECUTIONS quota provisioned for "
            f"org {args.org_id} (created_by {user_id})"
        )
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
