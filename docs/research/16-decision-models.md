# Decision Models (Jev, Kev, Laya, CLM) and the Selector Seam

Research doc 16 for `ofp-editor`. Research date: 2026-09-26. Audience: contributors and LLM coding agents. This file is meant to be read
on its own.
Question answered: what are "decision models", which public ones exist, where could one help the editor's built-in agent, where must it
never be used, and what must be true before we ship one?

**Epistemic legend.** **[V]** = verified against a public primary source fetched on 2026-09-26 (URL given inline or in Sources).
**[V-author]** = a number or claim the model's own author or vendor published; quoted correctly, not reproduced by anyone we know of, and
not reproduced by us. **[I]** = inferred by us; every design proposal in §3–§6 is [I] unless marked. **[U]** = unknown, needs measurement.

**Relation to sibling docs.** Model tiers and packaging are in doc 14. Local inference and constrained decoding (including reading option
probabilities from logits, doc 13 §4) are in doc 13. pi-ai's `classify()` slot for Jev is in doc 11; rig's `rig-typesafeai` client is in doc 12
§1.9. The weak-model workflow layer (menus, candidate selection, evaluation controls) is in doc 25. The agent's general doctrine is in
[21-agent-doctrine.md](21-agent-doctrine.md). Weight licensing and "do not bundle weights" are in doc 02. This doc does not repeat them.

**Glossary.**

- *Generative model*: an autoregressive LLM or SLM that writes tokens (text, JSON, tool calls). SLM here means a small, locally runnable one.
- *Decision model*: a non-generative model that takes a text *state* plus *typed questions* and returns a probability for each allowed
  answer, or ranks candidates it is given. It writes nothing. TypeSafe AI calls this class "System One" models.
- *Choice / Score / Noul*: the three question types in the Jev family. Choice = one of N options; Score = a level on an ordinal scale;
  Noul = yes/no as a probability.
- *Menu*: a code-computed list of options that are all valid in the current editor state (doc 25).
- *Selector*: our proposed Rust seam (§4.2) that turns a request plus a menu into `Candidate`, `NoMatch` or `Clarify`.
- *Calibration*: whether a stated 0.8 probability is right about 80% of the time. *ECE* (expected calibration error) measures the gap.

## TL;DR

- **Decision models choose; they do not write.** Jev, Kev and Laya take a state and typed questions and return a probability per option in
  one forward pass. CLM ranks candidates you supply. None generates dialogue, briefings or scripts, which are our highest-value AI tasks [V].
- **Jev (TypeSafe AI)** is the reference: hosted API only, `jev-1.13.0`, 64k tokens per request, text only, $0.042 per million input tokens,
  output free [V]. The vendor documents real weaknesses: literal reading, no counting or arithmetic, dates read as text, distraction by
  irrelevant state, and no built-in suspicion of adversarial content [V].
- **Kev (`jaredpalmer/kev-*`)** is an open Apache-2.0 family with the same state-plus-typed-questions interface: a rank-16 LoRA adapter and a
  pointer head on Qwen base models from 0.5B to 27B [V]. Its 0.8B card says it "trails Jev everywhere it can be compared" [V-author].
- **Laya (`convaiinnovations/laya`)** is an Apache-2.0, 421M-parameter ModernBERT-large encoder (plus a 322M multilingual variant). It is the
  only candidate small enough to run on CPU inside a desktop editor, but its base checkpoint is "near chance" zero-shot and needs
  fine-tuning and temperature calibration [V-author].
- **CLM (Contrastive-LM CLM-v0.1-8B)** is Apache-2.0 projection heads on a frozen Qwen3-8B encoder that rank supplied candidates. It needs a
  GPU and a vLLM-served encoder, which is out of scope for a desktop editor [V/I].
- **Nobody has measured any of them on editor tasks.** Every quality number below is an author claim [V-author].
- **Where one could help [I]:** picking which *authored* clarification question to ask; shortlisting a workflow from free text; advisory
  ordering of candidates that validators already accepted; cheap advisory flags (tone, era).
- **Where one must never decide [I]:** facts (catalog, island, engine limits), arithmetic, geometry, dates, IDs, permissions, legality,
  acceptance of generated content, and anything that should be authored.
