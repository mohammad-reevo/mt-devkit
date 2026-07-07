# Frontend: never hardcode colors

When writing or reviewing any frontend styling (Tailwind classes, `className`,
`style={}`, CSS), use the design system's **semantic color tokens** — never a
raw color value.

- **Banned:** Tailwind palette utilities (`text-violet-500`, `bg-blue-100`,
  `border-red-400`, `text-gray-900`), hex/rgb/hsl literals (`#fff`,
  `rgb(...)`), and any named CSS color.
- **Use instead:** the semantic token for the role — `text-foreground`,
  `text-muted-foreground`, `bg-muted`, `bg-background`, `border-border`,
  `text-destructive`, and for the AI / Ask Reevo mark `text-ai-accent`.
- If no token fits the need, that's a signal to ask which token to use (or
  whether one should be added) — don't reach for a raw color to fill the gap.

## Copying an existing hardcoded color is not a justification

The most common way this slips in: copying a class off a sibling component
that *already* hardcodes a color (e.g. lifting `text-violet-500` from another
button). The sibling being wrong doesn't make it right — use the token, and
ideally flag the sibling. "Matched the existing component" is not an excuse a
reviewer will accept.

## Why

Hardcoded colors break theming/dark-mode, drift from the design system, and
get rejected in review (the Reevo frontend gates them with `pnpm lint:colors`,
and reviewers flag them on sight). Tokens are the contract; raw colors are a bug.

This applies across all repositories and projects.
