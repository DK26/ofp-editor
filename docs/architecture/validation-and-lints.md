# Validation and lints

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`), a decided DG or an owner answer (`OWQ-nn`, all answered 2026-09-27). Type sketches are not compiled and names are
> not final.
> **Part of:** [architecture overview](README.md). **Main sources:** doc 19 §6.5; doc 21 §6.5, §11.1, §12.4; doc 23 §6, §13–§14;
> doc 24 §5; doc 27 §4.5; doc 28 §6.3; doc 31 §7; doc 34 §5; doc 35 §8.3, §9; doc 36 §5; doc 42 §2.8, §6.4; doc 45 §2.6; D003, D011,
> D012; DG005, DG033; `docs/upstream/README.md`.

One validator serves the editor, the headless CLI, registry CI and Wilco's repair loop (doc 45 §2.6). Rules are pure functions over
immutable snapshots; results are revision-stamped and stored per target profile; fixes are ordinary commands; acknowledgements are
fingerprinted sidecar records; codes are data. Teller, the language service, supplies the script checks.

## 1. Principles

1. **"Not run" is never "pass"** (doc 21 §6.5). A rule reports that it ran, did not apply, or could not run and why.
2. **Only what the engine or the target profile cannot run is an error.** Realism, craft and fun findings are advisory and dismissible
   as "intentional"; the tool never refuses, silently corrects or nags about a creative choice (D011).
3. **Every finding has a way out:** a fix, a dismiss, or both (I36-21; doc 21 §12.4).
4. **Fixing never waits for analysis.** Rules read snapshots on workers; a fix re-plans against the live document (doc 45 §2.6).
5. **Risk fails closed.** Unknown risk is shown as unknown, never as safe (doc 24 §5; doc 45 §2.6).
6. **Mission text is data.** Messages never echo mission text as instructions (`AGENTS.md` untrusted content; doc 23 §13.4).

## 2. The framework (`plotroom-validate`)

```rust
pub trait Rule: Send + Sync {                          // pure; no interior mutability
    fn meta(&self) -> &'static RuleMeta;
    fn check(&self, snap: &Snapshot, cx: &RuleCtx<'_>) -> RuleOutcome;
}
pub struct RuleMeta { code: DiagCode, kind: RuleKind, cost: Cost, default_on: bool, profiles: ProfileSet, tier: Tier,
                      reads: DependencySet /* entity kinds and cross-entity keys it reads */ }
pub enum RuleKind { Engine, Profile, Correctness, Craft, Plausibility, Risk }
pub enum RuleOutcome { Ran(Vec<Diagnostic>), NotApplicable(NaReason), Inactive(InactiveReason) }
pub enum InactiveReason { UserDisabled, ProfileUnavailable { missing: CommandSet, request: Option<EngineRequestId> },
                          MissingPack(PackKey), Orphaned, BlockedByError(DiagCode) }
pub struct Diagnostic { code: DiagCode, severity: Severity, targets: NonEmpty<ItemRef>, path: ElementPath, span: Option<DocSpan>,
                        rev: Revision, profile: TargetProfile, fixes: Vec<FixId>, data: DiagData /* typed facts for repair */ }
```

- `ProfileUnavailable` carries the engine-request id (`ER-###`) where one exists, so "Maximum within the engine" is visible in the
  type: the rule cannot run on this profile, and here is the engine change that would let it (D012).
- Only `UserDisabled` is document state (stored in the sidecar); derived inactive reasons are never saved and never undoable (doc 31
  N8; doc 45 §2.6).
- **Where rules live.** The framework, the runner and the engine-structural mission rules live in `plotroom-validate`. Rules that need
  a domain engine live with it and are registered by the session: script rules in Teller, lowering rules in `plotroom-lower`,
  campaign rules (C, CF, SL families) in `plotroom-campaign-compile` and `plotroom-campaign-sim`, catalog and mod rules in
  `plotroom-catalog`, export rules in `plotroom-export` ([crate-map.md](crate-map.md)).

## 3. Severity

```rust
pub enum Severity {
    EngineError,   // the engine cannot run it on any profile, or the file would be corrupt
    ProfileError,  // the mission's target profile cannot run it (fix: another construct, an opted-in capability, another profile)
    Warning,       // runs, but very likely not what was meant (a silent failure)
    Advisory,      // craft, realism, pacing, fun: dismissible as "intentional"
    Info,
}
```

- This one lattice replaces the three proposals' variants and is registered through DG005 before code generation.
- **Realism is a kind, not a severity.** `RuleKind::Plausibility` rules always emit `Advisory`, run only at or above the mission's or
  campaign's realism setting (a visible per-mission and per-campaign dial; level names come from the design round's names table,
  OWQ-08 (a), for which doc 39 §5.1 proposes Cinematic, Grounded, Doctrinal), and offer "intentional" as a dismissal. Generators
  read the same setting as a typed input (D011).
