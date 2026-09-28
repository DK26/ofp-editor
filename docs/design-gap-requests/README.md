# Design-gap requests

A **design-gap request** (DG) records a place where Plotroom's own design is missing a detail, contradicts itself, or has no
workable path. `AGENTS.md` ("Design Authority") forbids inventing behaviour silently in that case: the gap is filed here, and
any local work that depends on it is marked `implementation placeholder`, `proposal-only` or `blocked on <decision>` until the
request is decided.

Design-gap requests are about **this project's design**. Gaps in the **game engine** are engine requests. They belong in the
engine-requests register under `docs/upstream/` (`AGENTS.md`, "Maximum Within the Engine; Gaps Become Engine Requests"). A DG
may point to engine requests, for example when a doc routed engine defects to the wrong place (DG034).

## Lifecycle

| State | Meaning | What changes |
| --- | --- | --- |
| `open` | Filed. Context, options and a recommendation marked *proposal* are recorded. Nothing is decided | Dependent work stays `proposal-only` or `blocked on DGnnn` |
| `decided` | The decider chose an option (or a variant of one). The file records the date, who decided, the choice and the reason | Affected docs are not yet updated |
| `folded` | Every affected doc now states the decision, points to the DG and carries a dated verification note | The DG file stays as the record; later readers follow its pointers |
| `withdrawn` / `superseded by DGnnn` | The gap turned out not to exist, or another DG absorbed it | Pointer to the reason or the successor |

- **Owner decisions** cover product scope, user-facing names, security and network boundaries, licensing and legal matters, and
  public outreach. Only the owner moves such a request to `decided`. Owner-level requests are asked in
  [`docs/decisions/OWNER-QUESTIONS.md`](../decisions/OWNER-QUESTIONS.md); the owner's dated answer there is written into the request's
  header and "Decision record" section.
- The owner may delegate such a choice. A request decided under the owner's delegation says so in its header and "Decision record"
  section, names the record that states the choice, and may be overruled by the owner on return (DG039, DG041, DG050, DG052 and
  DG057 on 2026-09-28).
- A decided request whose answer sets a durable, project-level rule also gets a decision record (`Dnnn`, see
  [`docs/decisions/README.md`](../decisions/README.md)); the request's "Decision record" section then summarises that record and links
  to it. Either way the "Decision record" section is never left reading "Open" once the header says `decided`.
- **Technical decisions** are made in the design round from the evidence each request names (tests, benchmarks, probes) and are
  recorded in the same file.
- Never delete a DG file and never reuse a number. A decision that is later reversed gets a new DG that supersedes the old one.
- A recommendation in an `open` request is a proposal, not a decision. Docs may cite it only as "proposed in DGnnn".

## Naming

`DGnnn-short-slug.md`: `DG`, three digits, a hyphen, and a lowercase kebab-case slug of at most six words. Numbers are assigned
in filing order by this index, which is the source of truth. DG001 was filed before this index existed and keeps its file name
(`DG-preview-non-aborting-launch.md`) until the change that renames it also updates the references to it in doc 08 (§4.4 and its
verification notes).

## Template

```markdown
# DGnnn: <title>

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed <date> in <pass or change>. Status: **open**.
> **Decision by: owner | technical** (<who or which evidence>). Blocks: <what stays proposal-only or blocked until decided>.

## Context
<Source docs and sections, with a one-line summary of what each says.>

## The gap
<The contradiction or the missing "how", stated so a reader without the source docs understands it.>

## Options
| # | Option | For | Against |
| --- | --- | --- | --- |

## Recommended resolution (proposal)
<The option this request recommends and why. Always marked proposal until decided.>

## What it would change
<The concrete edits per affected doc, code area or test once decided.>

## Affected docs
<List.>

## Decision record
<"Open" while open. Once decided: date, decider (and the OWQ-nn or Dnnn it comes from), chosen option, reason, what stays open,
and the folding steps that move the request to `folded`.>

## Verification notes

### <pass name> (<date>)
- <What was read to file this, and what was not re-checked.>
```

## Index

