# Can Rust make weak models punch above their weight at coding?

Research doc 64 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered (owner, 2026-09-28, verbatim): "With Rust we can make weaker models punch above their weight at coding." The
owner's mechanism: APIs that lead the user (human or LLM) into correct usage and states, make bad states impossible and make logical
errors easy to spot (typestate, witness and guard types, compile errors that guide, doc comments as prompts; the owner's public
crate strict-path is an example), plus the compiler as a verifier in the loop.

**Status: research, a pilot and proposals.** No Plotroom code was written for this doc. The experiment (design, crates, tasks,
harness, analysis scripts) is research tooling under `tools/rust-weak-models`, a standalone workspace that evaluates the
development process, not a product feature; its run records stay local (§6 step 11). The one related rule change is `AGENTS.md`'s
"Fast inner loop, full gates at the end" (section "Local Repo-Specific Rules"), adopted by the owner on 2026-09-28 from the input
that §4.9 evaluates. Plotroom was never built or run. Every design proposal is [I]. This doc changes no decision.
**Epistemic legend** (doc 16's, extended as in docs 61–65). **[V]** read at the cited source on 2026-09-28. **[V-author]** a number
published by the cited authors, not reproduced by us; "(abstract)" or "(full text)" says what was read. **[V, pilot]** measured by
our pilot run of 2026-09-28. **[V, probe]** observed by compiling probe crates with rustc 1.98.1 and clippy 0.1.98.
**[V, model-free]** measured by the harness without any model (reference solutions, mutants). **[V, simulation]** our Monte Carlo
power simulation. **[V per doc N]** taken from a sibling doc. **[I]** our inference or proposal. **[U]** unknown until measured.
**Relation to sibling docs.** Doc 62 studies strict-path and type-driven guidance; its `AGENTS.md` amendment (witness and guard
rules, "Diagnostics as Guidance", trybuild "Negative Compile Tests") was applied on 2026-09-28, and its §9.1 proposes a
coding-agent misuse evaluation. Doc 61 designs Teller as the model's instrument (push findings, one root per repair, stop on
repeat). Doc 63 sets freedom levels FR0–FR8 (accepted as D051). Doc 65 applies the same principle to mission scripts; its §6
experiment mirrors this doc's design and asks to be re-aligned once this doc exists (done in §5.3 and "Findings for sibling
docs"). Docs 21 and 25 own the verifier-loop doctrine; docs 44, 46, 49 and 55 own the local models, pins, sampler rule and
per-model presets (D048); doc 48 owns the budget-capped cloud backend. `AGENTS.md`'s fast-loop rule (clippy on one crate, then
that crate's targeted unit tests, full gates once at the end) came from the owner's input after the pilot (§4.9, §5.1). This doc
adds the evidence review, the experiment, its pilot and the next iteration's design (§3.9).
**Names.** *PLAIN* and *GUIDED* are the two API variants of the experiment (§3.2). *Whole-file* and *unit-sized* are the two task
shapes of the next iteration: one file per task, or one function at a time against a compiling skeleton (§3.9). *GUIDED-L* is
GUIDED plus a lint table fed back through clippy (§3.9). *R0* is a model's first attempt; *R≤3* is the outcome after up to three
compiler and visible-test repair rounds (per unit, in the unit-sized shape). *Accepted but wrong* means the code compiles and
passes every visible test, so a loop would report success, but fails a hidden test: the "logical error" the theory is about.
*Trap classes*: S (GUIDED rejects the mistake at compile time), F (GUIDED forces handling of an `Option` or `Result`, but
`.unwrap()` escapes), R (checked at run time in both variants; a control). *Clearance*: a diagnostic kind present in round *r*'s
feedback that no longer appears in round *r+1*'s (§4.5). *Wilco* is Plotroom's in-product agent; *Teller* its script checker and
language service.
**Hygiene.** Public sources only. Model outputs are paraphrased; no local paths, user names or keys. Research proposals P64-A1 to
P64-A3, P64-S1 to P64-S6 and P64-W1 to P64-W5, hypotheses H1–H7 and decision rules DR1–DR14 are this doc's labels.

## TL;DR

- **Partly, and not yet for the part that is the owner's own.** (1) *Rust alone does not help weak models.* One-shot, Rust is the
  hardest of five languages for every model tested, and "the gap between Rust and the other languages grows substantially in the
  smaller models" [1] [V-author, full text]. (2) *Rust with the compiler in the loop does help, and helps weak models most.* Rust
  gains the most from a feedback round "because Rust's compile-time diagnostics are detailed and explicit" [1]; on repository-level
  Rust a 9B model with a compile loop reaches 30.3–48.3% functional correctness, about a frontier model's 32.0–43.3% without one
  [12] [V-author, full text]. Type information at decode time or in context helps small models most in repair (Gemma 2 2B repair
  pass@1 11.6 → 20.9) [13, 18, 19]. (3) *The owner's specific claim*, that APIs built to lead (typestate, witnesses, newtypes,
  fix-naming diagnostics) cut weak models' logical errors, **has no published measurement**. The nearest evidence is human studies
  [24] and runtime guards [26].
- **Our pilot ran and sat on the floor.** Three local 3–4B models (Qwen3.5-4B, Gemma 4 E4B, Granite 4.1 3B), 34 tasks × 2 APIs,
  one sample, up to three repair rounds: **0 of 204 correct at R0; at R≤3, 2/102 PLAIN and 2/102 GUIDED** [V, pilot]. Every
  paired sign test gives p = 1.0; the H1 estimand on this pilot is exactly 0.0 points (one task each way). It cannot discriminate.