- **Blocking** means `EngineError` and `ProfileError` for the target profile. Nothing else blocks export or Preview.

## 4. Snapshot evaluation

- Rules run on the worker pool over `Arc<Snapshot>`, **costliest first**; per-entity results are cached by `(entity, revision)`;
  cross-entity rules declare dependency sets (syncs, marker names used by triggers and scripts, radio slots) and re-run only when a
  member changed (TrenchBroom, UltimateDoomBuilder; doc 45 §2.6).
- Results carry the revision they were computed at. When the document moves on, the Problems panel shows them with a **"stale" badge,
  never blanked**, until fresh results land.
- During a `Live` group, validation is debounced; on an `Atomic` commit it is scheduled at once
  ([commands-undo-history.md §7](commands-undo-history.md)).
- Every rule runs twice on one snapshot with equal output (determinism test, [testing-strategy.md §7](testing-strategy.md)).

## 5. The code registry (DG005)

- **Codes are data.** DG005 option C (proposal) makes `docs/registry/codes.csv` the only place that assigns final codes (canonical id,
  short code, family, kind, severity, meaning, owner doc, status, superseded-by). Each code also has a data file with its summary,
  "why this matters", fix hint, profiles, suppressibility and at least one **failing and one passing fixture** (Yarn Spinner's
  pattern; doc 45 §2.6).
- `xtask` generates the `DiagCode` enum and `Display` in `plotroom-diag` (L0), a test per fixture, and the Standing Orders "Why?"
  links; a CI drift check fails when the generated code is stale.
- The registry also registers the decision (`Dnnn`), owner-question (`OWQ-nn`) and engine-request (`ER-###`) families, so labels such
  as doc 21's D1–D14, the mod lints D9–D12 and decision records never collide ([decisions README](../decisions/README.md)).
- Families already proposed across the docs: C01–C21 (doc 19), CF01–CF27 (docs 26, 36), MC01–MC31 (docs 28, 34, 36), SL01–SL31
  (doc 29, doc 36), D9–D12 (docs 27, 34, 42), doc 43's variety lints, doc 23's script codes (`type.binary_mismatch` style). All are
  provisional until the registry lands.

## 6. Quick fixes

- Fixes attach to codes, take **explicit targets** and are ordinary commands (`FixCmd`), so they re-plan against the live document and
  land as named undo groups (TrenchBroom; doc 45 §2.6).
- A multi-selection of findings offers only the fixes valid for every selected finding; "Fix all N similar" is one explicitly
  labelled group.
- Wilco proposes a fix by **picking a `FixId`** from the finding's list: a bounded decision a weak model can make (doc 25). Wilco may
  propose, never apply, an acknowledgement.
- Every diagnostic offers "Show on map" (padded zoom to its targets) and "Why?" (its Standing Orders entry, doc 33 §4.4).

## 7. Acknowledgements and suppressions

```rust
pub struct Acknowledgement { code: DiagCode, target: ItemRef, fingerprint: Fingerprint /* of the fields the rule reads */,
                             reason: AckReason, origin: Origin }
pub enum AckReason { Intentional, KnownIssue, Other(LabelText) }
```

- Stored in the shared sidecar (`acks.toml`); valid only while the fingerprint of the fields the rule reads still matches; an
  acknowledgement is an undoable edit (doc 45 §2.6; neither studied editor persisted them).
- Suppressions name one code, a scope (element, mission, campaign) and a reason; there is no "switch off most checks" switch.

## 8. Target profiles, capabilities and the "Requires" badge

- **Per mission and per campaign**, never global: `Cwa199`, `Cwr` (default), `Ce` (D003). The validator stores results per profile.
- **Availability** is recorded per script overload and syntax feature (`plotroom-script-catalog`, generated from pinned CWR release
  snapshots and CE, joined with wiki `since` data and optional owner-local 1.99 evidence; doc 23 §14), per attribute, module, rule
  atom, emitter and file feature.
- **Evidence tiers T1–T4** for `Cwa199` availability (doc 35 §8.3; I35-90) travel with each entry and drive the wording of badges:
  "verified by reading", "probe-confirmed", "unverified on Cwa199" (DG033 item 2 proposal). The data column the tiers need is a data
  pass on `docs/research/data/cwa199-observed-commands.csv`; the executable name scan stays a local, opt-in tool.
- **Capabilities** are engine-request ids: a shipped `ER-###` becomes an opt-in capability of the `Ce` profile (and of `Cwr` if an
  official release ports it). It is switched on only by a visible setting that needs `UserIntent`, never silently by a generator or
  Wilco (`docs/upstream/README.md`).
