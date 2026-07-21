# Grading — 🟢 / 🟡 / 🔴 discipline

## The colors

- **🟢 — consistently meeting.** Clear, cited evidence that the user meets this bullet as a matter of course
  — not once, not as a co-passenger.
- **🟡 — partial / co-driver.** Real evidence, but the user is one of several drivers, or the bar is only
  partly cleared (e.g. led the surface but not the whole domain; built the feature but the scale/latency
  proof point never shipped).
- **🔴 — little or no evidence.** Keep these honest. A real 🔴 with an improvement path is more credible than
  a manufactured 🟡, and it shows you read the bar accurately.

## The Example Behaviors are the interpretive key

Rubric bullets are often ambiguous on their own; the **Example Behaviors define what they actually mean.**
Read them before grading any ambiguous bullet.

- Worked example: "scalability" read alone looks like "handles complexity." But the Example Behaviors were
  all **data/traffic scale** — "cut P90 500→50ms," "load-tested 10×," "virtualized a list 4s→400ms." That
  flips a self-assigned 🟢 (for handling a complex feature) to 🟡 (no proven data-scale/perf work). The
  examples are almost all **metrics** — the rubric rewards quantified, at-scale impact.
- If the Example Behaviors are metric-heavy and the user has no metric to point at, that bullet is at most
  🟡 until a real number exists.

## Recurring judgment calls

- **Co-driver vs owner.** In a co-owned effort the honest grade is 🟡 for "drives X," unless the user was
  unambiguously the driver. Don't inflate on assertion.
- **DRI-of-surface vs whole-domain.** "Authority for the domain" in a co-owned domain → 🟡 or a reworded
  🟢 scoped to the user's surfaces. Scoping down is more credible, not less.
- **Shipped vs planned.** A bullet resting on unshipped work (ticket in Todo, PR not merged) is not 🟢.
  Grade what merged.
- **Level vs level+1.** Grade the current level first, then level+1 as the promotion case. A bullet can be
  🟢 at the current level and 🟡 at level+1 — that's the expected shape of a real promotion case, not a
  failure.

## Confirm-or-kill before you finalize a 🟢

For each of the strongest 🟢 claims, run one adversarial pass that **tries to disprove it** — check the
PR author, the ticket state, whether the link shows the user's own work, whether a claimed metric is the
user's or the team's. A 🟢 that survives a genuine attempt to kill it is a 🟢 you can defend to a TL. This
is where unshipped work and mis-attributed PRs die (see `honesty-traps.md`).

## Every colored bullet must cite

No uncited grades. Each 🟢/🟡 carries at least one: a **PR#**, an **authorship-verified Notion doc**, or an
**attested action + named voucher**. If you can't cite it, it's 🔴 or it's an attestation the user must
stand behind by name.
