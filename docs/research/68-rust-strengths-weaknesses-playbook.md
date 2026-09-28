# Rust for Plotroom: promises, strengths, weaknesses and a playbook

Research doc 68 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: the owner, contributors and LLM coding agents. This
file is meant to be read on its own.
Question answered (owner, 2026-09-28, verbatim): "I'd like you to research all advantaged and capbilities and promises of the Rust
langauge + all its weakness. And find out how to utilize them the best while avoiding, reducing or elminiting the weaknesses".

**Status: study; proposals only; nothing decided.** Nothing in the repository was changed except this file. Seven throwaway probes
(four at write-up, three in the verification pass) were compiled in a scratch folder outside the repository with rustc, cargo and
clippy 1.98.1 on Windows 10 (`x86_64-pc-windows-msvc`); no cargo command ran inside the repository. D058 item 2 names this doc as
in-flight work "whose playbook updates `AGENTS.md`": every `AGENTS.md`, crate-map, testing-strategy or workflow change below is a
proposal for the owner, marked as such, and none was applied.
**Epistemic legend** (doc 16's, extended as in docs 62–67). **[V]** opened at the cited source on 2026-09-28 (URL in Sources).
**[V-author]** a number published by the cited authors, not reproduced by us. **[V, probe]** observed in this doc's own probes
(verification notes). **[V, working tree]** read in the uncommitted M0 skeleton (files staged in the index on 2026-09-28, below); they
may change before they are committed. **[V, local registry]** read in the local Cargo registry sources. **[V per doc N]** taken from a
sibling doc or decision. **[I]** our inference or proposal. **[U]** unknown until measured or checked. The first draft also used an
**[R]** tag (reported by a research pass, not re-opened); the verification pass opened those sources and retagged every such claim
[V], [I] or [U], so no [R] remains.
**Relation to sibling docs.** Doc 62 owns type-driven guidance (witness and guard rules, "Diagnostics as Guidance", trybuild) and
its applied `AGENTS.md` amendment; doc 64 owns Rust and weak models (the evidence review, the pilot, the fast inner loop); doc 65
applies the same ideas to mission scripts; doc 43 §3.2 owns seed portability for generator crates (a pinned ChaCha behind a newtype,
integer scoring, golden seeds across the 3-OS matrix, RAT3). Doc 06 owns the UI stack (D016), doc 07 the formats and their caps
(D017), doc 13 local inference (D022), doc 22 plugins (D007). `docs/architecture/crate-map.md` §2.3–§2.5 and `testing-strategy.md`
§14 hold the planned lints and CI gates. This doc does not repeat them; it asks what Rust promises and does not, and turns the gaps
into settings, lints, code rules and CI jobs. Section 6 covers AI coding agents only where docs 62 and 64 do not.
**The M0 skeleton.** While this doc was written, the M0 skeleton (D058 item 1) was in the working tree, uncommitted and staged: the root
`Cargo.toml`, `Cargo.lock`, `clippy.toml` and `deny.toml`; `crates/plotroom-testkit/`; `xtask/` with working `layers` and `hygiene`
checks (`xtask/layers.toml`, unit tests, `tests/live_workspace.rs` and the planted cargo-deny fixtures); `.github/workflows/ci.yml` and
`fuzz.yml`; the separate `fuzz/` workspace with one placeholder target (`config_parse`, waiting for SP-09's `plotroom-config`); and
edits to `CODE-INDEX.md` §2–§3 that record the toolchain rule. It implements much of crate-map §2.4 and chooses a CI-only toolchain
pin. §4.3 is written as a diff against it and cites it as [V, working tree].
**Names.** A *promise* is a guarantee the Rust project states in its own documents. A *boundary* is where a promise stops. The
playbook ranks each mitigation as **Eliminate** (the weakness cannot occur, within the scope stated), **Reduce** (it occurs less or
costs less) or **Accept and monitor** (it stays; something watches it). *Status* in the playbook is **decided** (in `AGENTS.md` or a
`Dnnn`), **proposed** (in an architecture doc or research doc), **working tree** (in the uncommitted skeleton), or **missing**.
Doc-local labels: 68-W1–68-W27 (weaknesses, §3), 68-P1–68-P33 (playbook items, §4), 68-G1–68-G13 (design-gap candidates, §9), and
"68 OQ n" for this doc's open questions, to keep them apart from other docs' OQ numbers. L0–L8 are the crate-map §2 layers, not the
`L1`–`L4` code family that `docs/README.md` §2.2 lists under DG005. A search of `docs/`, `tools/`, `prompts/` and `skills/` found no
other `68-` label; D058 mentions "doc 68" only.
**Hygiene.** Public sources only. No private or unpublished project is named. No local paths, user names or keys; probe files stayed
in a scratch folder outside the repository.

## TL;DR

- **What Rust promises.** Safe Rust has no undefined behaviour: "`unsafe` only means that avoiding undefined behavior is on the
  programmer", and data races are on the Reference's UB list, so safe code cannot have them [V]. "If your code compiles on Rust stable
  1.0, it should compile with Rust stable 1.x with a minimum of hassle" [V]. Tier 1 targets are "guaranteed to work" [V]. Iterators are
  "*zero-cost abstractions*", meaning "using the abstraction imposes no additional runtime overhead" (the Book) [V].
- **Where the promises stop.** Rust does not promise: freedom from panics (crashes), from aborts that skip every destructor (stack
  overflow, allocation failure, a panic inside `Drop` during unwinding, `process::exit`), from integer wrap-around in release builds,
  from deadlocks, leaks and logic errors, or from bugs in the compiler (1.98.0 emitted a vtable "with a null pointer where a function
  pointer should be", fixed 14 days later in 1.98.1) [V]. There is no LTS toolchain: "The Rust project only provides support and
  security updates for the most recent stable release" [V]. On 2026-09-28 rust-lang/rust had **135 open `I-unsound` issues, 112 not
  marked nightly-only** [V]. `#![forbid(unsafe_code)]` covers only `unsafe` tokens written in our own crates: dependencies' unsafe,
  build scripts, and **unsafe emitted by any macro defined in another crate, a proc macro or an ordinary `macro_rules!`**, all compile
  under it, including an `unsafe { *p }` that lets a safe function dereference a raw pointer [V, probe].
- **Strengths that matter most for Plotroom** (§2, §5): types that make wrong states unbuildable (newtypes, closed enums with
  exhaustive `match`, witnesses consumed by move, typestate); the compiler and clippy as a gate that humans and agents loop on; a crate
  graph plus clippy and cargo-deny bans that confine files, processes and network to named crates; parsers of hostile files with no
  memory-safety class of bug; fearless data parallelism (rayon) and `Send`/`Sync`-checked threading; one codebase on three tier-1
  desktop targets; WebAssembly for plugins. Android measured about 0.2 memory-safety vulnerabilities per million lines of Rust against
  about 1,000 for C/C++, a rollback rate about 4× lower for medium and large changes, and about 25% less review time [V-author].
- **Weaknesses with high impact on Plotroom** (§3): panics and aborts on hostile input (68-W1, 68-W2); build-time code execution and
  supply-chain attacks (68-W8: in the `arrayref` compromise of 2026-08-20 a republished crate was made to depend on `proc-macro1`,
  whose build script downloaded a payload [V]); compile and link time (68-W9: 55% of surveyed developers wait over 10 s per rebuild
  [V-author]); Windows friction on the owner's Windows 10 host (68-W16: `link.exe` stays the MSVC default, #71520 is open [V]).
  Medium: silent overflow outside format crates, determinism (hash order, platform-dependent float functions, non-portable RNGs),
  concurrency at the async edge, borrow-checker friction, ecosystem churn, GUI maturity (IME), workspace-unified features, host paths
  in binaries, secrets in derived `Debug`, the orphan rule, no runtime reflection, the contributor pool. Low: no stable ABI (D007
  already avoids it), debugging, compiler soundness holes, text and path semantics, a single production compiler [U].
- **The playbook's top items** (§4; the order of work is §4.5): (1) a panic and crash policy: `panic = "unwind"`, `catch_unwind` only
  at job boundaries, the global rayon pool built with a panic handler (rayon's default "is to abort the process"), no dropped tokio
  `JoinHandle`s, a session sentinel for unclean exits, durability never in `Drop` (68-P1); (2) a depth cap on every recursive parser,
  tested at cap and cap+1, and every thread and pool the workspace creates named and given an explicit stack size (68-P2); (3) a cap
  on the in-memory byte size of every input-sized allocation, with `try_reserve` as a second line (68-P3); (4) `overflow-checks = true`
  in the release profile as an owner decision with measurements, knowing it applies to the whole dependency graph [V] (68-P4, 68 OQ 1);
  (5) cast lints in format crates (68-P5); (6) a toolchain policy: exact CI pin, stable N adopted on its latest point release when N+1
  ships, security bumps within a week, a beta canary, a check that the CI pin and `rust-version` agree (68-P9); (7) supply chain: a
  build-script allowlist seeded with the six crates that have build scripts today, a proc-macro allowlist (partial: it cannot see
  `macro_rules!`), advisories split from the blocking gate, pinned CI tools and actions, a publish-age cooldown once Cargo 1.100 is
  pinned (it does not cover `cargo install`), `cargo auditable` release builds (68-P10); (8) dev-profile debuginfo cuts, one
  integration-test binary per crate, a CI build cache; dependency `opt-level` only as a measured trade-off (68-P12); (9)
  `CARGO_BUILD_WARNINGS=deny` instead of `-- -D warnings`, which keeps the build cache when switching but, unlike `-D warnings`, also
  fails on linker warnings: an explicit choice (68-P13) [V, probe].
- **Draft configuration** (§4.3): a diff against the M0 skeleton's `Cargo.toml`, `deny.toml`, `clippy.toml`, `ci.yml` and `fuzz.yml`,
  plus a policy of **no root `rust-toolchain.toml` or `.cargo/config.toml`** (the skeleton's choice, which keeps `tools/rust-weak-models`
  unaffected and reverses FR-C-030's proposed fix) and **MSRV = the pinned stable**, checked against the CI pin.
- **How to exploit the strengths most** (§5): put the leverage where Plotroom is special: every edit path through one typed,
  witness-gated admission; parsers written as capped, borrowed, iterator-driven pure functions with fuzz and property tests; the
  harness as synchronous "sans-IO" crates; capability confinement by crate graph; the 3-OS CI matrix as our own crater.
- **AI coding agents** (§6, new only): Claude Code's rust-analyzer plugin feeds errors **and warnings** after each edit [V], so doc
  62's errors-only assumption is client-specific; opening or checking a workspace runs build scripts and proc macros [V]; parallel
  agent worktrees keep their own `target/`, and sharing dependency builds needs a measured cache such as sccache; snapshot "overwrite"
  switches let an agent rewrite a spec; rust-lang/rust's LLM policy (the monorepo only, "not an official stance") forbids LLM-created
  changes except pre-arranged ones with disclosure, and asks issue reporters to disclose and quote LLM-generated parts [V].
- **Counts:** 27 weaknesses; 33 playbook items (6 eliminate, five of them within a stated scope; 2 eliminate in our own parsers and
  reduce elsewhere; 21 reduce, one of them partly accepted; 4 accept and monitor); 13 design-gap candidates, none filed.

## 1. The promises and their exact boundaries

### 1.1 The state of Rust on 2026-09-28

| Item | State | Tag |
| --- | --- | --- |
| Stable | **1.98.1** (2026-09-03). "Rust 1.98.1 fixes a miscompilation in vtable generation": in 1.98.0 rustc "would incorrectly generate a trait object vtable with a null pointer where a function pointer should be. This leads to undefined behavior in the emitted code" (#161441). Point releases this year: 1.93.1, 1.94.1, 1.96.1, 1.97.1, 1.98.1 | [V] |
| Support window | "The Rust project only provides support and security updates for the most recent stable release and the latest releases in our beta and nightly channels": no LTS toolchain | [V] |
| Next releases | 1.99 about 2026-10-01 and 1.100 about 2026-11-12 on the six-week cadence. releases.rs showed stale data when read (stable 1.97.1), so its dates are not used | [I]; [U] releases.rs |
| Edition | 2024, since 1.85.0 (2025-02-20: "the Rust 2024 Edition is now stable!"). `std::env::set_var` and `remove_var` became `unsafe`: "It can be unsound to call `std::env::set_var` or `std::env::remove_var` in a multithreaded program" | [V] |
| Linker | LLD is the default only on `x86_64-unknown-linux-gnu` (1.90): on ripgrep "linking is reduced 7x, resulting in a 40% reduction in end-to-end compilation times", 20% for a clean debug build; `lld` "is not bug-for-bug compatible with GNU ld". Windows MSVC: rust-lang/rust#71520 "Use lld by default on x64 msvc windows" is open with six blockers, one being "rust-lld does not support the MSVC manifestdependency .drectve" (#85642) | [V] |
| Trait solver | The next-generation solver was enabled by default on nightly, as announced 2026-08-21, "to surface any remaining issues", with "more than 200 issues" fixed, "a non-trivial amount of breakage" (#160895) and a plan to "stabilize it in the next months"; it would "enable us to fix the remaining type system unsoundnesses". Its performance was compared on "the top 20,000 crates on crates.io". "Stabilize the next-generation trait solver" is a 2026 large goal | [V] |
| Borrow checker | Polonius alpha, which accepts "NLL problem case 3" and lending-iterator patterns, is a nightly prototype that "passes perf runs and crater runs"; the team would "accept a compile-time overhead of 10–20%". "Stabilize and model Polonius Alpha" is a 2026 large goal; no release named | [V] |
| Faster builds | Cranelift, the parallel front end (`-Zthreads`) and Cargo feature unification "require nightly". 2026 goals: "Promoting Parallel Front End" (large) and "Improve `rustc_codegen_cranelift` performance"; no release named | [V] |
| Project goals 2026 | "the complete list of all 81 goals for 2026"; among them "View types experiment", "Stabilize MemorySanitizer and ThreadSanitizer Support", "Native async fn dynamic dispatch in traits", "Prepare TAIT + RTN for stabilization"; none for build-script sandboxing, a stable ABI or `trim-paths` | [V] |
| Cargo | `build.build-dir` (1.91), `build.warnings` / `CARGO_BUILD_WARNINGS` (1.97), config `include` with `optional = true`. `min-publish-age` merged 2026-08-28 for 1.100 (#17335): `[registry] global-min-publish-age` and per registry `[registries.<name>] min-publish-age`, with duration strings such as `"7 days"`; `CARGO_RESOLVER_INCOMPATIBLE_PUBLISH_AGE=allow` overrides it; `registry.min-publish-age` was removed; it does not affect `cargo install` | [V] |
| Cargo security | CVE-2026-33055 and -33056 ("Extracting malicious crates can alter permissions on arbitrary paths on Unix-like systems") fixed in 1.94.1; CVE-2026-5223 and -5222 in 1.96 | [V] |
| Soundness | 135 open `I-unsound` issues, 112 without `requires-nightly`; #25860 ("Implied bounds on nested references + variance = soundness hole") open since 2015-05-28, partly fixed by #129021, the higher-ranked form remains | [V] |
| Local toolchain | rustc 1.98.1 (48a229cea 2026-09-01), cargo 1.98.1, clippy 0.1.98; components include `rust-src` | [V, probe] |

**Stabilised features this playbook uses** (each from its release post [V]):

| Release | Feature | Used by |
| --- | --- | --- |
| 1.81 (2024-09-05) | The `expect` lint level; "the non-unwind ABIs (e.g., `"C"`) will now abort on uncaught unwinds"; sorts "will now panic" on an incorrect `Ord` | `AGENTS.md` suppression rule; §1.3 |
| 1.85 (2025-02-20) | Edition 2024; async closures (`async \|\| {}`); `#[diagnostic::do_not_recommend]` | The workspace; 68-P18; `AGENTS.md` "Diagnostics as Guidance" |
| 1.88 (2025-06-26) | Let chains, "only available in the Rust 2024 edition" | Parsers and validators |
| 1.90 (2025-09-18) | LLD default on x86_64 Linux | 68-P14 |
| 1.91 (2025-10-30) | `strict_add`, `strict_sub`, `strict_mul` and the other `strict_*` methods; `aarch64-pc-windows-msvc` tier 1 | 68-P4 (conditional) |
| 1.92 (2025-12-11) | Two never-type lints deny-by-default; `Box::new_zeroed` | §1.5; 68-P2 |
| 1.95 (2026-04-16) | `cfg_select!`, "roughly similar to a compile-time `match` on `cfg`s" | Platform code (§2.5) |
| 1.97 (2026-07-09) | `build.warnings` / `CARGO_BUILD_WARNINGS`; `linker_messages` shown by default | 68-P13 |
| 1.98 (2026-08-20) | `algebraic_*` float methods, which "allow optimizations on these operations using the algebraic properties of real numbers" | 68-P7 (kept out of seeded crates) |

### 1.2 What the promises say, and when they hold

| Promise | The project's words | Holds only if | For Plotroom |
| --- | --- | --- | --- |
| No undefined behaviour in safe code | "`unsafe` only means that avoiding undefined behavior is on the programmer"; unsafe code that no safe client can misuse "is called *sound*" | Every `unsafe` below us (std, dependencies, macro expansions) is sound, and the compiler and LLVM are correct | `unsafe_code = "forbid"` puts the remaining UB risk in dependencies, their macros and the toolchain (§1.4) [I] |
| No data races | Data races are the first entry of the Reference's UB list, so safe code cannot have them | As above | Races on shared memory cannot happen in our code; logical races, deadlocks and lost updates can (§1.3) |
| Stability | "If your code compiles on Rust stable 1.0, it should compile with Rust stable 1.x with a minimum of hassle", while "We reserve the right to fix compiler bugs, patch safety holes, and change type inference" | The code compiles today; lint output is not covered | A workspace that denies warnings can break on a toolchain bump (§1.5) |
| Zero-cost abstractions | "Iterators are one of Rust's *zero-cost abstractions*, by which we mean that using the abstraction imposes no additional runtime overhead" (the Book, ch. 13-04) | Optimised builds; compile time and binary size are not covered | Iterator-style parsers cost nothing at run time; generics cost compile time (68-W9) |
| Tier 1 | "Guaranteed to work": official binaries, and every change is built and tested | The target is tier 1 | x86_64 Windows MSVC and GNU (Windows 10+), x86_64 Linux GNU (glibc 2.17+), aarch64 macOS (11.0+) and aarch64 Windows MSVC are tier 1; `x86_64-apple-darwin` is tier 2; the win7 targets are tier 3 [V] |
| Editions | "crates in one edition **must** seamlessly interoperate with those compiled with other editions" [V] | — | Edition-2021 dependencies work in an edition-2024 workspace |

### 1.3 What Rust does not promise

The Reference lists what is not unsafe: "Deadlocks", "Leaks of memory and other resources", "Exiting without calling destructors",
"Exposing randomized base addresses through pointer leaks", plus integer overflow and logic errors [V].

| Behaviour | What the sources say | Plotroom exposure |
| --- | --- | --- |
| Panics | Indexing out of bounds, `unwrap`, division by zero, and panics inside std: since 1.81 the sorts "will now panic" on an incorrect `Ord` [V]; a `std::sync::Mutex` locked twice by one thread "will not return on the second call (it might panic or deadlock, for example)" [V] | Hostile missions, PBOs and addons; model output; plugin output. A panic in the UI thread loses unsaved work unless contained |
| Integer overflow | With debug assertions, overflow panics; "Other kinds of builds may result in panics or silently wrapped values on overflow, at the implementation's discretion" [V]. Cargo's release profile has `overflow-checks = false` [V] | Format crates deny `arithmetic_side_effects` (crate-map §2.4); everything else wraps silently in shipped builds |
| Logic errors | Breaking Hash/Eq or key-mutation rules gives behaviour that "may be unspecified but will not result in undefined behavior … panics, incorrect results, aborts, and non-termination … may also differ between runs, builds, or kinds of build" [V] | Id maps, undo history, provenance hashes, seed-reproducible generation |
| Float functions | `f64::sin`, `exp`, `ln`, `powf` and the other transcendental functions: "The precision of this function is non-deterministic. This means it varies by platform, Rust version, and can even differ within the same execution from one invocation to the next"; `sqrt` and `mul_add` are "guaranteed not to change" [V] | Seeded generation, golden journals and provenance hashes that pass through these functions can diverge between OSes and toolchains (68-W4) |
| Stack overflow | Spawned threads get "2 MiB on all Tier-1 platforms"; "the stack size of the main thread is *not* determined by Rust" [V]; the MSVC default reserve is "1 MB" [V]. In our probe, unbounded recursion under `catch_unwind` printed "thread 'main' (…) has overflowed its stack" and the process ended with exit status 0xC00000FD (`STATUS_STACK_OVERFLOW`); `catch_unwind` never returned [V, probe] | Recursive-descent parsers (config classes, preprocessor includes, SQF, CXL) on hostile nesting, and every recursive walker of what they build |
| Allocation failure | With std, `handle_alloc_error` will "print a message to standard error and abort the process"; "Future versions of Rust may panic by default instead" [V]. `Vec::with_capacity` "Panics if the new capacity exceeds `isize::MAX` *bytes*"; `try_reserve` returns an error "If the capacity overflows, or the allocator reports a failure" [V] | A hostile element count passed to `Vec::with_capacity` either panics (capacity overflow; containable by 68-P1) or aborts (allocator failure). On an overcommitting OS a reservation that succeeds can still fail when its pages are touched [I], so caps come first (68-P3) |
| `catch_unwind` | "It is **not** recommended to use this function for a general try/catch mechanism"; it "*only* catches unwinding panics, not those that abort the process"; with foreign exceptions it is "unspecified" whether the process aborts or returns `Err` [V]; that case arises only for foreign exceptions entering through a `"C-unwind"` ABI (next rows) [I] | Useful only at job boundaries (68-P1) |
| Tests and `panic` | "Tests, benchmarks, build scripts, and proc macros ignore the `panic` setting. The `rustc` test harness currently requires `unwind` behavior" [V] | A `panic = "abort"` release would ship behaviour no test ran |
| Destructors | `process::exit` runs "no destructors on the current stack or any other thread's stack"; the docs recommend returning `ExitCode` or `Result` from `main` [V] | Durability must not live in `Drop` |
| Rust panic at a `"C"` boundary | Since 1.81 "the non-unwind ABIs (e.g., `"C"`) will now abort on uncaught unwinds" [V]; the Reference's unwinding table gives "abort" for a `panic`-unwind at a non-unwinding ABI under `panic=unwind` [V] | A Rust panic inside a callback we export as `extern "C"` (for example one registered with a native library) aborts the editor |
| Native exception into Rust | The same table gives "undefined behavior" for a native unwind at a non-unwinding ABI; the UB list includes "unwinding past a stack frame that does not allow unwinding (e.g. by calling a `"C-unwind"` function imported or transmuted as a `"C"` function or function pointer)" [V] | C++ exceptions from native code (a possible in-process inference engine, GPU drivers) must never cross a `"C"` import: keep such engines out of process (D022 item 2's default) or behind `"C-unwind"` plus `catch_unwind` |
| Host paths | `--remap-path-prefix` exists to "Remap source path prefixes in all output, including compiler diagnostics, debug information, macro expansions"; Cargo's `trim-paths` profile option, which controls "how paths are sanitized in the resulting binary", is unstable [V] | Without remapping, panic locations and debuginfo carry source paths, including dependency paths under `CARGO_HOME`, which contains the builder's user name [I] (68-W21) |
| Deadlock via temporaries | Edition 2024 drops `if let` temporaries before `else`, which fixes the classic `RwLock` read-then-write deadlock; "The temporaries of the `match` scrutinee are extended past the end of the `match` expression … the same as the 2021 behavior of `if let`" [V] | Guards taken in a `match` scrutinee still live through every arm |
| Async cancellation | "it must be a no-op to drop that future and recreate it"; `read_exact`, `read_to_end`, `read_to_string`, `write_all` can lose data and `Mutex::lock`, `Semaphore::acquire`, `Notify::notified` lose their queue place when dropped (tokio 1.53.1) [V] | SSE streaming, gamelink, MCP and downloads in L7 |
| Poisoning | "Poisoning is only advisory" [V] | A panicked writer does not protect readers |

### 1.4 Where the promise is thinner than it looks

- **Compiler bugs.** 1.98.0's miscompilation came from safe code; the fix shipped 14 days later [V]. Open soundness issues need
  contrived code such as higher-ranked function-pointer lifetimes (#25860) [V]; ordinary code does not hit them [I].
- **Dependency unsafe.** Of about 145,000 crates, "approximately 127,000 contain significant code"; of those, 24,362 (19.11%) use the
  `unsafe` keyword and 34.35% make a direct call into a crate that does; "Most of these Unsafe Rust uses are calls into existing
  third-party non-Rust language code or libraries" (Rust Foundation, 2024-05-21) [V]. Android's first Rust memory-safety vulnerability,
  a near-miss ("a linear buffer overflow in CrabbyAVIF", CVE-2025-48530), was rendered non-exploitable by the Scudo allocator's guard
  pages [V]; the post does not say where the bug sat, and that it involved `unsafe` code is our inference [I]. About 4% of Android's
  Rust is "written within `unsafe{}` blocks" [V].
- **Build-time code.** Build scripts and proc macros run on every developer and CI machine at build time; "an unsandboxed build script
  is effectively an enormous `unsafe` block" (2024H2 goal) [V]; no 2026 goal continues that work [V].
- **Macro-emitted unsafe escapes `forbid(unsafe_code)`.** In our probes a crate with `#![forbid(unsafe_code)]` compiled with no error
  while (a) a function-like proc macro and a derive each emitted an `unsafe impl` into it, and (b) `macro_rules!` macros exported by
  another crate emitted `unsafe impl Send`, `#[unsafe(no_mangle)] pub extern "C" fn` and `unsafe { $e }` around a caller-supplied
  `*p`, so a safe `pub fn` dereferenced a raw pointer [V, probe]. The same `unsafe impl` and `#[unsafe(no_mangle)]` written directly
  failed ("implementation of an `unsafe` trait"; "usage of the unsafe `#[no_mangle]` attribute") [V, probe]. So `forbid(unsafe_code)`
  proves "no `unsafe` token written in our own crates", not "no unsafe code in our crates": unsafe expanded from any macro defined in
  another crate is outside it. `cargo metadata` marks proc-macro crates but not crates that export `macro_rules!`, so no allowlist
  built from it can enumerate the second kind [I]. This settles doc 06 §4.3's open question on `bytemuck` derives in the direction of
  "it compiles", which makes it a policy question (68-P10, 68-G11) [I].
- **The rest of the toolchain.** Cargo itself shipped crate-extraction vulnerabilities in 2026 (§1.1) [V], and only the latest stable
  receives security fixes [V], so a pinned toolchain must move (68-P9).

### 1.5 The stability promise in practice

- **Lints are not covered.** 1.92 made two never-type lints deny-by-default, "approximately 500 crates affected" [V]; under
  `-D warnings` a toolchain bump can fail CI through a new lint with no code change [I]. Since 1.97 linker output is shown through
  the `linker_messages` lint, warn by default, which is "not affected by the `warnings` lint group" [V]. In our probe a linker warning
  (MSVC LNK4044) left a `RUSTFLAGS=-Dwarnings` build at exit 0 with the note "the `linker_messages` lint ignores `-D warnings`",
  while `CARGO_BUILD_WARNINGS=deny` failed the same build (exit 101, "warnings are denied by `build.warnings` configuration")
  [V, probe]. So a `build.warnings = deny` gate can also fail on a linker, SDK or toolchain change on any OS leg (68-P13) [I].
- **Diagnostic text is not covered.** The next trait solver will change trait-error text when it ships; trybuild `.stderr` snapshots
  (`AGENTS.md` "Negative Compile Tests") are exactly that text, and trybuild warns that output "can vary as a function of whether the
  `rust-src` Rustup component is installed" [V].
- **Real breakage happens.** Type-inference changes are reserved by the 2014 promise [V]. 1.80 stabilised `impl FromIterator<char>
  for Box<str>` and related impls [V]; #127343, "regression: type annotations needed for `Box<_>`", records "roughly ~5400
  regressions" in crater from `time` before 0.3.35 [V]; that the new impls caused it is our reading [I].

## 2. Strengths and capabilities

Each row gives the capability, the evidence and how Plotroom uses it. "Should" items are proposals [I].

### 2.1 Correctness by construction

| Capability | Evidence | Plotroom today | Should |
| --- | --- | --- | --- |
| Closed enums and exhaustive `match` | A new variant is a compile error at every unhandled site; `#[non_exhaustive]` has "no effect" inside its crate and outside it "matching on a variant does not contribute towards the exhaustiveness" [V] | Decided: exhaustive matching (`AGENTS.md`); proposed: closed command enums (architecture README §7) | Never put `#[non_exhaustive]` on workspace-internal enums: sibling crates would lose exhaustiveness. Use it only on plugin-SDK and wire enums (68-P20) |
| Newtypes, private fields, witnesses, typestate, sealed traits | "There is no runtime performance penalty for using this pattern, and the wrapper type is elided at compile time" (the Book, ch. 20-02) [V]; doc 62's probes on how their diagnostics land [V per doc 62] | Decided: `AGENTS.md` "Type Safety", witness and guard rules; newtype table in `CODE-INDEX.md` | Keep typestate at in-process seams (decided); P64-A1–A3 pending (doc 64 §5.1) |
| Move semantics (affine values) | A value moved into a function cannot be used again; a second use does not compile [I] | Decided in spirit: a witness is "taken by the code that requires the check" (`AGENTS.md`) | Make every witness and typestate transition consume `self`, so a check result is single-use (§5 rank 1) |
| Shared XOR mutable borrows | A live `&` and a live `&mut` to the same data cannot coexist, so iterator invalidation and aliased mutation do not compile [I] | — | Treat a borrow error as a design signal (68-P17), not as a reason to `clone()` |
| Const evaluation and `const` assertions | `const _: () = assert!(...)` fails compilation when a relation between constants breaks [I] | — | Tie caps and sizes together at compile time, for example a depth cap against its stack budget (68-P2, 68-P3) |
| Errors as values (`Result`, `?`, `#[must_use]`) | `unused_must_use` and clippy `let_underscore_must_use` can be deny [V per doc 62] | Decided: one structured `Error` enum per crate; guidance lints at deny | Keep error fields small: clippy's `result_large_err` fires above `large-error-threshold` 128 bytes by default [V] |
| Lints as mechanical rules | Clippy restriction lints enforce "no indexing, no unwrap"; "You shouldn't enable the whole lint group, but cherry-pick" [V] | Proposed (crate-map §2.4), working tree: the deny set plus `disallowed_methods`/`disallowed_types` at deny [V, working tree] | Add cast lints in format crates, `wildcard_enum_match_arm` in domain crates (68-P5, 68-P20) |
| Negative compile tests | trybuild snapshots the exact compiler output [V] | Decided (`AGENTS.md`) | Install `rust-src` in the UI-test job (68-P9) |

### 2.2 Tooling

| Capability | Evidence | Plotroom today | Should |
| --- | --- | --- | --- |
| Cargo, lockfile, `--locked` | Reproducible dependency graph | Decided (`AGENTS.md` commands) | Scheduled latest-dependencies job, non-blocking (68-P10) |
| Clippy, rustfmt, rustdoc tests | Edition 2024: "Doctests are now combined into a single binary" [V] | Decided: doctests must run | Keep logic in library crates: Cargo's `doctest` setting "is only relevant for libraries" [V] |
| rust-analyzer | `check.command` (default `"check"`), `check.workspace` (false passes `-p`), `cargo.targetDir` (prevents locking `Cargo.lock` "at the expense of duplicating build artifacts") [V] | Doc 62 proposes `check.command = "clippy"` | Ship the three settings (68-P15) |
| Property tests, fuzzing, mutation testing, model checking | `cargo-mutants --in-diff DIFF_FILE` "tests only mutants that overlap with regions changed in the diff" [V]; Miri claims "the first tool that can find *all* de-facto Undefined Behavior in deterministic Rust programs" [V-author]; Kani installs easily only on Linux x86_64 and macOS [V] | Decided: cargo-fuzz nightly workspace (D017) and proptest write → read round trips (D017 Consequences); proptest elsewhere proposed (testing-strategy §2) | Fixed proptest seed in PR CI plus a nightly random-seed run, mutants on parser PRs, Kani and Miri optional (68-P22) |
| Supply-chain tools | cargo-deny allow lists and build-script allowlist [V]; cargo-vet "safe-to-deploy" requires reasoning about "all unsafe blocks and usage of powerful imports" [V] | Decided: cargo-deny licence allowlist (D001); working tree: sources crates.io only, `yanked = "deny"` [V, working tree] | 68-P10 |

### 2.3 Performance

| Capability | Evidence | Plotroom today | Should |
| --- | --- | --- | --- |
| No garbage collector, predictable latency | Memory is freed deterministically [I] | Performance targets in ui-shell §11 (commit plus publish under 2 ms on a 5,000-entity synthetic mission) [V per ui-shell] | Measured in M0 (SP-10, roadmap M0 exit evidence item 6) and in the M2 benchmark |
| Iterators without bounds-check cost | The perf book: "Replace direct element accesses in a loop by using iteration", slice before the loop, "Add assertions on the ranges of index variables" [V] | Decided: iterator-first, no direct indexing (`AGENTS.md`) | Write hot loops (LZSS, DXT, terrain, `DrawList`) with `chunks_exact`/`split_first_chunk` [I] and check the assembly only when a benchmark asks |
| LTO and codegen units | `lto = true` is "fat" LTO; `"thin"` "takes substantially less time to run while still achieving performance gains similar to 'fat'" [V] | Decided: release `lto = true`, `codegen-units = 1` (`AGENTS.md` rule 7) | Add a `profiling` profile with thin LTO for local performance work (68-P12) |
| Memory layout control, `Box` on large values | `Box::new_zeroed` and `new_zeroed_slice` stable since 1.92 [V]; clippy `large_stack_arrays` (pedantic: "Large local arrays may cause stack overflow") [V] | — | Large buffers on the heap, never large stack arrays; `large_stack_arrays` at deny in parser crates (68-P2) |

### 2.4 Concurrency

| Capability | Evidence | Plotroom today | Should |
| --- | --- | --- | --- |
| `Send`/`Sync` checked at compile time | Data races are UB, so safe code cannot compile one (§1.2) | Proposed: one writer thread, `Arc<Snapshot>` published by atomic swap, rayon pool, one tokio runtime in L7–L8 (ui-shell §10; crate-map §2.3) | Keep single ownership; locks only at the edge (68-P8) |
| Data parallelism | rayon; in `scope`, "spawned tasks may access stack data in place that outlives the scope itself" [V] | Proposed: validation on rayon (ui-shell §10) | Parallel float reductions are not deterministic: rayon's `sum` "results are not fully deterministic" when `+` "is not truly associative (as is the case for floating point numbers)" [V]; keep seeded paths sequential (68-P7) |
| Cooperative cancellation | tokio cancel-safety list [V] | Proposed: `CancellationToken` at the provider seam (agent-runtime §3) | Cancel-safe `select!` only (68-P8) |

### 2.5 Portability and WebAssembly

| Capability | Evidence | Plotroom today | Should |
| --- | --- | --- | --- |
| Tier 1 on all three desktop OSes | §1.2 table [V]; GitHub's `macos-latest` label maps to "macOS-26-arm64" [V] | Decided: 3-OS CI matrix (`AGENTS.md`), Windows 10 floor (D016); working tree: ci.yml already runs `macos-latest`, the Apple-silicon tier-1 target [V, working tree] | Done |
| Platform code without extra crates | `cfg_select!` stable since 1.95 [V] | — | Use it in `plotroom-io` and `plotroom-install` |
| WebAssembly plugins | `wasm32-wasip2` is tier 2 and outputs a component rather than a core module [V]; wasmtime `Module::deserialize` is `unsafe` because it "can trivially be used to execute arbitrary code" (wasmtime 49.0.1) [V] | Decided: plugin tier T1 as WebAssembly components in wasmtime on an LTS line, with "fuel, epoch deadlines, memory limits" on every T1 plugin (D007 item 1) [V per D007] | `deserialize` is already a compile error under the workspace `forbid(unsafe_code)` (calling an `unsafe fn` needs an `unsafe` block); use `Config::cache` or recompile (68-P24) |

### 2.6 Ecosystem and Cargo

| Capability | Evidence | Plotroom today | Should |
| --- | --- | --- | --- |
| Workspaces, workspace lints, workspace dependencies | `[workspace.lints]` inherited per member [V, working tree] | Working tree: every member sets `[lints] workspace = true` | Keep; see §4.3 for the per-crate extras cargo does not allow |
| Crate graph as architecture | Layers L0–L8 with downward edges (crate-map §2) | Working tree: `xtask layers` checks direct edges, dev-only crates and confined third-party crates against `xtask/layers.toml` [V, working tree]; proposed: cargo-deny per-layer feature bans | The graph is both the compile-time lever (68-P12) and the capability fence (§5) |
| Linear-time regex | regex 1.13.1: "all regex searches in this crate have worst case `O(m * n)` time complexity" (`find_iter` is `O(m * n^2)`); for untrusted patterns, "Configure `size_limit` to something small" [V] | — | `regex` with a small `size_limit` for user and model patterns (Wilco find, lint filters) |
| Evidence at scale | Android: about 0.2 memory-safety vulnerabilities per MLOC in Rust against about 1,000 in C/C++, "a more than 1000x reduction"; for medium and large changes, "the rollback rate of Rust changes in Android is ~4x lower than C++"; "about 25% less time in code review" (2025-11-13) [V-author] | Supports the Rust-only choice | — |

## 3. Weaknesses and limits

Impact is for Plotroom, with the reason. **High**: likely to cost users' work or security, or the owner's daily time, unless handled.
**Medium**: real but bounded by an existing design choice. **Low**: already avoided or rare.

### 3.1 Boundaries of the safety promise

| Id | Weakness | Evidence | Impact |
| --- | --- | --- | --- |
| 68-W1 | Panics are crashes: indexing, `unwrap`, division by zero, and panics inside std (incorrect `Ord` in sort, `RefCell` double borrow, double `Mutex` lock) | §1.3 [V]. Cloudflare's 2025-11-18 outage: a generated file passed a hard limit of 200 features and the Rust proxy panicked with "called Result::unwrap() on an Err value"; the fix treats generated configuration "in the same way we would for user-generated input" [V] | **High**: Plotroom reads internet-downloaded missions and addons, model output and plugin output; a UI-thread panic loses unsaved work. Clippy lints catch our own `unwrap` and indexing, not panics inside std or dependencies |
| 68-W2 | Aborts skip every destructor and every `catch_unwind`: stack overflow, allocation failure, a panic in `Drop` during unwinding, `process::exit`, and a panic in a fire-and-forget rayon job | §1.3 [V]; Windows main thread 1 MB [V]; stack overflow ends the process [V, probe]; a rayon `spawn` panic goes to the pool's panic handler, whose default "is to abort the process" [V] | **High**: recursive parsers on hostile nesting and hostile element counts turn into an editor crash with no recovery hook; a panic hook does not run on these aborts [I]. The crash op journal, flushed per group and at idle (core-document-model §11), limits the loss [I] |
| 68-W3 | Integer overflow wraps silently in release; `as` truncates silently | §1.3 [V] | **Medium**: format crates deny `arithmetic_side_effects`; everything else (layout maths, ids, counters, sizes in export) wraps silently. A wrapped size can corrupt a saved file [I] |
| 68-W4 | Logic errors are unspecified and can differ between runs; nondeterminism across runs, platforms and toolchains | §1.3 [V]; `HashMap` iterates "in arbitrary order" with a randomly seeded SipHash 1-3 that is "subject to change" [V]; `f64::sin`, `exp`, `ln` and `powf` vary "by platform, Rust version" [V]; `rand` 0.10.3's `StdRng` is "Non-portable: any future library version may replace the algorithm and results may be platform-dependent" [V]; rayon float reductions are not deterministic [V] | **Medium**: seed-reproducible generation, golden journals, provenance hashes and "concurrency 1 and 8 give identical documents" (testing-strategy §9) depend on it. It stays medium because doc 43 §3.2's portability rules bound it once adopted; without them it would be high [I] |
| 68-W5 | Deadlocks, logical races, lock guards held by `match` temporaries, async cancellation, advisory poisoning | §1.3 [V] | **Medium**: the document has no locks by design (ui-shell §10); the risk sits in L7–L8 edges (providers, gamelink, MCP, downloads) |
| 68-W6 | Compiler bugs, soundness holes, and no LTS toolchain | §1.4 [V]; only the latest stable gets security fixes [V] | **Low** for ordinary code; **medium** for release timing and pins: never ship on a `.0` that later gets a miscompilation point release, and a pinned stable stops receiving security fixes when the next stable ships, about six weeks later [I]. Commercially supported, qualified toolchains exist [U]; Plotroom does not need one [I] |
| 68-W7 | Unsafe in dependencies and FFI; `forbid(unsafe_code)` misses unsafe emitted by any macro defined in another crate | §1.4 [V], [V, probe] | **Medium**: wgpu, winit, tokio, wasmtime and image decoders carry unsafe and C; our own claim must be phrased as "no `unsafe` token written in our crates" |

### 3.2 Supply chain and build-time code

| Id | Weakness | Evidence | Impact |
| --- | --- | --- | --- |
| 68-W8 | Build scripts and proc macros run arbitrary code; typosquats and account takeovers happen; editors run the same code | `arrayref@0.3.10` "had recently been republished and made to depend on" `proc-macro1`, which "had a build script that was downloading a malicious payload"; `append-only-vec@0.1.9` and `internment@0.8.7` by the same author were also compromised; the team deleted `proc-macro1`, `proc-macro-en`, `aovine`, `arone`, `aronenao` and `tinymember` (all versions); the three versions were online 86, 107 and 90 minutes; the author's "computer or credentials are likely compromised" (2026-08-20) [V]. rust-analyzer: "proc macros and build scripts are executed by default", ".cargo/config can override `rustc` with an arbitrary executable", "rust-toolchain.toml can override `rustc` with an arbitrary executable", and it "assumes that all code is trusted" [V] | **High**: a public GPL repository taking contributions, coding agents that propose dependencies, and contributors' machines, which hold credentials and game installs. Memory safety does not help here |

### 3.3 Productivity: build, IDE, learning

| Id | Weakness | Evidence | Impact |
| --- | --- | --- | --- |
| 68-W9 | Compile and link time, target-directory size | 2025 compiler performance survey: "over 3 700 responses", 55% wait more than ten seconds for incremental rebuilds, "Around 45%" of lapsed users cite compile times, "Almost 42%" tried no mitigation, satisfaction 6/10; top pains are workspace rebuilds, linking and uncached derive expansion [V-author] | **High**: 68 product crates in crate-map §3–§11, plus xtask, `plotroom-testkit`, `plotroom-script-oracle`, `plotroom-plugin-sdk` and `plotroom-plugin-testkit` in §12 [V]; Windows `link.exe`; many test binaries (the research workspace's README reports 406 tests in 146 test binaries [V]); no CI build cache yet (ci.yml has no cache step) [V, working tree]; every agent round and CI job pays it |
| 68-W10 | IDE and Cargo block each other; rust-analyzer memory; parallel agents share or duplicate artifacts | "More than 35%" call IDE and Cargo "blocking one another" a major issue [V-author]; cargo#16804: "Multiple Cargo instances cannot share build artifacts safely", 457 disk-exhaustion events and 3,703 compile failures from artifact corruption over 4,440 sessions, 105 GB in one project with 26 worktrees (self-reported; closed as duplicate of #5026) [V] | **Medium**: the owner and agents work on one Windows machine, sometimes in parallel worktrees |
| 68-W11 | Learning curve and borrow-checker friction: conditional returns of references (NLL case #3), helpers that borrow all of `&mut self`, self-referential structs, lifetimes spreading through APIs | Polonius alpha is still a nightly prototype, with "Stabilize and model Polonius Alpha" a 2026 large goal (§1.1) [V]; "View types experiment" is a 2026 goal [V] | **Medium**: the id-and-arena document model and split UI state (core-document-model; ui-shell §9) avoid most of it; contributors and weak models still meet it |
| 68-W12 | Async complexity: no `dyn` async traits on stable, no `Send` bounds on async trait methods without RTN, cancellation by drop | "Native async fn dynamic dispatch in traits" and "Prepare TAIT + RTN for stabilization" are 2026 goals [V] | **Low–medium**: tokio is confined to L7–L8 and the harness is synchronous (crate-map §2.3) |
| 68-W13 | Trait-bound errors are long; macros are opaque to people and agents; diagnostic attributes fail softly | Doc 62 §3 and doc 64 §4.5 measured where guidance lands and which errors get fixed [V per docs 62, 64] | **Medium**: covered by `AGENTS.md` "Diagnostics as Guidance"; the residue is macros and hint-less errors |

### 3.4 Ecosystem, platform and tooling

| Id | Weakness | Evidence | Impact |
| --- | --- | --- | --- |
| 68-W14 | Churn: fast-moving GUI crates, lint and diagnostic changes on toolchain bumps | wgpu majors 28→29→30 within 7 months, egui breaking minors every 2–3 months [V per doc 06 §6]; §1.5 [V] | **Medium**: UI crates and trybuild snapshots churn; the quarterly upgrade day (doc 06) is the budget |
| 68-W15 | No stable ABI | No 2026 goal (§1.1) [V] | **Low**: plugin tier T1 is WebAssembly (D007); native inference engines run out of process by default (D022 item 2), and architecture README §7 row 13 proposes always out of process |
| 68-W16 | Windows friction: `link.exe` default, antivirus scans of `target/`, Dev Drive needs Windows 11, MSVC Build Tools licence, long paths | §1.1 [V]; Dev Drive needs "Windows 11, Build #10.0.22621.2338 or later" [V]; the owner's host is Windows 10 (no Dev Drive) [V, probe host] | **High** for the owner's daily loop; **low** for users |
| 68-W17 | Deep verification tools are nightly or Unix-first | cargo-fuzz's README: "only on Unix-like operating systems (not Windows)", while the Fuzz Book says Windows works "thanks to the MSVC AddressSanitizer" [V, conflicting]; Kani easy install only Linux x86_64 and macOS [V]; the sanitizers are unstable, with "Stabilize MemorySanitizer and ThreadSanitizer Support" a 2026 goal [V] | **Low–medium**: run deep checks on Linux CI; keep harness bodies runnable under stable `cargo test` |
| 68-W18 | Debugger experience | The 2026 debugging survey: "At slightly over 74%, poor representation of values was the most common pain point" [V] | **Low**: tests are the evidence (`AGENTS.md`); good `Debug` and `Display` on newtypes |
| 68-W19 | Desktop GUI maturity: IME, fonts, accessibility | A 2025 survey of 43 GUI libraries found egui visible to Windows Narrator, while its default font lacked kana and kanji and a Tab press that should pick a kanji candidate "gets eaten by egui" [V-author] | **Medium**: M0's exit evidence already requires a Japanese IME note and an Accessibility Insights check (roadmap M0 item 3); `plotroom-fonts` plans a TTF fallback for CJK (crate-map §11) |

### 3.5 Further limits: features, paths, secrets, coherence, reflection, people, text

| Id | Weakness | Evidence | Impact |
| --- | --- | --- | --- |
| 68-W20 | Cargo features are additive and unified across the build: one crate enabling a dependency's feature changes it for every crate | serde_json's `Map::sort_keys`: "If serde_json's 'preserve_order' feature is not enabled, this method does no work because all JSON maps are always kept in a sorted state" [V], so one crate that enables `preserve_order` changes the key order of every `serde_json::Map` in the build [I]; per-package feature unification requires nightly (§1.1) [V] | **Medium**: canonical JSON for provenance hashes, cassettes and journals |
| 68-W21 | Host paths in binaries and diagnostics | §1.3 "Host paths" [V]; `AGENTS.md` Error Design forbids letting "host paths and user names reach" models, plugins or external agents | **Medium**: panic payloads, backtraces, crash reports and release debuginfo (68 OQ 7) carry them unless remapped [I] |
| 68-W22 | Derived defaults leak: a derived `Debug` prints every field, secrets included, into logs, panic messages and crash reports; the language has no secret type or lint for this [I] | 68-P25 asks for `Debug` on every newtype; provider keys and plugin tokens live in the OS keyring through `plotroom-io::secrets` (crate-map §2.3) but pass through memory as values [I] | **Medium** |
| 68-W23 | The orphan rule: a foreign trait cannot be implemented for a foreign type | The Reference: an `impl` is valid only if "`Trait` is a local trait" or at least one of the types "must be a local type" (with the uncovered-parameter condition) [V] | **Medium**: decides where serde and schemars derives live across the crate graph, and whether L0 types depend on serde and schemars or use feature gates; bears on §5 rank 6 |
| 68-W24 | No runtime reflection: property inspectors, schema generation and field-level diffs need derives or hand-written tables [I] | §5 rank 6 relies on derives; 68-P19 discourages in-house proc macros | **Medium**: a tension to decide (68-G13) |
| 68-W25 | Contributor pool: the game's modding community mostly writes the game's script language, C++ or Python, so a Rust core narrows who can contribute to the core [I] | — | **Medium**: bounded by plugins in any language compiled to WebAssembly (D007), SKILL.md styles and data-driven content |
| 68-W26 | Text and path semantics: `String` is always UTF-8 while the legacy files use code pages; Windows paths are `OsStr`; `to_string_lossy` replaces characters silently [I] | crate-map §3: `plotroom-encoding` handles "Legacy code pages and UTF-8"; D017's lossless CST keeps bytes | **Low**: already designed around |
| 68-W27 | One production compiler and a young specification [U] | Not verified in this pass | **Low** [U] |

## 4. The playbook

### 4.1 How to read it

One row per mitigation, ordered by weakness. **Class**: Eliminate, Reduce, Accept and monitor (see Names). **Rank** within a weakness
is by effect over cost, best first; §4.5 orders the work across weaknesses. **Status**: decided, proposed, working tree, missing. Every
row is a proposal unless its status says decided [I].

### 4.2 Mitigations

| Id | For | Mitigation (rank 1 first) | Class | Setting, tool or pattern | Status |
| --- | --- | --- | --- | --- | --- |
| 68-P1 | 68-W1, 68-W2 | Panic and crash policy: (1) keep `panic = "unwind"`; (2) `catch_unwind` only at job boundaries (a generation step, an import, a validation shard, a plugin or model call), turning a panic into a typed internal-error finding and a "this job failed" card; the job works on an immutable snapshot plus a private draft, a caught panic drops the draft uncommitted, and `AssertUnwindSafe` wraps only state that is discarded; (3) rayon: `join` and `scope` propagate a closure's panic to the caller [V], so they sit inside a boundary; fire-and-forget jobs have no caller and the default panic handler "is to abort the process" [V], so the one global pool is built at start-up with `ThreadPoolBuilder::new().thread_name(..).stack_size(N).panic_handler(h).build_global()`, where `h` records a typed job-failed finding, and `rayon::spawn`, `rayon::spawn_fifo` and `rayon::ThreadPool::spawn` are banned in favour of a workspace job-spawn wrapper that runs the closure under `catch_unwind`; (4) tokio: a dropped `JoinHandle` "*detaches* the associated task" and its outcome is lost [V], so no job's handle is dropped: `JoinSet` and `JoinError::is_panic` ("Returns true if the error was caused by the task panicking") [V]; (5) unclean exits are detected by a session sentinel written at start-up and removed on a clean exit, which triggers journal recovery at the next start (core-document-model §11), because a panic hook never runs on the aborts of 68-W2 and does run for panics a boundary later contains [I]; the hook, installed in `plotroom-app`, only records details (backtrace, thread name) in a per-session local log written through `plotroom-io`; the finding carries only a typed internal-error code, never the payload or paths (68-P28); (6) durability never in `Drop`: the crash op journal is already flushed per group and at idle; (7) `Drop` impls never panic; `main` returns `ExitCode`; `process::exit` is banned | Reduce | `[profile.release] panic = "unwind"` (explicit); `clippy.toml` bans `std::process::exit` and the rayon spawn functions; a test that a panic in a spawned job yields a finding and the process keeps running | Missing (crash journal proposed: core-document-model §11; M2 exit item 10) |
| 68-P2 | 68-W2 | Depth caps and stacks: every recursive parser, evaluator and tree builder over untrusted or model-produced input has a named constant, an `Error::NestingTooDeep { depth, limit }` and tests at cap and cap+1; deep-nesting fuzz seeds; each cap is sized against the smallest stack that any walker of the parsed tree runs on (the parser's thread, a UI tree view such as a config-class outliner on the 1 MB Windows main thread, and derived `Drop`, `Debug`, `Clone`, `PartialEq` and `Serialize`), measured in the dev profile on the Windows leg, where frames are largest; deep trees get an iterative `Drop` or a cap low enough for recursive derives (serde_json warns about `Drop`, `Debug` and `Display` [V]); every thread and pool the workspace creates has a name and an explicit stack size (`std::thread::Builder::stack_size`; rayon `ThreadPoolBuilder::stack_size`, "Sets the stack size of the worker threads" [V]; tokio `Builder::thread_stack_size`, default "2 MiB" [V]), and the pools are built in one place (`plotroom-session`); open and import parsing leave the UI thread (changes ui-shell §9–§10; 68-G2); `clippy::large_stack_arrays` at deny in parser crates; every dependency parser fed untrusted input (plugin-manifest TOML, SKILL.md front matter, model JSON) has its own depth limit checked [U] | Eliminate (own parsers) / Reduce (the process) | `clippy.toml` bans `std::thread::spawn` and `std::thread::Scope::spawn`, with reasons naming `Builder::spawn` and `Builder::spawn_scoped`; a test helper that runs a parser on a small stack; optionally a larger main-thread stack for the app on MSVC (`cargo:rustc-link-arg-bins=/STACK:...`) [I] | Partly proposed (doc 07 §4.2 plans a cap on preprocessor include depth); rule missing |
| 68-P3 | 68-W2 | Allocation caps: every input-sized allocation has its in-memory byte size (`count × size_of::<T>()` with `checked_mul`) capped against a named limit before it allocates, because a 1-byte on-disk element can become a 48-byte struct; element counts are also clamped to what the remaining bytes can hold, with `checked_div`, and a zero minimum element size gets its own cap; declared decompressed sizes (LZSS in PBOs) get an absolute cap and a ratio cap (doc 07 §16); `try_reserve` is a second line only, since on an overcommitting OS a reservation that succeeds can still fail when touched [I]; so a hostile count becomes an `Error`, never an abort | Eliminate (own parsers) / Reduce (dependencies) | Amend `AGENTS.md` heap rule 4 (Findings); an adversarial test per parser with `u32::MAX` counts | Partly decided (D017 item 3: "caps on every count and size"); doc 07 §16's caps table ("array count ≤ remaining bytes", "binary array ≤256 MiB" [V per doc 07]); byte-size, zero-size and `try_reserve` rules missing |
| 68-P4 | 68-W3 | (1) Checked arithmetic where input reaches (decided); (2) `overflow-checks = true` in the release profile as a backstop that turns a missed wrap into a panic, contained only under a job boundary (68-P1). It applies to the **whole dependency graph** unless an override says otherwise [V]: image and zlib decoders, egui tessellation and wgpu staging too, where it can block auto-vectorisation in hot loops [I] and turns a dependency's release-only wrap into a panic; on the UI thread outside a boundary it trades a glitch for a crash, softened by the crash journal [I]. A measured variant is `[profile.release.package."*"] overflow-checks = false`: our code, and dependency generics instantiated in it, stay checked; (3) arithmetic rule: `checked_*` returning a structured `Error` for sizes and offsets from input; `saturating_*` only where a clamped value is the intended result (a UI clamp), because a saturated size is wrong but plausible and can pass later checks [I]; `strict_*` (1.91 [V]) only as the per-site alternative if 68 OQ 1 rejects release overflow checks, since it panics in every build | Reduce | Probe: with release checks on for the graph and off for one library, a generic function from that library panicked when instantiated in a checked crate, while its non-generic function wrapped [V, probe], as the Cargo book predicts: "The location where generic code is instantiated will influence the optimization settings used for that generic code" [V]; the reverse direction and `#[inline]` non-generic functions, which are also compiled in the calling crate, were not probed [I] | Missing; owner decision (68 OQ 1); item (3) amends `AGENTS.md` "Integer Overflow Safety" (§4.4) |
| 68-P5 | 68-W3 | Cast lints in format crates: `cast_possible_truncation`, `cast_sign_loss`, `cast_possible_wrap` (all pedantic [V]) at deny beside `arithmetic_side_effects`; `TryFrom` for narrowing; `clippy::as_conversions` (restriction [V]) is the stricter option, forbidding every `as` | Eliminate (in format crates) | Crate-level `#![deny(...)]`, because cargo refuses to mix `workspace = true` with a crate's own lints ("cannot override `workspace.lints` in `lints`", cargo#13157, open) [V]; an `xtask` check that every L1 crate's `lib.rs` carries the set (§4.3) | Missing |
| 68-P6 | 68-W1, 68-W4 | Hand-written `Ord`, `Eq` and `Hash` are property-tested for consistency, or derived; no `RefCell` graphs | Reduce | proptest in the crate that defines the type | Missing |
| 68-P7 | 68-W4, 68-W20 | Determinism: anything serialised, hashed or seeded iterates `BTreeMap` or an insertion-ordered map, never `HashMap` order; float reductions in seeded paths stay sequential; seeded and hashed paths call no std transcendental float function (`sin`, `cos`, `powf`, `exp`, `ln`, …): integer or fixed-point maths, or a pinned pure-Rust implementation such as `libm` [I], enforced by `disallowed-methods` entries in the seeded crates or an `xtask` scan (68 OQ 18); sampling libraries such as `rand_distr` call these functions internally [I]; one pinned ChaCha RNG behind a newtype with test vectors, never `StdRng` (doc 43 §3.2, RAT3); golden-seed outputs byte-identical across the 3-OS CI matrix and re-checked on every toolchain bump; the `algebraic_*` float methods (1.98 [V]) stay out of seeded crates; SipHash stays for keys from untrusted files | Reduce | Tests already planned: concurrency 1 and 8 identical (testing-strategy §9); a run-twice test per seeded crate; golden seeds compared on all three OSes | Partly proposed (doc 43 §3.2; testing-strategy §9) |
| 68-P8 | 68-W5 | Concurrency rules: one owner per piece of state, messages instead of shared locks (proposed); bind guards with `let`, never in a `match` scrutinee (clippy `significant_drop_in_scrutinee`, nursery [V], trialled locally in the L7 edge crates and promoted to deny if quiet, since nursery lints can misfire); no guard across `.await` (`await_holding_lock` is a `suspicious` lint [V], so it warns by default and CI fails on warnings); only cancel-safe calls inside `select!`; user-cancellable CPU jobs on rayon with a cooperative token, not `spawn_blocking` | Reduce | Code rules (§4.4); a cancel-mid-stream test for each streaming reader | Partly proposed (ui-shell §10, agent-runtime §3) |
| 68-P9 | 68-W6, 68-W14, 68-W27 | Toolchain policy: exact stable pinned in CI and `rust-version` equal to it (MSRV = pin); **N-1 adoption**: move to stable N, on its latest point release, when N+1 ships; take security point releases within a week, which means moving to the latest stable, since only it gets security fixes [V]; each bump is its own change set with full 3-OS gates and a reviewed trybuild re-bless; a beta canary (non-blocking; clippy, unit tests and UI tests on beta, which is the next stable 0–6 weeks out) and a nightly job that only uploads the UI-test diff as an artifact and never reports red; the UI-test job installs `rust-src`; an `xtask hygiene` check that ci.yml's `RUST_TOOLCHAIN` equals `[workspace.package] rust-version` (and fuzz.yml's dated nightly, once pinned); final gates and trybuild re-blesses run on the pin (`cargo +<pin> …`, or an `xtask` wrapper that reads it from `Cargo.toml`) | Reduce | Point releases from 1.91 to 1.98 [V]: 1.91.1 after 11 days, 1.93.1 after 21, 1.94.1 after 21 (the Cargo CVE fixes), 1.96.1 after 33, 1.97.1 after 7, 1.98.1 after 14 (the miscompilation); six of those eight releases had one, all before N+1 at about day 42. The first draft's rule ("first point release or 14 days, whichever is first") would have adopted 1.93.0, 1.94.0 and 1.96.0 before their fixes; "four weeks after N, on its latest point release" would have missed only 1.96.1 [I]. CI variable (the skeleton's `RUST_TOOLCHAIN`); no root `rust-toolchain.toml` (§4.3) | Working tree: CI pin and `rust-version = "1.98.1"` [V, working tree]; policy missing |
| 68-P10 | 68-W7, 68-W8 | Supply chain: (1) committed `Cargo.lock` and `--locked` (decided); (2) cargo-deny `[bans.build]`: `allow-build-scripts` seeded with the six crates that have build scripts in today's lockfile (an empty list means "no crate is allowed to have a build script" [V]), growing one reviewed entry at a time and re-checked whenever `Cargo.lock` changes; `executables` deny (the default [V]); `include-workspace` "defaults to false" [V], so our own future build scripts are reviewed separately; a planted-fixture negative test (an unlisted build script must be rejected), like the planted GPL-2.0-only fixture; `wildcards = "deny"` with `allow-wildcard-paths = true`; per-layer feature bans; (3) a proc-macro allowlist checked by `xtask` from `cargo metadata`, seeded with `serde_derive`: `allow-build-scripts` does not cover proc macros (its `bypass` "only applies to crate with build scripts, not proc macros" [V]), but this is a **partial** measure, since no allowlist can see unsafe from a dependency's `macro_rules!` [V, probe]; unsafe inside dependency macros is a dependency-review question (items 8 and 10); a mechanical check, if wanted, is a nightly job that runs `cargo +nightly rustc -p <crate> -- -Zunpretty=expanded` and flags `unsafe` in the expansion against an allowlist [I]; (4) once the pinned Cargo is 1.100 or later, a publish-age cooldown: `[registry] global-min-publish-age = "7 days"`, overridden with `CARGO_RESOLVER_INCOMPATIBLE_PUBLISH_AGE=allow` for an urgent fix; it does not affect `cargo install` [V]; (5) CI tools installed with an exact version and `--locked` (`cargo install cargo-fuzz@<version> --locked`), because the cooldown does not cover them; third-party GitHub Actions pinned by commit SHA with the tag as a comment; `permissions: contents: read` kept; (6) release binaries built with `cargo auditable`, which embeds "data about the dependency tree in JSON format into a dedicated linker section" [V]; (7) a scheduled latest-dependencies job; (8) every new dependency, added by a person or a coding agent, is reviewed by a person before merge; Wilco and plugins have no dependency tool by construction (D006, D007); (9) advisories split from the blocking gate (§4.3); (10) cargo-vet only if the owner accepts its audit load | Reduce | §4.3 `deny.toml`; `xtask` checks; workflow pins | Working tree: licences, crates.io-only sources, `yanked = "deny"`, `permissions: contents: read` [V, working tree]; rest missing |
| 68-P11 | 68-W7 | Dependency unsafe: prefer pure-Rust, safe decoders for PAA, textures and audio; keep native engines out of process: out of process by default is decided (D022 item 2), always out of process (a supervised helper) is proposed (architecture README §7 row 13; agent-runtime §3), and §1.3's FFI rows support that stricter rule; an optional weekly Miri job over the L0–L1 crates' tests on Linux nightly | Reduce | Separate workflow, never a required gate | Partly decided (D022 item 2) |
| 68-P12 | 68-W9 | Compile time: (1) dev debuginfo cut to `line-tables-only`, dependencies without debuginfo, a `debugging` profile for debugger sessions (the Cargo book's own snippet [V]); (2) one integration-test binary per crate (`tests/it/main.rs` plus modules): each file in `tests/` is its own binary, and "rustc needs to repeatedly re-link the library crate with each of the integration tests" [V]; unit tests preferred; (3) thin generic shells over non-generic inner functions; proc macros kept out of L0–L1; (4) a `profiling` profile with thin LTO; (5) a CI build cache: a cargo cache action pinned by commit SHA, saved only on `main` to limit cache poisoning from pull requests, with `CARGO_INCREMENTAL=0` [I]; a Dev Drive on the Windows runners is optional, since 68-W16's Windows 10 limit is the owner's, not CI's [I]; (6) measurement: the owner runs `cargo build --timings`; agents use `cargo check --timings` or `cargo test -p <crate> --timings`, because `AGENTS.md` forbids them `cargo build`. Dependency `opt-level` in dev is not in this item: see the trade-off note below the table | Reduce | §4.3 profiles; a ci.yml cache step | Missing |
| 68-P13 | 68-W9, 68-W10 | Warnings gate without cache churn: gates use `CARGO_BUILD_WARNINGS=deny` instead of `-- -D warnings`, with `--keep-going` in CI so one run shows every crate's warnings [V]; the fast inner loop becomes `CARGO_BUILD_WARNINGS=deny cargo clippy -p <crate> --all-targets`; the same change applies to `AGENTS.md` ("Lint", "Fast inner loop"), ci.yml's clippy step, testing-strategy §14 row 1, roadmap M0 scope and `CODE-INDEX.md` §2. The setting "doesn't invalidate the underlying build cache" (1.97 post) [V]; probe: a clippy warning failed the run with "warnings are denied by `build.warnings` configuration" and the re-run reused the cache, while toggling `-- -D warnings` re-checked the crate [V, probe]. **It is stricter in one way:** `-D warnings` ignores `linker_messages`, while `build.warnings = deny` fails on a linker warning (probe: LNK4044, exit 101 against exit 0) [V, probe]; `cargo test` links while clippy does not, so an MSVC, ld or rust-lld warning on any OS leg, including the 68-P14 rust-lld trial, would fail the gate. The choice is explicit: treat linker warnings as real, or set `[workspace.lints.rust] linker_messages = "allow"` with its reason recorded; measure first (68 OQ 16). It fails a round on an unused import exactly as `-D warnings` does, so doc 64 §5.1's weak-model caveat is unchanged. Keep deny-level `[lints]` for guidance lints: under `build.warnings` the lint text stays at warning level for errors-only feeds. The cache benefit is local today; CI gains it once it caches builds (68-P12) | Reduce | Amend `AGENTS.md` commands and the other places above (Findings) | Missing |
| 68-P14 | 68-W16 | Windows loop: (1) try `rust-lld.exe` as the MSVC linker in the owner's user-level Cargo config (Bevy's snippet [V]), measured against `link.exe`, with release packaging verified under `link.exe` because of #85642; (2) a short checkout path; (3) Defender: folder exclusions for `target/` and `CARGO_HOME` trade scan coverage for speed, and Dev Drive needs Windows 11: owner decision | Reduce / accept | User config, not a root `.cargo/config.toml` | Missing |
| 68-P15 | 68-W10 | rust-analyzer: `check.command = "clippy"`, `cargo.targetDir = true` (a separate directory, so rust-analyzer's checks do not lock `Cargo.lock` [V]), `check.workspace = false`, shipped as editor settings (the book calls `rust-analyzer.toml` "a work in progress" [V]) | Reduce | `.vscode/settings.json` or CONTRIBUTING text | Proposed in part (doc 62 §4.3) |
| 68-P16 | 68-W10 | Parallel agent worktrees: keep the default per-worktree `target/`, which already isolates worktrees, plus rust-analyzer's `cargo.targetDir = true`; set no global `build.build-dir`: its default is "the value of `build.target-dir`" [V], and an explicit one would pull rust-analyzer's intermediate artifacts back beside the CLI's, bringing back lock contention and mutual rebuilds (rust-analyzer checks with `-p`, the gates with `--workspace`) [I]; to cut the real cost, N cold dependency builds, trial sccache as a user-level `build.rustc-wrapper` ("can be used to share built dependencies across different workspaces" [V]), measured first; it caches dependencies rather than incremental workspace crates [I], and stays out of CI if a cargo cache action is used there; never share one `target/` between concurrent cargo processes | Reduce | User-level config | Missing |
| 68-P17 | 68-W11 | Borrow-friendly design: typed ids into arenas and persistent maps; owned data at crate and model boundaries; `'input` lifetimes only inside L1 parsers; state split into disjoint structs; no self-referential structs | Eliminate (most cases) | Architecture (core-document-model §3–§6; ui-shell §9) | Proposed |
| 68-P18 | 68-W12 | Async confinement: tokio only in L7–L8; no `async fn` in `dyn` traits, explicit `Pin<Box<dyn Future + Send>>` at seams; `large_futures` (pedantic [V]) in edge crates; box known-large sub-futures | Reduce | crate-map §2.3 (proposed); crate-level lint | Proposed in part |
| 68-P19 | 68-W13 | Macros and diagnostics: prefer functions and generics over in-house proc macros; small `macro_rules!` only; guidance text guarded by trybuild snapshots (decided); the reflection substitute of 68-P31 is the open exception (68-G13) | Reduce | Code rule | Partly decided |
| 68-P20 | 68-W13, 68-W4 | Exhaustiveness: `wildcard_enum_match_arm` (restriction [V]) at deny in domain crates (commands, validate, session, workflow, decide); `#[non_exhaustive]` only on enums that cross the plugin or wire boundary | Eliminate (in those crates) | Crate-level `#![deny]`, checked by `xtask` | Missing |
| 68-P21 | 68-W14 | Churn: exact pins for fast movers at the edge (wgpu through egui-wgpu, rig, llama-cpp-2, wasmtime on its LTS line) and a quarterly upgrade day (doc 06 §6; D007) | Accept and monitor | Pins and a calendar | Proposed |
| 68-P22 | 68-W17 | Verification tiers: proptest with a fixed `PROPTEST_RNG_SEED` in PR CI and the default `proptest-regressions` failure files committed [V], paired with a nightly random-seed run at a higher `PROPTEST_CASES` whose failures are committed as regression files; cargo-fuzz nightly on Linux (`--sanitizer none` for targets with no unsafe and no C calls: "A speedup of 2x can be expected" [V]); `cargo mutants` on parser PRs (`git diff origin/main... > pr.diff && cargo mutants --in-diff pr.diff -p <crate>`), noting that "a diff that only deletes or changes test code won't cause any mutants to run" [V]; nextest optional, with doctests in a separate `cargo test --doc` step ("Doctests are currently not supported" [V]); Kani later for read helpers | Reduce | Workflows (§4.3) | Partly decided (fuzz: D017; proptest round trips: D017 Consequences) |
| 68-P23 | 68-W13 | Snapshot discipline: agent loops and CI run with `INSTA_UPDATE=no`; `TRYBUILD=overwrite` ("write all compiler output directly in place") and `INSTA_FORCE_PASS` are reviewed contract changes; `--unreferenced=reject` in CI [V] | Eliminate (silent re-bless) | Environment in CI and the agent wrapper | Missing (FR-C-030 open) |
| 68-P24 | 68-W15 | Plugin tier T1 as WebAssembly components; native engines as processes; `Module::deserialize` is already a compile error under the workspace `forbid(unsafe_code)`, so no new rule is needed | Eliminate | D007, D022 | Decided in part (plugin tier T1 as WebAssembly: D007; out of process by default: D022 item 2); helper-process rule proposed |
| 68-P25 | 68-W18 | `Debug` and `Display` on every newtype except secret-bearing ones (68-P29); tests as evidence | Accept and monitor | `AGENTS.md` newtype rule (decided) | Decided |
| 68-P26 | 68-W19 | M0 IME and accessibility checks; a CJK TTF fallback (crate-map §11) | Accept and monitor | Roadmap M0 item 3; `plotroom-fonts` | Proposed |
| 68-P27 | 68-W20 | Feature hygiene: `deny.toml` `[bans] features` entries (cargo-deny allows "crate specific allow/deny lists of features" [V]) for features that change shared behaviour, such as serde_json `preserve_order` and `arbitrary_precision`, unless decided; `cargo tree -e features` in every dependency review; canonical serialisation sorts explicitly rather than relying on a feature | Reduce | `deny.toml` | Missing |
| 68-P28 | 68-W21 | Path hygiene: shipped binaries are built only in CI, with `--remap-path-prefix` for the workspace root and `CARGO_HOME` [V]; crash details and backtraces pass through the shared display sanitizer and a path scrubber before any model, plugin or bug report sees them; `trim-paths` is adopted when it stabilises (a canary item) | Reduce | Release job; the diagnostics crate | Missing; links 68 OQ 7 |
| 68-P29 | 68-W22 | Secret newtypes (provider keys, plugin tokens): a hand-written redacting `Debug`, never `Display` or `Serialize`; trybuild cases proving `SecretKey: !Display` and `!Serialize` | Eliminate (for secret types) | Exception to the newtype rule (§4.4); trybuild | Missing |
| 68-P30 | 68-W23 | Coherence: domain types and their serde and schemars derives live in the lowest crate that owns them, behind no optional feature; newtypes wrap foreign types that need foreign traits | Reduce | crate-map layering | Missing |
| 68-P31 | 68-W24 | Reflection substitute: one derive family from the ecosystem (serde plus schemars) feeds inspectors, schemas and diffs, with small `macro_rules!` tables where a derive does not fit; its tension with 68-P19 is 68-G13 | Reduce | §5 rank 6 | Missing |
| 68-P32 | 68-W25 | Contributor pool: plugins in any language that compiles to WebAssembly components (D007), SKILL.md styles and data-driven content need no Rust; typed APIs and `AGENTS.md` lower the bar for Rust contributors | Accept and monitor | D007; styles and packs | Decided in part (D007) |
| 68-P33 | 68-W26 | Text and paths: `plotroom-encoding` for legacy code pages; bytes stay bytes until decoded (D017's lossless CST); `to_string_lossy` and `from_utf8_lossy` banned on save paths (`disallowed-methods` in the format and save crates) | Reduce | `clippy.toml` | Proposed in part (crate-map §3; D017) |

**Trade-off note: dependency `opt-level` in dev** (68 OQ 12). Optimised dependencies in dev speed up dependency code in debug runs,
not Plotroom's own: `"*"` matches "all dependencies (but not any workspace member)" [V], so our parsers and renderer stay at
`opt-level` 0, and generic dependency code monomorphised in our crates uses our crates' level [V]. The setting also adds compile time
on every clean or cold build (CI without a cache, each new worktree, each dependency bump), and because `package."*"` comes before
`build-override` in Cargo's "first match wins" order [V], it would compile syn, quote, proc-macro2 and serde_derive optimised too [I].
Bevy sets `opt-level = 1` for its own code and `3` for dependencies [V]; the Cargo book suggests trying `opt-level = 1`, which applies
some optimisations "while still allowing monomorphized items to be shared" [V]. If faster debug runs are needed: named overrides for
runtime-heavy crates (`[profile.dev.package.wgpu]`, image and zlib decoders) or `[profile.dev] opt-level = 1`, in a local, uncommitted
profile first, with clean and incremental times measured.

### 4.3 Draft configuration for the M0 workspace (proposal)

**What the skeleton already has** [V, working tree]: the workspace lints of crate-map §2.4 plus `disallowed_methods` and
`disallowed_types` at deny; release `lto = true` and `codegen-units = 1`; `resolver = "3"` and `rust-version = "1.98.1"`; a root
`clippy.toml` with the unwrap, expect, indexing and panic test allowances and the capability bans; a `deny.toml` with the licence
allowlist, `[graph] all-features = true`, crates.io-only sources, `yanked = "deny"` and `multiple-versions = "warn"`; ci.yml, which
pins `RUST_TOOLCHAIN: "1.98.1"`, runs `cargo fmt --all --check`, `cargo clippy --workspace --all-targets --locked -- -D warnings`
(line 50) and `cargo test --workspace --locked` on `windows-latest`, `ubuntu-latest` and `macos-latest`, runs `xtask layers` and
`xtask hygiene`, and runs cargo-deny (`check advisories bans licenses sources` as one blocking step, plus the planted GPL-2.0-only
fixture); and fuzz.yml, which installs `nightly` unpinned, runs `cargo install cargo-fuzz --locked` with no version and runs `cargo
+nightly fuzz run` from the repository root. Actions are referenced by tag (`actions/checkout@v4`,
`EmbarkStudios/cargo-deny-action@v2`). Its comments record choices this doc keeps: format crates add
`#![deny(clippy::arithmetic_side_effects)]` in `lib.rs` because of cargo#13157, and there is **no root `rust-toolchain.toml` or
`.cargo/config.toml`**, because either would reach `tools/rust-weak-models` and a pin that names an uninstalled version starts a
download. The blocks below are **deltas** against it.

**`Cargo.toml` (deltas).**

```toml
[workspace.package]
publish = false        # every member sets `publish.workspace = true` (xtask layers checks it); see deny.toml's allow-wildcard-paths

[workspace.lints.rust]
# linker_messages: an explicit choice with 68-P13 (68 OQ 16). Either leave it at warn and treat linker warnings as real,
# or set `linker_messages = "allow"` and record the reason here.

[workspace.lints.clippy]
# ... the skeleton's set stays ...
print_stdout = "deny"  # binaries (plotroom-app, plotroom-cli, xtask) opt out with #![expect(clippy::print_stdout, reason = "...")]
print_stderr = "deny"
dbg_macro = "deny"

# Dev loop: file:line backtraces, no full debuginfo (the Cargo book's build-performance snippet).
[profile.dev]
debug = "line-tables-only"

[profile.dev.package."*"]
debug = false          # no opt-level here: see the trade-off note under §4.2 (68 OQ 12)

# For debugger sessions: `cargo build --profile debugging` (run by the owner). Whether `inherits` carries the dev profile's
# package."*" override, which would leave dependencies without debuginfo here too, is [U] (68 OQ 17).
[profile.debugging]
inherits = "dev"
debug = true
# [profile.debugging.package."*"]   # uncomment to step into dependencies
# debug = true
# opt-level = 0

# Release keeps AGENTS.md rule 7 (lto = true, codegen-units = 1) and adds two explicit settings.
[profile.release]
lto = true
codegen-units = 1
panic = "unwind"       # abort would ship a panic strategy no test ran and would make catch_unwind job boundaries impossible (68-P1)
overflow-checks = true # owner decision (68 OQ 1): applies to the whole dependency graph, not just our crates
# [profile.release.package."*"]
# overflow-checks = false   # measured variant (68 OQ 13): dependencies unchecked; our code and generics instantiated in it checked

# Local performance work without fat-LTO link times; never used to ship.
[profile.profiling]
inherits = "release"
lto = "thin"
codegen-units = 16
debug = true
```

Not proposed: `panic = "abort"` (§1.3), `opt-level = "z"`, UPX ("There have been times that UPX-packed binaries have flagged
heuristic-based antivirus software because malware often uses UPX" [V]), `-C target-cpu=native` (players' hardware is old [I]). Release
debuginfo for symbolised crash reports is 68 OQ 7.

**`.cargo/config.toml`: none at the root.** Settings that would go there move to three places [I]:

| Setting | Where | Why there |
| --- | --- | --- |
| `CARGO_BUILD_WARNINGS=deny`, `CARGO_INCREMENTAL=0`, `RUST_BACKTRACE=1`, `INSTA_UPDATE=no`, a fixed `PROPTEST_RNG_SEED` | CI workflow environment | CI-only; keeps the research workspace untouched |
| `[target.x86_64-pc-windows-msvc] linker = "rust-lld.exe"` (after measurement); sccache as `build.rustc-wrapper` (after measurement, 68-P16); after the pin reaches 1.100, `[registry] global-min-publish-age = "7 days"` [V] | The contributor's user-level `$CARGO_HOME/config.toml`, documented in CONTRIBUTING | Per-machine choices |
| `rust-analyzer.check.command`, `cargo.targetDir`, `check.workspace` | `.vscode/settings.json` or CONTRIBUTING | Editor settings, not Cargo |

**Toolchain and MSRV.** The CI pin names an exact stable (today 1.98.1) and `[workspace.package] rust-version` equals it
[V, working tree]. That is the Cargo book's simplest policy, "always use the latest Rust version", applied to a pinned version [V].
Clippy's `msrv` "Defaults to the `rust-version` field in `Cargo.toml`" [V], so MSRV = pin also fixes clippy's MSRV lints to the pin.
Resolver 3 treats dependency versions whose `rust-version` is newer than ours through `resolver.incompatible-rust-versions` (values
`allow` and `fallback` [V]), so the latest-dependencies job runs `CARGO_RESOLVER_INCOMPATIBLE_RUST_VERSIONS=allow cargo update` to
see versions that need a newer Rust [I]. Nothing checks today that ci.yml's pin and `rust-version` agree (a comment asks to bump both)
[V, working tree]; 68-P9's `xtask hygiene` check closes that. Without a root toolchain file, local gates and trybuild re-blesses run
on whatever stable is installed (1.99 after about 2026-10-01), so they run as `cargo +1.98.1 …` with `rust-src` installed for that
toolchain, or through an `xtask` wrapper that reads the pin from `Cargo.toml` [I]. The UI-test job installs `rust-src` so snapshots
match [V]. Precedence, for agents that override locally: `cargo +toolchain` beats `RUSTUP_TOOLCHAIN`, which beats a directory
override, which beats `rust-toolchain.toml`, except that "a `rust-toolchain.toml` file that is closer to the current directory will
be preferred over a directory override that is further away"; rustup finds toolchain files by walking up from the current directory
[V]. Bump rules are 68-P9.

**Fuzz toolchain.** fuzz.yml runs `cargo +nightly fuzz run` from the repository root, so a `fuzz/rust-toolchain.toml` would have no
effect twice over: `+nightly` outranks it, and rustup's search starts at the root, not in `fuzz/` [V]. The dated nightly therefore
goes into fuzz.yml, like the stable pin in ci.yml:

```yaml
# fuzz.yml (delta)
env:
  FUZZ_TOOLCHAIN: nightly-YYYY-MM-DD   # bumped deliberately, like RUST_TOOLCHAIN
steps:
  - run: |
      rustup toolchain install "$FUZZ_TOOLCHAIN" --profile minimal
      cargo install cargo-fuzz@<version> --locked
  - run: cargo +"$FUZZ_TOOLCHAIN" fuzz run ${{ matrix.target }} -- -max_total_time=600
# ci.yml (delta): the pinned toolchain gets rust-src for the UI-test job:
#   rustup toolchain install "$RUST_TOOLCHAIN" --profile minimal --component rustfmt,clippy,rust-src
```

cargo-fuzz needs no `rust-src` without build-std [I]; `llvm-tools-preview` only if `cargo fuzz coverage` is used [I]. A
`fuzz/rust-toolchain.toml` could still serve local runs from inside `fuzz/`, but only if fuzz.yml drops `+nightly` and sets
`working-directory: fuzz` [I].

**`deny.toml` (deltas).**

```toml
[bans]
wildcards = "deny"                 # no `*` version requirements (the default is warn)
allow-wildcard-paths = true        # path dependencies in private (publish = false) crates are not wildcards [V]
# features = [{ crate = "serde_json", deny = ["preserve_order", "arbitrary_precision"] }]   # 68-P27, unless decided
# deny = [...]                     # per-layer bans: tokio runtime, HTTP clients, egui, wgpu, wasmtime, rmcp (crate-map §2.5)

[bans.build]
# Seeded from the skeleton's Cargo.lock, reviewed 2026-09-28 [V, local registry]; each grows one reviewed entry at a time.
# Regenerate the list from `cargo metadata` when this block is applied, and re-check it whenever Cargo.lock changes.
# `executables` stays at its default, deny; `include-workspace` defaults to false.
allow-build-scripts = [
  "proc-macro2",   # runs rustc to probe compiler features and sets cfgs
  "quote",         # runs `rustc --version` to detect the diagnostic attribute namespace
  "serde",         # sets cfgs from the rustc version; writes to OUT_DIR
  "serde_core",    # the same as serde
  "serde_json",    # picks the arithmetic limb width from the target; spawns no process
  "zmij",          # runs `rustc --version` and reads OPT_LEVEL to set cfgs (serde_json's float formatting)
]

[advisories]
unmaintained = "workspace"         # only direct dependencies fail; the default "all" fails on deep transitive crates [V]
```

Without `allow-wildcard-paths`, the skeleton's `plotroom-testkit = { path = "crates/plotroom-testkit" }` and every later inter-crate
path dependency (the first in M1: `plotroom-config` → `plotroom-preproc`, crate-map §2.2) count as wildcards; the exemption covers
path `dependencies` only in private crates, while "path or git `dependencies` … in **public** crates will continue to produce
warnings and errors" [V], hence `publish = false` for every member. The alternative is an explicit `version` on every workspace path
dependency. The package-spec syntax of `allow-build-scripts` entries is to be checked against the pinned cargo-deny when applied [U].
`multiple-versions` stays `warn` until the graph is real, as the skeleton says [V, working tree]. The `xtask` proc-macro allowlist
(68-P10) is required, not optional: `allow-build-scripts` covers crates with build scripts only [V].

**`clippy.toml` (deltas to the one root file).** Clippy searches for its file in `CLIPPY_CONF_DIR`, then `CARGO_MANIFEST_DIR`, then
the current directory, and "will walk up the directory tree, searching each parent directory until it finds one" [V]; the first file
found is used and no merge is documented, which supports the skeleton's single root file [V; a probe could confirm no merge].
Additions:

```toml
allow-dbg-in-tests = true
allow-print-in-tests = true

disallowed-methods = [
  # ... the skeleton's capability bans stay ...
  { path = "std::process::exit", reason = "Return std::process::ExitCode from main: exit runs no destructors (68-P1)" },
  { path = "std::thread::spawn", reason = "Use std::thread::Builder with a name and an explicit stack_size: parsers recurse (68-P2)" },
  { path = "std::thread::Scope::spawn", reason = "Use std::thread::Builder::spawn_scoped with a name and an explicit stack_size (68-P2)" },
  { path = "rayon::spawn", reason = "Use the workspace job-spawn wrapper: it catches a panic and reports a job-failed finding, while rayon's default handler aborts the process (68-P1)" },
  { path = "rayon::spawn_fifo", reason = "Use the workspace job-spawn wrapper: it catches a panic and reports a job-failed finding, while rayon's default handler aborts the process (68-P1)" },
  { path = "rayon::ThreadPool::spawn", reason = "Use the workspace job-spawn wrapper: it catches a panic and reports a job-failed finding, while rayon's default handler aborts the process (68-P1)" },
]
```

`std::thread::scope` itself stays allowed, because `Builder::spawn_scoped` needs the `Scope` it creates [I].

**Crate-level lint attributes (deltas)**, since cargo#13157 forbids per-crate additions to inherited lints [V]. An `xtask` check
requires each set in the `lib.rs` of every crate of that layer or role (`xtask/layers.toml` already records both), so a new crate
cannot silently miss its set [I]. The print and `dbg!` lints are workspace-wide instead (above).

| Crates | Attribute | Why |
| --- | --- | --- |
| L1 format crates, `plotroom-bytes` | `#![deny(clippy::arithmetic_side_effects, clippy::cast_possible_truncation, clippy::cast_sign_loss, clippy::cast_possible_wrap, clippy::large_stack_arrays)]` (or `clippy::as_conversions` in place of the three cast lints) | 68-P2, 68-P4, 68-P5 |
| Domain crates (`plotroom-commands`, `-validate`, `-session`, `-workflow`, `-decide`) | `#![deny(clippy::wildcard_enum_match_arm)]` | 68-P20 |
| L7 edge crates with async | `#![deny(clippy::await_holding_lock, clippy::large_futures)]`; `clippy::significant_drop_in_scrutinee` after a quiet local trial | 68-P8, 68-P18 |

**An approved `unsafe` exception.** `unsafe_code = "forbid"` cannot be relaxed inside a crate that inherits it, and every crate sets
`lints.workspace = true` (crate-map §2.4; `CODE-INDEX.md` §3; the skeleton's `Cargo.toml` comment) [V, working tree]. The route
`AGENTS.md` allows ("explicit prior discussion and written approval") has two possible shapes, both a design decision (68-G11): (a) a
separate crate whose own `[lints]` table repeats the workspace set with `unsafe_code = "deny"`, plus an `xtask` check that the table
equals the workspace table except for `unsafe_code`, since the copy would otherwise drift silently; (b) keep `workspace = true`
everywhere, lower the workspace level to `unsafe_code = "deny"`, and let an `xtask` check allow `#[expect(unsafe_code, reason =
"...")]` only in allowlisted files. The trade-off: under (b) an `#[allow(unsafe_code)]` anywhere else is caught only by the `xtask`
check, not by the compiler [I].

**CI jobs (proposal, as a diff against the working tree; testing-strategy §14 stays the gate list).** All workflows: third-party
actions pinned by commit SHA with the tag as a comment, `permissions: contents: read` kept (68-P10).

| Job | Today (working tree) | Proposed delta |
| --- | --- | --- |
| Fast gates (ci.yml `check`: Windows, Ubuntu, macOS on Apple silicon) | fmt; clippy with `-- -D warnings`; `cargo test --workspace --locked` | Clippy and test under `CARGO_BUILD_WARNINGS=deny` with `--keep-going`, after the linker-warning choice (68-P13); a cargo cache step pinned by SHA, saved on `main` only (68-P12); doctests in a separate `cargo test --doc` if nextest is adopted |
| xtask (ci.yml) | `layers`, `hygiene` | Add the pin-consistency check (68-P9), the proc-macro allowlist (68-P10), the crate-level lint-set check (above) and the `publish.workspace` check |
| Supply chain (ci.yml `deny`) | `check advisories bans licenses sources` as one blocking step; the planted GPL-2.0-only fixture | Bans, licences and sources stay blocking on every push; advisories run non-blocking on pull requests (`continue-on-error`, as cargo-deny-action's README does, to "Prevent sudden announcement of a new advisory from failing ci" [V]) and blocking in a daily scheduled job that notifies the owner; a planted build-script fixture (68-P10) |
| UI tests | None yet | trybuild on the pinned toolchain with `rust-src`, on one OS (doc 62 OQ5) |
| Fuzz (fuzz.yml, nightly, Ubuntu) | Unpinned `nightly`; `cargo install cargo-fuzz --locked` with no version | `FUZZ_TOOLCHAIN` dated nightly; `cargo-fuzz@<version>` (above) |
| Beta canary | None | Weekly, non-blocking, Ubuntu: clippy, unit tests and UI tests on beta; failures are acted on before the next stable |
| Nightly UI diff | None | The UI-test output on nightly uploaded as an artifact, never reported red (the next solver changes trait-error text); install with `rustup toolchain install nightly --profile minimal -c clippy --allow-downgrade` [I] |
| Latest dependencies | None | Weekly, non-blocking, Ubuntu: `CARGO_RESOLVER_INCOMPATIBLE_RUST_VERSIONS=allow cargo update`, then the fast gates on the pin and on beta |
| Mutation | None | Pull requests touching L1, Ubuntu: `cargo mutants --in-diff pr.diff -p <crate>`, report only at first |
| Proptest random seeds | None | Nightly, Ubuntu: a random seed and a higher `PROPTEST_CASES`; failures committed as regression files |
| Deep checks | None | Weekly, optional, Ubuntu: Miri over L0–L1 tests; the `-Zunpretty=expanded` unsafe scan (68-P10); later Kani on the read helpers |
| Release | None | Tag, all three OSes: `cargo auditable build --release` with `--remap-path-prefix` (68-P28); packaging verified with each platform's default linker |
| Other gates | — | Unchanged: REUSE/SPDX, the DCO check, the public-hygiene grep and the `xtask` drift checks, as testing-strategy §14, D001 and D032 require |

### 4.4 Code rules the playbook would add to `AGENTS.md` (proposal)

`AGENTS.md` "Maintaining This File" asks for general rules, and FR-C-010 asks to move checkable rules into lints; FR-C-010 also
records the file as over its ~600-line ceiling, so each row below adds friction unless a lint or test carries it (68 OQ 4) [I].

| Rule | Where in `AGENTS.md` | Mechanical check |
| --- | --- | --- |
| "Every recursive function over untrusted or model-produced input has a named depth limit, returns a structured error at the limit, and is tested at the limit and one past it." | Parser Design Philosophy | Tests |
| "Every thread or pool the workspace creates has a name and an explicit stack size, and the pools are built in one place; parsing leaves the UI thread." | A new concurrency bullet, not Parser Design Philosophy, which defines parsers as pure functions; changes ui-shell §9–§10 | `std::thread::spawn` and `Scope::spawn` bans |
| "An input-sized allocation has its byte size capped before it allocates; `try_reserve` is a second line. Allocation failure aborts the process." | Heap Allocation Policy, rule 4 | Adversarial tests |
| "Durability never depends on `Drop`; `main` returns `ExitCode`; `catch_unwind` only at job boundaries; no fire-and-forget rayon or tokio job; `Drop` never panics." | New "Panics and aborts" subsection | `std::process::exit` and rayon spawn bans |
| "Bind lock guards with `let`; never lock in a `match` scrutinee or hold a guard across `.await`." | New concurrency bullet | `await_holding_lock` at deny in edge crates; `significant_drop_in_scrutinee` after a trial |
| "Sizes and offsets from input use checked arithmetic that returns a structured error; saturating arithmetic only where a clamped value is the intended result." | Integer Overflow Safety: amends "Use `saturating_add` (or `checked_add` where recovery is needed)" | `arithmetic_side_effects` in format crates |
| "`as` never narrows a value read from input; use `TryFrom`." | Integer Overflow Safety | Cast lints in format crates |
| "Nothing serialised, hashed or seeded depends on `HashMap` order, a std transcendental float function or a non-portable RNG." | Type Safety or a determinism bullet | Run-twice and cross-OS golden-seed tests |
| "`#[non_exhaustive]` only on enums that cross the plugin or wire boundary." | Exhaustive matching | Review; `wildcard_enum_match_arm` |
| "Secret-bearing newtypes implement a redacting `Debug` by hand and no `Display` or `Serialize`." | Newtype rule ("Implement `Display`") | trybuild cases |
| `#[inline]` is a hint; say so (Findings) | Heap Allocation Policy, rule 6 | — |
| Gates and the fast inner loop use `CARGO_BUILD_WARNINGS=deny` (68-P13) | Local Repo-Specific Rules ("Lint", "Fast inner loop") | — |
| Final gates and trybuild re-blesses run on the pinned toolchain (68-P9) | Local Repo-Specific Rules | The pin-consistency check |

### 4.5 Order of work across weaknesses (M0)

§4.2 ranks mitigations within a weakness; this list ranks the first steps across them by effect over cost and by what they block [I].

1. **Supply chain** (cheap; high 68-W8): the seeded build-script allowlist with its planted fixture, the advisories split, SHA-pinned
   actions and versioned `cargo install` (68-P10). Blocks nothing; due before outside contributions are accepted, which the roadmap
   ties to the DCO check being live (M3 section, OWQ-05).
2. **Before SP-09 lands**: the depth-cap, stack and allocation-cap rules with their tests (68-P2, 68-P3). SP-09's recursive, lossless
   config parser is the next parser, and its fuzz target is already wired into fuzz.yml; the rules are cheap before it and costly to
   retrofit. Blocks SP-09 and the M1 format crates.
3. **The panic policy** (68-P1), including the rayon panic handler, the job-spawn wrapper, the `JoinSet` rule and the session sentinel.
   Blocks the first crate that spawns jobs (validation on rayon) and M2 exit item 10 (crash recovery).
4. **The warnings gate and the toolchain pin**: measure linker warnings (68 OQ 16), then choose 68-P13's setting; add the
   pin-consistency check and the N-1 policy (68-P9). Due before the first toolchain bump (1.99).
5. **The release overflow-checks decision** (68 OQ 1) with its dependency-heavy measurements (68 OQ 13). Blocks the first release
   build.
6. **Profile tuning and CI caching** (68-P12, 68-P16) after M0 has crates to time (68 OQ 12).

## 5. How to exploit the strengths most

Ranked by leverage for this product: how much correctness, security or speed a pattern buys per unit of effort [I].

| Rank | Pattern | Where in Plotroom | Why it has leverage | Status |
| --- | --- | --- | --- | --- |
| 1 | **One typed, witness-gated admission for every edit** (closed command enums, `Admitted<T>`, `UserIntent`, `Guarded<T>` without `DerefMut`; each witness consumed by move, so it is single-use) | `plotroom-commands`, `plotroom-session`, `plotroom-doc` | UI, Wilco, plugins, MCP and the CLI all pass one gate; the compiler, not review, refuses a bypass; trybuild proves each refusal (doc 62) | Proposed (commands-undo-history §4) |
| 2 | **Parsers as capped, borrowed, pure functions** over `&'input [u8]`, iterator- and chunk-driven, with fuzz, property round trips and adversarial tests | L0–L1 (`plotroom-bytes` cursor, format crates) | Removes the memory-corruption class from the riskiest input; 68-P2–P5 remove the panic and abort classes that remain in our own parsers | Decided (D017 item 3, `AGENTS.md`); depth-cap, byte-size and `try_reserve` rules missing |
| 3 | **Capability confinement by crate graph plus bans**: files, processes, network, environment and tokio confined to named crates; clippy `disallowed-*` with instruction reasons; `xtask layers`; cargo-deny per-layer bans | Whole workspace | Security properties become compile errors; an agent that reaches for `std::fs` gets a reason that names the sanctioned API | Working tree (bans; `xtask layers` for direct edges and confined crates); proposed (cargo-deny per-layer feature bans) |
| 4 | **Harness crates as synchronous, sans-IO state machines** fed by typed events, with `Clock`, `IdSource` and seeds injected | L6 | Deterministic tests, no async complexity, replayable journals; weak models fill typed slots | Proposed (crate-map §2.3; testing-strategy §1) |
| 5 | **Snapshot-and-swap document model** (`Arc<Snapshot>`, persistent maps, op log for undo) | `plotroom-project` | Readers never lock; `Send`/`Sync` checked; undo is data; rayon validation reads a stable snapshot | Proposed (core-document-model; ui-shell §10) |
| 6 | **Types as the model contract**: closed serde/schemars enums generate the schemas Wilco and external agents see, with derives placed by the orphan rule (68-P30, 68-P31) | `plotroom-commands`, `plotroom-decide` | One definition serves compiler, schema and validator | Proposed |
| 7 | **Immediate-mode GUI over a headless session** | `plotroom-ui`, `plotroom-view` | No callbacks and no shared mutable UI state, which is where Rust GUIs struggle [I]; every behaviour below the shell is testable without a window | Decided in part (egui, D016); headless session proposed (crate-map; testing-strategy §1) |
| 8 | **WebAssembly components for plugin tier T1** | `plotroom-plugin-host` (v1.x) | Isolation and a stable interface without unsafe FFI | Decided (D007) |
| 9 | **The 3-OS matrix as our own crater**: crater "only works on Linux at the moment" [V], and `cfg(target_os)` code is validated only on its OS (`AGENTS.md`) | CI | Catches platform-gated breakage the ecosystem never tests for us, including cross-OS golden seeds (68-P7) | Decided |
| 10 | **Data parallelism where it is safe**: rayon for validation, catalog merges, export scans | L4–L5 | Speed with compile-time race freedom; determinism kept by 68-P7; panics kept by 68-P1 | Proposed |

Patterns per domain [I]:

- **Parsers of untrusted files.** A cursor built on fixed-size views (`split_first_chunk::<N>()` then `from_le_bytes`) does one length
  check per field and no offset arithmetic [I]; caps are named constants with their engine origin and bound bytes, not only counts;
  every recursive rule counts depth; errors carry offsets and limits; `Display` names the next action.
- **Desktop GUI.** The document is immutable during a frame; edits are queued commands; state lives in disjoint structs so closures
  borrow only what they touch; heavy work and file parsing leave the UI thread; per-frame buffers are reused.
- **Typed document model with undo.** Ids are newtypes into maps; ops are data; undo is inverse ops; invariants are checked after
  every step in tests (`validate_invariants`, testing-strategy §6).
- **AI harness.** Model output is parsed into typed values or rejected with a finding that names allowed values; nothing unchecked
  becomes a command; budgets and cancellation are types; secrets never reach a `Debug` or a prompt (68-P29).
- **Plugins in WebAssembly.** Coarse calls (each host call is a boundary crossing); fuel, epoch deadlines and memory limits on every
  T1 call (D007 item 1) [V per D007].
- **Cross-platform CI.** Native builds on three runners; Apple-silicon macOS (already `macos-latest`); release packaging checked with
  each platform's default linker.

## 6. Rust and AI coding agents: what docs 62 and 64 do not cover

Doc 62 covers type-driven guidance and where diagnostics land (§3–§4); doc 64 covers the evidence on Rust and small models, the
pilot and the fast inner loop. New here:

1. **Claude Code's feed carries warnings.** With the `rust-analyzer-lsp` plugin, "each time Claude edits or writes a file the server
   handles, Claude gets the errors and warnings the server reports"; the plugin does not start in cloud sessions [V]. Doc 62 §4's
   errors-only analysis (OpenCode) is therefore client-specific; deny-level guidance is still needed for errors-only clients.
2. **Gate flags and the feed.** `CARGO_BUILD_WARNINGS=deny` fails the run but leaves the lint text at warning level, while
   `-D warnings` turns it into an error and re-checks the crate when toggled; `build.warnings = deny` also fails on linker warnings,
   which `-D warnings` ignores [V, probe]. The agent's terminal loop reads cargo's output in full, so the environment variable suits it;
   editor feeds need deny-level `[lints]` (68-P13).
3. **Opening a workspace runs code.** rust-analyzer runs build scripts and proc macros by default and trusts `.cargo/config` and
   `rust-toolchain.toml` overrides of `rustc` [V]. Agents and contributors must not open untrusted branches or plugin crates with it
   outside a sandbox; the plugin SDK scaffold should say that `cargo check` runs build scripts [I].
4. **Parallel agents.** Shared `target/` directories serialise and can corrupt, per-worktree ones multiply disk use (cargo#16804) [V];
   68-P16 keeps the per-worktree `target/` and trials sccache to share dependency builds.
5. **Snapshot switches rewrite the spec.** `INSTA_UPDATE=always` "overwrites old snapshot files with new ones unasked", `auto` means
   "`no` for CI environments or `new` otherwise", and `TRYBUILD=overwrite` writes compiler output in place [V]. An agent that sets
   one turns a failing behaviour into the new expected output (68-P23).
6. **Hint-less errors are narrower than doc 64 assumed.** rustc 1.98.1 names the fix for `Refusal::OutOfMap()` ("is a unit enum
   variant, and does not take parentheses to be constructed", with a suggested edit) but gives only "expected function, found
   `Refusal`" and "call expression requires function" for `Refusal::TooFar(x)` [V, probe]. The pilot's wall is that second case.
7. **Industry guidance agrees with `AGENTS.md`.** Microsoft's M-DESIGN-FOR-AI: "Rust's strong type system is a boon for agents, as
   their lack of genuine understanding can often be counterbalanced by comprehensive compiler checks"; it asks for idiomatic APIs,
   thorough docs and examples, strong types, testable APIs and test coverage [V].
8. **LLM-written Rust crypto often fails to compile, and is often insecure when it does.** In a study of 240 samples from three
   models, "only 23.3% of the generated code samples were successfully compiled", a rule-based analyser "identified vulnerabilities in
   57% of the compiled samples", and all three models showed "systematic failures, including nonce reuse and API hallucinations"
   [V-author]. That compiler and analyser gates, rather than model skill, must carry correctness is our inference [I].
9. **rust-lang/rust's LLM policy (the monorepo only, not project-wide).** The policy is "not an official stance on LLMs, and does not
   apply everywhere in the Rust project"; it governs the `rust-lang/rust` monorepo [V]. Its rules: "It's fine to use LLMs to answer
   questions, analyze, distill, refine, check, suggest, review. But not to **create**"; LLM-created code changes are allowed only when
   "pre-arranged, non-critical, high-quality, well-tested", with disclosure; issue reporters must "disclose any LLM involvement in
   discovering or reporting issues" and "clearly quote and indicate which parts of your report were LLM-generated" [V]. It does not
   name clippy or rust-analyzer. Plotroom's own choice: a toolchain request (for example the E0618 help above) is written by a
   person, with disclosure, for rustc, clippy and rust-analyzer alike (68-G9) [I].

## 7. Frictions introduced or removed (D049)

| Audience | Introduced by this playbook | Removed or reduced |
| --- | --- | --- |
| People using the editor | None directly | A hostile or broken file costs an error card, not a crash (68-P1–P3); an interrupted job keeps the document (68-P1); an unclean exit is detected and offers recovery (68-P1) |
| Models (Wilco, external agents) | None at run time | Findings instead of crashes on malformed model output (68-P1); no host paths or secrets in what they see (68-P28, 68-P29) |
| Contributors and coding agents | More lint attributes to satisfy in format and domain crates (68-P5, 68-P20); allowlists to extend by review (68-P10); a toolchain policy and `cargo +<pin>` for final gates (68-P9); depth-limit and byte-cap tests per parser (68-P2, 68-P3); a `build.warnings` gate that also fails on linker warnings unless that lint is allowed (68-P13); a longer `AGENTS.md`, which FR-C-010 already records as over its ~600-line ceiling (68 OQ 4 decides prose versus lints) | Cache churn between `-D warnings` and plain clippy (68-P13; locally now, in CI once it caches); slow dev links and full debuginfo (68-P12); IDE and cargo lock fights (68-P15); worktree collisions (68-P16); silent snapshot rewrites (68-P23); surprise CI breaks from a toolchain bump or an advisory (68-P9, 68-P10) |
| The owner | Decisions: release overflow checks, the linker-warning choice, Defender exclusions or Windows 11, cargo-vet, the `AGENTS.md` edits (Open questions) | Fewer late surprises; a written answer to "what does Rust guarantee" |

Not fixed here, for the register (not filed): the Windows 10 host cannot use Dev Drive (contributors; severity high for the owner;
removal: exclusions or an OS upgrade, owner); `AGENTS.md`'s gate and inner-loop commands re-check crates when switched with the
editor's clippy (contributors, models; removal 68-P13); unsafe emitted by dependency macros, proc macro or `macro_rules!`, is invisible
to `forbid(unsafe_code)` (contributors; removal 68-P10 in part, 68-G11); FR-C-030's proposed fix conflicts with the skeleton's
toolchain choice (Findings).

## 8. Tests to write first

Test-first per `AGENTS.md`; each proves one playbook item before its code lands [I].

1. **Depth cap** (68-P2): each recursive parser, starting with SP-09's config parser, accepts nesting at its cap and returns
   `NestingTooDeep { depth, limit }` at cap+1, run through a small-stack thread helper in `plotroom-testkit`.
2. **Allocation cap** (68-P3): a `u32::MAX` element count, a zero-size element and a declared decompressed size above the cap each
   return a structured `Error`, never a panic or an abort.
3. **Determinism** (68-P7): a run-twice test per seeded crate, and a golden-seed byte comparison that runs on all three CI OSes.
4. **Job boundary** (68-P1): a panic inside a job spawned through the workspace wrapper yields a job-failed finding, the process
   keeps running and the document is unchanged.
5. **Supply chain** (68-P10): an `xtask` negative fixture with a planted proc-macro dependency outside the allowlist fails, mirroring
   the planted GPL-2.0-only fixture; a planted dependency with an unlisted build script fails cargo-deny.
6. **Warnings gate** (68-P13): a fixture crate with one lint warning fails under `CARGO_BUILD_WARNINGS=deny`; the linker-warning
   choice is recorded where the gate is defined.
7. **Secrets** (68-P29): trybuild cases prove `SecretKey` has no `Display` and no `Serialize`; a unit test proves its `Debug` prints
   no secret.
8. **Pin consistency** (68-P9): an `xtask` test fails when ci.yml's `RUST_TOOLCHAIN` and `rust-version` disagree.

## 9. Design-gap candidates (listed, not filed)

1. **68-G1 Runtime panic and crash policy**: `panic = "unwind"`, job boundaries for `catch_unwind`, the rayon panic handler and
   job-spawn wrapper, `JoinSet` for tokio jobs, the session sentinel, the hook's contents and that they stay in local logs, the
   `Drop` rule, `ExitCode`, how a job failure appears to the user; ties to M2 exit item 10 (crash recovery) and DG017 (journal storage).
2. **68-G2 Recursion depth and stack policy**: the limit per parser and evaluator (config class nesting, preprocessor includes, SQF,
   CXL, briefing HTML) against the smallest stack any walker uses; sized stacks for every thread and pool, built in one place;
   parsing off the UI thread (changes ui-shell §9–§10); deep-tree `Drop`.
3. **68-G3 Allocation caps for input-sized buffers**: byte-size caps, zero-size elements, decompression caps, `try_reserve` as a
   second line; amends `AGENTS.md` heap rule 4; links doc 07 §16's caps table and D017 item 3.
4. **68-G4 Release overflow checks and the arithmetic and cast rules**: `overflow-checks` for the whole graph or our crates only, the
   checked-versus-saturating rule (amends `AGENTS.md` "Integer Overflow Safety"), cast lints; changes crate-map §2.4.
5. **68-G5 Toolchain pin, MSRV and bump policy**: N-1 adoption, security bumps, the beta canary and nightly diff, `rust-src` for UI
   tests, snapshot re-bless review, the pin-consistency check, the MSRV-aware resolver in the latest-dependencies job. The pin moves
   to CI plus `rust-version` (the skeleton's choice, `CODE-INDEX.md` §3), which reverses FR-C-030's proposed fix ("Pin the toolchain
   with rust-toolchain.toml"); answers doc 62 OQ5's cadence.
6. **68-G6 Supply-chain policy beyond licences**: build-script and proc-macro allowlists, the advisories split, SHA-pinned actions and
   versioned tool installs, the publish-age cooldown, `cargo-auditable`, the latest-dependencies job, whether to adopt cargo-vet, who
   approves a new crate.
7. **68-G7 Warnings gate**: `CARGO_BUILD_WARNINGS=deny` instead of `-- -D warnings` in `AGENTS.md` ("Lint", "Fast inner loop"),
   ci.yml, testing-strategy §14, roadmap M0 scope and `CODE-INDEX.md` §2, and the linker-warning choice that comes with it.
8. **68-G8 Contributor Rust environment**: rust-analyzer settings, Windows linker, sccache, Defender; where they live (CONTRIBUTING,
   `.vscode/`), given that no root `.cargo/config.toml` exists.
9. **68-G9 Where toolchain requests live**: rustc, clippy and rust-analyzer requests (the E0618-with-arguments help) are not engine
   requests; `docs/upstream/` is scoped to the game engine. "Written by a person, with disclosure" is Plotroom's own choice; the
   upstream policy covers only the rust-lang/rust monorepo.
10. **68-G10 Determinism rules for seeded crates**: maps, float reductions, std transcendental functions, a pinned ChaCha (doc 43
    §3.2), `algebraic_*` methods, feature bans (68-P27), run-twice and cross-OS golden-seed tests.
11. **68-G11 The unsafe policy's two gaps**: unsafe emitted by any macro defined in another crate, proc macro or `macro_rules!`, which
    `forbid` does not see, so the rule's meaning becomes "no `unsafe` token written in our crates; unsafe from dependency macros is a
    dependency-review question"; and the crate shape of an approved exception, which conflicts with "every crate sets
    `lints.workspace = true`" (crate-map §2.4; `CODE-INDEX.md` §3): options (a) and (b) of §4.3. A change to what the no-unsafe rule
    means is a design decision.
12. **68-G12 Verification tiers**: mutation testing on parser PRs, fixed and random proptest seeds, optional Miri, Kani and the
    expanded-unsafe scan; extends testing-strategy §2 and §14.
13. **68-G13 Reflection substitute and derive placement**: whether one ecosystem derive family (serde, schemars) is the sanctioned
    substitute for reflection in inspectors, schemas and diffs despite 68-P19's "no in-house proc macros", and where derives live
    under the orphan rule (68-P30, 68-P31).

## Open questions

Cited as "68 OQ n". Numbers 8, 9 and 11 are kept, with their answers, so that references stay stable.

1. **Owner:** turn on `overflow-checks` in the release profile (a missed wrap becomes a contained panic and an error card under a job
   boundary), or keep release wrapping and rely on checked arithmetic and lints alone? It applies to the whole dependency graph; in
   UI-thread code outside a job boundary it trades availability (a crash, softened by the crash journal) for integrity (no silent
   wrap). Cost unmeasured [U].
2. **Owner:** on the Windows 10 host, accept Defender folder exclusions for `target/` and `CARGO_HOME` (faster builds, and build
   scripts in those folders are no longer scanned in real time), upgrade to Windows 11 for Dev Drive, or accept slower builds? [I]
3. **Owner:** adopt cargo-vet (audit records per new dependency) or stop at cargo-deny plus allowlists and human review? [I]
4. **Owner:** apply §4.4's `AGENTS.md` rules as prose, as lints and tests only, or as a nested rule file under `crates/`
   (FR-C-010)? [I]
5. **Owner:** the publish-age cooldown length once Cargo 1.100 is pinned; the PR's own example is `"7 days"` [V].
6. **Technical:** depth limits and worker stack sizes per recursive parser; real nesting depths in official and community content are
   [U] and need measuring on owned installs (opt-in, local).
7. **Technical:** release debuginfo (`line-tables-only`, split into PDB or dSYM) for symbolised crash reports: size and privacy cost,
   with paths remapped (68-P28) [U].
8. **Answered** [V]: `allow-build-scripts` covers crates with build scripts only; its `bypass` "only applies to crate with build
   scripts, not proc macros". The `xtask` proc-macro allowlist is therefore required (68-P10), within the `macro_rules!` limit of §1.4.
9. **Answered** [V]: clippy walks up the directory tree "until it finds one", so the first file found is used and no merge is
   documented; a probe that nothing merges remains optional.
10. **Technical:** how noisy is `wildcard_enum_match_arm` on foreign `#[non_exhaustive]` enums such as `io::ErrorKind`? [U]
11. **Answered in part** [V]: the keys are `[registry] global-min-publish-age` and `[registries.<name>] min-publish-age`, values are
    duration strings such as `"7 days"`, and `CARGO_RESOLVER_INCOMPATIBLE_PUBLISH_AGE=allow` overrides (cargo#17335). Left: check them
    against the pinned Cargo once it is 1.100 or later.
12. **Measurement:** clean, incremental and link times on the owner's machine and each CI OS once M0 has crates; `link.exe` against
    `rust-lld.exe`; the effect of dependency `opt-level` (the §4.2 trade-off note) on clean and incremental builds; sccache on parallel
    worktrees [U].
13. **Measurement:** the run-time cost of release overflow checks on the parser and draw-list benchmarks and on dependency-heavy
    paths (texture decode, a UI frame with a large mission), with and without `[profile.release.package."*"] overflow-checks = false`
    (M2); a dependency that panics on a wrap would surface as a contained panic under 68-P1 [U].
14. **Measurement:** rust-analyzer memory on the full workspace with egui, wgpu, wasmtime and tokio [U].
15. **Measurement:** what share of an agent round is compilation for strong cloud agents on this workspace (doc 64 measured only
    3–4B local models) [U].
16. **Measurement:** linker warnings on all three CI legs, under `cargo test` and under the 68-P14 rust-lld trial, before switching the
    gates to `build.warnings = deny` (68-P13) [U].
17. **Technical:** does a custom profile with `inherits = "dev"` carry the dev profile's `package."*"` overrides? The Cargo book does
    not say [U].
18. **Technical:** do clippy's `disallowed-methods` accept primitive float methods such as `f64::sin`, or does 68-P7 need an `xtask`
    scan? Does tokio's `thread_stack_size`, documented "for worker threads", also size the blocking pool? [U]

## Findings for sibling docs (reported, not fixed)

- **`AGENTS.md`, Heap Allocation Policy rule 6:** "`#[inline]` … to guarantee inlining across crate boundaries" overstates it:
  `#[inline]` is a hint, and with `lto = true` release builds inline across crates anyway; it matters mostly for non-LTO dev and test
  builds [I].
- **`AGENTS.md`, rule 4:** "`Vec::with_capacity(known_size)`" should say the byte size is capped first and large totals use
  `try_reserve` as a second line: `with_capacity` panics above `isize::MAX` bytes and allocator failure aborts [V] (68-G3).
- **`AGENTS.md`, Local Repo-Specific Rules:** "Lint" and "Fast inner loop" use `-- -D warnings`; switching between that and the
  editor's plain clippy re-checks crates [V, probe], and the replacement `CARGO_BUILD_WARNINGS=deny` also fails on linker warnings
  (68-G7). The same command is in ci.yml (line 50), testing-strategy §14 row 1, roadmap M0 scope and `CODE-INDEX.md` §2. Final gates
  should name the pinned toolchain (68-P9). The file has no rule on recursion depth, aborts, thread stacks, lock guards, casts or
  secrets (§4.4).
- **`AGENTS.md`, Integer Overflow Safety:** "Use `saturating_add` (or `checked_add` where recovery is needed)" leads with saturation;
  for sizes and offsets from input, checked arithmetic with a structured error is safer, because a saturated size is wrong but
  plausible and can pass later checks [I] (§4.4, 68-G4). "Never rely on Rust's debug-mode overflow panics" stays right; if the owner
  turns on release overflow checks, add that they are a backstop, not the mechanism (68 OQ 1).
- **`AGENTS.md`, newtype rule:** "Implement `Display`" needs an exception for secret-bearing types (68-P29).
- **crate-map §2.4:** "Every crate sets `lints.workspace = true`; format crates add `arithmetic_side_effects`" cannot be written in a
  manifest (cargo#13157, open) [V]; the skeleton's crate-level `#![deny]` is the fix and the text should say so. "Per-crate
  `clippy.toml`" conflicts with the skeleton's single root file, and clippy uses the first file it finds [V]; the same "per-crate"
  wording is in roadmap M0 scope ("per-crate `disallowed-methods`") and testing-strategy §14 ("Per-crate clippy
  `disallowed-methods`/`disallowed-types`"). `unsafe_code = "forbid"` with `lints.workspace = true` everywhere leaves no route for an
  approved exception (68-G11).
- **testing-strategy §16 OQ2:** clippy 0.1.98's test keys are `allow-dbg-in-tests`, `allow-expect-in-tests`,
  `allow-indexing-slicing-in-tests`, `allow-panic-in-tests`, `allow-print-in-tests`, `allow-unwrap-in-tests`,
  `allow-useless-vec-in-tests` (default false) and `allow-large-stack-frames-in-tests` (default true) [V]; `string_slice`,
  `unreachable`, `todo`, `unimplemented` and `arithmetic_side_effects` have none. Integration tests under `tests/` are outside those
  keys per doc 62 (clippy #13981) [V per doc 62].
- **testing-strategy §14 and D017:** cargo-fuzz's README says "only on Unix-like operating systems (not Windows)" while the Fuzz Book
  says Windows works through MSVC AddressSanitizer [V]; fuzz on Linux CI and do not promise Windows-local fuzzing until checked.
- **Doc 62 §4 and OQ3:** Claude Code's rust-analyzer plugin forwards errors and warnings [V]; rust-analyzer calls
  `rust-analyzer.toml` "a work in progress" with many options unsupported [V], which answers OQ3 as "not reliable yet".
- **Doc 64 §1.3 and P64-A2:** "calling a unit variant (E0618) cannot be annotated" is right for library annotations, but rustc's own
  help names the fix when the parentheses are empty; E0618 is hint-less only when arguments are passed [V, probe]. §4.4 already
  describes the with-argument case.
- **Doc 06 §4.3:** a crate under `#![forbid(unsafe_code)]` accepted `unsafe impl` emitted by a proc macro, a derive and a dependency's
  `macro_rules!` in our probes [V, probe], so a `bytemuck` derive would most likely compile [I]; whether to allow it is a policy
  question (68-G11), and manual `to_le_bytes` packing stays the conservative choice.
- **`fuzz/Cargo.toml` (working tree):** its comment says the workspace's `unsafe_code = "forbid"` "cannot apply here, because
  `fuzz_target!` expands to the `extern "C"` entry point". `fuzz_target!` is a macro from another crate (libfuzzer-sys), and in our
  probe a `macro_rules!` from another crate that emitted `#[unsafe(no_mangle)] pub extern "C" fn` compiled under `forbid` [V, probe].
  Either libfuzzer-sys expands differently or the fuzz crate could keep the forbid; not compiled against libfuzzer-sys here [U].
- **`docs/friction/register.csv` FR-C-030:** its removal text ends "Pin the toolchain with rust-toolchain.toml" and its evidence cites
  "no rust-toolchain.toml". The skeleton pins in CI (`RUST_TOOLCHAIN`) plus `rust-version`, with no root `rust-toolchain.toml` because
  it would reach `tools/rust-weak-models` (`CODE-INDEX.md` §3; FR-C-033 proposes a root file only after that workspace moves). The
  row's removal and evidence need updating to "pin in CI plus `rust-version`; final gates run on the pin" (68-G5).
- **`docs/upstream/README.md`:** no place for toolchain requests (68-G9).
- **`docs/README.md`:** needs a row for this doc (not added here, per the task).

## Sources

All opened on 2026-09-28, at write-up or in the verification pass.

### Rust project: releases, goals, policy

- Release list: <https://blog.rust-lang.org/releases/>
- Rust 1.98.1: <https://blog.rust-lang.org/2026/09/03/Rust-1.98.1/>; Rust 1.98.0 (`algebraic_*`):
  <https://blog.rust-lang.org/2026/08/20/Rust-1.98.0/>
- Rust 1.97.0 (`build.warnings`, `linker_messages`): <https://blog.rust-lang.org/2026/07/09/Rust-1.97.0/>
- Rust 1.95.0 (`cfg_select!`): <https://blog.rust-lang.org/2026/04/16/Rust-1.95.0/>
- Rust 1.92.0 (unwind tables, never-type lints, `Box::new_zeroed`): <https://blog.rust-lang.org/2025/12/11/Rust-1.92.0/>
- Rust 1.91.0 (`strict_*`, aarch64 Windows tier 1): <https://blog.rust-lang.org/2025/10/30/Rust-1.91.0/>
- Rust 1.88.0 (let chains): <https://blog.rust-lang.org/2025/06/26/Rust-1.88.0/>
- Rust 1.85.0 (edition 2024, async closures, `do_not_recommend`): <https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/>
- Rust 1.81.0 (sort panics, `extern "C"` abort, `#[expect]`): <https://blog.rust-lang.org/2024/09/05/Rust-1.81.0/>
- Rust 1.80.0 (`FromIterator` for `Box<str>`): <https://blog.rust-lang.org/2024/07/25/Rust-1.80.0/>
- rust-lld on 1.90.0: <https://blog.rust-lang.org/2025/09/01/rust-lld-on-1.90.0-stable/>
- Next-generation trait solver on nightly: <https://blog.rust-lang.org/2026/08/21/enabling-next-solver-on-nightly/>
- The 2014 stability post: <https://blog.rust-lang.org/2014/10/30/Stability/>
- Compiler performance survey 2025: <https://blog.rust-lang.org/2025/09/10/rust-compiler-performance-survey-2025-results/>
- Rust debugging survey 2026: <https://blog.rust-lang.org/2026/09/07/rust-debugging-survey-2026-results/>
- Supply-chain attack on arrayref: <https://blog.rust-lang.org/2026/08/20/supply-chain-attack-on-arrayref/>
- rust-lang/rust LLM policy: <https://blog.rust-lang.org/inside-rust/2026/08/05/rust-langrust-is-adopting-an-llm-policy/>
- Security policy: <https://www.rust-lang.org/policies/security>
- Project goals 2026: <https://goals.rust-lang.org/2026/goals.html>; Polonius: <https://goals.rust-lang.org/2026/polonius.html>
- Sandboxed build scripts (2024H2): <https://goals.rust-lang.org/2024h2/sandboxed-build-script.html>
- Issues: <https://github.com/rust-lang/rust/issues/25860>, <https://github.com/rust-lang/rust/issues/71520>,
  <https://github.com/rust-lang/rust/issues/127343>, <https://github.com/rust-lang/cargo/issues/13157>,
  <https://github.com/rust-lang/cargo/issues/16804>, <https://github.com/rust-lang/cargo/pull/17335>; open `I-unsound` counts:
  <https://api.github.com/search/issues?q=repo:rust-lang/rust+label:I-unsound+state:open+is:issue> (and with
  `-label:requires-nightly`)
- crater: <https://github.com/rust-lang/crater>

### Reference, Book, std and edition guide

- Behavior considered undefined: <https://doc.rust-lang.org/reference/behavior-considered-undefined.html>
- Behavior not considered unsafe: <https://doc.rust-lang.org/reference/behavior-not-considered-unsafe.html>
- Functions (unwinding table): <https://doc.rust-lang.org/reference/items/functions.html>
- Implementations (orphan rules): <https://doc.rust-lang.org/reference/items/implementations.html>
- `non_exhaustive`: <https://doc.rust-lang.org/reference/attributes/type_system.html>
- The Book, zero-cost iterators: <https://doc.rust-lang.org/book/ch13-04-performance.html>; newtypes:
  <https://doc.rust-lang.org/book/ch20-02-advanced-traits.html>
- `catch_unwind`: <https://doc.rust-lang.org/std/panic/fn.catch_unwind.html>
- `handle_alloc_error`: <https://doc.rust-lang.org/std/alloc/fn.handle_alloc_error.html>; `Vec`:
  <https://doc.rust-lang.org/std/vec/struct.Vec.html>
- `std::thread` (stack size): <https://doc.rust-lang.org/std/thread/index.html>
- `std::sync::Mutex`: <https://doc.rust-lang.org/std/sync/struct.Mutex.html>
- `std::process::exit`: <https://doc.rust-lang.org/std/process/fn.exit.html>
- `HashMap`: <https://doc.rust-lang.org/std/collections/struct.HashMap.html>; `f64`: <https://doc.rust-lang.org/std/primitive.f64.html>
- Editions: <https://doc.rust-lang.org/edition-guide/editions/index.html>; `if let` temporary scope:
  <https://doc.rust-lang.org/edition-guide/rust-2024/temporary-if-let-scope.html>; newly unsafe functions:
  <https://doc.rust-lang.org/edition-guide/rust-2024/newly-unsafe-functions.html>; combined doctests:
  <https://doc.rust-lang.org/edition-guide/rust-2024/rustdoc-doctests.html>
- Platform support: <https://doc.rust-lang.org/rustc/platform-support.html>; wasm32-wasip2:
  <https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html>
- rustc command-line arguments (`--remap-path-prefix`): <https://doc.rust-lang.org/rustc/command-line-arguments.html>

### Cargo, rustup, clippy, rust-analyzer

- Profiles: <https://doc.rust-lang.org/cargo/reference/profiles.html>
- Configuration (`build.build-dir`, `build.warnings`, `resolver.incompatible-rust-versions`, `include`):
  <https://doc.rust-lang.org/cargo/reference/config.html>
- Build cache (build-dir, sccache): <https://doc.rust-lang.org/cargo/reference/build-cache.html>
- Targets (`doctest`): <https://doc.rust-lang.org/cargo/reference/cargo-targets.html>
- `rust-version` policies: <https://doc.rust-lang.org/cargo/reference/rust-version.html>
- Unstable features (`trim-paths`): <https://doc.rust-lang.org/cargo/reference/unstable.html>
- Build performance guide: <https://doc.rust-lang.org/cargo/guide/build-performance.html>
- Cargo changelog (CVE entries, 1.91, 1.97): <https://doc.rust-lang.org/cargo/CHANGELOG.html>
- rustup overrides: <https://rust-lang.github.io/rustup/overrides.html>
- Clippy configuration: <https://doc.rust-lang.org/clippy/configuration.html>; lint configuration:
  <https://doc.rust-lang.org/clippy/lint_configuration.html>; usage: <https://doc.rust-lang.org/clippy/usage.html>
- Clippy lint sources (categories): <https://raw.githubusercontent.com/rust-lang/rust-clippy/master/clippy_lints/src/casts/mod.rs>,
  <https://raw.githubusercontent.com/rust-lang/rust-clippy/master/clippy_lints/src/matches/mod.rs>,
  <https://raw.githubusercontent.com/rust-lang/rust-clippy/master/clippy_lints/src/await_holding_invalid.rs>,
  <https://raw.githubusercontent.com/rust-lang/rust-clippy/master/clippy_lints/src/large_futures.rs>,
  <https://raw.githubusercontent.com/rust-lang/rust-clippy/master/clippy_lints/src/large_stack_arrays.rs>,
  <https://raw.githubusercontent.com/rust-lang/rust-clippy/master/clippy_lints/src/as_conversions.rs>
- rust-analyzer configuration: <https://rust-analyzer.github.io/book/configuration.html>; security:
  <https://rust-analyzer.github.io/book/security.html>

### Ecosystem tools and libraries

- cargo-deny bans: <https://embarkstudios.github.io/cargo-deny/checks/bans/cfg.html>; advisories:
  <https://embarkstudios.github.io/cargo-deny/checks/advisories/cfg.html>; action: <https://github.com/EmbarkStudios/cargo-deny-action>
- cargo-vet criteria: <https://mozilla.github.io/cargo-vet/built-in-criteria.html>
- cargo-auditable: <https://github.com/rust-secure-code/cargo-auditable>
- trybuild: <https://github.com/dtolnay/trybuild>; insta: <https://insta.rs/docs/advanced/>
- cargo-nextest: <https://nexte.st/>; cargo-mutants `--in-diff`: <https://mutants.rs/in-diff.html>
- cargo-fuzz: <https://github.com/rust-fuzz/cargo-fuzz>; Fuzz Book setup: <https://rust-fuzz.github.io/book/cargo-fuzz/setup.html>;
  Testing Handbook on cargo-fuzz: <https://appsec.guide/docs/fuzzing/rust/cargo-fuzz/>
- proptest `Config`: <https://docs.rs/proptest/latest/proptest/test_runner/struct.Config.html>
- Kani install guide: <https://model-checking.github.io/kani/install-guide.html>
- Miri (POPL 2026): <https://plf.inf.ethz.ch/research/popl26-miri.html>
- rayon: <https://docs.rs/rayon/latest/rayon/fn.join.html>, <https://docs.rs/rayon/latest/rayon/fn.scope.html>,
  <https://docs.rs/rayon/latest/rayon/fn.spawn.html>, <https://docs.rs/rayon/latest/rayon/struct.ThreadPoolBuilder.html>,
  <https://docs.rs/rayon/latest/rayon/iter/trait.ParallelIterator.html>
- tokio: `select!` <https://docs.rs/tokio/latest/tokio/macro.select.html>; `JoinError`
  <https://docs.rs/tokio/latest/tokio/task/struct.JoinError.html>; `JoinHandle`
  <https://docs.rs/tokio/latest/tokio/task/struct.JoinHandle.html>; runtime `Builder`
  <https://docs.rs/tokio/latest/tokio/runtime/struct.Builder.html>
- serde_json `Deserializer`: <https://docs.rs/serde_json/latest/serde_json/struct.Deserializer.html>; `Map`:
  <https://docs.rs/serde_json/latest/serde_json/map/struct.Map.html>
- rand `StdRng`: <https://docs.rs/rand/latest/rand/rngs/struct.StdRng.html>; regex: <https://docs.rs/regex/latest/regex/>
- wasmtime `Module`: <https://docs.rs/wasmtime/latest/wasmtime/struct.Module.html>
- Bevy setup (Windows linker, dependency opt-level): <https://bevy.org/learn/quick-start/getting-started/setup/>
- Perf book, bounds checks: <https://nnethercote.github.io/perf-book/bounds-checks.html>; one integration-test binary:
  <https://matklad.github.io/2021/02/27/delete-cargo-integration-tests.html>; min-sized-rust (UPX):
  <https://github.com/johnthagen/min-sized-rust>
- GitHub runner images (`macos-latest`): <https://github.com/actions/runner-images>
- MSVC `/STACK`: <https://learn.microsoft.com/en-us/cpp/build/reference/stack-stack-allocations>; Dev Drive:
  <https://learn.microsoft.com/en-us/windows/dev-drive/>

### Evidence and practice

- Rust in Android (2025-11-13): <https://blog.google/security/rust-in-android-move-fast-fix-things/>
- Rust Foundation, unsafe in the wild:
  <https://rustfoundation.org/media/unsafe-rust-in-the-wild-notes-on-the-current-state-of-unsafe-rust/>
- Cloudflare outage of 2025-11-18: <https://blog.cloudflare.com/18-november-2025-outage/>
- 2025 survey of Rust GUI libraries: <https://www.boringcactus.com/2025/04/13/2025-survey-of-rust-gui-libraries.html>
- Microsoft Pragmatic Rust Guidelines, AI: <https://microsoft.github.io/rust-guidelines/guidelines/ai/>
- Claude Code code-intelligence plugins: <https://code.claude.com/docs/en/plugins/code-intelligence>
- LLM-generated cryptographic Rust, "An Empirical Security Evaluation of LLM-Generated Cryptographic Rust Code" (abstract):
  <https://arxiv.org/abs/2604.27001>

### This repository

- `AGENTS.md`; D001, D006, D007, D016, D017, D022, D032, D049, D058; `docs/architecture/README.md` §7, `crate-map.md` (§2–§16),
  `testing-strategy.md` (§1–§16), `core-document-model.md` §11, `ui-shell.md` §9–§11, `agent-runtime.md` §3;
  `docs/roadmap/m0-m3-foundations-to-preview.md` (M0 scope and exit evidence, M2 item 10); `docs/friction/register.csv` (FR-C-010,
  FR-C-030, FR-C-033); docs 06, 07 (§4.2, §16), 43 (§3.2), 62, 64; `CODE-INDEX.md` §2–§3; `tools/rust-weak-models/Cargo.toml`; the
  uncommitted M0 skeleton (`Cargo.toml`, `Cargo.lock`, `clippy.toml`, `deny.toml`, `xtask/`, `.github/workflows/ci.yml` and
  `fuzz.yml`, `fuzz/Cargo.toml`, `fuzz/fuzz_targets/config_parse.rs`)

## Verification notes

### 2026-09-28, author checks at write-up

- **Opened and quoted** (WebFetch, which summarises pages; quotes were requested verbatim): every URL in Sources that the first draft
  did not tag [R]. Numbers were copied as the sources state them.
- **Counts by API:** the GitHub search API returned `total_count` 135 for open `I-unsound` issues in rust-lang/rust and 112 with
  `-label:requires-nightly`.
- **Conflicts kept visible:** releases.rs listed stable 1.97.1 and beta 1.98.0 when read, against the Rust blog's 1.98.1; the blog
  is used and the 1.99 and 1.100 dates are cadence inferences. cargo-fuzz's README and the Fuzz Book disagree on Windows. The
  catch_unwind page calls foreign-exception behaviour "unspecified" while a research pass reported the Nomicon calling it "undefined";
  resolved in the verification pass below.
- **Probes** (scratch folder outside the repository; rustc, cargo and clippy 1.98.1, `stable-x86_64-pc-windows-msvc`, `--offline`):
  1. *Macro-emitted unsafe, proc macros.* A library with `#![forbid(unsafe_code)]` invoked a function-like proc macro emitting
     `pub struct Emitted(*const u8); unsafe impl Send for Emitted {}` and a derive emitting `unsafe impl Sync for Derived {}` (both
     token streams built by `str::parse`, so call-site spans). `cargo check` finished with only a `dead_code` warning, exit 0.
  2. *Overflow checks across crates.* Release profile `overflow-checks = true` with `[profile.release.package.genlib]
     overflow-checks = false`; `cargo test --release`: `genlib::add_generic::<u8>(255, 1)` panicked ("attempt to add with overflow"),
     `genlib::add_u8(255, 1)` (non-generic) returned 0, local arithmetic in the checked crate panicked. Inputs went through
     `black_box`. One configuration only; other generic shapes may differ [U].
  3. *Warnings gate.* A `clippy::clone_on_copy` warning: plain `cargo clippy` exit 0; with `CARGO_BUILD_WARNINGS=deny` exit 101,
     "error: warnings are denied by `build.warnings` configuration", no "Checking" line (cache reused), the lint still printed as a
     warning; `cargo clippy -- -D warnings` printed "Checking" and an error, and plain `cargo clippy` afterwards printed "Checking"
     again.
  4. *E0618.* `rustc --edition 2024 --crate-type lib`: `Refusal::OutOfMap()` gave E0618 with the unit-variant help and a suggested
     edit; `Refusal::TooFar(x)` gave "expected function, found `Refusal`" with no help.
- **Repository reads:** `AGENTS.md` (in context); crate-map §1–§16 and its verification notes; testing-strategy in full; roadmap M0
  scope and exit evidence; D058; core-document-model §11 lines on the crash op journal; `tools/rust-weak-models/Cargo.toml`;
  `CODE-INDEX.md` lines on the research workspace; the friction register rows FR-C-010 and FR-C-030; the skeleton's `Cargo.toml`,
  `clippy.toml` and `deny.toml`; docs 62, 64, 65 and 67 for format and scope.
- **Not done:** no cargo command in the repository; no build-time measurement of Plotroom (none is possible before crates exist).
- **Folding steps, not done here:** a row in `docs/README.md`; the sibling findings above; filing 68-G1–68-G13; friction rows.
- **Hygiene:** public sources only; no private or unpublished project named; no local path, user name or key in this file; probe
  files stayed outside the repository.

### 2026-09-28, verification pass (review findings applied)

- **2026-09-28:** 79 review findings were re-checked against their sources, and every one that held was applied, merged where
  several findings covered the same point. Corrections to the findings themselves: the lockfile has **six** crates with build scripts,
  not five (`zmij` 1.0.23 also has one) [V, local registry]; six of the eight releases from 1.91 to 1.98 had a point release, not five
  [V]; clippy's `large_stack_arrays` is `pedantic` in its source, although the lint list page summarised it as `perf` [V]. Kept with
  a stated reason: 68 OQ 8, 9 and 11 are marked answered in place rather than deleted, so that "68 OQ n" references stay stable.
- **Opened in this pass:** every source the first draft tagged [R] (Book ch. 13-04 and 20-02, the edition guide, #31273 and #127343,
  the perf book, matklad's post, Dev Drive, min-sized-rust, proptest, the Testing Handbook, cargo-auditable, the `rust-version`
  page, cargo-deny advisories, rayon, tokio, wasm32-wasip2, crater, the 1.85, 1.88, 1.91, 1.95 and 1.98 posts, the debugging survey),
  plus the Reference's unwinding table and orphan rules, `Vec`, `f64`, `HashMap`, rand, serde_json `Map`, regex, cargo-deny-action,
  the security policy, `trim-paths`, `--remap-path-prefix`, the build-cache and targets pages, runner images, the Bevy setup page,
  the LLM policy, the next-solver post, the goals list, the Android post, the arrayref post and PR #17335. #31273 is a closed request
  titled "Stack overflow should abort the process normally, not segfault", so the abort claim now rests on probe 5, not on it. The
  catch_unwind conflict is resolved by the Reference: a native unwind through a `"C"` ABI is undefined behaviour, and
  catch_unwind's "unspecified" applies to foreign exceptions entering through `"C-unwind"`.
- **Probes added in this pass** (same scratch folder and toolchain, `rustc` and `cargo --offline`):
  5. *Stack overflow.* Unbounded recursion inside `catch_unwind` printed "thread 'main' (…) has overflowed its stack" and the process
     exited with 0xC00000FD (`STATUS_STACK_OVERFLOW`); the "caught" line after `catch_unwind` never printed.
  6. *`macro_rules!` from another crate.* Library `mac` exported macros emitting `unsafe impl Send for $t {}`,
     `#[unsafe(no_mangle)] pub extern "C" fn $name()` and `unsafe { $e }`; a crate with `#![forbid(unsafe_code)]` used all three,
     including `pub fn read(p: *const u8) -> u8 { mac::emit_unsafe_block!(*p) }`: exit 0, no diagnostics. Controls written directly
     in a forbid crate failed with "implementation of an `unsafe` trait" and "usage of the unsafe `#[no_mangle]` attribute".
  7. *Linker warnings.* A bin crate built with `RUSTFLAGS="-C link-arg=/FOOBARPROBE"` (MSVC LNK4044): plain `cargo build` exit 0 with
     "warning: linker stdout: LINK : warning LNK4044"; with `CARGO_BUILD_WARNINGS=deny` exit 101, "warnings are denied by
     `build.warnings` configuration"; with `-Dwarnings` added to `RUSTFLAGS` exit 0 and the note "the `linker_messages` lint ignores
     `-D warnings`".
- **Repository reads added:** `.github/workflows/ci.yml` and `fuzz.yml`, `fuzz/Cargo.toml`, `fuzz/fuzz_targets/config_parse.rs`,
  `xtask/Cargo.toml`, `crates/plotroom-testkit/Cargo.toml`, `Cargo.lock` and the six locked crates' `build.rs` files in the local
  registry, `CODE-INDEX.md` §2–§3, `git status` (every skeleton file staged, none committed), D007, D017, D022, D032, architecture
  README §7, agent-runtime's design-gap list, ui-shell §9–§10, doc 07 §4.2 and §16, doc 43 §3.2, doc 64 §1.3, §4.4, §5.1 and
  P64-A2, testing-strategy §14, roadmap M0 scope, crate-map §2.2, §2.4, §3–§12 (the crate count) and the friction rows FR-C-010,
  FR-C-030 and FR-C-033.
- **Still not done:** no probe of `inherits` and package overrides (68 OQ 17), of `disallowed-methods` on primitive float methods or
  tokio's blocking-pool stack (68 OQ 18), of clippy's no-merge behaviour, or of `fuzz_target!` under `forbid`; no measurement of
  linker warnings on the CI legs (68 OQ 16). The consistency re-read checked that the TL;DR, the counts, the playbook table, §4.3,
  §4.5, the design-gap list and the open questions agree, and a scan for control, bidi, zero-width and tag characters found none.
