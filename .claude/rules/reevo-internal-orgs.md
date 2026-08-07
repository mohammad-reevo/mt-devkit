# Reevo internal orgs — and why "a reevo.ai user" never proves one

## When to Apply
Any time an analysis segments, counts, or attributes activity **by organization** — PostHog
queries (`properties.organizationId`), Snowflake `ORG_<uuid>` schemas, adoption/usage numbers,
"how many customers do X" questions. The failure this prevents: reporting internal dogfooding or
Reevo staff activity as customer usage.

## The internal orgs

| Organization | ID | What it is |
|---|---|---|
| `Reevo.ai - GTM` | `4d29f892-7e25-4efa-ad0b-f348bd0fc0fc` | Reevo's own go-to-market workspace |
| `Reevo.ai` | `b3c5bc5d-1eae-4586-b9bd-db8486e6b689` | Reevo's EPD (engineering/product/design) workspace |
| `zvtest org` | `a288b04b-7b77-4499-b907-6aa1764c92d1` | Test org |

These are **not customers**. Exclude them from adoption, usage, and customer-count figures, or
report them as a separate line — never fold them into a headline customer number.

This list is not a whitelist of "everything internal" — absence from it is not proof an org is a
real customer. Other internal/seed orgs exist. Verify before asserting an unfamiliar org is a
customer.

## `reevo.ai` in the user list means nothing

**Do not use the email domain as an internal/customer discriminator.** Reevo staff are members of
**100+ customer orgs** for support and onboarding, so `has(domains, 'reevo.ai')` matches most of
the customer base. A rule built on the domain misclassifies nearly every real customer as
internal.

Identify an org by its **ID** (table above) or by its name in `groups`, not by who is in it.

## Impersonator accounts are Reevo staff, not the customer

Accounts matching **`*+impersonator@reevo.ai`** (e.g. `kelly+impersonator@reevo.ai`,
`yuxiao+impersonator@reevo.ai`) are Reevo staff operating **inside a customer org**. The
`organizationId` on those events is the customer's, but the action was not taken by the customer.

When answering "did customers use X", activity from an impersonator account is **not** customer
usage. Split it out or exclude it, and say which you did.

**`is_impersonator_session` does not reliably flag this** — it has been observed `False` on events
fired by `+impersonator@` accounts. Match the email pattern; don't trust the boolean.

## Query notes that cost time to rediscover

- Org names live at **`groups` index 1**, not 0. `SELECT ... FROM groups WHERE index = 0` returns
  nothing, silently — an empty result reads as "org not found" when the index is simply wrong.
- Not every org has a `groups` row (no `$groupidentify` was ever sent), so a name lookup can come
  back empty for a perfectly real org. Fall back to user email domains for identification.
- `execute-sql` does **not** apply the project's test-account filtering (only the `query-*` tools
  do, via `filterTestAccounts`). Raw SQL includes internal orgs unless you exclude them yourself.

```sql
-- Exclude internal orgs and impersonator activity
WHERE properties.organizationId NOT IN (
        '4d29f892-7e25-4efa-ad0b-f348bd0fc0fc',  -- Reevo.ai - GTM
        'b3c5bc5d-1eae-4586-b9bd-db8486e6b689',  -- Reevo.ai (EPD)
        'a288b04b-7b77-4499-b907-6aa1764c92d1'   -- zvtest org
      )
  AND person.properties.email NOT LIKE '%+impersonator@reevo.ai'
```

## Why
A usage question answered without these two filters flips its own conclusion. A real case: the AI
Data Transform node looked like it had adoption across five orgs — two were the internal
workspaces above, one was `zvtest org`, and the remaining two were customer orgs where the only
add came from a `+impersonator@reevo.ai` account. Actual customer-initiated usage was zero. The
naive number was off by the entire answer.

This applies across all sessions working in this workspace.
