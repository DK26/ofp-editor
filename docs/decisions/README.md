# Decision records

A **decision record** (`Dnnn`) states one settled Plotroom decision: what was decided, the context, the alternatives considered, what
follows from it, the sources, the date and who decided. Records are short (about 60 lines at most) so that a contributor or a coding
agent can load the one they need.

- **Research docs** (`docs/research/`) are the evidence and the proposals. Their designs stay `proposal-only` unless a record adopts them.
- **Design-gap requests** (`docs/design-gap-requests/`) are open gaps or contradictions in Plotroom's own design.
- **Decision records** (this folder) are the settled rules that later work builds on.
- **Owner questions** ([`OWNER-QUESTIONS.md`](OWNER-QUESTIONS.md)) list the questions only the owner can answer, each with a
  recommended answer and, once decided, the owner's dated answer and the record it became.
- **Engine requests** (`docs/upstream/`, D012) are gaps in the game engine, not in Plotroom's design.

**Precedence.** `AGENTS.md` wins over every record; records that restate an `AGENTS.md` invariant summarise it and never widen or
narrow it. An accepted record wins over a research doc's proposal. A research doc that contradicts a record is stale: fold the
decision into it, or file a DG if the contradiction is real.

## Kinds of decision and who decides

| Decided by | Covers | Status it gets |
| --- | --- | --- |
| **owner** | Product scope, user-facing names, security and network boundaries, licensing and legal matters, public outreach (as in the DG README) | `accepted` |
| **owner (`AGENTS.md`)** | Invariants the owner wrote into `AGENTS.md`; the record is a summary with consequences | `accepted` (invariant) |
| **research** | A research doc's recommendation adopted as the working baseline for implementation | `baseline` |

A `baseline` record names what evidence would reopen it (**Revisit if:** a failed spike, benchmark or probe). Changing a baseline
needs that evidence or an owner decision; changing an `accepted` record needs the owner.

## Lifecycle

| State | Meaning |
| --- | --- |
| `accepted` | Decided by the owner, directly or as an `AGENTS.md` invariant |
| `baseline` | Adopted from research; stands until named evidence contradicts it |
| `superseded by Dnnn` | A later record replaced it; the header gets the date and a pointer, the text stays |
| `withdrawn` | The decision turned out to be unnecessary; the header gives the reason |

1. A decision is made (an owner answer, a decided DG, or the design round adopting a research recommendation).
2. A record is written with the decider and the date. Parts that remain open are listed under **Open parts** and point to DGs or owner
   questions; **a record never decides an open DG** by implication.
3. The affected docs are updated to state the decision and point to the record (the same folding step DGs use).
4. A decision is never edited in place. A reversal is a new record that supersedes the old one. Typo, link and citation fixes are
   allowed and noted at the end of the record.
5. A later decision that settles a record's open part, or narrows it without reversing it, **refines** it. It takes one of two forms:
   - a **new record** that names the old one under **Refines:** in its header, the usual form when the answer adds rules of its own
     (D031–D043; see "Records refined on 2026-09-27" below);
   - a dated **amendment note** at the end of the old record, under "Amendment notes", when the answer only fills in the old record's
     own items (for example the owner's runtime choice in D022).

   Either way the text above the notes stays as written. When both forms exist for one answer, the new record governs, and the note
   points to it. The only header change allowed is a pointer: an **Open parts** entry that is now settled gains "(answered `date` →
   Dnnn)", and a status the refinement changes gains "→ `new status` (`date`; see Dnnn or the note)", keeping the old words, as a
   superseded record's header does. A dated note at the end records the pointers.
6. Never delete a record and never reuse a number.

## Relation to design-gap requests

