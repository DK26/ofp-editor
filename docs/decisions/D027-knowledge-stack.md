# D027: Knowledge stack: deterministic actions first, facts from Teller, a small primer

> **Status:** baseline → item 6 `accepted` for v1 (2026-09-28, OWQ-28 under the owner's go-ahead; see the note) · **Decided by:**
> research (doc 30)
> · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** how models (in-app and external) learn the engine's facts, rules and craft. **Related:** D003, D019, D023, D026, D028.
> **Open parts:** DG031 (concept id scheme), DG032 (one knowledge store and tool family); card selection is unmeasured (doc 30 §3.6).

## Context

Models have seen little of this engine and much of its successors, so they fill gaps with confident near-misses from later games
(`sleep`, `isNil`, `//` comments in SQS, `class Entities`, the diary API) (doc 30 §1.1). Doc 30's experiment: on a weak model, one
hand-written reference card per task raised passes from 1 to 16 of 24 and cut hallucinating answers from 10 to 2, within one pass of
a frontier model working alone (17 of 24); a primer alone lifted passes only from 1 to 4 [M, with the limits in §3.6].

## Decision

Layered knowledge over one source of truth, strongest lever first (doc 30 TL;DR):

1. **L1: typed deterministic actions and code-written files.** Code renders `mission.sqm`, the briefing skeleton, `description.ext`
   settings, END-trigger wiring and common conditions, so whole error classes disappear.
2. **L2: facts from Teller**, the language service: computed menus, short reference cards and command lookups, generated from the
   pinned engine source and tagged per profile. For weak models, code picks the cards and injects them; strong and external agents may
   also call lookup tools.
3. **L3: Teller as guard rail**: engine-parity checks with model-readable diagnostics, and repair loops that fix one finding per turn.
4. **L4: a compact primer skill** (`skills/mission-primer/`, at most 1,200 words): routing to tools, the mission model, syntax rules and
   traps. It is the only layer an external agent reads before choosing a tool.
5. **L5: verified, profile-tagged exemplars**, later.
6. **No fine-tuning now** (training-data licensing, upkeep per profile and per base model, poor transfer, no help for cloud models).
7. **Activation is code's job**: a weak model never decides to load knowledge; each workflow step declares its primer sections and cards.

## Alternatives considered

- A large primer or RAG over prose: coverage capped by length, cannot follow the target profile, and was over-applied into a hack in the
  experiment (doc 30 TL;DR).
- Fine-tuning a model on engine knowledge: see item 6.
- Bohemia wiki text as a knowledge base: not allowed (D014).

## Consequences

- Every primer and card fact has an id, a pinned citation and a check kind (`catalog`, `const`, `vector`, `probe`, `review`); tests fail
  on drift. The experiment's tasks become the first cases of a knowledge instrument.
- Cards and catalog rows are tagged `cwa199` / `cwr` / `ce` and keyed to the mod-set fingerprint (D003, D030); mod knowledge overlays
  appear only inside code-selected cards (doc 42 §2.5).
- Standing Orders entries (D028) are the concept source shared by users and models; whether cards and entries are one store is DG032.
- External agents get the primer as an Agent Skill through Plotroom's MCP server (D019).

## Sources

Doc 30 (TL;DR, §1, §3, §4, §5); doc 33 §3; doc 42 §2.5; `skills/mission-primer/`.

## Amendment notes

### 2026-09-28: OWQ-28 (no training in v1) and D051 (lookups by grant)

A note under lifecycle item 5: it fills in items 2 and 6 and reverses nothing; the header's status gained a pointer. Both answers
were adopted under the owner's go-ahead of 2026-09-28 (lightly edited): "Tiny models with no cloud availability should be tested
directly on PC. Either way, except for GPG signing, we can do everything else." Recommended option adopted under the owner's
go-ahead; overrule on return. An amendment note, not a record, because the answer keeps item 6 and only adds when to look again.

- **Item 6, OWQ-28 (a) for v1 ([OWNER-QUESTIONS.md](OWNER-QUESTIONS.md); doc 58 §7 and Appendix A).** Plotroom trains no model,
  head or adapter in v1; presets (D048), zero-shot scoring, kNN over qualified examples and code-computed candidates carry the work.
  Item 6 is now the owner's rule for v1, not only a research baseline. Option (b), a narrow post-v1 spike (non-generative heads,
  extractors or format adapters on an OSI base of about 1B parameters or less, trained only on data Plotroom's generators produce and
  code labels, with provenance per item, published data and scripts, separate pinned downloads, qualification against the untrained
  baseline), is **revisited after doc 58's experiments E3 and E4**; it is not adopted. Generative fine-tuning (option (c)) is not
  recommended. D048 decision 3 is unchanged; doc 53 OQ6 (format adapters after v1) is folded into OWQ-28.
- **Item 2, refined by [D051](D051-capability-ladder-freedom-by-qualification.md) item 5.** For in-app setups, "strong … agents may
  also call lookup tools" now means: read-only lookup, navigation and check tools from freedom level FR5, by a qualification grant,
  and only at Thorough or Max effort (doc 30 §4.3). Code still pushes the cards at every level, and weak models never fetch (item 7).
  External agents keep the product tools the MCP server exposes (doc 63 §10).
