# DG033: Standing Orders phase-0 decisions (schema, demos, Easy/Advanced, relabels)

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by:** items 1–2 **technical**; items 3–4 **owner** (they change what the faithful original dialogs show). Blocks: doc 33
> phase 1 (registry and cards) for items 1 and 4; phase 3 (demos) for item 2; lesson C7 and the dialog layer for item 3.

## Context

Doc 33 §9 phase 0 ("Decisions") lists four design-gap requests: entry schema and ownership, demo fidelity policy, the Easy/Advanced
replacement, and plain-language relabels. The names are settled by the owner (Standing Orders, Drill; doc 21's Academy = Drill),
and "no new UI name" may ship before it clears doc 02 §9. The README promises "the same dialogs" as the original editor.

## The gap

Phase 0 names four decisions but files none of them: who owns the entry schema and how it is built, how faithful a demo must be
before it ships, what replaces the original Easy/Advanced switch, and whether plain-language labels replace or sit beside the
original ones. Each item below gives its context, options (lettered) and a proposal.

## Item 1: entry schema version and ownership (doc 33 OQ3)

- **Context:** doc 33 §3.2 sketches `ConceptEntry`, `Grounding`, `UiAnchor` and `Demo`; §3.3 says a build step (`xtask` or
  `build.rs`) parses the authored Markdown into typed entries and generates SKILL.md's index; the parser follows `AGENTS.md` parser
  rules (pure, size-capped, permissive on unknown keys). OQ3: a crate such as `standing-orders` or the editor core; `build.rs` or
  `xtask`; who owns the schema version.
- **Options:** (a) editor core; (b) a small registry crate owning the types, the parser and `schema: standing-orders/<major>`;
  generation by `build.rs`; (c) as (b), with generation by `xtask` and a CI check that the committed index matches.
- **Proposal:** (c). The crate is pure (bytes in, entries out); `build.rs` should not write into the source tree, and `xtask` keeps
  generation explicit. The registry crate owns the schema version; a major bump needs a migration note. DG031 and DG032 decide ids and
  the merged card kind.

## Item 2: demo fidelity policy

- **Context:** doc 33 §4.6: a computed layer (ported rules, exact) and an illustrative layer (storyboard, marked "illustration"); every
  behavioural demo names a probe mission that asserts the same outcome in the real game; AT6 requires demo and probe to agree.
- **Options:** (a) ship behavioural demos only after their probe passes on every profile; (b) ship them with an "unverified on
  (profile)" badge until the probe passes, withdraw on failure; (c) computed-layer demos only in v1.
- **Proposal:** (b). Computed layers always ship; an illustrative layer always carries its "illustration" label; a behavioural demo
  whose probe has not run on a profile shows "unverified on (profile)"; a demo whose probe fails is withdrawn until fixed (AT6).

## Item 3: the Easy/Advanced replacement

- **Context:** the original editor has an Easy/Advanced switch; "Easy only hides things. CWR defaults to Advanced; retail default
  [U]" (doc 33 §1.2 row 19). Doc 33's lesson C7 teaches "the Easy/Advanced replacement". Doc 33 §4.1 uses two disclosure levels
  (hover card, manual page); doc 31 §4.1 uses short forms with "Advanced" folds.
- **Options:** (a) keep the original switch exactly; (b) replace it with progressive disclosure (short forms and folds) and drop the
  switch; (c) keep the switch as a view preset over the same disclosure system: Easy hides what the original hides, Advanced shows
  everything, default Advanced as in CWR.
- **Proposal:** (c): faithful to the original and to community tutorials, and no second mechanism to maintain.

## Item 4: plain-language relabels beside or replacing the original labels (doc 33 OQ2)

- **Context:** doc 33 suggests plain-language lines such as "Countdown: fires after the delay no matter what" and "Group: not all
  inside"; its recommendation is "beside them, so community tutorials still match". §3.1 `labels` keeps the original label
  (resolved from the user's game locale) plus plain names.
- **Options:** (a) replace the original labels; (b) keep original labels on controls and show the plain-language line beside them
  (card `what` line or secondary text); (c) a setting to switch.
- **Proposal:** (b). Original labels stay primary so two decades of community tutorials still match; the plain line is the hover
  card's `what` and a dim secondary line in dialogs where space allows.

## Options

Listed per item above: item 1 (a)–(c), item 2 (a)–(c), item 3 (a)–(c), item 4 (a)–(c).

## Recommended resolution (proposal)

1. A pure registry crate owns the entry types, parser and schema version; `xtask` generates the SKILL.md index, checked in CI.
2. Computed layers always ship; behavioural demos carry "unverified on (profile)" until their probe passes and are withdrawn on a
   failing probe.
3. Keep the Easy/Advanced switch as a view preset over the shared disclosure system, default Advanced (**owner**).
4. Original labels stay primary; plain-language lines sit beside them (**owner**).

## What it would change

- Doc 33 §3.2–§3.3 (crate, schema version, `xtask`), §4.6 (fidelity rule), §5.4 lesson C7 (wording), OQ2 and OQ3 (answered), §9
  phase 0 (done).
- Doc 03 and doc 05 (dialog fidelity notes) for item 3, if the switch's behaviour needs recording.

## Affected docs

Docs 03, 05, 31, 33; DG031, DG032.

## Decision record

Open (per item).

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 33 §1.2 row 19, §3.1–§3.3, §4.1, §4.6, §5.4 (C7), §9 phase 0, OQ2 and OQ3; doc 31 §4.1; the README's
  description of the editor, re-read on 2026-09-27. The doc 03 and doc 05 references are where dialog fidelity is recorded; their
  Easy/Advanced text was not re-read here.
