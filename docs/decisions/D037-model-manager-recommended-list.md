# D037: Which models the Model Manager may recommend

> **Status:** accepted · **Decided by:** owner (OWQ-19 a) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** the Model Manager's recommended list of local models, and how every other model file is treated. Cloud endpoints are
> outside it (D021, D023). **Refines:** D022 (its open part OWQ-19) and D023 decision 6, which this record governs from now on.
> **Related:** D001, D008, D026. **Open parts:** which models qualify first (doc 49, in progress; D023's amendment names provisional
> candidates); badge wording (doc 21 OQ3); what voids qualification (DG012).

## Context

- D022 accepted a Model Manager that recommends local models fitting the user's hardware and installs them, including directly from
  Hugging Face. Its 2026-09-27 amendment makes the managed `llama-server` sidecar the primary runtime, with pinned downloads, pinned
  samplers and a guard against files the pinned runtime cannot run.
- D023 decision 6 limited default downloads to OSI-licensed weights and left the exact rule to the owner.
- Weight licences vary widely: OSI licences, custom revenue-gated or notice-and-indemnity licences, pass-through use terms,
  non-commercial terms, and one licence that excludes EU users (doc 47 §5). One candidate's usage policy bans military or warfare uses
  (doc 14 §6; doc 48 row O3), which matters for a military-game editor.
- Metadata can disagree with the licence text: a GGUF's `general.license` and the model card differed for one tested file (doc 46
  §4.1), and licences change between revisions (doc 47 §5).

## Decision

1. **The recommended list** holds only models whose licence is **OSI-approved with no field-of-use restriction**, and which **passed
   Plotroom's own qualification** (D022 item 4; `tools/local-qual/`) on the runtime the Manager pins.
2. **Everything else installs as "custom"**, including any Hugging Face file the user names: its licence and use policy are shown, the
   user explicitly accepts them, and it carries an **"unqualified" badge** until it passes qualification.
3. This honours the owner's "even directly from Hugging Face" while keeping licence risk visible; downloads still follow D008 (a
   user-enabled source, blocked offline, started by the user, never by Wilco).

## Alternatives considered

- Any licence on the recommended list, with warnings (OWQ-19 b): moves licence and use-policy risk onto users who trust the list.
- The recommended list only, no custom installs (OWQ-19 c): breaks "even directly from Hugging Face" and bring-your-own freedom.

## Consequences

- The licence is read at the pinned revision; the LICENSE file wins over metadata; when card and GGUF licence fields disagree, or
  whether a use statement is a binding field-of-use limit is unclear, the model is not recommended until resolved (doc 46 §4.1; doc 47
  §5). The manifest stores both licence fields and the LICENSE file's hash.
- Custom only, never recommended: not-yet-OSI licences (for example OpenMDW until OSI approves it), revenue-gated, indemnity or
  pass-through custom licences, non-commercial licences (labelled as such), territory-restricted licences, unclear provenance, and any
  model whose use policy bans military or warfare uses. This answers doc 47 OQ6; whether Plotroom's own evaluations may test such a
  model (doc 48 OQ9) is a separate call.
- OSI-licensed models that are not yet qualified are candidates, not recommendations; they can be installed as custom with their
  current badge (D023 decision 2).
- Badges are per setup (D022 item 4), so a model behind a bring-your-own endpoint (Ollama, LM Studio, a fork's server) shows
  "unqualified" until qualification passes on that endpoint.
- The Model Manager's catalogue data (roadmap M6) carries licence family, use-policy flags and qualification status per entry.

## Sources

Doc 02 (TL;DR, §8); doc 14 §6; doc 46 (TL;DR, §4.1); doc 47 (TL;DR, §2.7, §5, OQ6); doc 48 (row O3, OQ9); D022 (with its amendment of
2026-09-27); D023 (with its amendment of 2026-09-27); `OWNER-QUESTIONS.md` OWQ-19.

## Amendment notes

### 2026-09-28: refined by D047; related D045 (pointers)

A note under lifecycle item 5 (`docs/decisions/README.md`). The decisions above are unchanged, and the header has no open part to mark.

- **Testing → [D047](D047-military-use-policy-models-and-services.md)** (OWQ-26 (a), owner, 2026-09-28). The question the Consequences
  leave as "a separate call" (doc 48 OQ9) was filed as OWQ-26 and answered: Plotroom's own evaluations may test a model whose use
  policy bans military or warfare uses with the synthetic suites only, and the result never becomes a recommendation or a preset.
  D047 carries the same principle to hosted services: the NVIDIA trial and Z.ai are not used, and combat-flavoured items never go to
  hosts with violent-content clauses.
- **Free cloud presets → [D045](D045-free-model-offer-policy.md)** (OWQ-24 (b) and the owner's direction of 2026-09-27). Cloud
  endpoints stay outside this record's scope; D045 follows the same idea as decision 1 for them: a free model is offered for a step
  kind only if its provider's terms allow it and it passed Plotroom's qualification for that step kind.

### 2026-09-28: refined by D057 (badges per component kind)

A note under lifecycle item 5; [D057](D057-bindable-badged-switchable-components.md) governs (DG057 option B), decided under the
owner's delegation; the owner may overrule it on return. Non-generative components (doc 58 §1.2) carry a badge per component kind,
set by Plotroom's own qualification suites for that kind (doc 58 §4.9), beside the badges per model setup and step kind; as for
models, a badge comes from Plotroom's instruments, never from vendor claims. The decisions above are unchanged, and the header has no
open part to mark.