| Situation | What happens |
| --- | --- |
| A DG is decided and the decision sets a durable, project-level rule | The DG's "Decision record" section records the choice; a `Dnnn` states the rule going forward and cites the DG (DG013 → D024, DG028 → D008, DG033 items 3–4 → D029, DG002 → D034, DG029 → D035, DG030 → D038, DG014 → D043) |
| A DG is decided and the answer is a local detail (a name, a threshold, one doc's wording) | The DG alone records it; no `Dnnn` is needed |
| A DG is still open | Records that depend on it list it under **Open parts**; dependent work stays `proposal-only` or `blocked on DGnnn` |
| An owner question is answered | The answer is dated in `OWNER-QUESTIONS.md`; it becomes a new `Dnnn` or a DG decision as above, and the Summary table's "Answered" column names the record (the answers of 2026-09-27 became D031–D043; those of 2026-09-28 became D045–D047 and D044's amendment note) |

## Numbering and labels

- File names: `Dnnn-short-slug.md`: `D`, three digits, a hyphen, a lowercase kebab-case slug of at most six words.
- **Always write three digits** ("decision D007"). Other labels in the docs look similar: doc 21 cites its own sections as D1–D14; lint
  codes D9–D12 appear in docs 27, 34 and 42; Iron Curtain's decisions are cited as "IC D047" or by path in docs 02, 13, 14 and 17.
  DG005 (one code registry) should register the `Dnnn` family and the `OWQ-nn` family.

## Template

```markdown
# Dnnn: <title>

> **Status:** accepted | baseline · **Decided by:** owner | owner (`AGENTS.md`) | research (doc NN) · **Decided:** <date>
> **Recorded:** <date> · **Scope:** <what it governs> · **Refines:** <Dnnn, or omit> · **Related:** <Dnnn, …>
> **Open parts:** <DGnnn, OWQ-nn, or none> · **Revisit if:** <baseline records only>

## Context
## Decision
## Alternatives considered
## Consequences
## Sources
```

## Index