- **Recommendation for v1 [I]: no decision model in front of the generative model.** Build a `Selector` seam that returns
  `Candidate | NoMatch | Clarify`, ship a deterministic selector and a generative (constrained tool-call) selector first, and treat every
  selector output as an untrusted proposal that code re-checks.
- **A decision model earns an advisory slot only by clearing our evidence bar (§5):** it beats both the deterministic and the generative
  baseline on our own frozen routing and clarification instruments, holds up on held-out cases, and fits our latency, RAM, license and
  offline limits.

## 1. What a decision model is

### 1.1 Generative models versus decision models

| | Generative model (LLM/SLM) | Decision model |
| --- | --- | --- |
| Output | Free tokens: text, JSON, tool calls | A probability distribution per typed question, or a ranking of supplied candidates |
| Type errors | Possible; prevented only by constrained decoding and validation (doc 13 §4) | Impossible by construction: it can only point at an offered option [V: vendor claim "never makes type errors"] |
| Calls per answer | Many decode steps | One forward pass for all questions [V: Kev, Laya cards] |
| Can author content | Yes | No [V: Jev "is not trained to generate text"] |
| Confidence | Not native; must be derived (logits, sampling agreement) | Native per-option probability, calibrated by the author on the author's data [V-author] |
| Typical failure | Invents facts, drifts from schema, skips clarification | Picks a valid but wrong option with confidence; reads the question literally |

A decision model is therefore a **typed classifier with a question interface**. It is not a smaller LLM. The vendor defines the class as
models "built to make fast, structured decisions that software can use directly" that evaluate "a state and return typed answers and
probabilities" [V: https://docs.typesafe.ai/concepts/system-one].

### 1.2 The shared interface

1. **State.** One text document: a ticket, an email, JSON, or in our case a small code-built digest of the editor state plus the user's request.
2. **Questions.** Each question has a type and a closed answer set: Choice (N labelled options), Score (ordinal levels), Noul (yes/no).
3. **Answer.** For each question, a probability per option. No prose, no explanation, no reasoning trace.

