# D015: No-code first, scripting always available

> **Status:** accepted (direction); design proposal-only · **Decided by:** owner · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** attributes, modules, rules, cinematics, scripting and power tools. **Related:** D003, D010, D011, D012, D020.
> **Open parts:** DG001 (non-aborting Preview for the debug console), DG003 (attribute vocabulary), DG004 (what "module" means), DG007
> (one definition format), DG008 (condition language), DG009 (cinematic engine facts owner); OWQ-14 (which modules ship in v1;
> answered 2026-09-27 → D036).

## Context

The owner: scripting is very important and the whole experience should be upgraded; camera and cinematic scripting must be first-class;
if users can achieve everything without scripting, even better; everything the community loves should be easy, not hacky; classic
workarounds done by hand-editing `mission.sqm` or `description.ext`, or through init-line code, get direct and friendly equivalents.
Doc 31 §2 found that the most-downloaded community resources are tools that work around editor gaps, and that the most-duplicated
gameplay pattern (artillery) exists as many separate scripts.

## Decision

1. A **no-code ladder** of five rungs: (1) attributes and presets, (2) typed modules, (3) an event → condition → action rule builder,
   (4) a cinematics timeline, (5) the script editor with Teller, the mission-aware language service.
2. Every rung **compiles to plain vanilla content** for the mission's target profile (triggers, waypoints, sync, Effects fields,
   `description.ext`, `briefing.html`, SQS/SQF). No addon and no runtime framework: the mission runs with Plotroom's sidecar deleted.
3. **Code is one click away** and stays readable in the original in-game editor; native engine primitives come first, SQS only for
   sequencing (doc 31 §4.4).
4. **Camera and cinematics are first-class** (doc 32 timeline; doc 39 cutscene director). **Classic workarounds get power tools**
   (doc 37: intent attributes, an advanced property inspector, class remap, island retarget, SP↔MP, dependency repair, map-object
   actions, a safe raw mode, lift on import).
5. Every rung is glass-box (D010), profile-aware (D003) and configurable by weak models through typed forms (D009).

## Alternatives considered

- A runtime script framework shipped inside missions: adds a dependency, breaks vanilla compatibility and hides logic.
- Script-only power, as in the original editor: the pain the community worked around for two decades.
- No-code only, without code access: breaks the glass box and fails experienced scripters.

## Consequences

- The compiler owns the engine's scarce singletons (the global map-click handler, radio slots, the camera-script slot, hook files, the
  global namespace, a server guard that also works in single player) (doc 31 §4.5).
- Modules are T0 data: a typed schema plus minijinja lowerings per profile (D020); community modules ship as packs (D007).
- The timeline fits the real camera's limits (doc 31 §6; doc 32); a script error in Preview console text ends the session until DG001 is
  resolved.
- Teller ports the proven ideas of the owner's public LSP work (type algebra, precedence table, oracle, fuzzing), rewritten to
  `AGENTS.md` rules, with engine-parity field checks (doc 23 §13).

## Sources

README ("No-code first, scripting always available"); doc 23 §13; doc 31 (TL;DR, §1–§6); doc 32; doc 37 TL;DR; doc 39 TL;DR.

## Amendment notes

### 2026-09-27: refined by D036 (pointer)

The doc 31 §4.6 wave-1 modules whose probes pass on `Cwr` ship in v1. For rung 4, v1 ships the Cutscene-node recipe with camera
scripting through the script editor; the doc 32 timeline and the doc 39 cutscene director ship in v1.2 (OWQ-14 (a); D036 items 2
and 5). The header gained the pointer; nothing above changed.
