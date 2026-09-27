# D011: Realism and common sense are defaults, never walls

> **Status:** accepted (invariant) · **Decided by:** owner (`AGENTS.md`) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** generators, templates, lints, lenses and Wilco's behaviour. **Related:** D009, D010, D015.
> **Open parts:** OWQ-08 (names and levels of the realism setting; answered 2026-09-27 → D034), OWQ-22 (boundaries for generated
> moral choices; answered 2026-09-27 → D041).

## Context

The owner: realism and common sense were part of what made the original missions work, but they must not stand in the way of user
creativity or storytelling. `AGENTS.md` ("Realism and common sense are defaults, never walls") is authoritative.

## Decision (summary; `AGENTS.md` governs)

1. Generators, templates and Wilco **default** to grounded, plausible, era-appropriate content and common-sense logistics.
2. The user's **explicit creative intent always wins**: the tool never refuses, silently "corrects" or nags about a creative choice.
3. Plausibility checks are **advisory and dismissible** ("intentional"). Only what the engine or the target profile cannot run is an
   error.
4. How strongly realism applies is an **explicit, visible setting per mission and per campaign**, not a hidden policy.

## Alternatives considered

- Realism as a hard rule (block implausible setups): kills fun and storytelling, and lectures the author.
- No realism defaults: loses the grounded feel the owner names as part of the formula, and weak models drift to generic action tropes.

## Consequences

- **Severity policy**: engine or profile impossibility is an error; realism and taste findings are info or warn, dismissible per mission
  as "intentional", with fixes computed by code and applied through undoable commands (doc 41 §6; docs 32 and 39).
- The realism setting steers lint wording, lens wording and generator defaults. Doc 39 §5.1 proposes three levels: Cinematic, Grounded
  (default) and Doctrinal. Names and levels are proposals until OWQ-08 settles them.
- Code-owned generator defaults come from corpus measurements (doc 35 §9, rc41–rc57: scale presets, force ratios, time of day, weather)
  and stay overridable per mission.
- Wilco never gives realism as a reason to refuse an edit the user asked for; it may add one dismissible note.
- Generated suggestions that touch moral choices follow the boundary list OWQ-22 decides; the user's own content is not filtered.

## Sources

`AGENTS.md`; doc 35 §9; doc 39 (§2 principle 4, §5.1, §6.2); doc 41 §6; doc 28 OQ8; `prompts/design-sensibility/code-owned-principles.md`.

## Amendment notes

### 2026-09-27: refined by D034 and D041 (pointers)

The realism levels are named by the design round in the names table the owner reviews before the first release (OWQ-08 (a); D034
item 3); doc 39 §5.1's Cinematic, Grounded and Doctrinal are the starting candidates. Generated moral-choice suggestions follow a
short boundary list written in Standing Orders, and the user's own content is never filtered (OWQ-22 (a); D041). The header gained
pointers; nothing above changed.