- **Why the floor:** a slip in the shared task spec, identical in both arms, whose rustc error (E0618, "expected function, found
  `Refusal`") names no fix. It was cleared in 9 of 318 repair rounds; GUIDED's custom fix-naming errors in 11 of 28; rustc's own
  `?` errors, which name the missing `From` impl or the `Try` requirement, in 55 of 189 [V, pilot, descriptive]. Errors that say
  what to do get fixed; the one that does not almost never is. The custom notes did not beat rustc's own good notes.
- **Model-free, the mechanism exists.** Of 13 trap mutants, all compile under PLAIN and 9 pass its visible tests silently; GUIDED
  rejects 8 at compile time, 6 with its custom fix text; its 5 misses are the predicted escapes (`.unwrap()`, a minutes value
  wrapped as seconds, same-typed swaps, off-by-one indices) [V, model-free].
- **Compile time is not the bottleneck; reaching the tests is** (owner input, §4.9). Of the pilot's 8.4 wall-clock hours,
  generation took 97.7% (decoding 78.5%, prompt evaluation 18.6%), cargo 2.3% (median 0.6–1.0 s per round) and tests 0.01%
  [V, pilot]. Only 12 of 806 rounds compiled, so tests ran in 12, and visible-test failures reached a model in 3. The owner's
  principle, validate with unit tests rather than a complete compilation on each change, therefore applies to the **task shape**:
  the next iteration adds *unit-sized* tasks (one function at a time against a compiling skeleton, that function's tests as spec
  and feedback, hidden tests still scoring the whole) as a second factor beside PLAIN/GUIDED (§3.9).
- **Clippy is the right inner-loop command, and a lint arm is simple to add.** Warm, clippy costs 0.64–0.69 s per round against
  the pilot's 0.87–0.89 s build step [V, probe], and only clippy carries a lint table's reasons to the model (doc 62 §3). But lints
  run only on code that type-checks: with any type error present, no lint text is printed [V, probe]. A lint arm (GUIDED-L) cannot
  touch the hint-less E0618 wall and speaks only once the slip is gone, which is why it sits behind the spec fix (§3.9).
- **Reading [I].** For 3–4B models writing whole Rust files against an unseen API, neither API lifts them off the floor. At that
  size the lever is the harness (small typed steps, findings that name the fix, stall detection), which is what Plotroom already
  designs for Wilco (docs 21, 25, 61, 65) and what the unit-sized shape tests for code. Whether guiding APIs cut accepted-but-wrong
  code for 7–30B models or for strong coding agents is still **open**.
- **What remains to test:** remove the shared slip; apply the pre-registered floor rule (it fires: one worked example in both
  arms); replace Granite; add a 7–14B coder and the 30B-A3B comparator; build the unit-sized shape and the lint arm; re-pilot both
  shapes until PLAIN R≤3 lands between 20% and 60% in at least one and name it the primary shape; freeze; run Stage 1 (about 2,430
  episodes, about 55–130 h of local GPU at the pilot's pace, against 40–55 h for one shape); then Stage 2 (types versus text) and
  doc 62 §9.1's bypass test for strong coding agents (§6).
- **For Plotroom now:** the owner adopted `AGENTS.md`'s "Fast inner loop, full gates at the end" rule on 2026-09-28 (clippy on
  one crate, then that crate's targeted unit tests; full gates once); §4.9 backs its cost side. No other `AGENTS.md` change is
  justified by an effect estimate. Three refinements are backed by probes and the pilot's diagnostics and are proposed on top of
  doc 62's applied amendment (P64-A1 to A3, §5.1). The plugin SDK and Teller take the "hint-less error" lesson and the unit-sized
  scaffold (§5.2, §5.3); doc 65's experiment should adopt the calibration step and the shape factor.

## 1. The theory

### 1.1 Four mechanisms

The owner's theory combines four mechanisms. They are separable, and the literature measures them separately:

1. **The compiler as a verifier in the loop.** A strict compiler rejects a large class of errors and says where; a harness feeds
   that back to the model.
2. **Guiding APIs.** Typestate, witness and guard types and newtypes turn a *logical* error (the wrong sequence, a missing
   check, a mixed-up id) into a *compile* error, so it enters the loop instead of shipping silently.
3. **Actionable diagnostics.** `#[diagnostic::on_unimplemented]`, `#[must_use = "…"]` and similar hooks let a library author
   write the fix into the compiler's reply [28, 30].
4. **Doc comments as prompts.** Instructions in the API listing ("call `validate` first; building from data? use `AnyPlan`")
   reach the model as context.

### 1.2 Why it could hold

- Most errors in LLM code that a compiler can see are type and name errors, not syntax: syntax is about 6% of compile errors in
  TypeScript [13] [V-author, full text]. Rust's type system sees more of them than most [I].
- External feedback is what small models lack. Self-repair is "bottlenecked by the model's ability to provide feedback on its own
  code" [14] [V-author, abstract], and self-correction works in tasks "that can use reliable external feedback" [16] [V-author,
  abstract per research pass]. A compiler is a reliable external critic.
- A model can only repair what the loop sees. Moving a trap from "compiles, fails later" to "does not compile" puts it inside the
  loop (the design's H3).

### 1.3 Why it could fail

- **Rust is harder for small models** [1, 2, 11]; ownership and lifetimes are a tax even for humans [25].
- **Complex types confuse models.** Armin Ronacher: "LLMs have little clue how to read any of this", and in his tests a type check
  in the agent loop "showed worse performance" [34] [V, opinion]. Typestate generics are rare in training data.
- **Many rustc errors carry no guidance a library can change.** A type mismatch (E0308), a missing method (E0599) or calling a unit
  variant (E0618) cannot be annotated: the stable diagnostic attributes hook only trait obligations and impls [30] [V per doc 62
  §3.1; V, probe].
- **Escape hatches.** Agents use TypeScript's `any` nine times as often as humans [20]; Rust's equivalents are `.unwrap()`, `.clone()`
  and casts. A forced `Option` becomes a runtime panic.
- **Compile-clean is not correct.** Rewards from a linter alone pushed small models "toward shorter completions that reduce lint
  errors without reliably improving functional correctness" [17] [V-author, abstract].
- **Longer listings cost tokens** and may distract a small context.

### 1.4 What would count as support

The theory needs a comparison that holds "Rust plus a compiler" fixed and varies only the API design, with a metric for code that
compiles and passes the visible checks but is wrong. No published study does this (§2.7). §3 is that comparison.

## 2. Evidence

Kind: **M** measured by the authors; **O** opinion or practice report; **D** a design fact. Tags as in the legend.

### 2.1 Rust against other languages

| Source | Setting | Result | Kind |
| --- | --- | --- | --- |
| PROBE, 2026 [1] | 1,651 problems, 5 languages, 6 models | Rust lowest for every model; the gap "grows substantially in the smaller models" [V-author, full text]. Per a research pass: Qwen2.5-Coder-7B passes 0.25 in Rust (0.31 compile failures) against 0.36 in Python (0.01) [V-author, full text per research pass] | M |
| Multi-LCB, 2026 [2] | LiveCodeBench in many languages | Rust and Scala lowest; some reasoning models above 60% in Python stay under 30% in Rust [V-author, abstract per research pass] | M |
| MultiPL-E [3] | 18+ languages | "Type annotations have limited impact on model performance for gradually typed languages" [V] | M |
| SWE-bench Multilingual [4] | SWE-agent + Claude 3.7 Sonnet, agentic | Rust 58.14% (25/43), the highest; C/C++ 28.57% [V] | M |
| Multi-SWE-bench [5] | 1,632 issues, 7 languages | Rust mid-pack, behind Java [V-author, full text per research pass] | M |
| Rust-SWE-bench, ICSE 2026 [6] | 500 repository tasks, 34 repos | Best ReAct-style agent 21.2%; RustForger 28.6% with Claude Sonnet 3.7; hampered by repository structure and "Rust's type and trait requirements" [V-author, abstract] | M |
| RustRepoTrans [7] | Repository-level translation into Rust | DeepSeek-R1 drops from 73.7% to 51.5% pass@1 once repository context is involved [V-author, abstract per research pass] | M |
| Unreliable in Practice?, 2026 [8] | 86,726 erroneous samples, 7 models, 4 compiled languages | Error types vary strongly by language and model. Per a research pass, Rust compile errors: 43.4% incompatible parameter types, 20.5% missing imports, 16.7% ownership or lifetimes, 6.1% trait bounds [V-author, full text per research pass] | M |

**Reading [I].** One-shot, Rust is hard and hardest for small models. With a compiler and tests in an agent loop, rankings flip or
scatter. No single "Rust is easier or harder for LLMs" number exists, and the largest error buckets are wrong types or arguments
and missing or hallucinated names, not the borrow checker: exactly what domain types and explicit signatures can shrink.

### 2.2 The compiler in the loop

| Source | Setting | Result | Kind |
| --- | --- | --- | --- |
| PROBE [1] | One feedback round | Average +0.05 pass@1; "Rust shows the largest improvement … Because Rust's compile-time diagnostics are detailed and explicit" [V-author, full text] | M |
| Generative Compilation, 2026 [12] | Repository-level Rust, 7 models; code owns the loop | Mean compile-error rate 65.9% (no feedback) → 20.7% (post-generation loop) → 13.1% (checks during generation). Qwen3.5 9B functional correctness: Translation 8.3 → 30.3 → 33.3%; UpdatedAPI 10.0 → 48.3 → 41.7%. Claude Opus 4.8 without feedback: 32.0% and 43.3%; with it 61.0–86.7%. Qwen 9B needed more than 10 restarts on 40.9% of tasks (GPT 5.3 Codex 2.1%) and "often regenerate[s] the same erroneous prefix". Building a constrained decoder "from scratch for real Rust would be highly complex and costly" [V-author, full text] | M |
| RustAssistant, ICSE 2025 [10] | Real Rust compile errors, GPT-3.5/4 | Peak accuracy "roughly 74%" [V-author, abstract]. Prompt format dominates: GPT-4 on 270 micro-benchmarks 139 → 196 → 247 → 252 fixed as line prefixes, localization and "explain first" are added; clippy findings fixed 74.86% against clippy's own auto-fix 31.50% [V-author, full text] | M |
| CRUST-Bench, COLM 2025 [11] | C to safe Rust, 100 repositories | o1 solves 15 single-shot [V-author, abstract]; compiler-only repair adds up to +37 points build success; Llama-3-8B solved none [V-author, full text per research pass] | M |
| SafeTrans, 2025 [9] | C to Rust with guided compiler feedback | GPT-4o 54 → 80%, DeepSeek-V3 49 → 79%; 7B–70B models roughly double; E0277 and E0308 are the largest error share, up to 30% for 7B models [V-author, full text per research pass] | M |
| Iterative self-repair across scales, 2026 [15] | 7 models, HumanEval/MBPP | +4.9 to +17.1 points on HumanEval, +16.0 to +30.0 on MBPP; "most gains concentrate in the first two rounds"; assertion (logic) errors are the hardest, about 45% repaired [V-author, abstract] | M |
| Olausson et al., ICLR 2024 [14] | Self-repair at equal cost | Gains "often modest … and are sometimes not present at all"; better feedback from a stronger model gives "substantially larger" gains [V-author, abstract] | M |
| Weiss et al. [45] | C-to-Rust translation | "When the translation system uses feedback loops the differences across models diminish" [V per doc 62] | M |

**Reading [I].** The loop is where Rust pays, and the harness shape (localized edits, grouped errors, about two rounds, stop on
repeats) matters as much as model size. Weak models stall by repeating themselves.

### 2.3 Type information at decode time and in context

| Source | Result | Kind |
| --- | --- | --- |
| Type-constrained decoding, PLDI 2025 [13] (TypeScript; Gemma 2 2B–27B, 32–34B models) | Syntax-only constraining cuts compile errors 9.0% (HumanEval) and 4.8% (MBPP); type constraining 74.8% and 56.0% in synthesis. Repair pass@1: Gemma 2 2B 11.6 → 20.9 (+79.4%), Gemma 2 9B 24.0 → 34.9, CodeLlama 34B 17.5 → 27.4; synthesis gains only +0.3 to +8.0% relative. Median runtime +39.1% and +52.1% [V-author, full text] | M |
| Monitor-guided decoding, NeurIPS 2023 [18] | A static-analysis monitor lets SantaCoder-1.1B beat text-davinci-003 on compile rate [V per doc 61] | M |
| Typed holes (ChatLSP), OOPSLA 2024 [19] | Type definitions in context were the most useful single context; error rounds on top multiply the gain [V per doc 62] | M |
| Type-error ablation, 2026 [44] | qwen2.5-coder 14B repairs more with a proximate type error and its location; more verbosity adds little [V per doc 62] | M |
| DocPrompting, ICLR 2023 [23]; RustEvo², 2025 [22] | Docs in context make unseen APIs usable; Rust APIs after the training cutoff: 56.1% → 32.5% success, behavioural changes 38.0% against 65.8% for stabilisations, retrieval +13.5% [V-author, abstract] | M |

**Reading [I].** Types help small models most where they *repair*; one-shot gains stay small. No type-constrained decoder exists for
Rust [12], so for Rust the practical channels are the loop and the context.

### 2.4 APIs that encode invariants

| Source | Result | Kind |
| --- | --- | --- |
| Obsidian, OOPSLA 2020 [24], n = 20 humans | Typestate and asset types: participants "were able to successfully complete more of the programming tasks than the Solidity participants", who "commonly inserted asset-related bugs, which Obsidian detects at compile time" [V-author, abstract] | M (humans) |
| Bronze RCT, ICSE 2022 [25], 428 students | With an optional garbage collector, finishers needed "about a third as much time (4 hours vs. 12 hours)"; students named "ownership, borrowing, and lifetimes" as the obstacles [V-author, abstract] | M (humans) |
| Token Budgets, 2026 [26] | A 1,180-line affine-typed safe-Rust crate: zero cap violations in 160 live-API tests; the asyncio equivalent overshot 30/30 [V-author, abstract] | M (runtime guard, not LLM authors) |
| Agents and `any` [20]; API misuse [21] | Agents use `any` 9× as often as humans in TypeScript PRs [V-author, abstract]; thousands of API misuses by 7B models and Copilot, mostly hallucination and intent misalignment [V-author, abstract per research pass] | M |
| strict-path [31, 32] | "wrong code either doesn't compile, or the compiler tells you exactly what to do instead"; no `AsRef<Path>` or `Deref`, because either "would let anything call .join() … and build a new path that skips boundary validation"; `#[must_use]` with instructions; doc comments and `LLM_CONTEXT_FULL.md` "designed for LLMs with function calling" [V]. No published misuse-rate measurement (doc 62 §1.5) | D |

**Reading [I].** Domain invariants in types help humans and hold at run time. Nobody has measured whether they make LLM *authors*
commit fewer logical errors. Borrowing and lifetimes are a separate tax from domain typestate.

### 2.5 Guiding diagnostics: the hooks exist, the measurements do not

Stable Rust gives library authors `#[diagnostic::on_unimplemented]` with `message`, `label` and repeatable `note` (1.78) [28], and
`#[diagnostic::do_not_recommend]` (1.85) [29] [V per doc 62]. Doc 62 §3 maps where each text lands and which feeds keep it. The only
study of better-worded compiler errors we found is on students: GPT-4-written explanations beat stock compiler messages "in only 1
of the 6 tasks", while "handwritten explanations still outperform" both [27] [V-author, abstract]. Custom `on_unimplemented` notes are
handwritten, but no study measures their effect on LLM repair. §4.5 gives our descriptive numbers.

### 2.6 Opinion and practice (not measured)

Practitioner reports credit rustc with catching agents' hallucinations and dead code, while the bugs left are business logic
[36–38] [V, opinion]. Ronacher recommends Go for agentic backends for its simplicity [33], argues against type-level
cleverness for agents [34] and asks for explicit types, local reasoning and greppable names [35] [V, opinion]. This agrees with the
measured data: types help when simple, local, explicit and actionable.

### 2.7 What the evidence says, and what it does not

**Measured:** Rust alone hurts weak models; Rust plus a compiler loop helps them most and shrinks the gap to strong models; type
context and type-level decoding help small models most in repair; loops need stall detection and about two rounds; compile-clean
must never be the success metric. **Not measured anywhere we found:** whether API design (typestate, witnesses, newtypes,
fix-naming diagnostics) reduces LLMs' compiles-but-wrong errors, and at which model size. That is the gap §3 targets.

## 3. Experiment design and harness

### 3.1 Questions and hypotheses

A pre-registration draft, written before any model call (design version 0.1.0-draft, 2026-09-28) [I]:

- **RQ1** Against an unseen library, do small local models write more correct programs when the API is GUIDED rather than PLAIN,
  with identical functionality? **RQ2** Does GUIDED reduce accepted-but-wrong programs? **RQ3** Is the repair loop worth more under
  GUIDED? **RQ4** Does a small model with GUIDED reach a larger model's PLAIN level? **RQ5** (exploratory) Which ingredient carries
  the effect (static rejection, forced handling, instructive text), at what token cost?
- **Fixed-sequence tests** at α = 0.05, stopping at the first non-rejection: **H1** hidden pass at R≤3 is higher for GUIDED, small
  models pooled; **H2** accepted-but-wrong is lower for GUIDED (reported as support only if H1's estimate is not below −5 points);
  **H3** the loop's gain (R≤3 minus R0) is larger for GUIDED; **H4** per small model, GUIDED at R≤3 is non-inferior to the
  comparator's PLAIN within −10 points (Holm across models). Two-sided: a harmful result is plausible and informative.
- **Predicted pattern:** the reduction in trap failures ranks S > F > R ≈ 0. If class R improves too, the gain is more likely the
  instructive text than the types.
- **Added after the pilot** (design 0.2.0-draft, written before any run of the new arms; §3.9): **RQ6** Do unit-sized tasks raise
  small models' correctness over whole-file tasks, and does the API effect differ by shape (H5, H6)? **RQ7** Does routing GUIDED's
  lint guidance through clippy (instruction-style `disallowed-methods` reasons, deny-level `must_use`) add to GUIDED (H7)?

### 3.2 Domain and the two APIs

A synthetic "mission-builder" domain, loosely inspired by classic mission editors but claiming no engine fidelity: groups of units
with ranks, waypoint plans (MOVE, SEEK_AND_DESTROY, HOLD, GET_IN, GET_OUT, CYCLE), synchronisations, triggers with activations,
timers and endings, validation rules R1–R11 and a canonical text export. Both variants sit on one hidden core, so exports are
byte-identical by construction; the same "Domain rules" sheet goes to both.

| Concern | PLAIN (idiomatic, runtime-checked) | GUIDED (leads to correct use) |
| --- | --- | --- |
| Ids | `u32` unit, group and trigger ids | Unforgeable `GroupId`, `UnitId`, `VehicleId`, `WaypointRef`, `TriggerId`: no numeric constructor; from `add_*` or `lookup_*(label) -> Option` |
| Units | Plain `f64` seconds, metres, degrees | `Pos::new -> Result`, `Seconds::from_minutes`, `Metres::from_km`, `Degrees` |
| Plans | `add_waypoint(group, Waypoint)`; sequence rules checked by `validate()` | `Plan<Open / Mounted / Closed>`: `move_to` needs `AcceptsWaypoints`, `get_out` needs `IsMounted`, `hold` and `cycle` close the plan; `AnyPlan::apply(Order)` for data-driven plans |
| Triggers | Struct with public fields; `Timer::new -> Result` | `TriggerBuilder<NeedsActivation / Ready, Once / Repeating / Ends>`; `ends_mission` needs `FiresOnce` |
| Validate, export | `validate(&self) -> Result<(), Vec<MissionError>>`; `export()` does not re-validate (documented) | `Mission<Draft>::validate(self) -> Result<Mission<Validated>, ValidationReport>`; only `Validated` exports; `into_draft()` to edit again |
| Docs | Idiomatic rustdoc with `# Errors` sections | Doc comments written as instructions |

**Construction rule from the probe** [V, probe]: `on_unimplemented` text reaches the model only through a trait-bound obligation
(E0277). A **method-level** `where State: Trait` bound prints the custom message and `fix:` note; the same bound on the impl block
gives E0599 with the custom text dropped, and an inherent impl on one state gives E0599 with only "the method was found for
`Plan<Open>`". Passing an `Option<GroupRef>` where the proof value is expected gives a plain E0308 with no `?` or `match`
suggestion. So every GUIDED sequence rule is a method-level bound on an `on_unimplemented` trait.

### 3.3 Traps and tasks

- **Thirteen trap categories in three classes.** S: SEQ-CYCLE, SEQ-HOLD, SEQ-MOUNT, SEQ-EXPORT, ID-MIX. F: REF-SYNC, REF-VEHICLE,
  EMPTY-GROUP. R (controls): TIMER-ORDER, BOUNDS, ERR-HANDLING. Mixed S/F: UNIT-MEASURE, ACT-RULE.
- **Thirty scored tasks** in tiers A–D (6/8/8/8) plus four pilot tasks. One entry point:
  `solve(&Input) -> Result<Exported, Refusal>`; `Exported` has a private constructor, so only the library can write export text.
  Traps sit in natural phrasing ("also stop by the fuel depot" next to a loop; timers given in minutes). T01 and T03 carry no
  trap; seven tasks (T18, T19, T20, T23, T24, T27, T29) measure typestate's cost on data-driven, generic and collection code.
- **Tests.** Visible: one or two nominal tests per task, never touching a trap. Hidden: 167 tests, 97 of them trap tests, asserting
  through an independent parser and rule checker; never fed back.

### 3.4 Loop, prompts and fairness

- Up to three repair rounds feeding back rustc diagnostics from `cargo test --no-run` (errors first, 6,000-character cap; no clippy,
  no lint table) or visible-test failures; R0 is the first attempt of the same episode (same prompt, seed and sampler), so the
  no-loop arm costs nothing extra.
- Identical system text, rules sheet, task text, inputs, visible tests and sampler; only the API listing differs. Listings come from
  one generator (3,007 against 6,680 estimated tokens); by default the shorter prompt is padded with neutral example exports to equal
  length (8,976 against 8,974 estimated tokens). Diagnostics are blinded (`mb_guided::X` → `mb::X`).
- Thinking off; temperature 0.6 with each vendor's other sampler values (doc 49's rule); max 3,072 tokens per reply.

### 3.5 Statistics, power and decision rules

The task is the unit of inference, with errors clustered by task [39]: a sign-flip randomisation test (100,000 flips) on 30
task-level paired differences, task-cluster bootstrap intervals, and an equivalence test at ±5 points if H1 fails. pass@k uses the
unbiased estimator [41], consistency across samples is reported as pass^k [42], and the setting is reported in Dai et al.'s schema
(inputs, tool access, repair-time feedback, validation, budget) [40]. A standard-library power simulation (500 repetitions per
cell) gives, for 30 tasks and 6 samples per model, 74–91% power at +10 points and 91–99% at +13 [V, simulation]; task count, not
samples, is the lever. Effects under about 7 points are not reliably detectable, so a null result will usually read
"inconclusive".

| Rule | If | Then [I] |
| --- | --- | --- |
| DR1 | H1 ≥ +10 points and accepted-but-wrong not worse | Theory supported for 3–4B models on this domain: `AGENTS.md` gains the diagnostic-shape rule and unforgeable ids for agent-facing APIs; Plotroom's typed command layer and script compiler name the fix; run Stage 2 |
| DR1b | +5 to +10 | Adopt only the cheap parts (diagnostic shape, instructive docs) |
| DR2 | Gain only after the loop | Guided APIs only together with a mandatory verifier loop; round budgets in the doc 55 presets |
| DR3 | Harm (interval below 0) | Keep typestate out of agent-facing surfaces |
| DR4 | Equivalent within ±5 | Type-safety rules stay human code-quality rules; stop citing them as a weak-model lever |
| DR5 | Inconclusive | A new pre-registration, more tasks rather than more samples, no pooling |
| DR6 | H4 holds for a model | "Punches above its weight" may be said for that model, domain and loop only |
| DR7 | GUIDED tokens per success > 1.5× PLAIN | Flag the token cost; trim docs before dropping types |
| DR8 | Models disagree in sign | Per-model knobs in the presets |

Stage 2, only if H1 passes: a 2 × 2 of type structure × guidance text, to separate types from docs and diagnostics. The next
iteration's shape factor and lint arm add DR9–DR14 (§3.9).

### 3.6 The harness as built

Under `tools/rust-weak-models`: five std-only Rust crates (shared spec, hidden core, PLAIN, GUIDED, independent oracle), 34 tasks
with reference solutions in both variants, 68 generated test crates, and a standard-library Python runner with an
OpenAI-compatible client for llama-server. The model writes one file under `#![forbid(unsafe_code)]`; a static scan rejects
process, file, network, environment and include escapes; cargo runs `--offline --locked` with a 20 s limit per test binary.
Records are JSONL per round and per episode (tokens, timings, diagnostic codes, trap results, escape-hatch counts); they stay
local (the folder ignores `results/`). Evidence [V, model-free]: 68/68 reference runs pass every visible and hidden
test; 406 workspace tests and the pilot version's 27 harness unit tests pass (the packaged folder's README records its current
suite); the two references produce byte-identical exports or refusals on all 202
test inputs; mock runs prove repair from fed-back diagnostics. This is a research harness only; no product capability executes code.

### 3.7 Model-free result: the static catch rate

For 13 trap mutants in 11 tasks (a solution that makes exactly one trap mistake) [V, model-free]:

| | PLAIN | GUIDED |
| --- | --- | --- |
| Rejected at compile time | 0/13 | 8/13 (6 by E0277 with the custom `fix:` text: depot after the loop, move after hold, repeating ending, dismount without boarding, export without validation, edit after validation; 2 by E0308: an integer used as an id, a position used as a unit id) |
| Visible test fails (the loop sees it) | 4/13 | — |
| Silent (visible pass, hidden fail) | 9/13 | 5/13: minutes wrapped as `Seconds::new`, `.unwrap()` on a lookup, `.unwrap()` on `cycle()`, swapped same-typed sides, 1-based numbers used as indices |

A mock "perfect repairer" that fixes whatever the loop shows ends GUIDED 7/11 correct and PLAIN 3/11. So the mechanism the theory
needs exists and is sized; whether models use it is the pilot's question.

### 3.8 Deviations from the draft (to fold in before freezing)

Numbers are `f64`; a shared hidden core plus a conformance command replace the separate byte-identity suite; no
`rust-toolchain.toml` (it could trigger a download offline; the rustc version is recorded per run instead); the listing generator
is Python and drops `on_unimplemented` text as rustdoc does; equal-budget padding was added; context 24,576 instead of 16,384 (a
~9k system prompt plus repair feedback plus a 3,072-token reply does not fit in 16k); `Pos::new` takes `f64` metres; mutants cover
13 traps, not one per trap test. Not built yet: the frozen analysis script, the lock file, the cloud comparator backend and the
independent idiomaticity and neutrality reviews.

### 3.9 Next iteration: task shape and the lint channel (design 0.2.0-draft)

Written after the pilot and the owner's input (§4.9), before any run of the new arms. §3.1–§3.5 stay as they are; this adds a
second factor, one arm, three hypotheses and six decision rules [I].

**Unit-sized tasks (the owner's principle as a task shape).** Each scored task is split into 2–4 units along its reference
solution's natural steps; the references are small (median 17.5 code lines in PLAIN and 20 in GUIDED; the largest, T30, 69 and
68), and GUIDED's already use 1–4 functions [V, model-free]. The harness writes a compiling skeleton: each unit's signature and a
doc comment taken from the task text, with a `todo!()` body. The last unit is `solve` itself, whose tests are the task's existing
visible tests. The model fills one unit per step:

- **Loop per unit:** `cargo check -p <task crate>` (clippy in GUIDED-L) → that unit's visible tests → next unit; up to three
  repairs per unit. An exhausted unit keeps its last compiling body, else its stub, and the episode moves on, so per-unit pass
  rates stay measurable at the floor. The system text, rules sheet and API listing are the whole-file arm's, so prefix caching
  still applies.
- **Scoring is unchanged:** the hidden tests score the whole `solve`, never fed back; *accepted but wrong* keeps its meaning (every
  visible test passes, a hidden test fails).
- **Fairness rules:** per-unit visible tests are nominal and never touch a trap (as §3.3); unit boundaries and names come from the
  task text, never from a trap, and the decomposition joins the independent neutrality review (§3.8); both variants get the same
  decomposition. A GUIDED skeleton's signatures name its states and units (`Plan<Open>`, `Metres`): that is part of what GUIDED
  means at unit size and is reported, not hidden. Unit-sized episodes make more, shorter calls, so the per-episode cap on
  generated tokens equals the whole-file arm's (4 × 3,072) and every result is reported both as pass at R≤3 and as pass per
  GPU-hour.
- **The build becomes visible at this size:** cargo takes 0.6–2 s of a 9–17 s unit round (below), a tenth or more rather than the
  pilot's 2%, so the loop checks one crate against prebuilt dependencies and runs only that unit's tests (a test-name filter), as
  `AGENTS.md`'s fast-loop rule does.

**The lint arm (GUIDED-L).** GUIDED plus a lint table, with feedback from `cargo clippy` instead of the build output, per doc 62
§3.1's channel table:

- `clippy.toml` `disallowed-methods` entries for `Option::unwrap`, `Option::expect`, `Result::unwrap` and `Result::expect`, each
  with an instruction-style `reason` and no `replacement` ("a lookup can miss: `match` on it, or use `.ok_or(Refusal::…)?` with the
  refusal the task names"), so the text arrives as a note on the error [V, probe];
- `#[must_use = "…"]` messages naming the next step on GUIDED's state-carrying values (plans, trigger ids, the validated mission;
  GUIDED has none today), with `unused_must_use` and clippy's `let_underscore_must_use` at deny;
- levels set as `#[forbid(…)] pub mod solution;` in the generated `lib.rs`, so they bind the model's file only and cannot be
  allowed away inside it; the static scan counts `allow` and `expect` attributes in the solution as silencing (doc 62 §9.1's
  metric);
- no `-D warnings`: other warnings are fed back after errors but do not fail the round, because 11 of the pilot's 12 compiling
  rounds carried a rustc warning and would have failed under it (the pilot's warnings were mostly unused imports, §4.9);
- two harness fixes found by the probe: the generated `lib.rs` trips clippy's `write_with_newline` in every task crate (and its
  `let _ = write!(…)` would trip `let_underscore_must_use` if the levels were crate-wide), and `rwm/cargo.py` filters feedback by
  package, not file, so the arm must keep only diagnostics with spans in `solution.rs` [V, probe].

PLAIN gets no lint arm: a table of reasons would itself be guidance, and clippy's default lints are warnings that change no
outcome.

**How the lint arm interacts with the spec slip** [V, probe unless tagged]:

1. **It sits behind the same wall.** rustc runs late lints, which include every clippy lint and `unused_must_use`, only once the
   file type-checks: with an E0308 or E0618 present, the probe printed neither the `disallowed-methods` error nor the `must_use`
   error. In the pilot 794 of 806 rounds did not compile (38 of them had no complete code block), so a lint arm on the pilot's
   tasks would have spoken in at most 12 rounds [V, pilot].
2. **It cannot fix the hint-less error.** E0618's text is the same under clippy. Only the spec (§6 step 2) or a harness-side
   rewrite (§6 step 12) changes it.
3. **It adds errors of the kind that get cleared.** A reason note names the fix, like GUIDED's custom notes (cleared 11/28) and
   rustc's `?` notes (55/189), not like E0618 (9/318) [V, pilot, descriptive].
4. **It carries its own hint-less step.** A `must_use` error comes with rustc's help "use `let _ = ...` to ignore the resulting
   value"; following it passes `cargo check` but fails clippy's `let_underscore_must_use`, whose error says only "consider
   explicitly using expression value", without the custom message. That is the E0618 pattern in a new place; the prediction is low
   clearance for that code unless the `must_use` message itself names the sanctioned use [I].

So the order is fixed: remove the slip first, then run GUIDED-L; it is most informative at unit size, where the skeleton compiles
and each unit is small enough to type-check early.

**Hypotheses.** H1–H4 keep their fixed sequence in the primary shape, named at freeze: the shape whose PLAIN R≤3 lands in the
20–60% band on the calibration tasks, unit-sized if both do; if neither does, the floor rule loops and nothing is frozen.

- **H5 (shape)** Hidden pass at R≤3 is higher unit-sized than whole-file, small models and both APIs pooled. Its own family at
  α = 0.05 (it tests the owner's unit-test principle, not the API theory), tested like H1 on 30 task-level paired differences.
- **H6 (shape × API, secondary)** GUIDED − PLAIN is larger at unit size. Reported as an estimate with its interval; an interaction
  needs about four times the episodes of a main effect for the same power, so no rule rests on it alone.
- **H7 (lint arm, secondary)** GUIDED-L has fewer accepted-but-wrong programs and fewer `.unwrap()` escapes than GUIDED in the
  primary shape, without losing pass at R≤3. Model-free prediction: the two `.unwrap()` mutants of §3.7 become compile-time
  rejections with the reason text, so GUIDED-L's static catch rate is 10/13 against GUIDED's 8/13 (to be run, §6 step 6).

**Arms and GPU budget** (30 scored tasks, three small models):

| Arms | API | Shape | Feedback | Samples per task | Episodes | Minutes per episode | GPU hours |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A, B | PLAIN, GUIDED | Whole file | rustc (`cargo test --no-run`) | 6 | 1,080 | 2.0–3.1 by model, mean 2.5: the pilot's floor pace [V, pilot] | 40–55 |
| C, D | PLAIN, GUIDED | Unit-sized | rustc (`cargo check`), then the unit's tests | 6 | 1,080 | 0.7–1.3 if most units pass within two rounds; 1.8–3.4 at the floor [I] | 13–61 |
| E (GUIDED-L) | GUIDED | Primary shape | clippy with the lint table | 3 | 270 | 0.7–3.1 [I] | 3–14 |
| Stage 1 | | | | | 2,430 | | about 55–130 |

The unit round estimate, 9–17 s, uses the pilot's own rates: a median uncached prompt of 715–1,428 tokens at 132–234 tokens/s
(5–7 s), a function body of 100–300 tokens at about 38 tokens/s (3–8 s), and 0.6–2 s of cargo (a warm check or clippy of about
0.65 s, plus the unit's test build and run when it type-checks); a whole-file round took a median 23–39 s of generation [V,
pilot; I for the unit sizes]. Floor pace is 3 units × 4 rounds; success pace 3 units × 1.5 rounds. The re-pilot measures these
and replaces the range before freezing. If an owner budget cap binds, cut the non-primary shape to 3 samples first: 30 tasks × 3
samples still gives 80–91% power at +13 points (55–68% at +10) [V, simulation].

**Metrics.** Primary: hidden pass at R≤3 of the whole task. Secondary: accepted but wrong, hidden share, escape hatches in the
final file. Process metrics, the owner's own measures: the time split per round (generation with prompt evaluation and decode,
cargo, tests); the share of rounds that compile and that reach tests, by round index; per-unit pass rate and rounds per unit;
per-code clearance, lint codes included; tokens and GPU seconds per success; and how many rounds `-D warnings` would have failed
(from the records' warning counts, without an extra arm).

| Rule | If | Then [I] |
| --- | --- | --- |
| DR9 | H5 holds with unit-sized ≥ +10 points and accepted-but-wrong not worse | The owner's principle holds for weak models on this domain: weak-model coding work in Plotroom is unit-sized by default (a compiling skeleton, one function per step, its tests as spec and feedback): the plugin SDK's scaffold (P64-S6), doc 65's script tasks, Wilco's slots (P64-W1) |
| DR10 | +5 to +10 points | Unit-sized work only for models below the calibration band, as a per-model preset (doc 55) |
| DR11 | Equivalent within ±5 | Task shape is not the lever at this size; test feedback text and examples next (§6 step 12) |
| DR12 | Harm (interval below 0) | Units that pass alone do not compose into a correct whole; keep whole-file tasks and use per-unit tests only as extra checks |
| DR13 | GUIDED-L halves accepted-but-wrong or final-file `.unwrap()` against GUIDED and loses at most 5 points of pass at R≤3 | Lint reasons are a weak-model lever: P64-S5 and `AGENTS.md`'s `clippy.toml` reason rule gain an effect estimate |
| DR14 | GUIDED-L loses more than 5 points, or its lint codes clear less often than GUIDED's custom notes | Lints crowd the repair budget: for weak models, deny-level lints move to the final gate, set per model in the presets (doc 55) |

## 4. Pilot results

### 4.1 What ran

All 34 tasks × 2 variants × one sample, rounds R0–R3, for three local models on llama.cpp's llama-server with thinking off (0
reasoning characters in every round), all at temperature 0.6: Qwen3.5-4B Q4_K_M (top_p 0.8, top_k 20), Gemma 4 E4B QAT
(UD-Q4_K_XL file; top_p 0.95, top_k 64) and Granite 4.1 3B Q4_K_M (official GGUF, pinned; its card gives no sampler, so top_p and top_k were disabled
per the design rule). 204 episodes, 806 generations, no context overflow, no infrastructure error; weight hashes and system-prompt
hashes are in the run records. The Qwen arm was interrupted after 21 episodes and resumed with a guard that refuses to append
unless model, tasks, sampler, rounds, seed, context, budget and system-prompt hash match; seeds depend only on task, sample and
round. Prompt budgets balanced on each server's tokenizer (Qwen 7,658/7,673, Gemma 7,844/7,855, Granite 7,038/7,051 tokens).
Wall time: about 2.0–3.1 minutes per episode.

### 4.2 Outcomes

All 34 tasks per arm, one sample [V, pilot]:

| Model | Arm | Pass R0 | Pass R≤3 | Compiles at R≤3 | Accepted but wrong | Mean hidden share R≤3 | Tokens / episode | Generation s / episode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | PLAIN | 0/34 | 2/34 (T22, P02) | 6/34 | 1/34 (T25) | 0.104 | 47.6k | 147 |
| Qwen3.5-4B | GUIDED | 0/34 | 1/34 (P01) | 1/34 | 0/34 | 0.029 | 47.7k | 136 |
| Gemma 4 E4B | PLAIN | 0/34 | 0/34 | 1/34 (T25) | 1/34 (T25) | 0.012 | 50.4k | 178 |
| Gemma 4 E4B | GUIDED | 0/34 | 1/34 (T25) | 1/34 | 0/34 | 0.029 | 51.9k | 180 |
| Granite 4.1 3B | PLAIN | 0/34 | 0/34 | 0/34 | 0/34 | 0 | 44.1k | 108 |
| Granite 4.1 3B | GUIDED | 0/34 | 0/34 | 0/34 | 0/34 | 0 | 45.7k | 123 |

### 4.3 Paired comparisons

Scored tasks only (30), pass at R≤3, one sample per cell [V, pilot]:

| Model | PLAIN only | GUIDED only | Both | Neither | Sign test p | Mean hidden-share difference (GUIDED − PLAIN) |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | 1 (T22) | 0 | 0 | 29 | 1.0 | −0.085 (PLAIN higher on 5 tasks) |
| Gemma 4 E4B | 0 | 1 (T25) | 0 | 29 | 1.0 | +0.020 |
| Granite 4.1 3B | 0 | 0 | 0 | 30 | 1.0 | 0 |

At R0 every cell is "neither". The H1 estimand (per-task mean over the three models of GUIDED − PLAIN at R≤3) is +1/3 on T25,
−1/3 on T22 and 0 elsewhere: **0.0 points**. H2 to H4 have nothing to test; the comparator was not run.

### 4.4 Why the floor: friction both arms shared

1. **A shared spec slip with a hint-less error.** The shared `Refusal` enum has unit variants (only `Many` carries data), and the
   models wrote `Refusal::OutOfMap(label)`. Episodes containing it: Qwen 26/34 PLAIN and 29/34 GUIDED, Gemma 30/34 and 32/34,
   Granite 8 and 9. rustc 1.98.1 answers "error[E0618]: expected function, found `Refusal`" with the label "call expression
   requires function"; a local enum adds "`Refusal::OutOfMap` defined here", an enum from another crate not even that, and there is
   no "remove the parentheses" help [V, probe re-run]. In 45 (Qwen PLAIN), 25 (Qwen GUIDED), 42 (Gemma PLAIN) and 23 (Gemma
   GUIDED) failing rounds it was the **only** compile error. No stable diagnostic attribute reaches E0618 [30], so a library author
   cannot fix this text; only the type's shape or the harness can [I].
2. **Error conversion.** The most frequent E0277 in both arms was "`?` couldn't convert the error to `Refusal`": models applied
   `?` to library results inside `solve`, which returns the task's `Refusal` [V, pilot].
3. **Truncation.** 40 generations (Qwen 12, Gemma 15, Granite 13) hit the 3,072-token cap; 38 of them never closed the code block
   and counted as format failures. T30, the largest brief, hit it in both variants.
4. **Stalls.** Granite resubmitted byte-identical code in 59 of 102 repair rounds in each arm (Qwen 13/99 and 13/100, Gemma 18/99
   and 9/100) and never compiled; its errors were mostly unresolved imports and paths (E0432, E0433), E0277, E0308 and E0599.

### 4.5 Which diagnostics got fixed

Clearance per repair transition (round *r* failed to compile; the kind appears in *r*'s feedback; cleared if no diagnostic of that
kind appears in *r+1*'s), counted once per kind per transition [V, pilot, descriptive]:

| Diagnostic kind | Guidance in the text | Qwen P | Qwen G | Gemma P | Gemma G | Granite P | Granite G | Pooled |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E0618 on a unit `Refusal` variant | None | 2/57 | 1/78 | 3/75 | 3/80 | 0/12 | 0/16 | **9/318 (3%)** |
| E0277 with GUIDED's custom `fix:` note | Names the fix | — | 5/14 | — | 5/6 | — | 1/8 | **11/28 (39%)** |
| E0277 from `?` (conversion, or not a `Result`) | Names the missing `From` impl or the `Try` requirement | 17/20 | 13/18 | 3/3 | 18/29 | 3/64 | 1/55 | 55/189 (29%) |
| E0308 mismatched types | Expected and found | 11/18 | 9/62 | 8/22 | 21/39 | 7/49 | 3/66 | 59/256 (23%) |
| E0599 no method or unmet bounds | Sometimes where the method exists | 5/12 | 11/22 | 3/16 | 8/20 | 3/17 | 3/48 | 33/135 (24%) |
| Any compile failure → compiles next round | — | 6/96 | 1/100 | 0/99 | 1/100 | 0/102 | 0/102 | 8/599 |

Without Granite, which cleared almost nothing: custom fix notes 10/20, rustc's `?` notes 51/70, hint-less E0618 9/290.
**Reading [I]:** an error that states what is missing or what to do is cleared often; the one with no hint almost never. GUIDED's
handwritten notes did not beat rustc's own informative notes (Qwen: 5/14 against 30/38), so "some hint beats no hint" is supported,
"custom beats stock" is not. **Caveats:** kinds differ in difficulty (not a causal comparison); an earlier-phase error in round
*r+1* can hide a later-phase one, which overstates clearance; E0618 came in bursts of about four identical blocks per round, which
crowded the 6,000-character feedback. The per-block method used during the run (a block counts as fixed only when every identical
copy is gone) gives lower E0618 rates (0/18 to 15/326) and the same ordering.

### 4.6 What GUIDED cost

- **Compile rate.** Qwen compiled 6/34 PLAIN files at R≤3 against 1/34 GUIDED; Gemma 1 and 1; Granite 0 and 0 [V, pilot]. For
  Qwen this is the complexity tax DR3 describes, but at n = 34, one sample and a shared blocker it is a direction, not an estimate.
- **Newtype and typestate mismatches.** Qwen's repair rounds carried E0308 in 62 GUIDED transitions against 18 PLAIN.
- **A stray `?` on infallible steps.** 134 GUIDED blocks read "the `?` operator can only be applied to values that implement
  `Try`": the models put `?` on calls that return a `UnitId`, a `Plan`, a `TriggerId` or an `Exported` directly. A surface that
  mixes fallible and infallible steps invites the guess that every step is fallible [I].
- **Escape hatches.** `.unwrap()` in the final files: Qwen 18 PLAIN against 36 GUIDED, Gemma 16 against 20, Granite 18 against 15,
  as the probe predicted for `Option`-returning lookups [V, pilot].
- **GUIDED's own errors did reach the models.** 16 "`get_out` needs a mounted plan, but this plan is `mb::Open`" and 13
  "`Mission<Draft>` cannot be exported: only a validated mission can be exported" errors, each with its `fix:` note.

### 4.7 The two anecdotes

- **Gemma, T25 ("every problem at once"), in the theory's favour.** PLAIN compiled at R0, passed the visible test and failed three
  of four trap tests (ERR-HANDLING and SEQ-EXPORT): accepted but wrong. GUIDED failed to compile at R0 on ordinary errors (an import,
  a `?` conversion), was repaired at R1 and passed all five hidden tests. One of the two trap categories is class R, a control, so by
  the pre-registered reading the text, not the types, may have carried it. n = 1.
- **Qwen, T22 ("bearing and distance"), against.** PLAIN solved it; GUIDED never compiled. n = 1.

### 4.8 What the pilot shows and does not show

- **Shows [V, pilot]:** 3–4B local models, thinking off, cannot write whole Rust files of this size against an unseen API of
  3–7k tokens, with either API, even with three compiler rounds; the shared spec, not the API variant, dominated the failures; the
  loop's clearance depends on whether the error names a fix; Granite 4.1 3B stalls.
- **Does not show:** any effect of GUIDED on correctness or on accepted-but-wrong code, in either direction; anything about 7–30B
  models, cloud models or strong coding agents.
- **The pre-registered floor rule fires:** every small model's PLAIN R≤3 is below 10% (Qwen 2/34, Gemma 0, Granite 0), so the design
  adds one worked example to both variants before freezing.
- **A pilot-policy deviation:** the draft said pilot tasks P01–P04 alone calibrate difficulty, but this feasibility run used all
  34. Local models do not learn from the run, so the models are not contaminated; the risk is ours (tuning tasks after seeing
  outcomes). The deviations log must record it, and §6 step 1 offers two remedies.
- **Compute:** at the floor every episode used all rounds (about 45–52k tokens), so Stage 1's 1,080 small-model episodes would take
  about 40–55 GPU hours at this pace, not the draft's 20–25; early stops shorten it once models succeed. With the unit-sized factor
  and the lint arm, about 55–130 (§3.9).

### 4.9 Where the time went, and the owner's input

After the pilot the owner suggested (2026-09-28, verbatim): "Let me also suggest, that the correct way writing Rust, would be using
unit tests to validate everything, because a complete compilation on each change, would take far longer", and on the feedback
command, "cargo clippy is better, no?". The run records answer the first for this harness (`analysis/time_split.py`) [V, pilot]:

| Model | Rounds | Generation, share (min) | Prompt eval / decode (min) | Cargo, share (median / p90 per round) | Tests | Rounds that compiled | Rounds with test failures fed back |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | 267 | 97.4% (160) | 30.9 / 128.5 | 2.6% (0.84 / 1.74 s) | 3.8 s | 10 | 3 |
| Gemma 4 E4B | 267 | 97.8% (203) | 31.3 / 171.0 | 2.2% (0.97 / 1.52 s) | 0.5 s | 2 | 0 |
| Granite 4.1 3B | 272 | 97.9% (131) | 32.1 / 97.4 | 2.1% (0.63 / 0.84 s) | 0 | 0 | 0 |
| All | 806 | 97.7% (494) | 94.3 / 397.0 | 2.3% (0.77 / 1.47 s) | 4.3 s | 12 | 3 |

Per round, medians by model (Qwen, Gemma, Granite): generation 30.7, 39.2 and 22.9 s; prompt 10,714, 11,488 and 10,002 tokens,
of which uncached 1,428, 715 and 1,144; completion 882, 1,216 and 606 tokens; decoding 37.9, 36.7 and 39.5 tokens/s; prompt
evaluation 234, 132 and 172 tokens/s. Compiling rounds by round index: Qwen 0/68 at R0, then 3/68, 3/66 and 4/65; Gemma 1/68 at
R0 and 1/67 at R1, none later; Granite none. Cargo medians are over the 768 rounds that reached cargo.

- **Compile cost is not the bottleneck here.** Each round builds one small task crate against prebuilt dependencies in about a
  second; decoding alone took 73–82% of wall time and prompt evaluation 15–24%, although prefix caching kept the uncached part of
  each prompt near a tenth. Recorded generation, cargo and test time cover 99.8% of the wall-clock time between rounds.
- **Reaching the tests is.** Tests ran only in the 12 rounds that compiled, and visible-test failures were fed back in 3 (Qwen
  PLAIN: T26 twice, T08 once); every other compiling round either passed its visible tests or was the last. The unit tests already
  were a feedback channel; the models almost never got to it.
- **So the principle applies to the task shape [I].** Give weak models unit-sized work: one function against a fixed, compiling
  skeleton, with that function's tests as spec and feedback. This is Plotroom's harness doctrine for Wilco (one small bounded
  decision per step, code owns the structure) and doc 65's snippet-sized tasks, applied to code. §3.9 makes it the next
  iteration's second factor.
- **Clippy costs no more than the pilot's build step.** Warm, on one task crate (T22 GUIDED, three runs each): `cargo clippy
  --all-targets` 0.64–0.69 s, `cargo check --all-targets` 0.61–0.64 s, the pilot's `cargo test --no-run` 0.87–0.89 s [V, probe].
  Only clippy carries a lint table's reasons to a model (doc 62 §3.1), so it is the right inner-loop command, with one limit: lint
  text appears only once a file type-checks (§3.9). §3.9 adds the lint arm.
- **Warnings would block a `-D warnings` loop.** 455 of the 768 rounds that reached cargo carried rustc warnings (975 in all), and
  so did 11 of the 12 rounds that compiled; in the saved feedback, 403 of 432 warning headings are unused imports.
- **For Plotroom's own workspace** the owner's premise (a complete compilation per change is far slower than checking one crate) is
  the basis of `AGENTS.md`'s "Fast inner loop, full gates at the end" rule, adopted on 2026-09-28 (§5.1). Plotroom's build times
  were not measured here [U].

## 5. Implications for Plotroom

### 5.1 Coding agents building Plotroom (`AGENTS.md`)

Doc 62 §8's amendment is already in `AGENTS.md` (witness and guard types, "Diagnostics as Guidance", trybuild negative tests).

**Adopted on the owner's input (2026-09-28):** `AGENTS.md`, section "Local Repo-Specific Rules", now has "Fast inner loop, full
gates at the end": while changing code, `cargo clippy -p <crate> --all-targets -- -D warnings`, then that crate's unit tests
filtered to the module under change, written test first; the full workspace gates once before finishing; units kept small enough
that the loop stays in seconds. What this doc adds to it: clippy costs no more per round than a build step (§4.9) [V, probe]; it is
the only command that carries the workspace's guidance lints to an agent (doc 62 §3.1); and its lint text appears only once the
crate type-checks, so compile errors come first in any case [V, probe]. One caveat, for weak models only: `-D warnings` turns an
unused import into a failed round; it would have failed 11 of the pilot's 12 compiling rounds (§4.9). The rule's readers are
mostly strong agents, for whom that is a one-line fix, so no change is proposed; the lint arm (DR13, DR14) and §3.9's `-D
warnings` count decide whether weak models' presets should defer deny-level warnings to the final gate. The rule rests on
build-time facts, not on an effect estimate from this experiment.

The pilot supports none of `AGENTS.md`'s other rules by an effect estimate, and weakens none. Three refinements follow from the
probes and the pilot's diagnostics; all are **proposal-only**, pending the owner, and phrased to satisfy "Maintaining This File"
(general, no reference to this study):

| Id | Where in `AGENTS.md` | Proposed change | Evidence | Status |
| --- | --- | --- | --- | --- |
| P64-A1 | "Diagnostics as Guidance", "Where the attributes go" | After "guidance-bearing bounds on functions (`fn f<T: Trait>(…)`)", add: "or on the method's own `where` clause (`fn get_out(self) -> … where S: IsMounted`); a method that exists only in an inherent impl for one state, or behind a bound on the impl block, fails with E0599 and none of the custom text" | [V, probe]; 6 of 8 GUIDED compile-time catches used it (§3.7); the text reached the models (§4.6) | Proposal; one sentence |
| P64-A2 | "Diagnostics as Guidance", new bullet | "**Where no attribute reaches.** A type mismatch, a missing method or a call on a unit variant carries no custom text. For mistakes that surface that way, put the guidance in type and method names and the doc comment, or reshape the API so the likely mistake cannot arise or is correct as written" | Hint-less E0618 cleared 9/318 rounds against 11/28 (custom) and 55/189 (rustc's own `?` notes) [V, pilot, descriptive]; proximate errors carry repair [44] | Proposal |
| P64-A3 | "Type Safety", newtypes and witness rules | Reconcile the newtype rule ("Provide `from_raw`") with the witness rules: "An id that a store issues and whose existence proves the entity exists is a witness: `from_raw` stays crate-private; values from storage or the wire re-enter through a checked lookup returning `Option` or `Result`" | ID-MIX mutants rejected at compile time (§3.7) [V, model-free]; cost: more E0308 and `.unwrap()` in GUIDED (§4.6) | Proposal; a witness-surface rule, so a design-gap request and a UI test per `AGENTS.md` (candidate 1 below) |

**Not proposed:** typestate on more surfaces. The pilot's Qwen compile gap, Bronze [25] and Ronacher [34] argue for keeping
`AGENTS.md`'s "Typestate at in-process seams, enums in storage" as the limit. **For Plotroom's actual coding agents** (mostly strong
cloud models in a repository with a shell), the relevant measurement is doc 62 §9.1 (bypass and silencing rates), which this
harness can host (§6 step 12) [I].

### 5.2 The plugin SDK

The experiment's setting is exactly a plugin author's agent: an unseen library read from a listing, one file to write, a compiler
in the loop. Doc 62 §7 designs typed WIT and a Rust guest SDK with manifest-derived compile-time grants. Proposals [I]:

- **P64-S1 Test the SDK on models before publishing it:** a small SDK task suite run through this harness with one small local and
  one strong model, in both shapes, reporting pass, accepted-but-wrong, per-code clearance, escape hatches and the share of rounds
  that reach the tests. A diagnostic code with low clearance is an SDK design bug.
- **P64-S2 Guidance where rustc shows it:** every sequence or grant rule as a method-level bound on a sealed `on_unimplemented`
  trait (P64-A1); a trap trait is safe there because the guest cannot implement it (doc 62 §3.3).
- **P64-S3 Make the likely guess correct:** SDK errors convert into the plugin's result type with `?` (`From` impls), result enums
  have one construction shape a model will guess, and builder steps are either all fallible or visibly named, so none of §4.4
  items 1–2 or §4.6's stray `?` can recur.
- **P64-S4 Short listing plus one worked example per workflow** in the SDK's `LLM_CONTEXT.md`, beside doc 62 §7.3's "compiles but
  wrong" list: the pilot's floor rule fired without one [23].
- **P64-S5 Close the `.unwrap()` escape in the scaffold:** clippy `unwrap_used` and `expect_used` at deny in the plugin template's
  lint table (the pilot doubled `.unwrap()` under GUIDED for Qwen). This helps honest authors only; the host still enforces grants
  at run time (doc 62 §7.2). Where the fix depends on the SDK, a `disallowed-methods` entry whose reason names it (as in GUIDED-L)
  says more than the generic `unwrap_used` text. Two details from the probe: lints speak only once the file type-checks, so they
  help after the compile errors are gone; and levels set with `forbid` on the scaffold's module cannot be allowed away inside it
  (§3.9). DR13 gives it an effect estimate.
- **P64-S6 Scaffold unit-sized work:** the plugin template ships a compiling skeleton (signatures, doc comments, `todo!()` bodies)
  with one test per function, and `LLM_CONTEXT.md` tells an agent to fill one function at a time: `cargo clippy -p` on the plugin
  crate, then that function's tests (the `AGENTS.md` fast loop). Evidence so far is the pilot's process data (tests reached in 12
  of 806 rounds, §4.9); DR9–DR12 decide whether it becomes the default for weak models.

### 5.3 Wilco and Teller, by analogy

Wilco never writes Rust, but its typed command layer is a GUIDED API and Teller is its compiler. Proposals [I]:

- **P64-W1 Weak models fill slots, not files.** At whole-file scale both APIs floor for 3–4B models [V, pilot]. This supports doc 31
  §9, doc 30's measurement and doc 65 §5.3's table (FR0–FR4: typed IR slots and menus, no script text) and argues against letting
  sub-5B setups write scripts even in the Strict dialect until a snippet-sized experiment says otherwise. The owner's unit-test
  principle is the same idea for code; the unit-sized shape (§3.9, DR9–DR12) is that experiment's first measurement.
- **P64-W2 Every finding names the fix, and the harness measures it.** The pilot's clearance contrast (§4.5) is the reason doc 61
  §4.5 and doc 65 §4.9 require findings with the next action and allowed values. Add the instrument: per-finding-code clearance in
  the qualification suites (docs 44, 48); a sticky code is a finding-text or surface bug to fix in code, not in the prompt.
  Early-phase findings matter most: rustc prints lint guidance only after a file type-checks [V, probe], so one hint-less early
  error hides every later hint. Teller's parse and resolve findings must name the fix, and a report should say when later checks
  were skipped, so the model knows more feedback is coming.
- **P64-W3 Group identical findings, one root per repair.** E0618's bursts of identical blocks crowded the feedback; doc 62 §6.9's
  "one root with grouped findings" and RustAssistant's grouping [10] apply.
- **P64-W4 Stop on repeats.** Granite resubmitted identical code in 58% of repair rounds. Doc 61's stop-on-repeat rule and a switch
  to resampling or the authored split are necessary for weak setups [12, 15].
- **P64-W5 Re-align doc 65 §6.** Before any Strict-versus-plain run: a calibration pilot on pilot tasks only, a review of the shared
  spec and cards for slips that produce hint-less findings, the floor rule, snippet-sized tasks (one condition, one init line, one
  SQS sequence) rather than whole files, and the accepted-but-wrong metric as H2.

### 5.4 Friction review (D049)

Friction found, for the three audiences; listed, not filed in `docs/friction/register.csv`:

- **Models:** hint-less errors on shared types (E0618); error conversion at API boundaries; fallible and infallible steps mixed
  without a naming cue; truncation of long files; stalls without a stop rule; tests out of reach behind compile errors (12 of 806
  rounds reached them, §4.9); in a clippy loop, a hint-less `let_underscore_must_use` follow-up and, under `-D warnings`, unused
  imports that fail a round. Product transfer: P64-S3, P64-S6, P64-W2 to W4.
- **Contributors:** a complete compilation on each change (the owner's point), removed by `AGENTS.md`'s fast-loop rule (§5.1); the
  pilot-policy deviation and an under-estimated compute budget (§4.8, §3.9); the harness's generated `lib.rs` would feed a clippy
  warning back in every round of a lint arm (fix in §3.9); the harness is under `tools/rust-weak-models`, but its run records stay
  local, so others can rerun the pilot but not re-read its records until a results CSV lands under `docs/research/data/` (§6 step
  11).
- **People:** none directly; the transfer is through Teller's findings (P64-W2).

## 6. Next steps

1. **Record the run** as a feasibility pilot in the deviations log. Then either write fresh scored tasks for Stage 1 (cleanest), or
   freeze the current 30 with the deviation stated and only shared-spec edits applied to both arms (cheaper) [owner].
2. **Remove the shared slip:** state payload-free refusals in the rules sheet and spec, or give the variants the payload models
   guess; both arms alike. This comes first: it also gates the lint arm, whose text appears only on code that type-checks (§3.9).
3. **Apply the floor rule:** one worked example (a pilot task solved in each variant's API) in both variants, shown in each arm's
   shape.
4. **Raise the reply cap** to 4,096 tokens, or score truncation as its own failure class.
5. **Build the unit-sized shape** (§3.9): split each task into 2–4 units with a compiling skeleton and per-unit visible tests that
   never touch a trap; loop per unit (`cargo check -p`, then that unit's tests); prove it model-free: each variant's references pass
   unit by unit and whole, and a mock repairer finishes every unit.
6. **Build the lint arm GUIDED-L** (§3.9): `clippy.toml` reasons, `must_use` messages, levels as `forbid` on the solution module,
   feedback filtered to spans in `solution.rs`, the generated `lib.rs` made clippy-clean, silencing counted by the scan; rerun the
   13 mutants under it (prediction: 10/13 rejected at compile time).
7. **Report the time split** (generation with prompt evaluation and decode, cargo, tests) and the per-round compile and test-reach
   rates in every run summary; the records already hold them, and `analysis/time_split.py` computes them.
8. **Models:** replace Granite 4.1 3B; add a 7–14B coder that fits an 8 GB card and the Qwen3-30B-A3B comparator (cloud through doc
   48's capped backend on a D047-compatible route, since the synthetic tasks are combat-flavoured, or locally at `--cpu-moe`); an
   optional strong "ceiling" row to check solvability.
9. **Re-pilot on P01–P04 plus a few calibration tasks, in both shapes,** until PLAIN R≤3 lands between 20% and 60% in at least one
   shape for at least two small models; name the primary shape; replace §3.9's unit-round estimate with the measured one.
10. **Freeze:** the analysis script, the lock file with hashes, the independent reviews (the unit decomposition included); then
    Stage 1 (about 2,430 episodes, 55–130 GPU hours at the pilot's pace; §3.9 says what to cut first under a cap).
11. **Harness in the repository:** it is packaged under `tools/rust-weak-models` as research tooling (it evaluates the development
    process, not a product feature; design-gap candidate 4 asks where such tools live). Still to do: a results CSV under
    `docs/research/data/`, so the pilot's numbers can be re-read without the local run records.
12. **Then:** Stage 2 (types × text); an optional arm that rewrites hint-less rustc errors into fix-naming text in the harness, which
    tests "errors that name the fix" directly; doc 62 §9.1's bypass and silencing test for strong coding agents on the same harness.
13. **Update this doc** with Stage 1 results under DR1–DR14, and fold P64-A1 to A3 or drop them accordingly.

## Design-gap candidates (listed, not filed)

1. **Store-issued ids as witnesses** (P64-A3): the newtype `from_raw` rule against the witness rules; checked re-entry from storage.
2. **Diagnostic clearance as a qualification metric** (P64-W2): which doc owns the per-code instrument and its threshold.
3. **An agent-usability gate for the plugin SDK** (P64-S1): a task suite and pass criteria before an SDK release.
4. **Where research harnesses live:** `tools/` layout, CI status (opt-in, local GPU) and data retention for model outputs.
5. **Task shape for weak-model coding** (DR9, P64-S6, P64-W1): which doc owns the unit-sized scaffold rule across the plugin SDK,
   doc 65's script tasks and Wilco's slots, once DR9–DR12 have a result.

## Open questions

1. **Owner:** which "weak" does the theory mean: 3–4B local models (the pilot answers "not by itself" for whole files), 7–30B local,
   or cheap cloud models? [U]
2. **Owner:** fresh scored tasks, or the current 30 with a stated deviation (§6 step 1)? [I]
3. **Owner:** adopt P64-A1 to A3 now, or after Stage 1? [U]
4. **Owner:** a GPU-hour cap for Stage 1? With both shapes and the lint arm it is about 55–130 h at the pilot's pace, against 40–55
   h for one shape (§3.9). [U]
5. **Measurement:** which is the smallest local model whose PLAIN R≤3 reaches 20% on these tasks, in either shape? [U]
6. **Measurement:** do unit-sized tasks lift 3–4B models off the floor, and do units that pass alone compose into a correct whole
   (DR9–DR12)? [U]
7. **Measurement:** do lint errors help weak models or crowd their repair budget (DR13, DR14), and do they stall on the hint-less
   `let_underscore_must_use` follow-up? [U]
8. **Measurement:** does a harness-side rewrite of hint-less errors lift the floor for 3–4B models? [U]
9. **Measurement:** do strong coding agents show a GUIDED effect on accepted-but-wrong code, or only on bypass rates (doc 62 §9.1)?
   [U]
10. **Technical:** can every task be split into units without a unit boundary, name or visible test pointing at a trap (the
    neutrality review, §3.9)? [U]
11. **Technical:** which cloud route for the comparator satisfies D047 for a combat-flavoured synthetic domain? [U]

## Findings for sibling docs (reported, not fixed)

- **Doc 65 §6** says it "must be re-aligned when doc 64 is published": the design matches; add P64-W5's calibration step, the floor
  rule and the pilot-policy lesson; its §6.4 sample size assumes this doc's power simulation, which stands; its "three small local
  models" should not include a model that stalls like Granite 4.1 3B did here. It can mirror §3.9's shape factor as snippet versus
  whole script, and report the time split and the share of rounds that reach its checks.
- **Doc 62 §9.1** (coding-agent misuse evaluation) can run on this harness; its arms B and C correspond to GUIDED's witness rules and
  diagnostics, and GUIDED-L is a small-model version of arm C. Arm C's lint clearance should be counted only on rounds that
  type-check (below).
- **Doc 62 §3.1** ("bound on a function"): the probe shows a method's own `where` clause works too (P64-A1). The channel table
  lacks two rows [V, probe]: late lints (every clippy lint, `unused_must_use`) print nothing while any type error remains, so a
  type error hides every lint reason; and the error that follows rustc's `let _ =` help, clippy's `let_underscore_must_use`,
  carries no custom text, only "consider explicitly using expression value".
- **Doc 55** (presets): per-model repair rounds and a stop-on-repeat rule are presets' business (DR2, P64-W4), and so, after DR14,
  is whether deny-level warnings belong in a weak model's repair loop or only in its final gate; Granite 4.1 3B's local
  qualification should note its llama.cpp stalls on code.

## Sources

All read on 2026-09-28 unless stated. Tags in the text say what was read.

**Rust, languages and benchmarks**

- [1] Nogueira, Vieira, Campos. PROBE: Benchmarking Code Generation in Large Language Models. 2026. https://arxiv.org/abs/2607.13820
- [2] Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages. 2026. https://www.alphaxiv.org/abs/2606.20517
- [3] Cassano et al. MultiPL-E. IEEE TSE 2023. https://arxiv.org/abs/2208.08227; findings:
  https://github.com/nuprl/MultiPL-E/blob/main/docs/index.md
- [4] SWE-bench Multilingual, per-language rates. https://www.swebench.com/multilingual.html
- [5] Zan et al. Multi-SWE-bench. 2025. https://arxiv.org/abs/2504.02605
- [6] Xiang et al. Rust-SWE-bench and RustForger. ICSE 2026. https://arxiv.org/abs/2602.22764
- [7] RustRepoTrans. https://arxiv.org/abs/2411.13990
- [8] Nogueira, Vieira, Campos. Unreliable in Practice? A Comprehensive Study of Errors in LLM-Generated Code. 2026.
  https://arxiv.org/abs/2608.00661
- [9] SafeTrans: LLM-assisted transpilation from C to Rust. 2025. https://arxiv.org/abs/2505.10708

**Compiler and verifier loops**

- [10] Deligiannis, Lal, Mehrotra, Rastogi. RustAssistant (arXiv title "Fixing Rust Compilation Errors using LLMs"). ICSE 2025.
  https://arxiv.org/abs/2308.05177
- [11] Khatry et al. CRUST-Bench. COLM 2025. https://arxiv.org/abs/2504.15254
- [12] Mündler-Sasahara, Venev, Song, Vechev, He. Generative Compilation: On-the-Fly Compiler Feedback as AI Generates Code. 2026.
  https://arxiv.org/abs/2607.13921
- [14] Olausson, Inala, Wang, Gao, Solar-Lezama. Is Self-Repair a Silver Bullet for Code Generation? ICLR 2024.
  https://arxiv.org/abs/2306.09896
- [15] Arimbur. How Many Tries Does It Take? Iterative Self-Repair in LLM Code Generation Across Model Scales and Benchmarks. 2026.
  https://arxiv.org/abs/2604.10508
- [16] Kamoi et al. When Can LLMs Actually Correct Their Own Mistakes? TACL 2024. https://arxiv.org/abs/2406.01297
- [17] Skopin, Kotelnikov. Improving Small Language Models for Code Generation with RL from Verification Feedback. 2026.
  https://arxiv.org/abs/2605.30478
- [45] Weiss et al. Feedback loops in C-to-Rust translation. https://arxiv.org/abs/2512.02567 (per doc 62)

**Types, decoding and context**

- [13] Mündler, He, Wang, Sen, Song, Vechev. Type-Constrained Code Generation with Language Models. PLDI 2025.
  https://arxiv.org/abs/2504.09246
- [18] Agrawal et al. Monitor-Guided Decoding of Code LMs with Static Analysis. NeurIPS 2023. https://arxiv.org/abs/2306.10763
- [19] Blinn, Li, Kim, Omar. Statically Contextualizing LLMs with Typed Holes. OOPSLA 2024. https://arxiv.org/abs/2409.00921
- [22] Liang et al. RustEvo²: API Evolution in LLM-based Rust Code Generation. 2025. https://arxiv.org/abs/2503.16922
- [23] Zhou et al. DocPrompting. ICLR 2023. https://arxiv.org/abs/2207.05987
- [44] Krishnamurthi, Flatt. Type-Error Ablation and AI Coding Agents. 2026. https://arxiv.org/abs/2606.01522 (per docs 61, 62)

**API design, misuse and usability**

- [20] Lee, Hassan, Hindle. Mining Type Constructs Using Patterns in AI-Generated Code. 2026. https://arxiv.org/abs/2602.17955
- [21] Zhuo et al. Identifying and Mitigating API Misuse in Large Language Models. https://arxiv.org/abs/2503.22821
- [24] Coblenz, Aldrich, Sunshine, Myers. Can Advanced Type Systems Be Usable? Obsidian. OOPSLA 2020. https://arxiv.org/abs/2003.12209
- [25] Coblenz, Mazurek, Hicks. Garbage Collection Makes Rust Easier to Use: A Randomized Controlled Trial of the Bronze Garbage
  Collector. ICSE 2022. https://arxiv.org/abs/2110.01098
- [26] Khan. Token Budgets: 63 LLM-Agent Budget-Overrun Incidents, with an Affine-Typed Rust Mitigation. 2026.
  https://arxiv.org/abs/2606.04056
- [27] Santos, Becker. Not the Silver Bullet: LLM-enhanced Programming Error Messages are Ineffective in Practice. 2024.
  https://arxiv.org/abs/2409.18661

**Rust toolchain and strict-path**

- [28] Announcing Rust 1.78.0 (`#[diagnostic::on_unimplemented]`). https://blog.rust-lang.org/2024/05/02/Rust-1.78.0/
- [29] Announcing Rust 1.85.0 (`#[diagnostic::do_not_recommend]`). https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/
- [30] The Rust Reference, diagnostic attributes. https://doc.rust-lang.org/reference/attributes/diagnostics.html
- [31] strict-path repository, README and LLM context. https://github.com/DK26/strict-path-rs;
  https://github.com/DK26/strict-path-rs/blob/main/LLM_CONTEXT_FULL.md
- [32] strict-path on crates.io and docs.rs. https://crates.io/crates/strict-path; https://docs.rs/strict-path

**Practice and opinion**

- [33] Ronacher. Agentic Coding Recommendations. 2025. https://lucumr.pocoo.org/2025/6/12/agentic-coding/
- [34] Ronacher. In Support Of Shitty Types. 2025. https://lucumr.pocoo.org/2025/8/4/shitty-types/
- [35] Ronacher. A Language For Agents. 2026. https://lucumr.pocoo.org/2026/2/9/a-language-for-agents/
- [36] Love. How Rust's Compiler Catches What Coding Agents Get Wrong. 2025.
  https://marclove.com/blog/2025-12-13-rust-feedback-loop-catches-claude-code-hallucinations-dead-code-bugs/
- [37] Learnings from 100K lines of Rust with AI. 2025.
  https://zfhuang99.github.io/rust/claude%20code/codex/contracts/spec-driven%20development/2025/12/01/rust-with-ai.html
- [38] Belderbos. The Rust Compiler as an AI Coding Agent Guardrail. 2026. https://belderbos.dev/blog/rust-compiler-ai-agent-guardrail/

**Experiment method**

- [39] Miller. Adding Error Bars to Evals. 2024. https://arxiv.org/abs/2411.00640
- [40] Dai, Cai, Luo, Tseng. Experimental Settings in LLM-Based Program Repair. 2026. https://arxiv.org/abs/2609.17993
- [41] Chen et al. Evaluating Large Language Models Trained on Code (unbiased pass@k). 2021. https://arxiv.org/abs/2107.03374
- [42] Yao et al. τ-bench (pass^k). 2024. https://arxiv.org/abs/2406.12045

**Plotroom (this repository)**

- `AGENTS.md` ("Type Safety", "Witness and guard types", "Diagnostics as Guidance", "Negative Compile Tests", "Maintaining This File";
  "Local Repo-Specific Rules", "Fast inner loop, full gates at the end")
- `tools/rust-weak-models` (the experiment: README, `runner.py`, `rwm/cargo.py`, `analysis/time_split.py`, `design.json`)
- Research docs 16 (legend), 21, 25, 30, 31 §9, 44, 46, 48, 49, 55, 61 (§2, §4.5, §4.6), 62 (§3, §6.9, §7, §8, §9.1), 63 (§9), 65
  (§5, §6); decisions D047, D048, D049, D051, D052; `docs/friction/register.csv`

Sources are grouped by topic, so the numbers are not in order within every group; the numbers are the ones used in the text.

## Verification notes

### 2026-09-28, author checks at write-up

- **Re-opened on the web (abstract or landing page):** PROBE [1], Generative Compilation [12], type-constrained decoding [13],
  SWE-bench Multilingual [4], RustAssistant [10], Olausson et al. [14], iterative self-repair [15], RLVR for small models [17],
  Obsidian [24], Bronze [25], Token Budgets [26], Not the Silver Bullet [27], agents and `any` [20], CRUST-Bench [11], Rust-SWE-bench
  [6], RustEvo² [22], Unreliable in Practice? [8], Multi-SWE-bench [5], MultiPL-E's findings page [3], the Rust 1.78 post [28],
  strict-path's README [31] and Ronacher's "In Support Of Shitty Types" [34].
- **Re-read in full text** (local text extractions of the public PDFs): PROBE's ranking and feedback paragraphs; Generative
  Compilation's Table 1 (Qwen 9B and Opus 4.8 rows), its restart and overhead paragraphs and the "highly complex and costly"
  sentence; type-constrained decoding's Tables 2 and 3 and its runtime paragraph; RustAssistant's Tables I, IV and VI.
- **Corrected from the research inputs:** (1) type constraining cuts synthesis compile errors by **74.8% and 56.0%**, not "75.3% and
  52.1%"; 52.1% is the MBPP *runtime* overhead (39.1% on HumanEval); (2) RustAssistant's GPT-4 micro-benchmark best is 252/270 (Table
  IV); the "92.59%" figure was dropped because Table I's extracted row does not sum to 270; (3) "Unreliable in Practice?" analyses
  86,726 erroneous *code samples*, not errors; (4) Bronze's "2.44× more likely to finish" is not in the abstract and was dropped;
  (5) the iterative self-repair abstract gives ranges (+4.9 to +17.1 points on HumanEval, +16.0 to +30.0 on MBPP), so a single
  "Llama 3.1 8B +9.8" figure was dropped; (6) the RLVR paper's abstract states the lint-only effect qualitatively, so the "−2.0 to
  −6.2 points" figure was dropped; (7) RustAssistant's arXiv title differs from its ICSE title (both given).
- **Pilot numbers re-derived from the run records:** outcomes and paired tables from the pilot summary; truncation re-counted from
  `finish_reason` (40 generations hit the cap, 38 became format failures; an earlier count of 32 was wrong); clearance per
  transition computed by a new script over the saved feedback (the per-block rates of the run's own script are quoted for
  comparison); the Gemma T25 trap results and the `?`-error types read from the saved feedback; `.unwrap()` counts from the
  episodes' static scans (one Gemma and one to two Granite episodes lack a scan).
- **Probe re-run:** E0618 on a unit variant, for a local enum and for an enum from another crate, with rustc 1.98.1 (48a229cea
  2026-09-01): no fix hint in either; "defined here" only for the local enum.
- **Not re-opened** (tagged "per research pass" or "per doc N" in the text): Multi-LCB [2], RustRepoTrans [7], SafeTrans [9],
  Kamoi et al. [16], monitor-guided decoding [18], typed holes [19], API misuse [21], DocPrompting [23], type-error ablation [44],
  Weiss et al. [45], the Rust 1.85 post [29], the Rust Reference [30], strict-path's crates.io and docs.rs pages [32], Ronacher
  [33, 35], the practice posts [36–38] and the method papers [39–42]. Numbers that sit only in a paper body we did not re-read
  (PROBE's per-model outcome rates, Multi-SWE-bench's language ranking, the error breakdown of [8], CRUST-Bench's repair gains) are
  tagged "full text per research pass".
- **Model-free and simulation numbers** (static catch rate, conformance, reference runs, power) are quoted from the harness's own
  records of 2026-09-28 and were not re-run for this write-up.
- **Hygiene:** no private project names, local paths, user names or keys; model outputs paraphrased; the scratch workspace is named
  only as "outside the repository".

### 2026-09-28, revision after the owner's input

- **Owner input folded in as findings and design, not as an appendix:** §4.9 (time split; the owner's two remarks quoted
  verbatim), §3.9 (unit-sized shape, GUIDED-L, H5–H7, DR9–DR14, budget), §5.1 (the adopted `AGENTS.md` rule), P64-S6, P64-W1 and
  W2 additions, the TL;DR, §6, open questions and sibling-doc findings. `AGENTS.md` was read for the rule's wording; this revision
  edits only this file. The harness was packaged under `tools/rust-weak-models` during the revision, so the doc now names it there
  and no longer as "outside the repository"; no scratch path appears.
- **Recomputed from the three pilot JSONL files** by a new script (not copied from earlier summaries; the same computation ships as
  `analysis/time_split.py`), plus ad-hoc queries for the fed-back rounds and the warnings: 806 round records, 204 episode records
  and 4 run records; Qwen's two runs share no round key. Time split from each round's `gen_ms`, the server's
  `prompt_ms` and `predicted_ms`, `build_ms` and `test_ms`; cargo median and p90 over the 768 rounds that reached cargo; compiling
  rounds by round index; rounds whose visible-test failures were fed back (compiled, visible fail, not the last round); warning
  counts per round. Recorded time covers 99.8% of the wall-clock gaps between consecutive rounds. §4.2's tokens and generation
  seconds per episode and §4.1's 2.0–3.1 minutes per episode re-derived: unchanged.
- **Differences from the figures shown to the owner during the run:** those used Granite's partial records (187 rounds); the table
  uses the complete file (272 rounds; still 0 compiled; shares agree to the percent). Cargo medians here exclude the 38 rounds
  that never reached cargo (format failures), which moves them from 0.8, 0.9 and 0.6 s to 0.84, 0.97 and 0.63 s.
- **Warnings:** counted from the records' `n_warnings`; the unused-import share (403 of 432 warning headings) from the saved
  feedback, which is cut at 6,000 characters with errors first, so it undercounts warnings in long feedback.
- **Probe re-run** (a throwaway crate outside the repository; rustc 1.98.1, clippy 0.1.98): with an E0308 or E0618 present, neither
  a `disallowed-methods` error nor a deny-level `unused_must_use` error was printed; without one, both were, each text as a note,
  the latter with rustc's `let _ =` help; `let _ = …` then passed `cargo check` and failed clippy's `let_underscore_must_use` with
  only the generic help; E0618's headline is identical under clippy.
- **Timings:** warm `cargo clippy --all-targets`, `cargo check --all-targets` and `cargo test --no-run` on the T22 GUIDED task
  crate inside the harness, three runs each after touching the reference solution (content hash unchanged). The same clippy run
  flagged the generated `lib.rs` (`write_with_newline`), and the harness's feedback filter was read in its cargo module (package,
  not file).
- **Reference sizes:** non-blank lines without `use` or comments in the 34 reference solutions per variant; 3-sample power figures
  from the existing simulation records (not re-run).
- **Not run:** the 13 mutants under a lint table (§3.9's 10/13 is a prediction, [I]); the unit-round time (an estimate from the
  pilot's rates, [I]); Plotroom's own build times [U].
