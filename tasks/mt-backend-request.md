---
name: mt-backend-request
title: Rebuild devkit's backend-request as an mt- skill (authenticated local-backend HTTP)
target: personal-claude
created: 2026-07-07
source: Wave 2a devkit skills sweep (my-devkit-design.md)
---

## Problem
No personal equivalent of devkit's `backend-request` skill — authenticated HTTP
to the local backend (localhost:8000) with JWT/auth handled, used instead of raw
`curl`. Worth having (it backs mt-verify / api smoke testing) but not needed until
I actually reach for it.

## Why it matters
mt-verify and any local API poking currently have no sanctioned auth'd-HTTP path.
devkit's `curl.md` rule points at devkit's `backend-request` skill — a dependency
we're moving off. A thin `mt-backend-request` closes that gap.

## Fix ideas
- Rebuild self-contained under `~/.claude/skills/mt-backend-request/` — check
  whether the auth/JWT handling is devkit-specific (reimplement) or wraps a
  backend script/token I can point at (thin pointer). See the Wave 2a note on
  thin-pointer-vs-reimplement.
- Decide at build time whether it also needs a matching personal `curl`-style rule.

## Links
- [[my-devkit-design]] Wave 2a sweep — deferred (implement when I first need it).
