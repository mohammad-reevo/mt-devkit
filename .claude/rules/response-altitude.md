# Response Altitude — Calibrate Detail to What the Reader Needs

## When to Apply
When composing a user-facing reply that **aggregates the output of multiple agents** — a code review across reviewers, a multi-axis audit, a fan-out investigation — or any reply where you are tempted to dump everything you found. Does NOT apply to ordinary conversational answers; those are already at altitude.

## The Core Idea
**How much detail to include is a judgment call you make every time — think about it.** It is part of the work, not an afterthought. Sometimes the reader needs depth right there in the reply; sometimes a one-line verdict is the whole answer. Read the situation and decide. There is no fixed format and no fixed length — there is the right altitude for *this* question, and your job is to find it.

The failure this rule fixes is dumping the entire investigation into the reply — every finding wrapped in `Finding / Severity / Status: ✅ Verified — file:line`, axis-by-axis prose, the bottom line buried at the end. Unreadable. But the opposite failure is just as bad: stripping the reply down to a verdict and shoving everything that justifies it into a file the reader now has to open. **Do not make the reader open a file to learn the essence.** The reply must stand on its own.

## Verification Is Separate From Volume
The reply gets shorter by saying less, never by *checking* less. An agent that verified ten claims against real `file:line` did that work whether or not all ten appear in the message. Calibrating altitude is about what you *show*, not what you *do*. If you ever shorten a reply by skipping a verification step, you have misread this rule — the premise-resolution and data-freshness discipline stays in full force underneath it.

## The Rule
1. **Lead with the bottom line.** Verdict in the first sentence or two: what the answer is, and the one decision it forces. Never end the message with "bottom line" — if it belongs at the bottom, it belonged at the top.

2. **Put the load-bearing detail IN the reply.** A finding is load-bearing if it changes a decision the reader is about to make. Those — with enough "why" to act on — belong in the message itself, not behind a pointer. The reader should be able to act on the reply alone, without opening anything.

3. **Match the volume to the decision.** This is the judgment, stated as a gradient:
   - A quick check or factual question → a line or two. Don't pad it.
   - A real decision with tradeoffs → the verdict plus the handful of things that drive it, each with enough reasoning to act.
   - A sprawling audit → the verdict plus the load-bearing findings inline; trim the rest, don't relocate it onto the reader.

4. **A file is for the genuinely large, genuinely optional tail — and only rarely.** Exhaustive per-finding cards, full `file:line` proof tables, raw per-axis transcripts: if that residue is large AND you judge the reader is unlikely to want it, a scratch file under `tmp/` (e.g. `tmp/{topic}.md`) is fine as *supplementary* material. It is never the home of the answer, and the reply must be complete without it. When in doubt, keep it in the reply — an unread paragraph costs less than a file the reader has to chase.

5. **No finding-card decoration inline.** Don't render `Finding: … / Severity: … / Status: ✅ Verified — file:line` blocks in the message. In the reply a finding is a sentence: what it is and why it matters. The scaffolding is noise.

## What Does Not Change
- Agents dig exactly as deep and verify exactly as much as before — every claim still traces to real code.
- Reviewer agents keep their own compact formats; this rule governs YOUR synthesis of them, not their internals.
- What you DO with findings is a separate axis from how you report them — this rule governs only the reporting.

## Example — same review, three altitudes

The reader asked "is this proposal safe to build?" — a real decision. Right altitude:
```
**Inbound: green on persistence. FE: green to build, but re-sequence.**

Three things must be fixed in the contract before FE lockstep:
- object_type_id has no write path — the wizard can't map custom objects (High)
- enabled flat→nested silently breaks the toggle — currently mis-rated Low
- status-strip premise unresolved — hit the live GET before deleting status

Two docs disagree on the as-is baseline: §C is stale (the fold is already
done), and §5.2/§A4 leave sync_mode with no landing column. Reconcile those
before either doc is treated as the landing spec.
```
Self-sufficient: the reader can decide from this alone. Too low (a wall of ten verified finding-cards with the verdict at the end) and too high (just "green to build — see review.md") are both wrong for this question.

If the reader had only asked "did the persistence check pass?" the right altitude is one line: *"Yes — nothing inbound reads is dropped; every input survives in a reachable table."*

## The Check Before You Send
Two questions: **Can the reader act on this reply alone, without opening a file?** and **Is there a line here that doesn't change any decision?** Add what's missing for the first; cut what fails the second. The goal is the altitude that fits the question — not the longest answer, and not the shortest.
