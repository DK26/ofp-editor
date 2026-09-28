# Type-driven guidance: making wrong code and wrong actions unrepresentable

Research doc 62 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Questions answered (owner, 2026-09-28, paraphrased): (1) "Encode all knowledge and know-how into the harness; more powerful models
could go even crazier and be granted more freedoms." (2) "Learn from OpenCode (or better examples) about the usefulness of an LSP
server to the LLM." (3) "I had a research project: a Rust library that prevents LLM errors by type design (typestate, witness and
guard patterns), with compile errors guiding the LLM and comments as prompts on how to do it right: `strict-path`. Is that study
relevant now?"

**Governing principle (owner, 2026-09-28, verbatim):** "The API leads the user (human or LLM) into correct usage and states, making
bad states impossible. Making logical errors easy to spot." And its follow-up: "The language won't compile if things are not correct,
and the entire language is built to detect issues at compile time." So the aim is enforcement, not advice: wherever a check can be a
gate (a type that cannot be built, an action that cannot be expressed, code that does not compile or export), it should be one, and
guidance (diagnostics, doc comments, messages that name the next step) makes the gate easy to pass. It applies to three audiences:
the coding agents that write Plotroom, Wilco and other models using Plotroom's APIs, and people using the editor. Doc 65 applies the
same principle to mission scripts.