| ID | Title | Decision by | Status | Main sources |
| --- | --- | --- | --- | --- |
| [DG001](DG-preview-non-aborting-launch.md) | A non-aborting Preview launch for the debug console | technical + probe | open | 31 §7.4, 08 §4.4 |
| [DG002](DG002-product-name-and-subtitle.md) | Where the product name and its descriptive subtitle may appear | **owner** | decided 2026-09-27 (OWQ-07: option A; `AGENTS.md` amended to match; D034) | 02 §9, §11 |
| [DG003](DG003-attribute-vocabulary.md) | One canonical vocabulary for attributes and presets | technical | open | 37 §10 (g), 31 §3, mission-primer idioms |
| [DG004](DG004-module-vocabulary.md) | What "module" means: mission, persistence and strategic modules | technical | open | 31 §4.1, OQ9; 26 §5.2; 29 §3.1 |
| [DG005](DG005-code-registry.md) | One registry for lint, pattern and other codes | technical | open | 34, 36, 39, 41, 42, 43 headers; 21; 29; 33; 37; 40 |
| [DG006](DG006-menu-size-cap.md) | Weak-model menu cap: 5 or 7 options | technical (bench E4) | open | 25 §5.1, OQ1; 26 OQ6; 29 §6.2 |
| [DG007](DG007-one-definition-format.md) | One on-disk format for workflows, recipes, modules and rules | technical | open | 38 OQ1, §6.1; 21 §6.1, OQ7; 22 OQ9; 31 OQ8; 17 §10; 34 mo22 |
| [DG008](DG008-condition-language.md) | One condition language for campaign, mission and workflow scopes | technical | open | 19 §5; 31 OQ10; 38 §3.1, OQ6 |
| [DG009](DG009-rung-4-engine-facts-owner.md) | Which doc owns the cinematic engine facts: 31 §6 or 32 §2 | technical | open | 31 verification "Open" (1); 32 reviews |
| [DG010](DG010-resume-and-replay-wording.md) | Resume reuses settled entries; one meaning for "replay" | technical | open | 38 §4.3, OQ3; 21 §6.2, §8.2; 25 §4.2 |
| [DG011](DG011-admission-wrapper-name.md) | `Admitted<T>` or `Checked<T>`, and what a changed read does | technical | open | 21 §1.2, OQ1; 25 §4.2; 38 OQ4 |
| [DG012](DG012-requalification-triggers.md) | Which prompt, lens or exemplar changes void a qualification | technical | open | 38 OQ5, §3.5; 21 §12.3 |
| [DG013](DG013-user-gates-effort-or-autonomy.md) | User gates: set by effort or by autonomy | **owner** | decided 2026-09-27 (option B; D024) | 38 OQ12, §5.4, §8.1; 25 §5.2; 21 §7; 14 §8 |
| [DG014](DG014-cross-plugin-chaining.md) | May one plugin's output feed another plugin's egress in a workflow | **owner** | decided 2026-09-27 (OWQ-16: option B; D043) | 38 OQ13; 22 §3.1–§3.2 |
| [DG015](DG015-pick-answer-schema.md) | `DecisionSpec.schema` must not be declarable for Pick | technical | open | 38 §3.3, §4.7; 40 R4–R5, §4.1 |
| [DG016](DG016-budget-and-repair-accounting.md) | How turns, repairs, reservations and retries are counted | technical | open | 38 §3.4, §4.3, §4.5–§4.6, §7; 40 §6–§7; 25 §7.2; 21 §6.2 |
| [DG017](DG017-journal-storage-and-retention.md) | Journal storage, atomic save, retention and export stripping | technical | open | 38 §4.2, OQ2, OQ10; 25 OQ10 |
| [DG018](DG018-third-party-port-records.md) | Where records of ported permissive-licence code live | technical | open | 38 §1.2, OQ9; 02 §10.4 |
| [DG019](DG019-static-first-capsule-order.md) | Capsule order: static first, or exemplars next to the question | technical (measure) | open | 40 G1, §4.1, R2–R3; 25 §4.4, §4.6; 21 §8.1; 38 §3.3 |
| [DG020](DG020-reasoning-effort-table.md) | One measured reasoning-effort table per shape and provider | technical (measure) | open | 40 G2, R6; 21 §7.1; 25 §4.4; 14 §8; 12 §3.3 |
| [DG021](DG021-adaptive-candidates-k.md) | K candidates cost money on cloud setups: adaptive K | technical | open | 40 G3, R7; 25 §5.2 |
| [DG022](DG022-same-model-effort-escalation.md) | Same-model effort re-run versus "never upward" | technical (doctrine wording) | open | 40 G4, R6; 25 §3, §10.2; 21 §1.4, §6.2; 12 §5.7 |
| [DG023](DG023-fixed-tool-set-per-mode.md) | A fixed tool set per mode instead of per-turn `active_tools` | technical | open | 40 G5, R5; 12 §3.1; 21 §6.2 |
| [DG024](DG024-fixed-cloud-schemas.md) | No per-request dynamic enums in cloud schemas | technical | open | 40 G6, R5; 30 §4.5 |
| [DG025](DG025-cloud-prompt-budget-and-cache-minimum.md) | The cloud (T3) capsule budget and provider cache minimums | technical | open | 40 G7, R11, §2.3; 25 §4.4 |
| [DG026](DG026-candidate-diversity-without-temperature.md) | Candidate diversity when `temperature` is rejected | technical | open | 40 G8, R7; 21 §7.1; 25 §7.3; 38 §3.3 |
| [DG027](DG027-warm-first-fan-out.md) | Warm-first fan-out and llama.cpp slots | technical | open | 40 G9, R9, R14; 38 §4.5 |
| [DG028](DG028-t2-read-only-catalog-feeds.md) | Read-only catalog feeds and registry traffic | **owner** | decided 2026-09-27 (B + R1; D008) | 42 §3.4, §5.1, OQ3; 22 §2.3, OQ4; AGENTS.md |
| [DG029](DG029-mod-channel-outreach.md) | Outreach to the mod-channel maintainers | **owner** | decided 2026-09-27 (OWQ-12: option A and the non-objection rule; D035); outreach not yet sent | 42 OQ1–OQ2, §4.2, §8.1 |
| [DG030](DG030-mod-distribution-open-decisions.md) | Open decisions on mod install hand-off, directory freshness, CC-BY-SA and the registry operator | **owner** | decided 2026-09-27 (OWQ-17: all four proposals; D038) | 42 review "Still open", OQ8–OQ9; 34 OQ6 |
| [DG031](DG031-concept-id-scheme.md) | Flat or dotted ids for Standing Orders entries and cards | technical | open | 33 OQ11, finding 10, §3.1–§3.4; 30 §4.6; 38 §3.5 |
| [DG032](DG032-reference-tool-family.md) | One knowledge store and one tool family | technical | open | 30 OQ7, §4.4; 33 §6.1, OQ10; 21 §10.2; 23 |
| [DG033](DG033-standing-orders-phase-0.md) | Standing Orders phase-0 decisions (schema, demos, Easy/Advanced, relabels) | technical; **owner** for items 3–4 | items 3–4 decided 2026-09-27 (D029); 1–2 open | 33 §9 phase 0, OQ2–OQ3 |
| [DG034](DG034-camera-engine-defects-routing.md) | Camera and effects engine defects: route to the engine-requests register | technical | open | 32 §2.9, §3.7; 31 §10; AGENTS.md |
| [DG035](DG035-cutscene-director-sibling-changes.md) | Cutscene Director changes asked of sibling docs | technical | open | 39 §1.2, §9.3, OQ7 |
| [DG036](DG036-atmosphere-sibling-corrections.md) | Atmosphere and audio corrections to docs 32, 34, 35 and the catalog | technical | open | 41 §2.5, §5.2; 34 ed12; 35 rc08, rc43 |
| [DG037](DG037-director-feature-names.md) | One word, six features: names for the "Director" features | design round (OWQ-08 answered: the owner delegated pending names and reviews the names table) | open | 39 review "Names"; 41 §3; 32 §3.3; 33 §5.4; 34 ed18 |
| [DG038](DG038-sl11-engine-random-exceptions.md) | Engine `random` and SL11: the play-seed bootstrap and opt-in re-roll on restart | technical (OWQ-21 answered: re-roll (a), no exception in v1) | open | 43 §3.2, §2.5, OQ2–OQ3; 29 SL11; 36 OQ2 |
| [DG039](DG039-downstream-hosts-behind-aggregators.md) | Downstream hosts behind an aggregator: what "the model provider the user configured" covers | **owner** (network boundary) | decided 2026-09-28 (owner's delegation: option B; D053) | 48 §7.4 item 2, §7.1, §2.6, OQ2; 50 §4; D008; D046 |
| [DG040](DG040-bounded-repeat-until-step.md) | A bounded "repeat until" step with a code-checked condition and a hard maximum | technical (the owner reviews; amends D025 decision 2) | open | the owner's dynamic-workflow additions; 38 §3.2, §4.5, §7; D025; 21 §1.4, §8.2; 56 WR5 |
| [DG041](DG041-verification-panel-for-creative-steps.md) | A verification panel for strong models on creative work, opt-in by effort | technical; **owner** for a reviewer role | decided 2026-09-28 (owner's delegation: option B; D054) | the owner's dynamic-workflow additions; 25 §2.5, §7.3; 38 §3.3; 21 §1.4; D024; D026 |
| [DG042](DG042-plan-draft-format-and-saved-plans.md) | Dynamic authoring, static execution: the `PlanDraft` format, its checks and where saved plans live | technical (the principle is [D051](../decisions/D051-capability-ladder-freedom-by-qualification.md) item 9) | open | the owner's dynamic-workflow additions; 63 §8, §13 items 9–10; 38 §6.1 |
| [DG043](DG043-repair-turn-shape-and-content.md) | The repair turn: capsule shape, which finding goes in, and repair versus resample | technical (measure) | open | 51 §4.6, §6.1 item 9; 57 TE-G3, §6.3; 61 §6 items 1, 3, 7, 13; 62 §10 item 8 |
| [DG044](DG044-wording-and-profile-hashes-in-keys.md) | Question wording, model profile and language in the qualification and calibration keys | technical | open | 60 §4 items 1, 10; 55 §7 item 1; 63 §13 item 3; 51 §4.8; D051 item 4; DG012 |
| [DG045](DG045-model-profiles-beside-harness-presets.md) | Model profiles beside harness presets: where probed facts about a model live | technical | open | 51 §4, §6.1 items 1, 5–6; 55 §7 item 10, OQ1; D048 |
| [DG046](DG046-leading-why-doctrine-or-knob.md) | The leading `why`: doctrine for every Pick and Fill, or a per-model knob | technical (measure: 53 R7) | open | 53 R7; 55 §7 item 8; 59 §7 items 5–6; 60 §4 item 11 |
| [DG047](DG047-decompositions-and-forms-for-pick-fill.md) | Authored decompositions and question forms for Pick and Fill | technical | open | 55 §7 item 2; 59 §7 items 1, 7; 60 §4 items 3–5 |
| [DG048](DG048-answer-schema-identity-and-compiler.md) | Answer schema identity per harness preset, and one schema compiler | technical | open | 55 §7 items 3, 6; 51 §6.1 items 8, 14; DG015; DG024 |
| [DG049](DG049-named-capsule-layouts.md) | A small set of named capsule layouts that harness presets choose from | technical (measure) | open | 55 §7 item 5; 51 §6.1 item 11; 57 TE-G1; 52 RG6; 60 §4 items 6–7; DG019 |
| [DG050](DG050-second-stage-escalation-on-low-confidence.md) | Escalation to a second bound stage when the first is unsure | **owner** | decided 2026-09-28 (owner's delegation: option B; D055) | 53 §4.3, OQ2; 55 §7 item 9; 56 §10 item 6; 58 OQ4; D023; D050 |
| [DG051](DG051-provider-seam-outcome-taxonomy.md) | One outcome taxonomy at the provider seam | technical | open | 51 §4.5–§4.7, §6.1 items 2–5; 52 §5.2, RG2; D050 item 4; DG016 |
| [DG052](DG052-encoder-runtime-for-components.md) | A runtime for non-generative encoder components | **owner** (after spike S-ENC) | decided 2026-09-28 (owner's delegation: option A now, tier H only if S-ENC meets doc 58's bar; D056) | 53 §4.9; 58 §4.11 item 2, OQ2; D022 |
| [DG053](DG053-journal-record-kinds-and-ownership.md) | New journal record kinds, and one owner per journal | technical | open | 56 §10 items 2, 4; 57 TE-G4–G5; 58 §4.11 item 4; 59 §7 item 4; 63 §13 item 6; DG017 |
| [DG054](DG054-stakes-floors-per-decision-kind.md) | Stakes floors per `DecisionKind` that no preset can lower | technical (who sets them: owner or technical) | open | 60 §2.8, P-09, §4 item 2, OQ2; D048 item 2; D051 item 3 |
| [DG055](DG055-grant-witness-name-and-crate.md) | The grant witness: one name, one scope, one crate | technical | open | 63 §9.2, §9.4, §13 item 7; 62 §6.3, §10 item 7; D051 |
| [DG056](DG056-model-facing-result-envelope.md) | One envelope, sanitiser and diagnostic contract for model-facing tool output | technical | open | 57 TE-G9, TM1–TM3; 61 §6 item 2; 62 §10 item 4 |
| [DG057](DG057-component-bindings-and-visibility.md) | Bindings, badges and kill switches for non-generative components | **owner** | decided 2026-09-28 (owner's delegation: option B; D057) | 58 §4.11 items 1, 5, OQ3; D024 item 4 |
| [DG058](DG058-endpoint-verification.md) | Endpoint verification: behavioural probes, "Check this endpoint" and "last verified" | technical | open | 51 §6.1 item 10, K1–K4, K20, OQ12; 48 §7.4 items 3–4; 50 §6; D045 item 5 |
| [DG059](DG059-config-patch-witness-surface.md) | The witness surface of config span patches (lexemes, value references, `Patched`, `ByteEdit`) | technical | open | core-document-model §3.1, §4, §12; 04 §12.3; SP-09 |
| [DG060](DG060-generated-content-permission-text.md) | The exact text of the generated-content permission in `NOTICE` | **owner** | open | D001 item 4; D031 item 1; 02 §6.2, §10.1 |

## Candidates noticed but not filed in this pass

- **Cutscene-section staging** (doc 32 §7 phase 0; doc 08 verification notes): the staged-Intro refinement is listed as a design
  gap, but no request exists yet.
- **Workflow definitions replace doc 25's `Stage` enum** (doc 38 §4.7 and W0): needs a doc 25 note and a request.
- **Generated file names built from labels** (doc 31 verification notes, "Open" item 7): rename-follows-references or freeze at
  first export.
- **Doc 39 §1.2 sibling changes**: filed as DG035 once doc 39 was final (docs 39, 41 and 43 step, below).
- **A trimmed T1 core prompt** (`prompts/design-sensibility/README.md`, "Token budget"): needs an owner decision here if and when
  such a variant is proposed.
- Doc 37 §10's candidates other than (g) are factual corrections for the cross-doc correction step (docs 03 and 31 already carry
  (b), (c) and (f)). They are filed here only if a correction turns out to need a decision.

## Candidates not filed (2026-09-28)

The design-gap candidates listed in docs 51, 52, 53 and 55–63 that the go-ahead pass did not file, each with where it stands. Items
filed as DG043–DG058 are mapped in that pass's verification note below. "Decided" means decided in a decision record of 2026-09-28
under the owner's go-ahead; the owner may overrule those on return.

| Source item | Candidate | Where it stands |
| --- | --- | --- |
| 51 §6.1 item 6 | An untrusted-text control-token table per model family | A profile fact (doc 51 §4.3 "Untrusted text" row), so its home follows DG045; the neutralising rule stays doc 21 §9.3 |
| 51 §6.1 item 7 | Tracking re-authored third-party harness tests | DG018 (third-party port records); `docs/porting/upstream-test-map.csv` covers engine tests only |
| 51 §6.1 item 12 | Resume and cassette keys hash the full canonical request | DG010 (resume) and doc 38 §6.4 (cassettes); doc 51's `tools/local-qual --resume` finding |
| 51 §6.1 item 13 | The workflow runtime as a sans-IO reducer | An implementation shape for doc 38 §4.7; no conflict found |
| 51 §6.1 item 15 | Pick soft scores from log-probabilities; single-token letter check | D048 item 2 (scoring mode) and doc 53 §4.2; the tokenizer check is a test |
| 51 §6.1 item 16 | Vendor penalties against D022 item 5 | D022 item 5 stands (doc 55 applied it); a request only if a measured win appears |
| 52 RG1, RG3, RG4, RG8 | Route lists; quota ledger and `QuotaLimited`; the UX standard; the paid backstop | Decided: [D050](../decisions/D050-rate-limit-ux-standard-and-router.md) items 3, 4 and 6, 1, 5 |
| 52 RG2, RG5, RG6, RG7 | Retry accounting; cloud K; lean capsules; packing | D050 routes them to DG016 (and DG051 for the taxonomy), DG021, DG019 and DG025 (and DG049), and "not adopted" |
| 52 RG9 | Who curates the dated limit and free-preset data | Open part of D045 and D050; refreshed through releases only (D050 item 4); pairs with doc 50 §6's preset-data candidate |
| 55 §7 item 1 | The harness preset in the qualification key | Decided: [D051](../decisions/D051-capability-ladder-freedom-by-qualification.md) item 4; the remaining hashes are DG044 |
| 55 §7 item 4 | Card policy per model and `DecisionKind` | D051 items 2 and 5 express it as FR1 (no cards) against FR2 (cards), with push always; a request only if a preset moves cards to another channel |
| 55 §7 item 7 | Harness preset distribution and override UX | D048's open part (shipping through the Model Manager under D008) |
| 56 §10 item 1 | Check outcomes with counts | Validation-and-lints §2; technical, no conflict |
| 56 §10 item 3 | Operation policy as data | DG016 (retry causes) and doc 38 §4.2's class table |
| 56 §10 item 5 | Adoption on small suites (doc 55 PR4 against doc 56 EQ3) | Doc 56 §9 tension 3: the first tuning run or the owner decides |
| 56 §10 item 7; 57 TE-G7 | Token budgets against window fractions | Doc 56 WR6 and doc 57 TE-G7/TM2 both derive budgets from the served per-slot context, so they agree; folds remain for doc 38 §3.5 ("about 2% of the window") and doc 12 §5.3 (`T_result`) |
| 57 TE-G2 | Conversation context policy and narrative fields | Doc 57 §3.6; doc 21 §8.1 (no model-written summaries of facts) |
| 57 TE-G6 | Owner of the llama-server launch profile and slot map | D022 (the sidecar) and DG027 (slots) |
| 57 TE-G8, TE-G11 | TTL by pacing; uncached one-shot calls | DG025 and doc 40 R11 |
| 57 TE-G10 | "Unchanged since" receipts | Doc 57 TM4; no conflict |
| 57 TE-G12 | Journal query tools for Wilco | DG032 (tool family) and DG053 (records) |
| 58 §4.11 item 3 | Weights against data tables in the installer | D023 decision 1's reading (owner); a request when a component needs shipped tables |
| 58 §4.11 item 6 | A local reliability report from the journal | Doc 58 §4.10; a product proposal, no conflict |
| 58 §4.11 item 7 | Mozilla's model bucket as a download source | D008 (a user-enabled source, owner); a request when a component needs it |
| 59 §7 item 2 | Code-written thought as a named capsule segment | Owner question first (doc 59 OQ1; D010); DG049 names segments |
| 59 §7 item 3 | The two-phase call shape | DG045 (reasoning facts) and DG016 (the output cap); D023 decision 3 holds (same model) |
| 59 §7 item 8 | A dev-time prompt-pack optimiser | Tooling under D027 item 6 and D048 item 3; never at run time |
| 60 §4 item 8 | Known rough edges per harness preset | D048 item 6 and doc 55 §3.6 (visible presets) |
| 60 §4 item 9 | Recipes as a documented artifact kind | DG007 |
| 61 §6 items 4–5 | Freshness-bound handles; name-addressed query tools | DG032 (option C) |
| 61 §6 item 6 | Teller surface levels in the preset schema | D051 item 5 (pull by grant); a preset may declare a surface level, never above the effective level (doc 63's sibling finding) |
| 61 §6 item 8 | "Fixed by deletion" admission note | D024 (autonomy) |
| 61 §6 item 9 | Draft mode on a `Scratch` fork | D051 (FR6 under the existing autonomy dial); the dry-run tool is doc 63 §13 item 5, below |
| 61 §6 items 10–12 | Prefix verdicts while streaming; completeness of decode constraints; Teller latency targets | Experimental after v1 (doc 62 §6.9); a doc 30 §4.5 fold; the M2 benchmark and D050 item 1 |
| 61 §6 item 14 | Reference kinds for where-used and rename | A factual check of validation-and-lints §9 |
| 62 §10 items 1, 3 | Witness trait policy; diagnostics as guidance | `AGENTS.md` "Witness and guard types", "Diagnostics as Guidance" and "Negative Compile Tests"; DG011 for `Admitted<T>` |
| 62 §10 item 2 | Model-facing text against developer doc comments | Commands-undo-history §3 (doc 62's finding) |
| 62 §10 item 5 | The OS-path guard against the lexical `VfsPath`; a strict-path dependency | Owner (doc 62 OQ2) |
| 62 §10 items 6, 9, 10 | Typed plugin WIT; map-indexing check; the `CheckedUrl` egress shape | Doc 22 OQ2; crate-map §2.4; `plotroom-net` under D008 |
| 63 §13 items 1–3 | Level vocabulary; product ceilings; level and domain in the key | Decided: D051 items 2–4 (names: D034 item 3; ceilings above FR0: D051's open part); stakes floors are DG054, the hashes DG044 |
| 63 §13 items 4–5 | Tool sets per (chat mode, level group); a dry-run admission tool | DG023; doc 63 §3.1's FR6 row and commands-undo-history §4.1 |
| 63 §13 items 8, 11, 12 | A Draft vocabulary of know-how units; off-menu idea cards; the flywheel's review path | Doc 63 §2.3 and OQ10; doc 21 §5.1; doc 55's tuning split and doc 60 P-15 |

## Verification notes

### Consolidation pass (2026-09-27)

- Created this folder index, the template and DG002–DG034 from the design-gap list of the consolidation pass. Each request cites
  the sections it was built from; those sections were re-read on 2026-09-27. Docs 39, 41 and 43 were still being written and were
  only read, never edited. No research doc was edited by this step.
- DG001 was filed earlier in the same pass under an unnumbered name; this index assigns it DG001.
- `docs/upstream/` (the engine-requests register named in `AGENTS.md`) does not exist yet; DG034 records what goes there.
- **Docs 39, 41 and 43 step (2026-09-27).** With the three docs final, each was re-checked against DG001–DG034 and against the owner
  questions in `docs/decisions/OWNER-QUESTIONS.md`. Filed DG035 (doc 39 §1.2), DG036 (doc 41 §2.5, which no earlier request
  covered), DG037 (doc 39's "Names" item: six features called "Director") and DG038 (the SL11 rule text that doc 43's play seed and
  doc 36's re-roll question need). Doc 43's owner-level questions (the challenge catalogue of §3.7, the default play seed, memory
  across playthroughs, whether a re-roll may exist) are already owner questions OWQ-20 and OWQ-21, so doc 43 points there and no
  request duplicates them; DG038 only words the rule once OWQ-21 is answered. Existing requests gained verification notes where
  the three docs add evidence or cases: DG005 (their code families; the T0 label collision; shared findings; probe ids), DG006 (their
  ≤ 7 menus), DG009 (doc 39 §1.1 confirmed), DG010 and DG017 (doc 43's replay record), DG013 (doc 39's `approve` step), DG033 (the
  Easy view in docs 41 and 43) and DG034 (their engine limits, now entries of `docs/upstream/engine-requests.csv`, which the same
  pass created). Each of the three docs carries a dated
  "Consolidation pass" note; the "still being written" remark above no longer applies to them.

### Owner answers (2026-09-27)

- The owner answered every owner question in `docs/decisions/OWNER-QUESTIONS.md` on 2026-09-27. The four owner-level requests that
  were still open are now **decided**, each with a filled "Decision record" section and the index rows above updated: DG002 (OWQ-07,
  option A with the placement table; `AGENTS.md` "Naming and Trademarks" was amended to match in the same pass, outside this folder),
  DG014 (OWQ-16, option B), DG029 (OWQ-12, option A with the non-objection rule; outreach not yet sent) and DG030 (OWQ-17, all four
  proposals). None is `folded` yet: each file's decision record lists its folding steps (affected docs and the decision records'
  "Open parts"), which are edited outside this folder.
- **Leftover fixed.** DG013, DG028 and DG033 (items 3–4) had **decided** headers but decision records reading "Open". Each record is
  now filled from its decision record (D024, D008, D029); no decision changed. DG033 items 1–2 stay open.
- **Index cells for undecided requests.** DG037's decider is now the design round, since OWQ-08 delegated pending names (the owner
  reviews the names table before the first release); DG038's precondition is met, since OWQ-21 chose no re-roll exception in v1. Both
  requests stay open, and their own files still carry the earlier conditional wording, which is left to the pass that decides them.
- All relative links in this folder were checked and resolve.

### Consistency review of the owner answers (2026-09-27)

- DG002, DG014, DG029 and DG030 now link their decision records (D034, D043, D035, D038) in the index and in their "Decision record"
  sections, as the lifecycle asks, and their folding lists mark the decision-record step done (the earlier records' headers and
  notes point to the new records). Each still waits for its research-doc folds, so none is `folded`.
- DG037 and DG038 no longer carry the conditional wording from before OWQ-08 and OWQ-21 were answered: DG037's decider is the design
  round (D034 item 3), and DG038's precondition is met (D040). Both stay open.

### Owner answers to OWQ-24 to OWQ-27 (2026-09-28)

- Filed **DG039** (owner; network boundary) from doc 48 §7.4 item 2, as the owner's answer to OWQ-25 asked when it made aggregators
  first-class providers ([D046](../decisions/D046-aggregators-as-first-class-providers.md)). D046 lists DG039 as an open part and does
  not decide it. (DG039 was decided later the same day under the owner's delegation: D053; see "Owner delegation, design-gap pass".)
- Not filed in this step, and still candidates: doc 48 §7.4 item 1 (cloud artifact identity) and items 3–5, and doc 50 §6's two
  (free-provider preset data and its refresh; a "screened, not qualified" state in the model catalogue). D045 and D046 list the
  cloud artifact identity, and D045 the preset data's refresh, as open parts.

### Go-ahead pass (2026-09-28)

- **Dynamic-workflow requests.** The owner's go-ahead of 2026-09-28 ("Either way, except for GPG Signing, we can do everything else")
  covered filing the three dynamic-workflow requests discussed with the owner: DG040 (a bounded "repeat until" step), DG041 (a
  verification panel for strong models on creative work, opt-in by effort) and DG042 (dynamic authoring with static execution). The
  go-ahead chose no option among them and no research doc recommends DG040's or DG041's shape, so both stay **open** for the owner
  to decide on return. (DG041 was decided later the same day under the owner's delegation: D054; DG040 stays open.) DG042 covers
  only what [D051](../decisions/D051-capability-ladder-freedom-by-qualification.md) item 9 (plans as data after v1, adopted the same
  day under the go-ahead) leaves open: doc 63 §13 items 9–10.
- **Candidates of docs 51–63.** Every design-gap candidate listed in docs 51, 52, 53, 55, 56, 57, 58, 59, 60, 61, 62 and 63 was
  collected (119 items; doc 54 was out of scope) and deduplicated across docs. Filed as open requests, each with the source
  docs' recommended option marked as a proposal where they give one: DG043 (51 item 9, 57 TE-G3, 61 items 1, 3, 7, 13, 62 item 8),
  DG044 (60 items 1, 10; 55 item 1 and 63 item 3 in part), DG045 (51 item 1, citing items 5–6 as uses; 55 item 10), DG046 (53 R7, 55 item 8, 59 items
  5–6, 60 item 11), DG047 (55 item 2, 59 items 1, 7, 60 items 3–5), DG048 (55 items 3, 6; 51 items 8, 14), DG049 (55 item 5, 51
  item 11, 57 TE-G1, 52 RG6, 60 items 6–7), DG050 (53 §4.3, 55 item 9, 56 item 6, 58 OQ4), DG051 (51 items 2–5, 52 RG2), DG052 (53
  §4.9, 58 item 2), DG053 (56 items 2, 4, 57 TE-G4–G5, 58 item 4, 59 item 4, 63 item 6), DG054 (60 item 2; 63 item 2 in part),
  DG055 (63 item 7, 62 item 7), DG056 (57 TE-G9, 61 item 2, 62 item 4), DG057 (58 items 1, 5) and DG058 (51 item 10). The rest are
  in "Candidates not filed (2026-09-28)" above.
- **Decided the same day.** [D050](../decisions/D050-rate-limit-ux-standard-and-router.md) and D051 appeared during this step,
  both adopted under the go-ahead. Candidates they decide were not filed (doc 52 RG1, RG3, RG4, RG8; doc 55 §7 item 1; doc 63 §13
  items 1–3 in part), and DG042, DG044, DG050, DG051, DG054 and DG055 cite them as decided.
- **Owner-level requests.** DG050, DG052 and DG057 (and DG041's reviewer role) need owner questions (doc 53 OQ2, doc 58 OQ2 and
  OQ3 ask them). `docs/decisions/OWNER-QUESTIONS.md` is outside this folder and was not edited by this step. (All four were decided
  later the same day under the owner's delegation, without owner questions: D055, D056, D057 and D054.)
- **Earlier leftovers.** DG058 also covers doc 48 §7.4 items 3–4 and doc 50 §6's "screened, not qualified" state from the previous
  step's list; doc 48 §7.4 items 1 and 5 and doc 50 §6's preset-data refresh (with doc 52 RG9) remain candidates.
- No research doc, decision record or file outside this folder was edited. Every source section cited in DG040–DG058 was re-read on
  2026-09-28 unless its own verification note says otherwise. The next free number is DG059.

### Owner delegation, design-gap pass (2026-09-28)

- The owner wrote on 2026-09-28 (lightly edited): "Go ahead without the GPG passphrase. I will not be near the PC for hours. We are
  working remote", beside the go-ahead quoted above and, for a choice between design options, "Figure out the best option for this
  use case". Under that delegation, with the standing practice that follows from the owner's friction-review direction (D049) (decide
  where one option is sound, list it so the owner can overrule it on return, and ask only when options are balanced or the step is
  irreversible or outward-facing), five owner-level requests were decided without owner questions:
  DG039 option B ([D053](../decisions/D053-aggregator-downstream-hosts.md)), DG041 option B
  ([D054](../decisions/D054-review-stage-for-creative-steps.md)), DG050 option B
  ([D055](../decisions/D055-visible-second-stage-when-unsure.md)), DG052 option A now with tier H only if spike S-ENC meets doc
  58's bar ([D056](../decisions/D056-encoder-inference-out-of-process.md); its sources gave no recommendation, so the conservative
  option was chosen) and DG057 option B ([D057](../decisions/D057-bindable-badged-switchable-components.md)).
- Each file's header, "Decision record" and verification notes, and the index rows above, were updated; the lifecycle list gained a
  line on delegated decisions; the notes of the go-ahead pass and of the OWQ-24 to OWQ-27 step gained pointers where they call these
  requests open. DG042's Context now says DG041 is decided; DG042 stays open. None of the five is `folded`: each decision record lists
  its folding steps, which are edited outside this folder. No git action, account, key or purchase.
- Review of the pass (2026-09-28): the summaries of DG052 here, in DG052 and in the decisions README now say tier H is admitted only
  if S-ENC meets doc 58's bar, not "after S-ENC"; DG052's decision names the ONNX Runtime helper arm S-ENC needs for that bar
  (D056 item 3); DG057's decision record gained its reason; DG050's folding line names the notes on D026 and D051, since D055 item 6
  now keeps D051 item 6 (the second stage answers at the step's effective level, never higher). The five choices are unchanged.
