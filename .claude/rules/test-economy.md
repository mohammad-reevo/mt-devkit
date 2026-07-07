# Test Economy

## When to Apply
When writing tests — unit, integration, or E2E.

## Rule
Write the **fewest tests that cover the most behavior**. Each test must justify its existence by exercising a distinct code path. If removing a test wouldn't reduce confidence, it shouldn't exist.

- **Combine related scenarios** into one test rather than writing a separate test per input. A single test with mixed entity types covers more than individual tests for each type.
- **Boundary cases** (empty input, missing data, zero-length lists) only need a test when the code has an explicit branch handling them. Don't test a no-op path.
- **Use parametrize** (`@pytest.mark.parametrize`, `test.each`) when testing the same logic with different inputs — don't write N copies of the same test.
- **Fallback behavior** (e.g. name → email, default values) deserves a test only when the fallback logic is non-trivial or error-prone.
- **Don't test the framework** — if a field is required by Pydantic/Zod, you don't need a test proving it rejects missing values.

## Anti-Patterns

| Don't | Do instead |
|---|---|
| One test per entity type doing the same thing | One test with mixed types |
| Separate tests for empty input, single input, multiple inputs | One test with representative input; empty only if there's a branch |
| 8 tests for a service with 2 code paths | 2-3 tests that hit both paths |
| Asserting obvious validation the schema already enforces | Test business logic the schema can't express |
