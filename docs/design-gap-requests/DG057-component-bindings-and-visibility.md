# DG057: Bindings, badges and kill switches for non-generative components

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **decided** (owner's delegation, 2026-09-28): option B → D057. Component kinds are bindable beside D024's roles, each with a
> badge, a plan-card line, an "answered by" line and a kill switch. Not yet folded.
> **Decision by: owner** (D024 item 4's closed role list; doc 58 OQ3). Blocks: every doc 58 component in the product; the "answered
> by" display and component badges stay `proposal-only`.

## Context

- **D024 item 4.** Roles are `router`, `writer`, `scripter`, `explainer`, `play-tester` and `translator`; the user binds each to a
  configured model, and a step never runs on a setup other than the one shown. **D051 item 9** adds `planner` after v1.
- **Doc 58 §1.2.** The component contract: one consumer seam per component (`Selector`, `Retriever`, `Ranker`, `Extractor`,
  `Checker`, `Flagger`, `Translator`, `Voice`, `Transcriber`); advisory or pre-filtering only; a code-owned fallback; qualified against
  the simple baseline; visible, with "answered by" and a kill switch; optional pinned downloads; product-scoped.
- **Doc 58 §4.11 items 1 and 5, OQ3.** D024's roles "have no slot for non-generative or specialist components", and doc 55's knob
  table keeps model choice out of presets ("no preset names another model", under D023 decision 3 and D024). "A component needs its
  own visible binding, a badge per component kind (D037), a plan-card line and a kill switch", with qualification suites per
  component kind. OQ3 asks the owner whether component kinds become bindable roles beside D024's.
- **D023 decision 1; D037.** Weights are optional downloads; badges come from Plotroom's own instruments. **DG052** decides the
  runtime for encoders; **DG050** decides escalation between generative stages.

## The gap

Components (retrievers, rerankers, extractors, checkers, flaggers, translators, voices, transcribers) have no binding slot, no badge
kind, no plan-card line and no rule for switching them off, so a component could only be enabled silently or hard-wired.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Components fixed by the release, enabled per feature in Settings, shown only in the inspector's "answered by" | No new roles | The user cannot choose or see which artifact serves a seam before a run |
| B | Component kinds become bindable beside D024's roles, each with a badge per component kind (D037), a plan-card line and a kill switch; qualification suites per component kind | The glass box and user choice as for models (D010, D024) | Amends D024 item 4's closed list; more settings |
| C | A harness preset names the component | One place per model | Doc 55's knob table keeps model choice out of presets (D023 decision 3) |

## Recommended resolution (proposal)

B, as doc 58 §4.11 item 1 proposes; the owner decides (doc 58 OQ3).

## What it would change

- D024 item 4 (component bindings beside roles); D037 (badges per component kind); doc 58 §1.2 and §4.9 (suites); the plan card and
  inspector (doc 38 §5.2–§5.3); Settings → Models (doc 63 §7's ladder grid gains component rows).
- Tests first (proposal): a component runs only when bound and enabled; its kill switch returns the code-owned fallback with the same
  accepted result class; "answered by" names the component, artifact and threshold.

## Affected docs

D023; D024; D037; D051; doc 55 (knob table); doc 58 (§1.2, §4.9–§4.11, OQ3); doc 38 (§5.2, §5.3); doc 63 §7; DG050; DG052.

## Decision record

- **Decided 2026-09-28 under the owner's delegation: option B → [D057](../decisions/D057-bindable-badged-switchable-components.md).**
  Component kinds become bindable beside D024's roles, each with a badge per component kind (D037), a plan-card line, an "answered by"
  line in the inspector and a kill switch that returns the code-owned fallback with the same accepted result class; qualification
  suites per component kind; a harness preset never names a component (C rejected). No owner question was filed; the owner may
  overrule it on return.
- **Reason.** The glass box and user choice work for components as for models (D010, D024 item 4); A leaves the user unable to see
  which artifact serves a seam before a run; C conflicts with doc 55's knob table (D023 decision 3).
- **Related decisions of the same day.** DG052 → D056 (the encoder runtime); DG050 → D055 (escalation between generative stages).
- **Folding (what moves this request to `folded`).** Doc 58 §1.2 and §4.9; the plan card and inspector (doc 38 §5.2–§5.3); Settings →
  Models (doc 63 §7). The notes on D024 and D037 are done (2026-09-28).

## Verification notes

### Filing (2026-09-28)

- Filed from doc 58 §4.11 items 1 and 5, re-read on 2026-09-28 with doc 58 §1.2 and OQ3, D024 and D051.

### Owner delegation, design-gap pass (2026-09-28)

- Decided with the recommended option B under the owner's delegation of 2026-09-28 (quoted in D057), without an owner question. D057
  was written from this request, doc 58 (§1.2, §4.9–§4.11, OQ3), D023, D024, D037, D048 and D051, re-read on 2026-09-28. Doc 58
  gained only an answered-marker at OQ3.
