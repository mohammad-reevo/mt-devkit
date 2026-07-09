# Bash: prefer literal paths over variable expansions

## When to Apply
When issuing a Bash command that references a shell/environment variable
expansion (`$VAR`, `${VAR}`) — most commonly a path built from something like
`$CLAUDE_JOB_DIR`, `$HOME`, or a captured variable — and you know (or can
determine) the value it expands to.

## Rule
Write the **literal expanded value** in the command instead of the variable,
whenever the value is known.

- Prefer `/Users/mohammad/.claude/jobs/<id>/tmp/out.txt` over
  `"$CLAUDE_JOB_DIR/tmp/out.txt"`.
- This applies to redirects, arguments, and any position where a `$VAR` would
  otherwise appear in the command string.
- If the value is genuinely unknown and can't be resolved, using the variable
  is fine — accept the resulting prompt rather than guessing a path.

## Why
Claude Code refuses to auto-approve any Bash command containing a variable
expansion (it flags `simple_expansion`) — the guardrail runs *before* the
`permissions.allow` rules are consulted, so no allowlist entry can silence it.
A command with a literal path is statically analyzable, so it auto-approves
under the already-allowlisted binaries (`git`, `tail`, `wc`, …) and doesn't
prompt. The guardrail is intentional and correct; writing the literal simply
gives the matcher something it can vet.

This is a behavioral preference, not an enforced gate — a `$VAR` will still slip
in occasionally (e.g. a command copied verbatim from a skill's docs); that's
expected, just approve those.
