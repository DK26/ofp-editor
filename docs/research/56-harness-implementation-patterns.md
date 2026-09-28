# Harness implementation patterns

Research doc 56 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents who will build
the harness crates. This file is meant to be read on its own.
Question answered: which implementation patterns make Plotroom's code-owned harness (Wilco, the AI-off workflows and the evaluation
tooling) dependable with weak and small models, where each lands in the planned crates, what it would change in existing docs, and
which tests would prove it.

**Status: proposal. Nothing was run, measured or coded for this doc.** Every pattern is a proposal [I]; what a sibling doc already
says is [V per that doc]. This doc changes no decision and edits no other doc.
**Relation to sibling docs.** Docs 21, 25 and 38 set the doctrine, the campaign harness and the workflow format; doc 40 the token
economy; doc 51 §4 the intake order, error taxonomy and separate retry, resample and repair budgets; doc 53 §4 the tiny-first design;
doc 55 the harness-preset knobs, file and tuning protocol (D048). This doc does not repeat them; it adds the implementation detail
underneath and lists where each piece would fold in.
**Where things live.** "agent-runtime", "crate-map", "testing-strategy", "extensibility" and "validation-and-lints" are the files of
those names in [`docs/architecture/`](../architecture/README.md); crate names follow crate-map and are not final. Pattern ids are local
to this doc. Statistical methods are textbook and named only. **Hygiene:** no game content, local paths, model output or measurement
that is not already in a sibling doc.

## TL;DR

- **The rule behind every pattern** [I]: wherever a weak model could fail silently, the harness gets a typed outcome, a count and a
  test. Code decides whether to ask, whether an answer is admitted, whether a step is done and whether a run proves anything.
- **Workflow runtime (§1):** refuse unreachable steps and partly checked outputs; a closed retry, reuse, approval and undo policy per
  operation; run records that must match the declared model policy; exact loop detection; worst-case reservations.
- **Model adapters and presets (§2):** a test proving no preset reaches tools, grants, checks, steps or escapes; no "auto" values;
  asked-for, server-reported and measured settings; one request builder and one strict byte reader; per-reply identity and token
  checks.
- **Decision steps and abstention (§3):** escapes belong to the step; the clarifying question is computed; exact copies are picked by
  index; no look-alike lists or fields that must agree; conclusions instead of raw material; computed scores route, checks admit.
- **Validation and repair (§4):** closed repair kinds naming the exact text to restore; form failures replaced, never shown back; a
  malformed-reply streak apart from repairs; check results with counts that add up; slow reference oracles.
- **Evaluation (§5):** identity re-checked when a run ends; balanced interleaving and exact sequential stopping; item-level verdicts in
  a fixed order; abstention as its own instrument; held-out marker strings; one responsible layer per failure.
- **Local models (§6), journal (§7), packaging (§8):** downloads that resume only from a proven offset and verified, scrubbed
  launches; every harness message a record; reproducible positive-list bundles, registry-checked names, shape records and a hardened
  loopback server.
- **Tensions (§9)** with docs 25, 38, 51 and 55; **seven design-gap candidates, not filed (§10).**

Each pattern gives the pattern, then **Why** (why it helps weak or small models), **Maps onto** (planned crate and architecture
section), **Folds** (fold candidates in existing docs, none applied) and **Tests first** (red tests before the code, per `AGENTS.md`
"Test-First / Proof-First", each with its `AGENTS.md` doc comment).

## 1. Workflow runtime (`plotroom-workflow`, `plotroom-workflow-runtime`, `plotroom-campaign-flow`)

### WR1 The definition compiler proves every path is reachable and checked [I]

Beyond doc 38 §6.2, the compiler refuses: a declared input no step uses; a code step or check no workflow reaches; a model step whose
following check does not consume **all** its outputs; a non-routing model step bound to the raw request instead of a prepared view;
model steps that differ from the declared model jobs; a threshold that can never be reached. Every dispatch row and selection rule
must fire **alone** in some scenario. The loader takes one snapshot of each definition file and derives both its hash and its parsed
form from that snapshot.

- **Why:** a partly checked output is an unchecked channel, and a dead rule is an untested path a weak model will eventually take.
- **Maps onto:** the definition compiler (agent-runtime §4); the pack loader (extensibility §3.2); `xtask defs` (crate-map §12).
- **Folds:** doc 38 §6.2 (six refusals); agent-runtime §4's build-time test ("followed by a check that consumes every output").
- **Tests first:** an AT-W1 fixture per refusal; each dispatch row's scenario run alone; a loader test proving no second read occurs.

### WR2 Every operation carries a closed policy [I]

Each code step, tool and effect declares, as closed enums, its repeatability, whether it may be retried or its settled result reused,
what approval it needs and how it is undone. Retries exist only for replay-safe non-model operations and a short closed list of
passing faults (the service is busy or unreachable, a rate limit applies, the call ran out of time, the connection dropped), bounded in
attempts and backoff. A model call is never retried in place: a
new sample is a new journaled attempt, and no retry switches models. A timed-out call is finished only once the supervisor has seen it
end, and only then is its slot freed.

- **Why:** weak models fail often; silent retries would hide the real failure rate from qualification and double the cost.
- **Maps onto:** determinism classes (agent-runtime §5; doc 38 §4.2, §4.6); doc 51 §4.6; the model-manager supervisor (crate-map §10).
- **Folds:** doc 38 §4.2's class table gains retry, reuse, approval and undo columns; DG016 (retries counted per cause).
- **Tests first:** injected faults never retry a non-replay-safe operation; a named test per refused approval and undo path; on a
  virtual clock, a slot stays held until the fake process exits.

### WR3 A run record must agree with the declared model policy [I]

Each workflow declares a model as not allowed, allowed or needed, and each model step names its job from a closed list that includes
"no model", shown on the plan card (doc 38 §5.2). Before a run record is written, success, exit status, errors, outputs and model-call
counts must agree with each other and with the policy. If a job's passing runs never call a model, it is reclassified as a
code-only workflow.

