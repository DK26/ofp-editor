# DG005: One registry for lint, pattern and other codes

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: final lint codes in the linter, validators and findings panel; any code cited by
> a Standing Orders entry, lint link or test name.

## Context

Research docs mint provisional codes and several defer to "the design round" for final numbers (headers of docs 34, 36, 37, 42;
doc 35 proposes none). Doc 36's header keeps a "codes already in use" list; doc 34 §5.1 keeps the D series in one table.

## The gap

Families collide across docs, and growing lint families have no single owner.

| Label | Meaning A | Meaning B (and C) | Source of the note |
| --- | --- | --- | --- |
| `D9`, `D10`–`D12` | Lints: doc 27 D1–D8, doc 34 D9 (redistribution guard), doc 42 D10–D12 (stub owner, master-server redirect, launcher state) | Doc 21's legacy section labels D1–D14 (doc 21 header) | Doc 34 header and §5.1; doc 42 header |
| `P10` (and `P1`–`P8`) | Campaign patterns: doc 26 P1–P8, doc 29 P9, doc 34 P10 "Exodus" | Doc 09 pain points (P10 = packed and encrypted missions) | Doc 34 header; doc 36 §5 (its "ending routes" pattern waits for a number because P10 already collides) |
| `C6` vs `C06` | Doc 33 curriculum lesson C6 "Coming from later editors" (lessons C1–C7) | Doc 19 lint C06 (undeclared reference, type error, scope violation) | Doc 34 verification notes |
| `G1`–`G9` | Doc 40 §4.3 gap candidates G1–G9 | Doc 21 §12.4 product guarantees G1–G7; doc 37 principles G1–G8 | Found while filing this request |
| `E7`–`E12` | Doc 25 §11.1 instruments E1–E11 and doc 40's new instrument E12 | Doc 29 CWR-CE extensions E7–E14 | Found while filing this request |
| `L1`–`L4` | Doc 24 risk rules L1–L12 | Doc 31 phases L0–L4; doc 30 knowledge layers L1–L3 | Found while filing this request |
| `AT1`… | Acceptance tests numbered AT1… in several docs (31, 32, 33) | — | Docs 37 (PAT), 38 (AT-W), 42 (MAT) already prefix theirs |

Lint families keep growing across docs: doc 19 C01–C21; CF01–CF27 (docs 26, 28, 34, 36); SL01–SL31 (docs 29, 34, 36); MC01–MC31
(docs 28, 34, 36); TX01–TX07 (docs 28, 36); D1–D12 (docs 27, 34, 42); PL01–PL14 (doc 37); the L series (docs 23–24). Docs 39 and 41,
still being written, add DR, AU and AL families. Doc 30 §4.4 and doc 33 §3.4 also use dotted diagnostic ids
(`cmd.not-registered`, `logic.output-sync-on-gate`), a second naming style for the same kind of thing.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Keep short codes; renumber collisions by hand in the docs | Little work now | Collisions recur with every new doc; nothing checks them |
| B | One registry file assigns every final code; short codes get unique family prefixes; a CI lint rejects unknown or duplicate codes | One source of truth; testable | A registry to maintain |
| C | B, plus a stable dotted slug as each lint's canonical id (`campaign.guard.undeclared-ref`), with the short code as a display alias | Slugs are readable by users and models, cannot collide across namespaces, and match doc 23 §13.4's diagnostic `code` and doc 30's style | Two identifiers per lint |

## Recommended resolution (proposal)

Option C:

- A registry (proposed `docs/registry/codes.csv`; columns: canonical id, short code, family, kind, severity, meaning, owner doc,
  status `provisional`/`final`, superseded-by) is the only place that assigns final codes. Docs cite the short code or slug; the
  registry resolves both.
- Lint ids are dotted slugs; short codes stay as display aliases in families that are unique across the repo. Non-lint families
  (patterns, guarantees, instruments, principles, engine extensions, phases, acceptance tests) get prefixes that cannot be read as
  lints, for example `PAT-` for campaign patterns, `GTE-` for product guarantees, `INST-` for instruments; the registry decides the
  exact prefixes.
- Doc 21's legacy D1–D14 section labels are retired in favour of section numbers (doc 21 already maps them).
- A docs lint (CI) flags a code that is absent from the registry or used with two meanings; the linter's diagnostic table is
  generated from the registry.
- Provisional codes in research docs stay as written until their doc is folded; the registry records the mapping.

## What it would change

- New registry file and a docs lint; docs 19, 21, 25, 26, 27, 28, 29, 30, 31, 33, 34, 36, 37, 40 and 42 gain pointers when folded.
- Doc 36's header list and doc 34 §5.1 point to the registry instead of carrying their own lists.
- Doc 36 §5's "ending routes" pattern and doc 34's P10 get final pattern ids.

## Affected docs

Docs 09, 14, 19, 21, 22, 24, 25, 26, 27, 28, 29, 30, 31, 33, 34, 35, 36, 37, 39, 40, 41, 42, 43.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from the code headers of docs 34, 36, 37 and 42, doc 34 §5.1 and its verification notes, doc 36 §5, doc 21's header and
  §12.4, doc 40 §4.3, doc 29's CE-extension list, doc 25 §11.1, doc 24's L table, doc 31 §10 and doc 30 §4.1, re-read on 2026-09-27.
  The G, E and L collisions were found by grep in this pass and are not recorded in any research doc yet.
- *Docs 39, 41 and 43 step (2026-09-27).* The three docs are final. Their families: doc 39 CA01–CA12, DR01–DR22, TP01–TP10, CP1–CP13,
  DP0–DP4, DAT1–DAT13; doc 41 AH1–AH12, AM01–AM12, SX01–SX08, QP1–QP6, AU01–AU24, AL01–AL17, AP1–AP18, AD0–AD4, AMT1–AMT14; doc 43
  RP1–RP9, VX01–VX12, VY01–VY24, P-R1–P-R12, RV0–RV4, RAT1–RAT18. A grep of the rest of the repository finds them only where other
  files cite these docs, so no collision. Found while checking:
  - **`T0`–`T4`** mean three things: doc 14's model tiers (T0 no model … T3 cloud, used by docs 25 and 43 and by DG025), doc 22's
    plugin tiers (T0 data packs, T1 WASM, T2 remote) and doc 35 §8.3's command-evidence tiers (T1 proven … T4 absent). Doc 43 uses
    T0 in both of the first two senses; its header now says which is which.
  - **Shared findings**: doc 39's DR11–DR13, DR16 and DR18 restate doc 32 lints or doc 28 MC19; doc 43's VY19 (first clause) is
    doc 41's AL03 and VY08's weather clause is part of AL16. Each pair shares one finding until the registry gives it one id.
  - **Probe ids** (CP, AP, P-R here; PR in doc 29; PP in doc 37) are our own probes, not upstream tests, so they have no row in
    `docs/porting/upstream-test-map.csv` (doc 32 §7); the registry is the natural place to list them. Doc 43 §8.1 was corrected to
    say so; doc 33 §8 still routes its probes to that CSV.
  - "Affected docs" now lists docs 39, 41 and 43 without the "once final" qualifier, and docs 14, 22 and 35 for the T labels.
