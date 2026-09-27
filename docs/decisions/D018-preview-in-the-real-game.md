# D018: Preview launches the user's real game

> **Status:** baseline · **Decided by:** research (docs 01, 08, 24) · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** the Preview button, live link, probes and smoke runs. **Related:** D003, D006, D012, D024, D030.
> **Open parts:** DG001 (a launch that survives script errors); doc 01 OQ1 (behaviour of the flags on the shipping Steam build); doc 42
> OQ10 (`--private` in single-player Preview); OWQ-11 (the upstream patch; answered 2026-09-27 →
> D035 item 3; not yet filed).

## Context

- The Remastered client already starts a mission from outside the game: `--test-mission <folder>` stages and plays it with the same
  steps as the in-game Preview button, and `--harness <port>` opens a loopback JSON control channel (doc 08 TL;DR). Neither option has
  been run against the shipping Steam binary yet [U].
- `--test-mission` sets AutoTest: a script error aborts the game and mission end quits it. The harness has no authentication and is
  "local code execution for whoever reaches the port" (doc 24 TL;DR). The demo executable has no editor module (doc 01 TL;DR).

## Decision

1. Preview launches the user's installed **official full game** (Steam or GOG, Remastered 3.05 or later) by default, or an executable the
   user configures (a CE build or a self-built one, needed on macOS and Linux arm64). **Never the demo executable.**
2. **P1**: stage a snapshot of the mission folder and launch
   `PoseidonGame --test-mission <staged-folder> --window --no-splash --no-strict --harness 0` (the folder, not the `mission.sqm` path).
3. **P2**: a live link over the harness (stop, teleport, debug console, screenshots) that sends only a fixed **allowlist of harness
   verbs**; `eval`/`exec` only from typed templates or user-typed console text that passed lint; all harness output is untrusted data
   (doc 24 policy (c)).
4. **P3**: upstream a small `--preview-mission` / `--edit-mission` patch to CWR-CE (an engine request, CE #35; D012).
5. **P4**: multiplayer Preview through a local server started with `--private`, plus a client.
6. **Always**: an export-and-open-the-game fallback for 1.99 and unknown builds.
7. Features built by editing the staged copy need no engine change: preview from the camera position, Intro and Outro preview.

## Alternatives considered

- Simulating missions inside the editor: cannot match the engine; the engine is the only truth for behaviour.
- Opening a mission straight into the in-game editor with a positional path: the evidence conflicts and it is unverified (doc 08 TL;DR).
- Requiring a CE build: most players run official builds (D003).

## Consequences

- The first Preview spike confirms the flags and paths on the shipping Steam and GOG builds (doc 01 OQ1–OQ2).
- Preview uses the mission's resolved mod set, and also offers clean-room (required mods only) and vanilla previews (doc 27 TL;DR; D030).
  A mod can redirect the master server, so `--private` on every launch is proposed after a side-effect probe (doc 42 §6.3).
- Launching the game is an irreversible effect: always a user's click, never in Auto (D024). The product's Preview flow uses a non-shell
  process API; the agent may request a Preview but never launch an arbitrary process (D006).
- A debug console that survives its own errors needs DG001's launch mode.
- The in-game probe suite (D013) and the campaign smoke runs reuse this launcher; whole-campaign automation is still unknown (doc 29 OQ2).

## Sources

Doc 01 (TL;DR, §9, open questions); doc 08 (TL;DR, §2, §4.4, §6); doc 24 (TL;DR, policy); doc 27 TL;DR; doc 29 OQ2; doc 42 §6.3, OQ10;
DG001.

## Amendment notes

### 2026-09-27: refined by D035 (pointer)

The owner, or a maintainer the owner names, starts CWR-CE outreach with CE #35 and a small tested PR (OWQ-11 (a); D035 item 3).
DG001 and the other open parts are unchanged. The header gained the pointer; nothing above changed.
