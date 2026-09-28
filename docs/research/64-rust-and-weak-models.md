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
"Fast inner loop, full gates at the end" (section "Local Repo-Specific Rules"), adopted on the owner's suggestion (2026-09-28)
from the input that §4.9 evaluates. Plotroom was never built or run. Every design proposal is [I]. This doc changes no decision.
**D058 applies** (accepted 2026-09-28): the editor comes first, lane D starts no new work, harness testing uses cloud models through
the guarded paths, local small models come last and the owner's GPU stays free. So the next iteration (§3.9, §6) is a plan, deferred;
when it resumes it runs cloud-first through `tools/local-qual`'s guarded, budget-capped backend, and its local arms wait for the
optimization phase. **Friction:** adds FR-M-028 to FR-M-031; updates FR-C-013 (§5.4).
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
GUIDED plus a lint channel: a clippy lint table and `must_use` messages, fed back through clippy (§3.9). *R0* is a model's first
attempt; *R≤3* is the outcome after up to three compiler and visible-test repair rounds (per unit, in the unit-sized shape).
*Accepted but wrong* means the code compiles and passes every visible test, so a loop would report success, but fails a hidden
test: the "logical error" the theory is about.
*Trap classes*: S (GUIDED rejects the mistake at compile time), F (GUIDED forces handling of an `Option` or `Result`, but
`.unwrap()` escapes), R (checked at run time in both variants; a control). *Clearance*: a diagnostic kind present in round *r*'s
feedback that no longer appears in round *r+1*'s (§4.5). *Wilco* is Plotroom's in-product agent; *Teller* its script checker and
language service.
**Hygiene.** Public sources only. Model outputs are paraphrased; no local paths, user names or keys. Research proposals P64-A1 to
P64-A3, P64-S1 to P64-S6 and P64-W1 to P64-W5, hypotheses H1–H7, arms A–F and decision rules DR1–DR14 (with DR1b, DR12b and
DR14b) are this doc's labels.

## TL;DR

- **Partly, and not yet for the part that is the owner's own.** (1) *Rust alone does not help weak models.* One-shot, Rust is the
  hardest of five languages for every model tested, and "the gap between Rust and the other languages grows substantially in the
  smaller models" [1] [V-author, full text]. (2) *Rust with the compiler in the loop does help, and helps weak models most.* Rust
  gains the most from feedback rounds, which the authors attribute first to "its weaker initial performance" and then to its
  diagnostics: "Because Rust's compile-time diagnostics are detailed and explicit, the models can leverage this feedback
  effectively" [1]; on repository-level Rust a 9B model with a compile loop reaches 30.3–48.3% functional correctness, about a
  frontier model's 32.0–43.3% without one [12] [V-author, full text]. Type information at decode time or in context helps small
  models most in repair (Gemma 2 2B repair pass@1 11.6 → 20.9) [13, 18, 19]. (3) *The owner's specific claim*, that APIs built to lead (typestate, witnesses, newtypes,
  fix-naming diagnostics) cut weak models' logical errors, **has no published measurement**. The nearest evidence is human studies
  [24] and runtime guards [26].
- **Our pilot ran and sat on the floor.** Three local 3–4B models (Qwen3.5-4B, Gemma 4 E4B, Granite 4.1 3B), 34 tasks × 2 APIs,
  one sample, up to three repair rounds: **0 of 204 correct at R0; at R≤3, 2/102 PLAIN and 2/102 GUIDED** [V, pilot]. Every
  paired sign test gives p = 1.0; the H1 estimand on this pilot is exactly 0.0 points (one task each way). It cannot discriminate.
- **Why the floor:** a slip in the shared task spec, identical in both arms, whose rustc error (E0618, "expected function, found
  `Refusal`") names no fix, and which the prompt itself invites: the same listing shows a same-named variant that carries a label,
  `Problem::OutOfMap(String)`, beside the unit `Refusal::OutOfMap` (§4.4). E0618 was cleared in 9 of 318 repair rounds; GUIDED's
  custom fix-naming errors in 11 of 28; rustc's own `?` errors, which name the missing `From` impl or the `Try` requirement, in 55
  of 189 [V, pilot, descriptive]. Errors that say what to do were cleared more often; the hint-less one, contradicted by the
  prompt's own example, almost never was, so that contrast is confounded, not a clean test of hint text. The custom notes did not
  beat rustc's own good notes.
- **Model-free, the mechanism exists.** Of 13 trap mutants, all compile under PLAIN and 9 pass its visible tests silently; GUIDED
  rejects 8 at compile time, 6 with its custom fix text; its 5 misses are the predicted escapes (`.unwrap()`, a minutes value
  wrapped as seconds, same-typed swaps, off-by-one indices) [V, model-free].
- **Compile time is not the bottleneck; reaching the tests is** (owner input, §4.9). Of the pilot's 8.4 hours of recorded round
  time (806 rounds), generation took 97.7% (decoding 78.5%, prompt evaluation 18.6%), cargo 2.3% (median 0.6–1.0 s per round) and
  tests 0.01% [V, pilot]. Only 12 of 806 rounds compiled, so tests ran in 12, and visible-test failures reached a model in 3. For
  this harness the owner's premise (a complete compilation on each change takes far longer) did not hold; what holds is the idea
  behind it, small units validated by their own tests, read as a **task shape** [I]: the next iteration adds *unit-sized* tasks
  (one function at a time against a compiling skeleton, that function's tests as spec and feedback, hidden tests still scoring the
  whole) as a second factor beside PLAIN/GUIDED (§3.9).
- **Clippy is the right inner-loop command, and a lint arm is cheap to run (a few days to build).** Warm, clippy costs 0.64–0.69 s
  per round against 0.87–0.89 s for the pilot's `cargo test --no-run` in the same probe (the pilot's recorded median was 0.77 s);
  on rounds that type-check, the test build still follows [V, probe; V, pilot]. Only clippy carries clippy's own lints (a
  `disallowed-methods` table's reasons, `let_underscore_must_use`); `#[must_use]`, `#[deprecated]` and `on_unimplemented` text are
  rustc's and reach `cargo check` too (doc 62 §3.1). Lints run only on code that type-checks: with any type error present, no lint
  text is printed [V, probe]. A lint arm (GUIDED-L) cannot touch the hint-less E0618 wall and speaks only once the slip is gone,
  which is why it sits behind the spec fix (§3.9).
- **Reading [I].** For 3–4B models writing whole Rust files against an unseen API, neither API lifted them off the floor in this
  run, with a shared spec slip blocking most rounds. At that size the lever is likely the harness (small typed steps, findings that
  name the fix, stall detection), which is what Plotroom already designs for Wilco (docs 21, 25, 61, 65) and what the unit-sized
  shape tests for code. Whether guiding APIs cut accepted-but-wrong code for 7–30B models or for strong coding agents is still
  **open**.
- **What remains to test** (deferred under D058; cloud-first when it resumes): remove the shared slip and the name collision; add
  one worked example to both arms (a design change: the pre-registered floor rule, computed on its own scope P01–P04, does not
  fire, since Qwen PLAIN passed P02; it fires only over all 34 tasks, §4.8); replace Granite; add a 7–14B coder and the 30B-A3B
  comparator; build the unit-sized shape and the lint arm; re-pilot both shapes on calibration tasks outside the scored set until
  PLAIN R≤3 lands between 20% and 60% in at least one and name it the primary shape; re-run the power simulation at that baseline;
  freeze; run Stage 1 (about 2,970 episodes with an ablation arm; at the pilot's local pace about 57–161 GPU hours, against
  35–55 h for one shape, and more with larger models, §3.9); then Stage 2 (types versus text) and doc 62 §9.1's bypass test for
  strong coding agents (§6).
