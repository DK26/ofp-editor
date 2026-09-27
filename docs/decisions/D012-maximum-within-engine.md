# D012: Maximum within the engine; gaps become engine requests

> **Status:** accepted (invariant) · **Decided by:** owner (`AGENTS.md`) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** every feature that depends on game behaviour. **Related:** D003, D005, D015, D018.
> **Open parts:** the register `docs/upstream/` does not exist yet (created 2026-09-27); DG034 (camera and effects defects to move
> there); OWQ-09 and OWQ-11 (outreach; answered 2026-09-27 → D035, nothing sent yet).

## Context

The owner: "Our editor will do the maximum possible with what can be done with the game engine. And all gaps found might become a future
feature request for the game." `AGENTS.md`, "Maximum Within the Engine; Gaps Become Engine Requests", is authoritative. The research has
already found many candidate requests: a non-`AutoTest` preview launch (doc 08 P3, CE #35), campaign polish E1–E6 (doc 18 §9), strategic
extensions E7–E14 (doc 29 §7), nine hardening patches (doc 24 §6), camera defects (docs 31, 32; DG034), and an unseedable `random`
(doc 43 TL;DR).

## Decision (summary; `AGENTS.md` governs)

1. Plotroom does the maximum the shipped engine allows for each target profile: vanilla content, generated scripts, pre-placed variants
   and engine-faithful workarounds. **No core feature may require an engine change.**
2. Every engine limitation found is recorded in the **engine-requests register** under `docs/upstream/`: the limitation, what Plotroom
   does today, the proposed engine feature with its hook points in the engine source, the benefit, and a status (not filed, proposed to
   the community engine project, accepted, shipped).
3. When CWR-CE ships a requested feature, Plotroom exposes it as an **opt-in capability of the `Ce` profile**, never as a silent
   requirement for content that must also run on older versions.
4. Engine requests (gaps in the game) are distinct from design-gap requests (gaps in Plotroom's design).

## Alternatives considered

- Require a CE build for advanced features: excludes the players on official builds and 1.99 (doc 01 §10 risk 2).
- Work around gaps silently: loses the research's value as a roadmap for the community engine.

## Consequences

- Each feature design names its per-profile lowering and its fallback (for example doc 29's radio-menu camp on 1.99, and doc 31's
  pre-placed pools where `Cwa199` lacks dynamic creation).
- Creating `docs/upstream/` (index, entry template, first entries collected from the docs above) is a design-round task.
- Security hardening requests (doc 24 §6) go through private disclosure first (OWQ-09), not straight into the public register.
- Submitting requests to CWR-CE is public outreach and needs the owner (OWQ-11).

## Sources

`AGENTS.md`; doc 01 §10; doc 08 (TL;DR, §6); doc 18 §9; doc 24 §6; doc 29 §7; doc 31 TL;DR; doc 32 §2.9; doc 43 TL;DR; DG034;
`docs/design-gap-requests/README.md`.

## Amendment notes

### 2026-09-27: refined by D035 (pointers)

Security findings go privately to CWR-CE and Bohemia first, and hardening entries enter the register only after the reports are
acknowledged (OWQ-09 (a); D035 item 1). CWR-CE filing starts with CE #35 and a small tested PR, then one tracking discussion that
links the register (OWQ-11 (a); D035 item 3). The register now exists in `docs/upstream/`. The header gained pointers; nothing
above changed.
