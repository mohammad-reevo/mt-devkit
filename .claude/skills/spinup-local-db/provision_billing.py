"""Provision a subscription granting every quota resource for a locally-seeded org.

`make seed-dev-data` creates the org/users/CRM data but NO billing rows at all, and
every quota-gated feature resolves to DENIED_BY_PLAN rather than failing open. This
script fills that gap: it reuses the backend's own idempotent bootstrap helper for the
subscription/plan/cycle skeleton, then grants the plan every resource the backend's
RESOURCE_GROUP_TO_RESOURCES mapping knows about.

Iterating that mapping — rather than a hand-picked list of resources — is deliberate.
It is the backend's own source of truth, so a resource added upstream is granted here
without this script being touched, and the deprecated members of QuotaConsumingResource
(which the mapping omits) stay omitted.

Run it from the salestech-be repo so the backend package + project modules resolve:

    cd <devkit-root> && cd salestech-be && uv run python $HOME/Desktop/code/mt-devkit/.claude/skills/spinup-local-db/provision_billing.py

Defaults to the org created by `make seed-dev-data`
(00000000-0000-4000-a000-000000000001). Pass --org-id / --user-id to override.
If --user-id is omitted, any user associated with the org is used for the
created_by audit columns.

Idempotent, and safe to re-run against an org provisioned by an earlier version of this
script: an existing active subscription is reused rather than replaced, and a resource
the plan already grants is left exactly as it is.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from uuid import UUID, uuid4

# This file lives outside the salestech-be source tree (in the harness .claude/skills), so
# put the current working dir (the salestech-be repo) on the path to import its
# top-level `tests` / `salestech_be` packages.
sys.path.insert(0, os.getcwd())

from salestech_be.core.quota.type.usages_v2 import (
    PERPETUAL_TYPE_QUOTA_CONSUMING_RESOURCES,
    RESOURCE_GROUP_TO_RESOURCES,
)
from salestech_be.db.dao.quota_policy_repository import QuotaPolicyRepository
from salestech_be.db.dao.user_repository import UserRepository
from salestech_be.db.dbengine.core import DatabaseEngine
from salestech_be.db.models.organization_subscription import (
    OrganizationSubscription,
    OrganizationSubscriptionStatus,
)
from salestech_be.db.models.quota_policy_item import (
    QuotaPolicyItem,
    QuotaPolicyItemUnit,
)
from salestech_be.db.models.subscription_plan_quota_policy_item_association import (
    QuotaRenewType,
    SubscriptionPlanQuotaPolicyItemAssociation,
    SubscriptionPlanQuotaPolicyItemEntityType,
    SubscriptionPlanQuotaPolicyItemType,
)
from salestech_be.db.models.user_organization_association import (
    UserOrganizationAssociation,
)
from salestech_be.settings import settings
from salestech_be.util.time import zoned_utc_now
from tests.smoke.bootstrap import _bootstrap_subscription_with_flow_quota

DEFAULT_ORG_ID = UUID("00000000-0000-4000-a000-000000000001")

# Every association is created unlimited, so access resolution never depends on this
# number (_determine_resource_access short-circuits on unlimited_quota). It is set to
# something large anyway so the billing UI reads sensibly.
_LOCAL_QUANTITY = 1_000_000


async def _resolve_user_id(user_repository: UserRepository, org_id: UUID) -> UUID:
    assocs = await user_repository._find_by_column_values(
        UserOrganizationAssociation, organization_id=org_id
    )
    if not assocs:
        raise SystemExit(
            f"No users associated with org {org_id}. Run `make seed-dev-data` first."
        )
    return assocs[0].user_id


async def _resolve_active_plan_id(
    user_repository: UserRepository, org_id: UUID
) -> UUID:
    """The plan of the org's active subscription — the one to grant resources on."""
    subscriptions: list[
        OrganizationSubscription
    ] = await user_repository._find_by_column_values(
        OrganizationSubscription,
        organization_id=org_id,
        status=OrganizationSubscriptionStatus.ACTIVE,
    )
    if not subscriptions:
        raise SystemExit(
            f"No active subscription for org {org_id} after bootstrap — cannot grant "
            "resources. Check the bootstrap helper's output above."
        )
    return subscriptions[0].subscription_plan_id


async def _grant_all_resources(
    user_repository: UserRepository,
    quota_policy_repository: QuotaPolicyRepository,
    plan_id: UUID,
    user_id: UUID,
) -> tuple[int, int]:
    """Associate every known resource with the plan. Returns (granted, already_present)."""
    existing_assocs: list[
        SubscriptionPlanQuotaPolicyItemAssociation
    ] = await user_repository._find_by_column_values(
        SubscriptionPlanQuotaPolicyItemAssociation, subscription_plan_id=plan_id
    )
    already_associated = {assoc.quota_policy_item_id for assoc in existing_assocs}

    now = zoned_utc_now()
    granted = 0
    skipped = 0

    for resource_group, resources in RESOURCE_GROUP_TO_RESOURCES.items():
        for resource in resources:
            item = await quota_policy_repository.ensure_exists(
                QuotaPolicyItem(
                    id=uuid4(),
                    resource_name=resource,
                    resource_group=resource_group,
                    display_name=resource.value.replace("_", " ").title(),
                    description=f"Local dev grant for {resource.value}",
                    unit=QuotaPolicyItemUnit.QUANTITY,
                    unit_name="units",
                    created_at=now,
                    created_by_user_id=user_id,
                )
            )

            if item.id in already_associated:
                # Legit business flow: the plan already grants this resource — either
                # from the flow-quota bootstrap or an earlier run of this script. The
                # contract is "every resource ends up granted", and it already is, so
                # re-associating would only duplicate the row.
                skipped += 1
                continue

            await user_repository.insert(
                SubscriptionPlanQuotaPolicyItemAssociation(
                    id=uuid4(),
                    subscription_plan_id=plan_id,
                    quota_policy_item_id=item.id,
                    quantity=_LOCAL_QUANTITY,
                    unlimited=True,
                    item_type=SubscriptionPlanQuotaPolicyItemType.PLAN_INCLUDE,
                    entity_type=SubscriptionPlanQuotaPolicyItemEntityType.ORGANIZATION,
                    renew_type=(
                        QuotaRenewType.PERPETUAL
                        if resource in PERPETUAL_TYPE_QUOTA_CONSUMING_RESOURCES
                        else QuotaRenewType.RECURRING
                    ),
                    included_in_plan=True,
                    created_at=now,
                    created_by_user_id=user_id,
                )
            )
            already_associated.add(item.id)
            granted += 1

    return granted, skipped


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision a local subscription granting every quota resource"
    )
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
        plan_id = await _resolve_active_plan_id(user_repository, args.org_id)
        granted, skipped = await _grant_all_resources(
            user_repository=user_repository,
            quota_policy_repository=quota_policy_repository,
            plan_id=plan_id,
            user_id=user_id,
        )

        total = sum(len(rs) for rs in RESOURCE_GROUP_TO_RESOURCES.values())
        print(
            f"OK: plan {plan_id} for org {args.org_id} grants {total} resources "
            f"({granted} added now, {skipped} already present; created_by {user_id})"
        )
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
