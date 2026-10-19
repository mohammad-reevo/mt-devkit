---
name: pr-screenshots
description: Capture verification screenshots of a running app (signed in as the agent's own dev user) and attach them to a PR body myself — no drag-and-drop by Mohammad. Images go to the repo's orphan `pr-media` branch and are embedded in the live PR body, which turns frontend-monorepo's `validate-description` green. Used by `verify` for any UI change, and on its own. Triggers on "screenshot this", "attach the screenshots", "add verification media to the PR", "take a screenshot of the preview", "/pr-screenshots".
---

# pr-screenshots — capture, then attach

Two halves, usable separately: **capture** (sign in as the agent user, drive to the page, save
the image) and **attach** (commit the images to `pr-media`, embed them in the PR body).

## Why `pr-media`

GitHub has no API for PR image upload — drag-and-drop uses the signed-in web session, which no
token reaches. An image committed to the **same repo** renders in the PR body for anyone with
repo access, and frontend-monorepo's `validate-description` accepts an image embed with an HTTPS
URL (proven on frontend-monorepo#20793: red → pass).

So each repo keeps one **orphan branch `pr-media`**, never merged, one folder per PR (`<pr>/`).
Pushing it triggers no CI. Its images are private to repo members, like the PR.

## Capture

**Where to point the browser.** A frontend-only change: the PR's Vercel preview
(`reevo-webapp-start-pr-<n>-<branch-slug>.vercel.app`; the exact URL is in the PR comment marked
`<!-- vercel-deploy-previews -->`), which talks to the dev backend. Anything needing a backend
change: a local stack (`local-stack`).

**On a local stack, skip sign-in.** The agent user doesn't exist in the stack's pool org;
`local-stack up` writes the frontend a session override for the pool org's seeded admin, so the
stack's frontend opens already signed in.

**On the Vercel preview, sign in as the agent user** — `mohammad+agent@reevo.ai`, an admin of the dev org
`cce7b290-8a08-4904-a6c7-2b6613877cf5`. Credentials live in `~/.config/reevo/agent-login.env`
(`AGENT_EMAIL`, `AGENT_PASSWORD`, mode 600). **Never print the password or type it through a tool
argument** — the transcript would keep it. Instead, serve it once from localhost and have the
browser fetch it server-side:

1. Background: `python3 <this-skill-dir>/serve_secret.py` (127.0.0.1:8931, answers one GET, exits).
2. In `browser_run_code_unsafe`: `const pw = (await (await page.request.get('http://127.0.0.1:8931/')).text()).trim();`
   then fill the password field with `pw`.

The sandbox there has no `fs`, `require` or dynamic import — this hand-off is the way around it.
Auth0 is identifier-first: `Email address` → Continue → password → Continue. Run the server again
for every login.

**Drive and shoot.**
- Prefer deep links over canvas clicks. Workflow run details:
  `/workflows/<user_flow_id>?tab=run-history&run_id=<run_id>&focus-node="<node_id>"` (URL-encode
  the quotes).
- Scroll the element that proves the change into view (`locator.scrollIntoViewIfNeeded()`) before
  the shot, and assert its text in the same script — a screenshot of the wrong pane proves nothing.
- `browser_take_screenshot` may only write under the session's worktree: save to
  `.playwright-mcp/<name>.png`, then `mv` to `~/Downloads/images/<slug>/` (outlives `/done`, easy
  to find). Name files by what they show (`outcome-labels-enroll.png`).
- Look at each image (Read it) before attaching.
- Close the browser when done.

**Test data on dev** goes through `backend-request --dev` (`--write` for anything non-GET), and
stays inside records that are plainly test data — `[Testing Party] …` contacts, a dedicated test
workflow. Never someone else's records.

## Attach

```bash
python3 <this-skill-dir>/attach.py --repo-dir <worktree>/<repo> --pr <n> \
  ~/Downloads/images/<slug>/a.png ~/Downloads/images/<slug>/b.png \
  --caption "a.png=Enroll — Partial" --update-body
```

It fetches the remote `pr-media` tip (or starts the branch), rebuilds the tree keeping every other
PR's folder, commits with plumbing, and pushes — retrying if another session moved the branch.
`--update-body` edits the **live** body: the image block replaces the frontend template's
`[DRAG AND DROP SCREENSHOTS OR VIDEOS HERE]`, else goes under `# Visual Verification & UI Demo`,
else is appended. Without it, the script prints the markdown for you to place (salestech-be's
`## Verification`, say). Either way, attachments already in the body stay byte-for-byte
(`github.md`).

**Verifying it landed.** `curl` against `github.com/<org>/<repo>/raw/…` 404s even with a token (it
needs a web session), so it proves nothing. Check the files with the contents API —
`gh api "repos/<org>/<repo>/contents/<pr>?ref=pr-media"` — and, on frontend-monorepo, that
`validate-description` passes on its re-run.

## Guardrails

- **The PR's own branch never carries the images.** They would land in its diff.
- **Never force-push `pr-media`.** It holds every PR's media; the script only ever fast-forwards.
- **Screenshots show dev data only.** Never point capture at prod.
- Hand back the image paths and the PR link; say which check each image shows.
