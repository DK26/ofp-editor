# D003: Upstream alignment and per-mission target profiles

> **Status:** accepted · **Decided by:** owner · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** which source is the reference for behaviour, where patches go, and which game version a mission targets.
> **Related:** D012, D013, D017, D018. **Open parts:** 1.99 behaviour probes (doc 19 OQ1, doc 29 §9); outreach OWQ-10, OWQ-11
> (answered 2026-09-27 → D035; nothing sent yet).

## Context

- Doc 01: `BohemiaInteractive/CWR` is locked (no PRs; one squashed commit per Steam patch). `ofpisnotdead-com/CWR-CE` is where
  development happens (CI, reviewed PRs, a `port` label that feeds official patches). Both share the editor and mission code. The owner
  expects CWR-CE to be the community-led line.
- Players run official Remastered builds (3.05) and still the legacy 1.99; CE may gain features Steam builds lack (doc 01 §10 risk 2).
- The released source is the Remastered engine; 1.99 lacks many of its commands (doc 23 §4; doc 35 §8.2).

## Decision

1. **Align with CWR-CE.** Port and cite from CE `main` pinned to a SHA (currently `b67bf3bd62`). **BI/CWR release snapshots**
   (currently `ffc61838b7` = 3.05) are the official-behaviour baseline that every ported behaviour is cross-checked against.
2. **Patches and engine requests go to CWR-CE only** (doc 01 §9 (c); D012).
3. **The target is chosen per mission and per campaign**, never globally:

   | Profile | Meaning |
   | --- | --- |
   | `Cwa199` | Legacy *Arma: Cold War Assault* 1.99 |
   | `Cwr` | Official Remastered 3.05 (Steam, GOG), and CE builds used without extensions. **Default** |
   | `Ce` | CWR-CE with opt-in engine extensions (doc 29 writes it `CwrCe{…}` to carry the extension set) |

4. The linter computes a **"Requires: <minimum version>" badge** for every mission, module and campaign from the command catalog's
   per-overload availability, the features used and the mod set (doc 23 §13; doc 27 TL;DR).
5. **Editor-generated glue** (compiler output, module lowerings, campaign finishers) stays in the **conservative subset** of the
   mission's profile: only constructs that profile is shown to run (verified by reading, or confirmed by a probe), preferring those that
   also run on older profiles. A profile-specific construct appears only when the profile allows it, and the badge shows it.

## Alternatives considered

- Align with BI/CWR only: no contribution path; fixes land in CE first anyway.
- One global target (all 1.99, or all 3.05): either loses Remastered features or excludes the 1.99 player base.
- Default to `Ce`: most players run official builds, and CE build artifacts expire (doc 01 §9 (b)).

## Consequences

- The command catalog is generated from the pinned CWR snapshots and CE, joined with wiki `since` data and optionally an owner-local 1.99
  name scan, and emits availability per profile (doc 23 §13; doc 35 §8.2); entries carry a registration gate and capability tags
  (doc 24 TL;DR).
- Knowledge cards, primer facts and lints are tagged per profile (doc 30 TL;DR).
- 1.99 behaviours stay unverified until probes pass. Features degrade on `Cwa199` rather than disappear (doc 29's radio-menu camp,
  doc 31's pre-placed pools), and badges say "Cwr/Ce verified by reading, Cwa199 pending" where that applies (doc 43 §8.3).
- File writers default to output every profile accepts; profile-only file features (UTF-8 stringtables, `init.sqf`) sit behind the
  profile (doc 04 TL;DR; doc 07 §0).
- Upstream pins live in one tracked place, and a read-only job watches the editor-relevant upstream paths (doc 01 §11; proposal).

## Sources

Doc 01 (TL;DR, §9–§11); doc 04 TL;DR; doc 07 §0; doc 19 OQ1; doc 23 (TL;DR, §4, §13); doc 24 TL;DR; doc 27 TL;DR; doc 29 (glossary,
§7, §9); doc 30 TL;DR; doc 31 TL;DR; doc 35 §8.2; doc 43 §8.3.

## Amendment notes

### 2026-09-27: refined by D035 (pointer)

The owner answered OWQ-10 and OWQ-11: one letter to Bohemia after the name clearance and before the first public release, and
CWR-CE outreach that starts with CE #35 and a small tested PR, security items only after the private reports (D035 items 1–3).
The header gained the pointer; nothing above changed.
