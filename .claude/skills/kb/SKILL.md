---
name: kb
description: Read, search, and write the cross-session knowledge base in `knowledge-base/` — `projects/` for where a project stands and what its tickets actually cover, `concepts/` for durable things worth not explaining twice. Owns the index-line discipline that makes the store findable at all, the one-page cap, and the guarantee that `INDEX.md` exists. Every write shows a diff and waits for a yes. Use to look something up that the index hinted at, to search when no index line fired, to add or revise an entry, or to graduate a finished project's durable residue into concepts. Triggers on "add this to the knowledge base", "put this in the kb", "what do we know about X", "search the kb", "update the project doc", "/kb".
argument-hint: '[search <query> | add | update <entry> | graduate <project>]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool. Design: `spec/knowledge-base-design.md`.

# kb — the knowledge base

You own `knowledge-base/`: the store that carries context across sessions, so a project doesn't
have to be re-explained every time and a settled concept doesn't get re-derived.

Where kb ends: **an entry read, or a proposed change shown as a diff.** You never write without
showing what changes and getting a yes.

## Writing — always through the shell, never Edit/Write

**Use `Edit`/`Write` on the store and it will fail.** The store lives in the primary checkout and
is symlinked into every worktree; three separate guards (Claude Code's session isolation,
`worktree_gate_hook`, the background-isolation guard) resolve that symlink, see the primary
checkout, and refuse. They are right to — a symlink that could be followed into the primary would
make worktree isolation meaningless.

So writes go through Bash — and the gate **denies** an unmarked one outright, because a
confirmation prompt is a no-op in bypass-permissions mode (measured, not assumed). The sequence
is therefore fixed:

1. **Show the change** as a fenced ```diff block — `-` old, `+` new.
2. **Get an explicit yes.** Not implied consent from the original request.
3. **Then write**, with the marker:

```
MT_KB_WRITE=1 cat > knowledge-base/<path>.md <<'KB_EOF'
<the entry>
KB_EOF
```

`MT_KB_WRITE=1` is the one sanctioned escape. It is not a lock — you are the one adding it — but
it makes an *incidental* write impossible: nothing reaches the store without a deliberate token
sitting in plain sight in the command. **Never add the marker before step 2 has actually
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
2. **Apply the write gate** (below). If it fails, say why and stop; don't file it anyway.
3. **Draft the entry** — frontmatter (`name`, `title`, `kind`, `area`, `updated`), then the
   body, under a page.
4. **Write the index line** — see below. This is the part that decides whether the entry is ever
   found, so spend real thought here, not on the prose.
5. **Show the diff and wait.** The entry and the new index line, both.

### `update <entry>`
Same gate and same diff-and-wait. Two things to get right: bump `updated`, and **re-read the
index line** — an entry that has grown or changed direction usually needs a different trigger
than the one it was filed under.

### `graduate <project>`
Run when a project ships, **before** its project doc is deleted. Read the project doc, pull out
what outlives the project — decisions and why, gotchas, the concept-to-code name mappings — and
propose those as `concepts/` entries. Everything else (status, ticket scope, what's in flight)
dies with the doc, correctly.

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

- **Never write without showing a diff and getting a yes** — not for a new entry, not for a
  one-line index fix, not for a `updated:` bump.
- **Never edit an entry as a side effect** of reading or searching it.
- **Don't file what belongs elsewhere.** A behavioral rule goes in `.claude/rules/`; a small
  durable fact goes in the memory store. The KB is for what neither covers.
- **A bad index line is a bug, and reporting it is part of the job.** Re-deriving something the
  KB already holds is the failure this store exists to prevent — surface it, don't absorb it.
