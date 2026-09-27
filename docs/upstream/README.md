# Engine requests (`docs/upstream/`)

> This folder holds Plotroom's **engine-requests register**: every limitation and defect of the game engine that the
> research found, what Plotroom does about it today, and the engine change that would remove it. Created 2026-09-27.
> The lifecycle, the capability model and the filing rules below are **proposals** until the owner confirms them (see
> "Open decisions").

## What an engine request is

Plotroom does the maximum the shipped engine allows and never makes a core feature depend on an engine change
(`AGENTS.md`, "Maximum Within the Engine; Gaps Become Engine Requests"). Every limitation found on the way is recorded
here with the limitation itself, what Plotroom does today, the proposed engine change with its hook points in the engine
source, the benefit and a status.

- **Engine requests are about the game.** Gaps in Plotroom's own design are design-gap requests
  ([`docs/design-gap-requests/`](../design-gap-requests/README.md)). A design-gap request may point here, as DG034 does
  for the camera and effects defects that doc 32 had routed to the wrong register.
- **The community engine project is CWR-CE** (`ofpisnotdead-com/CWR-CE`), the continuation of the released Remastered
  source. Bohemia's own repository accepts no pull requests; CE's `port` label is the documented path by which a
  community change reaches an official release (doc 01 TL;DR and §9; doc 08 TL;DR).
- **The legacy 1.99 executable is frozen.** No request targets it; the `Cwa199` profile keeps every workaround forever.
- **Nothing here is promised.** An entry records what Plotroom would ask for and why. Whether and how the maintainers
  take it up is theirs to decide.

## Files

| File | Role |
| --- | --- |
| `README.md` | This file: what the register is, the lifecycle, the capability model and how to file |
| [`engine-requests.md`](engine-requests.md) | The readable register: how to read an entry, a summary, a filing plan (proposal), one table per area, a cross-reference from the source docs' own numbering (E1–E14, P1–P9, F1–F10, DG034 items) and verification notes |
| [`engine-requests.csv`](engine-requests.csv) | The canonical data, one row per entry. The tables in `engine-requests.md` are rendered from it; a change edits both in the same change set |

## Columns

| Column | Meaning | Rules |
| --- | --- | --- |
| `id` | `ER-###` | Three digits, assigned in filing order by this register. Never reused and never renumbered; a withdrawn or superseded entry keeps its row |
| `title` | A short name for the limitation | Names the problem, not the fix |
| `area` | `launch`, `harness`, `security`, `campaign`, `scripting`, `camera`, `atmosphere`, `random-mp`, `mission-format`, `mods` or `ai` | One per entry; a new area needs an edit of this list |
| `limitation` | What the engine does | Carries the source doc's evidence tags: **[V]** read in the pinned source, **[I]** inferred, **[U]** unverified |
| `current_workaround` | What Plotroom does today | Must hold on every target profile, because no core feature may wait for an entry |
| `proposed_feature` | The engine change | Starts with a kind tag (next section). A design that no source doc proposes is marked as this register's proposal [I] |
| `hook_points` | Where the change goes in the engine source | Pinned file and line ranges with the aliases below, as the source docs cite them; re-read before filing |
| `benefit` | What users gain | Stated from the user's side |
| `priority` | `P1`, `P2`, `P3` or `n/a`, with the score, for example `P1 (B3×F2)` | See "Priority" |
| `profiles_affected` | Which target profiles can gain the change, and its content impact | See "From a shipped change to a target-profile capability" |
| `source_docs` | Research doc numbers and sections, design-gap ids, integration items | At least one source per entry |
| `status` | Lifecycle state, with a note in parentheses | See "Lifecycle" |

**Citation aliases.** `P:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`; `EVAL:` = the same commit's
`engine/Evaluator/`; `RND:` = its `engine/Random/`; `R:` = its repository root; `CE:` =
`ofpisnotdead-com/CWR-CE@b67bf3bd62:` (repository root). Line numbers are CWR's unless a `CE:` path is given; they hold
for CE wherever the source doc compared the files.

## Kinds

| Tag | What the change is | Content impact | How Plotroom adopts it once shipped |
| --- | --- | --- | --- |
| `[fix]` | A defect or behaviour fix with no new syntax | None: existing content simply works better | Plotroom keeps its workaround while any build a profile targets lacks the fix; a lint may soften only for profiles whose minimum build has it |
| `[key]` | An opt-in key or class in `description.ext`, `mission.sqm` or the campaign description that older builds ignore | Degrades gracefully: the fallback is emitted beside the key | A capability of the target profile; the mission shows "enhanced on …" rather than "requires …" |
| `[command]` | A new script command | Hard: content that uses it fails on builds without it | A capability that raises the computed "Requires" badge; never used in `Cwa199` or `Cwr` output, and never by editor-generated glue unless the user opted in |
| `[launch]` | A command-line or tooling option | None | Used by Preview when the capability probe finds it |
| `[harness]` | A Preview-harness protocol change | None | Used by Preview when the harness's `describe` reply lists it |
| `[none]` | Recorded only | — | — |

