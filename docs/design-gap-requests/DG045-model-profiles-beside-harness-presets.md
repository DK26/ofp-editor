# DG045: Model profiles beside harness presets: where probed facts about a model live

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round; the record's user-facing name goes through D034 item 3). Blocks: the preset file format
> (D048's open part; doc 55 §3.3); doc 55 §6.4's `from_profile` thinking switch; doc 51 §4.2–§4.3 stay `proposal-only`.

## Context

- **D048** (owner, 2026-09-28): one harness preset per model and step kind, which "change[s] how Wilco asks, never what code owns";
  bound to the model file, runtime build and chat template; its format and shipping path are open parts.
- **D021; D023 Consequences.** The provider layer pins model ids in `models.toml` and probes each endpoint; "A capability probe per
  endpoint and model chooses a prompt profile (doc 14 §7)".
- **Doc 51 §4.1–§4.3, §4.10, §6.1 item 1.** A *profile* of probed facts about a model on an endpoint, which every preset for it must
  respect: keyed by (model artifact, wire, endpoint route); layered family defaults → model × wire → model × wire × endpoint →
  measured values → the user's override (which marks the setup custom); each fact `Unprobed`, `Yes{run_id, date}` or
  `No{run_id, date}`. Facts include template role rules, whether reasoning can be switched off (`Honoured` or `FloorAt`), schema
  dialect, stop tokens, error codes and the control-token families to neutralise in mission text. "A choice may only select among
  what the facts allow (a preset cannot switch off reasoning that the profile records as mandatory)."
- **Doc 51 §6.1 items 5–6.** Mandatory-reasoning endpoints (Pick and Fill at the floor level) and an untrusted-text control-token
  table both need a fact record.
- **Doc 55 §7 item 10, §6.4, OQ1.** The default preset's thinking switch is taken "from the model's profile"; doc 55 asks for one
  record of the facts-versus-choices split. OQ1: "harness preset" or another word, given four uses of "preset", and "model profile"
  should not name the harness preset.
- **Name collision.** "Profile" already means a *target profile* (D003; D051 item 4's domain).

## The gap

D048 decides presets, the tuned choices. It does not say where the facts about a model on an endpoint live, who fills them (release
data, probes, qualification), how their evidence is recorded, or how a preset is checked against them. Without that, a probe that
learns "reasoning cannot be switched off here" would have to edit a tuned preset, and the loader has nothing to refuse an impossible
choice against.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | One record: the harness preset holds both facts and choices | One file | Facts differ by endpoint and runtime while a preset is per model; a probe would rewrite a tuned, qualified preset |
| B | Two records: a profile of probed facts (doc 51 §4.2–§4.3: key, layering, tri-state evidence) and the preset of choices; the preset loader refuses a choice the profile forbids; badges record both hashes (DG044) | Facts are re-probed without touching tuned choices; one home for mandatory reasoning, template rules and control-token families | Two data files to version and ship |

## Recommended resolution (proposal)

B, as doc 51 §4 proposes and doc 55 §7 item 10 asks. The record's name is chosen with doc 55 OQ1 in the design round (D034 item 3);
it should not be "profile" alone, since D003 and D051 use that word for target profiles.

## What it would change

- D048's open parts (the format: two records); doc 55 §3.2–§3.3 (the preset refers to its profile by id and hash); doc 51 §4.10's
  sketch; D021 (the probe writes profile facts); D023's "prompt profile" wording; `models.toml` or its neighbour holds the facts.
- Tests first (proposal): the loader refuses a preset that sets reasoning off where the profile says `FloorAt`; a probe result updates
  the profile and marks dependent badges per DG012 without changing the preset file.

## Affected docs

D048; D021; D023; D003 (naming only); doc 51 (§4.1–§4.3, §4.10, §6.1); doc 55 (§3, §6.4, §7, OQ1); DG012; DG044; DG051.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 51 §6.1 item 1 and doc 55 §7 item 10 (one candidate in two docs), with doc 51 items 5–6 as uses, re-reading D048,
  D021, D023, doc 51 §4.1–§4.3 and doc 55 §6.4, §7 and OQ1 on 2026-09-28.