- **The badge is computed from what the snapshot actually uses and emits** (doc 23 §13.3): `[command]` capabilities and
  profile-only commands raise "Requires"; `[key]` capabilities with a fallback show "enhanced on …"; the mod set adds its
  requirement manifest (doc 42 §2.8). Editor glue stays in the **conservative subset of the mission's profile** (D003 item 5): only
  constructs that profile is shown to run (evidence "verified by reading" or "probe-confirmed", never "unverified"), preferring those in
  `Cwa199 ∩ Cwr ∩ Ce`; a profile-specific construct appears only when the profile allows it, and the badge shows it.

## 9. Teller: the language service

Teller (`plotroom-teller`, D002) is the mission-aware language service. It is a library the editor embeds; an LSP binary is optional
and later (doc 23 §13).

| Capability | Source | Notes |
| --- | --- | --- |
| Engine-parity field checks: `check_field(FieldKind, &[u8], TargetProfile) -> ParityVerdict` | doc 23 §6, §13.3 | `CheckExecute` and `CheckEvaluateBool` modes; first error only, with caret offset; used by admission ([commands-undo-history.md §4.2](commands-undo-history.md)) |
| Lints beyond parity, silent failures first | doc 23 §13.3; doc 31 §7.2 | Label resolution, 4,095-byte SQS lines, Arma-isms, `{…}` bodies |
| Symbol index and references | doc 31 §7.1; doc 37 §5 | Unit names, markers, `markers[]` links (case-insensitive), `respawn_` prefixes, objective ids across HTML and `objStatus`, per-unit briefing sections; runtime-built names listed as "cannot prove" (I37-31IDX) |
| Rename with references | doc 45 §2.3 | One undo group; checked against profile commands, keywords and engine globals |
| Hover, completion, path-resolution hover | doc 23 §8; doc 34 mo02 | Path hover shows which file serves a path in the active mod set; lint MC27 (I34-23-24) |
| Migration tips | doc 34 le09 | Triggered by findings, e.g. a later-game idiom in a `Cwa199` mission (I34-23-24) |
| Risk rows | doc 24 §5.1; doc 34 ed05, ed17 | `saveGame` checkpoints and `setAccTime` get catalog risk rows (I34-23-24) |
| Model-shaped diagnostics | doc 23 §13.4 | Versioned JSON (`schema: 1`) with expected and found types, candidates, `requires`, `did_you_mean` over profile-filtered names |

The catalog excludes the mock `EvalState.cpp` rows and compiled-out cheat commands and keeps the ungated `tri*` harness verbs in a
separate table (doc 23 §13.3 item 5; doc 24 F1).

## 10. Lint families and owners

Doc 35 §9 proposes rows without codes or owners (I35-LINT). This table assigns an owning crate and a family; the codes themselves are
assigned by the DG005 registry.

| Row | Finding | Owner crate | Family | Severity |
| --- | --- | --- | --- | --- |
| rc58 | Structural: item outside list, VEHICLE/GROUP activation without object, unknown `description.ext` key (did you mean), dropped syncs; the importer accepts a missing `;` and preserves bytes | `plotroom-validate` (structure), `plotroom-config` | mission structure | EngineError / Warning |
| rc59 | Endings and debriefs | `plotroom-campaign-compile` | C (doc 19 §6.5) | Warning |
| rc60 | Script defects: enum strings, near-miss globals, unresolved paths, `goto` to a missing label, backward `goto` without a wait, `camCreate` without destroy, code after `exit` | Teller | script (doc 23, doc 24) | Warning |
| rc61 | Names equal to commands in any enabled profile; `endGame` on `Cwr` (it closes the application; ER-023) | Teller | script | Warning / ProfileError |
| rc62 | Campaign state write-only, misspelt or cross-written; `saveStatus`/`loadStatus` mismatch | `plotroom-campaign-sim` | C | Warning |
| rc63, rc64, rc69 | Fragile references and stalls; pacing faults; briefing budgets | `plotroom-validate` craft rules | MC (doc 28 §6.3) | Advisory |
| rc65 | Multiplayer settings | `plotroom-validate` MP rules | MP | Warning |
| rc66 | Catalog and target faults, mod lint packs | `plotroom-catalog` | catalog (doc 27 §4.5) | Warning / ProfileError |
| rc67 | Complexity meter: 1.5 × p90 advisory; 12 units per group and 63 groups per side are errors | `plotroom-validate` limits | limits (doc 34 ed14) | Advisory / EngineError |
| rc68 | Debug leftovers at export | `plotroom-export` | export | Warning at export |
| rc70 | Pre-export completeness gate | readiness model (§11) | gate | Blocking only for engine and profile errors |

