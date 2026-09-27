# Design gap: a non-aborting Preview launch for the debug console

> Design-gap request for Plotroom (see `AGENTS.md`, "Design Authority"). ID: not yet numbered; the folder index
> assigns the `DGxxx` number. Filed 2026-09-27 in the consolidation pass.
> Status: **open**, `blocked on <decision>` (which non-aborting launch to use) and on a runtime probe.

## The gap

The P1 Preview launch (doc 08 §4.2) runs the game with `--test-mission <stage> --window --no-splash --no-strict
--harness 0`. `--test-mission` sets the engine's global `AutoTest` flag, and under `AutoTest` **any runtime script
error aborts the game with exit code 2**. That includes errors in text sent over the harness with `eval` / `exec`:
a debug-console line, a watch expression, a teleport or live-tweak snippet, an agent `eval`, or a generated "Try it"
call. One mistake ends the whole preview.

Doc 08 §4.4 listed the debug console and watch as working [V] without this caveat; the caveat is now added there.

## Evidence [V static]

- `--test-mission` sets `AutoTest = true`:
  `BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Game/GameApplication.cpp#L1703-L1718` (same line in CE).
- Harness `eval` runs `EvaluateMultiple`, whose `ShowError` calls `DisplayErrorMessage`, which requests close with exit
  code 2 under `AutoTest`: `engine/Evaluator/express.cpp#L2768`, `#L2988-L3011`;
  `engine/Poseidon/Game/Scripting/ExpressExt.cpp#L146-L165`.
- Under `--strict`, every script error and every other ERROR-level log ends the process
  (`ExpressExt.cpp#L166-L171`). The member default is `false`, but the flag help says it is on in
  Debug/RelWithDebInfo builds, so the shipping default is unconfirmed (doc 31 §7.4).

Sources: doc 31 §7.4 "Design gap", open question 7, and verification-notes item 8; doc 08 §2.4 (AutoTest side
effects). Static source reading only; nothing was run against a game.

## Constraint

A tolerant debug session needs a launch that is **both** non-`AutoTest` **and** `--no-strict`. `--no-strict` alone
does not help, because `--test-mission` itself sets `AutoTest`. The positional-plus-`--autotest` variant (doc 08
§2.4 C) also sets `AutoTest` and aborts the same way.

## Options

| # | Option | Engine change | Works on | Status |
|---|---|---|---|---|
| A | Upstream `--preview-mission` to CWR-CE (doc 08 §4.3, P3): runs in place without `AutoTest`; launch with `--no-strict` | Small CE pull request | CE builds; official builds only if adopted [U] | Planned P3 |
| B | Harness launch without `--test-mission`: positional `…/<name>.<Island>/mission.sqm` plus `--harness 0 --no-strict` (doc 08 §2.4 B) | None | Remastered and CE, if it plays | **[U]**: static reading says the positional `.sqm` opens the in-game editor; a CE organization member says it plays the mission (doc 08 open questions 2 and 10) |
| C | Keep `--test-mission` and accept the abort: pre-check every generated snippet, present the session as "strict preview", and report the error with its location | None | Remastered and CE | Interim only; a user-typed console line cannot be fully pre-checked |

## Impact

- Doc 08 §4.4 and P2: the SQF console, watches, teleport and live tweaks, and the agent's `eval_sqf_in_preview` tool.
- Doc 31 §5.4: "Try it" (force a rule, module or cutscene shot) and "why didn't this fire?" clause evaluation.
- Doc 31 §7.4: console, watch, logpoints and pause points.
- Doc 32 §4.2: live shot preview (per-key `eval` snippets under `--test-mission`).

## Proposed resolution path

1. P0 spike (doc 08 §6): probe option B on the shipping Steam binary and on a CE build. Record whether the positional
   launch plays the mission and whether it survives an `eval` error.
2. If B works, use it for debug sessions and keep `--test-mission` for "Validate" and strict previews.
3. Either way, raise option A with the CE maintainers in issue #35 and include the `eval` abort in the upstream report
   candidates (doc 31, "Upstream report candidates").
4. Until then, features that need a tolerant console are marked `blocked on non-aborting launch`, and the shipped
   console uses option C.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 31 §7.4 (design gap), doc 31 open question 7 and doc 31 verification-notes item 8, whose
  evidence was checked to exist in doc 31 before filing. The engine lines are quoted from doc 31 and were not
  re-read against the source in this pass.
