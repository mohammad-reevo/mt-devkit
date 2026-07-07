# TypeScript Style

When writing TypeScript components/hooks in `frontend-monorepo/`.

## Function Arguments — Named Object for >1 Parameter

Always use a named object parameter instead of positional arguments when a function has more than 1 parameter.

```tsx
// ✅ Named object parameter
function useBulkArchiveSelection({
  selectedCount,
  nonEditableItems,
  entityType,
}: {
  selectedCount: number;
  nonEditableItems: NonEditableItem[];
  entityType: BulkEditEntityType;
}): Result {
  // ...
}

// ✅ Extract interface when type is reused or complex
interface UseBulkArchiveSelectionParams {
  selectedCount: number;
  nonEditableItems: NonEditableItem[];
  entityType: BulkEditEntityType;
}

function useBulkArchiveSelection({
  selectedCount,
  nonEditableItems,
  entityType,
}: UseBulkArchiveSelectionParams): Result {
  // ...
}

// ✅ Single parameter — positional is fine
function getLabel(entityType: string): string {
  // ...
}

// ❌ Positional args — unclear at call sites, fragile ordering
function useBulkArchiveSelection(
  selectedCount: number,
  nonEditableItems: NonEditableItem[],
  entityType: BulkEditEntityType,
): Result {
  // ...
}

// ❌ Call site is unreadable
useBulkArchiveSelection(5, items, 'contact');

// ✅ Call site is self-documenting
useBulkArchiveSelection({ selectedCount: 5, nonEditableItems: items, entityType: 'contact' });
```
## Optional Callbacks — Don't Mark Optional When Always Passed

Optional means "genuinely unused in some call sites" — not "just in case." If a callback is always provided, make it required.

When optional IS correct: component is reusable and some consumers don't need the callback, or hook serves multiple call sites, some without the callback.

```tsx
// ❌ Optional but always passed — misleading contract
interface Props {
  onSuccess?: () => void;
}
// Every caller: <Component onSuccess={() => doStuff()} />

// ❌ Defensive call for no reason
onSuccess?.();

// ✅ Required — matches actual usage
interface Props {
  onSuccess: () => void;
}
onSuccess();
```

## Graceful Degradation in Non-Critical Paths

In non-critical paths (analytics, logging, toasts, background side effects, void functions), use `clientLogger.error(...)` instead of `throw new Error(...)`. A missed tracking event is fine; a runtime exception that kills the page is not.

```tsx
// ✅ Logs and continues
default:
  mode satisfies never;
  clientLogger.error('Unhandled job mode', { mode });

// ❌ Crashes the app over a non-critical miss
default:
  mode satisfies never;
  throw new Error(`Unhandled job mode: ${mode}`);
```

Throwing IS correct in functions that return values, core business logic, and invariants in critical paths.
