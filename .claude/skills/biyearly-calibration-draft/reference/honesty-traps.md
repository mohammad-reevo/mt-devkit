# Honesty Traps — the recurring overstatements to catch

Honesty is a **throughline, not a phase.** These same traps recur constantly while drafting. Run this
checklist continuously — every time you're about to color a bullet 🟢 or write an evidence sub-bullet, ask
whether it trips one of these. A TL who knows the work reads the result; **one overstatement taints the
credibility of every true green.**

Each trap below is: the pattern → how to detect it → how to reframe.

### 1. Someone else's doc claimed as yours
The flagship "PRD" was **PM-authored** (Author + Owner = the PM). → **Detect:** `notion-fetch` and read the
Author/Owner/created_by field before citing authorship. → **Reframe:** cite what's actually yours — "drafted
the scoping doc" (your content inside their roadmap page), not "authored the PRD."

### 2. Unshipped work claimed as done
"Variable Suggestions V3 reduced latency" — the latency ticket **never shipped** (sat in Todo). → **Detect:**
check the ticket/PR **state**, not just its existence. → **Reframe:** drop it, or claim only what merged.

### 3. A teammate's PR claimed as yours
"Built the analytics dashboard" pointed at **a teammate's PR**; the user had contributed + reviewed. →
**Detect:** `gh pr view N --json author`. → **Reframe:** "contributed to / reviewed," not "built."

### 4. Incident command with no incident ownership
Reliability claimed as incident leadership, but **zero Rootly incidents** list the user as responder/owner.
→ **Detect:** search Rootly/Sentry for the user as started/mitigated/resolved. → **Reframe:** reliability
rests on bug-fix turnaround + monitoring hygiene — claim *that*, not incident command.

### 5. Sole authority for a co-owned domain
Claiming the whole domain when it's co-owned. → **Detect:** who else leads projects/authors monitors in the
same domain? → **Reframe:** "authority for my surfaces / DRI of <surface>," not the whole domain. Humility
here **strengthens** credibility.

### 6. Team/product metric as personal impact
"100k+ workflow runs" is a **team/product** number, not the user's personal impact. → **Detect:** would this
number exist without the user? Is it the product's, or theirs? → **Reframe:** surface the user's **own**
numbers — delegation counts, projects genuinely led, features built. Drop the team metric or attribute it as
team achievement.

### 7. Unverified counts
"61 tickets," "5 docs," "several meetings" — round numbers with no source. → **Detect:** can you cite the
exact query/list behind it? Are some of the 61 internal vs. real customers? → **Reframe:** cite the source,
or soften ("dozens of," "multiple") and note what's included.

### 8. Overstated collaboration
"Hosted several meetings" where the evidence is one "let's sync today" message. → **Detect:** does the link
actually show the claimed volume/formality? → **Reframe:** claim exactly what the evidence shows.

### 9. Link doesn't show YOUR work
A permalink that lands on a teammate's "TYTY!" thanks, or on a bot's issue-report, instead of on the user's
own diagnosis/decision. → **Detect:** open the link; is the user's own message the thing it lands on? →
**Reframe:** deep-link the user's own message (with `?thread_ts=` for thread replies).

### 10. Broken / malformed links
`http://CRMF-761` is not a URL (must be `https://linear.app/reevo/issue/CRMF-761`); generic
`app.slack.com/client/.../CHANNEL` deep-links are not message permalinks. → **Detect:** does it resolve to
the specific artifact? → **Reframe:** use the canonical permalink for the specific message/issue.

---

## The stance

When a claim is borderline, **flag it for the user rather than deciding** — surface the nuance ("this PR is
Kyle's; you reviewed it — want to reframe as 'contributed to'?") and let them make the call. The user's
honest filter is the credibility engine; your job is to make the tradeoff visible, not to quietly inflate or
quietly cut.
