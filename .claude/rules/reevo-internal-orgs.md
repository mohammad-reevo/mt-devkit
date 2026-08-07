# Reevo internal orgs

## When to Apply
Any analysis that segments or counts activity **by organization** — PostHog
`properties.organizationId`, Snowflake `ORG_<uuid>` schemas, adoption/usage numbers, "how many
customers do X".

## The internal orgs

| Organization | ID |
|---|---|
| `Reevo.ai - GTM` | `4d29f892-7e25-4efa-ad0b-f348bd0fc0fc` |
| `Reevo.ai` (EPD) | `b3c5bc5d-1eae-4586-b9bd-db8486e6b689` |
| `zvtest org` | `a288b04b-7b77-4499-b907-6aa1764c92d1` |

Not customers — exclude them from customer figures, or report them on a separate line. The list
isn't exhaustive; absence from it doesn't prove an org is a customer.

## An internal person doesn't make the org internal

`reevo.ai` users are Reevo staff. But they are members of **100+ customer orgs** for support and
onboarding, so finding one in an org says nothing about whether the *org* is ours. Identify an
org by its ID — never by who is in it.

Same at the account level: **`*+impersonator@reevo.ai`** is staff operating inside a customer's
org. The `organizationId` is the customer's; the action is not theirs, so it isn't customer
usage. `is_impersonator_session` has been observed `False` on these events — match the email
pattern, not the boolean.

```sql
WHERE properties.organizationId NOT IN (
        '4d29f892-7e25-4efa-ad0b-f348bd0fc0fc',  -- Reevo.ai - GTM
        'b3c5bc5d-1eae-4586-b9bd-db8486e6b689',  -- Reevo.ai (EPD)
        'a288b04b-7b77-4499-b907-6aa1764c92d1'   -- zvtest org
      )
  AND person.properties.email NOT LIKE '%+impersonator@reevo.ai'
```

## Gotchas
- Org names live at `groups` **index 1** — index 0 returns empty silently.
- `execute-sql` skips the test-account filtering that the `query-*` tools apply.

This applies across all sessions working in this workspace.
