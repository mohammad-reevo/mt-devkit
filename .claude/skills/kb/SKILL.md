---
name: kb
description: Read, search, and write the cross-session knowledge base in `knowledge-base/` — `projects/` for where a project stands and what its tickets actually cover, `concepts/` for durable things worth not explaining twice. Owns the index-line discipline that makes the store findable at all, the one-page cap, and the guarantee that `INDEX.md` exists. Every write is explained and approved before anything is drafted, then shown as a diff and approved again. Use to look something up that the index hinted at, to search when no index line fired, to add or revise an entry, or to graduate a finished project's durable residue into concepts. Writing happens at `/done` close-out or on an explicit ask — never offered mid-session, however KB-worthy a deep dive or a deferred task feels at the time. Triggers on "add this to the knowledge base", "put this in the kb", "what do we know about X", "search the kb", "update the project doc", "/kb".
argument-hint: '[search <query> | add | update <entry> | graduate <project>]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool. Design: `spec/knowledge-base-design.md`.

# kb — the knowledge base

You own `knowledge-base/`: the store that carries context across sessions, so a project doesn't
have to be re-explained every time and a settled concept doesn't get re-derived.

Where kb ends: **an entry read, or a proposed change shown as a diff.** You never write without
first saying what you intend to write, then showing what changes — a yes at each point.

## When to offer a write

**Two moments, and no others: `/done` close-out, and Mohammad explicitly asking.** Reading is
always fine; *offering to write* is not.

**"Explicitly" is the load-bearing word.** "I might just save this", "maybe worth writing down",
"this feels KB-worthy" are Mohammad thinking out loud — an observation, or a question about
whether it's worth keeping. Answer the question; don't launch the flow. A write starts on an
instruction ("add this to the KB", "update the project doc"), never on a mention of one. If the
signal reads as ambivalent, it is ambivalent: say in a line what you'd file, ask whether he wants
it, and wait. Reading "might" as "do it" is how the store fills with entries nobody asked for.

Everything else is a read-only session as far as this store is concerned — a deep dive that
turned up something hard-won, a deferred task, a debugging session that finally landed. Don't
offer, don't suggest filing it, don't mention the KB at all. Documenting something while it is
still being discussed is premature: the shape of what was learned is still moving.

The pull is structural, so name it. § What earns an entry is a test of **content**, and a good
deep dive passes it at the exact moment it happens — which is why timing is a separate rule.
Content worth keeping is not the same as a moment to file it, and a finding that genuinely earns
an entry still earns it at `/done`. Nothing is lost by waiting, and the judgment is better once
the work is finished than mid-discussion.

`/done` is the sweep, and it covers **every** session — Mohammad runs it on non-funnel work too,
not just the funnel. So there is no capture gap to close by asking early. For funnel work it also
runs before the scope and plan files are deleted, so that reasoning is already carried there.

## Writing — always through the shell, never Edit/Write

**Use `Edit`/`Write` on the store and it will fail.** The store lives in the primary checkout and
is symlinked into every worktree; three separate guards (Claude Code's session isolation,
`worktree_gate_hook`, the background-isolation guard) resolve that symlink, see the primary
checkout, and refuse. They are right to — a symlink that could be followed into the primary would
make worktree isolation meaningless.

So writes go through Bash — and the gate **denies** an unmarked one outright, because a
confirmation prompt is a no-op in bypass-permissions mode (measured, not assumed). The sequence
is therefore fixed:

1. **Say what's coming, and wait.** One to three sentences in plain language: which file,
   `projects/` vs `concepts/`, and what the entry will cover. **Draft nothing yet.**
2. **Draft it, and show the change** as a fenced ```diff block — `-` old, `+` new.
3. **Get an explicit yes.** Not implied consent from the original request, and not carried over
   from step 1 — that yes was for the idea, this one is for the words.
4. **Then write**, with the marker:

```
MT_KB_WRITE=1 cat > knowledge-base/<path>.md <<'KB_EOF'
<the entry>
KB_EOF
```

**Both gates apply to every write** — a new entry, an `update`, a `graduate` proposal, a one-line
index-line fix, an `updated:` bump. No write is small enough to skip step 1: a sentence costs
nothing, and "which writes are small enough?" is exactly the judgment call that erodes a gate.

**Step 1 is the one doing the real work.** A diff shown at the end catches *bad content*, but by
then the entry exists, and refusing it means throwing away finished work — so the path of least
resistance is to approve. Stating the intent first makes "actually, don't" cheap, which is the
only thing that keeps unwanted entries out of the store. It also stops a discarded draft from
burning context.

`MT_KB_WRITE=1` is the one sanctioned escape. It is not a lock — you are the one adding it — but
it makes an *incidental* write impossible: nothing reaches the store without a deliberate token
sitting in plain sight in the command. **Never add the marker before step 3 has actually
happened.** Doing so converts the one real safeguard on this store into decoration.

Keep to that shape. A write in some other form may slip past the matcher, which defeats the
point of having a gate at all.

## The store

```
knowledge-base/
├── INDEX.md              ← imported by CLAUDE.md; in every session's context
├── projects/<name>.md    ← where a project stands, what its tickets cover
└── concepts/<area>/<topic>.md
```

**The two halves have different lifecycles, and that's the point.** A project doc churns weekly
and is thrown away once the project ships. A concept entry barely changes and is maintained
indefinitely. Keeping them apart is what lets either one's freshness be trusted at a glance —
don't file a concept under `projects/` because it came up during a project.

## Invariants

Check these whenever you touch the store:

- **`INDEX.md` must exist.** `CLAUDE.md` imports it, and the behavior of a missing import target
  is undocumented — the bad case breaks all of `CLAUDE.md`, not just the KB. If it's gone,
  recreate it (header + `## Projects` / `## Concepts`) before anything else and say you did.
