# Friction audit of the design (2026-09-28)

Research doc 66 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: the owner, contributors and LLM coding agents. This
file is meant to be read on its own.
Question answered (owner, 2026-09-28, verbatim): "As we design and implement, we will have to actively notice and think about
potential frictions and how to reduce or eliminate them." In Plotroom's terms: where does the current design (decisions,
architecture, roadmap, research docs, skills and tools) make a correct action slower, harder, more confusing or more error-prone than
it needs to be, for people using the editor, for models using its APIs and tools, and for contributors building it; and what would
remove each friction without weakening the product invariants?

**Status: proposal.** Nothing was coded. This doc, `docs/friction/README.md` and `docs/friction/register.csv` are the first contents
of the friction register that D049 starts. Every removal is a proposal; the ones that would change a decision record are listed in
§4 as proposed owner questions, **not filed**. This doc changes no decision.
**Epistemic legend** (doc 16's). **[V]** read in the cited repository file on 2026-09-28. **[I]** our inference or proposal. **[U]**
unknown until code or measurement exists. Each register row's evidence is [V] unless the row marks a claim [I]; every severity,
frequency class and removal is [I].
**Relation to sibling docs.** D049 and `AGENTS.md` ("Friction Review (Required)") set the duty; `docs/friction/README.md` sets the
register's format, severity and frequency scales, lifecycle, review checklist and measurement plan; `register.csv` holds all 138
entries with full evidence. The findings draw on most research docs from 01 to 65, the architecture and roadmap files, the
decision and DG records, the skills and the tools, as §Sources lists.
**Names.** Register ids are `FR-P-nnn` (people), `FR-M-nnn` (models) and `FR-C-nnn` (contributors). They are distinct from doc 63's
*freedom levels* FR0–FR8, which have no hyphen and no audience letter; where both appear, this doc says "freedom level FR2".
Doc-local labels 66-Q1 to 66-Q18 (§4) carry this doc's number, as FR-C-021 proposes for all doc-local codes.
**Hygiene.** Only repository files were read. No local paths, user names, keys or private project names. The register was assembled
from the sweep notes with a one-off script that refused to write local paths; from now on the register is edited directly
(`docs/friction/README.md` §4, §7), so no generator needs to live in the tree.

## TL;DR

- **138 frictions are registered** (81 people, 27 models, 30 contributors as primary audience; people are affected by 104, models by
  46, contributors by 44). 13 are severity 3. Six walkthrough sweeps raised 146 findings; a verification pass judged all of them
  real, merged 8 duplicates into their keepers and corrected 32 removals, 2 of which would otherwise have weakened an invariant.
- **The worst frictions for people sit where AI meets editing and where the game is launched**: a pending Wilco proposal blocks
  editing or is thrown away by the next edit (FR-P-042); every small AI edit costs a plan-card click (FR-P-060, FR-P-033); a user's
  strong cloud key gets the smallest steps until the user pays to qualify it (FR-P-064); Preview has no progress, timeout or failure
  states, so a failed launch looks like nothing happened (FR-P-008); first-release users get no first-run flow (FR-P-001).
- **For models, most friction is waste the harness could avoid**: retries on a throttled host followed by a stall card per decision
  (FR-M-008), tool names that differ between primer, digest, errors and manifest (FR-M-018, FR-M-004, FR-M-017), an unmeasured 'why'
  field on every answer (FR-M-013), cards that break the cache prefix (FR-M-016), free-text inputs where a menu would do (FR-M-020,
  FR-M-009).
- **For contributors, the rules are heavier than the checks**: public hygiene is a manual search on every commit (FR-C-012); every
  session loads over 700 lines of rules (712 when swept, 816 later the same day), mostly for code that does not exist yet
  (FR-C-010); the docs index cannot be read in one call
  (FR-C-011); counts and indexes drift because they are kept by hand (FR-C-015); the only verification commands named cannot run
  (FR-C-014).
- **Three umbrellas unlock many rows**: one wait-policy table for "what waits for a click" (FR-C-008), the names table D034 already
  requires (FR-C-009), and one standard-library check script for the repository (FR-C-014).
- **18 quick wins** are small and high value (§3). **18 owner questions** are proposed, not filed (§4), mostly on D024 (what waits
  for a click), D023 (rerouting without a click per switch), D037/D045 (what makes a model recommendable), D008 (source kinds) and
  AGENTS.md's structure. D050, recorded after the audit, has since answered 66-Q4 and part of 66-Q5 (§4, Verification notes).
- **Not assessable yet**: real step counts, waits, error rates and comprehension; several product areas were not swept (§5).

## 1. Method

**Sweeps.** Six walkthroughs, each taking the point of view of one audience and walking concrete tasks through the design as it
stands on 2026-09-28:

| Sweep | Walked | Rows (after merges) |
| --- | --- | --- |
| first-run | First launch, install discovery, target profile, first mission, the Preview loop, mods, keymap, help, updates, offline use, external agents' setup | 23 |
| ai-setup | Turning Wilco on: the connect flow, the Model Manager, qualification badges, free cloud, keys and caps, role binding, routing, disclosures | 24 |
| editing | Placing and editing content, dialogs, undo, proposals as ghosts, modules and regeneration, validation noise, import, campaigns, cinematics, model-facing edit tools | 25 |
| wilco-ux | Running Wilco: plan cards, autonomy, check-ins, stall cards, review of generated content, the inspector, run states, naming, learning | 23 |
| model-facing | What a model sees and does: intake, menus, repair, schemas, capsules and caches, tool names and manifests, MCP | 22 |
| contributors | Working in the repository: rule load, indexes, hygiene, tooling, commands, doc conventions, trackers, commits, future code scaffolds | 21 |

Each finding records its audience, area, the walkthrough, cited evidence, a proposed removal in D049's order (eliminate the step,
safe default, make wrong input impossible, automate, explain at the point of friction), where the change lands and a rough effort.

