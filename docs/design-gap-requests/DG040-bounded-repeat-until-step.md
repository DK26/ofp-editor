# DG040: A bounded "repeat until" step with a code-checked condition and a hard maximum

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 under the owner's go-ahead of 2026-09-28 ("Either way,
> except for GPG Signing, we can do everything else"), as one of three dynamic-workflow additions discussed with the owner (DG040,
> DG041, DG042). Status: **open**.
> **Decision by: technical** (design round; the owner asked for the capability, and every option but A amends D025 decision 2 or
> doc 38 §3.2, so the owner reviews the result). Blocks: any workflow definition that repeats a group of steps; doc 38 §3.2's step
> table and its "no loop" rule stay as written until decided.

## Context

- **D025 decision 2; doc 38 §3.2.** Steps come from "a closed set of twelve kinds". Doc 38: "There is deliberately no loop, goto,
  sleep or free 'choice' kind: bounded repair lives inside model steps, branching is `when` plus `call`, and waiting happens only in
  `ask` and `approve`." `map` runs one inline step or a sub-workflow per item of a collection keyed by a stable id, with
  `max_items`; §4.5's placeholder caps are ≤ 512 items per `map`, ≤ 2,000 decisions per run and call depth ≤ 3.
- **Doc 38 §7, "Done requested".** The completion gate already repeats in a bounded way: "a red gate becomes one more repair turn
  with a code-written finding within budget, then an honest report".
- **Doc 25 §7.2; doc 38 §3.3.** Repair inside one model step quotes one finding per turn and stops on a recurring finding, a repeated
  answer or a spent R (0–3).
- **Doc 21 §1.4** rejects "ungated 'run everything' loops"; **§8.2** stops a run whose fingerprint cycle repeats three times.
  **Doc 56 WR5**: exact progress detection over every harness-visible transition, kept across resume. **WR6**: the worst case is
  reserved before each model call.
- **Doc 38 §4.2.** Journal keys are `(run, step, item, attempt)` built from authored ids and stable editor ids, never list indices,
  "because positional matching breaks on reorder".
- **Doc 63 §8.3; D051 item 9.** A model-proposed `PlanDraft` may not contain "loops other than a bounded `map`", and its `when` may
  test only inputs, `ask` answers and trusted code outputs.
- **Doc 38 §10 W1** names `core/validate-and-fix`, a workflow whose natural shape is "fix, re-check, and go again while findings
  remain".

## The gap

The format can repeat work only inside one model step (repair), at the completion gate, or over a collection fixed before a `map`
starts. It cannot say "run this group of steps again until a code check passes, at most N times", for example: fix one finding,
re-validate, and continue while findings remain and each pass makes progress. An author must unroll the group N times or hide the
loop inside a code step, where the plan card, the journal and the inspector cannot show its iterations.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | No loop (today): repair inside model steps, the gate's repair turn, and `map` over a code-computed collection such as the current findings | Keeps the closed set; the simplest runtime | Repeat-until procedures are unrolled or hidden in code steps; the plan card cannot show them |
| B | A thirteenth step kind, `repeat`: the body is one inline step or a sub-workflow (`call`); `until` is a non-empty list of registered check ids or a closed `when` predicate over admitted or code outputs, never a model's judgement; `max_iterations` is required and capped by the loader; each iteration is a journal item keyed by its ordinal (iterations are sequential, so the ordinal cannot be reordered); the loop settles `Done`, `MaxReached` (to `on_fail`), `Stalled` (no progress, WR5) or `BudgetLimited` | The shape discussed with the owner; visible and resumable like `map`; the condition is code-owned | Amends D025 decision 2 and doc 38 §3.2; one more kind for the compiler, the run graph and the path tests |
| C | `until` and `max_iterations` as attributes of `call`, with the same rules as B and no new kind | Keeps twelve kinds | Changes what `call` means; a reader must check every `call` for a loop; harder to show as its own row |
| D | `map` over a code-computed range 1..N, later items skipped by `when` once the check passes | No format change | `map` items are independent and join all-settled (doc 38 §4.5), so "stop at the first pass" is not native; the plan card shows N items even when one suffices |

## Recommended resolution (proposal)

B, the shape discussed with the owner, held to the doctrine it touches:

- The `until` condition is computed by code: a registered check or a closed `when` predicate. A model's answer, a judge or free text
  can never end or extend the loop, so it is not an "ungated" loop in doc 21 §1.4's sense.
- `max_iterations` is required, and the loader refuses a value above a cap that the design round sets as a placeholder, like doc 38
  §4.5's caps. An iteration that changes nothing stops the loop (doc 56 WR5), and each iteration reserves its worst case before it
  starts (WR6; counted as DG016 decides).
- A model step inside the body keeps its own `verify`, `repair`, `on_fail` and grant (D051), so iterating never raises a level.
- Whether a model-proposed `PlanDraft` may contain `repeat` is decided with DG042; until then doc 63 §8.3's "no loops other than a
  bounded `map`" stands.

If the design round prefers to keep twelve kinds, C is the fallback with the same rules.

## What it would change

- D025 decision 2 (an amendment note: thirteen kinds) and doc 38 §3.2 (table row and the "no loop" sentence); doc 38 §4.2 (class:
  structural), §4.5 (caps), §5.3 (run-graph glyph), §6.2 (refusals: missing `until` or `max_iterations`, a maximum above the cap,
  an `until` that reads a model step's output).
- Doc 21 §1.4: a note that a bounded, code-gated `repeat` is not an ungated loop.
- Tests first (proposal): an AT-W1 fixture per refusal; a faux-model path test whose check never passes stops at the maximum and
  follows `on_fail`; an iteration that changes nothing settles `Stalled`; a crash at every iteration resumes with zero extra model
  calls for settled entries (doc 38 §6.4).

## Affected docs

D025; doc 38 (§3.2, §4.2, §4.5, §5.3, §6.2, §6.4, §10); doc 21 (§1.4, §8.2); doc 56 (WR5, WR6); doc 63 §8.3; D051 item 9; DG016;
DG042.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from the owner's dynamic-workflow additions, as the go-ahead of 2026-09-28 allowed. D025, doc 38 (§3.2–§3.3, §4.2, §4.5, §7,
  §10), doc 21 (§1.4, §8.2), doc 56 (WR5, WR6), doc 63 §8.3 and D051 item 9 were re-read on 2026-09-28.
- No research doc proposes this step. Options B–D are this request's reading of the format as written; nothing here is decided.