- **Why:** crediting a model for work code did is the easiest way for a weak model to look better than it is.
- **Maps onto:** `required` and `forbidden` (doc 38 §6.2); `RunFinished` (agent-runtime §5); `plotroom-evals` (agent-runtime §7).
- **Folds:** doc 21 §6.3 (model job per step); agent-runtime §4 (the plan card lists each step's job).
- **Tests first:** a fixture per invariant; a `forbidden` workflow makes zero calls; a `required` workflow that succeeds on defaulted
  answers alone is reclassified as code-only.

### WR4 Code steps return closed statuses; "done" needs coverage [I]

Every code step returns one of four closed statuses (finished, blocked on missing data, outside what the step handles, unusable input)
with a reason code and exact fields, never free text;
a missing typed result is an error, never a cue to parse text. A job is done only if it exited cleanly, a separate check of the
state it left behind passed, every check it claims ran, and its inputs did not change underneath it; later edits that could break it
re-open the check. The assistant may report a more modest status than coverage supports, never a stronger one.

- **Why:** a weak model can relay a computed status but cannot overclaim one code did not compute.
- **Maps onto:** code steps in `plotroom-generate` and `plotroom-campaign-flow` (agent-runtime §10); `Done(TurnReport)` (§5, §9).
- **Folds:** doc 38 §3.2's `code` row; doc 21 §5.1 (status capped by coverage); validation-and-lints §1 principle 1, for jobs too.
- **Tests first:** "done" with a failed or skipped check is refused or downgraded; a mid-job input change settles "inputs changed".

### WR5 Exact progress detection [I]

Fingerprint every harness-visible transition, including turns where the model did nothing; keep a short bounded history that survives
resume; stop when the latest block of transitions has repeated a fixed number of times. Any changed output or state is progress. A
suggestion is never offered twice in a session, and each saved one carries the producing code's version.

- **Why:** small models loop more; a hash comparison is exact and free, while asking a model "are you stuck?" is neither.
- **Maps onto:** Wilco's stagnation fingerprints (agent-runtime §9), generalised to the runtime (doc 38 §4.6).
- **Folds:** agent-runtime §9 (no-op turns fingerprinted; history kept across resume).
- **Tests first:** period-two and period-three loops stop at the declared count; one changed byte is progress; resume keeps the count.

### WR6 Reserve the worst case and mark calls in flight [I]

Before each model call, reserve prompt plus output cap and flush an in-flight record. A run that dies mid-call leaves the attempt
unfinished with unknown cost, never replayed; an unknown cost stops and asks. Usage is charged as reported only if self-consistent,
otherwise as a conservative estimate marked "estimated"; a reply whose charge crosses a cap is not acted on. Admission uses the
per-request context read back from the server (parallel slots divide it) and, without the exact tokenizer, a provable upper bound
(the whole request with tool schemas, non-ASCII at byte width, plus a fixed template reserve).

- **Why:** small windows are tight, and a silently truncated prompt yields a reply that looks like a wrong answer.
- **Maps onto:** the ledger (agent-runtime §12); `ModelRequested` (§5); `/props` at start-up (§3); admission (§6); doc 40 R8, R11.
- **Folds:** agent-runtime §5 (`ModelRequested` flushed before sending, with its reservation); §3 (per-slot context); DG016.
- **Tests first:** a crash mid-call leaves an unfinished, unknown-cost attempt and no new call; the bound never falls below a fixture
  tokenizer's count; a reply crossing the run cap is not admitted.

### WR7 Fixed hashing for evidence; a fixed review checklist [I]

Anything stored or used as a seed comes from one documented hash function, never a randomised hasher or map order, and floats are
coarsely rounded before entering stored evidence. Each first-party workflow is reviewed against one checklist that covers the trust
and privacy of its inputs, where its facts and computations come from, step order and resumption, what it changes and under which
permission, its limits and platform differences, the decision left to the model and the model's way out, and the evidence for
acceptance. Every checklist item is demonstrated by at least one scenario, among them the normal path, an edge limit, a user turning
down an approval, a request the workflow turns down, recovery after a fault and a model that declines.

- **Why:** one unstable byte turns a reused decision into a new, paid one; the checklist makes the model's share a reviewable line.
- **Maps onto:** `plotroom-ids` (crate-map §3); runtime-minted seeds (agent-runtime §5); built-in packs (extensibility §3.5).
- **Folds:** testing-strategy §15 (golden digests); crate-map §2.4 (ban randomised hashers in evidence paths); doc 38 §6.1.
- **Tests first:** committed golden digests (stable across processes and machines without spawning anything); two insertion orders
  give one digest; a coverage report fails when a checklist part has no scenario.

## 2. Model adapters and presets (`plotroom-provider`, `plotroom-provider-http`, `plotroom-net`)

### MA1 A test proving no preset widens anything [I]

The preset loader accepts only a closed list of typed, range-checked knobs and refuses unknown keys; a test enumerates the schema's
fields and shows none reaches a tool, grant, check, step kind or escape. Whether "ask" or "none fit" is legal belongs to the step:
where code supplied all evidence there is no ask; where a fact may be missing, a short question runs nothing and changes nothing.

- **Why:** doc 55 §1.4 states the invariant; this makes "does this preset widen anything?" answerable by a test.
- **Maps onto:** `plotroom-provider` (agent-runtime §1, §3); doc 55 §3.3's schema.
- **Folds:** doc 55 §3.1 principle 5 (the enumeration test); doc 55 §2.3 (escapes as step properties).
- **Tests first:** the enumeration against capability-bearing types; negative controls beyond doc 55 §3.3's three: a preset removing
  `Q`, one naming a tool, one with an unknown key.

### MA2 No "auto": every setting explicit, recorded three ways [I]

A preset sets, disables or marks unsupported every behaviour-changing setting (every sampler value including those switched off and
the order samplers run in, the random seed, the output cap and stop strings, the repetition window, reasoning switches and budgets,
constrained decoding, per-request context, cache types, offload, prompt-cache policy), noting start-up or per request; "auto" and "default" are refused, and non-reproducible
settings (adaptive samplers, automatic fitting, context extension, speculative decoding) form a separate setup. Run records keep what
was asked for, what the server reported applying and what the reply showed; unknown stays unknown. Pinned samplers become the managed server's defaults as well as request
fields, so a client that omits a field still gets the measured value.

- **Why:** a hidden default moves small-model answers (agent-runtime §3's presence-penalty case) and is caught only if recorded.
- **Maps onto:** model setups in `plotroom-provider`; the sidecar start-up (agent-runtime §3); external clients of `plotroom-mcp`.
- **Folds:** agent-runtime §3 (pin server defaults too); doc 55 §3.3 ("unsupported" values); doc 51 §4.3 (tri-state on run records).
- **Tests first:** "auto" is refused; a fake server reporting other settings labels the run "requested only"; a request without
  sampler fields reaches the fake server with the pinned values.

### MA3 One request builder, one strict reader [I]

One pure function per wire builds every request, with the thinking switch in the form the serving stack actually reads. One strict
reader parses every reply from bytes: depth counted outside strings before decoding; duplicate keys refused without echoing the key;
non-finite and overlong numbers refused; output bounded as raw bytes first, then after display expansion. The envelope must agree with
itself (one choice, assistant role, no legacy function field, a finish reason matching the tool calls, no truncation or filtering); JSON
inside a tool call is a second strict document. The adapter never invents envelope fields or repairs output into a valid-looking answer.

- **Why:** a library that keeps the last duplicate key, or an adapter that fills a missing role, admits a malformed small-model reply.
- **Maps onto:** `plotroom-provider-http` (crate-map §10); admission in `plotroom-decide` (agent-runtime §6).
- **Folds:** doc 51 §4.5 step 6 (pre-decode depth scan; bytes-first limits); agent-runtime §6 "Strict admission" (envelope rules).
- **Tests first:** the `AGENTS.md` parser categories for the reader (depth at and past the cap, duplicate keys at both levels, bad
  numbers, oversize bytes); a fuzz target (testing-strategy §3); a request golden per wire.

### MA4 Cross-check the served model and the token counts [I]

On every reply, check that the reported model is the one the setup names, counting matches, mismatches and malformed identities per
run; a mismatch makes the result incomplete, never scored. Compare the provider's prompt tokens with the editor's own count of the
rendered prompt, and the total with prompt plus completion; a mismatch means the template, tokenizer or served model changed, so the
reply is not admitted and usage is marked estimated.

- **Why:** a silent reroute or re-issued template looks like the model getting worse; qualification holds only on the exact setup.
- **Maps onto:** `plotroom-provider-http`; D046; DG039; the ledger (agent-runtime §12).
- **Folds:** agent-runtime §12 (per-call served-model check); doc 51 §4.8 (token cross-check); DG012 (mismatch as a trigger).
- **Tests first:** cassettes with a swapped model id, an off-by-one prompt count and a wrong total, each giving its typed outcome.

### MA5 Untrusted text both ways; absolute transport limits [I]

Provider output outside the admitted answer is kept by kind, size and hash only; the user sees a fixed message, and none of it reaches
the model or the logs. Reasoning is sought in every field, tool arguments included. Before untrusted text is quoted into a prompt, the
control tokens of every supported family and any line that begins with harness markup (menu letters, escape lines, section headers,
answer field names) are broken with a visible escape marker; mid-line mentions stay data, and a raw protocol token in output is a
leak. Requests get an absolute deadline besides the inactivity timeout, follow no redirects, ignore proxy variables not set in
Settings, carry no credentials in URLs, and "local" is decided from the address.

- **Why:** a small model cannot tell a mission line shaped like a menu option from a real one; a server sending a byte now and then
  never looks idle.
- **Maps onto:** `plotroom-net` (crate-map §2.3, §10; D008); `plotroom-provider-http`; capsules and intake (agent-runtime §6, §14).
- **Folds:** agent-runtime §14; doc 21 §9.3 (line-start rule); doc 51 §6.1 candidate 6; testing-strategy §12 (slow-sending stubs).
- **Tests first:** an escape-shaped line is escaped at line start but not mid-line; a slow-sending stub trips the deadline; a name
  resembling loopback is remote; reasoning inside tool arguments is refused.

### MA6 Shipped values carry evidence; measured bytes are shipped bytes [I]

Every value in a shipped preset links to its evidence (source, hash, location), with upstream facts apart from Plotroom policy; a
preset built without new measurements says so. Each recommended model entry states what was observed and what it must not be used for;
the loader refuses entries without limits or with acceptance but no evidence. The measured prompt bytes are the shipped bytes: a
wording change is a new configuration, and a template override must produce exactly its intended byte differences on a fixture
matrix. Prefix caches reset on any model or template change and are off, or a recorded condition, in experiments.

- **Why:** a small model's result belongs to one exact rendering; an unmeasured wording tweak silently voids it.
- **Maps onto:** qualification records in `plotroom-provider`; the manifest in `plotroom-model-manager` (agent-runtime §13).
- **Folds:** doc 55 §3.4 (provenance per value); D037's manifest rows ("must not be used for"); doc 40 R2's golden (overrides).
- **Tests first:** a loader fixture per refusal; a template-override matrix test; a badge naming its prompt-pack hash.

## 3. Decision steps and abstention (`plotroom-decide`, `plotroom-wilco`)

### DS1 The need to ask is computed [I]

The model fills only closed fields with what the request states; each field has its own explicit value for "the request is silent"
(one name=value line is a candidate format beside JSON). Code picks the one workflow whose requirements equal the fill, never showing
workflow names; when none matches, code computes the question from the dispatch table (the workflows that still agree and the fact
each lacks), shortened when needed by leaving out complete options and saying how many. At load, every legal fill must fit the reply
budget and each row must cover the declared fields, no more and no fewer. A refusal reports its category and never repeats what was
refused. No step asks for fields that must agree (a choice plus a "needs clarification" flag plus a quote); an ambiguous unit is asked
about, never guessed.

- **Why:** small models pick the nearest valid operation instead of asking, so asking cannot be left to them.
- **Maps onto:** IntentFill → Dispatch (agent-runtime §6; doc 21 §4.1); DG015.
- **Folds:** doc 21 §4.1 (question algorithm, two load checks); doc 55 §4.2 (extract-then-dispatch reuses it; name=value as an arm).
- **Tests first:** two agreeing workflows yield a question naming both and the missing fact; a trim reports its count; a row naming
  an undeclared field is refused; no refusal message contains the input it refused.

### DS2 Menus a small model cannot confuse [I]

Two closed value lists share a step only if visibly distinct, and a wrong-list value is its own failure type. Text that must be copied
exactly (names, callsigns, marker text, quoted lines) comes as code-listed spans: the model picks an index, code copies the characters.
A costly or binary choice may be asked twice with options reversed; disagreement becomes a user question. All matching authored
entries are shown; load order never decides. Free text over many entries is first narrowed by a keyword shortlist; the model chooses
one shortlisted id or none, quoting the words that justify it, and code re-applies every exclusion. Stable option text precedes live
state.

- **Why:** look-alike lists, paraphrased copies and position bias are failure classes doc 55 §1.1 measured; each goes by construction.
- **Maps onto:** menus (agent-runtime §6; doc 25 §6.2); free-text intake and skill activation (agent-runtime §8–§9).
- **Folds:** doc 25 §6.2 (distinct lists; the wrong-list failure type); DG006 ("right option shown" measured apart from "picked").
- **Tests first:** overlapping lists refused at load; copies of listed text keep non-ASCII and whitespace exactly; a reversed-order
  disagreement yields an `ask` card; a right entry pushed off a full shortlist scores "not shown".

### DS3 Send conclusions, keep evidence, say what was cut [I]

When code has computed the facts, the capsule carries what code concluded and leaves the underlying data out. A fact bundle carries
facts, a quality status, the allowed next actions with a default and explicit "not established" flags, and is refused if its inputs
changed meanwhile; optional explorations are never phrased as commands. After a refused reply the latest evidence stays in the
request, or the step stops. Every cut list states how many items were left out, keeping "cut for budget", "source incomplete" and
"already shown" apart. A shrinking chat drops whole middle exchanges only; long tool output shows head and tail with a marker.
Reference search merges several keyword query forms with reciprocal rank fusion (a textbook method) and says when a weaker fallback
ran.

- **Why:** a small model follows every imperative it sees and guesses at gaps; explicit flags and counts leave nothing to guess.
- **Maps onto:** the capsule (agent-runtime §6), knowledge packing (§8), Wilco chat (§9); doc 40 §4.1.
- **Folds:** agent-runtime §6 capsule segment 3 ("not established" flags; cut counts); §8 (caveats travel with their card).
- **Tests first:** a capsule golden whose cut marker states its count; a request that would lose pending evidence is not sent.

### DS4 Text slots: fixed text from code, fact tokens from facts [I]

Generated documents are templates: code writes the fixed text, each slot is filled and checked alone with the final check's rules, and
the final check refuses drift in the fixed text. Tokens only facts can supply (grid references, times, dates, unit counts, class names,
callsigns, marker names, coordinates) are refused in model text unless present in the given facts; small ambiguous numbers are left
alone. An explanation that is only a one-word verdict, asks a question back, restates the question or repeats the instructions is
refused; an explanation of findings covers every finding given and no other. A failed length or count limit reports the number found,
the number allowed and how it was counted. Code attaches citations; empty retrieval returns "not in the reference" with no call.

- **Why:** small models rewrite fixed text and invent plausible numbers; a one-step repair needs the exact measured violation.
- **Maps onto:** V-text (agent-runtime §6; doc 25 §7.1); `plotroom-template` (crate-map §8); explain mode (agent-runtime §9).
- **Folds:** doc 25 §7.1 (fact-token classes); doc 21 §5.2; agent-runtime §7 (`NotInManual` for empty retrieval).
- **Tests first:** per token class, absent refused and present accepted; a one-character drift refused; an extra finding refused.

### DS5 Diagnosis as closed moves over typed evidence [I]

A diagnose step returns exactly one of: run one listed inspection; conclude from a closed set citing only evidence shown; pause for a
typed reason. Each inspection result is marked fresh, outdated, contradicted or absent, and only a check that ran counts. The next
check proposed leaves the fewest candidate causes in the worst case, then costs least; conclusions keep their premises and go stale
with them. Graph questions are closed operations (neighbours, shortest route, dependents, nodes every route passes through), and an
empty answer means "not recorded". Proof-style campaign checks answer always, never, sometimes (one example each way) or contradictory
premises; examples replay on a separate simple interpreter, and a contradiction is shown as a smallest unsatisfiable set.

- **Why:** the model only names and phrases, and the evidence rules stop it treating a skipped check as proof.
- **Maps onto:** explain mode (agent-runtime §9); readiness (validation-and-lints §11); `plotroom-campaign-sim`, `plotroom-cxl`.
- **Folds:** doc 21 §11.2 (playbooks); doc 19 §6.4 (the four outcomes; "every route passes here" as an advisory lint).
- **Tests first:** next-check choice and the pass-through operation against brute force; every example replays; removing any condition
  from a reported contradiction leaves the rest satisfiable.

### DS6 Computed scores route; checks admit; code grants actions [I]

A stronger model is offered only when a deterministic check failed or needed evidence is missing, never because the model said it was
unsure, and a code-computed routing score (doc 53 §4.2's calibrated margin) must itself be qualified on held-out data. Whether an action
runs is decided by code from grants and actual inputs. A very small model gets one closed decision in a fresh context. A two-level
router must beat a flat menu with the same information budget; per-step model mixing must beat one model at the same budget, load and
switch costs included. Different models never vote.

- **Why:** a small model's self-reported confidence is not evidence, and every routing level is another chance to be wrong.
- **Maps onto:** candidates and clarification (agent-runtime §6); role binding (§11); doc 53 §4.2–§4.3; DG022.
- **Folds:** doc 53 §4.3 (routing score qualified on held-out data); DG006 (facets against a flat menu at equal budget).
- **Tests first:** stated high confidence plus a failed check gets the escalation card, stated low confidence plus a passed check does
  not; a safety case with valid inputs but a wrong choice still fails.

## 4. Validation and repair (`plotroom-validate`, repair in `plotroom-decide`)

### VR1 A closed repair vocabulary [I]

The text checker reports one of: a fixed fact changed, an invented item, a missing item, evidence on the wrong item, an unfilled slot,
a field too long or split, a status claimed too high, a protocol leak; each repair names one kind, and removed fixed text is quoted
exactly for restoring. A reply refused for its form (cut off, filtered, malformed) is never shown back: one fixed message asks for a
replacement, and a success counts as recovered. Consecutive malformed replies are counted apart from repairs and end the step at a
small fixed number. Prose is recovered only on an exact match with a legal answer. Model values have a declared shape: bounded length,
declared lines, no control or unpaired surrogate characters, no leading character the destination reads as syntax.

- **Why:** a small model can fix one named thing given the exact target text; it cannot decode an abstract message.
- **Maps onto:** repair in `plotroom-decide` (agent-runtime §6; doc 25 §7.2); doc 51 §4.6's repair capsule; DG016.
- **Folds:** doc 25 §7.2 (kinds; restore-exact-text); DG016 (malformed streak apart from R); doc 51 §4.7 (`InvalidAnswer` feeds it).
- **Tests first:** a fixture per kind; the streak ends the step at its count and resets on admission; a directive-marker lead refused.

### VR2 Check results carry counts that must add up [I]

Each check reports whether it ran, whether it applied, whether it had enough input and whether it found anything, with item counts
that add up; "found nothing" needs examined items and none skipped. Every cheap validator always runs; only expensive checks are
gated, by a visible condition or a click, never by the model. Several faint plausibility hints raise one advisory only when their
hand-set scores together cross a threshold tied to the realism setting; the total is shown, the advisory feeds no other rule, and a
threshold that no combination can reach is a load error.

- **Why:** a model explaining a clean result must be told what was not checked, or it will say "healthy".
- **Maps onto:** `RuleOutcome` (validation-and-lints §2: `Ran`, `NotApplicable`, `Inactive`); plausibility rules (§3; D011).
- **Folds:** validation-and-lints §2 (`Insufficient` and counts; this doc's §10 candidate 1); §3 (weighted advisories).
- **Tests first:** counts add up for every outcome; "found nothing" with skipped items cannot be built; no advisory below threshold.

### VR3 Slow references as oracles [I]

Every clever algorithm keeps a slow, obviously correct reference, compared on seeded random inputs; expected values never come from the
code under test, "impossible" or "always" claims are checked independently, and a run resumed midway equals an uninterrupted one. A
seeded generator that claims a distribution gets a goodness-of-fit test against critical values fixed in the test. Across repeated
probe runs, events seen in every earlier run but not this one are flagged, and lines without timestamps are kept in a visible count
rather than discarded.

- **Why:** harness facts come from these algorithms; a wrong fact is one no model can fix.
- **Maps onto:** `plotroom-campaign-sim`, `plotroom-cxl`, `plotroom-generate` (crate-map §8); run reports (testing-strategy §13).
- **Folds:** testing-strategy §5 (reference-versus-fast rows); §13 (ordered per-entity probe assertions).
- **Tests first:** the comparisons themselves, each first seen failing on a bug planted in the fast version.

## 5. Evaluation and qualification instruments (`plotroom-evals`, `tools/local-qual`)

### EQ1 Results sealed by identity and re-checked at the end [I]

Each result records hashes of the model file, runtime build and libraries, chat template, context, quantisation, full sampler, thinking
switch, prompt prefix and tool schemas per decision kind, preset, suite and scoring code, plus a hardware label; the runner re-checks
them at the end and discards the run if anything changed. Input files are bound to their role (tuning or held-out). Configurations are
compared only if the declared variable is the only difference and it actually differed. A gate judges the one candidate it was set up
for, never whichever row scored highest; exact counts are compared, never rounded ones; a missing case is an error; a provider that
cannot be reached is a service fault left unscored, never counted against the model. Published summaries are recomputed from per-call
records in CI.

- **Why:** small-model differences are a few items, smaller than one undeclared change or rounded figure.
- **Maps onto:** `plotroom-evals` (agent-runtime §7; testing-strategy §10); `tools/local-qual` until the Rust port.
- **Folds:** doc 55 §4.3 (end-of-run re-check; role-bound inputs); doc 51 §5.7 (comparator); testing-strategy §14 (recompute gate).
- **Tests first:** the comparator refuses undeclared differences and an unchanged variable; a deleted case fails; outages go unscored.

### EQ2 Fair ordering and exact early stopping [I]

Arms compared on one machine are interleaved item by item and rotated, so none always runs first or cold; for a few arms, a balanced
Latin square puts each arm once in each position, following every other equally often. An exact sequential probability ratio test in
rational arithmetic (every machine decides alike) may stop a clearly bad or good candidate early; a passed screen is never acceptance.
Winners and the baseline are confirmed on fresh seeds with the option order reversed. Calls are never retried to improve a score, and
an arm with missing results has no score.

- **Why:** cache warmth and order effects are as large as the knob effects expected on small models.
- **Maps onto:** `plotroom-evals`; the Model Manager's "Check this model on my machine" (agent-runtime §13).
- **Folds:** doc 55 §4.3 (interleaving; reversed-order confirmation); doc 21 §12.3 (sequential stopping for the smoke check).
- **Tests first:** Latin-square properties for several arm counts; the stopping decision matches a committed rational golden.

### EQ3 Items, not calls, and an ordered verdict list [I]

The unit is the test item: an item is stable when most repeats pass; count items only one setup made stable, apply an exact sign test,
show the paired table, split the error budget over simultaneous claims, and always report the no-model path. A candidate is adopted only
if pass rate and stable-item count rise by declared amounts, slowdown stays within a declared ratio and no single item gets worse;
both arms are scored on anonymised copies, and a baseline that failed to run voids the comparison. Verdicts come in order: invalid,
regression, no improvement, inconclusive, supported. The baseline for a preset is the general fallback preset; for a workflow, the
no-model path. Rankings put correctness ahead of speed and penalise confident wrong choices; the suite declares the full order.

- **Why:** repeats of one item are not independent, so pooled call counts overstate small-model gains.
- **Maps onto:** `plotroom-evals`; doc 55 §4.4 (PR1–PR9).
- **Folds:** doc 55 §4.4 (verdict order; anonymised scoring; items the baseline passes cannot show gains); doc 21 §12.3.
- **Tests first:** the verdict function's truth table; exact sign-test values against a committed table; no arm label reaches scoring.

### EQ4 Abstention is its own instrument [I]

Every choice suite runs "always ask", "always none fit" and "always first option" controls and scores the two escapes separately: "I
need more information" and "none of these can do it" are different correct answers. A decline set includes "should act" controls, is
seeded, fingerprinted by item ids and re-verified after the run, and reports an exact one-sided upper bound (Clopper-Pearson) on the
false-action rate, conservative after early stopping. Declinable menus report how often the model commits when it should and how often
it is wrong when it commits; a rate with nothing to divide by has no value, never 0 or 100%. Every set holds a known positive, a
clean negative, a just-below-threshold case, a harmless case that resembles a real one and a multi-item case.

- **Why:** a pass rate rewards a small model that always asks; split escapes show whether it declines for the right reason.
- **Maps onto:** instruments in `plotroom-evals` (testing-strategy §10); doc 25 E4; doc 21 §12.1–§12.2.
- **Folds:** doc 21 §12.1 ("always none fit" control; split escape scores); doc 55 §4.1 (the five case types in held-out sets).
- **Tests first:** each control gets its degenerate score; the bound matches committed goldens; a rate with nothing to divide by
  reports no value.

### EQ5 Held-out hygiene you can check [I]

The held-out set is fixed and its hash recorded before tuning starts; it is kept out of every prompt, preset, exemplar and repair
loop, seeded with unique marker strings that CI scans tuning material for, and scored once after settings freeze. After a possible
leak, what is discarded is decided before any held-out score is seen. Items split by scenario family with a seeded hash, never by
position; a set dominated by one trap type or missing act or decline items is refused. Automatic rejections are reviewed by hand, but
the official score stands, and checkers change only in the next frozen version. Fixtures a stronger model proposes must pass the
product's validators and never become held-out items.

- **Why:** held-out evidence is the only guard against a preset tuned to the test instead of the model (D048 item 4).
- **Maps onto:** `tools/local-qual` suites; an `xtask` scan in CI (crate-map §12).
- **Folds:** doc 55 §4.1 (markers, leak protocol, family split, coverage refusal); doc 21 OQ2.
- **Tests first:** the marker scan over the prompt pack and presets; family-split determinism; a coverage-refusal fixture.

### EQ6 One outcome, one layer, one claim level [I]

Replies are passed, missed, invented or correctly silent; runs are first-pass success, success after recovery, legitimate pause,
failure or incomplete. Pauses are never successes and incomplete runs never zeros. A model is credited only with its typed difference
from the no-model run. Each failure has one layer (transport, format, choice, harness or code, defective check, defective item), and
diagnosis tries code first (reachable? every fact supplied? would code alone solve it?), never a longer prompt. A run is model
evidence only if it echoes a one-time token, made a real call and names the check of its end state that passed. Claims are labelled
by reach (an operation; a checked flow; one exact setup; users finish faster); cost is per independently accepted result.

- **Why:** without one layer per failure, harness defects get blamed on small models and the wrong fix (a bigger model) follows.
- **Maps onto:** `plotroom-evals`; doc 21 §12.1's attribution order; doc 51 §4.7's accounting table.
- **Folds:** doc 21 §12.1 (six layers; code-first diagnosis); §12.3 (smoke check with a one-time token); doc 40 §7.
- **Tests first:** the classifier's exhaustive table; an attribution fixture per layer; a run with no model call is never evidence.

### EQ7 Honest throughput and a drift watch [I]

Throughput sums tokens and durations and divides once; percentiles have one stated definition; unobservable metrics are "unavailable".
Phases are timed apart (load, verify, first token, generation, validation), and time to an accepted result is reported. Live acceptance
and latency are watched per setup with the median, the median absolute deviation and a cumulative-sum change detector; a sustained
change offers re-qualification with the numbers. Exports carry the hardware class only.

- **Why:** a small model that answers fast but wrong looks best on a naive speed metric.
- **Maps onto:** `plotroom-evals`; Model Manager badges (agent-runtime §13); DG012.
- **Folds:** DG012 (drift as a trigger); agent-runtime §13 (time to an accepted result on badges).
- **Tests first:** a fixture where mean-of-rates and sum-then-divide differ; a change-detector golden; an export with no machine name.

## 6. Local model management (`plotroom-model-manager`, `plotroom-net`, `plotroom-io`, `plotroom-preview`)

### MM1 Downloads trust only a proven resume point and the manifest size [I]

Show size and licence before any byte moves. Resume a partial download only if the server's reply proves it continues from the exact
byte where the local copy ends; never write past the size recorded in the manifest; verify the hash; install only if the destination
did not change meanwhile, then check again in place. Models, presets and packs update as one versioned set, atomically, with rollback
to the last set that passed qualification.

- **Why:** a corrupt or swapped file makes a small model produce nonsense that looks like a model limitation.
- **Maps onto:** `plotroom-net` downloads and `plotroom-io` installs (crate-map §2.3, §10; agent-runtime §13).
- **Folds:** agent-runtime §13 (range, size and destination checks; set rollback); doc 55 §3.5 (presets roll back with their set).
- **Tests first:** a stub ignoring the range restarts, not appends; bytes past the manifest size fail; a changed destination blocks.

### MM2 A scrubbed, recorded, verified launch and a stop record [I]

The managed server starts on loopback with its web interface and network fetches off and a scrubbed environment; exact arguments and
variables are recorded for a "show launch" diagnostic; the port is checked free, and the answering server must be the one launched.
GPU-to-CPU fallback happens only at start-up and is a separate setup; a user file's prompt format comes from its embedded template's
fingerprint, never its name. Crossing a free-memory floor stops with a message instead of shrinking context or switching models.
Stopping records once what was observed (already exited, stopped, killed, still running), never rewritten, and proves the model was
unloaded before Preview.

- **Why:** an inherited variable or a stale server silently changes the qualified setup, and a resident model starves the game.
- **Maps onto:** sidecar start-up and supervision (agent-runtime §3, §13; crate-map §10); `plotroom-preview` run records.
- **Folds:** agent-runtime §3 (scrubbed environment, launch record, answering-server check); §13 (memory floors; stop record).
- **Tests first:** with a fake server helper, a taken port and a server of another build are refused; an injected variable map never
  reaches the child; a process ignoring termination yields "killed"; a double stop yields one record.

## 7. Tracing and the decision journal (`plotroom-workflow-runtime`, session logs)

### TJ1 Every harness utterance is a record; history holds only admitted answers [I]

Every message the harness adds (a repair note, a correction, a reminder) is its own journal record, so any result traces to the model,
a tool or the harness. When a reply carries a valid answer plus chatter, only the admitted answer re-enters history; the chatter is
logged by hash. Reasoning blocks a provider needs back travel only inside the live exchange and are never stored. Logs keep sizes,
hashes, counts and decisions; raw text is a warned opt-in. The cacheable prefix of each request is hashed and logged, so a change
within one cache namespace is a visible event, and the hit rate comes from the provider's own counters.

- **Why:** a small model imitates its own earlier chatter, and a lost prefix cache doubles its latency and invites blaming the model.
- **Maps onto:** `JournalRecord` (agent-runtime §5); session logs (§9); the run panel (§12); doc 40 R2–R4, R10.
- **Folds:** agent-runtime §5 (a record kind for harness messages); §12 (a "prefix changed" event); DG017 (chatter hashes).
- **Tests first:** a repair run's golden journal holds the repair note; the capsule after a chatty reply holds only the admitted
  value; a sentinel in reasoning never reaches a log; a volatile field above a breakpoint raises the prefix event.

### TJ2 One owner per journal; labels travel [I]

Resume state is a closed, validated record of harness facts; identity checks run on reopening, and a mismatch parks the run. Only one
runner owns a journal at a time; a lock left by a crash is reported, never silently broken. Every input carries its origin and trust,
and every output inherits a sensitivity label: a prompt built from a user's mission is as private as the mission, and sending or export
follows the label.

- **Why:** two runners on one journal can double-commit or double-pay, and a resumed run must not trust stale state.
- **Maps onto:** resume and storage (agent-runtime §5; DG017); trust labels (§14; doc 21 §9); egress cards (extensibility §8).
- **Folds:** DG017 (the lock); doc 21 §9.1 (sensitivity inheritance); agent-runtime §5 (export follows labels).
- **Tests first:** a second runner is refused; a stale lock is a user-visible state; output derived from a private input is private.

### TJ3 Recorded traces and injected defects gate the harness [I]

Recorded traces replay as tests, a replay whose expected output is impossible is vetoed, and the prompt rebuilt from saved state must
match its recorded bytes. The engine runs on several deliberately different definitions (menus only; fills with questions; fan-out cut
by budget midway; no model; a failed compose that splits; plugin tools). Named defects are injected at exact places, and each must be
caught by the check meant to catch it; a crash or timeout does not count. Each new gate is first seen failing on a negative control.

- **Why:** the harness carries the weight for weak models, so it needs regression evidence independent of any model.
- **Maps onto:** golden journals and cassettes (testing-strategy §9; doc 38 §6.4); `plotroom-testkit` (crate-map §12).
- **Folds:** testing-strategy §9 (defect matrix; negative control first); doc 38 §10 (a prompt-rebuild test beside AT-W3).
- **Tests first:** the defect catalogue, each entry red against its seeded defect before the gate exists.

## 8. Packaging (`plotroom-export`, `plotroom-packs`, `plotroom-mcp`, `plotroom-plugin-host`, `xtask`)

### PK1 Positive-list, reproducible bundles and sealed packs [I]

Shared bundles are built from a positive list, so hidden files and runtime leftovers (caches, journals, databases) are excluded by
construction. Bundles are versioned by a digest of their bytes and byte-reproducible (fixed member order, timestamps, permissions);
verification regenerates and compares; an existing export is never overwritten; names that collide on another OS (case folding,
reserved device names) are refused. A pack partly removed or failing its seal is reported as disabled, never clean.

- **Why:** a journal leaking into a shared mission ships AI leftovers, and a non-reproducible bundle cannot be audited.
- **Maps onto:** `plotroom-export` (crate-map §8); built-in packs (extensibility §3.5); export stripping (agent-runtime §5).
- **Folds:** testing-strategy §7 (regenerate-and-compare beside the export scan); extensibility §3.2 (seal state).
- **Tests first:** a planted journal never ships; case-folding and reserved-name collisions are refused; a rebuild is byte-identical.

### PK2 Model-facing names and stored shapes are CI-checked [I]

CI confirms that every tool, argument, enum value, card, workflow and skill named in prompts, cards, primer sections and lessons exists
in the registry. Activation phrases ship with load-time tests (a positive case per entry, a no-match case, a case per exclusion proving
it wins, no phrase in two entries); no match or several means ask. Skill descriptions are bounded and markup-free, and nothing
executes. The shape of every stored format (journal, qualification and replay records, preset files, manifests, sidecar records) sits
beside its version; CI fails when it changes without a version decision (a new key that may be absent leaves the version alone;
deleting a key, changing its type or making it mandatory raises the version).

- **Why:** a small model trusts every name it is shown, and qualification records outlive releases and their shapes.
- **Maps onto:** `xtask` drift checks (testing-strategy §14; crate-map §12); skills (extensibility §5; D019); `plotroom-sidecar`.
- **Folds:** testing-strategy §14 (name and shape gates); extensibility §5 (activation tests; skill bounds); doc 55 §3.3 (versioning).
- **Tests first:** a prompt naming a removed tool fails; clashing phrases are refused; a negative shape change per format fails.

### PK3 The loopback server and query surface defend themselves [I]

A local helper server binds to loopback, accepts only its exact Host value (against DNS rebinding), refuses cross-origin requests, caps
request size, time and response, and never echoes errors. External agents get named read-only queries with typed filters and page
limits, never a query language; each reply carries its data revision, and an over-large result returns its size instead. The server
enforces its own per-session call and repetition limits. No component installs schedulers, services, autostart entries or detached
processes. A headless job is closed data (input, workflow, model use with full sampler and budget, outputs); anything unspecified is an
error.

- **Why:** external agents may be driven by weak models too; limits in the editor hold whatever the caller does.
- **Maps onto:** `plotroom-mcp` (extensibility §10; agent-runtime §15); `plotroom-plugin-host`; `plotroom-cli` (crate-map §10–§11).
- **Folds:** extensibility §10 (Host check, caps, session limits); crate-map §2.3 (no schedulers or autostart, checked statically).
- **Tests first:** a spoofed Host and a foreign Origin are refused; an over-large query returns its size; the repetition limit trips.

## 9. Boundaries kept, and tensions found

**Boundaries** [I on V]: models never author executable plans or receive command-line style instructions; authority comes only from
typed user intent and egress grants (agent-runtime §2; commands-undo-history §4.4); acceptance gates are in-process; models are fitted
by adapting the harness, never by training (D048 item 3; D027). A public table of rejected designs, reopened only on new evidence,
would list: confidence numbers shown to a weak model; thresholds that adapt at run time (tuned thresholds frozen per preset version do
not); model-written memory or summaries (doc 40 §8); repairing malformed tool calls into valid ones; files opened by the model; bulk
raw reads into the window; voting across different models; budgets as a fraction of a window.

**Tensions with current docs** [I]:

1. **Window-fraction budgets.** Doc 38 §3.5 sizes the free-chat skill catalog at about 2% of the window; WR6 states budgets in tokens
   from the per-request context, because an advertised window is not what a request can use.
2. **Voting versus asking.** Agent-runtime §6 and doc 25 §7.3 vote over permuted Pick samples (DG021); DS2 asks the user when a
   reversed-order double ask disagrees. Proposal: vote for ordinary Picks, ask for costly or binary ones; the step says which.
3. **Per-item regressions.** Doc 55 PR4 tolerates up to two menus lost per held-out category; EQ3 adopts only if no single item gets
   worse. Stricter may suit small suites and be too strict at 120 menus; the owner or the first tuning run decides.
4. **Graders.** Doc 55 §4.6 grades EXPLAIN and text with LLM graders; EQ6 and doc 21 §12.3 keep smoke checks and closed decisions on
   deterministic checks. Consistent only if LLM grades never gate admission or badges alone (doc 51 §4.9; doc 55 OQ9).
5. **Deterministic cleanup.** Doc 51 §4.5 step 4 strips an outer fence or a BOM; MA3 forbids repair into a valid-looking answer.
   Consistent only if each cleanup is logged and never counts as first-pass (doc 51 §4.5 step 9).

**Fold targets, collected:** agent-runtime §3–§6, §9, §12–§14; crate-map §2.3–§2.4; testing-strategy §5, §7, §9, §12–§15;
extensibility §3.2, §5, §10; validation-and-lints §1–§3; docs 19 §6.4, 21, 25 §6.2 and §7, 38, 40, 51 §4–§6, 53 §4.3, 55 §2–§4;
DG006, DG012, DG016, DG017. Each pattern's **Folds** line says what changes where.

## 10. Design-gap candidates (listed, not filed)

1. **Check outcomes with counts** (validation-and-lints §2): `Insufficient` plus item counts that must add up in
   `RuleOutcome`, with "found nothing" unrepresentable when items were skipped. Technical.
2. **Harness-authored journal records** (agent-runtime §5; DG017): a record kind for repair notes, corrections and reminders, and only
   admitted answers re-entering history. Technical.
3. **Operation policy as data** (doc 38 §4.2; DG016): repeatability, retry, reuse, approval and undo per step kind and code step, with
   retry causes as a closed list. Technical.
4. **Journal ownership** (DG017): a single-owner lock with user-visible stale-lock handling. Technical.
5. **Adoption on small suites** (doc 55 PR4 against EQ3): whether any single-item regression blocks adoption. Owner or technical.
6. **Routing scores need their own qualification** (doc 53 §4.2–§4.3): a computed margin routes only after held-out calibration;
   self-reported confidence never routes. Technical.
7. **Token budgets instead of window fractions** (doc 38 §3.5; doc 40): every budget is a token count derived from the per-request
   context the runtime reads back. Technical.

## Open questions

1. Which patterns belong in roadmap M4's no-model runtime and M6's Wilco, and which wait for doc 55's first tuning run? [I]
2. Do the always-none control and split escape scores apply to the spike-checked records of docs 44 and 46, or only from the Rust
   port of the suites on? [I]
3. Is a Latin square worth its complexity for the two-arm comparisons that dominate doc 55's plan, or is alternation enough? [U]
4. Which leading characters count as syntax per destination format (config, script, stringtable, briefing HTML), and does
   `plotroom-template` own that table? [U]
5. Does MM2's answering-server check need a launch nonce, or are build and path from the properties endpoint enough? [U]

## Verification notes

### 2026-09-28, author checks at write-up

- **Read for this doc:** agent-runtime in full; crate-map §1–§2 and §8–§12; testing-strategy in full; extensibility §1–§10;
  validation-and-lints §1–§4; doc 21 §12; doc 38 §3.2–§4.6, §6.2–§6.4 and §10; doc 51 §3.10–§6.4; doc 53's TL;DR and §4.1–§4.8;
  doc 55 in full; D044, D045 and D048; the design-gap index.
- **Every pattern is a proposal.** No model was loaded, no code written, nothing measured. Section references were checked against the
  sibling docs' headings on 2026-09-28; no fold was discussed with those docs' owners.
- **Not verified:** what each pattern costs against what it saves; whether §5's rules have enough power at doc 55 §4.1's suite sizes;
  any serving-stack behaviour beyond what docs 46, 51 and 55 record.
- **Folding steps, not done here:** a row for this doc in `docs/README.md`; the folds; filing the §10 candidates.
