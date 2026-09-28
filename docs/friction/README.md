# Friction register

> **Status:** register, started 2026-09-28 under D049. `register.csv` holds one row per known friction; this file holds the rules
> for adding, updating and closing rows and the friction check every change runs. The first contents come from the audit in
> [doc 66](../research/66-friction-audit.md). D049 leaves the register's format open; the format below is the working format until
> the owner confirms it (doc 66, 66-Q18).

## 1. Purpose

The owner's direction of 2026-09-28: "As we design and implement, we will have to actively notice and think about potential frictions
and how to reduce or eliminate them." [D049](../decisions/D049-friction-review.md) makes that a duty, and `AGENTS.md` ("Friction
Review (Required)") states it as a rule for every design and implementation change.

**Friction** is anything that makes a correct action slower, harder, more confusing or more error-prone than it needs to be: extra
steps or clicks, waits without feedback, confirmations that add no information, setup the product could do itself, unclear or
misleading errors, silent failures, surprising defaults, jargon, inputs that are easy to get wrong, and wasted tokens or calls for
models.

This folder exists so that friction found but not fixed is not lost. A row records who meets the friction, how bad and how often it
is, the evidence, and the proposed removal. Removing friction never weakens the product invariants in `AGENTS.md`: product scope,
typed undoable commands, validation and the glass box stay intact (D049 item 5).

| File | What it holds |
| --- | --- |
| `README.md` | These rules, the review checklist and the measurement plan |
| `register.csv` | The register: one row per friction, 13 columns (§4) |
| [`../research/66-friction-audit.md`](../research/66-friction-audit.md) | The first audit: method, top 20, quick wins, owner questions |

## 2. The three audiences

| Audience | Who | Typical signs of friction |
| --- | --- | --- |
| `people` | People using the editor: mission and campaign authors, newcomers, scripters, players testing | Extra clicks, modal questions, waits with no progress, jargon, silent failures, surprising defaults, setup the editor could do |
| `models` | Models using Plotroom's APIs and tools: Wilco's steps and external agents over MCP | Wasted calls and tokens, names that differ between prompt and manifest, inputs that are easy to get wrong (free text where a menu would do), errors that do not say how to recover, polling |
| `contributors` | People and coding agents building Plotroom: docs, tools, code, tests, review | Rules that must be remembered instead of checked, hand-maintained indexes, commands that do not run, files too large to read in one call, unclear intake |

A friction often touches several audiences. The **first** audience listed in a row is the primary one and decides the id prefix.

## 3. Ids

- `FR-P-nnn` for people, `FR-M-nnn` for models, `FR-C-nnn` for contributors, numbered in the order rows are added, three digits.
- An id is never renumbered or reused, even when a row is closed or merged.
- **Not the freedom levels.** Doc 63 names *freedom levels* FR0–FR8 (how large a step the harness gives a model). Those are `FR`
  followed directly by a digit. Register ids always have a hyphen, an audience letter and three digits. Always write the full id
  (`FR-P-012`, never `P-012` or `FR12`); where both appear in one text, say "freedom level FR5" and "register entry FR-M-005".

## 4. Columns

`register.csv` is UTF-8 without a BOM, LF line endings, comma-separated, quoted by the rules of Python's `csv` module (a field with a
comma, quote or line break is double-quoted and inner quotes are doubled). **One row per line:** no line breaks inside a field, so a
search for an id always finds the whole row.

| Column | Meaning | Format |
| --- | --- | --- |
| `id` | Register id (§3) | `FR-P-001` |
| `title` | The friction as one plain sentence | Says what goes wrong, not the fix |
| `audiences` | Who meets it, primary first | `people; models; contributors`, separated by a semicolon and a space |
| `area` | Where it lives | `<sweep or topic>: <detail>`, for example `first-run: Preview launch` |
| `description` | The walkthrough: what the person, model or contributor does and what happens | Plain prose; mark inferences `[I]` and unknowns `[U]` |
| `evidence` | Where the design or code says so | File and section (`game-integration §7`, `D024 item 2`, `doc 52 §5.4`), measurements with their source |
| `severity` | How bad it is when it happens | `1`, `2` or `3` (§5) |
| `frequency` | How often an affected person, model or contributor meets it | `<class>: <detail>` (§5), for example `constant: every Preview` |
| `removal` | The proposed removal, in D049's order (§6) | Names what stays intact; ends with "Resolve together with FR-..." when rows overlap |
| `change_in` | The files, records or crates the removal changes | Semicolon-separated |
| `effort` | Rough size of the removal | Starts with `S`, `S-M`, `M`, `M-L` or `L`, optional detail |
| `status` | Lifecycle state (§8) | `open`, `planned`, `removed`, `mitigated`, `declined` or `merged` |
| `found_on` | Date the row was added | `YYYY-MM-DD` |