## Priority

- **Benefit B.** 3: removes a crash, a security hole, or a trap that silently breaks shipped content or the Preview loop
  for many users. 2: clearly improves a feature many users see, or removes a common trap. 1: polish, a niche need, or a
  capability that only content aimed at the community-engine profile can use. New commands and keys count at most B2
  unless they fix a defect.
- **Feasibility F.** 3: a small, local change at one or two hook sites with an obvious test. 2: several sites, or a
  design discussion with the maintainers first. 1: large or risky, or it touches the save or network format.
- **Priority = B × F.** P1 for 6 or 9, P2 for 3 or 4, P3 for 1 or 2; `n/a` for entries Plotroom will not file. The
  score is Plotroom's view of user value; the maintainers weigh their own costs.
- A note in `status` can hold an entry back regardless of priority, for example "(probe first)" when the evidence is
  [I] or [U].

## Lifecycle

| Status | Meaning | Who moves it there | What is recorded |
| --- | --- | --- | --- |
| `not filed` | Recorded here; nobody has asked the maintainers | A register change | The entry, with preconditions in the note: "(private report first)", "(probe first)", "(confirm at runtime first)" |
| `proposed` | Before the community engine project as an issue, discussion or pull request, whether Plotroom opened it or joined one that others opened | The owner, or someone the owner names (see "Filing") | Link, date, the CE commit whose lines were re-read; "opened by others" when Plotroom joined an existing issue |
| `accepted` | The maintainers agreed to the change, or merged a pull request not yet in a build | Evidence from the upstream thread | Link to the decision or merge |
| `shipped` | In a community-engine build, and later perhaps in an official release | Evidence: a commit and a build | `shipped (Ce @<commit>)`, later `; Cwr <version>` when an official release carries it |
| `declined` | The maintainers said no | Evidence from the upstream thread | Their reason; Plotroom's workaround becomes permanent |
| `won't file` | Plotroom decided not to ask | A register change with the reason | The reason in the note |
| `superseded by ER-###` or `withdrawn` | Replaced by another entry, or the limitation turned out not to exist | A register change | Pointer or reason |

- The normal path is `not filed` → `proposed` → `accepted` → `shipped`. An entry may go straight from `proposed` to
  `shipped` when a pull request is merged into a build at once.
- **Already asked by others.** When the same ask already exists upstream as someone else's issue, the entry is recorded as
  `proposed (CE #…, opened by others)` from the start, as nine entries are today. That status records the upstream issue only:
  Plotroom has not joined it, and adding Plotroom's evidence there is outreach in the order the owner set (OWQ-11 (a); D035 item 3),
  not yet started. When that
  happens (Filing, step 3), the note gains "Plotroom evidence added" and the date.
- A grouped entry (for example ER-060, several missing commands) is split into new ids when filed; the grouped row
  becomes `superseded by …`.
- Every status change edits the CSV row and the rendered table row in one change set, and adds a dated line to the
  verification notes of `engine-requests.md`.
- **Adding entries.** Any doc that finds an engine limitation adds a row here in the same change set (next free id,
  status `not filed`), and cites the ER id where it describes its workaround.

## From a shipped change to a target-profile capability

Target profiles are per mission: `Cwa199` (the 1.99 executable), `Cwr` (the official Remastered releases, 3.05 as the
baseline) and `Ce` (community-engine builds). The editor computes a "Requires" badge from what a mission uses, and
editor-generated glue stays in the conservative subset (doc 24 §5.5; doc 23 §13.3; doc 29 §7). A shipped entry reaches
users as follows (proposal):

1. **Record it.** Set `shipped (Ce @<commit>)` and note the first community-engine build that carries it and the key,
   flag or command that turns it on.
2. **Name the capability after the entry.** The capability id is the entry id (`ER-027`), so the profile table, the
   lints and the register cannot drift apart.
3. **Attach it to profiles.** The `Ce` profile gains the capability from that build. If an official release ports the
   change, the `Cwr` profile gains it from that version. `Cwa199` never gains one.
4. **Detect it.** Preview's capability probe (doc 08 §6: help output, the harness's `describe`, or a probe mission from
   the in-game probe suite) confirms that the build the user points at has it. An unknown build counts as not having it.
5. **Make it opt-in and visible.** A capability that narrows which builds can play the content is never switched on
   silently, by a generator or by Wilco, at any autonomy setting: it is a visible per-mission or per-campaign setting
   beside the target profile, with a plain-language line saying who can then play the mission. Generators and Wilco may
   propose it.
6. **Keep the fallback.** Every capability keeps the lowering of the `current_workaround` column for the other profiles,
   and content compiled for `Cwa199` or `Cwr` never depends on a capability those profiles lack (doc 29 §7). Using one
   on a profile that lacks it is a lint error.
