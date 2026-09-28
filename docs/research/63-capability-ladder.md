# Knowledge in the harness, freedom by capability

Research doc 63 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Questions answered (owner, 2026-09-28, lightly edited): (1) "Encode all knowledge and know-how into the harness; more powerful
models could go even crazier and be granted more freedoms." (2) What OpenCode, or better examples, teach about how useful a language
server is to the model. (3) Is the owner's `strict-path` study (a Rust crate that prevents LLM errors by type design, with typestate,
witness and guard patterns, compile errors that guide, and comments as prompts) relevant now?

**Status: proposal.** Nothing was run, measured or coded for this doc. Every level, number, type, budget and UX below is [I] unless
marked; the numbers are placeholders for the instruments that would set them.
**Epistemic legend** (doc 16's): **[V]** read at the cited source on 2026-09-28 (OpenCode at a pinned commit; papers and pages at
their URLs; the verification notes say which were re-read). **[V per doc N]** taken from a sibling doc. **[I]** our inference or
proposal. **[U]** unknown, needs measurement.
**Relation to sibling docs.** Doc 21 sets the doctrine (shapes, "qualification grants a shape", "split, never escalate"); doc 25 the
shapes, the effort table and draft-first defaults; doc 30 the knowledge stack and which knowledge each shape gets; doc 38 workflows
as data; doc 48 the uplift instrument 48-U; doc 53 the step floors; doc 55 per-model presets; doc 56 implementation patterns; doc
59 reasoning scaffolds; doc 60 stakes floors. Doc 61 (the language service as the model's instrument, same day) owns Teller's
model-facing channels, tools and its surface levels TS0–TS3, and says "Doc 63 owns the ladder these rows join"; §3.1 maps them. Doc 62
(type-driven guidance, the `strict-path` study) was not available when this was written; §9 covers only what the ladder needs, and doc
62 governs the rest. Doc 62 now exists (review note): its §6.3 proposes the same grant witness as §9.2 under the name
`ShapeGrant<S: Shape>`, and its §5.6 and §8 answer §9.4 option 3. D009, D023, D024, D025, D027, D037, D044, D045 and D048 govern. **This doc changes no decision.**
**Names.** A *freedom level* (FR0–FR8, working codes) is how large a step the harness gives a model. The docs already use "rung" for
at least five other things (D015's no-code ladder, doc 21 §2.1's who-decides ladder, doc 48's 48-U arms, doc 53's DP-08, doc 59's
scaffolds), so this doc avoids the word. A *grant* is the record that lets one model setup take steps of one level for one
`DecisionKind`. A *product ceiling* is the highest level a `DecisionKind` ever allows. A *know-how unit* is a registered, code-run
piece of procedure (workflow, recipe, macro, no-code module, template) that a model can name but never change.
**Hygiene.** Public sources only. `strict-path` is the owner's public crate. No game content, local paths, usernames or keys.

## TL;DR

- **Direction (1) is already the doctrine's shape; what is missing is the ladder.** D009 says "Stronger models may take larger
  steps, but **no workflow may require one**"; doc 21 §3.3 says "Qualification grants a shape" and "Effective shape = min(effort
  ceiling, qualified shape)" [V per docs]. Missing: levels finer than Pick/Fill/Compose/Draft, a ceiling per `DecisionKind` that no
  model can lift, a rule for what freedom loosens and what it never loosens, rules for pulling knowledge, and a view for the user.
- **Principle: raise the ceiling, never lower the floor.** Knowledge and know-how are encoded once, in the harness, and do not depend
  on the level. The level decides only who drives them: code alone (FR0), code walking the model through one small decision (FR1–FR4),
  or the model choosing and combining harness units (FR5–FR8). Freedom changes how a model uses the harness's knowledge, never
  whether its output passes through it.
- **Facts stay code-owned even for the strongest model.** The frontier model working alone missed an engine-internal rule (doc 30
  §3.4); fact-bearing Picks are "No model tier: a harness fix" and free-text engine knowledge is "Never local, at any size" (doc 53
  DP-08, DP-16) [V per docs]. A strong model gets room in how it combines facts, never permission to supply them.
- **Bigger steps buy coherence, fewer calls, lower latency and delight, not correctness.** Correctness is a harness property at every
  level. So a level is granted only at a reliability bar (METR: "models' 80% time horizons are 4-6x shorter" than their 50% ones [V])
  and only where it beats the next-lower level on the same cases.
- **Nine levels** (§2): FR0 no model; FR1 one-pass Pick; FR2 guided Pick; FR3 per-field Fill; FR4 whole record; FR5 Compose; FR6
  Draft; FR7 scene or mission draft; FR8 a plan as data over registered workflows. **Effective level = min(product ceiling,
  qualified level, effort ceiling, the user's per-role cap)**; mid-run it can only go down.
- **Knowledge: push always, pull from FR5, compose at FR8** (§3). Weak models never fetch (D027 item 7). Doc 61's Teller surface
  levels sit on the ladder: TS1 (push only) for FR1–FR4, TS2 lookups from FR5, the full TS3 query family from FR6, with pulls still
  only at Thorough or Max effort (doc 30 §4.3). OpenCode shows
  both halves: it appends language-server errors to every edit result for every model, while its navigation tool is opt-in and
  experimental [V].
- **Dynamic authoring (FR8, §8)**: a strong model may *propose* a workflow as data built only from registered units. The definition
  compiler checks it, the user edits and **saves** it as their own workflow, and only then can it run. Saved plans become know-how that
  weak models run at FR1–FR4. This amends D025 decision 1, so it is an owner question, recommended for after v1.
- **The `strict-path` study applies twice** (§9). For the Rust code that coding agents write: grants as witness types with a private
  constructor, sealed level markers, and `#[diagnostic::on_unimplemented]` notes that tell the agent how to get a grant. For Wilco at
  run time: checkers as teachers, which Plotroom already does with typed rejections and Teller diagnostics; from FR5 the model may
  call the checker before it submits.
- **The user sees and caps every level** (§7): "asked as" on the plan card, a ladder grid of badges in Settings, a lower-only
  "largest step" cap per role, split-down events in the run panel. No fourth dial (D024 keeps three).
- **Twelve design-gap candidates and a draft decision record** (§13, §14), none filed.

## 1. The principle

### 1.1 Where the doctrine already stands

| Owner direction | Already in the docs [V per docs] | Gap [I] |
| --- | --- | --- |
| Encode knowledge in the harness | D027: typed actions (L1), facts from Teller (L2), Teller as guard rail (L3), a small primer (L4), exemplars (L5); "Activation is code's job" (item 7). D048 item 2: "Presets change how Wilco asks, never what code owns" | No single map of *which* knowledge lives *where*, and no rule that strong-model discoveries flow back into the harness as data |
| Encode know-how in the harness | Workflows as typed data (D025); macros, generators and providers as registered code steps (doc 38 §3.2); no-code modules (doc 31); recipes proposed (doc 60 P-15) | Strong models cannot yet *use* know-how units as vocabulary; they only fill slots inside them |
| Stronger models get more freedom | D009 decision 3; doc 21 §3.3; agent-runtime §7; effort's shape ceiling (doc 21 §7.1) | Four coarse shapes; no product ceiling per `DecisionKind`; no pull rules per shape beyond doc 30 §4.2; no FR8; no user-facing ladder |
| LSP-style help for the model | Teller (validation-and-lints §9), `script.check`, `script.command` and friends (doc 30 §4.4); repair quotes one finding (doc 25 §7.2) | Which Teller operations each level may call (doc 61 designs the operations) |
| Types that guide agents | AGENTS.md type-safety rules; `Admitted<T>` with a private constructor; `UserIntent` minted only by the session; a typestate `CoreBuilder` (commands-undo-history §4.1, §4.2, §4.4) | No type that proves a model setup may take a given step size |

### 1.2 Knowledge and know-how: what lives where

"Encode all knowledge and know-how into the harness" is concrete once each kind has a home. The home does not change with the level;
only the way a model meets it does [I on V per D027, doc 30 §4].

| Kind | Examples | Encoded as | Met at FR1–FR4 as | Met at FR5–FR8, in addition, as |
| --- | --- | --- | --- | --- |
| Facts | Class ids, places, 12 seats per group, the 100 m auto-join, profile availability | Catalog, island packs, Teller's per-profile catalog; every fact with an id and a pinned citation (D027) | Code-built options and fact tokens; the model never types a fact | Lookup tools (`catalog.find`, `island.places`, `script.command`) whose rows are code-rendered |
| Rules | Trigger semantics, END wiring, `this` per field, crew seats | Cards (≤ 150 words), validators, Teller `check_field` | A pushed card or the decisive card sentence; a finding in a repair turn | `reference.search`, `reference.card`, `diagnostic.explain`; `script.check` before submitting |
| Craft | Pacing, fun, era tone, realism defaults | Design-sensibility lenses, advisory lint families (MC, CF), frozen exemplars | The lens in the system text; 0–3 exemplars | The same, plus advisory findings on its own drafts |
| Procedures | Build a patrol, write a briefing, wire an ending | Workflow definitions (TOML), recipes | Walked through one step at a time by the runtime | `workflow.search` and `workflow.describe`; a plan composed of them (FR8) |
| Patterns | Ring patrol, ambush at a site, a no-code module | Macros, generators, modules, templates (registered code) | Code applies the pattern the user or a Pick chose | Named as vocabulary inside Drafts, with typed parameters (§2.3) |
| State | Document, journal, story bible | Code-owned stores | A code-built digest | Read-only Query tools, Teller navigation, Path Explorer queries |

**The flywheel [I].** When a strong model's output proves useful, the harness absorbs it as reviewed data, never as model memory: a
saved plan becomes a user workflow (§8.5); a good draft becomes a frozen exemplar only through doc 55's tuning split and a human
review (doc 60 §2.2 lets "a stronger model … *propose* variants offline, frozen before any held-out run"); a repeated repair becomes a
card or a lint. This is D048 item 3 ("Adapt the harness, do not train the model") applied to know-how.

### 1.3 Why facts stay in code even for strong models

- The frontier model working alone missed the 100 m auto-join (doc 30 task T11), and doc 30 §3.4 concludes: "Rules that live only in
  source need cards even for strong models" [V per doc 30].
- Fact-bearing semantic Picks (TR UNLOAD vs UNLOAD, Countdown vs Timeout) are "**No model tier: a harness fix**": `pick-hard` without
  cards scored 0.70 at Qwen3-30B-A3B, level with the 4B class (doc 53 DP-08, §1.4; preliminary per doc 53) [V per doc 53].
- Free-text engine knowledge is "**Never local, at any size**": every 3–4B build scored 0 of 24 without cards (doc 53 DP-16) [V per doc
  53].
- No bare model can know Plotroom's own catalogue ids or a user's mod set (doc 48 §5.2; D030) [V per docs].

Consequence [I]: menus, ids, positions, engine rules and validity are code-owned at every level. The ladder loosens how facts are
combined, never who supplies them.

### 1.4 Why give strong models bigger steps at all

Correctness never needs a high level: validity is a harness property (doc 25 §1), and maximal decomposition with small models has run
over a million steps without error (MAKER, arXiv 2511.09030, per doc 48 §5.5) [V per doc 48]. The value lies elsewhere [I on V]:

- **Coherence.** Tight scaffolding can make characters less believable (arXiv 2510.25820, per doc 21 §13.1) [V per doc 21].
  Whole-record Fill improves with size: all fields right per call 0.25–0.64 at 4B (Gemma 4 E4B up to 0.86) against 0.917 at
  Qwen3-30B-A3B (doc 53 §1.4, preliminary) [V per doc 53].
- **Calls and quota.** An 8-mission campaign is about 273 decisions and 650 calls at today's step sizes (doc 53 §1.3) [V per doc 53];
  a free OpenRouter account gives 50 requests a day (D045 Consequences) [V per D045]. Larger steps on a qualified cloud setup cut calls.
- **Latency and something to watch.** Fewer round trips; drafts stream as ghosts (doc 25 §10.3).
- **Delight.** Surprise, variation and cross-entity ideas are part of "fun is a requirement" (AGENTS.md).
- **Scaffolds are not free.** "additional scaffolding does not consistently improve reliability" (arXiv 2607.05775, per doc 25) [V per
  doc 25], so a strong model may drop a scaffold only where 48-U's paired removal arms show non-inferiority (doc 48 §5.1), and never on
  a code-owned item.
- **Reliability decides, not "sometimes works".** METR's 50% time horizon "has doubled every 207 days", but "models' 80% time horizons
  are 4-6x shorter" (arXiv 2503.14499 v4, §3.2, §3.2.1) [V]. A level is granted at a reliability bar and re-qualified as models improve,
  so the ladder opens up over time without any change to the floor.

### 1.5 The principle, as rules

1. **Knowledge is level-independent.** Every fact, rule, craft note, procedure and pattern lives in the harness once (§1.2). No level
   has knowledge another lacks; higher levels only get more ways to reach it.
2. **Raise the ceiling, never lower the floor.** A level widens what the model may return and which read-only tools it may call. The
   invariants of §5 hold at every level, preset, effort and autonomy.
3. **Freedom is earned per step kind.** A grant belongs to (setup, harness preset, `DecisionKind`, level, domain) and is set only by
   qualification (§4). Nothing else can raise it: not a prompt, not a plugin, not mission text, not the model itself.
4. **Freedom is capped by the product.** Each `DecisionKind` has a product ceiling that no preset, grant or user setting can lift
   (§4.2).
5. **Down is automatic; up is a click.** Failure splits down along an authored decomposition; a larger step or a stronger model is
   offered as a priced button (§4.6).
6. **Every level is visible.** The plan card says how each step is asked; the inspector shows what knowledge was pushed and pulled
   (§7).

### 1.6 What "crazier" can mean, and what never changes

| Freedom that grows with the level [I] | Lowest level | Never grows |
| --- | --- | --- |
| Scope per call: letter → field → record → sub-structure → multi-entity change set → scene → plan | FR1 → FR8 | Facts: ids, positions, counts, engine limits |
| Knowledge access: pushed only → TS2 lookups → the full TS3 query family → Path Explorer → the workflow catalog | FR5, FR6, FR7, FR8 | Effects: only the command bus applies admitted batches |
| Composition vocabulary: options → fields → typed actions → macros and modules → workflows | FR6, FR8 | Checks: the same families for every output |
| Creative latitude: K candidates, longer text, cross-entity ideas, a surprise twist offered as an idea card with a build | FR4, FR7 | Consent: saves, approvals, Preview, egress and pinned-field writes need a click |
| Iteration inside a step: check-then-fix before submitting, within a turn budget | FR5 | Scope: no shell, file, web or process tool at any level |
| Disagreement: `X` with an idea card ("none fit; here is what I would do instead"), routed by code to a question or the nearest workflow | FR5 | Honesty: "done" comes only from the completion gate |

### 1.7 Outside precedent

| Source [V] | What it says | What Plotroom takes [I] |
| --- | --- | --- |
| Feng, McDonald, Zhang, arXiv 2506.12469 | "an agent's level of autonomy can be treated as a deliberate design decision, separate from its capability and operational environment"; five user roles; "AI autonomy certificates" | Keep the freedom level (what the model may produce) separate from autonomy (what waits for a click); badges act as certificates |
| Morris et al., arXiv 2311.02462 v5 | "Higher levels of autonomy are 'unlocked' by AGI capability progression, though lower levels of autonomy may be desirable for particular tasks and contexts" | Capability unlocks levels; the user may always choose lower (Teach and Drill use low levels on purpose) |
| Parasuraman, Sheridan, Wickens (2000) | Automation is set separately for information acquisition, analysis, decision selection and action implementation | Grant per function: pull tools are acquisition and analysis; the level is the decision; action implementation is never delegated (code applies every command) |
| SAE J3016 (2021) | Automation levels hold only inside an operational design domain | A grant holds only inside its qualified domain (profile, language, mod-set class) |
| Karpathy, YC talk 2025-06-17 | An autonomy slider ("Tab -> cmd+K -> Cmd+L -> Cmd+I"); "Keep AI on tight leash"; make verification "easy, fast to win" | The ladder is Plotroom's slider for step size; the validators keep the verify loop fast |
| Progent, arXiv 2504.11703 | "the agent's effective action space can only shrink without approval (monotonic confinement)" | Split-down is automatic; any rise needs the user |
| Claude Code permission modes | "Actions no mode auto-approves"; "Deny rules block in every mode, including `bypassPermissions`" | §5's floor: invariants no level, effort or autonomy loosens |
| Anthropic, "Measuring agent autonomy" (2026-02-18) | Full auto-approve rises from "roughly 20%" of sessions for new users to "over 40%" by 750 sessions; interrupts rise from 5% to "around 9%" of turns; "requiring humans to approve every action, will create friction" | Visibility and stop or redirect controls, not a new approval prompt per level |

## 2. The ladder

### 2.1 Levels

| Level | The model returns | Today's shape (doc 21 §3.1) | Default floor [I, from docs 21, 25, 53] | Latency (doc 53 §1.1) |
| --- | --- | --- | --- | --- |
| **FR0** No model | Nothing; code decides | Deterministic | — (the baseline every level must beat, doc 21 §1.1 rule 7) | L0 |
| **FR1** One-pass Pick | One letter from ≤ 7 code-built options plus `X`/`Q` (≤ 3 per facet step below 1B, doc 53 §4.2); no cards; read by letter scoring where log-probabilities exist (doc 53 §4.2) | Pick | Tiny local, on easy taste menus (DP-06, DP-07) | L1 |
| **FR2** Guided Pick | FR1 plus code-pushed knowledge: cards, the decisive card sentence, option-diff and consequence lines, or extract-then-dispatch facets (doc 59 S1, S2, S7) | Pick | Local small; **the default for an unqualified setup** (agent-runtime §7) | L1 |
| **FR3** Field Fill | Closed fields as per-field Picks; spans by code candidates or a verbatim grammar; one short text slot (doc 53 §4.4; doc 55 H-Q3, H-R3) | Fill, per field | Local 1–4B | L1–L2 |
| **FR4** Whole record | A flat typed record in one call, or K creative candidates per text slot | Fill | 3–4B only as a pre-fill the user confirms; the whole record at 26–30B MoE or cloud (DP-01, DP-12) | L2–L3 |
| **FR5** Compose | One nested sub-structure: a mission concept, one node's transitions, one radio exchange, one script snippet | Compose | ≥ 8B or cloud; scripts cloud or ≥ 9B behind the gates (DP-19) | L3 |
| **FR6** Draft | A ChangeSet of typed commands over several entities, after a bounded read-only tool loop (doc 19 §8 `campaign.propose_branch`) | Draft | Cloud; local 27B+ experimental (DP-20) | L3–L4 |
| **FR7** Scene draft | A whole scene, mission or branch as one ChangeSet in the typed-action and know-how-unit vocabulary (§2.3); replaces the draft-first default only when every mission-scope gate passes | Draft at mission scope (new) | Cloud | L4 |
| **FR8** Plan | A `PlanDraft` over registered workflows and units (§8); runs only after the user saves it | None (today forbidden, §8.1) | Cloud | L4 |

FR7 is split from FR6 because its gates differ (mission validators, readiness, compile and round-trip) and because it replaces a
whole default rather than adding entities. FR1 is split from FR2 because doc 55 H-R2 found 82 of 90 Pick calls unchanged with and
without cards [V per doc 55], so for some (model, `DecisionKind`) pairs the cheaper form is enough.

### 2.2 What code owns at every level

Code owns [V per doc 21 §1.1, §2.2; doc 25 §3 principle 2; commands-undo-history §4]:

- **Facts**: classes, ids, places, coordinates, counts, distances, times, engine limits.
- **Menus**, option text and the escapes `X` and `Q`.
- **Admission** and every check family (V-schema … V-compile; Teller `check_field`; reference integrity; ownership; profile and risk
  policy).
- **Effects**: only the command bus applies `Admitted<CommandBatch>`; the model never executes anything.
- **"Done"**: only the completion gate reports it.
- **State**: document, journal and story bible; no model-written summaries.
- **Authored decompositions** for split-down; **budgets and caps**; **role bindings** and data destinations.
- **Consent**: an unforgeable `UserIntent`; **trust labels and provenance**.

Level-specific [I]: at FR5–FR7 every identifier the model writes must resolve against a declared table (doc 25 §3); at FR8 the
runtime owns execution and control flow, a plan may name only registered units, and every nested model step keeps its own grant. A
plan never lifts a sub-step above that sub-step's grant (no transitivity).

### 2.3 A composition vocabulary for strong models: know-how units addressed by anchors

Proposal [I]: a Draft (FR6–FR7) is written in **typed actions plus know-how units**, never raw `mission.sqm` text or positions.

- Units are registered macros, generators and no-code modules (ring patrol, formation at a site anchor, garrison, ambush, radio
  exchange; doc 31 modules; doc 38 `code` steps), each with typed parameters and its own checks.
- Places are **anchors and site ids** from `island.places` and the mission's markers, so code computes every coordinate; counts are
  bands or menu letters; classes are catalog ids from `catalog.find` rows.
- A unit the model names that does not exist, or a parameter outside its declared type, is a finding in the repair turn, with the
  allowed values (commands-undo-history §4.1 `Rejection { allowed }`).

This is "know-how encoded in the harness" made usable by strong models: they compose the harness's procedures instead of re-deriving
them, and the procedures stay correct because code runs them.

## 3. Knowledge exposure per level

### 3.1 Push always, pull from FR5, compose at FR8

This extends doc 30 §4.2 (knowledge by shape) and §4.3 (by effort), and places doc 61's Teller surface levels (§4.10 there: TS0 no
model; TS1 push only, for every setup; TS2 lookups, for setups qualified for script Compose; TS3 the whole query family, for setups
qualified for multi-entity work at Thorough or Max effort) on the ladder [I on V per docs 30, 61]. Teller tool names are doc 61 §4.3's
(provisional until DG032).

**Effort still gates pulls** [I, added in review]. Doc 30 §4.3 allows model lookups only at Thorough and Max, and doc 61 §4.10 keeps
that rule. So the pull and pre-submit check columns below apply only at those efforts: an FR5 step run at Standard (which §6's D024
row allows when qualified) keeps FR5's step size but gets push only (TS1), unless the owner changes doc 30 §4.3.

| Level | Teller surface (doc 61) | Pushed by code into the capsule | Pull tools the model may call | Checks the model may call before submitting |
| --- | --- | --- | --- | --- |
| FR0 | TS0 | — (code uses the knowledge directly; the user sees the same findings) | — | — |
| FR1 | TS1 | Option lines from facts only | None | None |
| FR2 | TS1 | Code-selected cards, the decisive sentence, option-diff lines or dispatch facets (doc 59 S1, S2, S7); repair cards and fix menus | None | None |
| FR3–FR4 | TS1 | Slot or record spec with dynamic enums and fact tokens; code-written bands; at most one card per rule-bearing slot; for creative slots a style card and 0–3 frozen exemplars | None | None |
| FR5 | TS2 | Primer sections for the step; the field-context card; a catalog row for each command code expects | TS2's set: `script.command`, `script.complete` as menus, `mission.find`, `reference.explain_instance`, `mission.where_used` (cap 5 rows); `reference.card` | `script.check` in the field's mode |
| FR6 | TS3 | The whole primer; code-picked cards; findings after every attempt (informational inside a draft, doc 61 §4.10) | TS3's whole family (adds `mission.outline`, `script.calls`, `fix.options`, larger caps) plus the Lookup tools `catalog.find`, `island.places`, `reference.search` (≤ 8 rows, shown/total), `diagnostic.explain` | `script.check`; a **dry-run admission** of the draft ChangeSet on a `Scratch` fork (commands-undo-history §4.1 step 2 is pure, so no effect; doc 61's "Draft mode") |
| FR7 | TS3 | FR6, plus the know-how unit catalogue for the mission's profile | FR6, plus Path Explorer's closed queries (`paths_to`, `writers_of`, `readers_of`, `uncovered_cases`; doc 21 §11.5) and `next_step` | FR6, plus mission readiness |
| FR8 | TS3 for nested steps only; none for the planner | The verbatim request; code-rendered structure (ids, types, counts); never quoted mission text | `workflow.search` (id plus one line, ≤ 8 rows, shown/total); `workflow.describe(id)` (typed inputs and outputs, preconditions, effects, model policy, cost estimate) | `plan.check` (the definition compiler in dry-run mode, §8.3) |