Other families folded here: provisional MC20–MC29 from doc 34 §5.1, registered in DG005 with doc 28 §6.3's merges (I34-28); MC25
(camera scene in MP without an audience) and MC26 (an outcome can fire during a cinematic) in v1 with the Cutscene node (I34-32);
MC21 `MomentSlot` (I35-MOMENT); MC30 (each archetype supports at least two non-passive approaches) and CF26 (back-half escalation)
(I36-26); CF27 (ending progress track) (I36-19); the SL family cross-referenced from C and CF (I29-26-19); the D9 redistribution
guard for user-supplied files (I34-02; doc 34 mo10) in `plotroom-export`; doc 42 §6.4's mod lints including D11 (a mod that
redirects the master server) in `plotroom-catalog`. The idiom constraints of doc 37 §4 (for example "protected" and "destroyed at
start" are mutually exclusive on `Cwr`/`Ce`; I37-IDIOMS) are enforced as construction rules in the attribute planner and as
validators for hand-written content.

## 11. Readiness: model, coach and gates

- `ReadinessModel` (pure, in `plotroom-validate`) combines, per target profile: blocking findings; advisory findings; for campaigns,
  Path Explorer coverage (every node reachable, every ending reachable, no dead state; doc 19 §6.4); and the state of an optional
  smoke run in Preview (doc 08; doc 35 rc70).
- **The readiness coach** is a no-AI feature (doc 21 §11.1, model policy `Forbidden`): one dominant control that shows blocking
  versus advisory items, snooze, and an audited "Preview anyway" recorded in the project log (I36-21; doc 36 cv25). It lives in the
  Problems panel ([ui-shell.md §6](ui-shell.md)); Wilco may only phrase its computed items, and every "why" it shows is computed
  (doc 36 cv18, cv31).
- **Export gate:** refuses on blocking findings and `Todo` elements; debug leftovers and D9 are shown for confirmation
  ([game-integration.md §11](game-integration.md)).
- **Preview gate** (doc 24 §5.2): a `deny` finding, or an L4 finding combined with file-read or internet capability, blocks one-click
  Preview; the override names the findings and is stored in project metadata, not in the mission.
- The pre-release self-review checklist (doc 35 rc75) is the lint summary of this model.

## 12. Risk badges and untrusted content

- Every command, config override and pack item carries a risk class from the catalog (doc 24 §5.1). Downloaded missions get risk
  badges for `tri*` verbs reachable under `--test-mission`, `CfgRemoteExec` mode 2, `loadFile` paths and non-literal config values
  evaluated as code (doc 24 §3; ER-021). Unknown classes read as "unknown risk".
- AI-proposed script text passes doc 24 §5.3's policy at admission and is never run automatically.
- Hidden characters (bidi, zero-width, variation selectors, tag characters, private use) in mission and pack text are rendered as
  visible markers and linted (`plotroom-encoding`; doc 21 §9.3; doc 42 §6.4).

## 13. One validator, many clients

| Client | Uses |
| --- | --- |
| Editor | Problems panel, inline squiggles, map glyphs, readiness coach, dialog greying ("why is this greyed out", doc 33 §4.4) |
| `plotroom check` CLI | Headless run over a folder; per-profile report; exit code by blocking count (part of the minimal v1 CLI, OWQ-14 (a)) |
| Admission | Field checks, limits, profile and risk policy ([commands-undo-history.md §4.2](commands-undo-history.md)) |
| Wilco and workflows | Check steps (V-families), one-finding repair turns quoting code, field path, value, why and allowed values (doc 25 §7.2) |
| Registry CI | `plotroom check` per target profile on submitted packs (doc 42 §5.2) |
| Drill | Lesson goals are validator predicates (doc 33 §5.1) |

## 14. Open questions

1. The final severity lattice and family prefixes (DG005).
2. Which realism levels exist and which plausibility rules run at each (doc 39 §5.1; names through the design round's names table,
   OWQ-08 (a)).
3. The fingerprint fields for acknowledgements per rule kind.
4. Whether `ProfileError` should block export for a mission whose profile the user is about to change (a "retarget" preview).
5. Cost annotations and dependency sets for cross-entity rules: measured, not guessed, in M2.
6. How registry CI runs rules that need an install (catalog, terrain) without shipping game data (synthetic packs only).

## Verification notes

### Owner answers folded (2026-09-27)

- §3, §13 and §14 now cite OWQ-08 (a) (names through the design round's names table) and OWQ-14 (a) (the minimal v1 CLI), from
  `OWNER-QUESTIONS.md` as answered on 2026-09-27. No rule, severity or code changed.
