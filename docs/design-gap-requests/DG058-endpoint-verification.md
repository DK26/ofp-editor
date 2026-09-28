# DG058: Endpoint verification: behavioural probes, "Check this endpoint" and "last verified"

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63;
> it also covers doc 48 §7.4 items 3–4). Status: **open**.
> **Decision by: technical** (design round); the re-check interval and the canary's share of a free allowance are measured (doc 51
> OQ12). Blocks: D045 item 5's regular re-qualification of free endpoints and D021 decision 4's probe contents; doc 51 K1–K4 and K20
> stay `proposal-only`.

## Context

- **D021 decision 4** probes each endpoint's capabilities. **D044**: a cloud screen never sets a badge. **D045 item 5**: offered free
  models are "dated and re-qualified" regularly. **D050 item 4**: host health (cool, probe, demote) for routing. **D051 item 4**: a
  D044 screen never sets a grant.
- **Doc 48 §7.4 items 3–4.** "Probe by behaviour": the capability probe must send a real strict-schema request and a reasoning-off
  request and check the served provider; "Check this endpoint": the Model Manager's "check this model on my machine" gets a cloud
  counterpart, the same suites against a user's endpoint under a cost cap shown in advance.
- **Doc 51 K1–K4, K20, §6.1 item 10, OQ12.** Qualify the endpoint, not only the model: replay the same requests against a reference
  serving (the qualified local run or a pinned paid endpoint of the same weights) and score agreement and schema-pass; the pass bar
  comes from the reference arm's own noise; the schema-pass denominator is every call; per endpoint, store the Pick choice
  distribution and Fill outcome mix as a fingerprint; badges carry "last verified"; a re-check canary runs only when the user starts
  or enables it, with its call count shown first, because each call spends the user's allowance. Hosts serving the same weights
  differed in tool-schema accuracy from 100% down to 71.96% in a vendor's own test (doc 51 TL;DR, [V-vendor]).
- **Doc 50 §6.** A "screened, not qualified" state in the model catalogue is a listed candidate.
- **D008.** Outbound traffic goes only to the provider the user configured and sources the user enabled; a check against the
  configured provider is allowed, but it spends the user's own quota.

## The gap

D045 requires free endpoints to be re-qualified regularly and D021 probes capabilities, but no document defines an endpoint check:
what it sends, what reference it is compared with, its pass bar, who starts it, what it costs in quota, how its result is shown, and
how "screened in the cloud" differs from "qualified" in the catalogue.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Capability probe only (D021 decision 4 as written) | Cheap | Hosts serving the same weights differ in decisions and schema accuracy |
| B | A behavioural probe (doc 48 §7.4 item 3) plus a user-started "Check this endpoint": a fixed suite replayed against a reference arm, pass within the reference's own noise bound, every call in the schema-pass denominator; a stored per-endpoint fingerprint; badges showing "last verified"; a re-check canary only when the user starts or enables it, with its call count shown first; a "screened, not qualified" catalogue state for D044 screens | Qualifies the endpoint, not only the model; spends quota only with consent; honest labels | Needs a reference arm per model; every check spends allowance |

## Recommended resolution (proposal)

B (doc 51 K1–K4 and K20; doc 48 §7.4 items 3–4; doc 50 §6's catalogue state). The re-check interval and the canary's share of a daily
allowance stay open until measured (doc 51 OQ12).

## What it would change

- D021 decision 4 (probe contents); D045 item 5 (what "re-qualified" runs); D022 and the Model Manager (the cloud counterpart of
  "check this model"); the model catalogue (the screened state); `tools/local-qual` (the reference-arm comparator, doc 51 K2).
- Tests first (proposal): a stub endpoint that serves the wrong provider or ignores the strict schema fails the behavioural probe; a
  canary never runs without the user's start or opt-in and shows its call count first; a D044 screen shows "screened, not qualified",
  never a badge.

## Affected docs

D008; D021; D022; D044; D045; D050; D051; doc 48 §7.4; doc 50 §6; doc 51 (K1–K4, K20, §4.8, §6.1, OQ12); `tools/local-qual`.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 51 §6.1 item 10, with doc 48 §7.4 items 3–4 and doc 50 §6's catalogue-state candidate, which the DG039 step had left
  unfiled; re-read on 2026-09-28 with D021, D044, D045, D050 and D051. No endpoint was contacted.