**Reading one row.** Rows are long (up to about 3,700 characters), so text search tools may hide whole lines and a plain file read may
cut them. Search with a short pattern that prints only the start of the row (`^FR-P-012,[^,]*`), then read the row with a CSV reader,
for example `Import-Csv -Encoding UTF8 docs/friction/register.csv | Where-Object id -eq 'FR-P-012' | Format-List` in PowerShell, or
`python -c "import csv; print([r for r in csv.DictReader(open('docs/friction/register.csv', encoding='utf-8')) if r['id'] == 'FR-P-012'])"`.
Edit with a CSV-aware tool, never by hand-splitting on commas.

## 5. Severity, frequency and priority

**Severity** (how bad one occurrence is):

| Value | Meaning | Examples |
| --- | --- | --- |
| `3` | Blocks or derails a correct action, loses work, fails silently, or is likely to make people give up; for contributors, a risk that cannot be undone (a leak into the public repository) | A proposal thrown away by the next edit; Preview that seems to do nothing; a public-hygiene miss |
| `2` | A real cost with a workaround: extra steps, waits, confusion, wasted calls, rules that must be remembered | A confirmation that adds no information; two names for one tool |
| `1` | A minor annoyance, a rare case, or a cost only a few meet | A long staging path on a rare setup |

**Frequency** (how often an *affected* person, model or contributor meets it; breadth is shown by `audiences`, not here):

| Class | Score | Meaning |
| --- | --- | --- |
| `constant` | 4 | Many times per session: every call, every Preview, every edit of a kind, every commit |
| `session` | 3 | About once per session, or every session for the group affected |
| `workflow` | 2 | Each time a particular task is done: a new mission, a campaign run, a new rule, a measurement round |
| `once` | 1 | Once per install, setup, key, machine or newcomer, or rare |

**Priority** is severity × frequency score (1–12). It is computed when needed, never stored, so a row only changes when its facts do.
Ties are broken by severity, then by lower effort (cheaper first), then by more audiences. A friction that happens once can still
decide whether someone keeps using Plotroom (a first-run blocker); review severity-3 rows separately from the ranking, as doc 66 §2
does.

## 6. Removal order

A proposed removal follows D049 item 2 and the `AGENTS.md` rule, in this order:

1. **Eliminate the step** (the action, question or call is no longer needed).
2. **Choose a safe default** (the common case needs no input; the default is visible and editable).
3. **Make the wrong input impossible** (types, menus, generated names, computed paths, checks that run as you type).
4. **Automate** what the product or the tooling can compute.
5. **Explain at the point of friction** what happened and the one next action, when none of the above is possible.

Every removal states what stays intact. It must not widen the agent's scope, bypass typed undoable commands or UserIntent, weaken a
validator or a gate, or hide an AI-made element from the glass box. A removal that changes a decision record is marked "needs the
owner" and is raised as an owner question through the normal lifecycle (`docs/decisions/`), not decided in the register.

## 7. Adding an entry

1. **Search first.** Look for the area and key words in `register.csv` (title and area columns) and in the design-gap index. If a row
   already covers it, update that row (§8) instead of adding one.
2. **Pick the id**: the next free number for the primary audience's prefix.
3. **Fill every column.** Evidence cites files and sections; a claim nobody checked is marked `[I]` in the description. Keep every field
   on one line.
4. **Write the removal** in the order of §6, name what stays intact, and name overlapping rows ("Resolve together with FR-...").
5. **Check hygiene**: no local paths, user names, keys or private project names (`AGENTS.md`, "Public Repository Hygiene").
6. **Say it in the change set.** A design doc that introduces or removes a friction notes the ids in one header line (`Friction:
   adds FR-P-nnn; removes FR-P-009`, with the real new id), not in a new section.

The register is not a design-gap queue. When a friction's removal needs a design decision the docs do not make, also file or update
the design-gap request (`docs/design-gap-requests/`); an engine limitation goes to `docs/upstream/`; a question only the owner can
answer becomes an owner question. The friction row points to them.

## 8. Updating and closing