CLM differs: instead of fixed questions it embeds the state and each candidate action, and ranks candidates by similarity with a softmax over
the offered set [V: https://github.com/Contrastive-LM/CLM].

### 1.3 Properties that matter for an editor agent

- **Probabilities are relative to the menu.** CLM's softmax makes every probability depend on which candidates were offered [V: CLM README].
  Jev does not guarantee that separate questions are mutually consistent; P(yes) and P(not yes) asked separately need not sum to 1
  [V: Jev 1.13 limitations page]. So a probability is never comparable across different menus [I].
- **Literal reading.** Jev "answers the question you wrote, not the one you meant"; negations and scoping words are read at face value
  [V: Jev limitations]. Question wording becomes part of the tested artifact [I].
- **No arithmetic, counting or date ordering.** The vendor writes "Jev is not a calculator" and recommends putting math in code
  [V: Jev limitations]. Distances, crew-seat counts, group limits and timings in our editor stay in Rust [I].
- **Distraction and hostility.** Accuracy falls as unrelated state grows, and the model "does not treat [adversarial content] as hostile by
  default" [V: Jev limitations]. Mission text downloaded from the internet is exactly such content (AGENTS.md: untrusted content) [I].

## 2. The four public models

### 2.1 Jev (TypeSafe AI) — hosted reference

- **What it is.** TypeSafe's first System One model. Launch post dated 2026-09-15, initially in early access with a waitlist [V: launch post].
- **Version and limits.** `jev-1.13.0`; aliases `jev-latest` and `jev-preview` both point to it today. 64k tokens per request, of which state
  plus the longest question may use 32k. Text input only. English is the primary language; others work with weaker guarantees
  [V: https://docs.typesafe.ai/models].
- **Price and rate limits.** $0.042 per million input tokens; output tokens free; 250,000 tokens/s and 1,200 requests/min listed [V: models
  page]. Vendor prices and limits can change.
- **Availability.** Hosted API only. "The same weights serve every account"; customization goes through the state, instructions and
  criteria, not per-account fine-tuning. We found no downloadable weights and no parameter count in the public docs [V: models page].
- **Data handling.** The vendor says it does not train on customer requests; zero data retention is offered to enterprise customers
  [V: models page].
- **Author claims.** "Two orders of magnitude faster and more efficient" than LLMs on System One tasks; 70–500 ms responses [V-author:
  launch post].
- **Public study closest to our use.** The vendor's skill-suggestion cookbook ranks 182 skills from the Hermes catalog with `jev-1.12` in front
  of an agent, over 488 synthetic requests (315 covered by one skill, 173 by none). Wrong first skill loads fell from 16.8% to 7.3% and
  unneeded loads from 9.8% to 4.0%; an oracle scored 2.5% / 1.2%. The suggestion fixed 37 requests and **broke 7 that the agent had right
  on its own** [V-author: https://docs.typesafe.ai/cookbooks/skill_suggestion]. A net gain, not a free one [I].
- **Existing client code.** pi-ai exposes Jev through `classify()` (doc 11); rig has an experimental, unpublished `rig-typesafeai` client
  whose README warns "Confidence measures concentration, not correctness" (doc 12 §1.9) [V].

### 2.2 Kev (`jaredpalmer/kev-*`) — open, same interface

- **What it is.** "A decision model: one document (the state) and a set of typed questions in, a probability distribution per question out,
  in one forward pass" [V: https://huggingface.co/jaredpalmer/kev-4b]. It generates no text.
- **How it works.** A rank-16 LoRA adapter plus a pointer head on a Qwen *base* (not instruct) checkpoint. The adapter is small (about 11.3M
  parameters at 0.8B, 33.8M at 4B); the base model supplies most of the size [V: 0.8B and 4B cards]. A fitted temperature ships with the
  head (2.35 at 0.8B, 2.41 at 4B); it changes confidence, never the chosen answer [V-author].
- **Sizes and bases** (Hugging Face `base_model` tags): 0.5B on Qwen2.5-0.5B (tagged `prototype`); 0.6B and 8B on Qwen3 Base; 0.8B, 4B and
  9B on Qwen3.5 Base; 27B tagged `Qwen/Qwen3.8-27B`. Created 2026-09-18 to 2026-09-24 [V: Hugging Face API listing].
- **License.** Apache-2.0 for adapter and head; the Qwen3.5 bases are also Apache-2.0 [V: cards].
- **Resources.** About 9 GB of GPU memory for the 4B in bf16 [V-author]. The 0.8B card reports about 0.33 s for a five-question request on
  Apple silicon (MPS, bf16) [V-author]. The reference runtime is Python (`transformers`, `peft`) [V].
- **Author claims.** Kev-0.8B "trails Jev everywhere it can be compared" on the author's development splits (for example 0.648 vs 0.857
  out of domain). Kev-4B reports 0.490 on MMLU-Pro against 0.840 for Jev [V-author].
- **Ports.** Community GGUF, ONNX and CoreML conversions of Kev-0.8B exist, plus `espetro/kev-0.8b-mistralrs`, a mistral.rs (Rust
  runtime) port [V: Hugging Face search]. None is checked by us [U].
- **Interpretation [I].** Kev is the open, self-hostable option with the Jev interface. Whether it is affiliated with TypeSafe is not
  stated on the cards we read [U].

### 2.3 Laya (`convaiinnovations/laya`) — small encoder

- **What it is.** "Multilingual, non-autoregressive System 1 decision model. Give it a state … and typed questions; it returns typed answers
  with … calibrated probabilities in a single forward pass" [V: https://huggingface.co/convaiinnovations/laya].
- **How it works.** An encoder, not a decoder. English variant: ModernBERT-large backbone (395M) plus a small decision head (two transformer
  layers, an option-marker scorer, an act/escalate head), 421,293,830 parameters in total; context 512 tokens. Multilingual variant:
  mmBERT-base, 322M, context 1,024 tokens (expandable to 8,192) [V: card; API metadata]. Primitives: `choice`, `score`, `noul` [V].
- **License and date.** Apache-2.0; created 2026-09-18 [V: API metadata].
- **Latency (author claims).** About 33 ms for one question on a T4 GPU, about 193–464 ms on CPU; the card compares this with 236–276 ms p50
  for hosted Jev [V-author].
- **Critical caveats (author claims).**
  - Base checkpoints are "near chance on typed-decisions zero-shot": 0.362 English and 0.352 multilingual, below the card's 0.461
    majority-class baseline. A fine-tuned checkpoint reaches 0.766 on the author's 2,000-decision set [V-author].
  - It "ships over-confident"; refitting one temperature per question type and option count brings mean ECE to 0.081 [V-author].
  - Weak with many options: 0.425 on the 77-way Banking77 task against 0.870 for Jev, because options share a fixed token budget. Ordinal
    `score` questions are its weakest type; `noul` can follow option labels instead of the state; the act/escalate signal "carries no
    usable signal" [V-author].
- **Tooling and ports.** The author ships a fine-tuning notebook targeting two T4 GPUs and an optional ONNX Runtime extra [V-author].
  Community ONNX (including int8), GGUF, CoreML, MLX and LiteRT ports exist [V: Hugging Face search].
- **Interpretation [I].** The only candidate that plausibly runs in-process on a player's laptop without a GPU. The 512-token English
  context forces a very small state digest, which matches how doc 25 already sizes prompts. Useful only after fine-tuning on our own
  typed editor decisions.

### 2.4 CLM (Contrastive-LM CLM-v0.1-8B) — candidate ranker

- **Name.** "CLM" is ambiguous. We read it as Contrastive-LM's CLM-v0.1-8B, the only public System-One-style model by that name we found [I].
- **What it is.** "A new class of System One model trained with a contrastive learning objective that connects states and actions": two
  small projection heads (state and action) on a **frozen Qwen3-8B encoder**, trained with a bidirectional InfoNCE loss. It scores and ranks
  candidates you supply [V: https://huggingface.co/Contrastive-LM/CLM-v0.1-8B].
- **License.** Apache-2.0 for the heads and for the Qwen3-8B encoder [V].
- **Serving.** `pip install contrastive-lm`; a vLLM server running Qwen3-8B; a GPU (tested on RTX 4090 and H100); CPU works but slower. States
  longer than 2,048 tokens are truncated by default [V: https://github.com/Contrastive-LM/CLM].
- **Author claims.** "On par with Jev on computer-use, gaming and tool-calling tasks, with up to 9× lower latency". The card adds that "the
  SOTA agentic-benchmark numbers come from fine-tuned heads, not this checkpoint zero-shot" [V-author].
- **Interpretation [I].** Out of scope for a desktop editor (8B encoder, GPU server). Its lessons still apply to any selector: pin the
  encoder, pooling and head files; refuse silent truncation instead of trimming the state; log the candidate set with every probability.

### 2.5 Side by side

| | Jev | Kev | Laya | CLM-v0.1-8B |
| --- | --- | --- | --- | --- |
| Output | Choice/Score/Noul probabilities | Per-question distributions | choice/score/noul | Ranking of supplied candidates |
| Architecture | Undisclosed | LoRA + pointer head on Qwen decoder base | ModernBERT / mmBERT encoder + head | Heads on frozen Qwen3-8B encoder |
| Size | Undisclosed | 0.5B–27B (base) | 421M / 322M | 8B encoder |
| License | Proprietary service | Apache-2.0 | Apache-2.0 | Apache-2.0 |
| Availability | Hosted API | Open weights; community GGUF/ONNX/CoreML/mistral.rs ports | Open weights; community ONNX/GGUF/CoreML/MLX/LiteRT ports | Open weights; Python + vLLM |
| Offline in our editor [I] | No | 0.8B plausible; 4B+ needs a GPU | Plausible on CPU | Impractical |
| Ready zero-shot | Vendor-trained | Trained on the author's data mix | Near chance; needs fine-tuning | Zero-shot checkpoint; best claims use fine-tuned heads |
| Independent evaluation on editor tasks | None | None | None | None |

## 3. Where a decision model fits in our editor agent

### 3.1 The order of deciders [I]

The editor already knows most intents without any model: a toolbar button, a context menu or a command-palette entry names the operation.
We therefore apply one rule before any model is asked to choose: **use the cheapest decider that is always right.** In order:

1. the user's own gesture (the UI already chose; do not choose again);
2. Rust code and domain rules (engine limits, geometry, validation);
3. loaded data (unit and vehicle catalogs, island locations, the mission's own names);
4. schemas and templates (the menu of valid operations and slot types);
5. the user's explicit answer or approval;
6. a learned chooser (a decision model, or a generative model forced to pick from a menu), advisory, with a way to say "none" or "ask";
7. free generation, for the parts that really are authorship.

A decision model can only ever occupy step 6. If removing it would not change the accepted result, it does not ship.
[21-agent-doctrine.md](21-agent-doctrine.md) states the doctrine this order comes from.

### 3.2 Where one could help (ranked by expected value) [I]

1. **Clarification selection.** Code detects the missing or ambiguous slot ("which town?", "which group?", "which side?") and offers a few
   *authored* questions; the chooser picks which one to ask, or says none is needed. We do not rely on any model to ask on its own. This
   is a natural Choice question with a small menu.
2. **Workflow shortlist from free text.** When a typed prompt could map to many workflows ("set up an ambush on the road north of the
   village"), a chooser can shortlist two or three for the generative model or the user. This mirrors the vendor's skill-suggestion study,
   including its lesson that suggestions also break some requests that would have gone right.
3. **Advisory ordering of already-valid candidates.** At higher effort levels the harness samples K candidates (doc 25 §7.3). After every
   validator has passed them, Score questions ("how well does this patrol match 'cautious'?", "which dialogue variant fits 1985 Soviet radio
   style?") could order what the user sees first. Ordering is never acceptance.
4. **Cheap advisory flags.** Noul questions such as "does this line sound anachronistic?" as warnings next to lint results, calibrated
   against human labels, never blocking.

### 3.3 Where one must never decide [I]

- **Facts.** Class names, island geography, engine limits, stringtable keys and mission contents come from code and data, not from a model.
- **Arithmetic, geometry, counts, dates and ordering.** The vendor itself says to keep math in code [V].
- **Identifiers.** A chooser returns an index into a code-built menu; code maps it to the real ID.
- **Permissions, policy and legality.** Whether an action is allowed, whether a script command is safe (doc 24), whether a plugin may act.
  A probability is never permission.
- **Acceptance.** Validators, lints and compilers decide whether content is admitted; the user decides whether it is kept.
- **Authorship.** Dialogue, briefings, SQS/SQF and campaign text are generated and then validated; a chooser cannot write them.
- **Hostile input.** Text taken from missions, addons or plugin results may appear in a state only as quoted data, and the answer it
  produces carries no more authority than any other proposal.

## 4. Recommendation for v1

### 4.1 No decision model in front of the generative model [I]

1. **The cheaper deciders already cover most intents** (§3.1). A chooser would mostly re-select what the UI selected.
2. **Our high-value tasks are authorship**, which decision models cannot do.
3. **No evidence in our setting.** No independent evaluation exists for any of the four on editor-style routing or clarification.
4. **Deployment friction.** Jev is hosted only, which conflicts with offline-first use and would send mission content to a second service.
   Laya needs fine-tuning before it beats a majority-class guess. Kev at useful sizes wants a GPU. CLM needs an 8B encoder on a GPU.
5. **Harm is possible even when the average improves**, as the vendor's own study shows (37 fixed, 7 broken).

### 4.2 Build the Selector seam now

The seam decouples *who picks* from *what happens next*, so a decision model can be added later without touching workflows. Proposal-only
sketch (names are not final):

```rust
/// Turns a request plus a code-built menu into an untrusted proposal.
/// Every implementation is replaceable; none of them is trusted.
pub trait Selector {
    fn propose(&self, request: &SelectionRequest<'_>) -> Result<Selection, Error>;
}

/// What a selector may answer. Nothing else is representable.
pub enum Selection {
    /// One offered candidate, by the opaque index code assigned for this request.
    Candidate { id: CandidateId, telemetry: Option<SelectorTelemetry> },
    /// None of the offered candidates fits the request.
    NoMatch,
    /// Ask one of the authored clarification questions offered in the request.
    Clarify { question: ClarifyId },
}
```

- `SelectionRequest` carries the user's text (untrusted), a small code-built state digest, the menu (opaque IDs plus short descriptions
  written by us, not taken from mission text), the authored clarification questions, and the editor-state generation it was built from.
- **Admission is separate.** A pure function re-checks every proposal: the ID is in the offered menu, the state generation is still
  current, and the user or plugin has permission. Only an admitted selection reaches a workflow. A stale or unknown answer is refused.
- **Telemetry is not authority.** Probabilities are logged with the menu hash and the model artifact, never used to admit anything. At most
  they change presentation, for example showing the top two options when their margin is small (doc 25 §7.3).
- **Effort levels change budgets, not deciders.** A higher effort level may ask for more candidates or an advisory ordering, but it never
  silently adds or swaps a model. Enabling a decision model is a visible user setting.

Implementations, in the order we build them:

| Order | Implementation | How it picks | Status |
| --- | --- | --- | --- |
| 1 | `RuleSelector` | Exact command names, aliases, catalog synonyms, lexical match; code-detected missing slots map to `Clarify` | v1 |
| 2 | `GenerativeSelector` | The configured LLM picks from a shuffled menu with neutral labels through a constrained tool call or enum schema (doc 13 §4, doc 25 §2.3); must be able to answer `none` and `ask` | v1 |
| 3 | `DecisionModelSelector` | Local Laya/Kev via an in-process runtime, or hosted Jev as an opt-in provider | Only after §5 |

A decision-model selector can first run in **shadow mode** in benchmark and opt-in local runs: it answers alongside the active selector,
its answer is logged, and nothing it says is shown or applied. Hosted Jev in shadow mode still sends data out, so it stays opt-in.

## 5. The evidence bar (all must hold before an advisory slot) [I]

These are this project's own criteria.

1. **Frozen instruments, identical inputs.** Measure on our own instruments, frozen before the comparison, with byte-identical state,
   menu and question text for every arm:
   - *Routing*: requests mapped to `Candidate | NoMatch | Clarify` over the editor's operation menu, in four classes: supported, ambiguous,
     unsupported, and injected (hostile text inside mission data).
   - *Clarification*: under-specified requests where the right answer is one specific authored question, plus cases where the answer is
     already in the mission, so asking counts as a failure.
   - *Ranking* (only if the ranking use is proposed): K validated candidates with blind human preference labels.
   - Variants in every instrument: paraphrases, negations, reordered menus, near-duplicate operations, the correct option removed, hostile
     candidate descriptions, and cases that rules already solve, so a model cannot win credit for plain automation.
2. **Beats both baselines on the same cases.** It must beat `RuleSelector` *and* `GenerativeSelector`:
   - fewer valid-but-wrong selections and fewer unneeded clarifications;
   - no more missed clarifications, and correct `NoMatch` on unsupported requests;
   - no loss of coverage on supported requests;
   - no case-level regression on safety cases (injected or out-of-scope requests).
3. **Statistics declared in advance.** Repeated trials per case, paired case-level comparisons (for example an exact sign test) at a
   threshold written down before the run, and per-case reliability (pass^k, doc 25 §11.2), never a pooled score across instruments.
4. **Held-out confirmation.** Cases written by a different contributor, kept out of this public repository, and frozen before any tuning or
   calibration ends. Development cases alone are not enough.
5. **Calibration checked, not assumed.** Temperatures are fitted on development cases only; calibration error is reported on the held-out
   set; any threshold used for presentation is fixed before the held-out run.
6. **Cost fits.** Added p95 latency, peak RAM on our minimum-spec machine, download size and maintenance fit budgets set before the
   experiment. For a local selector the budget is CPU-only.
7. **Offline and license.** Apache-2.0 or compatible weights; runs with no network; offered as a separate, checksummed download, never
   bundled in the installer (doc 02). The run record pins hashes of the weights, tokenizer, head and calibration file, and the runtime
   version. A hosted Jev is allowed only as a user-configured provider, pinned to an exact version such as `jev-1.13.0`, never an alias.
8. **Adapter robustness first.** Offline tests for unknown or duplicate IDs, non-finite or missing probabilities, oversize state (refuse,
   do not truncate), timeouts and partial responses pass before any live call.
9. **Advisory, visible, removable.** A wrong pick stays cheap to undo and easy to see, and the user can turn the selector off.

Arms for the comparison:

| Arm | Setup | Question it answers |
| --- | --- | --- |
| R | `RuleSelector` only | What does plain automation already get right? |
| G | `RuleSelector`, then `GenerativeSelector` | The v1 product |
| D | `RuleSelector`, then `DecisionModelSelector` | Can a chooser replace the generative pick? |
| G+D | G with the decision model as advisory shortlist or ordering | Does advice help the generative model? |

A decision model is adopted only for the role (shortlist, clarification pick, ordering) and the arm where it cleared every item above.

## 6. Experiment order if we pursue the bar [I]

1. **Laya.** Smallest, Apache-2.0, CPU-plausible, community ONNX ports. Needs fine-tuning on a few hundred authored editor decisions (our
   own synthetic data only, doc 02) and per-question-type temperature calibration.
2. **Kev-0.8B.** Apache-2.0 on a Qwen3.5-0.8B base; community GGUF, ONNX and mistral.rs ports.
3. **Jev via API.** As a yardstick for what a trained vendor model achieves on our instruments, not as a default.
4. **CLM.** Only in a separate GPU lane, if ever.

Runtime feasibility in Rust is [U]: candidates are ONNX Runtime bindings (`ort`), candle's ModernBERT support, and mistral.rs for the Kev
port. A small spike should measure load time, p95 latency and peak RAM on the minimum-spec machine before any quality work.

## Open questions

1. **Minimum spec.** Is roughly 0.2–0.5 s per question on CPU (Laya's own figure) acceptable in an interactive editor, and on what
   minimum machine? [U]
2. **Rust runtime.** Which of `ort`, candle or mistral.rs runs Laya or Kev-0.8B in-process with pinned, reproducible outputs? [U]
3. **Fine-tuning data.** How many authored, typed editor decisions does Laya need, and can we produce them from synthetic fixtures alone
   without training on game text (doc 02)? [U]
4. **Languages.** Czech, Polish and Russian prompts: does Laya's multilingual variant hold up, given Jev's English-first guarantees? [U]
5. **Hosted privacy.** If a user enables hosted Jev, what exactly leaves the machine, and how is that shown before the first call? [I/U]
6. **Held-out custody.** Who writes the held-out routing and clarification cases, and where are they kept outside this public repo? [U]
7. **Ranking judge.** Is advisory ordering of creative candidates worth measuring at all, or should blind human choice stay the only
   ordering signal for creative text? [U]
8. **Upstream facts.** Is `Qwen/Qwen3.8-27B` (Kev-27B's base tag) a real upstream release? Only the Hugging Face tag was seen [U].

## Sources

All web sources fetched 2026-09-26.

**TypeSafe AI (Jev)**

- System One concept: https://docs.typesafe.ai/concepts/system-one
- Models, aliases, limits, pricing, data handling: https://docs.typesafe.ai/models
- Jev 1.13 limitations: https://docs.typesafe.ai/model-jaggedness/jev-1.13
- Skill-suggestion cookbook: https://docs.typesafe.ai/cookbooks/skill_suggestion
- Launch post: https://typesafe.ai/blog/introducing-system-one-models-and-jev

**Kev**

- Kev-4B card: https://huggingface.co/jaredpalmer/kev-4b
- Kev-0.8B card: https://huggingface.co/jaredpalmer/kev-0.8b
- Family listing with base-model tags: https://huggingface.co/api/models?search=jaredpalmer/kev&full=true
- Kev-0.8B ports: https://huggingface.co/api/models?search=kev-0.8b

**Laya**

- Card: https://huggingface.co/convaiinnovations/laya
- API metadata: https://huggingface.co/api/models/convaiinnovations/laya
- Ports: https://huggingface.co/api/models?search=laya

**CLM**

- Card: https://huggingface.co/Contrastive-LM/CLM-v0.1-8B
- Repository: https://github.com/Contrastive-LM/CLM

**This repository**

- Doc 02 (licensing, weights), doc 11 (pi-ai `classify()`), doc 12 §1.9 (`rig-typesafeai`), doc 13 §4 (constrained decoding and local
  option probabilities), doc 14 (model tiers), doc 24 (script command risk), doc 25 (menus, candidates, evaluation controls),
  [21-agent-doctrine.md](21-agent-doctrine.md) (agent doctrine), and `AGENTS.md` (product invariants: offline-first, untrusted content).

## Verification notes

- Every [V] item above was re-read on the live page on 2026-09-26.
- The Laya card gives two different uncalibrated ECE figures in different sections; this doc quotes only the calibrated 0.081 and the
  "ships over-confident" wording.
- The vendor cookbook's agent model and exact thresholds were not needed for this doc and are not repeated.
- Jev's architecture and parameter count are not published; Kev's affiliation with TypeSafe is not stated. Both stay [U].
- No number in this doc comes from our own measurements; we have none yet.
