# DG023: A fixed tool set per mode instead of per-turn `active_tools`

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G5).
> Status: **open**. **Decision by: technical**. Blocks: the tool-exposure design in `ofp-agent-rig`; doc 40 R5 stays `proposal-only`.

## Context

- **Doc 12 §3.1**: "Workflows: per-turn `RequestPatch.active_tools` restricts which tools the model sees. For example, a 'Briefing
  writer' workflow sees only read tools plus `set_briefing`." §5's capsule and "Fewer tool schemas" row rely on it.
- **Doc 21 §6.2 rule 7**: "Small tool subsets per step; blanket-denied tools are hidden from the model."
- **Doc 38 §3.3**: tools ⊆ registry ∩ plugin grants ∩ role, empty for Pick and Fill (they answer by structured output).
- **Doc 40 §2.3** [V]: a changed tool list breaks the provider cache without an error. **R4**: model, effort, schema and tool set
  stay fixed inside one cache namespace per (stage, DecisionKind). **R5**: chat modes get a fixed, name-sorted tool set; out-of-step
  calls are refused by admission with a typed error rather than removed from the list; mode switches may use Anthropic's
  `tool_addition` / `tool_removal` beta (not Sonnet 5); plugin tools use `defer_loading` past about 10 tools or 10K tokens.

## The gap

Per-turn narrowing (doc 12) changes the tool list between turns and so defeats caching in chat; doc 21's per-step subsets are
compatible only if each step's set is fixed. No doc states the unit over which the tool set must stay constant.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Keep per-turn `active_tools` | The model sees only what it may call | Cache miss on every change; more cost and latency |
| B | Fixed, name-sorted tool set per chat mode and per (stage, DecisionKind); out-of-step calls refused by admission with a typed error; local engines mask by grammar | Cache-stable; doc 21's "small subsets" holds at mode and step granularity | The model may attempt a tool it cannot use now (refused, costs a turn) |

## Recommended resolution (proposal)

Option B. The unit of a fixed tool set is a chat mode or a cache namespace (stage × DecisionKind). Tools blanket-denied in that mode
stay absent (doc 21 rule 7 at mode granularity); tools allowed in the mode but not in the current step are refused by admission
with `ToolNotInStep { tool, step }` and a list of what the step allows. Serialisation is deterministic (sorted names, stable schema
text). Enabling a plugin mid-session costs one cache miss, or uses deferred loading where the provider supports it. Pick and Fill
steps expose no tools (doc 38 §3.3).

## What it would change

- Doc 12 §3.1 "Workflows" bullet and §5's "Fewer tool schemas" row: fixed set per mode or namespace; admission refusal.
- Doc 21 §6.2 rule 7: "per mode or step namespace".
- Doc 40 R5: rule; G5 closed.

## Affected docs

Docs 12, 21, 40 (doc 38 already consistent).

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 12 §3.1 and §5, doc 21 §6.2, doc 38 §3.3, and doc 40 §2.3, R4, R5 and §4.3 G5, re-read on 2026-09-27.