- **One line per entry in the index.** Detail lives in the entry. The index stays scannable or
  it stops being read.
- **One page per entry, hard cap.** Past a page, split it. This is what stops the KB drifting
  into codebase documentation — `spec/inline-computed-fields/CONTEXT.md` reached 53 KB and is
  loaded by nothing.

## Modes

### `search <query>`
The fallback for when the index didn't fire. Grep entry bodies (`knowledge-base/`), report which
entries matched and what they say. **If a good entry existed but its index line didn't surface
it, say so — that's an index-line bug, and offer to fix the line.** That feedback loop is how the
index gets good; without it, a silently-missed entry looks identical to a missing one.

### `add`
1. **Decide where it goes** — `projects/` or `concepts/<area>/`. Ask if genuinely ambiguous.
2. **Apply the earns-an-entry test** (§ What earns an entry). If it fails, say why and stop;
   don't file it anyway.
3. **Say what you're about to write, and wait** — gate 1 of § Writing. Nothing below this line
   happens before the yes.
4. **Draft the entry** — frontmatter (`name`, `title`, `kind`, `area`, `updated`), then the
   body, under a page.
5. **Write the index line** — see below. This is the part that decides whether the entry is ever
   found, so spend real thought here, not on the prose.
6. **Show the diff and wait.** The entry and the new index line, both.

### `update <entry>`
Same two gates — what's changing and why, stated before anything is drafted, then diff-and-wait.
Two things to get right: bump `updated`, and **re-read the index line** — an entry that has grown
or changed direction usually needs a different trigger than the one it was filed under.

### `graduate <project>`
Run when a project ships, **before** its project doc is deleted. Read the project doc, pull out
what outlives the project — decisions and why, gotchas, the concept-to-code name mappings — and
propose those as `concepts/` entries. Everything else (status, ticket scope, what's in flight)
dies with the doc, correctly.

Propose them as a list of one-liners first — that list *is* gate 1, and cutting an entry from it
is far cheaper than cutting one from three drafted entries. Each survivor then runs `add` from
step 4.

Without this step, finishing a project deletes exactly the knowledge that was worth keeping.

## Writing an index line

**This is the highest-leverage thing in the skill.** The index is the whole retrieval mechanism:
Claude can't search for an entry it doesn't know exists, but it will open one whose line is
already in context. A line that fails to fire makes the entry invisible.

**Name what will be on screen when the entry becomes relevant** — table names, error strings,
command names, the terms actually in play. Not what the entry is *about*.

```
❌ flow-definition-structure — how a FlowDefinition is shaped
✅ flow_definition / user_flow / flow_run — which table holds what, and why node
   configs look duplicated
```

The test to apply before writing the line: *what am I looking at, in the moment I need this?*
If the answer isn't in the line, the line is wrong.

## What earns an entry

One question: **would this cost real investigation to re-derive, and is it un-greppable?**

- **Yes:** why a thing is shaped the way it is, what the enum values mean, which of three similar
  tables is the live one, what was tried and rejected, what a ticket's scope actually covers.
- **No:** anything a grep answers, anything already in `.claude/rules/` or the memory store, and
  anything that would need editing every time code moves.

**Project progress is an explicit exception to "don't store the derivable."** It *is* derivable
from Linear plus PRs — but only by reading every ticket and every PR, and that still misses what
changed during implementation. A ten-line hand-written doc beats a five-minute derivation. Store
it.

**Staleness is Mohammad's call, not yours.** Some structures genuinely never change and are safe
to document. If something looks like it'll rot, say so once, then defer — do not refuse to file
it, and do not turn this into a debate.

## Guardrails

- **Two gates on every write, and no write is too small for either.** Say what's coming and get a
  yes *before* drafting; then show the diff and get a second yes. This holds for a new entry, a
  one-line index fix, and an `updated:` bump alike.
- **An ambivalent mention is not an instruction.** "I might save this" opens a conversation, not
  a write.
- **Never edit an entry as a side effect** of reading or searching it.
- **Don't file what belongs elsewhere.** A behavioral rule goes in `.claude/rules/`; a small
  durable fact goes in the memory store. The KB is for what neither covers.
- **A bad index line is a bug, and reporting it is part of the job.** Re-deriving something the
  KB already holds is the failure this store exists to prevent — surface it, don't absorb it.