### 3.2 Fixed rules

1. **Pull never replaces push.** A qualified model still gets the code-selected cards; tools only add reach. Weak models never fetch
   (D027 item 7) [V per D027].
2. **Tool results are code-rendered**, with shown/total counts; untrusted text inside them stays quoted and labelled (doc 21 §9.1).
3. **One fixed tool set per (chat mode, level group)**, name-sorted, extending DG023 option B. Proposal: at most three groups per mode
   (none for FR0–FR4; TS2 for FR5; TS3 plus the FR7–FR8 extras for FR6–FR8), with per-step narrowing by OpenAI-style
   `allowed_tools` ("not modify the list of tools you pass in, so you can maximize savings from prompt caching" [V]) or by grammar
   masking locally. An out-of-step call is refused with `ToolNotInStep` (agent-runtime §2).
4. **The callable set** = `Reach::AgentCallable` ∩ chat mode ∩ step ∩ plugin grant ∩ role (agent-runtime §2) **∩ level grant**.
5. **Progressive disclosure at FR8.** The Agent Skills specification loads metadata (~100 tokens), then instructions (< 5,000 tokens
   recommended), then resources "only when required" [V]; Anthropic reports Tool Search cutting tokens by 85% and raising accuracy from
   49% to 74% (Opus 4) and from 79.5% to 88.1% (Opus 4.5), worth it past "10+ tools" or ">10K tokens" of definitions [V]; RAG-MCP
   raised tool-selection accuracy from 13.62% to 43.13% while cutting prompt tokens by over 50% [V]. Wilco's core families are small,
   so this matters at FR8's workflow catalogue and for large plugin tool sets, not at FR1–FR4, where "fewer tools help small models"
   (arXiv 2411.15399, per doc 21 §3.2) [V per doc 21].
