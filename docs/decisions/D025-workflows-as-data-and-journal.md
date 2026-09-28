# D025: Workflows are typed data; runs keep a decision journal

> **Status:** baseline · **Decided by:** research (doc 38, building on docs 21 §6 and 25) · **Decided:** 2026-09-27 · **Recorded:**
> 2026-09-27 · **Scope:** every multi-step procedure Wilco or the AI-off features run. **Related:** D009, D010, D020, D024, D026.
> **Open parts:** DG007 (one definition format), DG008 (`when` vocabulary), DG010 (resume wording), DG011 (wrapper name), DG012
> (requalification), DG016 (accounting), DG017 (journal storage), DG018 (port records); OWQ-15 (external deciders;
> answered 2026-09-27 → D036); OWQ-16 (plugin chains; answered 2026-09-27 → D043).

## Context

Weak models cannot hold a long plan (D009). Claude Code puts orchestration in a script the model writes per task; Codex keeps reliable
flows as fixed Rust tasks and lets users extend prose and guards; workflow engines interpret declarative graphs or replay journals
(doc 38 §1.1). Plotroom needs the user to direct mid-run, runs that survive crashes, and results that do not depend on concurrency.

## Decision

1. **Workflows are typed data (TOML) interpreted by a Rust runtime.** The model never writes control flow; chat may start and
   parameterise a workflow, never redefine it.
2. **One format for built-in and pack workflows**: metadata with a model policy (`Forbidden` / `Optional` / `Required`), typed inputs,
   budget ceilings, steps from a **closed set of twelve kinds**, outputs and a completion gate. A model step cannot exist without its check
   and fallback; repair is a bounded attribute; only a code gate says "done".
3. **A typed decision journal**: pure steps are recomputed; recorded steps (model, user, plugin) settle once and are reused; effects
   commit as idempotent undo groups. **Resume never re-executes a settled model call or a Preview**; a changed input marks steps stale.
4. **The user directs mid-run**: `ask` and `approve` steps park the run behind a one-shot, validated card (what waits is D024).
5. **Deterministic fan-out**: `map` steps iterate over stable ids, seed items from their keys and admit in key order. Model-spawned
   sub-agents and agent teams are rejected.
6. **Policy hooks are built in and typed** (admission, autonomy, provenance, budget, completion gate). Packs may only tighten, through
   declarative lints; no shell, HTTP, MCP-tool, prompt or agent hooks exist. Runs are pinned to a definition snapshot.
7. **A small in-house interpreter**; no workflow-engine dependency (duroxide is the reference design).

## Alternatives considered

- Model-written orchestration scripts per task: control flow a weak model cannot be trusted with.
- Fixed Rust code per workflow only: no packs, no user-visible definitions.
- An external durable-execution engine: heavy dependency for a desktop editor; the needed subset is small.

## Consequences

- **Glass-box UX** (doc 38 §5): palette actions, a plan card with steps and budgets, a run panel by phase, one-tap cards, a "why"
  inspector per step, a read-only run graph; the runtime writes the checklist, the model has no plan tool.
- **Testing like durable-execution code** (doc 38 §6.4): golden journals replayed in CI, cassettes keyed by capsule hash, a fake model
  that walks every menu escape, and a crash at every journal entry that must resume to the same document with zero extra model calls.
- Doc 25 §4.2's campaign `Stage` enum becomes workflow definitions plus campaign code steps on this runtime (doc 38 §4.7).
- A definition's `[budget].turns` is a whole-run ceiling that replaces only the per-request "model turns" row of doc 21 §7.1 (doc 38
  §3.4); the other effort rows still apply.
- Single gates and checks of doc 21 §6.1 become non-empty lists (doc 38 §3.2).
- External agents start workflows through the same admission over MCP (doc 38 §9); T2-plugin workflows are not exposed in v1.

## Sources

Doc 38 (TL;DR, §1–§9, open questions); doc 21 §6–§8; doc 25 (§4.2, §5); doc 22 §4.2.

## Amendment notes

### 2026-09-27: refined by D036 and D043 (pointers)

External agents may list and start workflows over the v1 MCP server, but decision points are answered only in the editor until
`workflow.decide` ships after v1 (OWQ-15 (a); D036 item 6). Cross-publisher chains are allowed only in first-party and
user-authored workflows, and a third-party pack workflow whose `requires` names another publisher's plugin is refused at load
time (OWQ-16 = DG014 option B; D043). The header gained pointers; nothing above changed.

### 2026-09-28: decision 1 refined by D051 (plans as data, after v1)

A note under lifecycle item 5; [D051](D051-capability-ladder-freedom-by-qualification.md) governs, and the header is unchanged (no
open part to mark). Doc 63 §8.7's option B was adopted under the owner's go-ahead of 2026-09-28 (lightly edited): "Tiny models with
no cloud availability should be tested directly on PC. Either way, except for GPG signing, we can do everything else." Recommended
option adopted under the owner's go-ahead; overrule on return.

- **After v1**, decision 1 reads: "the model may propose a definition as data; only a user's save makes it runnable" (doc 63 §8.7).
  The `planner` role (D051 item 9), bound to a setup with an FR8 grant, may propose a `PlanDraft` built only from registered units,
  reached only when no workflow fits (`Dispatch::NotSupported`); the definition compiler checks it in dry-run mode; it runs only
  after the user saves it as their own workflow, through the ordinary loader, with a click that carries `UserIntent` (in Auto too).
  A plan that is not saved never runs.
- **Unchanged:** Wilco has no tool that creates, saves or edits a definition; chat never redefines a workflow; a `PlanDraft` adds no
  step kind, so decision 2's closed set of twelve kinds stands; its `when` may test only workflow inputs, `ask` answers and outputs
  of `code` steps computed from trusted state, so untrusted text cannot change which units run; runs keep decisions 3–7.
- **In v1** decision 1 applies as first written.
- **Still open:** the `PlanDraft` format, its checks and where saved plans live
  ([DG042](../design-gap-requests/DG042-plan-draft-format-and-saved-plans.md)); a bounded "repeat until" step, which would amend
  decision 2 if adopted ([DG040](../design-gap-requests/DG040-bounded-repeat-until-step.md)).

### 2026-09-28: D054's review stage adds no step kind (pointer)

A note under lifecycle item 5; [D054](D054-review-stage-for-creative-steps.md) governs (DG041 option B), decided under the owner's
delegation; the owner may overrule it on return. The advisory review of creative candidates is a `review` key of `sample`, not a new
step kind, so decision 2's closed set of twelve kinds stands (DG041 option C, a `panel` kind, was not adopted); a reviewer never
admits, rejects, edits or repairs, so only a code gate still says "done". The header is unchanged; nothing above changed.