| ID | Decision | Decided by | Status | Decided | Main sources |
| --- | --- | --- | --- | --- | --- |
| [D001](D001-licence-gpl-3-or-later.md) | Licence: GPL-3.0-or-later everywhere, Bohemia's §7 terms, generated-content permission (draft) | owner | accepted | 2026-09-26 | 02 §6, §10 |
| [D002](D002-name-and-naming-system.md) | Plotroom, its descriptor, Wilco, Plotline, the Tote, Teller; `plotroom` identifiers | owner | accepted | 2026-09-27 | 02 §9; DG002 |
| [D003](D003-upstream-alignment-and-target-profiles.md) | Align with CWR-CE; BI snapshots as baseline; per-mission profiles and "Requires" badge | owner | accepted | 2026-09-26 | 01 §9; 23 §13 |
| [D004](D004-v1-scope.md) | v1 = faithful editor + Preview + Wilco + the campaign flow | owner | accepted | 2026-09-26 | README; 34 OQ6 |
| [D005](D005-north-star-xcom-like-campaign.md) | North star: an XCOM-like real-time campaign, "Operation Grey Heron" | owner, research | accepted | 2026-09-27 | 29 §8 |
| [D006](D006-product-scoped-agent.md) | The AI agent is product-scoped | owner (`AGENTS.md`) | accepted | 2026-09-26 | 21; 22; 24 |
| [D007](D007-plugin-tiers.md) | Plugin tiers T0 packs, T1 WASM, T2 remote connectors | owner | accepted | 2026-09-27 | 22 |
| [D008](D008-outbound-network-sources.md) | Outbound network: provider, enabled plugins, user-enabled sources; `feed` connectors | owner | accepted | 2026-09-27 | DG028; 42 §3–§5 |
| [D009](D009-campaign-first-weak-model-harness.md) | Campaign creation first-class; the harness carries the weight | owner (`AGENTS.md`) | accepted | 2026-09-26 | 25; 21 |
| [D010](D010-glass-box-generation.md) | Nothing the AI makes is a black box | owner (`AGENTS.md`) | accepted | 2026-09-26 | 25 §9; 38 §5 |
| [D011](D011-realism-default-not-wall.md) | Realism and common sense are defaults, never walls | owner (`AGENTS.md`) | accepted | 2026-09-27 | 39 §5.1; 41 §6 |
| [D012](D012-maximum-within-engine.md) | Maximum within the engine; gaps become engine requests | owner (`AGENTS.md`) | accepted | 2026-09-27 | 18 §9; 29 §7 |
| [D013](D013-port-upstream-tests.md) | Port upstream tests with the code | owner (`AGENTS.md`) | accepted | 2026-09-26 | 20 |
| [D014](D014-public-repo-hygiene.md) | Public-repository hygiene and our own words | owner (`AGENTS.md`) | accepted | 2026-09-26 | `AGENTS.md`; 02 |
| [D015](D015-no-code-ladder.md) | No-code first, scripting always available | owner | accepted | 2026-09-27 | 31; 32; 37 |
| [D016](D016-ui-stack.md) | UI stack: egui shell and our own classic 2D renderer | research | baseline | 2026-09-26 | 06 |
| [D017](D017-format-crates-lossless-cst.md) | Format crates, a lossless CST and raw-byte strings | research | baseline | 2026-09-26 | 04; 07 |
| [D018](D018-preview-in-the-real-game.md) | Preview launches the user's real game | research | baseline | 2026-09-26 | 01; 08; 24 |
| [D019](D019-skills-standard-skill-md.md) | Skills use the standard SKILL.md format | owner | accepted | 2026-09-27 | 22 §2.1; 30 |
| [D020](D020-templating-minijinja.md) | Templating with minijinja | owner | accepted | 2026-09-27 | 22 §2.1; 31 |
| [D021](D021-provider-layer.md) | Provider layer: own the seam, rent the wires | research | baseline | 2026-09-26 | 12; 14 §7 |
| [D022](D022-local-inference-and-model-manager.md) | Local inference path and the Model Manager; the managed `llama-server` sidecar is the primary runtime (amendment note, 2026-09-27) | owner, research | accepted (the runtime path was a baseline until the owner's 2026-09-27 amendment) | 2026-09-27 | 13; 14; 46; 47 |
| [D023](D023-model-strategy.md) | Model strategy: no bundled weights, bring your own model, qualified local tiers | owner, research | accepted | 2026-09-26 | 14; 16 |
| [D024](D024-effort-autonomy-role-binding.md) | Effort, autonomy and role binding are three separate dials | owner (DG013), research | accepted | 2026-09-27 | DG013; 21 §7 |
| [D025](D025-workflows-as-data-and-journal.md) | Workflows are typed data; runs keep a decision journal | research | baseline | 2026-09-27 | 38 |
| [D026](D026-token-economy.md) | Saving users' API costs is a usability requirement | owner, research | accepted | 2026-09-27 | 40 |
| [D027](D027-knowledge-stack.md) | Knowledge stack: deterministic actions, Teller facts, a small primer | research | baseline | 2026-09-27 | 30 |
| [D028](D028-standing-orders-and-drill.md) | Standing Orders and Drill | owner | accepted | 2026-09-27 | 33 |
| [D029](D029-easy-advanced-and-labels.md) | Keep the Easy/Advanced switch and the original labels | owner (DG033) | accepted | 2026-09-27 | DG033; 33 |
| [D030](D030-mod-handling.md) | Mods: first-class mod sets; integrate, never host | research, owner (DG028) | baseline | 2026-09-27 | 27; 42 |
| [D031](D031-generated-content-permission-and-licence-scope.md) | Generated-content §7 permission with a coverage list; GPL-3.0-or-later for docs and the plugin SDK; no GPL-3.0-only ports by default | owner (OWQ-01–04) | accepted | 2026-09-27 | 02 §6; 22 §5; 45 |
| [D032](D032-contribution-terms-dco.md) | Contribution terms: DCO, no CLA; AI assistance allowed with a human sign-off; `Assisted-by:` optional | owner (OWQ-05) | accepted | 2026-09-27 | 02 §10.5 |
| [D033](D033-campaign-extension-overlays.md) | Extension overlays: shareable extension-only for Bohemia's campaigns; licence or permission for third-party ones | owner (OWQ-06) | accepted | 2026-09-27 | 34 cw13; 19 §7.6 |
| [D034](D034-descriptor-placement-and-names-delegation.md) | Descriptor placement (DG002 A, `AGENTS.md` amended); clearance and rename before release; pending names delegated | owner (OWQ-07, OWQ-08) | accepted | 2026-09-27 | DG002; 02 §9 |
| [D035](D035-outreach-and-security-disclosure.md) | Outreach and private disclosure: security reports first; one letter to Bohemia; CE #35 first; mod channels with a non-objection rule | owner (OWQ-09–12) | accepted | 2026-09-27 | 24; 02 §11; 01 §9; DG029 |
| [D036](D036-v1-contents-and-release-split.md) | v1 contents: classic patterns, probe-cleared modules, minimal CLI, English first, Cutscene node, MCP server; Grey Heron v1.1, timeline v1.2 | owner (OWQ-13–15) | accepted | 2026-09-27 | 26 §9.4; 29; 31 §4.6; 33; 38 §9 |
| [D037](D037-model-manager-recommended-list.md) | Model Manager recommends only OSI-licensed, unrestricted, qualified models; everything else is "custom" and "unqualified" until qualified | owner (OWQ-19) | accepted | 2026-09-27 | 02 §8; 46; 47 §5 |
| [D038](D038-mod-handling-owner-additions.md) | Mods: launch-to-install, directory freshness, CC-BY-SA editor-only, registry operator, extended addon set by default | owner (OWQ-17, OWQ-18) | accepted | 2026-09-27 | DG030; 42; 27 |
| [D039](D039-engagement-ethics.md) | Engagement ethics (doc 36 cv43) as a product rule; a challenge catalogue with no calendar, streak, reward or reminder | owner (OWQ-20) | accepted | 2026-09-27 | 36 cv43; 43 §3.7 |
| [D040](D040-play-seeds-and-memory.md) | Fresh play seed by default; memory across playthroughs opt-in; no re-roll on restart in v1 | owner (OWQ-21) | accepted | 2026-09-27 | 43; 29 SL11; DG038 |
| [D041](D041-moral-choice-suggestion-boundaries.md) | A short boundary list, in Standing Orders, for generated moral-choice suggestions; user content never filtered | owner (OWQ-22) | accepted | 2026-09-27 | 28 FP48, OQ8 |
| [D042](D042-strategic-layer-commander-and-triage.md) | Strategic layer: commander design a campaign setting (plot armour default); triage disclosed in the debrief | owner (OWQ-23) | accepted | 2026-09-27 | 29 OQ5–OQ6; 36 cv07 |
| [D043](D043-cross-plugin-chaining-in-workflows.md) | Cross-plugin chains only in first-party and user-authored workflows, with the egress card every time; never exposed externally | owner (OWQ-16 = DG014 B) | accepted | 2026-09-27 | DG014; 22 §3; 38 |
| [D044](D044-cloud-first-model-screening.md) | Cloud-first screening: a local candidate is first tested on a hosted copy of its weights and tried locally only if promising; the protocol is a proposal; spend and schedule (OWQ-27) in its amendment note (2026-09-28) | owner (direction of 2026-09-27; OWQ-27 b) | accepted | 2026-09-27 | 50 §5; 47 §6; 48 §6.0 |
| [D045](D045-free-model-offer-policy.md) | Free models: "connect a free model" presets on the user's own account (OpenRouter PKCE first); no Plotroom key, proxy or keyless default; offered only where terms allow and qualified per step kind, dated and re-qualified, with a clean fallback; preset list fixed at release | owner (OWQ-24 b; direction of 2026-09-27) | accepted | 2026-09-28 | 50 §1–§4, §6; 48 §7.4 |
| [D046](D046-aggregators-as-first-class-providers.md) | Aggregators are first-class providers: pinned route, ZDR and no data collection by default, serving host shown per call, per-key host allow-list, re-probes; DG039 open | owner (OWQ-25 a) | accepted | 2026-09-28 | 48 §2.5–§2.6, §7.1, §7.4, OQ10; 50 §4 |
| [D047](D047-military-use-policy-models-and-services.md) | Models and services whose policies ban military uses or violent content: synthetic tests only, never recommended or preset; the NVIDIA trial and Z.ai not used; no combat-flavoured items to hosts with violent-content clauses | owner (OWQ-26 a) | accepted | 2026-09-28 | 48 OQ9, O3; 50 §2.3, §5.9 |
| [D049](D049-friction-review.md) | Friction review in every design and implementation change, for people, models and contributors: remove before explaining, measure, record in `docs/friction/`; invariants stay | owner (direction of 2026-09-28) | accepted | 2026-09-28 | AGENTS.md |
| [D048](D048-per-model-harness-presets.md) | Per-model harness presets: the harness adapts to each model per step kind (how Wilco asks, never what code owns); no fine-tuning; tuned on a tuning split, accepted on held-out; bound to model file, runtime and template; badges per preset and step kind; visible and overridable; a general fallback preset | owner (direction of 2026-09-28) | accepted | 2026-09-28 | 44, 46, 49, 51, 53, 55 |

### Records refined on 2026-09-27

| Earlier record | Refined by | What the refinement settles |
| --- | --- | --- |
| D001 | D031, D032, D033 | OWQ-01 to OWQ-06: licence follow-ups, contribution terms, extension overlays |
| D002 | D034 | Descriptor placement (replaces the surfaces listed in D002 item 1), clearance, rename, delegated names |
| D003, D012, D018 | D035 | Outreach to CWR-CE and Bohemia and the private security reports (OWQ-09 to OWQ-11); the actions are still to be done |
| D004 | D036 (and D004's amendment note) | The size of v1 (OWQ-13 to OWQ-15) |
| D005 | D036, D039, D042 | Grey Heron in v1.1; engagement ethics; commander design and triage |
| D006, D025 | D036, D043 | External agents in v1 and `workflow.decide` after v1 (OWQ-15); cross-plugin chains (OWQ-16) |
| D007 | D031, D038, D043 | The SDK licence (OWQ-03), the registry operator (DG030 item 4), cross-plugin chains (DG014) |
| D008 | D035, D038 | The channel maintainers' outreach and non-objection rule (DG029); directory freshness (DG030 item 2) |
| D011 | D034, D041 | How the realism levels get their names (OWQ-08); the boundary list for generated moral choices (OWQ-22) |
| D015, D028 | D036 | Which modules ship in v1; Standing Orders and Drill content and locales (OWQ-14) |
| D019, D029 | D034 | How pending user-facing names are chosen (OWQ-08) |
| D022, D023 | D037 (and their amendment notes) | The recommended-model policy (OWQ-19); D022's note also records the owner's runtime choice |
| D030 | D033, D035, D038 (and D030's amendment note) | OWQ-06, DG029, DG030 and OWQ-18 |

Each earlier record above carries the pointers in its header's **Open parts** and a dated note at its end (lifecycle item 5).

### Records refined on 2026-09-28

| Earlier record | Refined by | What the refinement settles |
| --- | --- | --- |
| D021 | D045, D046 | Free-model presets as provider data (OWQ-24); aggregators as first-class providers with safeguards (OWQ-25, doc 48 OQ10) |
| D037 | D047 (D045 related) | Whether Plotroom's own evaluations may test models whose policies ban military uses (doc 48 OQ9 = OWQ-26); the same principle for services and presets |
| D044 | D047 and D044's amendment note | OWQ-26; OWQ-27's spend and schedule |

D021 and D037 had no open part to mark, so each carries only a dated note at its end; D044's header **Open parts** gained pointers.

## Integration items this folder owns

These proposals from later research docs, aimed at earlier designs, are owned here:

- Doc 17 §16 and §15 row 11 (adopt decision records with a short capsule each): this folder and its template. The retrieval index for
  agents that doc 17 also suggests belongs to `docs/README.md`, not here.
- Doc 42 §8.3 row 22 (decide the `feed` connector kind): D008.
- Doc 40 R1 (prices are dated data in `models.toml`): D026; the doc 14 §7 edit is a folding step.
- Doc 38 §4.7 (workflow definitions replace doc 25 §4.2's `Stage` enum) and §3.4 (whole-run turn ceiling): D025; the doc 21 and doc 25
  notes are folding steps.
- Doc 34 §5.2 row 02 (licence items, including shared extension overlays): D001, D031 and D033 (OWQ-06).
- Doc 29 §6 (register pattern P9 with docs 26 and 19): D005.

## Verification notes

### Consolidation pass (2026-09-27)

- Created this folder, D001–D030 and `OWNER-QUESTIONS.md`. Owner decisions were taken from `AGENTS.md`, the README, the decided DGs
  (DG013, DG028, DG033 items 3–4) and the decision notes in the research docs' verification sections; research baselines from each
  doc's TL;DR and recommendation sections, re-read on 2026-09-27. Owner decision dates are the days the owner decided; baseline dates
  are the research dates.
- No research doc, DG or `AGENTS.md` was edited by this step. `docs/README.md` (named in `AGENTS.md` as the start of `docs/`) does not
  exist yet and should link here when it is written.

### Consistency review (2026-09-27)

- `docs/README.md` now exists and links here. Checked the records against `AGENTS.md`, the architecture and the roadmap. Two
  clarifying notes were added at the end of records, without changing any decision: D002 (descriptor placement: `AGENTS.md` versus
  DG002's recommendation) and D026 (the same-model escalation stays DG022's call). OWQ-07 gained a "Conflict to resolve" line for the
  same placement question, and OWQ-14 gained a rung-4 item: whether the cinematics timeline (D015 item 4) ships in v1, which the
  architecture and roadmap had deferred to v1.2 without an owner question.

### Owner answers (2026-09-27)

- The owner answered all 23 owner questions on 2026-09-27, each with its recommended option; the dated Answer lines are in
  `OWNER-QUESTIONS.md`. The durable rules became D031–D043, written from those Answer lines, the questions' option texts and the
  sources each record cites, re-read on 2026-09-27. Record numbers follow the grouping below, not the strict order of the questions.
- Grouping: licences (OWQ-01–04) in D031; contributions (OWQ-05) in D032; overlays (OWQ-06) in D033; names (OWQ-07–08) in D034;
  outreach (OWQ-09–12) in D035; v1 contents (OWQ-13–15) in D036; the recommended-model policy (OWQ-19) in D037; mods (OWQ-17–18) in
  D038; player-facing rules (OWQ-20–23) in D039–D042; cross-plugin chains (OWQ-16) in D043. Four DGs are decided through these
  answers: DG002 (D034), DG029 (D035), DG030 (D038) and DG014 (D043); their "Decision record" sections are a folding step.
- The owner's runtime choice of the same day (the managed `llama-server` sidecar as the primary local runtime, GGUFs pulled from
  Hugging Face by pinned revision and SHA-256, Ollama and LM Studio as optional bring-your-own endpoints; evidence in doc 46) is not
  an owner question. It is recorded as D022's amendment note, which D037 builds on. The owner's deferral of doc 48's cloud test round 1
  until doc 49's local results are in is a scheduling choice, noted in D021's amendment note, and needs no record.
- Lifecycle item 5 (refines: a new record or an amendment note) and the template's **Refines:** field were added in this step, so that
  records written the same day in both forms follow one written rule. Records D001–D030 were not edited here; their pointers to the
  refining records are a folding step (see "Records refined on 2026-09-27").
- Decisions that stay open inside the new records are listed under each record's **Open parts**: the legal review before 1.0 (D031),
  the clearance search and the names table (D034), all outreach still to be sent (D035), probe results for v1 modules (D036), the first
  qualified models (D037, doc 49), DG038's SL11 wording (D040) and the owner's confirmation of D042 after the first balance-lab runs.
  No outreach was made and no legal advice is given.

### Consistency review of the owner answers (2026-09-27)

- Checked `OWNER-QUESTIONS.md`, D031–D043, the decided DGs, `AGENTS.md`, the architecture, the roadmap and D004/D021–D023/D030
  against each other. The folding step for older records is done: D001–D008, D011, D012, D015, D018, D019, D025, D028, D029 and D030
  gained header pointers and a dated note naming their refining records (lifecycle item 5, which now states that header pointers are
  the only header change allowed). D022 and D023 name D037 where they had the placeholder "the OWQ-19 record", and their doc 46
  figures carry doc 46's own qualifiers (one Pascal card; Ollama's backend not logged; the memory saving is measured against
  Ollama's builds with vision parts; spike checks per step kind). No decision changed.

### D044 and OWQ-24 to OWQ-27 (2026-09-28)

- The owner's direction of 2026-09-27 (screen local candidates in the cloud first; try locally only if promising) became D044, with
  its protocol marked as a proposal from doc 50 §5. Its other direction (a free service Plotroom could preconfigure or offer) is an
  owner question, OWQ-24, beside OWQ-25 (aggregators, doc 48 OQ10), OWQ-26 (military-use policies, doc 48 OQ9) and OWQ-27 (screening
  spend and schedule). D021–D023 and D037 were not edited; their pointers are a folding step once the questions are answered.

### Owner answers to OWQ-24 to OWQ-27 (2026-09-28)

- The owner answered OWQ-24 to OWQ-27 on 2026-09-28, each with its recommended option, and gave a further direction dated
  2026-09-27: "offer the user the free models that work perfectly with our harness". The records were written from the Answer lines,
  the questions' option texts, that direction, docs 48 and 50, and D008, D021–D023, D037 and D044, re-read on 2026-09-28.
- D045 (OWQ-24 with the direction), D046 (OWQ-25) and D047 (OWQ-26) are new records, because each answer adds rules of its own
  (lifecycle item 5). OWQ-26 became a record rather than a D037 note: D037 covers local files only, and the answer adds rules for
  tests, hosted services and item routing. OWQ-27 is a one-off spend and schedule decision, so it is D044's amendment note.
- Pointers: D021 and D037 gained dated notes (they had no open part to mark); D044 gained header pointers and its note;
  `OWNER-QUESTIONS.md`'s Summary names the records; docs 48 and 50 gained dated pointers beside their open questions and
  recommendations. D022 and D023 are related, not refined, and were not edited. DG039 (downstream hosts behind an aggregator) was
  filed as OWQ-25's answer asked; D046 lists it as open and does not decide it.
- Plotroom's D047 is unrelated to Iron Curtain's decision D047, which docs 12, 13, 14, 17 and 34 cite by path or as "D047" in
  context ("Numbering and labels").
- Not legal advice. No provider was contacted, no account or key was created, and nothing was bought.

### Verification of the OWQ-24 to OWQ-27 fold (2026-09-28)

- Checked each Answer line against `OWNER-QUESTIONS.md`'s Summary, D044's note, D045–D047, DG039 and its index row, and the pointers
  in D021, D037 and docs 47, 48 and 50. No answer is contradicted and no decision changed.
- Places where a record stated a proposal as settled were reworded: D045 item 5 and D046's Consequences no longer fix the identity
  tuple of a cloud setup or the probe's contents, which stay proposals and open parts (doc 48 §7.4 items 1 and 3); D045 no longer
  cites D047 for qualification in general, and its "attribution headers off" line joined the listed proposals. D045's open parts
  now separate the re-qualification cadence (doc 48 OQ11) from its triggers (DG012). D044's note gives the card fee as $0.80 (the
  minimum), as OWQ-27 does. DG039 no longer says the owner declined OWQ-25's reading (the Answer line is silent on it), and its
  "Blocks" no longer covers the pinned route's serving host, which every option names and D045's card shows.
- Pointers added where the fold had missed them: doc 48 §3.2 (Muse-Glimmer row) and §7.1; doc 50 §5.7 and §6's D021 bullet; doc 47
  §6's "See also" (OWQ-27 answered). Each doc's verification notes say so.
- Relative links in this folder, `docs/design-gap-requests/` and docs 48 and 50 resolve (179 checked). `docs/README.md` still lists
  D001–D043, DG001–DG038 and OWQ-01–OWQ-23; updating it is left to the change that maintains that file.