- **For Plotroom now:** `AGENTS.md`'s "Fast inner loop, full gates at the end" rule was adopted on the owner's suggestion on
  2026-09-28 (clippy on one crate, then that crate's targeted unit tests; full gates once); §4.9 backs only that clippy costs no
  more than check per crate, and the rule's workspace premise (a complete compilation per change is far slower) stays [U] until
  Plotroom has code to time. No other `AGENTS.md` change is justified by an effect estimate. Three refinements are proposed on top
  of doc 62's applied amendment (P64-A1 to A3, §5.1): P64-A1 rests on probes, P64-A2 on the pilot's descriptive and partly
  confounded clearance numbers, P64-A3 on the witness rules alone until a mutant tests it. The plugin SDK and Teller take the
  "hint-less error" lesson and the unit-sized scaffold (§5.2, §5.3); doc 65's experiment should adopt the calibration step and the
  shape factor.

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
- External feedback is what small models lack. Olausson et al. hypothesise that self-repair "is bottlenecked by the model's
  ability to provide feedback on its own code" [14] [V-author, abstract], and self-correction works in tasks "that can use
  reliable external feedback" [16] [V-author, abstract per research pass]. A compiler is a reliable external critic.
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
- **Compile-clean is not correct.** Rewards from static analysis alone "may bias the policy toward shorter completions that reduce
  lint errors without reliably improving functional correctness" [17] [V-author, abstract].
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
| Multi-LCB, 2026 [2] | LiveCodeBench in many languages | Rust and Scala lowest; some reasoning models above 60% in Python stay under 30% in Rust [V-author, full text per research pass; the abstract says only "substantial disparities in multilingual performance"] | M |
| MultiPL-E [3] | 18+ languages | "Type annotations have limited impact on model performance for gradually typed languages" [V] | M |
| SWE-bench Multilingual [4] | SWE-agent + Claude 3.7 Sonnet, agentic | Rust 58.14% (25/43), the highest; C/C++ 28.57% [V] | M |
| Multi-SWE-bench [5] | 1,632 issues, 7 languages | Rust mid-pack, behind Java [V-author, full text per research pass] | M |
| Rust-SWE-bench, ICSE 2026 [6] | 500 repository tasks, 34 repos | Best ReAct-style agent 21.2%; RustForger 28.6% with Claude Sonnet 3.7; hampered by repository structure and "complying with Rust's strict type and trait semantics" [V-author, abstract] | M |
| RustRepoTrans [7] | Repository-level translation into Rust | DeepSeek-R1 drops from 73.7% to 51.5% pass@1 once repository context is involved [V-author, abstract per research pass] | M |
| Unreliable in Practice?, 2026 [8] | 86,726 erroneous samples, 7 models, 4 compiled languages | Error types vary strongly by language and model. Per a research pass, Rust compile errors: 43.4% incompatible parameter types, 20.5% missing imports, 16.7% ownership or lifetimes, 6.1% trait bounds [V-author, full text per research pass] | M |

**Reading [I].** One-shot, Rust is hard and hardest for small models. With a compiler and tests in an agent loop, rankings flip or
scatter. No single "Rust is easier or harder for LLMs" number exists, and the largest error buckets are wrong types or arguments
and missing or hallucinated names, not the borrow checker: exactly what domain types and explicit signatures can shrink.

### 2.2 The compiler in the loop

| Source | Setting | Result | Kind |
| --- | --- | --- | --- |
| PROBE [1] | Up to two feedback rounds | +0.05 pass@1 and pass@5 on average; "Rust shows the largest improvement, which can likely be attributed to its weaker initial performance … Because Rust's compile-time diagnostics are detailed and explicit, the models can leverage this feedback effectively" [V-author, full text] | M |
| Generative Compilation, 2026 [12] | Repository-level Rust, 7 models; code owns the loop | Mean compile-error rate 65.9% (no feedback) → 20.7% (post-generation loop) → 13.1% (checks during generation). Qwen3.5 9B functional correctness: Translation 8.3 → 30.3 → 33.3%; UpdatedAPI 10.0 → 48.3 → 41.7%. Claude Opus 4.8 without feedback: 32.0% and 43.3%; with it 61.0–86.7%. Qwen 9B needed more than 10 restarts on 40.9% of tasks (GPT 5.3 Codex 2.1%) and "often regenerate[s] the same erroneous prefix". Building a constrained decoder "from scratch for real Rust would be highly complex and costly" [V-author, full text] | M |
| RustAssistant, ICSE 2025 [10] | Real Rust compile errors, GPT-3.5/4 | Peak accuracy "roughly 74%" [V-author, abstract]. Prompt format dominates: GPT-4 on 270 micro-benchmarks 139 → 196 → 247 → 252 fixed as line prefixes, localization and "explain first" are added; clippy findings fixed 74.86% against clippy's own auto-fix 31.50% [V-author, full text of the ICSE camera-ready, Tables IV and VI; the arXiv version's tables differ] | M |
| CRUST-Bench, COLM 2025 [11] | C to safe Rust, 100 repositories | o1 solves 15 single-shot [V-author, abstract]; compiler-only repair adds up to +37 points build success; Llama-3-8B solved none [V-author, full text per research pass] | M |
| SafeTrans, 2025 [9] | C to Rust with guided compiler feedback | GPT-4o 54 → 80%, DeepSeek-V3 49 → 79%; Qwen2.5-Coder 7B and DeepSeek-Coder 16B "nearly double", Llama3 70B gains about 12 points; E0277 and E0308 are "over 18% of all errors in most models, and up to 30% for Qwen2.5-Coder and Llama3" (7B and 70B) [V-author, full text] | M |
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

One practitioner report credits rustc with catching agents' hallucinations and dead code, so that "what's left is mostly business
logic bugs" [36]; another credits compile-time catching of a class of errors that would otherwise surface at run time [38]; a
third puts correctness on code contracts, spec-driven tests and property tests, not on the compiler [37] [V, opinion; all three
re-opened 2026-09-28]. Ronacher argues against type-level cleverness for agents [34] [V, opinion], recommends Go for agentic
backends for its simplicity [33] and asks for explicit types, local reasoning and greppable names [35] [V-author per research
pass]. This agrees with the measured data: types help when simple, local, explicit and actionable.

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
  small models' correctness over whole-file tasks, and does the API effect differ by shape (H5, H6)? **RQ7** Does adding a lint
  channel to GUIDED help (H7)? GUIDED-L bundles two changes: clippy's own lints (instruction-style `disallowed-methods` reasons,
  `let_underscore_must_use`), which only clippy prints, and new `must_use` messages at deny, which are rustc's and would reach
  `cargo check` too, so H7 tests an API change plus a channel, not the clippy channel alone.

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
- **Tests.** Visible: one nominal test per task, never touching a trap. Hidden: 154 tests on the 30 scored tasks (168 with the
  pilot tasks), 97 of them trap tests, asserting through an independent parser and rule checker; never fed back.

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
cell) gives, for 30 tasks and 6 samples per model and a PLAIN pass rate near 35%, 74–91% power at +10 points and 91–99% at +13
[V, simulation]; task count, not
samples, is the lever. Effects under about 7 points are not reliably detectable, so a null result will usually read
"inconclusive".

| Rule | If | Then [I] |
| --- | --- | --- |
| DR1 | H1 ≥ +10 points and accepted-but-wrong not worse | Theory supported for 3–4B models on this domain: `AGENTS.md` gains the diagnostic-shape rule and unforgeable ids for agent-facing APIs; Plotroom's typed command layer and script compiler name the fix; run Stage 2 |
| DR1b | +5 to +10 | Adopt only the cheap parts (diagnostic shape, instructive docs) |
| DR2 | Gain only after the loop | Guided APIs only together with a mandatory verifier loop, stated in the plugin SDK's guidance and contributor guidance (D048 presets never change repair limits, and Wilco writes no Rust) |
| DR3 | Harm (interval below 0) | Keep typestate out of agent-facing surfaces |
| DR4 | Equivalent within ±5 | Type-safety rules stay human code-quality rules; stop citing them as a weak-model lever |
| DR5 | Inconclusive | A new pre-registration, more tasks rather than more samples, no pooling |
| DR6 | H4 holds for a model | "Punches above its weight" may be said for that model, domain and loop only |
| DR7 | GUIDED tokens per success > 1.5× PLAIN | Flag the token cost; trim docs before dropping types |
| DR8 | Models disagree in sign | Per-model notes in the plugin SDK's guidance; for Wilco, an input to doc 55's preset tuning only |

Stage 2, only if H1 passes: a 2 × 2 of type structure × guidance text, to separate types from docs and diagnostics. The next
iteration's shape factor and lint arm add DR9–DR14b (§3.9).

### 3.6 The harness as built

Under `tools/rust-weak-models`: five std-only Rust crates (shared spec, hidden core, PLAIN, GUIDED, independent oracle), 34 tasks
with reference solutions in both variants, 68 test crates generated by `runner.py scaffold` (not committed), and a
standard-library Python runner with an OpenAI-compatible client for llama-server. The model writes one file under
`#![forbid(unsafe_code)]`; a best-effort static scan rejects process, file, network, environment and include escapes and, since
this review, allows only listed standard-library modules and rejects crate-root aliases, raw identifiers and macro-built paths
(the pilot's 768 saved solutions get the same verdicts under both versions); it is not a sandbox, so the runner talks to loopback
endpoints unless told otherwise; cargo runs `--offline --locked` with a 20 s limit per test binary.
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

Written after the pilot and the owner's input (§4.9), before any run of the new arms, and revised after the review of
2026-09-28. §3.1–§3.5 stay as they are; this adds a second factor, two arms, three hypotheses and seven decision rules [I]. Under
D058 the whole iteration is deferred; every rule below is written so it can run cloud-first, with compute counted as GPU seconds
locally and as billed tokens in the cloud.

**Unit-sized tasks: the owner's idea as a task shape, tested as a package.** Each scored task is split into 2–4 units along its
reference solution's natural steps; the references are small (median 17.5 code lines in PLAIN and 20 in GUIDED; the largest,
T30, 69 and 68), and GUIDED's already use 1–4 functions [V, model-free]. The harness writes a compiling skeleton: each unit's
signature and a doc comment taken from the task text, with a `todo!()` body. The last unit is `solve` itself, whose tests are the
task's existing visible tests. The shape bundles several levers: a harness-written skeleton (imports and signatures, which remove
the E0432/E0433 and many E0308 errors of §4.4), a harness-supplied decomposition (a plan), extra visible per-unit tests, short
replies (no truncation) and more attempts. So H5 and DR9 test **the unit-sized scaffold package**, not "validate with unit tests"
alone, and an ablation arm (F, below) separates the per-unit tests from the rest.

