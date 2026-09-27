# DG034: Camera and effects engine defects: route to the engine-requests register

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (`AGENTS.md` already sets the rule; this request records how doc 32 follows it). Proposing an item to
> the community engine project is public outreach and follows whatever rule the owner sets for it (compare DG029). Blocks: nothing
> in the compiler, which routes around every defect already (doc 32 §3.7 lints).

## Context

- **Doc 32 §2.9**: seven engine defects "the compiler routes around". "Each becomes a lint (§3.7) and a candidate upstream CE issue,
  filed through `docs/design-gap-requests/` [I]." Phase 0 (doc 32 §7) lists "design-gap entries (… upstream candidates in §2.9)".
- **`AGENTS.md`**, "Maximum Within the Engine; Gaps Become Engine Requests": every engine limitation goes into the engine-requests
  register under `docs/upstream/` with the limitation, what Plotroom does today, the proposed engine feature with its hook points in
  the engine source, the benefit and a status (not filed, proposed to the community engine project, accepted, shipped). "Engine
  requests (gaps in the game) are distinct from design-gap requests (gaps in this project's own design)."
- **Doc 31 §10** keeps its own "Upstream report candidates (CWR-CE)" list, which overlaps doc 32 §2.9.
- `docs/upstream/` does not exist yet.

## The gap

Doc 32 routes engine defects to the wrong register, and the defects themselves are not yet recorded anywhere in the form `AGENTS.md`
requires.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Keep the defects as design-gap requests | Matches doc 32's text | Contradicts `AGENTS.md`; mixes engine and design gaps |
| B | Move them to the engine-requests register; doc 32 §2.9 points there; this DG records the routing only | Follows `AGENTS.md`; one place for engine requests | Needs `docs/upstream/` created |

## Recommended resolution (proposal)

Option B. When `docs/upstream/` is created, add these seven entries (status "not filed"); the evidence is doc 32's, with CWR line
ranges as cited there:

| # | Limitation | What Plotroom does today | Proposed engine change (hook) | Benefit |
| --- | --- | --- | --- | --- |
| 1 | `camSetBank` and `camSetDir` are bound to the dive handler; dive, bank and heading are stored but read nowhere | Lint error on `camSetDir`/`Bank`/`Dive` anywhere; timeline offers no roll or heading on targeted shots (doc 32 §2.2–§2.3) | Bind each command to its own setter and apply the fields in the camera commit (`Game/Commands/GameStateExt.cpp#L1341-L1356`; `World/Scene/Camera/CameraHold.hpp#L58-L81`) | Heading and roll for cinematics |
| 2 | `camSetFovRange` has an empty handler, so the distance-based auto-zoom is unreachable | Lint error; FOV set per segment with `camSetFov` | Implement the handler (same camera block) | Auto-zoom shots |
| 3 | An `RscTitles` `fadeOut` overwrites `fadeIn`; the fade-out is always 1 s | Documented in doc 32 §2.4; §2.9 promises a lint, but §3.7 lists none yet | Keep separate fade-in and fade-out values (`Game/TitEffects.cpp#L476-L625`) | Authored title fades |
| 4 | An unknown `cameraEffect` name is dereferenced after a suppressed warning (probable crash [I]) | Lint error on unknown names; names come from pickers only | Fail safely on a missing name (`UI/OptionsUI.cpp#L492-L496`, `#L588-L625`) | No crash from a typo |
| 5 | Effect setters (`setCameraEffect`, `setTitleEffect`, …) store unknown enum strings as −1; firing such a trigger probably crashes [I] | Lint error "enum setter with a non-enum string"; pickers only (doc 31 §3, doc 32 §2.8) | Reject or ignore unknown strings (`Game/Commands/GameStateExtWorldWaypoint.cpp#L569-L644`) | No crash from scripted effects |
| 6 | The capture tool writes `camSetTarget '<debugName>'`, which no overload accepts (single quotes are not string delimiters) | Lint error on `camSetTarget '<name>'`; capture import flags quoted debug-name targets and resolves them to the object nearest the captured point (doc 32 §3.8) | Emit a valid target form in the `clipboard.txt` export (`CameraHold.cpp#L463-L536`) | Captured shots paste and run |
| 7 | The manual camera's lock loop examines only the first collision result | Documented only (doc 32 §2.9); the capture workflow (§4.4) does not yet say how it copes | Iterate all collision results (`CameraHold.cpp#L426-L439`) | Reliable target lock during capture |

Each lint stays in doc 32 §3.7 (and in the code registry, DG005). Doc 32 §2.9 keeps a one-line summary and points to the register.

## What it would change

- Doc 32 §2.9 last sentence and §7 phase 0: "recorded in the engine-requests register (`docs/upstream/`)".
- `docs/upstream/`: the register file with the seven entries above.
- Doc 31 §10, "Upstream report candidates (CWR-CE)", overlaps items 1–5 and adds six more: harness `eval` errors that abort
  AutoTest, script name and line in error messages, the `camSetFov` "set" flag that is never cleared, `RptF` compiled to a no-op,
  the root-only existence gate on respawn hooks, and `respawn = SIDE` logging through `Fail()`. They go into the same register, as
  does DG001 option A (the `--preview-mission` request).

## Affected docs

Docs 31, 32; `docs/upstream/` (new); DG001, DG005, DG009.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 32 §2.2–§2.4, §2.8, §2.9, §3.7, §3.8, §4.4 and §7, doc 31 §3 and §10, and `AGENTS.md` "Maximum Within the Engine", re-read on
  2026-09-27. Engine line ranges are doc 32's (CWR `ffc61838b7`, engine-reviewed there) and were not re-read against the source in
  this pass. The "what Plotroom does today" column quotes doc 32 §2.4, §2.9, §3.7 and §3.8; items 3 and 7 have no mitigation in doc 32
  yet, which the register entries should record.