**Verification.** A second pass re-read the cited sections for every finding and judged four things: is the friction real, is the
removal sound, does it respect the invariants (product scope, typed undoable commands, validation, the glass box), and is it a
duplicate. Outcome: 146 findings, all real. 8 duplicates were merged into their keepers, carrying over their distinct parts
(FR-P-028 absorbs the unload-before-Preview finding; FR-P-052 the five meanings of 'Classic'; FR-P-020 the MCP token hand-over;
FR-M-018 the two knowledge tool families; FR-M-007 two MCP findings; FR-P-064 the cloud-grant finding; FR-C-015 the doc-number
finding). 32 removals were corrected. Three removals were unsound as first written: the staging-path fix shortened a root that does
not appear in the truncated path (FR-P-011; the lever is the engine's temp directory), and two weakened an invariant: dropping a
licence warning at export (FR-P-047) and cutting the product invariants in `AGENTS.md` to one-line pointers (FR-C-010). Evidence was
corrected where the verifier found an error (for example 17 unused letters, not 19, in FR-M-025). Overlapping rows the verifier did
not judge duplicates are kept and cross-referenced ("Resolve together with ...").

**Classification.** Severity 1–3 and a frequency class (`constant` 4, `session` 3, `workflow` 2, `once` 1) per row, defined in
`docs/friction/README.md` §5. Priority is severity × frequency score; ties are broken by severity, then by lower effort, then by
more audiences.

| Breakdown | Counts |
| --- | --- |
| Primary audience | people 81 · models 27 · contributors 30 |
| Audiences affected (a row can name several) | people 104 · models 46 · contributors 44 |
| Severity | 3: 13 · 2: 107 · 1: 18 |
| Frequency class | constant 32 · session 26 · workflow 53 · once 27 |
| Priority score | 12: 6 · 9: 3 · 8: 23 · 6: 19 · 4: 49 · 3: 8 · 2: 26 · 1: 4 |

**Limits.** This is a design-only audit: no user was observed, nothing was timed, and frequencies are judgements from the designs.
§5 lists what it could not assess.

## 2. The top 20 by severity × frequency

Ranked by score, then severity, then lower effort, then more audiences. The removal is summarised; the register row has the full
text, evidence and what stays intact.

1. **FR-P-042 (12): A pending Wilco proposal either blocks all further editing or is thrown away by the next edit.** Removal:
   proposals stay pending while the user edits, and read-set freshness re-verifies them when accepted (DG011 option C). Only save,
   export and Preview need a choice, defaulting to "continue without it, keep it pending"; the saved bytes stay pre-proposal. A
   proposal whose reads changed gets a Stale badge and "re-plan" instead of vanishing.
2. **FR-P-060 (12): The plan card gates every writing run, even a one-step, free, undoable edit.** Removal: under Confirm, a run whose
   effects are all undoable creates or sets, touching no human-owned or pinned field, with no egress, Preview, delete, move, ask or
   approve step, within its caps, within the size threshold and not started by an external agent, runs at once and leaves a receipt
   with Undo. Every other run keeps the card. The rule is one row set of the wait-policy table (FR-C-008). Needs the owner (66-Q2).
3. **FR-C-012 (12): Public-hygiene checks are manual searches on every commit, and the planned CI grep for private names cannot be
   committed.** Removal: a committed generic check (local paths, the user name read at run time, e-mail addresses, key-like strings)
   in the repository check script and an optional pre-commit hook; private names come from a git-ignored local pattern file plus a
   CI secret, never from the tree (66-Q16).
4. **FR-M-008 (12): A busy free host gets retried on the same endpoint, then raises a stall card on every decision.** Removal: one
   `LimitOutcome` taxonomy; an upstream 429 cools the host and reroutes along a user-authored route list, with every switch recorded
   in the run panel and the inspector; only account-scoped 429s follow Retry-After; at most 2 retries per endpoint; the stall card
   appears only when the list is exhausted. Needs the owner's reading of D023 decision 3 (66-Q4; since answered by D050 item 3).
5. **FR-P-008 (12): Preview launch has no designed progress, timeout or failure states.** Removal: a typed status strip driven by
   the harness's jsonl events (Staging, Starting game, Loading mission, Running, Ended), a boot budget measured in SP-07 that turns
   "nothing happened" into a named state with Stop, minimising the editor only once the mission runs, and one sentence plus one next
   action per outcome, each state tested against the fake game binary.
6. **FR-P-064 (12): A user's own strong cloud key gets the weakest-model treatment until it is qualified.** Removal: the project
   qualifies pinned paid cloud setups before each release and ships dated grants, voided by a served-model mismatch or a DG012
   trigger; the connect flow says what an unqualified setup can and cannot do; a staged, priced check grants lower levels first; and
   pre-fill confirmations are batched into one review card per run. Shapes are still granted only by qualification (66-Q5).
7. **FR-C-011 (9): `docs/README.md` is too big for one tool read and hides its rows from search.** Removal: move the §5 research
   table to `docs/research/README.md` (as its own §8 foresees), cap rows at one sentence, give index files a byte budget checked by
   the check script, and keep a one-screen "Start here".
8. **FR-P-001 (9): No designed first-run flow or start screen before the first public release.** Removal: adopt doc 34 le25 as M3
   work: one install summary with the defaults already chosen, a start screen whose primary action opens a ready-to-Preview sample
   mission, and le02's question optional on the single welcome card; measure launch to first Preview.
9. **FR-C-010 (9): `AGENTS.md` loads over 700 lines into every session (712 when swept, 816 later the same day), mostly prose
   rules for code that does not exist yet.** Removal:
   move mechanically checkable rules into lints and checks; move the Rust coding rules into a topic file loaded near code; keep the
   product invariants, hygiene and naming in full in the always-loaded core; give every rule a scope. Needs the owner (66-Q13).
10. **FR-M-004 (8): Edit tool names follow four different conventions.** Removal: tool names exist only as generated `CommandSpec`
    ids under one grammar; a registry test rejects ids outside it and near-duplicate verbs for one effect.
11. **FR-M-013 (8): Every Pick and Fill must start with a 'why' field that was never measured.** Removal: no 'why' by default; it
    becomes a preset knob per model and `DecisionKind`, switched on only where a measurement shows a gain; the inspector's 'why' is
    built by code from the recorded sub-answers.
12. **FR-M-016 (8): Cards that depend on the decision sit in the frozen cache prefix.** Removal: two card slots with type-level
    volatility tiers; decision cards go in the tail after the digest; the renderer refuses a misplaced card and a golden prefix test
    covers it.
13. **FR-M-018 (8): The same tools go by different names across prompts, digests and error text.** Removal: decide DG032, generate
    every model-facing name from the one registry, gate unknown names in CI before any wording is measured, and test that no two
    tools in one step share a job.
14. **FR-M-019 (8): Letter-coded Fill fields share one alphabet, so a letter meant for another field passes silently.** Removal:
    disjoint label sets per field in one request, so a wrong-list answer fails membership as its own finding; write it into DG024
    before DG024 is decided.
15. **FR-P-009 (8): Pressing Preview while a Preview is running is undefined.** Removal: the button becomes "Restart Preview": one
    click stops the game, restages the current snapshot and relaunches; two games never run at once.
16. **FR-P-013 (8): Every 1.99 Preview costs 5–7 manual clicks in the game.** Removal: launch straight into the mission if SP-08
    shows 1.99 accepts it; otherwise launch with the player profile, put the mission name on the clipboard and show the remaining
    clicks as a checklist; one overwritten export folder with a warning on in-game saves.
17. **FR-P-033 (8): A plan-card click before runs that cost nothing or almost nothing.** Removal: below a visible, editable threshold,
    the estimate shows on the turn card and the run starts on the user's gesture; never for external-agent runs, egress or Preview.
    Resolve with FR-P-060.
18. **FR-P-067 (8): The fixed 10-second stall card would fire on nearly every call of slow local setups.** Removal: the threshold
    comes from the setup's measured p90 latency, bounded by the step's latency class; below it a progress bar with an estimate;
    cards only for real anomalies, with "apply to the rest of this run". D050 item 1 has since fixed the 10-second card for
    limit-induced waits on cloud setups, so this applies to slow local setups and needs an owner note on D050.
19. **FR-M-017 (8): The primer tells every model to call lookup tools that most steps do not offer.** Removal: render the primer's
    "How to work" section per surface level and client from the actual callable set, and fail CI on out-of-step tool names.
20. **FR-C-024 (8): No defined way for agent-prepared commits to get a human sign-off and signature.** Removal: agents commit on a
    branch with neither; the human finishes with one documented command; the project states whether signatures are required; the
    DCO check's failure prints the fix (66-Q15).

**Just below the cut (also score 8):** FR-M-010 (faceted Picks), FR-P-028 (local model load waits and the unload before Preview),
FR-M-007 (external agents start runs blind), FR-M-009 (intake before any work), FR-M-015 (capsules too large for token-capped
tiers), FR-M-020 (verbatim quotes), FR-M-021 (manifests from doc comments), FR-M-022 (re-read prompts on local caches), FR-M-023
(escapes), FR-P-043 (script fields checked only at OK), FR-M-006 (128-bit ids in model text), FR-P-061 (a dense plan card).

**Severity 3 but rare, so ranked low.** These happen once per setup or per measurement round, yet decide whether people keep AI on
or whether results can be reproduced: FR-P-021 (no recommended local model may exist at v1), FR-P-022 and FR-P-065 (every role is
unassigned after connecting, and unbound roles silently fall back to templates), FR-C-013 (measurement tooling lives in scratch
copies). Treat them with the top 20.

**Clusters to resolve together.** Many rows share one fix; resolving the cluster at once avoids three partial designs.

| Cluster | Rows | Shared fix |
| --- | --- | --- |
| What waits for a click | FR-C-008 (umbrella), FR-P-060, FR-P-033, FR-P-062, FR-P-063, FR-P-061, FR-P-068, FR-P-074 | One wait-policy table and one exhaustive function |
| Names | FR-C-009 (precondition), FR-P-005, FR-P-035, FR-P-052, FR-P-075, FR-P-076, FR-P-077, FR-P-078, FR-P-016 | The names table now, one meaning per word, "Name · descriptor" |
| Model-facing tool names | FR-M-018, FR-M-004, FR-M-017, FR-M-021, FR-M-027 | DG032 plus names generated from the one registry |
| Qualification and grants | FR-P-021, FR-P-064, FR-P-023, FR-P-027, FR-P-026, FR-P-080, FR-P-040 | Who issues grants, which evidence, keyed per `DecisionKind` |
| Connect and bind | FR-P-022, FR-P-065, FR-P-024, FR-P-025, FR-P-029, FR-P-030 | One connect flow that measures, proposes a binding and ends in a first result |
| Free cloud, routing and stalls | FR-M-008, FR-P-032, FR-P-067, FR-P-031, FR-P-066, FR-P-038, FR-M-003 | Route lists built by code, visible switches, measured thresholds |
| External agents (MCP) | FR-P-020, FR-P-081, FR-M-002, FR-M-007, FR-M-027, FR-M-001 | Stable keychain token, typed waiting states, one batch proposal |
| The Preview loop | FR-P-008, FR-P-009, FR-P-007, FR-P-013, FR-P-010, FR-P-011, FR-P-028, FR-C-001 | Typed Preview states, restart, probe-by-Preview, recorded traces |
| Capsule cost | FR-M-013, FR-M-015, FR-M-016, FR-M-022, FR-M-024, FR-M-025, FR-M-026, FR-M-019 | Per-model preset knobs measured before adoption, typed prefix tiers |
| Repository tooling | FR-C-014 (umbrella), FR-C-012, FR-C-015, FR-C-018, FR-C-019, FR-C-022, FR-C-011, FR-C-017 | One standard-library check script that runs every check that exists |

## 3. Quick wins

Small removals (effort S or S-M, or S for the design part) with a high score, or cheap preconditions for several other rows. Rows marked
"owner" need the owner question named.

| # | Rows | Score | Why it pays | First step |
| --- | --- | --- | --- | --- |
| 1 | FR-C-008 | 4 | Umbrella for every wait rule; turns seven disagreeing texts into one tested table | Write the wait kind × autonomy × origin table in agent-runtime §11 |
| 2 | FR-P-060, FR-P-033 | 12, 8 | Removes a click from most small AI edits | Add the receipt predicate as rows of that table (owner: 66-Q2) |
| 3 | FR-C-011 | 9 | Every coding session starts at this index | Move docs/README §5 into docs/research/README.md |
| 4 | FR-C-012 | 12 | A public leak cannot be taken back | Commit the generic hygiene check; file the DG for private names (66-Q16) |
| 5 | FR-C-014 | 6 | Home for hygiene, drift, tag, size and line-ending checks | Add `python tools/check.py` running what exists today |
| 6 | FR-C-009 | 4 | Precondition for six naming rows | Create the names table as data now, not at M4 (66-Q10) |
| 7 | FR-M-018, FR-M-004, FR-M-017 | 8 | Removes unknown-tool refusals and wasted turns | Decide DG032; render the primer per surface level |
| 8 | FR-M-013 | 8 | Up to about 40 decode tokens per call, times K | Make 'why' a preset knob, off by default |
| 9 | FR-M-016 | 8 | Restores cache hits on every carded capsule | Split stage and decision card slots with typed tiers |
| 10 | FR-M-019, FR-M-025 | 8, 4 | Closes a silent wrong-value path; removes 17 never-valid letters | Disjoint labels per field; generate the Pick enum from MENU_MAX |
| 11 | FR-P-009 | 8 | Many round trips to the game per session | Specify "Restart Preview" in game-integration §7 |
| 12 | FR-P-013 | 8 | Every Preview for 1.99 authors | Put the positional-launch question first in SP-08 |
| 13 | FR-P-067 | 8 | Stops a card from becoming the normal state | Threshold from measured p90 per step kind on local setups (D050 keeps 10 s for cloud limit waits) |
| 14 | FR-C-024 | 8 | Agent sessions stall on key prompts | Write the commit flow into a first CONTRIBUTING.md (66-Q15) |
| 15 | FR-P-022, FR-P-065 | 3 (severity 3) | Blocks the first AI run after connecting | Proposed complete binding on the connect-success card |
| 16 | FR-P-006 | 4 | The first mission must appear in the game | Default save location per profile with a writability check |
| 17 | FR-C-022 | 4 | Cheap before the first byte-exact fixture, expensive after | Add .gitattributes and .editorconfig |
| 18 | FR-C-026, FR-C-002 | 2 | One-line fixes a newcomer or agent meets first | Point the README docs link at docs/README.md; rename DG001's file |

## 4. Frictions that need an owner decision

Proposed owner questions, **not filed**. Each names the decision record it would change, the rows it resolves and the proposed
answer. Filing them goes through the normal lifecycle in `docs/decisions/`.

- **66-Q1 (D003).** Should a new mission's target profile be preselected from the installs found and the user's last choice,
  instead of always Cwr, and which profile does an OFP 1.96 user land in? Rows: FR-P-004, FR-P-005, FR-P-050. Proposed: yes, shown
  as a chip on the New Mission card, stored per mission, capabilities still per mission; 1.96 lands in the closest profile, badged
  "unverified on 1.96"; doc 19 then folds to the amended D003.
- **66-Q2 (D024 item 2).** Under Confirm, may a small run skip the plan card and leave a receipt (conditions as in FR-P-060), and
  does an approved plan pre-authorise create and set batches inside its stated scope whatever their size? Rows: FR-P-060, FR-P-033,
  FR-P-062, FR-C-008. Proposed: yes to both, as rows of one wait-policy table; safety waits unchanged.
- **66-Q3 (D024, DG023, roadmap M4).** Remove the user-facing chat-mode selector (Dispatch picks the mode's tool set), and offer
  "Auto for this project" as an explicit, badged setting? Rows: FR-P-063. Proposed: yes; Auto's exclusions stay.
- **66-Q4 (D023 decision 3, RG1).** May a user-authored, visible route list, or a "for this session" choice on a stall card,
  reroute calls without a click per switch, provided every switch is journaled and shown? Rows: FR-M-008, FR-P-032, FR-P-067,
  FR-P-066. Proposed: yes; file RG1 and RG2 as DGs. **Answered after this audit:** D050 item 3 (accepted 2026-09-28 under the
  owner's go-ahead) adopts user-authored route lists that move a call on a limit outcome without a click per move, each move
  recorded and shown; RG2 goes to DG016. The "for this session" stall-card choice is not decided there.
- **66-Q5 (D037, D045).** What makes a model recommendable at v1, and who issues grants? (a) Product qualification on reference
  hardware classes as a v1.0 release gate, or a DG now; (b) project-run qualification of pinned paid cloud setups shipped as dated
  grants; (c) show the free-cloud option only when a qualified free preset exists, reconciling D045 item 4 with doc 52; (d) a
  "requalifying" state for bring-your-own endpoints serving a manifest file. Rows: FR-P-021, FR-P-064, FR-P-023, FR-P-027.
  **Partly overtaken after this audit:** D050 reads free cloud as custom and unqualified until qualification runs and makes the
  free flow lead to two providers plus a local model (item 2), so (c) as proposed would now change D050; D051 keys grants per
  freedom level but does not say who issues grants for cloud setups, so (a), (b) and (d) stay open.
- **66-Q6 (D008).** Source kinds and the enabling gesture: (a) an opt-in "Check for Plotroom updates" source; (b) a user-enabled
  "Plotroom model data" update source; (c) one click on a card that names its origins enables exactly those sources for those
  pinned files; (d) a user-enabled source for pinned, hash-checked CE builds (a DG, given executable downloads). Rows: FR-P-018,
  FR-P-023, FR-P-025, FR-P-012.
- **66-Q7 (D026).** Conservative, dated default session and monthly caps for keys that can spend money, editable in place? Rows:
  FR-P-034.
- **66-Q8 (D047).** Extend D047's content-policy flags from Plotroom's own evaluations to product routing, so combat-flavoured steps
  avoid hosts whose policy refuses them before any call? Rows: FR-P-036.
- **66-Q9 (D022 amendment).** Reword "pins every sampler value" to "pins every accepted key", with a strict profile for unknown
  endpoints, omitted keys recorded as "server default, unknown", and a user-started connect canary? Rows: FR-M-014.
- **66-Q10 (D002, D028, D034).** Naming: (a) reword D028's "F1 pages" to "the help action"; (b) create the names table now rather
  than at M4; (c) rename one of the two user-facing "Ask"s and settle the other collisions in one pass; (d) show "Teller · script
  check" rather than replacing Teller; (e) add a "Working with Wilco" Drill lesson on the $0 path. Rows: FR-P-016, FR-C-009,
  FR-P-035, FR-P-076, FR-P-077, FR-P-079.
- **66-Q11 (D036 item 5).** Move the camera tools that need neither the timeline nor the harness (clipboard capture, map reading of
  camera scripts, camera lints, a safe-epilogue fix) into v1? Rows: FR-P-056.
- **66-Q12 (D046, DG039).** Pre-fill each key's host allow-list from the presets the user accepted, and re-probe on triggers instead
  of a timer? Rows: FR-P-039, FR-M-003.
- **66-Q13 (AGENTS.md; docs/README §3.3).** Restructure `AGENTS.md` into an always-loaded core (invariants in full, hygiene, naming,
  intake, what to run) plus topic files loaded near code; replace mechanical prose rules with lints; set budgets per file kind; drop
  change logs from index files; one intake table. Rows: FR-C-010, FR-C-019, FR-C-017, FR-C-027, FR-C-011.
- **66-Q14 (decision lifecycle).** Make record headers the single source (Refines, Answers, Decides, Affects) with generated
  backlinks and status banners, and stop folding pointers into research docs? Rows: FR-C-016, FR-C-015.
- **66-Q15 (D032).** Adopt the agent commit flow (no sign-off or signature from agents; the human finishes with one command), and
  state whether signed commits are required? Rows: FR-C-024.
- **66-Q16 (testing-strategy §14).** Check private names with a git-ignored local pattern file plus a CI secret, instead of a
  committed list? Rows: FR-C-012.
- **66-Q17 (design-gap process).** Adopt each open technical DG's recommended resolution by default at a set date unless someone
  records an objection, DG005 first? Rows: FR-C-005.
- **66-Q18 (D049 open part).** Accept the register format in `docs/friction/README.md` (13 columns, the severity and frequency scales,
  the lifecycle and the per-change check) and these first contents? Rows: all.

## 5. What the audit could not assess before code exists

- **Real counts.** Steps, clicks and confirmations are counted from the designs. The flows they describe do not exist yet, so the
  budgets in `docs/friction/README.md` §10 have no baseline.
- **Real waits.** Game boot time (SP-07), model load, swap and reload times on hardware other than the reference card (SP-13), the
  effect of a kernel cache, and how long the connect and download flows take on real networks are unmeasured [U].
- **Real model behaviour.** Error, repair and escape rates, and token counts, of real capsules on qualified setups; several removals
  (FR-M-013, FR-M-022, FR-M-023, FR-M-026) are marked "measure before adopting" for this reason.
- **Comprehension.** Whether names, badges, receipts and status lines are understood needs sessions with newcomers and community
  authors; no designs were tested with people.
- **Interactions.** Removals that touch the same rule (receipts, the size threshold, Auto, check-ins) can combine in unplanned ways;
  the wait-policy table (FR-C-008) should be model-checked over every cell once it exists.
- **Frequencies.** The classes are judgements. No usage data exists, and none will be collected remotely (D008); frequency will come
  from tests, local statistics the user can open, and voluntary alpha reports.
- **Install diversity.** Retail 1.99, OFP 1.96, the demo, Linux and macOS setups were assessed from docs only.
- **Areas not swept.** Export and publishing (packing, sharing, the export scan as a whole), plugin installation and permissions,
  localisation and stringtables, multiplayer Preview and slots, accessibility (keyboard-only use, screen readers, colour), performance
  on large missions and low-end machines, the campaign play-testing loop, and audio and music authoring. Each needs its own sweep.
- **The register's own shape.** Rows are long (up to about 3,700 characters), so search tools can hide them and plain reads can cut
  them; `docs/friction/README.md` §4 explains how to read one row. If the register grows past a few hundred rows, split it per
  audience.

## Sources

All read in this repository on 2026-09-28. Every register row cites its own sections.

**Rules and entry files.** `AGENTS.md` (Friction Review, Design Authority, Naming and Trademarks, Public Repository Hygiene, Coding
Session Discipline, Local Repo-Specific Rules); `CLAUDE.md`; `README.md`; `CODE-INDEX.md`; `docs/README.md`.

**Decisions.** `docs/decisions/` D002, D003, D004, D008, D009, D010, D011, D015, D018, D019, D021, D022, D023, D024, D025, D026,
D028, D029, D030, D031, D032, D034, D036, D037, D038, D043, D044, D045, D046, D047, D048, D049; `README.md` (lifecycle);
`OWNER-QUESTIONS.md` (OWQ-05, OWQ-08, OWQ-27).

**Design-gap requests.** `docs/design-gap-requests/` README (index, lifecycle, candidates); DG001 (`DG-preview-non-aborting-launch.md`),
DG003, DG004, DG005, DG006, DG007, DG008, DG009, DG010, DG011, DG012, DG015, DG016, DG019, DG021, DG023, DG024, DG025, DG032, DG035,
DG037, DG039.

**Architecture.** `docs/architecture/` README, `agent-runtime.md`, `commands-undo-history.md`, `core-document-model.md`,
`crate-map.md`, `extensibility.md`, `game-integration.md`, `testing-strategy.md`, `ui-shell.md`, `validation-and-lints.md`.

**Roadmap.** `docs/roadmap.md`; `docs/roadmap/m0-m3-foundations-to-preview.md`, `m4-v1-power-campaigns-wilco.md`,
`integration-owners.md`, `spikes-and-probes.md`.

**Engine requests.** `docs/upstream/README.md`, `engine-requests.md` and `engine-requests.csv` (ER-001, ER-003, ER-004, ER-005,
ER-006).

**Research docs.** `docs/research/` 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 15, 16, 19, 20, 21, 23, 24, 25, 27, 30, 31,
32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65.

**Skills and tools.** `skills/mission-primer/SKILL.md`; `skills/standing-orders/` (SKILL.md and its 32 reference entries);
`tools/local-qual/` (README.md, run.py, score.py); `tools/quota-sim/` (README.md, test_quota_sim.py).

## Verification notes

### 2026-09-28, review of this doc, `docs/friction/README.md` and `register.csv`

**What was checked, and how.**

- **The CSV.** Parsed with Python's `csv` module: 138 data rows, 13 fields each, UTF-8 without a BOM, LF only, no line break inside
  a field, and re-writing it with the `csv` writer gives identical bytes. Ids are unique and contiguous (FR-P-001 to FR-P-081,
  FR-M-001 to FR-M-027, FR-C-001 to FR-C-030); each prefix matches the row's first audience; every column follows
  `docs/friction/README.md` §4. Every FR id in the register, this doc and the README exists, except the README's example header
  line, now a placeholder.
- **The counts.** The TL;DR and §1 tables were recomputed from the CSV and match (81/27/30 primary; 104/46/44 affected; severity
  13/107/18; frequency classes; every priority bucket; 23/24/25/23/22/21 rows per sweep). The top 20, the twelve rows just below
  the cut and the four rare severity-3 rows follow from the stated ranking. Every score in §3 matches its rows. The eight merges
  are noted in the seven keeper rows.
- **The evidence.** A script resolved every `Dnnn`, `DGnnn`, `ER-`, `SP-`, `OWQ-`, doc number, decision item number, `le`/`I34-`/
  `RG`/`UX`/`DS`/`DP-` token and `§` section cited in the evidence, description, removal and change columns against the tree.
  All resolve apart from one pointer that the cited files themselves get wrong (below). 204 quoted phrases in the evidence column
  were searched in the repository's text; all are there, 5 with small differences in formatting only. The walkthroughs of
  FR-P-042 and FR-P-060 were re-read against their sections. The measured figures of FR-C-010, -011, -014, -015, -017, -019,
  -022, -025 and -026 were re-measured.
- **The removals.** All 138 were read against the invariants. None widens the agent's scope (FR-M-001's query reduces paths to
  kinds; FR-P-081 and FR-P-020 write no other program's files), bypasses typed undoable commands or `UserIntent` (FR-P-033,
  FR-P-060, FR-P-062 and FR-P-074 keep the click or its equivalent and leave safety waits unchanged), weakens a validator or gate
  (FR-P-043, FR-P-046 and FR-P-048 re-check or announce), or hides an AI-made element (FR-P-061, FR-P-070 and FR-P-075 layer
  detail without removing it). The removals that would change a record say "needs the owner".
- **Hygiene.** The three files were scanned for drive-letter and home-directory paths, user and e-mail names, key-like strings
  and, from a git-ignored local pattern list, private project names. No hits other than the product's own terms.
- **Links.** The README's three relative links resolve. This doc has no Markdown links, and every path it names exists except
  those it proposes to create (`docs/research/README.md`, `tools/check.py`). The README's two row-reading commands (PowerShell
  `Import-Csv`, Python `csv`) were run and work as written.

**Fixed in place.**

- **Stale figures from same-day edits** in other files, now given as "when swept" and "on re-check": FR-C-010 (`AGENTS.md` went
  from 712 lines and 40,105 bytes to 816 lines and 46,758 bytes and now carries doc 62 §8's proposed text; the always-loaded
  core is about 150 lines; the Rust rules are lines 248–782), FR-C-011 (`docs/README.md` 507 lines, 66,141 bytes), FR-C-015
  (29 owner questions, D051, the new status-line wording, the decision index since reordered) and FR-C-019 (54 of 64 docs over
  600 lines, 8 over 1,000). This doc's TL;DR and top-20 item 9 now say "over 700 lines".
- **Wrong or loose evidence:** FR-C-015's blank lines end the §5.6 table for every row from doc 50 on, not only rows 50–53;
  FR-C-007's quote comes from core-document-model §9, not doc 35, and names a doc 39 §9.4 that does not exist; FR-C-010's
  `AGENTS.md` quote is now verbatim ("security/vulnerability tests"); FR-C-016 quotes the real header-pointer pattern; FR-P-003
  marks its elided quote.
- **Decisions recorded after the sweep.** D050 and D051 were accepted on 2026-09-28 under the owner's go-ahead. D050 answers
  66-Q4 and overlaps FR-M-008, FR-P-023, FR-P-031, FR-P-032, FR-P-066, FR-P-067, FR-C-003 and FR-C-020; those rows now name it,
  and §4 notes it under 66-Q4 and 66-Q5. D050 item 1 keeps a fixed 10-second card for limit-induced waits on cloud setups, so
  FR-P-067's measured threshold now applies to slow local setups only and needs an owner note. D051 changes no row's facts.
  Statuses stay `open`: a decision is not a change set, milestone or DG that owns a removal (README §8).
- **Consistency:** §1's tie-break now includes severity, as the README and §2 state; §3's lead-in admits effort S-M; bare
  freedom-level codes next to register ids in FR-P-064, FR-M-009 and FR-P-080 now read "freedom level FR2" (README §3); ten
  one-way "Resolve together" links were made mutual; the README's example header line, which used an id no row has, now uses
  `FR-P-nnn`; the
  README's no-telemetry sentence cites D008 item 1; the longest row is now about 3,700 characters (README §4, §5 here).

**Found outside these files, not fixed here.** Core-document-model §9 (Cinematics row) and roadmap integration-owners (I35-CUT)
cite "doc 39 §9.4", which does not exist; doc 39's reconciliation with doc 35 is §9.3. Doc 62 §8's heading still reads "awaiting
owner approval" while the working-tree `AGENTS.md` already carries its text. Several rows quote file sizes and counts that
parallel sessions change within hours; such figures are dated evidence, and FR-C-015's generated indexes would retire most of
them.