- **Protocol, fixed before the build** (§6 step 5): the reply is one function item; the harness splices it into the skeleton by
  name and rejects a changed signature as a format failure; a unit may add `use` lines and private helper functions, nothing else
  at file level; each unit is a fresh conversation carrying the current skeleton (earlier units filled), the unit's text and its
  own feedback, so context does not grow over the episode's calls (the whole-file arm's multi-turn form stays as it ran); the
  system text has a unit-specific task line in place of "Return the complete file"; escape-hatch counts exclude the harness's own
  `todo!()` stubs.
- **Loop per unit:** `cargo check -p <task crate>` (clippy in GUIDED-L) → that unit's visible tests → next unit; up to three
  repairs per unit. An exhausted unit keeps its last compiling body, else its stub, and the episode moves on, so per-unit pass
  rates stay measurable at the floor. The rules sheet and API listing are the whole-file arm's, so prefix caching still applies.
- **Scoring:** the hidden tests score the whole `solve`, never fed back. *Accepted but wrong* keeps its meaning within a shape.
  For every cross-shape comparison it is defined on the common test set, `solve`'s own visible tests only, because the unit shape's
  extra visible tests would otherwise lower it by construction.
- **Fairness rules:** per-unit visible tests are nominal and never touch a trap (as §3.3); unit boundaries and names come from the
  task text, never from a trap; the independent neutrality review (§3.8) sees the unit names, signatures and per-unit tests without
  the trap labels; both variants get the same decomposition. A GUIDED skeleton's signatures name its states and units
  (`Plan<Open>`, `Metres`): that is part of what GUIDED means at unit size and is reported, not hidden. Model-free, the 13 mutants
  are re-run in the unit shape: PLAIN must stay 0/13 static with its silent count unchanged, and any change is reported as
  skeleton leakage.
- **Prompt length:** per step, the shorter variant's skeleton-plus-listing is padded to the longer one's token count with the
  same neutral padding as §3.4; prompt tokens per step are reported for every arm.
- **Compute:** unit-sized episodes make more, shorter calls: whole-file 1–4 generations per episode, unit-sized 2–16 (3 units × 4
  at the floor). The per-episode cap on generated tokens is 4 × the reply cap in both shapes (4 × 4,096 after §6 step 4), which
  short unit replies rarely reach, so the cap alone does not equalise compute; H5 below is therefore compute-matched.
- **The build becomes visible at this size:** cargo takes 0.6–2 s of a 9–17 s unit round (below), roughly 4–20% rather than the
  pilot's 2%, so the loop checks one crate against prebuilt dependencies and runs only that unit's tests (a test-name filter), as
  `AGENTS.md`'s fast-loop rule does.

**The lint arm (GUIDED-L).** GUIDED plus a lint channel, with feedback from `cargo clippy` instead of the build output, per doc 62
§3.1's channel table. It changes two things at once, and says so: clippy's own lints, which only clippy prints, and new `must_use`
messages, which are an API change that rustc would print under `cargo check` too.

- `clippy.toml` `disallowed-methods` entries for `Option::unwrap`, `Option::expect`, `Result::unwrap` and `Result::expect`, each
  with an instruction-style `reason` and no `replacement` ("a lookup can miss: `match` on it, or use `.ok_or(Refusal::…)?` with the
  refusal the task names"), so the text arrives as a note on the error [V, probe]. The harness pins its own `clippy.toml` (empty
  until this arm exists), so no configuration above the folder reaches it;
- `#[must_use = "…"]` messages naming the next step on GUIDED's state-carrying values (plans, trigger ids, the validated mission;
  GUIDED has none today), with `unused_must_use` and clippy's `let_underscore_must_use` at deny. They sit behind a cargo feature
  that only GUIDED-L's task crates enable, so GUIDED's build, listing and diagnostics stay as they ran, and the listing generator
  drops them, so the text arrives only through diagnostics and GUIDED-L's prompt is byte-identical to GUIDED's;
- clippy runs with its default groups allowed (`-A clippy::all`), and the lint table's levels are set as
  `#[forbid(…)] pub mod solution;` in the generated `lib.rs`, so only the table speaks, and only for the model's file. An `allow`
  or `expect` for a forbidden lint inside the solution then fails with E0453 ("incompatible with previous forbid"), a hint-less
  error of the E0618 kind; `#[expect(unused_must_use)]` fails that way even under `cargo check` [V, probe]. So the silencing count
  of doc 62 §9.1 measures failed attempts here, and E0453 joins the clearance table;
- no `-D warnings`: other warnings are fed back after errors but do not fail the round, because 11 of the pilot's 12 compiling
  rounds carried a rustc warning and would have failed under it (the pilot's warnings were mostly unused imports, §4.9);
- two harness fixes found by the probe: the generated `lib.rs` trips clippy's `write_with_newline` in every task crate (and its
  `let _ = write!(…)` would trip `let_underscore_must_use` if the levels were crate-wide), and `rwm/cargo.py` filters feedback by
  package, not file, so the arm must keep only diagnostics with spans in `solution.rs` [V, probe]. The stimulus crates also start
  from a clippy baseline that is not clean (6 `collapsible_if` warnings); the arm needs a clean baseline and a re-run of
  conformance and the neutrality review, since the `must_use` messages change mb-guided.

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
4. **It carries its own hint-less steps.** A `must_use` error comes with rustc's help "use `let _ = ...` to ignore the resulting
   value"; following it passes `cargo check` but fails clippy's `let_underscore_must_use`, whose error says only "consider
   explicitly using expression value", without the custom message; an attempt to silence either lint fails with E0453. That is the
   E0618 pattern in new places; the prediction is low clearance for those codes unless the `must_use` message itself names the
   sanctioned use [I].

So the order is fixed: remove the slip first, then run GUIDED-L; it is most informative at unit size, where the skeleton compiles
and each unit is small enough to type-check early.

**Hypotheses.** H1–H4 keep their fixed sequence in the primary shape, named at freeze: the shape whose PLAIN R≤3 lands in the
20–60% band on the calibration tasks, unit-sized if both do; if neither does, the calibration loop continues (§6 step 9) and
nothing is frozen.

