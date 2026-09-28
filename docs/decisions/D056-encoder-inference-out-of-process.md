# D056: Encoder components: inference stays out of process

> **Status:** accepted · **Decided by:** owner delegation (2026-09-28, lightly edited: "Go ahead without the GPG passphrase. I will not
> be near the PC for hours. We are working remote"; "Tiny models with no cloud availability should be tested directly on PC. Either
> way, except for GPG signing, we can do everything else"; for a choice between design options, "Figure out the best option for this
> use case"); decided under the owner's delegation; the owner may overrule it on return · **Decided:** 2026-09-28 · **Recorded:**
> 2026-09-28
> **Scope:** where non-generative neural components (encoders: extractors, checkers, NLI, encoder rerankers and embedders) run, and
> which runtimes may serve them (DG052; doc 58 OQ2 and finding 6; doc 53 OQ3). **Refines:** D022 (amendment note: its
> out-of-process rule covers encoders). **Related:** D008, D023, D037, D049, D057; DG052; doc 53 §4.9; doc 58 §4; architecture README
> §7–§8; agent-runtime §3; crate-map §2.3, §10.
> **Open parts:** spike S-ENC (doc 58 §6.0), which gains an ONNX Runtime helper arm on the tier H models for item 3's bar (its tract
> and rten arms no longer inform a decision), and, if it meets that bar, tier H's admission (item 3); the reproducible ONNX Runtime
> build and its CI cost (doc 58 §4.5); doc 58 §4.2's classifier heads through the sidecar and OQ10 (rank pooling for NLI); doc 58
> OQ5 (specialists' delivery) and OQ6 (whether data tables may ship).

## Context

- Doc 53 §4.9: generative tiny models, rerankers and embedders run in the pinned llama.cpp sidecar (D022); GLiNER2, HHEM,
  LettuceDetect and mDeBERTa NLI do not, and need ONNX Runtime or candle. HHEM's reference path loads with `trust_remote_code`,
  "which the product would never do". Until decided, encoder arms are offline research only.
- Doc 58 §4.1 proposes three tiers: S (the sidecar), I (pure-Rust encoders inside the editor process under §4.4's admission rule) and
  H (a helper process with a telemetry-free ONNX Runtime build, supervised by the Model Manager). Finding 6: the architecture's
  "embedded inference always out of process" resolution (architecture README §7 row 13, §8 item 7; agent-runtime §3) is written for
  generative engines. §4.5: official ONNX Runtime builds collect telemetry (and upload it on Linux and macOS), and recent releases
  fixed out-of-bounds and overflow bugs in its kernels: "That is why downloaded models are parsed and run here, not in the editor."
- D022 item 2 makes inference out of process by default; its Alternatives name only generative engines (doc 58 finding 3).
- DG052's sources give no recommendation: doc 58 "decides nothing" and leaves the choice to the owner after S-ENC (OQ2). This record
  chose the conservative option under the delegation "Figure out the best option for this use case".

## Decision

1. **The out-of-process rule covers encoders** (doc 58 finding 6): no encoder component runs its model inside the editor process.
   Tier I (option C, encoders in the editor process) is not adopted. Deterministic crates that load no downloaded model file and run
   no neural network (lingua, spellbook, Harper, BM25; doc 58 §4.1) are ordinary editor code and are not affected (this concerns only
   where they run; whether their data tables may ship is doc 58 OQ6, not decided here). D022 item 1(3)'s in-process generative
   backend is not decided here.
2. **Now: option A (sidecar only).** Rerankers and embedders are served by the pinned llama.cpp sidecar (D022); no other runtime.
3. **Tier H (option B) is the only path admitted for other encoders, and only if spike S-ENC** (doc 58 §6.0), run with an ONNX
   Runtime helper arm on the tier H models, meets doc 58's evidence bar, which this record reads from §6.0's measurement list as
   pass criteria (parity with reference logits within 1e-4, a 20-run bitwise repeat, typed errors on truncated or corrupt files, a
   no-egress check with networking denied; size, load time, latency and memory recorded on the reference machines): a helper process
   with a telemetry-free, reproducible ONNX Runtime build, started by the Model Manager's supervisor, with networking denied and
   tested, and weights pinned by revision and SHA-256 (doc 58 §4.5). The S-ENC result is recorded as an amendment note on this
   record; the owner may overrule it.
4. **Until then, doc 53 §4.9's interim rule holds:** encoder arms are offline research only.
5. **No `trust_remote_code` path**, in any tier.
6. **Tests first** (DG052; doc 58 §4.5), for tier H if admitted: the helper runs with networking denied; weights are refused unless
   pinned by revision and SHA-256.

## Alternatives considered

| Option (DG052) | Why not chosen |
| --- | --- |
| B now, before S-ENC | A second native supply chain (a reproducible ONNX Runtime build and its CI cost) before evidence that it works on the reference machines |
| C: tier I, encoders in the editor process | An exception to "embedded inference always out of process": native and SIMD kernels over downloaded model bytes in the process that holds unsaved work, and two rules for contributors instead of one |
| D: A, B and C | Every cost above |

## Consequences

- One rule for contributors (no encoder inference in the editor process; D022 item 1(3) for generative engines is unchanged), crash
  isolation (D022's reason: a native crash would lose unsaved work), supply-chain isolation for downloaded model files, and no
  `trust_remote_code` path.
- Cost: GLiNER2, HHEM, LettuceDetect and the NLI checkers cannot run in the product until tier H is admitted, and doc 58's E3 encoder
  arms stay offline; what the sidecar serves today (embedders and rerankers) is available.
- Friction (D049): contributors keep one rule; users wait for extraction and checker components until S-ENC passes.
- Folding steps, not done here: architecture README §7 row 13 and §8 item 7 and agent-runtime §3 (the rule covers encoders);
  crate-map §2.3 and §10 (the helper, only if admitted); doc 53 §4.9 and OQ3; doc 58 §4.1 and §4.4–§4.5 (tier I not adopted) and
  §6.0 (S-ENC gains an ONNX Runtime helper arm; its tract and rten arms no longer inform a decision). D022 carries a dated note.

## Sources

DG052; D022 (with its amendment notes); doc 53 (§4.9, OQ3); doc 58 (§4.1–§4.5, §4.11 item 2, §6.0, OQ2, findings 3 and 6);
architecture README (§7 row 13, §8 item 7); `docs/architecture/agent-runtime.md` §3; the owner's delegation of 2026-09-28.
