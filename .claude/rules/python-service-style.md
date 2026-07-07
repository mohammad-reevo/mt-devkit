# Python Service Style

## When to Apply
When writing service-layer Python in `salestech-be/`. The **Comments** and **Avoid Polishing** sections apply globally to any code or markdown edits.

## Defensive Defaults & No Silent Data Loss

See `defensive-defaults.md` — both rules live there together.

## Single Source of Defaults

Optional-parameter defaults must be resolved at exactly **one** layer — and only one. The layer choice (view, service, repository) is not prescribed; what matters is that no other layer re-resolves the same default. The anti-pattern is **distributed default resolution**: the same `if x is None: x = DEFAULT` repeated at multiple layers, where the "real" default becomes whichever layer happens to fire last.

A useful guideline (Slatkin, *Effective Python*): `None` belongs in a function's signature only when the function treats `None` as a meaningful value *distinct from any concrete value*. Otherwise, take the value as required at that layer and resolve the default at the layer above.

```python
# ✅ Service resolves the default once; repository takes a required argument.
class SyncConfigService:
    async def upsert(self, *, poll_minutes: int | None = None) -> ConfigDTO:
        poll_minutes = poll_minutes if poll_minutes is not None else _DEFAULT_POLL_MINUTES
        return await self._repo.upsert(poll_minutes=poll_minutes)

class SyncConfigRepository:
    async def upsert(self, *, poll_minutes: int) -> ConfigDTO: ...

# ✅ View resolves the default once; service takes a required argument.
#    Equally valid — Clean Architecture prefers pushing decisions to the boundary.
@router.post(...)
async def upsert(payload: UpsertRequest, svc: SyncConfigService = Depends(...)) -> ConfigDTO:
    poll_minutes = payload.poll_minutes if payload.poll_minutes is not None else _DEFAULT_POLL_MINUTES
    return await svc.upsert(poll_minutes=poll_minutes)

# ❌ Distributed default resolution — both layers re-guess.
class SyncConfigService:
    async def upsert(self, *, poll_minutes: int | None = None) -> ConfigDTO:
        poll_minutes = poll_minutes if poll_minutes is not None else 10  # ← here
        return await self._repo.upsert(poll_minutes=poll_minutes)

class SyncConfigRepository:
    async def upsert(self, *, poll_minutes: int | None = None) -> ConfigDTO:
        poll_minutes = poll_minutes if poll_minutes is not None else 10  # ← AND here — duplicate
        ...
```

## Prefetch and Pass

When shared data (mappings, configs, settings) is needed by multiple downstream calls in a loop, fetch it **once** at the orchestration level and pass it down. Do not fetch the same data inside each called method.

| Don't | Do instead |
|---|---|
| Fetch same data inside each method in a loop (N+1) | Fetch once, pass down |
| Fetch all rows then filter in Python | SQL WHERE clause, or prefetch + group in one pass |
| Two separate queries for the same table to get different groupings | One query, group into both dicts in a single pass |
| Pass raw rows to callers and let each re-group | Prefetch method returns data in the format callers need |

```python
@dataclass(frozen=True)
class SyncContext:
    mappings_by_type: dict[str, list[MappingDTO]]
    type_lookup: dict[RemoteType, LocalType]

async def prefetch_sync_context(self, *, organization_id: UUID) -> SyncContext:
    rows = await self._repository.find_all_by_org(organization_id=organization_id)
    # One pass over rows → both dicts
    ...
```

Local fetch IS correct for guard clauses (existence/permission checks), single-entity gets, and data used by only one method.
## Comments

Applies globally to all code and markdown. Only add comments that explain **why**, not **what**. Never narrate or duplicate what the code says.

```python
# ❌ Couples comment to project context that will rot
"""HubSpot counterpart (HubspotSyncConfigService + hubspot_sync_config)
is out of scope for this design — already shipped by Sa in PR #22305."""

# ✅ If a note about the sibling is needed at all
"""See HubspotSyncConfigService for the HubSpot equivalent."""
```

Do not embed developer names, PR numbers, ticket IDs, "out of scope" notes, or counts of sibling implementations.

## Avoid Polishing

Applies globally to all code and markdown edits. Do not reword, restructure, or "improve" existing text unless asked. The diff should contain **only** the functional change.

Banned edits: rewording for "clarity", reordering bullets/sections, changing heading levels, splitting/merging paragraphs, adding transition sentences.

```markdown
# ❌ Coupled — breaks when you add a 4th class or 9th endpoint
- Service interface (three classes, concrete method signatures)
- API surface — 8 endpoints

# ✅ Resilient — stays correct as the design evolves
- Service interfaces and method signatures
- API surface under `/v1/crm_sync/config/`
```

Don't write descriptions that just restate a self-descriptive name. Before writing a description, ask: **does this tell the reader something the name alone doesn't?** If not, omit it.