- **H5 (shape, compute-matched)** Hidden pass at R≤3 is higher unit-sized than whole-file at matched compute, small models and both
  APIs pooled, on 30 task-level paired differences tested like H1. The comparator is whole-file best-of-n: the chance that the
  first of n fresh whole-file R0 samples that passes the visible tests passes the hidden tests, computed exactly from the six R0
  samples (design.json's `matched_resampling_control`), with n ≤ 6 set so that mean compute per episode matches the unit-sized arm;
  whole-file R≤3 is reported beside it. H5 is its own family at α = 0.05, beside H1–H4's; the doc's confirmatory claims therefore
  carry up to about 0.10 familywise error, a deliberate choice because H5 answers the owner's question, not the API theory.
- **H6 (shape × API, secondary)** GUIDED − PLAIN is larger at unit size. Reported as an estimate with its interval; an interaction
  needs about four times the episodes of a main effect for the same power, so no rule rests on it alone.
- **H7 (lint arm, descriptive)** GUIDED-L has fewer escape hatches and fewer class-F accepted-but-wrong programs than GUIDED in the
  primary shape, without losing pass at R≤3. Escape hatches are counted in total (`unwrap`, `expect`, `panic!`, `unreachable!`,
  `unwrap_or_default`, `unwrap_or` with a literal) and only in final files that type-check, because GUIDED-L's table forbids
  `.unwrap()` and `.expect()`, so no compiling GUIDED-L file can keep one and a bare `.unwrap()` count would measure the compile
  rate. At 3 samples the pass-rate interval half-width is 7.5–9.4 points (6 samples: 5.9–8.1) [V, simulation], too wide to settle
  a 5-point non-inferiority margin, so H7 is reported with intervals and decides nothing on its own. Model-free prediction: the two
  `.unwrap()` mutants of §3.7 become compile-time rejections with the reason text, so GUIDED-L's static catch rate is 10/13
  against GUIDED's 8/13 (to be run, §6 step 6).

**Power is not yet known for these contrasts.** The simulation of §3.5 assumed PLAIN near 35% (`power_sim.py`, `mu = -0.6`),
while the calibration band admits 20–60%, and it simulated the API contrast only. Before freezing, re-run it at the calibrated
baseline for H5 (including an unbalanced case, 6 against 3 samples, if a budget cut applies) and for accepted-but-wrong at the
re-pilot's measured rate (the pilot: 2 of 204 episodes), and state the minimum detectable effect per hypothesis. A budget cut
takes only what that H5 simulation says H5 can afford; H1 is tested in the primary shape only, so its power is not what a cut of
the other shape changes.

**Arms and budget** (30 scored tasks, three small models; a local plan for the optimization phase under D058, informative for a
cloud run's token budget):

| Arms | API | Shape | Feedback | Samples per task | Episodes | Generations per episode | Minutes per episode (local) | GPU hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A, B | PLAIN, GUIDED | Whole file | rustc (`cargo test --no-run`) | 6 | 1,080 | 1–4 | 1.96, 3.05 and 2.42 by model: the pilot's floor pace [V, pilot] | 35–55, about 45 at the pilot's model mix |
| C, D | PLAIN, GUIDED | Unit-sized | rustc (`cargo check`), then the unit's tests | 6 | 1,080 | 2–16 | 0.7–1.3 if most units pass within two rounds; 1.8–3.4 at the floor [I] | 13–61 |
| C, D sensitivity | as C, D | Unit-sized | as C, D | 6 | 1,080 | 12 at the floor | about 6 at the floor if unit replies are as long as the pilot's whole-file replies [I, arithmetic] | about 108 |
| E (GUIDED-L) | GUIDED | Primary shape | clippy with the lint table | 3 | 270 | as its shape | 0.7–3.1 [I] | 3–14 |
| F (ablation) | PLAIN, GUIDED | Unit-sized | rustc (`cargo check`) only, no per-unit tests | 3 | 540 | 2–16 | as C, D [I] | 6–31 |
| Stage 1 | | | | | 2,970 | | | about 57–161 |

The unit round estimate, 9–17 s, uses the pilot's own rates: a median uncached prompt of 715–1,428 tokens at 132–234 tokens/s
(5–7 s), a function body of 100–300 tokens at about 38 tokens/s (3–8 s), and 0.6–2 s of cargo (a warm check or clippy of about
0.65 s, plus the unit's test build and run when it type-checks); a whole-file round took a median 23–39 s of generation [V,
pilot; I for the unit sizes]. The pilot's replies were longer than that (median 606–1,216 completion tokens for files whose
references have about 20 lines), so the sensitivity row assumes unit replies of whole-file length: 12 × (≈6 s prompt + ≈23 s
decode + ≈1 s cargo) ≈ 6 minutes per floor episode [I, arithmetic]. Floor pace is 3 units × 4 rounds; success pace 3 units × 1.5
rounds. The table covers only three small models at the pilot's pace; it leaves out Granite's replacement, the 7–14B coder and
the comparator. On the 8 GB card a 7B Q4_K_M (about 4.4–4.7 GB) with a 24,576-token cache does not fit beside the desktop's
≈2.5–2.7 GB and needs partial offload, a 14B cannot fit (doc 44 §2.5), and the comparator at `--cpu-moe` takes about 8–16 minutes
per floor episode at doc 49's rates [I, arithmetic]; their speeds at this context are [U]. The pilot's llama.cpp backend was not
recorded [U]; doc 49 measured CUDA prompt processing at 1.7–1.9× Vulkan on this card, which matters most for the prompt-heavy unit
shape. Whether the 7–14B coder is pooled into H1's "small models" or reported separately is settled at freeze, before any run.
In the cloud the budget is tokens: at the pilot's 45–52k tokens per whole-file episode, arms A and B alone are about 50M tokens,
mostly re-sent prompt prefix, so a cloud run needs prefix caching and doc 48's caps [I].

**Metrics.** Primary: hidden pass at R≤3 of the whole task. Secondary: accepted but wrong (on the common test set across shapes),
hidden share, escape hatches in final files that type-check. Process metrics, the owner's own measures: the time split per round
(generation with prompt evaluation and decode, cargo, tests); the share of rounds that compile and that reach tests, by round
index; per-unit pass rate and rounds per unit; prompt tokens per step; per-code clearance, lint codes and E0453 included; tokens
and compute per success; and how many rounds `-D warnings` would have failed (from the records' warning counts, without an extra
arm).

Decision rules for the shape factor, applied in order; the first that matches decides, each needs its interval as stated, and
per-model estimates are exploratory only:

| Rule | If | Then [I] |
| --- | --- | --- |
| DR9 | H5 holds (compute-matched, significant), unit-sized ≥ +10 points over whole-file R≤3, and accepted-but-wrong on the common test set not worse (interval upper bound at most +5 points) | The unit-sized scaffold package helps weak models on this domain: the plugin SDK's scaffold ships it (P64-S6) and contributor guidance for weak-model coding uses it. For Wilco and doc 65's script tasks it is input to D051's qualification suites, a lower step size a preset may choose, never a default; per-unit "tests" for scripts mean Teller's static checks or Preview probes the user starts (D006). If arm F lands within ±5 points of C and D, the gain belongs to the skeleton and decomposition, not to the per-unit tests, and is reported that way |
| DR10 | H5 holds but the gain is +5 to +10 points, or ≥ +10 while failing DR9's accepted-but-wrong condition | Offer the unit-sized scaffold in the plugin SDK as an option, not the default; no other adoption |
| DR11 | Equivalent within ±5 points (both one-sided tests reject) | Task shape is not the lever at this size; test feedback text and examples next (§6 step 12) |
| DR12 | Harm: the interval lies below 0 | Units that pass alone do not compose into a correct whole; keep whole-file tasks and use per-unit tests only as extra checks |
| DR12b | None of the above | Inconclusive: a new pre-registration with more tasks rather than more samples; no adoption |

Rules for the lint arm, applied after the shape rules; DR13 is checked first and DR14 only if DR13 does not match:

| Rule | If | Then [I] |
| --- | --- | --- |
| DR13 | GUIDED-L lowers both total escape hatches in type-checking files and class-F accepted-but-wrong against GUIDED (intervals exclude 0), with a pass-at-R≤3 estimate no more than 5 points lower | Lint reasons are a candidate weak-model lever: P64-S5 and `AGENTS.md`'s `clippy.toml` reason rule gain a descriptive effect estimate |
| DR14 | GUIDED-L's pass at R≤3 is lower, with the interval's upper bound below 0 | Lints crowd the repair budget for weak models: the plugin SDK's `LLM_CONTEXT.md` and scaffold (P64-S6) and contributor guidance for weak-model loops defer deny-level lints to the final gate. Per-code clearance is reported beside it, descriptively |
| DR14b | Neither | Report the estimates; no change |

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
   cannot fix this text; only the type's shape or the harness can [I]. **The prompt itself suggests the wrong form:** both
   listings show `Problem::OutOfMap(String)` ("carries the unit's label", the item type of `Refusal::Many`) beside the unit
   variant `Refusal::OutOfMap`; PLAIN also has `MissionError::OutOfMap { x, z }` and GUIDED a `struct OutOfMap { x, z }` [V, from
   `crates/mb-spec/src/refusal.rs` and the generated system prompts]. So the slip is a name collision in the shared spec as much as
   a hint-less error, and the low E0618 clearance is confounded by that contradicting context.
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
| Any failed round (compile error, no code block or scan rejection) → compiles next round | — | 6/96 | 1/100 | 0/99 | 1/100 | 0/102 | 0/102 | 8/599 (rounds that failed in cargo alone: 7/560) |

Without Granite, which cleared almost nothing: custom fix notes 10/20, rustc's `?` notes 51/70, hint-less E0618 9/290.
**Reading [I]:** an error that states what is missing or what to do is cleared often; the one with no hint almost never. GUIDED's
handwritten notes did not beat rustc's own informative notes (Qwen: 5/14 against 30/38), so "some hint beats no hint" is suggested,
"custom beats stock" is not. **Caveats:** the E0618 contrast is confounded, because the prompt shows a same-named variant with a
payload (§4.4 item 1), so a model may keep the call shape it was shown; kinds differ in difficulty (not a causal comparison); an
earlier-phase error in round
*r+1* can hide a later-phase one, which overstates clearance; E0618 came in bursts of about four identical blocks per round, which
crowded the 6,000-character feedback. The per-block method used during the run (a block counts as fixed only when every identical
copy is gone) gives lower E0618 rates (0/18 to 15/326) and the same ordering.

### 4.6 What GUIDED cost

- **Compile rate.** Qwen compiled 6/34 PLAIN files at R≤3 against 1/34 GUIDED; Gemma 1 and 1; Granite 0 and 0 [V, pilot]. For
  Qwen this is the complexity tax DR3 describes, but at n = 34, one sample and a shared blocker it is a direction, not an estimate.
- **Newtype and typestate mismatches.** Qwen's repair rounds carried E0308 in 62 GUIDED transitions against 18 PLAIN.
- **A stray `?` on infallible steps.** Saved feedback blocks reading "the `?` operator can only be applied to values that
  implement `Try`": GUIDED 134 (Qwen 14, Gemma 16, Granite 104, most of Granite's being repeats of byte-identical resubmissions)
  against PLAIN 20 (all Granite) [V, pilot]. The models put `?` on calls that return a `UnitId`, a `Plan`, a `TriggerId` or an
  `Exported` directly. A surface that mixes fallible and infallible steps invites the guess that every step is fallible [I].
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

- **Shows [V, pilot]:** three 3–4B local models, thinking off, did not, in this run, write whole Rust files of this size against
  an unseen API of 3–7k tokens with either API, even with three compiler rounds, with a shared spec slip that blocked most rounds;
  the shared spec, not the API variant, dominated the failures; clearance was higher for errors that name a fix (descriptive, and
  confounded for E0618, §4.5); Granite 4.1 3B stalls.
- **Does not show:** any effect of GUIDED on correctness or on accepted-but-wrong code, in either direction; a capability limit of
  3–4B models once the slip is gone; anything about 7–30B models, cloud models or strong coding agents.
- **The floor rule, applied on a deviated scope:** design.json states it for the pilot, whose tasks are P01–P04. On that scope it
  does not fire: Qwen PLAIN passed P02, 1/4 (25%, n = 4, one sample; Gemma 0/4, Granite 0/4). It fires only when computed over
  all 34 tasks (Qwen 2/34) or the 30 scored tasks (1/30), the pilot-policy deviation below. Adding one worked example to both
  variants is therefore a design change, logged in the deviations log with an owner decision (§6 step 1), not an automatic
  trigger.
- **A pilot-policy deviation:** the draft said pilot tasks P01–P04 alone calibrate difficulty, but this feasibility run used all
  34. Local models do not learn from the run, so the models are not contaminated; the risk is ours (tuning tasks after seeing
  outcomes). The deviations log must record it, and §6 step 1 offers two remedies.
- **Compute:** at the floor every episode used all rounds (about 45–52k tokens), so Stage 1's 1,080 small-model episodes would take
  35–55 GPU hours at this pace (about 45 at the pilot's model mix: 1.96, 3.05 and 2.42 minutes per episode), not the draft's
  20–25; early stops shorten it once models succeed. With the unit-sized factor, its ablation and the lint arm, about 57–161
  (§3.9); under D058 none of it runs on the owner's GPU before the optimization phase.

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
R0 and 1/67 at R1, none later; Granite none. Cargo medians are over the 768 rounds with a complete code block: 761 reached cargo
and 7 were rejected by the static scan (0 ms), which leaves the medians unchanged at two decimals. The 8.4 hours are the sum of the
806 rounds' recorded generation, cargo and test time; the four runs' spans (first to last record) also sum to 8.4 h, and first to
last record across the day is 9.8 h, the gap being the Qwen interruption.

- **Compile cost is not the bottleneck here.** Each round builds one small task crate against prebuilt dependencies in about a
  second; decoding alone took 73–82% of wall time and prompt evaluation 15–24%, although prefix caching kept the uncached part of
  each prompt near a tenth. Recorded generation, cargo and test time cover 99.8% of the wall-clock time between rounds.
- **Reaching the tests is.** Tests ran only in the 12 rounds that compiled, and visible-test failures were fed back in 3 (Qwen
  PLAIN: T26 twice, T08 once); every other compiling round either passed its visible tests or was the last. The unit tests already
  were a feedback channel; the models almost never got to it.
- **So the idea applies to the task shape [I].** The premise (compilation is the cost) did not hold here, but the idea behind it
  can be tested: give weak models unit-sized work, one function against a fixed, compiling skeleton, with that function's tests as
  spec and feedback. This is Plotroom's harness doctrine for Wilco (one small bounded decision per step, code owns the structure)
  and doc 65's snippet-sized tasks, applied to code. §3.9 makes it the next iteration's second factor, tested as a package with an
  ablation.
- **Clippy costs no more than the pilot's build step.** Warm, on one task crate (T22 GUIDED, three runs each): `cargo clippy
  --all-targets` 0.64–0.69 s, `cargo check --all-targets` 0.61–0.64 s, the pilot's `cargo test --no-run` 0.87–0.89 s [V, probe].
  Only clippy carries clippy's own lints (a lint table's `disallowed-methods` reasons, `let_underscore_must_use`) to a model (doc 62
  §3.1), so it is the right inner-loop command, with one limit: lint text appears only once a file type-checks (§3.9). §3.9 adds
  the lint arm.
- **Warnings would block a `-D warnings` loop.** 455 of the 761 rounds that reached cargo carried rustc warnings (975 in all), and
  so did 11 of the 12 rounds that compiled; in the saved feedback, 404 of 434 warning headings are unused imports.
- **For Plotroom's own workspace** the owner's premise (a complete compilation per change is far slower than checking one crate) is
  the basis of `AGENTS.md`'s "Fast inner loop, full gates at the end" rule, adopted on the owner's suggestion on 2026-09-28
  (§5.1). This section backs only that clippy costs no more than check per crate; Plotroom's build times were not measured here
  [U].

## 5. Implications for Plotroom

### 5.1 Coding agents building Plotroom (`AGENTS.md`)

Doc 62 §8's amendment is already in `AGENTS.md` (witness and guard types, "Diagnostics as Guidance", trybuild negative tests).

**Adopted on the owner's suggestion (2026-09-28):** `AGENTS.md`, section "Local Repo-Specific Rules", now has "Fast inner loop,
full gates at the end": while changing code, `cargo clippy -p <crate> --all-targets -- -D warnings`, then that crate's unit tests
filtered to the module under change, written test first; the full workspace gates once before finishing; units kept small enough
that the loop stays in seconds. What this doc adds to it: clippy costs no more per round than a check on one small crate (§4.9)
[V, probe]; it is the only command that carries clippy's own lints (`disallowed-methods` reasons, `let_underscore_must_use`) to
an agent, while `#[must_use]`, `#[deprecated]` and `on_unimplemented` text are rustc's and reach `cargo check` as well (doc 62
§3.1); and its lint text appears only once the crate type-checks, so compile errors come first in any case [V, probe]. One wording
fix is proposed (proposal-only, pending the owner): the rule's "the workspace's guidance lints reach you only through clippy"
becomes "clippy's guidance lints reach you only through clippy". One caveat, for weak models only: `-D warnings` turns an unused
import into a failed round; it would have failed 11 of the pilot's 12 compiling rounds (§4.9). The rule's readers are mostly
strong agents, for whom that is a one-line fix, so no change is proposed; the lint arm (DR13, DR14) and §3.9's `-D warnings`
count inform whether weak-model loops (the plugin SDK's scaffold, contributor guidance) defer deny-level warnings to the final
gate. The rule rests on build-time facts, not on an effect estimate from this experiment, and its workspace premise stays [U]
until Plotroom has code to time.

The pilot supports none of `AGENTS.md`'s other rules by an effect estimate, and weakens none. Three refinements follow from the
probes and the pilot's diagnostics; all are **proposal-only**, pending the owner, and phrased to satisfy "Maintaining This File"
(general, no reference to this study):

| Id | Where in `AGENTS.md` | Proposed change | Evidence | Status |
| --- | --- | --- | --- | --- |
| P64-A1 | "Diagnostics as Guidance", "Where the attributes go" | After "guidance-bearing bounds on functions (`fn f<T: Trait>(…)`)", add: "or on the method's own `where` clause (`fn commit(self) -> … where S: Checked`); a method that exists only in an inherent impl for one state, or behind a bound on the impl block, fails with E0599 and none of the custom text" | [V, probe]; 6 of 8 GUIDED compile-time catches used it (§3.7); the text reached the models (§4.6) | Proposal; one sentence |
| P64-A2 | "Diagnostics as Guidance", new bullet | "**Where no attribute reaches.** Errors raised by name resolution and type checking (a type mismatch, a missing method, a call on something that is not a function) carry no custom text. For mistakes that surface that way, put the guidance in type and method names and the doc comment, avoid same-named items with different shapes, or reshape the API so the likely mistake cannot arise or is correct as written. On a generic typestate type, a signpost method under the likely-guessed name with a sealed `on_unimplemented` bound turns the E0599 into an E0277 with the custom text; the listing then advertises that method, and a non-generic type needs a probe first, because rustc rejects trivially false bounds there" | Hint-less E0618 cleared 9/318 rounds against 11/28 (custom) and 55/189 (rustc's own `?` notes) [V, pilot, descriptive; confounded by a same-named variant in the prompt, §4.5]; proximate errors carry repair [44]; the signpost mechanism is P64-A1's and doc 62 §3.3's trap trait [I, not probed for this use] | Proposal |
| P64-A3 | "Type Safety", newtypes and witness rules | Reconcile the newtype rule ("Provide `from_raw`") with the witness rules: "An id that a store issues is a witness bound to that store's revision or generation: `from_raw` stays crate-private; a use after a delete or an undo is checked (the lookup returns `Option` or `Result`), and values from storage or the wire re-enter through that checked lookup" | The ID-MIX catches of §3.7 come from distinct newtypes, which the existing newtype rule already gives; no mutant forges an id through `from_raw`, so crate-private `from_raw` is untested here (a mutant or probe for that path comes first, §6 step 6). Cost of distinct ids: more E0308 and `.unwrap()` in GUIDED (§4.6) | Proposal; a witness-surface rule, so a design-gap request and a UI test per `AGENTS.md` (candidate 1 below) |

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
  wrong" list: the pilot ran without one and sat on the floor [23].
- **P64-S5 Close the `.unwrap()` escape in the scaffold:** clippy `unwrap_used` and `expect_used` at deny in the plugin template's
  lint table (the pilot doubled `.unwrap()` under GUIDED for Qwen). This helps honest authors only; the host still enforces grants
  at run time (doc 62 §7.2). Where the fix depends on the SDK, a `disallowed-methods` entry whose reason names it (as in GUIDED-L)
  says more than the generic `unwrap_used` text. Two details from the probe [V, probe]: lints speak only once the file type-checks,
  so they help after the compile errors are gone; and levels set with `forbid` on the scaffold's module cannot be allowed away
  inside it, since an inner `allow` or `expect` fails with E0453, itself a hint-less error, so `LLM_CONTEXT.md` should say that the
  levels are fixed (§3.9). The author owns `lib.rs` and can delete the attribute, so this too helps honest authors only. DR13
  gives it a descriptive effect estimate.
- **P64-S6 Scaffold unit-sized work:** the plugin template ships a compiling skeleton (signatures, doc comments, `todo!()` bodies)
  with one test per function, and `LLM_CONTEXT.md` tells an agent to fill one function at a time: `cargo clippy -p` on the plugin
  crate, then that function's tests (the `AGENTS.md` fast loop). Evidence so far is the pilot's process data (tests reached in 12
  of 806 rounds, §4.9); DR9–DR12b decide whether it becomes the default for weak models, and arm F whether the per-unit tests or
  the skeleton carry it.

### 5.3 Wilco and Teller, by analogy

Wilco never writes Rust, but its typed command layer is a GUIDED API and Teller is its compiler. Proposals [I]:

- **P64-W1 Weak models fill slots, not files.** At whole-file scale both APIs floored for 3–4B models in this run, with a shared
  spec slip blocking most rounds [V, pilot]. That is consistent with doc 31 §9, doc 30's measurement and doc 65 §5.3's table
  (FR0–FR4: typed IR slots and menus, no script text). Whether sub-5B setups may write scripts, even in the Strict dialect, is
  a transfer from Rust to scripts [I] and is settled by D051's qualification, not by this pilot; the unit-sized shape (§3.9,
  DR9–DR12b) and a snippet-sized script experiment are inputs to those qualification suites, a lower step size a preset may
  choose, never a default.
- **P64-W2 Every finding names the fix, and the harness measures it.** The pilot's clearance contrast (§4.5, descriptive and
  confounded for E0618) supports doc 61 §4.6's (item 5) and doc 65 §4.9's requirement of findings with the next action and
  allowed values. Add the instrument: per-finding-code clearance in
  the qualification suites (docs 44, 48); a sticky code is a finding-text or surface bug to fix in code, not in the prompt.
  Early-phase findings matter most: rustc prints lint guidance only after a file type-checks [V, probe], so one hint-less early
  error hides every later hint. Teller's parse and resolve findings must name the fix, and a report should say when later checks
  were skipped, so the model knows more feedback is coming.
- **P64-W3 Group identical findings, one root per repair.** E0618's bursts of identical blocks crowded the feedback; doc 62 §6.9's
  "one *root* per turn, with the findings that share its entity or field grouped" and RustAssistant's grouping [10] apply.
- **P64-W4 Stop on repeats.** Granite resubmitted identical code in 58% of repair rounds. Doc 61's stop-on-repeat rule and a switch
  to resampling or the authored split are necessary for weak setups [12, 15].
- **P64-W5 Re-align doc 65 §6.** Before any Strict-versus-plain run: a calibration pilot on pilot tasks only, a review of the shared
  spec and cards for slips that produce hint-less findings, the floor rule, snippet-sized tasks (one condition, one init line, one
  SQS sequence) rather than whole files, and the accepted-but-wrong metric as H2.

### 5.4 Friction review (D049)

Friction found, for the three audiences. The recurring model-facing frictions are filed in `docs/friction/register.csv`
(2026-09-28): **FR-M-028** errors that name no fix, and prompts that show a same-named item with another shape, stall weak models'
repairs; **FR-M-029** tests are out of reach behind compile errors (12 of 806 rounds reached them, §4.9); **FR-M-030** in a
clippy loop, `-D warnings` fails weak models' compiling rounds on unused imports, and the `must_use` → `let _` →
`let_underscore_must_use` and `forbid` → E0453 steps carry no custom text; **FR-M-031** API surfaces invite wrong guesses (a `?`
that cannot convert at the boundary, fallible and infallible steps mixed without a naming cue). **FR-C-013** (instruments in
scratch copies) is updated: doc 64's instrument now lives in `tools/rust-weak-models`, but its run records stay local until a
results CSV lands (§6 step 11); `tools/local-qual`'s part is unchanged.

- **Models, not filed separately:** truncation of long files (§6 step 4 removes it for the experiment) and stalls without a stop
  rule (already P64-W4 and doc 61's stop-on-repeat rule). Product transfer: P64-S3, P64-S6, P64-W2 to W4.
- **Contributors, fixed in this change or one-off:** a complete compilation on each change (the owner's point), removed by
  `AGENTS.md`'s fast-loop rule (§5.1); the pilot-policy deviation and an under-estimated compute budget (§4.8, §3.9; one-off, in
  the deviations log); the harness's generated `lib.rs` would feed a clippy warning back in every round of a lint arm (fix listed
  in §3.9 and §6 step 6); `cargo fmt` or `cargo clippy --fix` would silently rewrite the stimuli, and a `clippy.toml` or
  `rustfmt.toml` above the folder would reach them (removed in this review: the folder pins both files, `test_rwm` pins the
  prompt hashes, and the hygiene check reports enclosing configs; this also removes the clippy and rustfmt part of FR-C-033,
  whose toolchain and cargo-config part remains).
- **People:** none directly; the transfer is through Teller's findings (P64-W2).

## 6. Next steps

All of this is deferred under D058 (editor first; lane D starts no new work). When harness work resumes, model runs go cloud-first
through `tools/local-qual`'s guarded, budget-capped backend (doc 48; D044–D046, D050), on a route D047 allows; the local arms wait
for the optimization phase, and no agent starts a local model server unless the owner asks. Steps 1–7 need no model at all.

1. **Record the run** as a feasibility pilot in the deviations log. Then either write fresh scored tasks for Stage 1 (cleanest), or
   freeze the current 30 with the deviation stated and only shared-spec edits applied to both arms (cheaper) [owner]. The same
   owner decision covers the worked example (step 3): on its pre-registered scope the floor rule did not fire (§4.8).
2. **Remove the shared slip and the name collision:** state payload-free refusals in the rules sheet and spec, and give the
   same-named items one consistent shape or distinct names (`Problem::OutOfMap(String)` beside the unit `Refusal::OutOfMap`, and
   the `OutOfMap` error types, §4.4); both arms alike. This comes first: it also gates the lint arm, whose text appears only on code
   that type-checks (§3.9).
3. **Add one worked example** (a pilot task solved in each variant's API) to both variants, shown in each arm's shape, as a logged
   design change (step 1).
4. **Raise the reply cap** to 4,096 tokens, or score truncation as its own failure class.
5. **Build the unit-sized shape** (§3.9): first write down the protocol of §3.9 (reply format, splice by name, signature changes
   as format failures, allowed file-level additions, a fresh conversation per unit, the unit system text, the per-episode cap of 4
   × the reply cap, stubs excluded from escape-hatch counts, per-step padding); split each task into 2–4 units with a compiling
   skeleton and per-unit visible tests that never touch a trap; loop per unit (`cargo check -p`, then that unit's tests); build
   arm F (the same units, compile feedback only). Prove it model-free: each variant's references pass unit by unit and whole, a
   mock repairer finishes every unit, and the 13 mutants re-run in the unit shape leave PLAIN at 0/13 static with its silent
   count unchanged (any change is reported as skeleton leakage). The neutrality reviewer sees the unit names, signatures and
   per-unit tests without the trap labels.
6. **Build the lint arm GUIDED-L** (§3.9): first make the stimulus crates clippy-clean against a recorded baseline (6
   `collapsible_if` warnings today) and re-run conformance and the neutrality review after the `must_use` messages land behind
   their feature; then the table in the harness's pinned `clippy.toml`, clippy run with `-A clippy::all`, levels as `forbid` on the
   solution module, feedback filtered to spans in `solution.rs`, the generated `lib.rs` made clippy-clean (its `write!` newlines,
   logged as a deviation), silencing and E0453 counted; rerun the 13 mutants under it (prediction: 10/13 rejected at compile time)
   and add a mutant that forges an id through `from_raw` before P64-A3 cites any evidence.
7. **Report the time split** (generation with prompt evaluation and decode, cargo, tests), the per-round compile and test-reach
   rates and the prompt tokens per step in every run summary; the records already hold the first two, and
   `analysis/time_split.py` computes them.
8. **Models:** replace Granite 4.1 3B; add a 7–14B coder and the Qwen3-30B-A3B comparator, cloud-first (D058); locally, in the
   optimization phase, the 7B needs partial offload at this context and a 14B does not fit the 8 GB card (§3.9); an optional
   strong "ceiling" row to check solvability. Decide before any run whether the 7–14B coder is pooled into H1's "small models" or
   reported separately.
9. **Re-pilot on calibration tasks outside the scored set, in both shapes:** P01–P04 plus new tasks written for calibration (or
   tasks dropped from Stage 1 scoring), never scored tasks. At most three calibration iterations; every spec change goes into the
   deviations log before Stage 1. The target: PLAIN R≤3 between 20% and 60% in at least one shape for at least two small models;
   name the primary shape; replace §3.9's unit-round estimate with the measured one.
10. **Freeze:** re-run the power simulation at the calibrated baseline for H5 (compute-matched, with the unbalanced case) and for
    accepted-but-wrong at the measured rate, and state the minimum detectable effect per hypothesis (§3.9); then the analysis
    script, the lock file with hashes, the independent reviews (the unit decomposition included); then Stage 1 (about 2,970
    episodes; at the pilot's local pace 57–161 GPU hours, or its token equivalent in the cloud; §3.9 says what a cut may take).
11. **Harness in the repository:** it is packaged under `tools/rust-weak-models` as research tooling (it evaluates the development
    process, not a product feature; design-gap candidate 4 asks where such tools live). Still to do: a per-episode results CSV
    under `docs/research/data/` (no raw model text), so the pilot's numbers can be re-read without the local run records; land it
    before any `AGENTS.md` proposal cites pilot numbers.
12. **Then:** Stage 2 (types × text); an optional arm that rewrites hint-less rustc errors into fix-naming text in the harness, which
    tests "errors that name the fix" directly; doc 62 §9.1's bypass and silencing test for strong coding agents on the same harness.
13. **Update this doc** with Stage 1 results under DR1–DR14b, and fold P64-A1 to A3 or drop them accordingly. The doc is past the
    600-line soft ceiling (FR-C-019); when Stage 1 results arrive, they go into a companion file with §3.9, rather than growing
    this one.

## Design-gap candidates (listed, not filed)

1. **Store-issued ids as witnesses** (P64-A3): the newtype `from_raw` rule against the witness rules; ids bound to a store
   revision or generation so a use after delete or undo is checked; checked re-entry from storage; a UI test per misuse.
2. **Diagnostic clearance as a qualification metric** (P64-W2): which doc owns the per-code instrument and its threshold.
3. **An agent-usability gate for the plugin SDK** (P64-S1): a task suite and pass criteria before an SDK release.
4. **Where research harnesses live:** `tools/` layout, CI status (opt-in, local GPU) and data retention for model outputs.
5. **Task shape for weak-model coding** (DR9, P64-S6, P64-W1): which doc owns the unit-sized scaffold rule across the plugin SDK,
   doc 65's script tasks and Wilco's slots, once DR9–DR12b have a result; for Wilco and scripts the answer runs through D051's
   qualification suites, not a default.

## Open questions

1. **Owner:** which "weak" does the theory mean: 3–4B local models (the pilot answers "not by itself" for whole files), 7–30B local,
   or cheap cloud models? [U]
2. **Owner:** fresh scored tasks, or the current 30 with a stated deviation (§6 step 1)? [I]
3. **Owner:** adopt P64-A1 to A3 now, or after Stage 1? [U]
4. **Owner, reframed by D058:** the GPU-hour cap is answered for now (the owner's GPU stays free; local arms wait for the
   optimization phase). What remains is a token and spend cap for a cloud-first Stage 1 through doc 48's capped backend (about
   2,970 episodes; §3.9 gives the local equivalent, 57–161 GPU hours). [U]
5. **Measurement:** which is the smallest local model whose PLAIN R≤3 reaches 20% on these tasks, in either shape? [U]
6. **Measurement:** do unit-sized tasks lift 3–4B models off the floor, and do units that pass alone compose into a correct whole
   (DR9–DR12b), and do the per-unit tests or the skeleton carry any gain (arm F)? [U]
7. **Measurement:** do lint errors help weak models or crowd their repair budget (DR13, DR14), and do they stall on the hint-less
   `let_underscore_must_use` and E0453 follow-ups? [U]
8. **Measurement:** does a harness-side rewrite of hint-less errors lift the floor for 3–4B models? [U]
9. **Measurement:** do strong coding agents show a GUIDED effect on accepted-but-wrong code, or only on bypass rates (doc 62 §9.1)?
   [U]
10. **Technical:** can every task be split into units without a unit boundary, name or visible test pointing at a trap (the
    neutrality review, §3.9)? [U]
11. **Technical:** which cloud route for the comparator satisfies D047 for a combat-flavoured synthetic domain? [U]

## Findings for sibling docs (reported, not fixed)

- **Doc 65 §6** says it "must be re-aligned with it when doc 64 is published": the design matches; add P64-W5's calibration step,
  the floor rule (computed on its pre-registered scope) and the pilot-policy lesson; its §6.4 sample size assumes this doc's power
  simulation, which stands for an API contrast at a 35% baseline and needs a re-run at its calibrated baseline; its "three small local
  models" should not include a model that stalls like Granite 4.1 3B did here. It can mirror §3.9's shape factor as snippet versus
  whole script, and report the time split and the share of rounds that reach its checks.
- **Doc 62 §9.1** (coding-agent misuse evaluation) can run on this harness; its arms B and C correspond to GUIDED's witness rules and
  diagnostics, and GUIDED-L is a small-model version of arm C. Arm C's lint clearance should be counted only on rounds that
  type-check (below).
- **Doc 62 §3.1** ("bound on a function"): the probe shows a method's own `where` clause works too (P64-A1). The channel table
  lacks two rows [V, probe]: late lints (every clippy lint, `unused_must_use`) print nothing while any type error remains, so a
  type error hides every lint reason; and the error that follows rustc's `let _ =` help, clippy's `let_underscore_must_use`,
  carries no custom text, only "consider explicitly using expression value".
- **Doc 55** (presets): presets set how Wilco asks, never repair limits (D048 item 2), and Wilco writes no Rust, so this doc's
  per-model findings for Rust coding (DR2, DR8, DR14) go to the plugin SDK's guidance and contributor guidance, not to presets.
  What transfers is the choice between a repair turn and a fresh sample after a stall (doc 61 §4.6 item 6; P64-W4), which is a
  preset setting; Granite 4.1 3B's local qualification should note its llama.cpp stalls on code.
- **Doc 62 §2** (evidence table, RustAssistant row): its GPT-3.5 figures (10.7% → 73.7%) come from the arXiv version's prompt
  ablation (Table 5), while the ICSE camera-ready runs that ablation with GPT-4 (Table IV, 139 → 252 of 270); the row should name
  the version it quotes (§2.2 and Sources [10] here).
- **D058** says doc 64's pilot "ran about 7.5 hours"; the records give 8.4 hours of recorded round time, 8.4 h summed over the
  four runs' spans and 9.8 h from the first to the last record including the Qwen interruption (§4.9). The decision is unaffected.

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

- [10] Deligiannis, Lal, Mehrotra, Poddar, Rastogi. RustAssistant: Using LLMs to Fix Compilation Errors in Rust Code. ICSE 2025.
  Camera-ready (the source of Tables I, IV and VI quoted here):
  https://www.microsoft.com/en-us/research/wp-content/uploads/2024/08/paper.pdf. Earlier arXiv version, single version v1 with
  four authors, titled "Fixing Rust Compilation Errors using LLMs", whose tables differ: https://arxiv.org/abs/2308.05177
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
- Research docs 16 (legend), 21, 25, 30, 31 §9, 44 (§2.5), 46, 48, 49, 55, 61 (§2, §4.6), 62 (§2, §3, §6.9, §7, §8, §9.1), 63
  (§9), 65 (§5, §6); decisions D006, D047, D048, D049, D051, D052, D058; `docs/friction/register.csv` (FR-M-028 to FR-M-031,
  FR-C-013, FR-C-019)

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
- **Corrected from the research inputs:** (1) 74.8% and 56.0% are the synthesis-only reductions of compile errors (Table 2
  caption); the 75.3% and 52.1% of §5.2 average synthesis and translation; the doc uses the synthesis figures (the MBPP runtime
  overhead, also 52.1%, is a separate number); (2) RustAssistant's GPT-4 micro-benchmark best is 252/270 (Table IV of the ICSE
  camera-ready); in that version Table I's GPT-4 N = 5 row (252 fixed plus 7 + 4 + 14 failures = 277) does not sum to 270, while
  the arXiv v1 reports 92.59% (250/270), a row that does sum; (3) "Unreliable in Practice?" analyses
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
- **Not re-opened** (tagged "per research pass" or "per doc N" in the text): Multi-LCB [2] (its abstract was re-opened in the
  review pass below), RustRepoTrans [7], Kamoi et al. [16], monitor-guided decoding [18], typed holes [19], API misuse [21],
  DocPrompting [23], type-error ablation [44], Weiss et al. [45], the Rust 1.85 post [29], the Rust Reference [30], strict-path's
  crates.io and docs.rs pages [32], Ronacher [33, 35] and the method papers [39–42]; SafeTrans [9] and the practice posts [36–38]
  were re-opened in the review pass below. Numbers that sit only in a paper body we did not re-read
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
  `prompt_ms` and `predicted_ms`, `build_ms` and `test_ms`; cargo median and p90 over the 768 rounds with a complete code block
  (761 reached cargo; corrected in the review pass below); compiling
  rounds by round index; rounds whose visible-test failures were fed back (compiled, visible fail, not the last round); warning
  counts per round. Recorded time covers 99.8% of the wall-clock gaps between consecutive rounds. §4.2's tokens and generation
  seconds per episode and §4.1's 2.0–3.1 minutes per episode re-derived: unchanged.
- **Differences from the figures shown to the owner during the run:** those used Granite's partial records (187 rounds); the table
  uses the complete file (272 rounds; still 0 compiled; shares agree to the percent). Cargo medians here exclude the 38 rounds
  that never reached cargo (format failures), which moves them from 0.8, 0.9 and 0.6 s to 0.84, 0.97 and 0.63 s.
- **Warnings:** counted from the records' `n_warnings`; the unused-import share (404 of 434 warning headings, counted as lines
  that start with `warning:` or `warning[<code>]:` in the saved feedback of every round with a complete code block; an earlier
  count gave 403 of 432) from the saved feedback, which is cut at 6,000 characters with errors first, so it undercounts warnings
  in long feedback.
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

### 2026-09-28, review pass (findings re-checked, then applied or skipped)

- **2026-09-28, review of doc 64 and `tools/rust-weak-models`.** Each finding was re-checked against its source before it was
  applied. **Web and PDF sources re-opened:** PROBE [1] (HTML: "We selected two feedback iterations", +0.05 for pass@1 and pass@5,
  both reasons for Rust's gain), Rust-SWE-bench's abstract [6], the abstracts of [14] ("We hypothesize …") and [17] ("may bias"),
  SafeTrans [9] (HTML: "nearly double" names Qwen2.5-Coder and DeepSeek-Coder; the 18–30% E0277/E0308 sentence), Multi-LCB's
  abstract [2] (no Rust or Scala figures in it), the practice posts [36]–[38], and text extractions of the type-constrained
  decoding PDF [13] (§5.2's 75.3%/52.1% average synthesis and translation; Table 2's caption gives 74.8%/56.0% for synthesis) and
  of both RustAssistant versions [10] (ICSE camera-ready: five authors with Poddar, Tables I, IV and VI as quoted, Table I's GPT-4
  N = 5 row sums to 277; arXiv v1: four authors, 92.59% = 250/270, a GPT-3.5 prompt ablation 29 → 199 of 270). **Recomputed from
  the pilot records and task files:** 154 hidden tests on the scored tasks (168 with the pilot tasks), 97 trap tests, one visible
  test per task; Qwen PLAIN 1/4 on P01–P04 (P02), 2/34 over all tasks; `?`-on-non-`Try` blocks GUIDED 14/16/104, PLAIN 0/0/20;
  599 transitions from failed rounds (560 cargo failures, 33 without a code block, 6 scan rejections; next round compiles 7 + 0 +
  1); 434 warning headings, 404 of them unused imports; 768 rounds with a complete code block, 761 of which reached cargo (7 scan
  rejections, 0 ms), medians unchanged; minutes per episode 1.96/3.05/2.42, so 1,080 episodes take 35–55 h (44.6 h at the pilot's
  mix); 8.43 h of recorded round time, run spans summing to 8.38 h, 9.84 h from first to last record; the power simulation's CI
  half-widths at 30 tasks (3 samples 7.5–9.4 points, 6 samples 5.9–8.1). **Probed** (rustc 1.98.1, clippy 0.1.98, rustfmt 1.9.0,
  throwaway crates outside the repository): an inner `#![allow(clippy::disallowed_methods)]` under a module-level `forbid` fails
  `cargo clippy` with E0453 and passes `cargo check`; `#[expect(unused_must_use)]` under `forbid` fails `cargo check` with E0453;
  `disable_all_formatting = true` makes `cargo fmt` a no-op on a copy of the stimulus crates (`--check` fails with 1,399 lines of
  diff without it); the old static scan accepted grouped imports, crate aliases, raw identifiers and macro-built `std` paths.
  **Read for the rules:** D006, D048, D051, D058; doc 61 §4.5–§4.6; doc 62 §2 and §6.9; doc 65 §6; docs 44 §2.5 and 49 (fit and
  speed of larger models); `docs/friction/README.md` and the register.
- **Applied to this doc:** the corrections above; D058 in the status line, TL;DR, §6 and open question 4; the floor rule's
  pre-registered scope and the name collision (§4.4, §4.5, §4.8, §6 steps 1–3); §3.9 rewritten (the scaffold package with ablation
  arm F, a written unit protocol, per-step padding, accepted-but-wrong on the common test set, the skeleton-leakage check, a
  compute-matched H5 with its familywise error stated, H7 made descriptive with total escape hatches in type-checking files,
  GUIDED-L's `must_use` messages behind a feature and out of the listing, clippy with `-A clippy::all`, E0453, ordered and
  exhaustive DR9–DR14b retargeted away from D048 presets and toward D051 qualification, a budget with a sensitivity row, the
  models it leaves out and the unrecorded backend, and power stated as not yet simulated); clippy's exclusivity narrowed to
  clippy's own lints (TL;DR, RQ7, §4.9, §5.1, with a one-word `AGENTS.md` wording proposal); P64-A1 to A3, P64-S4 to S6, P64-W1
  to W3 and the sibling-doc findings (docs 55 and 62, D058) revised; friction FR-M-028 to FR-M-031 filed and FR-C-013 updated;
  the working copy converted to LF.
- **Applied to the harness** (test first: of 24 new tests in `test_rwm_guards.py`, 16 failed before the change, as did the
  extended `.gitignore` test; the other 8 pin behaviour that already held, such as the prompt hashes): an allow-list static
  scan that also rejects crate-root aliases, glob imports of the root, raw-identifier and macro-built paths (0 verdict differences
  against the pilot's scan on the 768 saved solutions and the 68 references); a loopback-only client that reads only
  `RWM_API_KEY`, needs `--allow-remote-endpoint` and https for any other host and never follows a redirect (a two-server test shows
  the token no longer reaches a redirect target); pinned `rustfmt.toml` (formatting off) and empty `clippy.toml`; pinned listing,
  system-prompt and user-prompt hashes, equal to the pilot's; the hygiene check now reports key-like tokens, a CR without LF,
  terms from an optional local denylist and unshadowed `clippy.toml`/`rustfmt.toml` above the folder, and the README says what it
  does not check; the server command passes values through the environment (a stub script received an apostrophe and a
  "; Write-Output" path as single arguments); `start-server.ps1` defaults to 24,576 tokens; tests clean up their temporary
  folders; probe build output is ignored; the README gained the scaffold-first note and the "never `cargo fmt` or `clippy --fix`"
  rule. `CODE-INDEX.md` and `docs/README.md` (a §5 row for this doc, status line, headings, §6.4) updated.
- **Verification after the change** (from `tools/rust-weak-models`): `python -m unittest test_rwm` 77 tests OK;
  `python runner.py scaffold` 68 crates; `python runner.py verify --tasks all` 68/68; `cargo test --workspace --offline --locked`
  406 passed in 146 binaries, 0 warnings; `python runner.py mutants --tasks scored` PLAIN static 0/13, loop 4/13, silent 9/13,
  GUIDED static 8/13, silent 5/13 (unchanged); `run --mock fail-first --tasks pilot` repaired at R1; `listing` and `run --dry-run
  --tasks all --samples 6` with the pinned hashes; `cargo clippy` on the five crates after `cargo clean -p` the same 6
  `collapsible_if` warnings; `cargo fmt --all --check` clean; `python -m rwm.hygiene` 305 files, 0 problems; the changed docs and
  files scanned as bytes: no hidden characters, BOM, CR, local paths or key-like tokens.
- **Skipped, with reasons:** splitting this doc (over 1,100 lines) now: not a cheap change while other work edits the indexes;
  §6 step 13 puts Stage 1 results and §3.9 into a companion file, and FR-C-019 already records the ceiling. The generated `lib.rs`'s `write!`
  newlines: changing them now is an experiment deviation, so they wait for the GUIDED-L build (§6 step 6). The commit-message BOM
  advice: this pass made no commit. Per-model budget rows for the replacement model, the 7–14B coder and the comparator: their
  speeds at this context are unmeasured [U] and, under D058, not to be measured on the owner's GPU now; the fit limits and the
  comparator's rate are stated instead. Every other finding was applied.
