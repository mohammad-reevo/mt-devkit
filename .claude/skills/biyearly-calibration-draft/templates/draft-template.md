# Draft Output — the submittable format

Output in the **rubric's own submittable structure**, not a bespoke template — so the draft lifts directly
into the user's real calibration doc.

## Per-bullet format

For every rubric bullet (at the current level, then level+1):

```
- [🟢|🟡|🔴] <verbatim rubric bullet text>
	- <first-person evidence sub-bullet> (<verified link>)
	- <another first-person evidence sub-bullet> (<verified link>)
Reasoning: <context + honesty caveats FOR THE USER — why this color, what the ceiling is, what to watch,
what rests on attestation>
```

Rules:
- **Verbatim bullet text** — copy the rubric's wording exactly; don't paraphrase the bar.
- **First-person evidence** — write sub-bullets as the user ("I drove…", "I built…") so they're liftable.
- **Every colored bullet cites** — a PR#, an authorship-verified Notion doc, or an attested action + named
  voucher. No uncited grades.
- **Add vouchers to load-bearing claims** — "(verify: Kai / Tan / PM)", "(TL: X)" — so the user knows what
  rests on someone's word.
- **`Reasoning:` is for the user, not the TL** — this is where the honesty caveats live: why not a 🟢, what's
  the proven-at-scale gap, which trap this narrowly avoids. The user decides what survives into the final.

## The three output docs

Ask the user up front: **Notion** (you create/collect the page links) or **one local markdown file**. Either
way, produce:

1. **Calibration Draft** — the graded per-bullet answers above. The submittable artifact.
2. **Evidence Dossier** — the raw cited findings behind every grade (the receipts): PR lists, Linear
   delegation counts, Slack permalinks, Notion authorship checks, the reliability picture, and every
   confirm-or-kill result. This is what lets the user (and the review skill) re-verify without re-sweeping.
3. **(optional) The user's own topic-organization** — if the user wants to group evidence their own way to
   write from, keep a doc for that.

## Local-file naming

If local: write under a path the user controls (e.g. `~/.claude/tmp/calibration-<window>/`), named clearly
(`calibration-draft-<level>-<window>.md`, `evidence-dossier-<window>.md`). **Never commit, post, or share
these** — they're the user's private artifact, handed to their TL by the user.