7. **Badge it by kind.** `[command]` capabilities raise the "Requires" badge; `[key]` capabilities with a fallback show
   as "enhanced on …"; `[fix]`, `[launch]` and `[harness]` entries never change the badge.
8. **Test it.** Compile tests with and without the capability, a `probe` row in `docs/porting/upstream-test-map.csv`
   for the runtime check, and ported upstream tests wherever Plotroom mirrors the new behaviour (`AGENTS.md`, "Porting
   Upstream Code and Tests").
9. **Retire nothing early.** A workaround for a `[fix]` stays while any build a profile targets lacks the fix.

## Filing with the community engine project

Filing is public outreach in the project's name, so nothing leaves `not filed` without the owner's approval (compare
DG029). The checklist for each entry:

1. **Security first, privately.** Entries whose status says "(private report first)" go to the community engine
   maintainers and to Bohemia Interactive through a private channel before any public issue, because downloaded missions
   can use them against players of the shipping game (doc 24 disclosure note; neither source repository has a
   `SECURITY.md`). The report carries no exploit strings, and the public issue waits until the maintainers agree. The
   owner sends the reports through a private channel of each project and records the dates in OWQ-09 (OWQ-09 (a); D035
   item 1; not yet sent).
2. **Re-verify.** Re-read every hook point at the current CE `main` commit and update the lines; run the probes the
   entry's note names. Record the commit in the status note.
3. **Search first.** If an issue or pull request already covers the entry, add Plotroom's evidence there instead of
   opening a duplicate, and set `proposed (CE #…, opened by others)`.
4. **Discuss before code.** Open an issue or discussion before any pull request, as CE's contribution guide asks
   (`CE:CONTRIBUTING.md#L74-L78`, doc 01 §7.3).
5. **One ask per issue.** Small, self-contained, vanilla behaviour kept when a new key is absent, no content dependence
   for fixes.
6. **Tests with the change.** A regression test and adversarial tests in CE's own style: Catch2 unit tests, Trident
   mission tests and source-scanning gate tests (doc 24 §6; doc 08 §4.3 item 6).
7. **Licence.** Contributions to CE are GPL-3.0-or-later with Bohemia's Section 7 additional terms, inbound equals
   outbound (`CE:CONTRIBUTING.md#L80-L87`; doc 02 §2.2). Plotroom only invokes the engine, so its own licence is
   unaffected (doc 08 §4.3).
8. **Authorship.** Follow CE's rules for AI-assisted contributions: a human author who is accountable, no AI
   boilerplate, no AI trailers or mentions in commit metadata, and no AI review bots run against their repository
   (`CE:CONTRIBUTING.md#L59-L72`; doc 02 §2.2; doc 09 §7).
9. **Names.** Refer to the game nominatively, claim no affiliation with Bohemia Interactive, and do not use the
   request to promote Plotroom (the Section 7 terms; `AGENTS.md`, "Naming and Trademarks").
10. **Target `main`,** and leave the `port` decision to the maintainers.
11. **Record it:** status, link, date and commit in the CSV and the rendered table, plus a verification note.

**Issue text** (a starting point, in the filer's own words):

```text
Title: <the limitation, in one line>
What happens: <the limitation, with file#lines at CE main <commit>>
Why it matters: <who hits it and what they lose>
Proposed change: <the change; vanilla behaviour kept when …>
Tests: <regression and adversarial tests>
Evidence: static reading at <commit>; runtime probe: <result, or "not yet run">
```

## Open decisions

- *Decided 2026-09-27:* **who files, where and when** (OWQ-11 (a); D035 item 3): the owner, or a maintainer the owner names,
  starts with CE #35 and a small tested PR, then opens one tracking discussion that links this register; security entries only
  after the private reports. The mod-channel maintainers follow the same outreach rule (OWQ-12 = DG029 option A; D035 items 4–5).
  Nothing has been filed yet, so every entry keeps its current status.
- *Decided 2026-09-27:* **the private-report channel and timing** for the security entries (OWQ-09 (a); D035 item 1): the owner
  reports now, privately to the CWR-CE maintainers and to Bohemia Interactive, and records the dates in OWQ-09; no new public detail
  until the reports are acknowledged. Reports sent: not yet.
- **DG034** (technical): this folder implements its option B; DG034 moves to decided once the doc 32 and doc 31
  pointers are added.
- **Capability wording** (technical, with doc 33's plain-language labels): "requires …" versus "enhanced on …", and
  where the capability toggle sits in the target-profile panel.

## Hygiene

This repository is public. Entries are written in this project's own words, cite public sources only, name no private
project, and add no exploit detail beyond what the research docs already state.

## Verification notes

### Owner answers (2026-09-27)

- "Open decisions", the lifecycle's "already asked by others" rule and filing step 1 now state the owner's answers to OWQ-09 and
  OWQ-11 (and OWQ-12 for the mod channels), as recorded in D035. No outreach has been made and no entry's status changed.