6. **Push first, then let good models explore.** Anthropic's context-engineering guidance describes "a hybrid strategy, retrieving
   some data up front for speed, and pursuing further autonomous exploration at its discretion", and expects that "As model
   capabilities improve, agentic design will trend towards letting intelligent models act intelligently, with progressively less
   human curation" (2025-09-29) [V]. The ladder is that trend under qualification: the curation (push) stays; the exploration (pull)
   is granted.

### 3.3 What OpenCode's language-server use teaches for the ladder

Read at `github.com/anomalyco/opencode` @ `03e67171ab2dc1e7f16e8cebfbc7f778f61b89f0` (committed 2026-09-28; MIT) [V]. Doc 61 covers
Teller's model-facing design; here only what bears on levels.

| OpenCode [V at source] | Ladder reading [I] |
| --- | --- |
| **Diagnostics are pushed to every model.** After an edit the tool result appends `"LSP errors detected in this file, please fix:"` and the report (`packages/opencode/src/tool/edit.ts:196-201`) | Checker output after every attempt at every level (L3 of D027). The same idea is Plotroom's one-finding repair turn |
| **Navigation is pulled, and opt-in.** The `lsp` tool offers nine closed operations: goToDefinition, findReferences, hover, documentSymbol, workspaceSymbol, goToImplementation, prepareCallHierarchy, incomingCalls, outgoingCalls (`src/tool/lsp.ts:11-21`), and is registered only behind `flags.experimentalLspTool` (`src/tool/registry.ts:247`) | Teller lookups are pull tools only by grant: doc 61's TS2 subset from FR5, its whole query family from FR6; never at FR1–FR4. Doc 61 (§2.5, TL;DR) rates model-called navigation as of little or negative measured value, which is why it is granted per setup, not given |
| **The tool surface adapts per model family.** `apply_patch` is used for model ids containing `gpt-` except `gpt-4` and `oss` ids, `edit`/`write` otherwise (`src/tool/registry.ts:297-300`) | D048's per-model presets applied to tools: a preset may choose among equivalent tool forms, never widen the set |
| **Agents are permission rulesets.** `plan` denies edits except its plan files (`src/agent/agent.ts:156-181`); `explore` denies everything but grep, glob, list, bash, webfetch, websearch and read (`:196-218`); a per-agent `steps` value from config (`:291`) caps the loop (`src/session/prompt.ts:1178`, `agent.steps ?? Infinity`) | Levels as rulesets with turn caps (§4.5); Plotroom's caps are always finite |
| **Loop guard.** Three identical calls of one tool with the same input raise a `doom_loop` ask (`src/session/processor.ts:29`, `:356-373`) | Doc 21 §8.2's stagnation fingerprints at FR5+; Plotroom stops and reports rather than asking to continue |

