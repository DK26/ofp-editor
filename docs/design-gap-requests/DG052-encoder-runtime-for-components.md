# DG052: A runtime for non-generative encoder components

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: owner** (D022-level: a second supply chain and an exception to an architecture rule; doc 58 OQ2), informed by spike
> S-ENC (doc 58 §6). Blocks: every encoder component (extractors, checkers, NLI, encoder rerankers) in the product; until decided,
> encoder arms are offline research only (doc 53 §4.9).

## Context

- **Doc 53 §4.9.** Generative tiny models, rerankers and embedders run in the pinned llama.cpp sidecar (D022); GLiNER2, HHEM,
  LettuceDetect and mDeBERTa NLI do not, and need ONNX Runtime (the `ort` crate) or candle. HHEM's reference path loads with
  `trust_remote_code`, "which the product would never do". The alternative named there: only llama.cpp-served rerankers and embedders.
- **Doc 58 §4.1, §4.4, §4.5, §4.11 item 2, OQ2, finding 6.** Three tiers: S (the sidecar), I (small pure-Rust encoders inside the
  editor under §4.4's admission rule: pinned, small and capped), H (a helper process with a telemetry-free ONNX Runtime build and
  `fxtranslate`, started by the Model Manager's supervisor, with a no-egress test). Tier I "would depart from the architecture's
  'embedded inference always out of process' resolution"; the doc "decides nothing". Finding 6: that resolution is written for
  generative engines, and this request should say whether it covers encoders.
- **D022** names only generative engines in its Alternatives and Consequences. **Architecture README** §7 row 13 and §8 item 7;
  **agent-runtime §3**: embedded engines run out of process. **Crate-map §2.3, §10**: the Model Manager may spawn a helper process.

## The gap

Components that doc 58 expects to cut cloud calls (span extraction, NLI checks, hallucination flags) cannot run on the only runtime
D022 provides, and adding one is a supply-chain and architecture decision nobody has taken.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Sidecar only (tier S): rerankers and embedders served by llama.cpp; no other runtime | One supply chain; the architecture rule holds | GLiNER2, NLI and hallucination checkers cannot run |
| B | A plus tier H: a helper process with a telemetry-free ONNX Runtime build | Inference stays out of the editor process | A second supply chain; a reproducible ORT build and its CI cost (doc 58 §4.5) |
| C | A plus tier I: pure-Rust encoders in the editor process under §4.4's rule | Lowest latency; no extra process | An exception to "embedded inference always out of process" |
| D | A, B and C | Everything doc 58 proposes | Every cost above |

## Recommended resolution (proposal)

None in the sources: doc 58 proposes a shape and leaves the choice to the owner after S-ENC (OQ2). Until then, doc 53 §4.9's interim
rule holds (encoder arms are offline research only). Whichever option is chosen, the decision states whether the out-of-process rule
covers encoders (doc 58 finding 6), and D022 gets an amendment.

## What it would change

- D022 (an amendment); architecture README §7–§8 and agent-runtime §3 (the rule's scope); crate-map §2.3 and §10 (a
  `plotroom-components` crate or a helper, per doc 58 §4.1's provisional name); doc 53 §4.9; doc 58 §4.1 and §4.4–§4.5.
- Tests first (doc 58 §4.5, proposal): the helper runs with networking denied; weights are refused unless pinned by revision and
  SHA-256.

## Affected docs

D022; D023 decision 1; D037; architecture README (§7, §8); `docs/architecture/agent-runtime.md` §3; `docs/architecture/crate-map.md`
(§2.3, §10); doc 53 §4.9; doc 58 (§4.1, §4.4, §4.5, §4.11, §6, OQ2, findings).

## Decision record

Open. Owner-level: needs an owner question (doc 58 OQ2 asks it).

## Verification notes

### Filing (2026-09-28)

- Filed from doc 53 §4.9 and doc 58 §4.11 item 2 (one candidate in two docs), re-read on 2026-09-28 with doc 58 OQ2 and findings.
  The architecture README's rows were not re-read for this filing; their numbers are cited as doc 58 gives them.
