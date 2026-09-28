# D057: Non-generative components: bindable, badged, switchable

> **Status:** accepted · **Decided by:** owner delegation (2026-09-28, lightly edited: "Go ahead without the GPG passphrase. I will not
> be near the PC for hours. We are working remote"; "Tiny models with no cloud availability should be tested directly on PC. Either
> way, except for GPG signing, we can do everything else"; for a choice between design options, "Figure out the best option for this
> use case"); decided under the owner's delegation; the owner may overrule it on return · **Decided:** 2026-09-28 · **Recorded:**
> 2026-09-28
> **Scope:** how doc 58's purpose-specific components (retrievers, rerankers, extractors, checkers, flaggers, translators, voices,
> transcribers) are bound, shown, qualified and switched off (DG057 option B; doc 58 OQ3). **Refines:** D024 item 4 (component kinds
> bindable beside the roles); D037 (badges per component kind); both by dated notes. **Related:** D010, D023, D048, D049, D051, D055,
> D056; DG057; doc 38 §5.2–§5.3; doc 55 (knob table); doc 58 (§1.2, §4.9–§4.11); doc 63 §7.
> **Open parts:** the list of component kinds and their user-facing names (the names table, D034 item 3); the per-kind suites and
> bars (doc 58 §4.9, proposals); the component rows in Settings → Models (doc 63 §7's grid); the journal record for component outputs
> (DG053); which encoders can run at all (D056).

## Context

- D024 item 4: roles are a closed list (`router`, `writer`, `scripter`, `explainer`, `play-tester`, `translator`); the user binds each
  to a configured model, and a step never runs on a setup other than the one shown. D051 item 9 adds `planner` after v1.
- Doc 58 §1.2 proposes a component contract: one consumer seam per component; advisory or pre-filtering only; a code-owned fallback;
  qualified against the simple baseline; visible, with "answered by" and a kill switch; optional pinned downloads.
- Doc 58 §4.11 items 1 and 5: D024's roles have no slot for components, and doc 55's knob table keeps model choice out of presets
  ("no preset names another model", under D023 decision 3 and D024); a component needs its own visible binding, a badge per component
  kind (D037), a plan-card line and a kill switch, with qualification suites per component kind.
- DG057 recommends B. Decided under the owner's delegation, as the decisions README's "owner delegation" kind (the practice that
  follows from D049) asks when one option is sound.

## Decision

1. **Option B of DG057: component kinds become bindable** beside D024's roles. A component runs only when its kind is bound and
   enabled; otherwise the code-owned fallback answers.
2. **Each component kind carries:**
   - a **badge per component kind** (D037), from Plotroom's own qualification suites for that kind;
   - a **plan-card line** before a run;
   - an **"answered by" line in the inspector** that names the component, the artifact and the threshold;
   - a **kill switch** that returns the code-owned fallback with the same accepted result class.
3. **Qualification suites per component kind** (doc 58 §4.9), against the simple baseline each kind must beat (doc 58 §1.2 item 4).
4. **A harness preset never names a component** (option C rejected): presets adapt how Wilco asks, never which artifact answers (doc
   55's knob table; D023 decision 3; D048).
5. **Tests first** (DG057): a component runs only when bound and enabled; its kill switch returns the code-owned fallback with the
   same accepted result class; "answered by" names the component, artifact and threshold.

## Alternatives considered

| Option (DG057) | Why not chosen |
| --- | --- |
| A: components fixed by the release, enabled per feature in Settings, shown only in the inspector | The user cannot choose or see which artifact serves a seam before a run (D010, D024) |
| C: a harness preset names the component | Doc 55's knob table keeps model choice out of presets (D023 decision 3) |

## Consequences

- The glass box and user choice work for components as for models (D010, D024 item 4). Admission stays with code's verifiers
  (doc 25 principle 4); a component orders, shortlists, flags or drafts, as doc 58 §1.2 item 2 proposes.
- Which encoder components can be bound at all follows D056 (sidecar-served only, for now); escalation between generative stages is
  D055, not a component binding.
- Components stay harness code steps or editor features, never agent tools, with no network, file or process reach (doc 58 §1.2
  item 7; `AGENTS.md`); a component that acts as a decision model in front of the generative model still follows D023 decision 5.
- Friction (D049): more settings, but an unbound kind needs no setup (the code-owned fallback answers), so AI-off users see nothing
  new; a component is never enabled silently.
- Folding steps, not done here: doc 58 §1.2 and §4.9; the plan card and inspector (doc 38 §5.2–§5.3); Settings → Models (doc 63 §7's
  ladder grid gains component rows). D024 and D037 carry dated notes.

## Sources

DG057; `AGENTS.md`; D023 (decisions 3 and 5); D024; D034 item 3; D037; D048; D051; doc 55 (knob table); doc 58 (§1.2, §4.9–§4.11,
OQ3); doc 38 (§5.2, §5.3); doc 63 §7; the owner's delegation of 2026-09-28.