**Not adopted:** OpenCode's defaults start from `"*": "allow"` with asks for exceptions (`src/agent/agent.ts:119-136`) and include
shell, web and file tools. Plotroom is deny-by-construction: `AgentTool` has no Network, FileSystem or Process effect (D006;
agent-runtime §2).

## 4. Qualification, grants and ceilings

### 4.1 Effective level

**Effective level = min(product ceiling of the `DecisionKind`, qualified level of (setup, harness preset, `DecisionKind`), effort
ceiling, the user's per-role cap)** [I; extends doc 21 §3.3 and agent-runtime §7]. Every term can only lower the result. An
unqualified setup runs FR2, with FR4 only as a pre-fill the user confirms (agent-runtime §7 today).

### 4.2 Product ceilings per `DecisionKind` family

Set in the `DecisionKind` registry, reviewed like code, and unraisable by any preset, grant or user. This is the ladder form of doc 60
§2.8's "stakes floors … that no preset can lower" [I on V].

| `DecisionKind` family | Product ceiling [I] | Why |
| --- | --- | --- |
| Fact-bearing semantic Picks (waypoint type, trigger timing, end semantics) | **FR0**: code filters by the fact | DP-08: no model tier fixes it |
| Free-text engine knowledge answers | **FR0**: the card is shown; a model may only phrase a computed finding (EXPLAIN) | DP-16; agent-runtime §7 `NotInManual` |
| Workflow routing (the `Selector`) | FR2 | DP-02: one letter over workflow descriptions; larger steps add nothing |
| Guard constants and enum fills over computed ranges | FR3 | DP-12: per-field Picks, ints binned into bands |
| Intent fill from free text | FR4 | DP-01: the whole record in one call only at 26–30B MoE or cloud |
| Script snippets (conditions, init lines, `.sqs`) | FR5, behind `check_field` and the risk policy | DP-19; doc 24 §5.3 |
| Campaign transitions (CXL) | FR5 per node; FR6 for a branch | Doc 19 §8 |
| Prose, dialogue, briefings | FR4 alone; FR7 inside a scene draft | DP-17, DP-18: size helps text |
| A mission, scene or branch | FR7 | Mission-scope gates |
| A plan over workflows | FR8, only through an explicit entry (§8) | §8 |

### 4.3 What a setup must show to be granted a level

All must hold [I on V per doc 21 §2.2, §12.3; D037; D045; D048]:

1. **Reliability at that level's bar.** n consecutive all-pass trials on that level's instrument. Doc 21 §12.3's arithmetic: 14 trials
   support 80% at 95% confidence, 29 support 90%, 59 support 95% [V per doc 21]. Proposal: n ≥ 14 at FR1–FR4; n ≥ 29 at FR5–FR6; n ≥
   29 per scenario class at FR7–FR8, plus an E10-style end-to-end run with validity 100% and clobbers 0. Larger steps cost more per
   failure (time, tokens, undo size), and the 80% horizon is 4–6× shorter than the 50% one (§1.4).
2. **Beat the next-lower level** on the same cases, paired, with no case-level safety regression (doc 21 §2.2 items 5–6, the
   "remove-it test"). A level that does not is not offered for that `DecisionKind` (the kill rule, §12).
3. **Pass every must-pass case**: planted escapes, no false admits, indirect injection, out-of-scope refusal.
4. **From FR5: tool-loop hygiene**: no out-of-step calls, no stagnation, within budget, no pull that replaces an available push.

### 4.4 Grant key, domain and voiding

- A grant belongs to **(setup, harness preset version, `DecisionKind`, level)** and to its **domain**: target profile, prompt language,
  mod-set class. SAE J3016's operational design domain is the model [V; mapping I].
- DG012's triggers void it; doc 60 P-02's wording hash joins the key.
- D045's "offered only where qualified per step kind" becomes "per step kind and level"; D037 badges gain the level.
- A D044 cloud screen never sets a grant (D044 Consequences: "A cloud result is never shown to users as a badge") [V per D044].

### 4.5 Checks and budgets per level

The checks never change with level or effort (doc 21 §7.1). Higher levels add the checks of their wider scope [I]:

| Level | Added checks | Proposed budget (placeholders) |
| --- | --- | --- |
| FR1–FR4 | The step's V-families (doc 25 §7.1) | Zero tool turns; K and R from effort |
| FR5 | V-cxl; Teller parity for scripts | ≤ 2 lookups, ≤ R repairs |
| FR6 | Per-command admission; full lints; reference integrity; ownership | ≤ 8 tool turns; one final ChangeSet of ≤ ~40 commands |
| FR7 | Mission validators; readiness; compile; round-trip; Path Explorer coverage for branches | ≤ 16 tool turns at mission scope |
| FR8 | The definition compiler (doc 56 WR1: every step reachable, every model step followed by a check consuming all its outputs, completion gate present); a budget pre-check against the whole-run ceiling; a diff against the nearest authored workflow | A plan of ≤ ~12 units; the whole-run ceiling on the plan card (doc 38 §3.4) |

Worst-case reservation precedes every call (doc 56 WR6); stagnation fingerprints stop loops (doc 21 §8.2; doc 56 WR5). A tool loop
keeps a bounded transcript inside one step only; every step starts from a fresh capsule (doc 21 §8.1).

### 4.6 Failure route: down automatically, up only by the user

- A failed or over-budget step **keeps its admitted parts** and re-runs the rest one or more levels lower along the `DecisionKind`'s
  authored decomposition: FR7 → FR6 per entity group → FR4 per record → FR2 Picks → the kept default. This is doc 21 §3.3's "Split,
  never escalate".
- The draft-first default is in place before any model step (doc 25 §10.1), so a failure never leaves a hole.
- The effective level is fixed and shown on the plan card before the run. Mid-run it can only go down; never up, never to another
  model (D023 decision 3). DG022's same-model re-run stays compatible, because a re-run never raises the level.
- A higher level, or a stronger model, is offered as a visible button with its cost.

## 5. The floor: invariants no level loosens

Precedent: Claude Code lists "Actions no mode auto-approves", and "Deny rules block in every mode, including `bypassPermissions`" [V].
Plotroom's floor, at every level, preset, effort and autonomy [V per the cited docs; the list is proposed]:

1. **Product scope.** `AgentTool` has no Network, FileSystem or Process effect (agent-runtime §2; D006); plugin tools only through a
   manifest and a grant.
2. **Same path as the user.** Every write is `Proposal<CommandBatch>` → `Admitted` → one undo group (commands-undo-history §4).
3. **Same checks** for every output; strict admission; a truncated reply is never executed (doc 21 §8.2).
4. **Code owns facts and "done".**
5. **Human-edited and pinned fields win**; writing them needs `UserIntent` (core-document-model §8.1).
6. **No silent switch**: the setup used is the setup shown; no cross-model escalation (D023 decision 3).
7. **Glass box** (D010): every generated element opens its decision record, which now also names its level, the knowledge ids pushed
   and the tool calls pulled.
8. **Untrusted text is data**: trust labels; never in instruction positions or a thought channel (doc 21 §9; doc 59 §5.1). Beurer-
   Kellner et al.: "once an LLM agent has ingested untrusted input, it must be constrained so that it is *impossible* for that input to
   trigger any consequential actions" [V].
9. **Consent is typed and unforgeable**: Preview, egress, plan approval, saving a workflow, idea cards and pinned-field writes each
   need a click with `UserIntent`.
10. **Budgets are ceilings** that only tighten.
11. **Draft-first**: the document is always compilable.
12. **No model self-grading, no model-written memory, no stored reasoning text** (doc 21 §8.2; doc 56 §9).
13. **Product ceilings per `DecisionKind`** (§4.2).

## 6. Fit with existing decisions

| Record | How the ladder fits [I] | Change needed |
| --- | --- | --- |
| D009 (decision 3) | The ladder is "stronger models may take larger steps" made concrete; FR0 and the authored split keep "no workflow may require one" | None |
| D023 (decision 3) | Down-only mid-run; a stronger model is a button | None |
| D024 | Levels live in effort's existing shape-ceiling row; the per-role cap sits inside role binding and only lowers; **no fourth dial**. Proposed ceiling row: Quick ≤ FR4; Standard ≤ FR4, FR5 if qualified; Thorough ≤ FR5, FR6 if qualified; Max ≤ FR7 if qualified (today: Pick/Fill; Fill, Compose if qualified; Compose, Draft if qualified; Draft if qualified). FR8 is not an effort value (§8) | Doc 21 §7.1 note; a `planner` role would amend item 4 (owner) |
| D025 (decision 1) | FR1–FR7 fit unchanged. FR8 has a model *propose* a definition that the user saves: the model still never writes a definition the runtime runs without a user gesture, but it does draft control flow | **Owner** (§8.7) |
| D027 | Push at every level; pull only with a grant ("strong and external agents may also call lookup tools", item 2) | None; doc 30 §4.3's "if qualified" becomes "from FR5 with a grant" |
| D037 | Badges gain the level; custom models stay "unqualified" at FR2 | Badge wording (doc 21 OQ3) |
| D044 | A screen can suggest which levels to qualify locally; it never sets a grant | None |
| D045 | Free cloud models are offered per step kind **and level** | Wording of item 4 |
| D048 | A preset may lower a level or choose among equivalent forms; it never raises a level or the product ceiling (item 2: "never … what code owns") | Doc 55 §1.4 note |
| DG022, DG023 | A same-model re-run never raises the level; tool sets per (mode, level group) extend option B | DG023 text |

## 7. What the user sees and controls

User-facing names are placeholders for the design round (D034 item 3): "Pick", "Pick with notes", "Fill a field", "Fill a form",
"Compose", "Draft changes", "Draft a scene", "Plan the run" [I].

- **Plan card** (doc 38 §5.2): per step, "asked as" (the level's name), the bound setup and harness preset, the level's badge, estimated
  time and cost; a "why this size?" tooltip ("qualified up to Fill a form for briefing slots on this model"); a priced "Try a bigger
  step" offer when a higher level is qualified but effort caps it; a "Smaller steps" toggle that lowers every step by one level.
- **Settings → Models**: a ladder grid (level × `DecisionKind` family) with badges (qualified, spike-checked, not met, requalifying,
  custom: unqualified), links to evidence (suite hash, n, date, runtime), and "Check this model on my machine". These are Feng et al.'s
  autonomy certificates made concrete.
- **Settings → Roles**: a "largest step" cap per role, lower only (an advanced setting inside role binding, not a new dial).
- **Run panel**: split-down events ("Draft ran out of budget; kept 12 of 15 commands; finishing 3 as Picks"); pulled lookups as typed
  tool cards whose `ItemRef` links select on the map (agent-runtime §9); stagnation stops in plain words; FR6+ drafts stream as ghosts
  so there is something to watch every minute (doc 25 §10.3).
- **Decision inspector**: the level, the knowledge pushed (card and primer ids), the tools pulled with their results, findings and
  repairs, and "written by the editor" against "written by the model" (doc 59 §5.4).
- **Teaching and Drill use low levels on purpose**, because "lower levels of autonomy may be desirable for particular tasks and
  contexts" (Morris et al.) [V], and a small visible step teaches more than a finished draft.
- **No per-level approval prompts.** Anthropic's autonomy study found users auto-approve more as they gain experience while
  interrupting more often, and that "requiring humans to approve every action, will create friction" [V]. Autonomy (D024) stays the
  only dial for waits; larger batches already trip Confirm's delete, move or size threshold, and Propose shows every level's output as
  ghosts and a diff.

## 8. Dynamic authoring: a strong model proposes a workflow as data

### 8.1 What current doctrine says

- D025 decision 1 and doc 38 TL;DR: "The model never writes control flow; chat may start and parameterise a workflow, never redefine
  it" [V].
- Doc 38 §2 principle 1: "Wilco has no tool that creates or edits a definition"; people author TOML and the loader validates it as
  data [V].
- Doc 56 §9: "models never author executable plans" [V]. Doc 59 TL;DR: model-written plans are not recommended for local 1–9B models,
  and executing model-written programs is not adopted (§4.5) [V]. Doc 21 §1.4: no ungated "run everything" loops [V per doc 21].
- Precedent outside: Claude Code's dynamic workflows put orchestration in a JavaScript script the model writes per task, which can be
  saved as a command (per doc 38 §1.1) [V per doc 38]. Plotroom rejected model-written scripts; §8.2 keeps the idea (a strong model
  composes a procedure; the user keeps it) and drops the script.

### 8.2 The proposed flow [I]

1. **Entry.** Only when `Dispatch` returns `NotSupported { nearest }` (doc 21 §4.1): the card offers the nearest workflows and, if a
   planner setup holds an FR8 grant and the user's cap allows it, a priced "Plan it for me" button. The user's click starts it.
2. **Planner capsule.** The verbatim request plus code-rendered structure (workflow ids and one-liners, typed signatures, mission ids,
   types and counts). **No `Untrusted` segment**: no marker, briefing or mission text.
3. **Tools.** `workflow.search`, `workflow.describe` and `plan.check`, all `AgentEffect::None`.
4. **Output.** A `PlanDraft` (§8.3), a typed proposal shown as a card; it is not a definition and cannot run.
5. **Check.** `plan.check` runs the definition compiler in dry-run mode (doc 38 §6.2) plus the rules of §8.3, and returns typed
   findings; repair quotes one finding per turn within R.
6. **Review.** The plan card shows the checklist with each unit's level, role, budget and cost, the whole-run ceiling, and a diff
   against the nearest authored workflow. The user may edit, reorder or drop units.
7. **Save.** The user clicks **Save workflow** (or **Save and run**, which also counts as the plan-card approval for that run). The
   session writes a user-authored TOML definition through the ordinary loader into the user's workflow folder (never a mission or
   campaign folder, doc 38 §6.1), hash-pinned, with provenance: "drafted by [setup] on [date], saved by you". A plan that is not saved
   never runs. In Auto, the save still needs the click.
8. **Run.** It runs as any user workflow: every nested model step at its own grant, draft-first defaults, journal, undo groups.
9. **Reuse.** The saved workflow appears in the palette; any setup, including a weak local one, can run it at its own levels.

### 8.3 `PlanDraft`: what it may and may not contain [I]

- **May contain**: `call` of registered workflows; registered `code` steps (generators, macros, providers); `pick` and `fill` steps of
  registered `DecisionKind`s with their registered menu providers and checks; `ask`, `approve`, `verify` with registered checks; `map`
  over a stable key with `max_items`; `commit`; typed bindings to inputs or earlier admitted outputs; a registered completion gate.
- **May not contain**: new step kinds, `DecisionKind`s, types, checks, providers or tools; loops other than a bounded `map`; a model
  step without `verify` and `on_fail`; a tool step for a plugin that is not enabled and granted.
- **Stricter than authored workflows (CaMeL's rule made concrete)**: in a `PlanDraft`, `when` may test only workflow inputs, user
  answers from `ask` steps, and outputs of `code` steps computed from trusted state, never a model step's output. So untrusted text,
  which reaches only model slot steps, cannot change which units run.
- **Size**: ≤ ~12 units; the whole-run cost estimate is computed by code from `workflow.describe` data.

### 8.4 Why this is safe enough to propose

- **CaMeL** "explicitly extracts the control and data flows from the (trusted) query; therefore, the untrusted data retrieved by the
  LLM can never impact the program flow", solving "77% of tasks with provable security (compared to 84% with an undefended system) in
  AgentDojo" [V]. The planner sees only the trusted request and code-rendered structure (§8.2 step 2), and §8.3's `when` rule keeps
  untrusted data out of control flow.
- It is Beurer-Kellner et al.'s **Plan-Then-Execute** pattern ("a fixed list of actions to take") [V], not their Code-Then-Execute,
  which stays rejected (doc 59 §4.5).
- **Progent's monotonic confinement**: the plan can only narrow what runs; any rise needs the user [V].
- **Consent** stays with the user: saving a definition is a user gesture with `UserIntent`; Wilco still has no tool that creates or
  edits a definition (doc 38 §2 holds for Wilco; what changes is that Wilco may *propose* one as data).
- **The same capability already exists outside the editor**: a user can ask any external agent to write a TOML workflow and put it in
  their workflow folder, where the loader validates it as data. FR8 brings that path in-app, checked, glass-box and priced.

### 8.5 Saved plans are know-how for weak models

A strong model's composition, once saved, is ordinary harness know-how: typed, checked, versioned and runnable by FR1–FR4 setups. This
is the flywheel of §1.2: the strong model explores, the user curates, the weak model reuses. It is also the cheapest way to spend a
strong model: once per workflow, not once per run.

### 8.6 Strong planner, local executors

ReWOO decouples a planner from executors and reports "5x token efficiency" and "4% accuracy improvement on HotpotQA", and offloads
reasoning "from 175B GPT3.5 into 7B LLaMA" [V]; its offload used instruction fine-tuning of the small model, which Plotroom does not do
(D027 item 6; D048 item 3), so the local half must be tested with presets only (H-FL4, §12). The Plotroom form: a `planner` role bound
to a qualified cloud setup; nested steps bound to the user's local roles; each step at its own grant. Adding a role amends D024 item 4
(owner).

### 8.7 Options for the owner

| Option | What it means | Assessment [I] |
| --- | --- | --- |
| A. No FR8 | The ladder stops at FR7; `NotSupported` shows the nearest workflows only | Safest; leaves "go crazier" unanswered for the one case no workflow fits |
| **B. FR8 as proposal, saved by the user, after v1 (recommended)** | §8.2–§8.6; amends D025 decision 1 to "the model may propose a definition as data; only a user's save makes it runnable" | Keeps every invariant; turns strong-model work into reusable know-how |
| C. FR8 only for external agents over MCP | External agents may submit a `PlanDraft` through a `workflow.propose` tool; the user saves in the editor | Adds no in-app model capability; weaker glass-box story for in-app users |

## 9. Types that teach: the `strict-path` study applied

### 9.1 What the study shows [V]

`strict-path` (v0.2.3, MIT OR Apache-2.0) states its guarantee as a type: "If a `StrictPath<Marker>` value exists, it is already
proven to be inside its designated boundary by construction — not by best-effort string checks" (docs.rs). Its README names "an LLM
tool call" among untrusted path sources, says the API is designed so "LLMs and humans naturally reach for the correct pattern", and
describes "`#[must_use]` with instructions — … When a caller — human or model — loops on compiler output, the message itself teaches
the API", with doc comments that "explain *why*, not just *what*". It ships LLM context files and an `AGENTS.md` for agent use.

**Relevance [I]: high, in two places.** The owner's study is about agents writing code against an API that makes the wrong call
unrepresentable and the compiler's reply instructive. Plotroom has two such agents: the coding agents that will write most of the Rust
harness (AGENTS.md), and Wilco's models at run time.

### 9.2 For the code agents write: grants as witnesses

Plotroom already uses the pattern: `Admitted<T>` has a private constructor; `UserIntent(GestureToken)` is minted only by
`plotroom-session`; `CoreBuilder` cannot `build()` without every check family (commands-undo-history §4.1, §4.2, §4.4) [V per doc]. The
ladder adds one more witness. Sketch only, not compiled; names are not final:

```rust
// plotroom-evals::grant — the only module that can mint a grant (sketch).
mod sealed { pub trait Sealed {} }

/// A freedom level as a type. Sealed, so no other crate can add a level.
pub trait Level: sealed::Sealed + Copy { const CODE: &'static str; }
#[derive(Clone, Copy)] pub struct GuidedPick; // FR2 (one marker per level; each implements Sealed and Level)
#[derive(Clone, Copy)] pub struct Draft;      // FR6

/// "A grant of level `Self` allows any step that needs `Min`." Implemented here only, once per ordered pair.
#[diagnostic::on_unimplemented(
    message = "a `{Self}` grant does not allow a step that needs `{Min}`",
    note = "grants come only from `plotroom_evals::grant::effective`; ask it for this step's level, never construct one",
    note = "if the setup is not qualified for `{Min}`, run the step's authored split instead (doc 21 §3.3)"
)]
pub trait AtLeast<Min: Level>: Level {}

/// Proof that one model setup may take steps of level `L` for one DecisionKind. Private fields, no public constructor.
#[must_use = "a grant proves one step's size; pass it to that step's executor"]
pub struct Grant<L: Level> {
    kind: DecisionKindId, setup: ModelSetupId, preset: HarnessPresetRef, evidence: QualRecordId, _level: PhantomData<L>,
}

/// What the runtime receives. Levels are data at run time, so callers `match` every variant, including "no model".
pub enum EffectiveGrant { NoModel, GuidedPick(Grant<GuidedPick>), /* … */ Draft(Grant<Draft>) /* … */ }

// plotroom-wilco: a Draft executor cannot be called without proof of at least Draft.
pub fn run_draft<L: AtLeast<Draft>>(grant: &Grant<L>, step: &DraftStep, snapshot: &Snapshot)
    -> Result<Proposal<CommandBatch>, Error>;
```

- `#[diagnostic::on_unimplemented]` with `message`, `label` and `note` was stabilised in Rust 1.78 (2024-05-02) [V]; the notes turn the
  compile error into the "comment as prompt" the study describes.
- Levels are data at run time (grants come from qualification records), so AGENTS.md's rule applies: "prefer an internal enum over
  typestate on the outer type". The typestate lives only at the executor boundary; the enum's exhaustive `match` makes every call site
  handle every level, including FR0.
- Doc comments on `Grant`, `effective` and every executor say *why* (which invariant) and *how* (where to get the proof), per AGENTS.md
  "Commenting and Documentation for Context Isolation".
- **Placement is open** (review note). The sketch puts `Grant` in `plotroom-evals` and `run_draft` in `plotroom-wilco`, but crate-map
  §2.2 lists `plotroom-wilco` and `plotroom-evals` as siblings (both → `plotroom-workflow-runtime`) with no edge between them, and
  qualification-record types live in `plotroom-provider` (crate-map §9). The witness type probably belongs in `plotroom-provider`
  or `plotroom-decide` (an allowed edge), with minting behind one function that only the runtime may call (§9.4 option 2). Part of
  design-gap candidate 7.

### 9.3 For Wilco at run time: checkers as teachers

The runtime analogue of "the compiler message teaches the API" is already doctrine [V per docs]: a rejection carries typed findings
and, where code can compute them, the allowed values (commands-undo-history §4.1 `Rejection { findings, allowed, repair }`); repair
quotes one finding per turn (doc 25 §7.2); Teller's diagnostics are model-shaped JSON with `did_you_mean` and `requires`
(validation-and-lints §9). OpenCode appends the language server's errors to the edit result for the same reason (§3.3). The ladder
adds only one step [I]: from FR5 the model may **call the checker before it submits** (`script.check`, a dry-run admission,
`plan.check`), so a strong model loops on the checker's output inside its step budget, exactly as a coding agent loops on `cargo
check`. Doc 61 adds the runtime twin of a witness: opaque, revision-bound handles for symbols and fix menus, which the model can only
copy, so a stale or forged one is refused with a message that says what to redo (its TL;DR, after Qwen Code) [V per doc 61].

### 9.4 Proving a grant cannot be forged under AGENTS.md's rules

AGENTS.md forbids `compile_fail` doctests. Options [I]:

1. **Privacy plus behaviour tests** (now): private fields and a crate-private constructor are enforced by the compiler; unit tests in
   `plotroom-evals` show `effective` returns a grant only with a matching record and never above the product ceiling.
2. **A layering check** (now): like `xtask layers`, which already fails the build when agent-side crates depend on `plotroom-session`
   (commands-undo-history §4.4), an `xtask` rule that only the runtime crate may call `grant::effective`.
3. **Compile-fail tests in a dedicated test crate** (trybuild-style), if a technical decision allows them; they would prove that
   `run_draft` rejects a `Grant<GuidedPick>` and that no crate can build a `Grant` literal. Whether this is allowed is design-gap
   candidate 7. Doc 62 §5.6 answers the technical half (review note): AGENTS.md bans `compile_fail` *doctests*, and trybuild UI
   tests are not doctests; they also snapshot the compiler's text. Doc 62 §8 proposes an AGENTS.md amendment ("Negative Compile
   Tests") that would make them the standard. It awaits the owner.

## 10. External agents and the ladder

- The loopback MCP server exposes the registry's product tools and `workflow.list/start/status/cancel`; externally started runs wait
  for an editor click (agent-runtime §15) [V per doc]. An external agent can therefore already compose product tool calls much as
  FR6–FR7 would, and still writes only through `Proposal` → `Admitted` → undo group, without `UserIntent`.
- `workflow.decide` comes after v1 and its answers are "excluded from model qualification" (agent-runtime §15) [V per doc]. Reading
  [I]: an external decider holds no grant, so it answers only at the step's unqualified default (FR2, FR4 as a confirmed pre-fill).
- The ladder gives qualified in-app models the room external agents already have, through the same doors, and with evidence.

## 11. Tests to write first

Each test fails before the feature exists (AGENTS.md "Test-First / Proof-First"). Crate names follow crate-map and are not final.

| Id | Test | Crate |
| --- | --- | --- |
| T-L1 | Effective level is the minimum of its four terms (property test); changing any term can only lower it | `plotroom-evals` |
| T-L2 | A preset or qualification record above a `DecisionKind`'s product ceiling is clamped, and the loader reports it; a fact-bearing Pick with an FR6 record still runs at FR0 | `plotroom-evals`, preset loader |
| T-L3 | Mid-run the level never rises; a failed FR6 step keeps its admitted commands and finishes the rest as authored FR2 Picks; the journal records the split-down | `plotroom-workflow` |
| T-L4 | FR1–FR4 capsules carry zero tool schemas; an FR5 step calling `catalog.find` is refused with `ToolNotInStep`; the serialized tool list is byte-identical across steps in one level group | `plotroom-wilco` |
| T-L5 | Pull never replaces push: an FR6 capsule golden still contains the code-selected cards | `plotroom-wilco` |
| T-L6 | A Draft that states a raw coordinate or a class id absent from the catalog is refused with allowed values; a Draft using an anchor and a macro is admitted | `plotroom-commands` |
| T-L7 | A `PlanDraft` with an unregistered unit, a loop, a new step kind, a model step without `verify`, or a `when` over a model step's output is refused by `plan.check` with typed findings | `plotroom-workflow` |
| T-L8 | A `PlanDraft` never runs without a save carrying `UserIntent`, including in Auto; a changed plan needs a new save; a nested step runs at its own grant, not the planner's | `plotroom-workflow`, `plotroom-session` |
| T-L9 | The planner capsule contains no `Untrusted` segment (trust-label test) | `plotroom-wilco` |
| T-L10 | The decision record names the level, pushed knowledge ids and pulled calls, and the inspector renders them | `plotroom-wilco`, UI golden |
| T-L11 | A DG012 trigger (model file, runtime, template, wording hash) marks the level grant `requalifying` | `plotroom-evals` |
| T-L12 | Three identical lookups at FR6 stop the step with a plain report | `plotroom-workflow` |
| T-L13 | Mission text claiming a permission ("you may draft the whole mission") changes no level and no result | injection suite |
| T-L14 | An external `workflow.decide` answer is scored and admitted at the step's unqualified default | `plotroom-mcp` |
| T-L15 | §9.4 options 1–2: `effective` never returns a grant without a record; the layering rule fails a crate that calls `grant::effective` outside the runtime | `plotroom-evals`, `xtask` |

## 12. Experiments

Pre-registered hypotheses [I], run with doc 48's 48-U machinery and doc 21 §12.3's reporting (per level, per `DecisionKind`, per
setup; never pooled):

- **H-FL1**: at equal validity (100%) and clobbers (0), a qualified cloud setup at FR7 beats the FR4-decomposed flow on blind human
  preference for the coherence of scenes and dialogue. Doc 25 §11.2's single-prompt control is this arm's nearest existing form.
- **H-FL2**: FR6 pull lookups cut repair turns against push-only cards for the same setup, with no rise in false admits.
- **H-FL3**: FR8 plans pass `plan.check` and are saved without edits in ≥ X% of `NotSupported` requests (X set before the run), with no
  validity loss against the nearest authored workflow.
- **H-FL4** (ReWOO-style): a strong-planner FR8 plan executed by a local 4B model at FR1–FR4 beats the 4B model alone on the brief
  checklist, at lower cloud cost than cloud-only.
- **H-FL5**: FR1 one-pass scoring on sub-2B setups matches FR2 on easy taste menus (doc 53 §5).
- **Kill rule**: a level that does not beat the next-lower level on its instrument is not offered for that `DecisionKind`.
- **Cost note**: FR6–FR8 qualification means dozens of cloud drafts per setup and scenario class; the spend is an owner decision like
  OWQ-27's, not assumed here.

## 13. Design-gap candidates (listed, not filed)

1. **Level vocabulary FR0–FR8** refining the four shapes (doc 21 §3.1, doc 25 §5.1, doc 38 §3.2), including FR7 as a mission-scope
   Draft with replace-the-default semantics, and its final name.
2. **Product ceilings per `DecisionKind`** in the registry, unraisable by presets or qualification (links doc 60 §2.8; doc 53 DP-08,
   DP-16).
3. **The qualification key gains the level and the domain** (DG012; doc 55 §7 item 1; D045 wording).
4. **Tool sets per (chat mode, level group)**, at most three per mode (extends DG023 option B; doc 40 R4–R5).
5. **A dry-run admission Check tool** for draft ChangeSets (commands-undo-history §4.1 step 2).
6. **Pull-tool budgets and split-down records** in the ledger and journal (DG016, DG017).
7. **The `Grant` witness type**, and how to prove a grant cannot be forged without compile-fail doctests (§9.4).
8. **A Draft vocabulary of typed actions plus know-how units** addressed by anchors, so code owns coordinates at FR6–FR7 (doc 19 §8,
   doc 31).
9. **The `PlanDraft` format, `plan.check`, `workflow.search`/`describe`, the entry from `Dispatch::NotSupported`**, and a `ProposeOp`
   form for plans with `AgentEffect::None` (agent-runtime §2: "adding a variant is a design review").
10. **Where saved user workflows live and how their provenance shows** (doc 38 §6.1 covers packs and first-party only).
11. **Off-menu idea cards on `X`** at FR5+, and how code routes them (doc 21 §5.1).
12. **The flywheel's review path**: how a strong model's output becomes a frozen exemplar, card or recipe (doc 55 tuning split; doc 60
    P-15).

## 14. Proposed decision record (not filed)

The text below is offered for the owner to accept, change or reject. It has no number; one is assigned on filing.

> **D0xx: Knowledge lives in the harness; models earn freedom by qualification**
>
> **Status:** proposed, not decided · **To be decided by:** owner (prompted by the direction of 2026-09-28) · **Scope:** how much
> of each step a model may take, and how it reaches knowledge. **Refines:** D009 decision 3, D024 item 1 (shape ceiling), D027 item 2, D037, D045 item 4, D048 item 2.
> **Amends, if option B of doc 63 §8.7 is chosen:** D025 decision 1. **Open parts:** the level names, trial counts and budgets (doc 63
> §4); design-gap candidates 1–12 (doc 63 §13).
>
> **Decision**
>
> 1. **Knowledge and know-how live in the harness**, once, independent of the model: facts in catalogs and Teller, rules in cards and
>    checkers, craft in lenses and lints, procedures in workflows and recipes, patterns in macros and modules. What a strong model
>    teaches us is absorbed as reviewed data, never as model memory or weights.
> 2. **Freedom levels.** Model steps are asked at one of the levels FR0–FR8 (doc 63 §2.1). Effective level = min(product ceiling,
>    qualified level, effort ceiling, the user's per-role cap). An unqualified setup runs FR2, with FR4 only as a confirmed pre-fill.
> 3. **Product ceilings.** Each `DecisionKind` declares the highest level it allows; no preset, grant or setting raises it.
>    Fact-bearing Picks and free-text engine knowledge stay at FR0.
> 4. **Earned per step kind.** A grant belongs to (setup, harness preset, `DecisionKind`, level, domain), is set only by qualification
>    at that level's bar against the next-lower level, and is voided by DG012's triggers.
> 5. **Push always, pull by grant.** Code pushes the step's knowledge at every level; read-only lookup, navigation and check tools are
>    added from FR5 by grant; weak models never fetch.
> 6. **Down automatically, up by the user.** Failures split down along authored decompositions and keep admitted parts; a larger step
>    or a stronger model is a priced button. The level never rises mid-run.
> 7. **The floor holds at every level**: product scope, the command path, the checks, code-owned facts and "done", pinned-field
>    ownership, no silent switch, glass box, untrusted text as data, typed consent, tightening budgets, draft-first, no self-grading or
>    model memory (doc 63 §5).
> 8. **Visible.** The plan card shows how each step is asked; Settings shows the ladder grid of badges; a per-role cap may lower levels.
>    No new dial.
> 9. **(If chosen) Plans as proposals.** A qualified planner may propose a workflow as data built only from registered units; it runs
>    only after the user saves it as their own workflow. Wilco never saves a definition itself.
>
> **Alternatives considered:** one shape per model tier (ignores measured per-kind differences, doc 55); letting strong models supply
> facts (doc 30 §3.4, doc 53 DP-08/DP-16); a fourth "freedom" dial (D024 keeps three); model-written scripts as plans (doc 59 §4.5).

## Open questions

1. **Owner:** FR8 at all, and which option of §8.7? Recommended: B, after v1. [I]
2. **Owner:** must a model-proposed plan always be saved before it runs, or may "run once, don't keep" exist? This doc follows "runs only
   after the user saves it"; runs pin a definition snapshot anyway (doc 38 §6.1, §6.3), so a throwaway run is technically possible. [I]
3. **Owner:** add a `planner` role to D024's closed role list? Recommended: yes, behind an FR8 grant. [I]
4. **Owner:** trial counts per level (14 / 29 / 29 per scenario class) and the spend for FR6–FR8 qualification. [I]
5. **Technical:** are compile-fail tests in a dedicated crate allowed under AGENTS.md's doctest rule (§9.4 option 3)? [I] Review
   note: doc 62 §5.6 reads the ban as covering doctests only and proposes trybuild UI tests through its §8 amendment; the owner
   decides that amendment.
6. **Technical:** three tool-set groups per chat mode, or one per level, given doc 40 R4's cache namespaces? [U until measured]
7. **Design:** user-facing names for the levels and for "largest step" (D034 item 3; doc 02 §9). [I]
8. **Measurement:** does any local setup reach FR5 on script snippets behind Teller, or FR4 on whole-record Fill at 4B? (doc 49,
   doc 53) [U]
9. **Design:** should FR7 exist separately from FR6, or be FR6 with mission scope as a parameter? [I]
10. **Design:** does the know-how unit catalogue (§2.3) cover enough of mission making for FR7 to avoid raw positions entirely? [U]

## Findings for sibling docs (reported, not fixed)

- **Doc 21 §3.1 table and §7.1 shape-ceiling row; doc 25 §5.1–§5.2; doc 38 §3.2–§3.3**: levels refine the four shapes; `tools` and
  `split` keys for FR5–FR7; a possible `plan` form would change doc 38's "closed set of twelve kinds" only if it became a step kind
  (this doc proposes a `ProposeOp` form instead).
- **Doc 30 §4.2–§4.3**: "Model lookups: if qualified" becomes "from FR5 with a grant"; §4.2's Compose row matches FR5. §4.3's
  effort column (no model lookups at Quick or Standard) stays unless the owner changes it (review note; §3.1).
- **Agent-runtime §2, §7, §9**: callable set ∩ level grant; grants per level; chat modes × level groups.
- **Doc 55 §1.4 and D048**: a preset may lower a level, never raise it or a product ceiling.
- **Doc 53 §4.3**'s two-stage cascade stays separate: it is about another model, while the ladder is about step size on the bound
  model.
- **DG023**: per-level groups multiply cache namespaces (doc 40 R4); proposal of at most three per mode.
- **Doc 61 §4.10** says the Teller surface level "is part of the setup's preset (D048)". Reconciliation proposed here: a preset may
  declare a surface level, but the effective level (§4.1) caps it, so a preset never grants more Teller reach than qualification does.
  Doc 61's design-gap candidate 9 ("which freedom level and which autonomy" for draft mode) is answered by §3.1 (FR6) and §6 (D024
  row).
- **Doc 62 §6.3** names the same witness `ShapeGrant<S: Shape>`; one name and one level vocabulary should be chosen with design-gap
  candidates 1 and 7 (review note).
- **Research input correction**: DP-20's local floor is 27B+, not 26B+ (doc 53 §1.2); external deciders are excluded from
  qualification (agent-runtime §15), so they run at the unqualified default rather than "until checked".

## Sources

All read on 2026-09-28 unless noted.

**OpenCode** (MIT), `github.com/anomalyco/opencode` @ `03e67171ab2dc1e7f16e8cebfbc7f778f61b89f0`: `packages/opencode/src/tool/edit.ts:196-201`;
`src/tool/lsp.ts:11-21`; `src/tool/registry.ts:247`, `:297-300`; `src/agent/agent.ts:119-136`, `:156-181`, `:196-218`, `:291`;
`src/session/prompt.ts:1178`; `src/session/processor.ts:29`, `:356-373`; `LICENSE`.

**strict-path** (the owner's public crate): https://crates.io/crates/strict-path (v0.2.3, MIT OR Apache-2.0; the README quoted in
§9.1 is the current one in the repository linked from that page, read 2026-09-28); https://docs.rs/strict-path/latest/strict_path/.

**Autonomy and capability frameworks**

- Feng, McDonald, Zhang, "Levels of Autonomy for AI Agents": https://arxiv.org/abs/2506.12469
- Morris et al., "Levels of AGI": https://arxiv.org/html/2311.02462v5
- Parasuraman, Sheridan, Wickens, "A model for types and levels of human interaction with automation", IEEE TSMC-A 30(3):286–297
  (2000): https://dl.acm.org/doi/10.1109/3468.844354 (not re-read)
- SAE J3016 (2021) summary: https://blog.ansi.org/ansi/sae-levels-driving-automation-j-3016-2021/ (not re-read)
- Karpathy, "Software Is Changing (Again)", YC AI Startup School, 2025-06-17: https://www.latent.space/p/s3;
  https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again
- Miller, "Robust Composition" (PhD thesis, 2006): http://www.erights.org/talks/thesis/ (background on capabilities; not cited in the
  text; not re-read)
- Anthropic, "Measuring agent autonomy" (2026-02-18): https://www.anthropic.com/research/measuring-agent-autonomy
- METR, time horizons: https://arxiv.org/abs/2503.14499, https://arxiv.org/html/2503.14499v4

**Agent security**

- CaMeL, "Defeating Prompt Injections by Design": https://arxiv.org/abs/2503.18813
- Beurer-Kellner et al., "Design Patterns for Securing LLM Agents against Prompt Injections": https://arxiv.org/html/2506.08837v3
- Progent: https://arxiv.org/abs/2504.11703
- Claude Code permission modes and permissions: https://code.claude.com/docs/en/permission-modes,
  https://code.claude.com/docs/en/permissions
- MCP tools specification 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/server/tools

**Planning, tools and context**

- ReWOO: https://arxiv.org/abs/2305.18323
- Agent Skills specification: https://agentskills.io/specification
- Anthropic, "Effective context engineering for AI agents" (2025-09-29):
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, "Introducing advanced tool use" (2025-11-24): https://www.anthropic.com/engineering/advanced-tool-use
- RAG-MCP: https://arxiv.org/abs/2505.03275
- OpenAI function calling (`allowed_tools`): https://developers.openai.com/api/docs/guides/function-calling
- Rust 1.78.0 (`#[diagnostic::on_unimplemented]`): https://blog.rust-lang.org/2024/05/02/Rust-1.78.0/
- Cited through sibling docs, not re-read: arXiv 2511.09030 (MAKER, doc 48), 2510.25820 (doc 21), 2607.05775 and 2411.15399 (docs 21,
  25).

**This repository**

`AGENTS.md`; docs 21 (§1.1, §1.3–§1.4, §2.2, §3.1–§3.3, §4.1, §5.1, §7.1, §8.1–§8.2, §9, §11.5, §12.3, §13.1), 25 (§1, §3, §5.1–§5.2,
§7.1–§7.3, §10.1–§10.3, §11.2), 30 (§3.4, §4.2–§4.4), 31, 38 (TL;DR, §1.1, §2, §3.1–§3.4, §5.4, §6.1–§6.2, §9), 48 (§5.1–§5.2,
§5.5), 53 (§1.1–§1.4, DP-01–DP-20, §4.2–§4.4), 55 (§1.1, §1.4, H-R2, H-Q3, §7), 56 (WR1, WR5, WR6, §9), 59 (TL;DR, §4.5, §5.1, §5.4),
60 (§2.2, §2.8, P-02, P-15), 61 (TL;DR, §4.2, §4.3, §4.10); `docs/architecture/agent-runtime.md` §2, §6, §7, §8, §9, §11, §15;
`docs/architecture/commands-undo-history.md` §4.1, §4.2, §4.4; `docs/architecture/validation-and-lints.md` §9, §13; D006, D009,
D010, D015, D023, D024, D025, D027, D030, D034, D037, D044, D045, D048; DG012, DG016, DG017, DG022, DG023.

## Verification notes

### 2026-09-28, author checks at write-up

- **Re-read at the source**: OpenCode at the pinned commit (every cited line range, the MIT licence, and `prompt.ts:1178` for how
  `steps` is used); the strict-path docs.rs page, crates.io metadata and README quotes; the abstracts or pages of Feng et al. (full
  quote), Morris et al., Progent, METR (§3.2 and §3.2.1), CaMeL, Beurer-Kellner et al., ReWOO, RAG-MCP; Anthropic's autonomy study,
  context-engineering and advanced-tool-use posts; the Agent Skills specification; OpenAI's `allowed_tools` text; the MCP tools spec;
  Claude Code's permission-modes page; the Rust 1.78 release post; the Karpathy talk summary.
- **Repository claims re-read**: D009 decision 3, D024, D025 decision 1, D027, D037, D044, D045, D048; DG012, DG022, DG023; doc 21
  §3.1–§3.3, §7.1, §8.1–§8.2, §9.1–§9.2, §12.3; doc 25 §11.2; doc 30 §3.4 and §4.2–§4.4; doc 38 TL;DR, §2, §3.2–§3.3, §6.1; doc 53
  §1.2–§1.4; doc 55 H-R2; doc 56 §9; doc 59 TL;DR and §4.5; doc 60 §2.2 and §2.8; agent-runtime §2, §7, §9, §15;
  commands-undo-history §4.1–§4.4; validation-and-lints §9.
- **Corrections to the research input, made here**: OpenCode's `explore` agent also allows bash, webfetch and websearch, not only read
  and search tools; `apply_patch` is chosen for `gpt-` ids except `gpt-4` and `oss` ids; `steps` has no default cap (`?? Infinity`);
  doc 53 DP-20 says local 27B+; doc 55 H-R2 is 82 of 90 calls unchanged with and without cards; the Anthropic autonomy quote is cut
  where the page's verified text ends; Feng et al.'s sentence ends "capability and operational environment"; ReWOO's 7B offload used
  instruction fine-tuning; METR's doubling time is 207 days; external deciders are excluded from qualification (agent-runtime §15).
- **Not re-read**: Parasuraman et al., SAE J3016, Miller's thesis (standard references, cited for concepts only); arXiv 2511.09030,
  2510.25820, 2607.05775 and 2411.15399 (through sibling docs).
- **Not verified**: any effect of any level; every number in §4 and §11–§12 is a placeholder.
- **Sibling docs**: doc 61 appeared while this was being written; its TL;DR, §1.1, §4.2, §4.3 and §4.10 were read and §3.1, §3.3,
  §9.3 and the sibling findings were aligned with them (tool names and TS0–TS3). Doc 62 did not exist when this was written.
- **Folding steps, not done here**: a row for this doc in `docs/README.md`; the sibling findings above.
- **Hygiene**: public sources only; `strict-path` is the owner's public crate; no private project, local path, username or key; every
  proposal is [I] and adds no tool with a network, file or process effect. Emphasis inside quotes is rendered with asterisks; the
  bare-URL style of Sources follows the sibling docs.

### 2026-09-28, review of docs 61–63

- **Spot-checked and confirmed at `03e67171`** (a fresh fetch of OpenCode's `dev` branch is still that commit): `tool/edit.ts:196-201`,
  `tool/lsp.ts:11-21`, `tool/registry.ts:247` and `:297-300`, `agent/agent.ts:119-136` (`"*": "allow"`, `doom_loop: "ask"`),
  `:196-218` (explore: grep, glob, list, bash, webfetch, websearch, read), `:291`, `session/prompt.ts:1178` (`?? Infinity`),
  `session/processor.ts:29` and `:356-373` (three identical calls, then a `doom_loop` ask).
- **Confirmed on the page:** Progent's abstract ("the agent's effective action space can only shrink without approval (monotonic
  confinement)"); CaMeL's two quotes; METR v4 §3.2 (207 days, CI 166–240) and §3.2.1 ("4-6x shorter"); Anthropic's autonomy study
  (2026-02-18; roughly 20% → over 40%, 5% → around 9%, "friction", which continues "without necessarily producing safety
  benefits"); Claude Code's permission-modes page (both quotes); OpenAI's `allowed_tools` sentence; Beurer-Kellner et al.'s
  quote and Plan-Then-Execute wording; Feng et al.'s abstract; the docs.rs guarantee sentence and README `#L13`, `#L181-L187`
  quotes for strict-path 0.2.3.
- **Repository claims confirmed:** D009 decision 3; doc 21 §3.3 (both quotes); agent-runtime §7's rule; D024 item 1 and "Effort
  never changes the checks"; D025 decision 1; D027 items 2 and 7; D044 "never shown to users as a badge"; D045's 50 requests a day;
  D048 item 2; doc 53 DP-08, DP-16, DP-20 (27B+); doc 55 H-R2 (82 of 90); doc 30 §3.4; doc 38 TL;DR and §2; doc 56's "never author
  executable plans"; DG011, DG012, DG016, DG017, DG022, DG023 and DG032 exist with the options cited.
- **Corrected or added in this review:** (1) §3.1 and the TL;DR: doc 30 §4.3 allows model lookups only at Thorough and Max, and doc
  61 keeps that rule, while §6's D024 row lets FR5 run at Standard; §3.1 now says the effort gate still applies to pulls. (2) §9.2:
  the sketch needs a `plotroom-wilco` → `plotroom-evals` edge that crate-map §2.2 does not allow; placement is flagged as open, with
  `plotroom-provider` or `plotroom-decide` as candidates. (3) §9.4 option 3 and open question 5 point to doc 62 §5.6 and §8, which
  exist now. (4) §14's draft record said "Decided by: owner (direction of 2026-09-28)", which could read as decided; it now says
  "proposed, not decided" and "To be decided by". (5) Sibling findings: doc 30 §4.3's effort column; doc 61's changed wording
  ("freedom level"); doc 62's `ShapeGrant` names the same witness as §9.2's `Grant<L>`. (6) Sources: Miller's thesis is not cited in
  the text and is now labelled as background.
- **Scope check:** every FR level keeps §5's floor; FR8 adds only `AgentEffect::None` tools and needs a user save with `UserIntent`;
  it amends D025 decision 1 only if the owner picks option B. Nothing here is decided.
- **Not re-verified in review:** ReWOO, RAG-MCP, the Agent Skills specification, Anthropic's context-engineering and
  advanced-tool-use posts, Morris et al., the Karpathy summary.