| Status | Meaning | What to record |
| --- | --- | --- |
| `open` | Known, not yet scheduled | — |
| `planned` | A change set, milestone or DG owns the removal | Name it at the end of `change_in` |
| `removed` | The friction is gone | Append `Closed YYYY-MM-DD: <proof>` to `evidence`: the test, measurement or doc section that proves it |
| `mitigated` | It cannot be removed, but it is now visible and explained where it happens | Same closing note, saying what remains |
| `declined` | The owner or a decision chose to keep it | The decision or owner answer, in `removal` |
| `merged` | Another row covers it | "Merged into FR-..." in `removal` |

- Change severity, frequency or removal when the facts change, and say why in the change set's message. Rows keep no change log;
  git history is the log.
- A row is closed only with evidence (the `AGENTS.md` Evidence Rule): a test, a measurement against a budget, or the doc section that
  now carries the removal.

## 9. The friction check for every change

Designers and implementers run this check on every design or implementation change and note the result in one line of the change
set (for example "Friction: none new; removes FR-C-022"). Answer each question for the audiences the change touches.

### 9.1 People using the editor

- Count the steps, clicks and confirmations for the main task this change touches. Can one go (eliminate, default, compute)?
- Does any confirmation guard something that is already undoable? If so, remove it (undo is the safety net).
- Is there a wait over about one second? Does it show progress, an estimate and a way to stop? Can it start earlier, in the
  background?
- Can anything fail silently: a refused gesture, a skipped step, a default kept, a fallback taken? Each needs a visible reason and
  one next action at the point where it happens.
- Are the defaults safe and visible? Would a newcomer be surprised by one?
- Is every new user-facing word in the names table, with a plain descriptor, and free of collisions?
- Does the change work on a laptop keyboard (no keypad, F-keys behind Fn), on each supported OS and with each install layout?

### 9.2 Models using Plotroom's APIs and tools (Wilco, external agents)

- Count the calls and tokens a typical task costs. Can code answer part of it (menus, computed options, UI context) so the model
  answers less?
- Is every name the model sees generated from the one registry? Is every tool the text mentions actually callable in that step?
- Can the input be a closed choice (letters, indexes, typed atoms) instead of free text the model must copy exactly?
- Does every error say what went wrong and what to call or change next, naming only tools the caller has?
- Does anything make a model poll, retry blindly or resend identical bytes? Give it a typed state, a bounded wait or a changed retry.
- Does the capsule stay cache-stable (nothing volatile above a breakpoint) and within the smallest qualified window?

### 9.3 Contributors and coding agents building Plotroom

- Is every new rule checked by a lint, test or check script rather than remembered? If it must be prose, is its scope stated?
- Does the change add a count, list or index row that someone must keep in sync by hand? Generate it instead.
- Can each index or entry file still be read in one tool call, and each row found by search?
- Do the documented commands run as written on Windows, Linux and macOS?
- Is there a scaffold for the new kind of file, fixture or test, or a one-line command to regenerate it?
- Does the change use the existing intake (DG, engine request, owner question, friction row) instead of a new list?

### 9.4 Every change

- Did the change remove friction without weakening product scope, typed undoable commands, validation or the glass box?
- Is friction found but not fixed recorded here?

## 10. Measuring friction once code exists

D049 item 3 asks for measurement where possible. Nothing leaves the user's machine for this: Plotroom sends no telemetry (D008 item 1
allows outbound traffic only to the configured model provider, enabled plugins and sources the user enabled), so measurement comes
from tests, local tools and voluntary reports.

| Audience | What is measured | Where |
| --- | --- | --- |
| people | Steps, clicks, confirmations and seconds for key flows: launch to first Preview; edit to Preview and back; connect a model to the first admitted proposal; open a downloaded mission to first edit | Acceptance tests with a stated budget per flow, driven through the UI test harness with the fake game binary and the deterministic fake model; a budget regression fails CI like a performance regression |
| people | Refusals per gesture, OK presses that return a rejection, confirmations per session, proposals discarded unseen, re-raised acknowledgements | Local session statistics the user can open (a view, never sent anywhere); alpha testers' voluntary reports |
| models | Calls and tokens per task, repair turns per decision, wrong-tool and not-in-step rates, format failures, waits per step kind | The decision journal and the cost ledger; harness evaluation suites (`tools/local-qual` today, `plotroom-evals` later) with budgets per `DecisionKind` |
| contributors | Time of the repo check script and of CI, files touched per typical change (a new rule, a new crate, an owner answer), index sizes against their byte budgets, rules enforced by lint versus prose | The check script's own report; a short list of "typical changes" whose file counts are recorded when the process changes |

Each budget is written next to the flow it measures (architecture or roadmap exit evidence), and a row in this register cites the
budget it is measured against when it is closed.
