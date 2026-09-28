# D052: Strict script regions: a gate with an explicit, visible way out

> **Status:** accepted · **Decided by:** owner delegation ("Figure out the best option for this use case", 2026-09-28); the option
> was chosen by the design round and can be overruled by the owner · **Decided:** 2026-09-28 · **Recorded:** 2026-09-28
> **Scope:** what happens when a script region the user set to Strict has a contract error (doc 65 §4.4, owner options (a)–(c)).
> **Refines:** D011 (realism and checks as defaults, never walls). **Related:** D010, D049, D050, D051; doc 62; doc 65.
> **Open parts:** the exact wording of the gate cards; how "Preview once" runs are shown in the run history (doc 65 SG-candidates).

## Context

- Doc 65 proposes an opt-in Strict level for script regions: code the Strict checker accepts is gated like compiled code, and all
  Wilco, generator and plugin output must pass Strict. It leaves one owner choice open: what happens when a region the *user* set to
  Strict has a contract error — (a) block export, (b) block with an in-refusal downgrade, or (c) never block and only withhold the
  "verified" badge.
- The owner's principle (doc 62; 2026-09-28): an API leads its user into correct usage, and enforcement, not advice, is what makes a
  check worth having ("the language won't compile if things are not correct"). D011: the user's explicit intent always wins; checks
  are defaults, never walls. D049: remove friction before explaining it.

## Decision

1. **Option (b): Strict means strict, with an explicit way out.** A region the user set to Strict never reaches Preview or export with
   a contract error unless the user explicitly chooses an exception, in the way Rust code with errors does not compile unless the
   author writes an explicit, visible opt-out.
2. **While editing:** contract errors show live, with the fix named and a quick fix where one exists, so the gate rarely surprises.
3. **At Preview:** the gate offers "Fix" or "Preview once without strict checks". The exception covers that one Preview run, is
   recorded in the run history, and leaves the region Strict.
4. **At export or publish:** the gate offers "Fix" or "Downgrade this region to Advisory". The downgrade is persistent and visible:
   the region loses its verified badge, the change is recorded (who, when, which findings) and can be reversed at any time.
5. **No exception for model or tool output.** Wilco, generator, plugin, external-agent, quick-fix and migration output has no such way
   out; it must pass Strict (doc 65).
6. **Never silent.** No level change, exception or bypass happens without a visible user action.

## Alternatives considered

| Option (doc 65 §4.4) | Why not chosen |
| --- | --- |
| (a) Block export with no in-place way out | A wall at the worst moment (mid-iteration); conflicts with D011 and D049 |
| (c) Never block; withhold the badge only | Turns Strict into Advisory; the user who chose Strict for guarantees gets advice |

## Consequences

- Strict keeps its meaning (a Strict region is never shipped with contract errors without a recorded, visible decision), and the
  user's creative control is never removed (D011).
- The Preview gate and the export gate are distinct cards; the "Preview once" exception needs a run-history entry and no change to the
  region's level.
- Doc 65's owner options for user regions are settled by this record; doc 65 gains a pointer.

## Sources

Owner delegation of 2026-09-28; doc 65 §4.3–§4.5, §4.10 and open questions 1–2; doc 62 (governing principle); D011; D049.