**Status: proposal.** Nothing in the repository was coded or changed except this file. Two throwaway probe crates outside the
repository were checked with rustc and clippy 1.98.1 (verification notes). `AGENTS.md` is unchanged: §8 summarises a proposed
amendment that awaits owner approval. Every design proposal is [I].
**Epistemic legend** (doc 16's): **[V]** read at the cited source or commit on 2026-09-28. **[V, probe]** observed by compiling the
probe crates. **[V-author]** a number published by a paper's authors, quoted as published and not reproduced by us. **[I]** our
inference or proposal. **[U]** unknown, needs measurement.
**Relation to sibling docs.** Doc 21 sets the agent doctrine and doc 30 (D027) the knowledge stack; doc 23 §13.4 designs Teller's
model-shaped diagnostics, and validation-and-lints §9 places Teller; doc 45 §2.1 and core-document-model §5.1 chose module privacy
over `compile_fail` doctests; doc 57's CL1 enforces a cache tier by type; doc 22 §7.3 sketches the plugin WIT; doc 24 (rule L2) and
doc 27 §4.10 set the path rules. Doc 10 studied OpenCode's harness but not its LSP path. This doc does not repeat them. It asks how
far types, compiler diagnostics and lints can carry guidance, for the coding agents that write Plotroom and for Wilco at run time,
and what strict-path contributes. The wider value of a language server to an LLM (direction 2) belongs to Teller's design (doc 61,
same day); §4 covers only the part that decides whether type-driven guidance reaches an agent. Freedom levels for stronger models
(direction 1) belong to doc 63 (same day); §6.3 here covers only the type that would carry a grant.
**Names.** A *witness* is a value whose existence proves that a check ran (`Admitted<T>`, `UserIntent`). A *guard* wraps a value so
it can be used only through checked operations (`Guarded<T>`, strict-path's `StrictPath<M>`). A *capability token* is a witness
that grants an action (`EgressGrant`). A *feed* is how an agent receives diagnostics: **raw** (it runs cargo in a shell and reads
all of it) or **errors-only** (an editor-style client forwards language-server diagnostics of error severity, as OpenCode does).
**Hygiene.** Public sources only. strict-path is the owner's public crate and is cited like any other source. No game content, no
local paths.

## TL;DR

- **Is strict-path relevant? Yes, mostly as confirmation, plus four additions.** Plotroom's design already holds its strongest
  patterns: `Admitted<T>` with a private constructor, the typestate `CoreBuilder`, `UserIntent` behind a sealed input source, and
  `Guarded<T>` without `DerefMut` [V]. The study adds (a) explicit rules for witness and guard types and for diagnostics as
  prompts; (b) two corrections found by probing the crate: a phantom marker is not a proof, and warning-level guidance never reaches
  an errors-only agent [V, probe]; (c) a file-I/O plan: depend on strict-path inside `plotroom-io` for OS paths and copy its pattern
  lexically for PBO and in-game paths (§6.5, §6.6); (d) typed plugin WIT and SDK, so plugin authors' agents get compile-time
  guidance too (§7). strict-path publishes no measurement of LLM errors, so §9 proposes one.
- **The evidence backs the lever, not the prose.** Most compile errors in LLM code are type errors (94% in a PLDI 2025 study); type
  context plus error rounds lift weak models most (ChatLSP); a proximate type error with its location gives most of the repair gain
  (Krishnamurthi and Flatt); feedback loops shrink the differences between models [V-author]. Repository context files barely help
  and cost over 20% more inference (Gloaguen et al.) [V-author]. So every rule a type or lint can check should become one; prose
  keeps the rationale (§2).
- **Direction 1, know-how in the harness, is a layer order:** wrong actions unrepresentable (typed commands, closed menus,
  witnesses) → facts computed by code → cards → checker diagnostics that state the next action → primer. That is D027's order, and
  strict-path arrived at the same order in another domain. **More freedom for stronger models becomes a typed grant:** a
  `ShapeGrant` minted only from qualification and the effort ceiling lets a strong model take larger steps and pull knowledge on
  top of what code pushes, inside the `Scratch` fork. Admission, validators, files and network never relax (§6.3).
- **Direction 2, what an LSP feed delivers:** OpenCode appends only error-severity diagnostics to an edit result, prints only each
  `message`, keeps at most 20 per file, starts rust-analyzer without options and never sends `didSave`, so on its edit path
  rust-analyzer probably never runs `cargo check` [V source; runtime U]. rust-analyzer folds span-less notes into the message and
  turns `help`s into separate hints [V]. Guidance must therefore sit in a deny-level diagnostic's headline or notes (§4).
- **Channels that work, probed on rustc 1.98.1:** `#[diagnostic::on_unimplemented]` replaces the E0277 headline, but only through a
  function's trait bound; a `#[must_use]` message arrives as a note, and as an error only under `unused_must_use = "deny"`; a clippy
  `disallowed-methods` reason is a note without `replacement` and a droppable `help` with one [V, probe] (§3).
- **Guidance can invite the wrong fix:** rustc says "consider adding one" for an unimplemented trait, offers `let _ =` to silence
  `must_use`, and clippy's `new_without_default` proposes `impl Default` [V, probe]. Rule: guidance never tells the caller to widen a
  guard, and an agent never follows such a suggestion on a guard type (§3.3).
- **Proof by trybuild UI tests**, not `compile_fail` doctests, which stable rustdoc passes on any error (so `AGENTS.md` is right to
  ban them). Each misuse compiles against a committed `.stderr` snapshot, which also regression-tests the guidance text (§5.6).
- **strict-path in Plotroom:** `MIT OR Apache-2.0` fits GPL-3.0-or-later and the cargo-deny allowlist. Proposal: use it only in
  `plotroom-io`, wrapped in Plotroom types; build boundaries only from resolved roots, never from model or plugin strings; use
  `StrictPath` (reject), never `VirtualPath` (clamp), for extraction. It would close a gap the upstream PBO extractor leaves open: a
  link already present inside the destination (§6.5, §6.6).
- **A proposed `AGENTS.md` amendment awaits owner approval** (§8): witness and guard rules, a "Diagnostics as Guidance" section,
  error text for developers only, trybuild negative compile tests and one agent-use rule; 116 lines added, none removed. Ten
  design-gap candidates are listed, not filed (§10).

## 1. What strict-path is

### 1.1 The crate

| Aspect | Fact | Source |
| --- | --- | --- |
| Purpose | An untrusted string becomes a `StrictPath<Marker>` only through `PathBoundary<Marker>::strict_join`, which canonicalizes on disk (symlinks, junctions, 8.3 short names, NTFS alternate data streams, NUL, cycles) and then checks containment. `VirtualRoot`/`VirtualPath` (feature `virtual-path`) clamp an escape instead of rejecting it | README; `strict-path/src/lib.rs` [V] |
| Version, licence | 0.2.3 (2026-05-03), `MIT OR Apache-2.0`, MSRV 1.76, edition 2021; 4,352 downloads when read | crates.io; `strict-path/Cargo.toml` [V] |
| Dependencies | `soft-canonicalize` 0.5.6 (feature `anchored`), which uses `proc-canonicalize` 0.1.3, both `MIT OR Apache-2.0`; `dunce` on Windows | Cargo.toml; crates.io [V] |
| Non-goals | "Not a sandbox or chroot"; not a URL or shell-argument sanitizer; changes on disk between the check and the I/O (TOCTOU) are out of scope | README.md#L89-L97; CHANGELOG.md#L88 [V] |
| Repository | `DK26/strict-path-rs` at `ed6bbeda`; design book on branch `docs` at `c24e97ea` | [V] |

### 1.2 The research story and its method

The design book reports that the first, ergonomic prototype failed with generated code: "The LLM did not use the API correctly at
all! It constantly worked its way around safety features" (`docs` branch, design_decisions.md#L9) [V]. The response was to shrink
the surface: no `as_ref()`, no way to get a `Path` back out, and a method name per kind of path (`strict_join` versus
`virtual_join`), so a bare `.join()` in generated code is a review red flag (development_story.md#L82-L97, "the Three join()
problem") [V]. Release 0.2.0 made three moves: it removed `AsRef<Path>` from boundaries and the lossy string accessors ("One Way");
it added "Systematic `#[must_use]` with descriptive messages across all public APIs to create a compiler-driven feedback loop for AI
agents and LLMs"; and it front-loaded a "Critical mistakes that compile but are WRONG" section into `LLM_CONTEXT.md` "for
small-context LLM visibility" (CHANGELOG.md#L79-L101) [V]. **The reusable method: watch what generated code does, then remove the
surface the model used to escape.** The same project also practised D013's idea (port the reference tests with the behaviour): its
canonicalizer was built by having an agent port Python's pathlib unit tests (development_story.md#L41-L45) [V].

### 1.3 Design patterns

| Pattern | strict-path's form | Source (at `ed6bbeda`) |
| --- | --- | --- |
| Typestate history | Internal `PathHistory<H>` stamps `Raw → (Raw, Canonicalized) → ((Raw, Canonicalized), BoundaryChecked)`; each transition exists only on the previous state; `boundary_check` is "the single gate". Rationale: "booleans can lie" | `strict-path/src/validator/path_history.rs#L32-L42`, `#L158-L180`; docs `type_history_design.md` [V] |
| Witness value | `StrictPath` holds the stamped path plus an `Arc<PathBoundary>`; constructor `pub(crate)` | `strict-path/src/path/strict_path/mod.rs#L42-L52`, `#L99-L108` [V] |
| Domain markers | `StrictPath<UserUploads>`, tuple markers `(Resource, Capability)`, `change_marker()` | README; `strict_path/mod.rs` [V] |
| Guard with one exit | Never `AsRef<Path>`, `Deref` or implicit `From`/`Into`; `interop_path()` returns `&OsStr` (usable by `AsRef<Path>` APIs, but with no `join`/`parent`); named escape hatches `unstrict()`/`unvirtual()` | README.md#L181-L187; `.agents/design-decisions.md#L16-L47` [V] |
| One Way principle | One method per operation; no new public API without maintainer approval; a mandatory API-addition checklist | `.agents/design-decisions.md#L36-L47`, `#L83-L102` [V] |
| Typed ingestion | Command-line and config fields are `PathBoundary<Marker>`, never a raw `PathBuf` | `.agents/design-decisions.md#L118-L132` [V] |
| Built-in I/O | Read, write, rename and directory operations live on the typed value, so callers never need `std::fs` | README [V] |

### 1.4 How it shapes compiler output and comments into prompts

| Channel | Example | Source |
| --- | --- | --- |
| Type mismatch whose marker name is the message | "expected `StrictPath<WritePermission>`, found `StrictPath<ReadOnly>`", shown by `compile_fail` doctests | `strict_path/mod.rs#L270-L281` [V] |
| Missing impls | `std::fs` on a boundary fails with E0277 `AsRef<Path>` | [V, probe] |
| `#[must_use = "next action"]` | A category table (validated types, error enums, validation and consuming methods, security accessors: message; `io::Result` and builder chains: none) and the rule "Messages must be actionable: tell the caller what to do next" | `.agents/coding-standards.md#L5-L22` [V] |
| Error `Display` | Ends with a fix sentence | `strict-path/src/error/mod.rs#L83-L123` [V] |
| Doc comments | "WHY", "WHEN TO USE", "WHEN NOT TO USE" and "SECURITY" blocks; `#[doc(alias = "jailed_path")]`, `"sandbox"` and similar | `strict_path/mod.rs#L44-L47`, `#L203-L217` [V] |
| Example naming | Variables that "scream" their untrusted origin (`untrusted_user_input`, `requested_file`) | `.agents/documentation.md#L28-L33`; `LLM_CONTEXT.md#L13-L17` [V] |
| Agent context files | `llms.txt`, `LLM_CONTEXT.md`, `LLM_CONTEXT_FULL.md`, `context7.json`, `.cursorrules`, a `CLAUDE.md` that points to an `AGENTS.md` hub with `.agents/` satellites; README examples mirrored by tests | repository root; `.agents/documentation.md#L14-L21` [V] |

Not used: `#[diagnostic::on_unimplemented]` (its MSRV 1.76 predates the attribute's stabilisation in 1.78), trybuild snapshots and
clippy `disallowed-methods` [V].

### 1.5 What the study does not show

1. **No measurements.** The repository, design book and changelog contain no LLM error rates, no evaluation suite and no
   before/after counts; the claim is "AI agents use the API correctly when following the documentation" (docs
   design_decisions.md#L78) [V]. Its roughly 40 security test modules, CVE suites, fuzzing and one Kani harness measure path
   security, not model behaviour. Treat the LLM claim as a hypothesis to measure (§9).
2. **Phantom markers are not proofs** [V, probe]. In a downstream crate, `PathBoundary::<UserHome>::try_new_create(..)` and
   `.change_marker::<ReadWrite>()` compile with no `UserHome` or `ReadWrite` value in scope, because both accept any marker
   (`strict-path/src/validator/path_boundary.rs#L164-L219`, `#L281-L288`). The design book's "Markers as Proof ... compiler
   mathematically proves" (docs `best_practices/authorization_architecture.md`) is therefore convention, not compiler enforcement.
   Lesson: a proof is a value with a private constructor, taken by the gated function; a phantom parameter only labels a domain.
3. **Type stamps do not bind to what was checked, and the internal typestate leaks** [V, probe]. `path_history::PathHistory` is
   public (`validator/mod.rs#L1-L2`) although its module doc says it is internal; a downstream crate minted a fully stamped history
   using `/` as the anchor. That is harmless only because `StrictPath::new` is `pub(crate)`. The real guarantee is the stamp *plus*
   the runtime `Arc<PathBoundary>`. Plotroom's `Admitted<T>` already binds `reads` and `revision`, which is the right design.
4. **Holes that compile** [V, probe]. `Path::new(briefing.interop_path()).join("../../escape.txt")` compiles; `LLM_CONTEXT.md#L58-L82`
   admits this hole along with `unstrict()`. `.join()` on a `StrictPath` gives E0599 "no method named `join` found" with no hint
   towards `strict_join`, and `std::fs::read_to_string(&boundary)` gives a generic E0277 that names what is missing, not the fix.
   These holes are guarded by documentation and review only.
5. **`must_use` is weak by default** [V, probe]. Discarding `strict_join(..)` gives two warnings; the custom text is a span-less
   note and rustc adds "help: use `let _ = ...` to ignore the resulting value", so the compiler itself offers the silencing move.
   Without `unused_must_use = "deny"` and clippy `let_underscore_must_use = "deny"`, an agent can satisfy the compiler with
   `let _ =`. The crate's `compile_fail` doctests pass on any compile error, because stable rustdoc does not check error codes.
6. **Runtime errors address the wrong reader.** `StrictPathError`'s `Display` embeds host paths and advice written for a coder, and
   the MCP demo forwards it verbatim to a model (`demos/src/bin/llm/mcp_file_service.rs#L156-L170`), against the design book's own
   anti-pattern. The display sanitizer (`strict-path/src/sanitize.rs#L3-L37`) misses zero-width and Unicode tag characters, which
   Plotroom already renders visibly and lints (validation-and-lints §12; doc 42 MAT14 for tag characters). Smaller: `FromStr` for
   `PathBoundary` creates the directory (a side effect in parsing), `write()` is not atomic, and the design book's examples are
   `rust,no_run` fences, so they are not compiled [V].

## 2. Literature and evidence

| Study | Setting | Result [V-author] | What Plotroom takes |
| --- | --- | --- | --- |
| Mündler, He, Wang, Sen, Song, Vechev, PLDI 2025, type-constrained decoding | TypeScript, open-weight models | Syntax errors are about 6% of compile errors; about 94% are type errors. Type-constrained decoding more than halves compile errors and raises functional correctness at all sizes | Type errors are where the gain is. Constrained decoding needs logit access, so it applies only to local backends |
| Agrawal et al., NeurIPS 2023, monitor-guided decoding | Static analysis over LSP as logit masks | Compile rate +18.5% to +24.7% relative; SantaCoder-1.1B with monitors beats text-davinci-003; monitors include typestate and API-protocol checks for Rust | A language service can steer a small model during generation |
| Blinn, Li, Kim, Omar, OOPSLA 2024 (ChatLSP) | Typed holes (Hazel) and TypeScript | Approximate, read from figures: Hazel with GPT-4 about 5% → 20% (type definitions) → 60% (plus headers) → 90% (plus error rounds). Type definitions were the most useful single context | Five methods (tutorial, expected type, relevant types, relevant headers, error report) map onto a Teller card API (§4.4) |
| Krishnamurthi, Flatt, 2026, "Type-Error Ablation and AI Coding Agents" | 2,400 trials, four reporting modes | qwen2.5-coder:14b: about 24–41% (tests only) → 41–63% (full type errors); most of the gain came from untyped → minimal and minimal → proximate (one expression plus its location); 97.9% of type-fixed programs passed semantic tests; claude-haiku-4.5 scored 87–99% in every mode | Weak models need the conflicting facts plus a precise location; more verbosity is wasted tokens (§6.9) |
| Deligiannis et al., ICSE 2025, RustAssistant | Real Rust compile errors and clippy findings | About 74% fix rate; prompt format and error grouping dominate (with GPT-3.5, 10.7% basic → 73.7% full; without grouping 91.5% → 14.0% at error level) | Group related findings; localised, line-prefixed context (§6.9) |
| Weiss et al., arXiv 2512.02567 | C-to-Rust translation | "When the translation system uses feedback loops the differences across models diminish" | Direction 1: put the know-how in loops code owns |
| Mündler-Sasahara et al., arXiv 2607.13921, "Generative Compilation" | Repository-level Rust | A "sealor" closes a partial program so the standard compiler can check it mid-generation; fewer non-compiling outputs, better correctness (abstract gives no numbers) | Candidate for Teller: check a streaming script early (§6.9) |
| Biagiola et al., arXiv 2606.21619 | Constrained decoding with incomplete constrainers | Up to 97% lower functional correctness when the constrainer rejects valid programs; more timeouts and out-of-tokens | Every hard constraint must accept all the engine can run (§6.9) |
| Gloaguen, Mündler, Müller, Raychev, Vechev, arXiv 2602.11988 | Repository context files for coding agents | Context files "do not generally improve task success rates" and add over 20% inference cost; developer-written about +4%, generated about −3%; useful for non-standard practices | Turn checkable rules into types and lints; keep prose for rationale (§5) |
| Shepard, Albrecht, arXiv 2606.20512 | Tuned against static guidance | 33.0% versus 28.3% (static) and 25.5% (none), mostly from finding the right files | Guidance helps where it routes, not where it lectures |
| Xu, arXiv 2608.13568 | LSP tools for Claude Opus 4.8, Sonnet 4.6, Haiku 4.5 | Models used grep for localisation (0–6% LSP use); LSP cost +6% to +118% tokens there; the author recommends an "adaptive router keyed on task class, model capability, and lexical noise" | Push cards to weak models; offer pulled lookups to strong ones (§6.3) |
| ImpossibleBench, arXiv 2510.20270 | Tasks whose tests contradict the spec | GPT-5 passed the one-off impossible variant 76% of the time by altering tests or exploiting side channels | A free, strong model weakens checks it can reach: no grant ever covers validators or admission (§6.3) |

**Doc comments and API knowledge.** Retrieved documentation helps with unseen APIs (DocPrompting, ICLR 2023), badly chosen
documentation hurts (CloudAPIBench), and usage examples are the strongest single component (NovelAPIBench, arXiv 2606.03657)
[V-author]. Misleading comments cut fault-localisation accuracy to about 28.7% (arXiv 2504.04372), and rules files have been used
as an injection vector with hidden Unicode (Pillar Security, 2025) [V-author]. So: runnable examples (already mandatory) are the
most valuable comment form, comments are reviewed like code, and a hidden-character check covers tracked files.
**API drift.** Models reach for deprecated APIs (37.4% of GPT-3.5's calls in one Python study, ICSE 2025) and do worse on APIs newer
than their cutoff (RustEvo², arXiv 2503.16922) [V-author]; a `#[deprecated(note)]` at deny level is a cheap in-loop signal for
Plotroom's own evolving APIs. **Crate hallucination:** 22.23% of Rust crate recommendations were hallucinated, most within five
edits of a real name (arXiv 2606.08444) [V-author]; lockfile, cargo-deny and the layer check catch these, prompts do not.
**Capabilities as values.** CaMeL (arXiv 2503.18813), FIDES (arXiv 2505.23643), Progent (arXiv 2504.11703) and the design-pattern
catalogue of arXiv 2506.08837 enforce provenance labels and privileges deterministically outside the model [V-author]. Plotroom's
`Proposal { trust, origin }`, `Admitted<T>` and `UserIntent` are the Rust-native form of the same idea.
**Do not overclaim language-level effects.** Benchmark rankings of Rust against other languages disagree (SWE-bench Multilingual:
Rust highest; Multi-SWE-bench: Rust far below Python) and are confounded by task difficulty [V-author]. The consistent evidence is
inside the repair loop.

## 3. Rust's guidance channels and where their text lands

### 3.1 Channel table

| Channel | Stable | Where rustc puts the text | After rust-analyzer | Reaches an errors-only feed? |
| --- | --- | --- | --- | --- |
| `#[diagnostic::on_unimplemented(message, label, note)]` on a trait, bound on a **function** | 1.78 | `message` replaces the E0277 headline; `note` is a span-less note | Note folded into the message; the label is dropped once a note exists | Yes |
| Same trait, bound on an **impl block** (a typestate gate) | 1.78 | Generic E0599 "trait bounds were not satisfied"; custom text unused | — | No guidance |
| Typestate method missing on the current state | — | E0599 "no method named `build` found for `CoreBuilder<Missing>`" plus a note "the method was found for `CoreBuilder<Ready>`" | Note folded | Where, not how |
| `#[must_use = "…"]` | long stable | Warning; the message is a span-less note; a spanned help offers `let _ =` | Warning severity | Only with `unused_must_use = "deny"`; the help is dropped |
| `#[deprecated(note = "…")]` | long stable | Warning headline includes the note | Warning severity | Only with `deprecated = "deny"` |
| clippy `disallowed-methods`/`-types` `reason`, no `replacement` | clippy | Span-less note | Folded | Yes, at deny |
| Same with `replacement` | clippy | The reason becomes a spanned help with a suggestion | Separate hint | No |
| `#[diagnostic::do_not_recommend]` on an impl | 1.85 | Hides a blanket impl from suggestions | — | Removes misleading text |
| `#[expect(lint, reason = "…")]` | 1.81 | Warns (`unfulfilled_lint_expectations`) when a suppression goes stale | — | — |
| `#[diagnostic::on_move]`, `on_unknown` | unstable in 2026 | — | — | Watch: `on_move` would suit single-use witnesses |

Sources: the Rust Reference's diagnostics chapter; release posts for 1.78, 1.81 and 1.85; clippy's `DisallowedPath::diag_amendment`
(`clippy_config/src/types.rs`, read 2026-09-28); rust-analyzer as in §4.2 [V]. Rows marked by behaviour were confirmed in the probe
[V, probe].

### 3.2 What the probe printed

- On a function bound: error E0277 "the core is missing its validator family (state `Missing`)" with the note "call
  `.validators(..)` before `.build()`; every check family must be supplied". The same bound on the impl printed only "the method
  `build` exists for struct `CoreBuilder2<Missing>`, but its trait bounds were not satisfied" [V, probe].
- `must_use` at deny: the error "unused `admission::Admitted` that must be used", the note "an `Admitted<T>` is proof that checks
  passed; pass it to `commit(..)` or the edit is lost", then the help "use `let _ = ...` to ignore the resulting value" [V, probe].
- clippy with a reason only: the note "Wilco crates never spawn processes (AGENTS.md product scope); ask the user to launch Preview
  through plotroom-preview instead". With a replacement: the help "file writes live only in plotroom-io:
  `plotroom_io::write_atomic`", a spanned help that rust-analyzer turns into a separate hint [V, probe].
- `indexing_slicing = "deny"` flagged `v[0]` on a `Vec` but not `m[k]` on a `HashMap<String, u32>` [V, probe]. clippy lints an
  indexed type only if its inherent `get` returns `Option` of the index type or a type parameter (`indexing_slicing.rs#L262-L288`
  at clippy `57785c2b`, with a FIXME). This answers crate-map §2.4's [U]: a small custom check is needed.

### 3.3 Guidance that invites the wrong fix

Three suggestions from the toolchain would weaken a guard if an agent followed them: rustc's "help: this trait has no
implementations, consider adding one" on a trap trait; rustc's `let _ = ...` on a discarded witness; and clippy's
`new_without_default` proposing `impl Default` for a type with a `new()` [V, probe]. Our own first draft of a probe message made the
same mistake: it told the caller to "register it in the CommandSpec registry with `Reach::AgentCallable`", which widens what Wilco
may call. **Rule: guidance never tells the caller to add an impl, make a field public, grant a capability or silence a lint;
needing more capability is a design decision.** A trap trait (an unimplementable bound that exists only to carry a message) is
therefore safe only where the caller cannot implement it: the plugin SDK (§7.2), not inside the workspace.

## 4. How guidance reaches an agent: the LSP and terminal feeds (direction 2)

### 4.1 OpenCode's path

- After `edit` and `write`, OpenCode touches the file, waits for diagnostics and appends a block headed "LSP errors detected in this
  file, please fix" (`packages/opencode/src/tool/edit.ts#L196-L201`); `write` also reports up to 5 other files
  (`tool/write.ts#L18`, `#L76-L90`) [V, at `03e67171`].
- `Diagnostic.report` keeps only severity 1, at most 20 per file, and prints `SEVERITY [line:col] message`
  (`src/lsp/diagnostic.ts#L3-L27`) [V]. Warnings, hints, related information, codes and rust-analyzer's `data.rendered` are dropped.
- Rust support spawns `rust-analyzer` with no initialisation options (`src/lsp/server.ts#L922-L931`), so its check command is the
  default `cargo check`, not clippy [V].
- File sync sends `workspace/didChangeWatchedFiles` and `textDocument/didChange`, never `didSave` (`src/lsp/client.ts#L554-L620`) [V].
  rust-analyzer starts its cargo check on save; on watched-file changes only for files outside the workspace roots
  (`handlers/notification.rs#L303-L326` at `03fcb772`) [V]. So on OpenCode's edit path the model probably sees only rust-analyzer's
  own native diagnostics, not rustc or clippy guidance [I from source; runtime U].

### 4.2 rust-analyzer's mapping

`flycheck_to_proto.rs` (at `03fcb772`): a child diagnostic without a primary span becomes a line appended to the parent message
(`#L188-L192`, `#L332-L346`); once any such line exists, the primary span label is not appended (`#L341-L343`, `#L375-L376`);
spanned children (helps with suggestions) become related information plus separate `Hint` diagnostics (`#L461-L484`); the full
rustc text is kept in `data.rendered` (`#L456`) [V].

### 4.3 Consequences for Plotroom's coding agents

1. Warnings never reach an errors-only agent. CI already fails on warnings (`-D warnings`), so raising guidance lints to `deny` in
   `[workspace.lints]` changes nothing about what can merge; it changes what an agent sees while editing [I].
2. Guidance goes in the headline or a span-less note, never only in a label or a help.
3. clippy guidance reaches an LSP-fed agent only if rust-analyzer runs clippy; ship editor configuration that sets
   `check.command = "clippy"` (whether a workspace `rust-analyzer.toml` is honoured by each client is [U]).
4. A shell-driven agent sees everything, including the unhelpful helps of §3.3, so both feeds must be designed for.
5. A test can check the feed: run `cargo check --message-format=json` over the UI-test cases and assert that each guidance sentence
   sits in a `message` or a span-less child (§5.6).

### 4.4 Consequences for Teller and Wilco

- Wilco gets Teller's findings in process, not through LSP, so Plotroom owns that transport: code, message, expected and found,
  location, allowed values and the next action all survive (doc 23 §13.4; agent-runtime §6).
- The optional Teller LSP binary (validation-and-lints §9) should assume errors-only, message-only clients: the rule and the fix go
  in `message`, anything a model must act on uses error severity, and the rich JSON rides in `data`.
- External agents through the outbound MCP server get typed results: MCP 2025-06-18 adds `outputSchema` and `structuredContent`;
  when a tool declares an output schema, servers MUST return structured results that conform to it and clients SHOULD validate them
  [V].
- ChatLSP's five methods map onto a Teller card API: tutorial → primer section; expected type → the type at the cursor or hole;
  relevant types → catalog classes; relevant headers → command signatures for the profile; error report → diagnostics [I].
- Xu's result argues against pushing language-service lookups to strong models for navigation: offer them as pulled tools and keep
  code-selected cards for every model, since pull never replaces push (D027; §6.3; doc 63 §3.2 rule 1; doc 61 §4.10).

## 5. Application 1: Plotroom's Rust conventions for coding agents

### 5.1 What `AGENTS.md` already covers

Plotroom's `AGENTS.md` already mirrors most of strict-path's contributor rules: "Maintaining This File", safe indexing, no
`unwrap`, lifetime naming, the 600-line ceiling, what/why/how comments, the evidence rule, typestate, private constructors and enum
state machines [V]. Net new from this study: witness and guard rules, diagnostics as guidance, error text for its reader, and
trybuild negative tests. §8 lists them as a proposed amendment.

### 5.2 Witness and guard types

1. A proof is a value with a private constructor in the module that runs the check; gated code takes it. Phantom parameters only
   label domains (§1.5 item 2).
2. Bind the witness to what it was checked against (revision, root, grant, scope), as `Admitted<T>` binds `reads` (§1.5 item 3).
3. Never `Default`, `Deserialize`, `From<Inner>`, `DerefMut` or public fields. `Deref`/`AsRef` only when no workspace API accepts the
   inner type unchecked (strict-path's reason: `&Path` hands `.join()` to `std::fs`). One named exit, one named escape hatch.
4. Name operations after the kind of value they act on (`mission_join`, `vfs_join`, `admit_batch`), so a bare `join` stands out.
5. A change to a guard's public surface is a design decision with a design-gap entry and a UI test. An optional public-API snapshot
   (for example `cargo-public-api`) on the guard crates would make such changes visible in review [I].

### 5.3 Diagnostics as prompts

- **`#[must_use]` table** (strict-path's, adapted): witness and guard types, validation functions, consuming functions and
  security accessors carry a message that states the next action; `io::Result`, `Result<(), _>` and builder chains do not.
- **`on_unimplemented`** on every sealed or capability trait (`Checkable`, `AgentCallable`, `CanRead<S>`); guidance-bearing bounds
  on functions such as `admission::check<T: Checkable>(..)`; `do_not_recommend` on blanket impls.
- **Lint levels:** `unused_must_use` and `deprecated` at deny; clippy `let_underscore_must_use` and `allow_attributes_without_reason`
  at deny; suppressions as `#[expect(lint, reason = "…")]`, or as `#[allow(lint, reason = "…")]` where a lint fires only on some
  targets or feature sets (an unfulfilled `expect` warns, which fails the other targets under `-D warnings`), and capability lints only
  inside the confining crates of
  crate-map §2.3. Every `disallowed-*` entry has an instruction-style `reason` and no `replacement` unless the call shape is
  identical.
- **Prose rules that can become lints** (lint names verified at clippy `57785c2b`) [V]:

| `AGENTS.md` rule | Lint |
| --- | --- |
| Meaningful lifetime names | `single_char_lifetime_names` (restriction) |
| Exhaustive matching | `wildcard_enum_match_arm` (restriction) |
| Enums over boolean flags | `fn_params_excessive_bools`, `struct_excessive_bools` (pedantic) |
| Documented suppressions | `allow_attributes_without_reason`; `#[expect]` |
| Doc comments on public items | rustc `missing_docs`; clippy `missing_errors_doc`, `missing_panics_doc` (pedantic) |
| `must_use` discipline | `let_underscore_must_use` (restriction), `return_self_not_must_use` (pedantic) |
| Soft size ceiling | `too_many_lines` (pedantic, with a threshold) |
| No indexing on maps | Not covered by `indexing_slicing` (§3.2): a custom check |

clippy's test allowances (`allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-indexing-slicing-in-tests`) reportedly do not
cover integration tests, examples or benches (clippy issue #13981) [V-author]; those need `cfg_attr` or `expect` with a reason.

### 5.4 Doc comments as instructions

Keep `AGENTS.md`'s what/why/how. For guard types add "When to use", "When not to use" and "Security" paragraphs and
`#[doc(alias)]` for the names an agent will search for (`sandbox`, `jail`, `validated path`). Name untrusted values by provenance
(`model_reply`, `plugin_output`, `requested_mission_name`). Runnable doctests are the highest-value comment form (§2); prose
comments are reviewed like code, because a wrong comment misleads more than a missing one.

### 5.5 Compile-error-first API design as a standing process

1. When review or an agent run shows code that compiles but bypasses a guard, **close the escape**: remove or rename the surface
   that allowed it, and add a UI test for the bypass. A new comment is not a fix.
2. Start a new guard API from its misuse cases: write the UI tests (the wrong calls and the messages they should produce), then the
   API. This is `AGENTS.md`'s red-green order applied to compile errors.
3. Prefer "no such method" plus an instruction-bearing function bound over a runtime check for anything a type can express.

### 5.6 Tests that prove it

- **trybuild UI tests** per guard crate, one case per misuse, each with a committed `.stderr` snapshot and a leading comment stating
  the rule. Stable rustdoc never checks the error code in `compile_fail,E0xxx` (checking is nightly-only, and the rustdoc book says
  a stable sample with an error code is read as plain text), so on stable such a doctest proves at most that some error occurred; trybuild
  compares the exact output, so one test proves the misuse fails *and* the message is the intended prompt, and it fails if an agent
  weakens the guard (for example by making `Admitted`'s fields public) [V: trybuild docs; rustdoc unstable-features page].
- UI tests run on one CI job with a pinned toolchain, because compiler text changes between releases; snapshots change only with a
  toolchain bump or a reviewed guidance change.
- **Feed test:** the §4.3 item 5 JSON check over the same cases.
- **Lint-table test:** an `xtask` check that the workspace lint table contains the deny list and that every `disallowed-*` entry has a
  non-empty `reason`.

## 6. Application 2: Wilco's typed action layer

### 6.1 What the design already has

| strict-path pattern | Plotroom counterpart | Gap this study finds |
| --- | --- | --- |
| Private-constructor witness | `Admitted<T>`, built only by the admission module (commands-undo-history §4.1) | Trait policy: never `Deserialize` (§6.2) |
| Typestate history | Typestate `CoreBuilder` that cannot `build()` without every check family (§4.2) | Guidance text for the wrong state (§3.1) |
| Unforgeable capability | `UserIntent(GestureToken)` behind a sealed input source plus `xtask layers` (§4.4) | `must_use` and UI tests |
| Guard with no mutable escape | `Guarded<T>`: `Deref`, never `DerefMut` (core-document-model §5.1) | A test that no commit or save API accepts a bare `T` |
| TOCTOU declared out of scope | Read-set freshness re-check at commit (DG011 option C) | None: Plotroom goes further |
| `StrictPath` versus `VirtualPath` | Commit boundary versus the `Scratch` fork | Use it for freedom (§6.3) |

### 6.2 Witness policy

- `Admitted<T>`, `UserIntent`, `EgressGrant` and any `ShapeGrant` never implement `Deserialize`, `Default` or `Clone` where cloning
  would let one approval act twice. Journal resume data (DG017), test cassettes (doc 38 §6.4: "Cassettes hold raw replies, so
  admission, repair and checks run for real") and MCP input re-enter as `Proposal<T>` and are admitted again.
- `#[must_use = "an Admitted batch does nothing until committed: pass it to the session's commit, or drop it to discard"]`.
- Do not copy strict-path's public nested-tuple history: errors would print `((Proposal, Planned), Admitted)`. Use named states, or
  at most one phantom scope if two admission levels (ghost preview versus commit) really exist.

### 6.3 Freedom for stronger models as a typed grant (direction 1)

"Effective shape = min(effort ceiling, the shapes qualified for that decision)" (agent-runtime §7) is today a rule in prose. As a
type [I]:

```rust
// Proposal-only [I]. Minted only by the qualification module; the phantom `S` labels, the private fields prove.
pub struct ShapeGrant<S: Shape> {
    setup: SetupId, kind: DecisionKind, record: QualificationRef, ceiling: Effort, _s: PhantomData<S>,
}
pub fn run_compose(step: &ComposeStep, grant: ShapeGrant<Compose>, snap: &Snapshot)
    -> Result<Proposal<Batch>, StepError>;
```

- **What a wider grant allows:** larger Compose steps, Draft of script text, many ops per proposal in `Scratch`, fewer decomposition
  facets, and knowledge *pulled* through Teller lookups in addition to the cards code pushes (Xu's adaptive routing; pull never
  replaces push, doc 63 §3.2 rule 1). strict-path's two
  modes map onto this: `VirtualPath`, "freedom of operation under complete isolation" (README.md#L83-L87), is the `Scratch` fork;
  `StrictPath`, detect and reject, is the commit boundary.
- **What no grant allows:** fewer checks at admission, self-admission, writes to validators, cards or the knowledge the checks use,
  file or network capability, or a change of autonomy (the user's dial, D024: "Effort never changes the checks"). ImpossibleBench
  shows why: a capable model with access to its checks weakens them.
- **Glass box:** the journal records which grant ran each step (D025), so the choice is visible and replayable.
- An alternative is a broader `AutonomyGrant` (step size, allowed kinds, approval threshold, repair budget), after Feng et al.'s
  "autonomy certificates" (arXiv 2506.12469). D024 keeps effort, autonomy and role binding as separate dials, so this doc keeps
  autonomy out of the grant; the choice is a design-gap candidate (§10 item 7).
- **Same witness as doc 63.** Doc 63 §9.2 sketches this grant as `Grant<L: Level>` over its freedom levels FR0–FR8, with an
  `on_unimplemented` bound on the executor; `ShapeGrant<S: Shape>` here is the same idea over today's four shapes. One name and one
  level vocabulary should be chosen together (this doc's §10 item 7; doc 63 §13 items 1 and 7).

### 6.4 Typestate at seams, enums in storage

A persisted workflow run is an enum state machine with a journal (D025; `AGENTS.md` already prefers an internal enum where one
concrete type is required). Typestate belongs only at in-process seams: `Proposal → Admitted → GroupId`, `CoreBuilder`, egress card
→ `EgressGrant`, and a Preview launch that requires `UserIntent`.

### 6.5 OS paths: strict-path in `plotroom-io` (recommendation)

**Licence.** `MIT OR Apache-2.0` (crate and dependencies) is compatible with GPL-3.0-or-later (D001) and with cargo-deny's allowlist
(crate-map §2.5). As a dependency it needs its notices in the release's generated third-party notices (doc 02); ported test
corpora need provenance records (DG018) [I; not legal advice].
**Recommendation [I]:** depend on strict-path (pinned, 0.2.x is pre-1.0) **only in `plotroom-io`**, behind Plotroom wrapper types,
so markers, guidance text and the dependency stay swappable and confined. Its `try_new_create` and `write` perform file writes,
which crate-map §2.3 confines to `plotroom-io`; cargo-deny per-layer bans enforce that.

- **Boundaries come only from resolved roots:** discovered install paths, the user's file-dialog picks (`Reach::UserOnly`), app-data
  directories. Model and plugin strings supply only segments, and segments go through `strict_join`.
- **Markers by resource:** `MissionFolder`, `CampaignFolder`, `UserProfileMissions`, `ModRoot`, `ExtractTarget`, `AppData`,
  `JournalStore`, `PluginAssets` (doc 22's hostile asset names such as `../`).
- **Reject, never clamp**, for extraction and imports: `StrictPath`, never `VirtualPath` (strict-path's own `AGENTS.md#L72`:
  "VirtualPath for archive extraction — hides attacks"), matching doc 27 §4.10.
- **Call constructors by name**, never `.parse()`, because `FromStr` creates directories. **Atomic save** is `strict_join` of a
  temporary name, write and sync, then a rename inside the boundary; plain `write()` is not atomic.
- **Mod roots:** mod managers often link mod folders elsewhere [I]. One boundary per canonicalized mod root keeps such roots working
  while links *inside* a mod that point out are still rejected (doc 27: "Do not follow symlinks out of a scan root").

### 6.6 PBO extraction and in-game paths

**Upstream's lexical guard.** `unpack_to_dir` (BohemiaInteractive/CWR@ffc61838b7:`mserver/Archive/src/pbo.rs#L261-L285`) rejects
absolute names, any component other than a normal one or `.`, and a first `/`-segment ending in `:`, then calls `dest.join` and
`fs::write`; its test
(`#L458-L472`) covers `../escape.bin`, `/absolute.bin` and `c:/windows.bin` [V]. The porting CSV lists it as `port-now`, target
`formats-pbo`. Not covered [I]: (1) a link or junction already inside the destination: normal components pass and `fs::write`
follows the link, the class strict-path's CVE-2025-11001 suite tests; (2) backslash names that bypass the reader: the reader maps
`\` to `/` and lowercases (`normalize_name`, `#L289-L291`, applied at `#L326`), so `..\x` read from a file is caught, but the test
sets `entries[0].name` directly, and on Linux an unmapped `..\x` is one normal component, so the ported test should also feed a
backslash name through the reader; (3) alternate data streams (`name:stream`) below the first segment;
(4) Windows reserved device names (`con.txt`, `nul`), where strict-path's behaviour is [U].
**Plan [I]:** port the upstream test with its CSV row, add these cases, then extract in two stages: the lexical reject first (engine-
parity diagnostics and doc 24's L2 rule), then `ExtractTarget` `strict_join` for on-disk resolution.
**In-game paths: copy the pattern, not the crate.** Paths inside PBOs, `#include` targets and script file names are engine-virtual:
case-insensitive, backslash-separated, prefixed by the PBO stem, collapsed as the engine does. There is no disk to canonicalize. In
`plotroom-vfs`, a lexical `VfsPath` with named states (raw → normalized → confined to a bank prefix), a private constructor, no
`Deref` to `str`, rejection on escape and one `vfs_join`. Property tests prove the collapse never yields a path above the root.
strict-path's adversarial inputs (`security_traversal.rs`, `security_input_encoding.rs`, `advanced_security_ntfs.rs`,
`windows_junction_prefix.rs`) can seed fixtures for both layers, with DG018 records.

### 6.7 Network egress guard

`EgressGrant` in `plotroom-net` (crate-map §2.3; extensibility §8) takes the same shape [I]: only Settings, the plugin manager and
the Model Manager mint the grant, after `UserIntent`. URLs are built only by `AllowedOrigin::join_path(untrusted_segment) ->
Result<CheckedUrl<Endpoint>, Error>`, the network analogue of `strict_join`, which rejects off-origin results, off-origin redirects
and IPv4-mapped IPv6 (doc 22 §3.2). No `From<String>`, no `Deref<Target = Url>`; the HTTP client is reachable only through
`&CheckedUrl` plus the grant. `disallowed-types` entries for HTTP clients outside `plotroom-net` carry instruction-style reasons.

### 6.8 Model-facing text and developer docs

"Tool schemas and descriptions come from `///` docs via `schemars`" (commands-undo-history §3), and `schemars` uses the whole doc
comment as `description`. `AGENTS.md` asks that same `///` to carry the developer's what, why and invariants. That text would leak
Rust identifiers and rationale into cache-stable tool prompts (D026) and address the wrong reader, the mistake of §1.5 item 6.
Proposal [I]: author model-facing descriptions in the knowledge store keyed by `CommandId` (D027, DG032; cards of at most 150 words
in product vocabulary) or through `#[schemars(description = "…")]`, with a CI check for Rust identifiers and host paths. strict-path
made the same split with separate files for users (`LLM_CONTEXT*.md`) and contributors (`AGENTS.md`, `.agents/`).

### 6.9 Validator and Teller messages as prompts

- **Every finding ends with the next action**, in product vocabulary; `Rejection` already carries allowed values and a `RepairHint`
  (commands-undo-history §4.1).
- **Proximate beats verbose:** the conflicting facts plus the field path, not a derivation (Krishnamurthi and Flatt).
- **Retryable versus terminal** as enum variants, as Pydantic AI separates `ModelRetry` from terminal tool failures [V]; the repair
  prompt is the validator's typed message, never model-written prose (TypeChat's "schema engineering").
- **Tension:** agent-runtime §6 repairs "one finding per turn"; RustAssistant's ablation found grouping related errors decisive.
  Proposal: one *root* per turn, with the findings that share its entity or field grouped (§10 item 8).
- **Completeness of hard constraints:** any grammar or strict schema for local models must accept everything the engine can run for
  the target profile; plausibility stays advisory (`AGENTS.md` realism rule; Biagiola et al.).
- **Teller's "compiles but wrong" list** (`arma_ism`, doc 23 §13.4) and the primer's traps come from one fact store, as
  strict-path's front-loaded mistakes list does for its users. A sealed partial-script check while a cloud model streams is a
  candidate after v1 (Generative Compilation).

### 6.10 Tests

UI tests: building `Admitted { .. }` outside admission (E0451); passing a `Proposal` to commit; `serde_json::from_str::<Admitted<_>>`
(E0277); constructing `UserIntent` outside `plotroom-session`; `build()` on an incomplete `CoreBuilder`; forging a `ShapeGrant`;
passing a bare document value to a save or commit API that expects the guarded store. Runtime and property tests: a replayed
journal re-admits every step; a changed read entity re-verifies (DG011); the path adversarial corpus on the three-OS matrix;
`VfsPath` never escapes; the egress stub-server suite (testing-strategy §12).

## 7. Application 3: the plugin SDK

### 7.1 The WIT layer

Doc 22's sketch is stringly typed: `query(scope: string, filter: json)`, `invoke(name: string, input: json)`,
`host-error::invalid(string)` (doc 22 §7.3) [V]. Proposal [I], arguing doc 22's open question 2 towards typed records for the stable
core: typed WIT enums for read scopes and proposal kinds; component-model `resource` handles as capability tokens (WASI's design
principles call handles unforgeable; only the implementor constructs them), for example a host-issued `mission-view` per grant and a
`proposal-draft` resource with typed `add-*` methods, so a guest can only express kinds its grant allows and the host refuses at the
call, not at the end; and a structured `host-error` (`denied { scope }`, `invalid { pointer, expected, allowed }`) mirroring
`Rejection` and Teller findings. JSON stays for large, evolving payloads behind typed SDK builders. The package is
`plotroom:plugin@1` (extensibility §6).

### 7.2 The Rust guest SDK

`plotroom-plugin-sdk` over wit-bindgen [I]: newtypes; a typestate builder (`ProposalDraft<Empty> → ProposalDraft<WithCommands> →
build()`); instruction-bearing `must_use`; sealed traits with `on_unimplemented`. **A compile-time grant from the manifest:** a
macro reads `plugin.toml` and implements `CanRead<Triggers>` for the plugin's `Grant` through a hidden sealed path, so using an
undeclared scope fails with "add `triggers` to `reads` in plugin.toml (the user will review the new grant)". The §3.3 trap is safe
here because the plugin crate cannot implement the sealed trait. These checks help honest authors only: a guest can call raw imports
and bypass the SDK, so the host keeps enforcing grants at run time (strict-path's own "not a sandbox" caveat).

### 7.3 Docs for plugin authors' agents

Ship with the SDK and the plugin scaffold: an `llms.txt`; a short `LLM_CONTEXT.md` that front-loads the "compiles but wrong" cases
(hand-built command JSON, mission text copied into script fields, asset names containing `../`); an `AGENTS.md` template; README
examples mirrored by test-kit tests. Licence per D031: GPL-3.0-or-later for now.

### 7.4 Tests

trybuild cases in the SDK (undeclared scope, proposal kind outside the grant, building an empty draft); test-kit host tests where an
adversarial component calls raw imports outside its grant and is denied at run time.

## 8. Proposed `AGENTS.md` amendment (proposed, awaiting owner approval)

A unified diff was prepared outside the tree. It applies cleanly to `AGENTS.md` as of 2026-09-28, adds 116 lines and removes none
(114 before the review edits recorded in the verification notes).
It is not applied; the owner decides. Written in `AGENTS.md`'s own style: general, context-free, no references to this study.

| Where | Rule added | Evidence |
| --- | --- | --- |
| "Error Design" | `Display` ends with the next action; `Display` text is for developers and logs, never forwarded verbatim to a model, plugin or external agent; untrusted text in errors goes through one shared sanitizer | §1.5 item 6; §6.9 |
| "Type Safety" | Witness and guard types: private-constructor proofs, phantom parameters only label, bind to what was checked, forbidden traits, the `Deref` rule, one named exit and escape hatch, kind-named operations, surface changes need a design-gap request and a UI test. "Typestate at seams, enums in storage" | §1.5 items 2–3; §5.2; §6.4 |
| New "Diagnostics as Guidance" | Compile errors beat comments; guidance states the next action; guidance never widens a guard; the `must_use` table; `on_unimplemented` on function bounds and `do_not_recommend`; guidance survives every feed (`unused_must_use`, `deprecated`, `let_underscore_must_use` at deny; clippy reasons without `replacement`); suppressions with `expect` and a reason; provenance names; guard doc sections; close the escape | §3; §4.3; §5.3–§5.5 |
| "Testing Standards", new "Negative Compile Tests" | Keep the `compile_fail` ban and say why; trybuild UI tests with `.stderr` snapshots, one per misuse, pinned toolchain, every guard property covered | §5.6 |
| "LLM / Agent Use Rules" | Follow compiler and lint text on guard types only when it names a sanctioned API; never add the suggested impl, public field, `Default` or `#[allow]`; file a design-gap request instead | §3.3 |

Companion changes it implies, not in the diff: crate-map §2.4's lint table and `clippy.toml` reasons; testing-strategy §14 (a UI-test
gate) and §16 item 1 (answered, §3.2); core-document-model §5.1's "Module privacy, not a doctest" gains "plus a trybuild UI test".

## 9. Proposed experiments (research only, under `tools/`)

### 9.1 Coding-agent misuse evaluation

strict-path never measured its claim; Plotroom can. About 20 small tasks on a scaffold crate with Plotroom-like guards, each
tempting a bypass: write a file directly, join an untrusted segment, commit without admission, construct `UserIntent`, call HTTP
outside the network crate, deserialize an `Admitted`. **Arms:** A = types and docs; B = A plus the witness rules; C = B plus the
deny-level guidance lints, `on_unimplemented` and clippy reasons. **Feeds:** raw cargo output in a shell, and an OpenCode-style
errors-only LSP feed. **Metrics:** bypass rate (compiles with a violation), silencing rate (`let _`, `#[allow]`, an added impl),
turns to green, tokens. **Models:** one small local coder and one cloud model. The results decide which parts of §8 are kept.
The tool evaluates Plotroom's development process, not a product feature, so it sits outside Wilco's product scope.

### 9.2 Validator message detail for Wilco

A pre-registered ablation on doc 44's suites, after Krishnamurthi and Flatt: finding detail (none, minimal, proximate, full) ×
model tier, measuring repair success and tokens; plus grouped against single-finding repair turns (§6.9).

## 10. Design-gap candidates (listed, not filed)

1. **Trait and constructor policy for witness types** (no `Deserialize`, `Default`, `From`, `DerefMut`; the `Deref` rule); could
   fold into DG011.
2. **Model-facing text versus developer doc comments** (§6.8): where tool descriptions live, and the CI check.
3. **Diagnostics as guidance** (§8): trybuild instead of `compile_fail`, deny-level guidance lints, clippy reasons, rust-analyzer
   running clippy.
4. **A diagnostic transport contract** between Teller, Wilco, external agents and coding agents: which fields must survive
   (message, notes, code, location, next action, rendered).
5. **The OS-path guard versus the lexical `VfsPath`**, and whether `plotroom-io` depends on strict-path (§6.5, §6.6).
6. **Typed plugin WIT and SDK with manifest-derived compile-time grants** (doc 22 open question 2).
7. **`ShapeGrant` as the typed freedom dial**, or a broader grant that also carries autonomy (§6.3; D024); one candidate with doc
   63 §13 item 7 (its `Grant<L>`).
8. **Repair granularity:** one finding per turn or one root with its grouped findings (§6.9).
9. **Map indexing:** `indexing_slicing` misses `HashMap` indexing; which custom check (crate-map §2.4).
10. **The `CheckedUrl` egress shape** in `plotroom-net` (§6.7).

## Open questions

1. **Owner:** approve the §8 amendment in full, in part, or after §9.1's results? [U]
2. **Owner:** depend on strict-path (the owner's own crate) in `plotroom-io`, or copy the pattern only? Either works technically;
   depending on it brings its Windows and CVE test suites [I].
3. **Technical:** does OpenCode's edit path ever trigger a cargo check at run time, and does each client honour a workspace
   `rust-analyzer.toml`? [U]
4. **Technical:** does strict-path reject Windows reserved device names and trailing dots or spaces in joined segments? [U]
5. **Technical:** which OS and toolchain carry the pinned UI-test job, and how often are snapshots refreshed? [I]
6. **Measurement:** does arm C of §9.1 lower bypass and silencing rates on both feeds? [U]
7. **Design:** do two admission levels (ghost preview versus commit) exist, or one? It decides whether `Admitted` needs a scope
   parameter (§6.2) [U].

## Findings for sibling docs (reported, not fixed)

- **crate-map §2.4 and testing-strategy §16 item 1:** clippy's `indexing_slicing` does not flag `HashMap<String, u32>` indexing
  [V, probe]; a custom check is needed.
- **core-document-model §5.1, doc 45 §2.1, doc 57 CL1:** module privacy remains the mechanism; a trybuild UI test can now prove it
  without breaking the `compile_fail` ban.
- **commands-undo-history §3:** tool descriptions from `///` via `schemars` conflict with `AGENTS.md`'s developer-facing doc rules
  (§6.8).
- **testing-strategy §14:** the CI gate denies warnings, but the edit loop does not see them; see §4.3.
- **agent-runtime §6:** "one finding per turn" meets contrary evidence on grouping (§6.9).
- **doc 22 §7.3:** the WIT sketch's string scopes and JSON inputs bear on its open question 2 (§7.1).

## Findings for strict-path (for its author; not fixed here)

The public `PathHistory` lets a downstream crate mint stamps; the design book's "markers as proof" is convention; `must_use` is not
paired with deny-level lints, and rustc offers `let _`; `compile_fail` doctests pass on any error, where trybuild would check the
text; the MCP demo forwards error `Display` text (with host paths) to the model; the sanitizer misses zero-width and tag characters;
`FromStr` creates directories; `write()` is not atomic; design-book examples are `no_run`; `on_unimplemented` needs MSRV 1.78.

## Sources

All read on 2026-09-28.

**strict-path**

- https://crates.io/crates/strict-path (0.2.3, 2026-05-03, `MIT OR Apache-2.0`); https://docs.rs/strict-path;
  https://dk26.github.io/strict-path-rs/
- https://github.com/DK26/strict-path-rs at `ed6bbeda5f39587666a4cb58864f54264d6d8fb9`: `README.md`, `AGENTS.md`, `.agents/*.md`,
  `LLM_CONTEXT.md`, `LLM_CONTEXT_FULL.md`, `llms.txt`, `CHANGELOG.md`, `strict-path/src/**`, `demos/src/bin/llm/*.rs`
- Branch `docs` at `c24e97ea3f23076f113264fab48f3f4d20a2790d`: `docs_src/src/design_decisions.md`, `development_story.md`,
  `type_history_design.md`, `anti_patterns.md`, `best_practices/authorization_architecture.md`
- https://crates.io/crates/soft-canonicalize (0.5.6); https://crates.io/crates/proc-canonicalize (0.1.3)

**Harnesses, language servers and the toolchain**

- https://github.com/anomalyco/opencode at `03e67171ab2dc1e7f16e8cebfbc7f778f61b89f0`: `packages/opencode/src/lsp/diagnostic.ts`,
  `lsp/client.ts`, `lsp/server.ts`, `tool/edit.ts`, `tool/write.ts`
- https://github.com/rust-lang/rust-analyzer at `03fcb77246f2568adb0e9b2fa60d19c6cc1686f4`:
  `crates/rust-analyzer/src/diagnostics/flycheck_to_proto.rs`, `crates/rust-analyzer/src/handlers/notification.rs`
- https://github.com/rust-lang/rust-clippy at `57785c2b475d0e0998ba6a933de491ec0b342473` (`clippy_lints/src/indexing_slicing.rs`,
  `disallowed_methods.rs`, `let_underscore.rs`, `book/src/lint_configuration.md`); `clippy_config/src/types.rs` on master;
  https://github.com/rust-lang/rust-clippy/issues/13981; https://doc.rust-lang.org/clippy/lint_configuration.html
- https://doc.rust-lang.org/reference/attributes/diagnostics.html; https://blog.rust-lang.org/2024/05/02/Rust-1.78.0/;
  https://blog.rust-lang.org/2024/09/05/Rust-1.81.0/; https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/;
  https://github.com/rust-lang/rust/pull/150935 (`on_move`); https://github.com/rust-lang/rust/pull/152901 (`on_unknown`);
  https://doc.rust-lang.org/rustc/json.html; https://doc.rust-lang.org/rustdoc/unstable-features.html
- https://github.com/dtolnay/trybuild; https://docs.rs/trybuild/latest/trybuild/
- https://github.com/BohemiaInteractive/CWR at `ffc61838b7`: `mserver/Archive/src/pbo.rs`
- https://component-model.bytecodealliance.org/design/wit.html;
  https://github.com/WebAssembly/component-model/blob/main/design/mvp/Explainer.md;
  https://github.com/WebAssembly/WASI/blob/main/docs/DesignPrinciples.md
- https://graham.cool/schemars/deriving/attributes/; https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- https://microsoft.github.io/TypeChat/docs/introduction/; https://pydantic.dev/docs/ai/core-concepts/retries/

**Papers and reports**

- Type-constrained decoding (PLDI 2025): https://arxiv.org/abs/2504.09246; https://github.com/eth-sri/type-constrained-code-generation
- Monitor-guided decoding: https://arxiv.org/abs/2306.10763; https://github.com/microsoft/monitors4codegen
- ChatLSP (OOPSLA 2024): https://arxiv.org/abs/2409.00921; https://hazel.org/papers/chatlsp-oopsla2024.pdf
- Type-error ablation: https://arxiv.org/abs/2606.01522
- Feedback loops in C-to-Rust: https://arxiv.org/abs/2512.02567
- RustAssistant: https://arxiv.org/abs/2308.05177
- AutoVerus: https://arxiv.org/abs/2409.13082
- Generative Compilation: https://arxiv.org/abs/2607.13921
- Alignment in constrained generation: https://arxiv.org/abs/2606.21619; "Let Me Speak Freely?": https://arxiv.org/abs/2408.02442;
  rebuttal: https://blog.dottxt.ai/say-what-you-mean.html
- Evaluating AGENTS.md: https://arxiv.org/abs/2602.11988; tuned guidance: https://arxiv.org/abs/2606.20512
- mini-swe-agent: https://github.com/SWE-agent/mini-swe-agent/
- Language servers and tokens: https://arxiv.org/abs/2608.13568
- ImpossibleBench: https://arxiv.org/abs/2510.20270
- Library evolution: https://arxiv.org/abs/2406.09834; RustEvo²: https://arxiv.org/abs/2503.16922
- Rust crate hallucination: https://arxiv.org/abs/2606.08444
- DocPrompting: https://arxiv.org/abs/2207.05987; CloudAPIBench: https://arxiv.org/abs/2407.09726; NovelAPIBench:
  https://arxiv.org/abs/2606.03657
- Misleading comments: https://arxiv.org/html/2504.04372v2
- Rules File Backdoor: https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents
- Structured outputs: https://openai.com/index/introducing-structured-outputs-in-the-api/;
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use; JSONSchemaBench: https://arxiv.org/abs/2501.10868
- DSPy Assertions: https://arxiv.org/abs/2312.13382
- CaMeL: https://arxiv.org/abs/2503.18813; FIDES: https://arxiv.org/abs/2505.23643; Progent: https://arxiv.org/abs/2504.11703;
  design patterns: https://arxiv.org/abs/2506.08837; levels of autonomy: https://arxiv.org/abs/2506.12469
- Language-level comparisons: https://www.swebench.com/multilingual.html; https://arxiv.org/abs/2504.02605;
  https://github.blog/ai-and-ml/llms/why-ai-is-pushing-developers-toward-typed-languages/

**Plotroom (this repository)**

- `AGENTS.md` ("Error Design", "Type Safety", "Doc Examples Must Compile and Pass"); `docs/architecture/commands-undo-history.md`
  §3, §4; `core-document-model.md` §5.1; `crate-map.md` §2.3–§2.5, §10; `agent-runtime.md` §6–§8; `testing-strategy.md` §12, §14,
  §16; `extensibility.md` §6, §8; `validation-and-lints.md` §9, §12, §13
- Research docs 22 §7.3–§7.4, 23 §13.4, 24 (rule L2), 27 §4.10, 30 (TL;DR), 38, 45 §2.1, 57 (CL1); decisions D001, D008, D024,
  D025, D026, D027, D031, D044, D048; design-gap requests DG011, DG017, DG018, DG032; `docs/porting/upstream-test-map.csv`

## Verification notes

### 2026-09-28, author checks at write-up

- **Probes re-run** (two throwaway crates outside the repository; rustc 1.98.1 and clippy 0.1.98 of 2026-09-01; strict-path pinned
  `=0.2.3` with `virtual-path`): the phantom-marker forge and the public `PathHistory` mint compile; `.join()` on a `StrictPath`
  gives E0599 with no suggestion; `std::fs` on a boundary gives E0277 on `AsRef<Path>`; an `on_unimplemented` message replaced the
  E0277 headline and was followed by "help: this trait has no implementations, consider adding one"; a function bound showed the
  custom note while an impl bound did not; `must_use` at deny printed its note plus the `let _` help; a clippy reason was a note
  without `replacement` and a spanned help with one; `indexing_slicing` flagged `Vec` but not `HashMap` indexing; clippy's
  `new_without_default` proposed `impl Default` for a typestate builder (new in this pass). Quotes in §3.2 are from this run.
- **Sources re-read at the cited commits:** OpenCode `diagnostic.ts`, `edit.ts`, `write.ts`, `client.ts` (no `didSave`) and
  `server.ts`; `git pull` on the OpenCode clone reported it already at `03e67171`. rust-analyzer `flycheck_to_proto.rs` and
  `notification.rs` at `03fcb772`. strict-path `README.md`, `CHANGELOG.md`, `AGENTS.md#L72`, `.agents/coding-standards.md` and
  `strict-path/Cargo.toml` at `ed6bbeda`; design book `design_decisions.md` and `development_story.md` at `c24e97ea`. CWR `pbo.rs`
  at `ffc61838b7`; its test is row 140 of the porting CSV (`port-now`, `formats-pbo`).
- **Papers:** titles, authors and headline claims of arXiv 2606.01522, 2608.13568, 2606.21619, 2602.11988 and 2607.13921 were
  checked on their abstract pages. Numbers beyond the abstracts (per-mode rates, ablation percentages) were read by the research
  pass from the papers' full text and are quoted as [V-author], not re-read in this pass. ChatLSP values are read from figures.
- **Plotroom lines** checked: `AGENTS.md` "Doc Examples Must Compile and Pass" bans `compile_fail`; commands-undo-history §3 derives
  tool descriptions from `///`; core-document-model §5.1 (`Guarded<T>`, module privacy); crate-map §2.3–§2.5; agent-runtime §7
  (effective shape rule); doc 30 TL;DR (1 → 16 of 24 with cards, 1 → 4 with the primer alone); doc 22 §7.3 WIT sketch;
  extensibility §6 (`plotroom:plugin@1`).
- **The §8 diff** was generated by a script from `AGENTS.md` as of 2026-09-28 and checked with `git apply --check` on a copy outside
  the repository; applying it reproduced the intended text exactly. `AGENTS.md` itself was not modified.
- Not done: no runtime test of OpenCode with rust-analyzer, no model runs, no legal review of the licence reading.

### 2026-09-28, review of docs 61–63 and the §8 diff

- **Spot-checked and confirmed at the cited commits:** OpenCode `edit.ts#L196-L201`, `write.ts#L18`, `#L74-L90`, `diagnostic.ts#L3-L27`,
  `server.ts#L922-L931` (rust-analyzer spawned with no initialisation options) and `client.ts` (no `didSave`; `didChange` and
  `didChangeWatchedFiles` only); a fresh fetch of OpenCode's `dev` branch is still `03e67171`. rust-analyzer `notification.rs#L303-L326`
  and `flycheck_to_proto.rs#L188-L192`, `#L332-L346`, `#L456`, `#L461-L484`; clippy `indexing_slicing.rs#L262-L288` and every lint name
  and group in §5.3 (`let_underscore_must_use`, `allow_attributes_without_reason`, `single_char_lifetime_names` and
  `wildcard_enum_match_arm` restriction; `fn_params_excessive_bools`, `struct_excessive_bools`, `return_self_not_must_use`,
  `too_many_lines`, `missing_errors_doc` and `missing_panics_doc` pedantic). strict-path at `ed6bbeda`: `README.md#L83-L97`,
  `#L181-L187`, `CHANGELOG.md#L79-L101`, `AGENTS.md#L72`, `.agents/coding-standards.md#L5-L22`, `validator/mod.rs#L1-L2`,
  `strict_path/mod.rs#L42-L52`, `#L99-L108`, `path_boundary.rs#L281-L288`, `sanitize.rs#L3-L37` (no zero-width or tag characters),
  the MCP demo `#L156-L170`; design book at `c24e97ea`: `design_decisions.md#L9`, `#L78`, `development_story.md#L41-L45`, `#L82-L97`,
  and "mathematically proves" in `authorization_architecture.md`. docs.rs shows 0.2.3 and the quoted guarantee sentence. CWR
  `pbo.rs#L261-L285`, `#L458-L472` and CSV row 140.
- **Confirmed on the page:** abstracts of 2504.09246 ("more than half"; the 94% type-error share is in the paper body, per search
  snippets of the full text), 2602.11988 ("do not generally improve", "over 20%"), 2608.13568 and 2503.18813; ImpossibleBench's
  76% (GPT-5, one-off SWE-bench) is in the paper body, not the abstract; clippy issue #13981 is open with the stated scope.
- **Corrected in this review:** (1) the MCP rule in §4.4: servers MUST conform to a declared output schema and clients SHOULD
  validate, not "must validate"; (2) §5.6: the rustdoc book says error-code checking is nightly-only and that a stable sample with an
  error code is read as plain text, so "treated as a label" was replaced by the weaker, sourced statement; (3) §6.6: the upstream
  guard also accepts `.` components, and the reader already maps `\` to `/` (`normalize_name`, `#L289-L291`, used at `#L326`), so
  gap (2) applies only to names that bypass the reader, as the upstream test's do; (4) TL;DR, §4.4 and §6.3 said a strong model pulls
  knowledge *instead of* pushed cards, which contradicts doc 61 §4.10 and doc 63 §3.2 rule 1; now "in addition to"; (5) TL;DR "It
  closes a gap" is now conditional, because nothing is adopted; (6) §5.3 and the diff: `#[expect]` alone breaks on lints that fire
  on only some targets (an unfulfilled expectation warns, and CI denies warnings on three OSes), so the rule now allows
  `#[allow(lint, reason = "…")]` for those cases; (7) cross-links to doc 61 (Teller) and doc 63 (`Grant<L>`, the same witness as
  `ShapeGrant`) in the sibling paragraph, §6.3 and §10 item 7.
- **The §8 diff after review:** three edits (the `expect` exception above; "Most code in this repository" became "Much of the code",
  since no code exists yet; "the pinned toolchain" became "a pinned toolchain", because the repository has no toolchain pin, no Cargo
  workspace, no `clippy.toml` and no CI workflow yet). The diff was regenerated from a patched copy of `AGENTS.md`, re-checked with
  `git apply` on a fresh copy (output byte-identical to the intended text) and adds 116 lines, removes none. It follows "Maintaining
  This File": no reference to this study, strict-path or any session; every named file or tool (`clippy.toml`,
  `[workspace.lints.rust]`, trybuild, `tests/ui`) is the mechanism the rule is about. `AGENTS.md` itself is unchanged.
- **Still open for the owner:** approval of §8; whether `plotroom-io` depends on strict-path; the one name for the grant witness
  (§6.3 here, doc 63 §9.2).
