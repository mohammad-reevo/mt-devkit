---
name: vendor-api-research
description: Research what a third-party vendor's API can actually do before a design depends on it — the public reference plus the places it under-reports (OAuth discovery metadata, dynamic client registration, partner programs, official CLIs / SDKs / MCP servers and the endpoints they really call, plan gating), with every load-bearing claim probed read-only and labelled verified / doc-only / inferred. Absence claims ("no X endpoint", "no OAuth") are the riskiest and need a probe before anything is designed on them. Read and followed by create-project-discovery's `systems` and `spike` steps and by the `scoper` agent on a vendor-integration idea; also invocable on its own. Triggers on "research the <vendor> API", "what can <vendor>'s API do", "does <vendor> support OAuth / webhooks / X", "/vendor-api-research".
argument-hint: <vendor> [the capabilities the design needs]
---

> Self-contained — no devkit dependency. Read-and-follow: subagents (the `scoper`, discovery's
> research agents) can't invoke skills, so their brief points them at this file.

# vendor-api-research — what the vendor can do, proven

A vendor's public API reference is a lower bound on what it can do, not the whole of it.
Official tooling often reaches further than the documented API, auth servers advertise
themselves in metadata no reference page mentions, and endpoints are gated by plan without
saying so. A design built on doc-only conclusions inherits every one of those gaps. Catching a
wrong capability at research time costs one read-only probe; catching it after the eng doc
costs a rewrite.

## Input

The vendor, and **the capabilities the design needs** — e.g. "list a workspace's tables", "a
third-party app can act for a customer", "push on row change". Research what would change a
decision; don't catalogue the whole API.

## 1. Read every source, not just the reference

Per capability, look in all of these:

- **The public API reference** and its OpenAPI spec when published. Read the raw spec, not a
  truncated render — a "no such endpoint" read off a partial spec is unverified.
- **Auth discovery metadata.** Fetch `https://<api-host>/.well-known/oauth-authorization-server`
  and `/.well-known/openid-configuration`. Note the registration endpoint (dynamic client
  registration — open, or approval-gated?), grant types, PKCE and scopes. An OAuth server that
  exists "for MCP" still issues tokens; find out what those tokens can call.
- **App / partner programs and marketplaces** — the vendor's developer portal, integration
  directory, "build an app" pages. A listed partner app is proof a third-party auth path exists.
- **Official CLIs, SDKs and MCP servers.** Install or read them and see **which endpoints they
  actually call** — `--help`, `--verbose` / debug flags, the package source. They often hit an
  internal API (`/v3/...`) the public reference never lists.
- **Plan gating** — pricing pages, "Enterprise only" notes, trial limits. A capability that
  exists only on a plan our customers don't have is, for the design, absent.
- **Webhooks / events** — the documented event list, how subscriptions are registered, and the
  delivery guarantee.

## 2. Probe every load-bearing claim

A claim is load-bearing if the design would change were it false. Each gets a read-only probe:
a metadata fetch, a `GET`, a CLI list command, a `--help`. Credentials come from the project's
test org or testing kit (see the KB index); never a customer's.

- **Read-only by default.** Anything that registers, creates or writes — a dynamic client
  registration, a webhook subscription, a test record — needs Mohammad's go first, per probe.
- **Absence claims are the riskiest.** "There is no list-tables endpoint", "only a personal API
  key", "no row-level events": a doc's silence is not evidence. Before a design depends on one,
  try to disprove it — the CLI, the OAuth metadata, the internal API with each credential you
  hold. If you can't, say what you tried.
- **Compare credentials.** Make the same call with each auth method you have (API key vs OAuth
  token) — a 403 "Insufficient permissions" on one and a 200 on the other is itself a finding.

## 3. Label every claim

Each finding carries one label, and the write-up keeps them visible:

- **verified (how)** — probed; name the call and what came back.
- **doc-only** — the docs say so; not probed. Name the page.
- **inferred** — reasoned from other facts. Name them.

A design input may rest on **verified** only. A doc-only or inferred claim the design needs is
either probed now or written up as an open question that names the probe that would settle it.

## 4. Report

Per capability: the answer, its label, and the evidence (URL, command, status code). Then the
claims that changed from the docs' story, and what each changes in the design. Write it where the
caller says — discovery's step write-up, the scope file, or the project's scratch dir
(`scratch-files.md`).

## Worked example — Clay (Prospecting Integrations, Nov 2026)

What the docs-led research concluded, and the design stood on for a week:

- "Clay can't list tables or tell us a row's table" → a pasted per-workflow URL, and no table
  filter.
- "No third-party OAuth, only a personal API key" → an API-key connection.

What hands-on probing showed (2026-11-13):

- `https://api.clay.com/.well-known/oauth-authorization-server` publishes an open OAuth server:
  dynamic client registration at `api.clay.com/oauth/register` with no approval,
  authorization_code + refresh + device code, PKCE S256, scopes `mcp` and
  `public-endpoints:mcp`. The early research *had* seen "MCP OAuth with dynamic client
  registration" — and dismissed it as MCP-only without probing.
- The official CLI (`@clay-run/cli` 1.19.0; `clay login` = browser OAuth) lists tables
  (`clay tables list`) and reads rows, through Clay's internal API
  `https://api.clay.com/v3/workspaces/:id/...`. The same calls with the Public API key return
  403 "Insufficient permissions"; `/public/v0` has no tables endpoints (404).

Two absence claims, both wrong, both cheap to probe, and both had already shaped the eng doc.
Labelling would have marked each as doc-only before it became a design input.

## Guardrails

- **Never write to a vendor without a go** — per probe, as above. Fake records only, in a test
  org we're allowed to use.
- **Never a customer's credentials or org.**
- **Stop at what changes a decision.** This is research for a design, not API documentation.
