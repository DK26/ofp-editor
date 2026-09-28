# D058: Editor first; harness testing on cloud models; local small models last

> **Status:** accepted · **Decided by:** owner (direction of 2026-09-28, verbatim: "while the harness is key, we first need a working
> mission editor so we will have something useful for the harness. Make it a piority for now."; "All in all, when testing harness,
> use the cloud and, not local SLMs. These we will leave for last for optimization. I need my GPU free") · **Decided:** 2026-09-28 ·
> **Recorded:** 2026-09-28
> **Scope:** the order of work across the roadmap's lanes, and which models harness testing uses until the optimization phase.
> **Refines:** the roadmap's lane order (`docs/roadmap.md` §6, a proposal); D044 (for harness testing, cloud-first becomes cloud-only
> until the optimization phase). **Related:** D004, D013, D016, D017, D022, D023, D037, D045, D046, D048, D050; docs 44, 46–49, 53–55,
> 59, 64, 68; `docs/roadmap/m0-m3-foundations-to-preview.md`.
> **Open parts:** when the optimization phase starts (after the editor milestones; the owner calls it).

## Context

- The harness (Wilco, the workflow runtime, presets, qualification) acts on the editor's document model, commands, validators,
  catalog and Preview. Without a working editor there is nothing real for it to drive, and harness results measured on suites alone
  do not tell whether it helps a mission maker.
- The roadmap already orders the editor first (M0 foundations → M1 viewer → M2 classic editor → M3 Preview; the AI layers from M4),
  but lane D (AI de-risking and harness) ran in parallel and took most of the recent effort, much of it on the owner's GPU.
- Local small-model runs occupy the owner's only GPU for hours (doc 64's pilot ran about 7.5 hours).

## Decision

1. **Editor first.** Work on the roadmap's M0–M3 comes first: the workspace and its mechanical checks, the formats and the lossless
   config and mission parser, the document model and commands, the map and the classic editor, then Preview. Lanes A (core and
   formats), B (renderer and shell) and C (game integration) have priority; lane F (docs) supports them.
2. **Lane D pauses new work.** No new model or harness research starts. Work already in flight that feeds the editor's coding rules
   finishes (doc 64's revision and doc 68, whose playbook updates `AGENTS.md`).
3. **Harness testing uses cloud models.** When harness work resumes, its tests and qualification runs use hosted models through the
   guarded paths already built (D044–D046, D050; `tools/local-qual`'s pinned routes, free-only guard and budget caps), not local small
   models. The owner has accounts with **OpenRouter, Groq and Cloudflare Workers AI** (owner, 2026-09-28: "These two could also be
   useful for us when testing free models and needing more tokens to test models"), so free-tier load can be spread across three
   providers, as D050's route lists do. Before Groq or Cloudflare is first used, `tools/local-qual` gains the same key handling it has
   for OpenRouter (a DPAPI key store per provider, the launcher, a zero-spend or budget guard fitted to each provider's limits; doc 52
   §2.1 lists them); keys are entered by the owner through those scripts, never in chat or on a command line.
4. **Local small models come last,** as optimization after the editor milestones: SP-11, local qualification and preset tuning on
   local weights, and local arms of docs 53, 55 and 59 wait for that phase. D022's product design (the managed local runtime for
   users) is unchanged; only the order of this project's own testing changes.
5. **The owner's GPU stays free.** No agent starts `llama-server`, loads a model into Ollama or runs other GPU jobs unless the owner
   asks for it. The editor's renderer tests run headless on software rasterizers (WARP, lavapipe), as testing-strategy already plans;
   visual checks on real hardware are the owner's manual verification notes.

## Consequences

- The roadmap's lane D row and SP-11 carry a pointer to this record; M6's qualification track starts with cloud models.
- Spikes that need the owner's hardware or installs (SP-01–SP-05 visual checks; SP-06 and SP-07 on real game installs) are scheduled
  with the owner; the rest of M0 proceeds without them.
- Research docs 44, 46–49, 53–55 and 59 keep their results; their local-model next steps are deferred, not cancelled.

## Sources

The owner's messages of 2026-09-28 quoted above; `docs/roadmap.md` §4–§6; `docs/roadmap/m0-m3-foundations-to-preview.md` (M0–M3);
`docs/roadmap/spikes-and-probes.md` (SP-11); D044; D022.
