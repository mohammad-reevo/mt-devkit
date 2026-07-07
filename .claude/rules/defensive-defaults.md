# Defensive Defaults

## When to Apply
Before writing `try/except`, `?? fallback`, `or default`, `getattr(..., default)`, or any record-skipping `continue` / ambiguous `return []` in a pipeline.

## The Rule
A `try/except` (or `if … : continue`) that substitutes a fallback value and continues is forbidden — even with a metric, log, or alert. Two allowed exits only: (1) re-raise as a typed exception the caller acts on; (2) surface the failure in a return-value field that the caller actively presents to the user (UI, DB row, response body). Logs and fire-and-forget metrics do not count — nobody reads them. Same rule applies to `for` loops: every record that enters must either appear in the output or be explicitly reported back to the caller.

## Inline Comment Requirement
Every surviving `except` and every record-skipping `continue` MUST carry an inline comment: `# Legit business flow: <business case>, not <error path>` naming why this is normal flow, not error handling. No honest comment ⇒ delete the catch. Code review should reject any `except` whose comment doesn't answer: *what business case is this, and why is it normal flow rather than an error?*

## The Three-Question Test
1. Can this actually fail? (If the input is upstream-validated by Pydantic / type checker / prior guard — delete the catch, it's dead code lying about the contract.)
2. Which of the two legitimate exits will I take? (Re-raise typed, OR surface in return value. Anything else: don't catch.)
3. Does my exit actually reach the caller? (UI table, DB audit row, response body — not logs, not metrics.)

## ✅ Allowed: re-raise as a typed exception
```python
try:
    mode = SyncMode(user_input)
except ValueError as e:
    # Legit business flow: invalid user input is a normal client error,
    # not a server failure. The HTTP layer maps this to a 422 the user sees.
    raise InvalidArgumentError(f"Invalid sync mode: {user_input}") from e
```

## ✅ Allowed: surface the failure in a return-value field
```python
@dataclass(frozen=True)
class SyncResult:
    synced: list[Record]
    skipped_unparseable: list[str]  # IDs shown in the "Sync Errors" UI

def sync_records(records: list[Raw]) -> SyncResult:
    synced, skipped_unparseable = [], []
    for raw in records:
        try:
            synced.append(transform(raw))
        except UnparseableRecordError:
            # Legit business flow: the sync contract returns skipped IDs in
            # SyncResult.skipped_unparseable; the user reviews them in the
            # Sync Errors UI and decides whether to fix the source data.
            skipped_unparseable.append(raw["Id"])
    return SyncResult(synced=synced, skipped_unparseable=skipped_unparseable)
```

## ❌ Forbidden: swallow with substitute (any form)
```python
# ❌ Even with metric+alert — caller still computes downstream on a fake date
try:
    updated_at = datetime.fromisoformat(raw_ts)
except ValueError:
    metrics.increment("sf.timestamp.malformed")
    updated_at = _EPOCH
```
If the caller can't keep going without `updated_at`, raise. If the contract reports per-record failures, surface the record in `skipped_unparseable`. The metric pages someone off-stream while the caller still computes on incomplete data.

## ❌ Forbidden: silent skip in loops
```python
# ❌ Record vanishes — caller sees "success" with fewer records
if header is None:
    continue
```
Either raise (the caller decides) or include the failed record in a return-value field the caller presents.
## Two Legitimate Silent-Skip Cases
```python
# ✅ Business-rule filtering — intentional exclusion by configuration
for mapping in mappings:
    if not mapping.sync_enabled:
        # Legit business flow: org-level setting disables this object type;
        # not data loss, this is the configured exclusion.
        continue
    sync(mapping)

# ✅ Empty input → empty output — there was no data to lose
def transform(records: list[Raw]) -> list[Out]:
    if not records:
        # Legit business flow: empty input legitimately produces empty output;
        # no record is being dropped because no record was ever in scope.
        return []
    ...
```
