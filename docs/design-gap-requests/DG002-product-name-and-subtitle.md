# DG002: Where the product name and its descriptive subtitle may appear

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **decided** (owner,
> 2026-09-27, OWQ-07): option A with the placement table in the decision record; `AGENTS.md` "Naming and Trademarks" is amended to
> match; the clearance search is recorded in doc 02 and the repository renamed before the first release. Not yet folded (see the
> folding list in the decision record; the `AGENTS.md` step is done).
> **Decision by: owner.** Blocks: the repo rename, crate and binary names, the window title, and the final `NOTICE` and disclaimer
> text (doc 02 §11 steps 1–2).

## Context

- The owner has settled the name: **Plotroom: Mission & Campaign Editor for Arma: Cold War Assault / Operation Flashpoint**. The
  README already uses "Plotroom" as the heading and the rest as a bold tagline.
- Doc 02 §11 step 1 still reads "Pick a new product name (§9 checklist, clearance search) and rename the GitHub repo", and doc 02 §9
  and §10.2 still carry `<Product>` placeholders (disclaimer, SPDX copyright lines).
- Doc 02 §9 naming checklist, item 1: the product, repo, crate names, binary, window title, installer and icon contain none of
  `Arma`, `OFP`, `Flashpoint`, `Cold War Assault`, `Cold War Crisis`, `Poseidon`, `Bohemia`/`BI` or BI island names. Item 2: a
  clearance search (USPTO, EUIPO, WIPO Global Brand DB, crates.io, GitHub, Steam, ModDB). Item 4: nominative use is fine in body
  text ("a standalone mission editor for *Arma: Cold War Assault*").
- Doc 02 §9 on the repo name: `ofp-editor` uses the universal abbreviation of the EA mark; rename before the first release.

## The gap

The settled name contains two third-party marks ("Arma", "Operation Flashpoint") and "Cold War Assault". Read as one product name,
it breaks checklist item 1. Read as a product name ("Plotroom") plus a descriptive subtitle, the subtitle is nominative use under item
4. No doc says which reading applies, or where the subtitle may and may not appear. The clearance search for "Plotroom" is also not
recorded as done.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | The formal product name is **Plotroom**; the subtitle is a descriptive tagline used only in body-text places | Fits doc 02 §9 items 1 and 4; keeps marks out of identifiers | The long form cannot be the window title or installer name |
| B | The full long form is the product name everywhere | Matches how the owner phrased the decision | Conflicts with doc 02 §9 item 1 and Bohemia's §7 term against distributing a modification "using" the marks (doc 02 §9, "What binds us") |
| C | Plotroom alone everywhere; no subtitle | Simplest legally | Users searching for the game would not find the tool; loses the owner's framing |

## Recommended resolution (proposal)

Option A, with this placement rule:

| Place | "Plotroom" | Subtitle "…for Arma: Cold War Assault / Operation Flashpoint" |
| --- | --- | --- |
| Repo name, crate names, binary, installer file and product name, icon, window title, config and sidecar directory names | Yes | **No** |
| README heading and tagline, About box, website, release notes, store or forum descriptions, doc headers | Yes | Yes, as plain text (no stylised marks or logos), with the doc 02 §9 disclaimer in the same place or one click away |
| In-app body text ("Preview in game", compatibility notes, target-profile badges) | As needed | Game names used only to identify the game (doc 02 §9 item 4) |

Also: record the clearance search for "Plotroom" (doc 02 §9 item 2) in doc 02 before the first release; fill the disclaimer and
SPDX `<Product>` placeholders with "Plotroom"; rename the repository away from `ofp-editor` before the first release (GitHub keeps
redirects). Never claim "official", "remastered" or "endorsed" (item 5).

## What it would change

- Doc 02 §11 step 1: "Name chosen by the owner (Plotroom); clearance search pending; rename the repo." §9: a short "Placement of the
  descriptive subtitle" paragraph with the table above; the disclaimer and §10.2 SPDX lines use "Plotroom".
- README: unchanged (it already follows option A).
- Future `NOTICE`, About box and window-title code follow the table.

## Affected docs

Doc 02 (§9, §10.2, §11); README.md; later `NOTICE` and `CONTRIBUTING.md`.

## Decision record

- **Decided:** 2026-09-27. **By:** the owner, answering OWQ-07 in
  [`docs/decisions/OWNER-QUESTIONS.md`](../decisions/OWNER-QUESTIONS.md). **Chosen:** option A, as recommended above, with the
  placement table below. **Decision record:** [D034](../decisions/D034-descriptor-placement-and-names-delegation.md) states the rule
  going forward (with OWQ-08's delegated names) and refines D002.
- **Rule.** The formal product name is **Plotroom**. "Mission & Campaign Editor for Arma: Cold War Assault / Operation Flashpoint" is
  a plain-text descriptor (tagline), not part of the name. Identifying surfaces carry "Plotroom" alone; descriptive surfaces may pair
  the name with the descriptor and carry the disclaimer.

  | Place | "Plotroom" | Descriptor |
  | --- | --- | --- |
  | Repository name, crate names, binary, installer file name and installer product name, icon, **window title**, config and sidecar directory names | Yes | **No** |
  | README heading and tagline, splash, About box, website, release notes, store and forum listings, doc headers | Yes | Yes, as plain text (no stylised marks or logos), with the `README.md` non-affiliation disclaimer in the same place or one click away |
  | In-app body text ("Preview in game", compatibility notes, target-profile badges) | As needed | Game names only to identify the game (doc 02 §9 item 4) |

  The splash is not in the proposal's table. `AGENTS.md` listed it among the descriptor surfaces and the owner's answer excludes only
  the window title, installer name, binaries and directories, so the splash sits in the descriptive row with the About box.
- **`AGENTS.md` amendment (owner-approved, made).** The first bullet of "Naming and Trademarks" was replaced by four bullets that state
  this table: the descriptor is a descriptive tagline, not part of the name; "Plotroom" alone, never with the descriptor, on the
  identifying surfaces (window title, installer product name and file name, application icon, repository, crate and binary names,
  configuration and sidecar directory names); "Plotroom" with the plain-text descriptor and the `README.md` disclaimer (same place or
  one click away) on the descriptive surfaces, including the splash screen; in-app body text names the game only to identify it. The
  section's other bullets (the `plotroom` prefix, no marks in identifiers) are unchanged. `AGENTS.md` is the authoritative wording.

- **Clearance and rename.** Before the first release: the clearance search (doc 02 §9 item 2: USPTO, EUIPO, WIPO Global Brand DB,
  crates.io, GitHub, Steam, ModDB) for Plotroom, Wilco, Plotline, the Tote and Teller is recorded in doc 02, and the repository is
  renamed away from `ofp-editor` (GitHub keeps redirects). The new repository name follows the identifying row (no third-party marks);
  choosing it is part of the rename and is not decided here. The disclaimer and SPDX `<Product>` placeholders in doc 02 §9 and §10.2
  take "Plotroom". Never "official", "remastered" or "endorsed" (doc 02 §9 item 5).
- **Reason.** Option A fits doc 02 §9 items 1 and 4: marks stay out of every surface that names or identifies the product, and the
  descriptor still tells players which game the tool serves. Option B conflicts with doc 02 §9 item 1 and Bohemia's §7 term against
  distributing a modification "using" the marks; option C would hide the tool from players searching for the game.
- **Folding (what moves this request to `folded`).**
  1. `AGENTS.md` "Naming and Trademarks": done (the amendment above).
  2. D002 item 1 and its "placement open" status and Consequences: updated under the decision-record rules (`docs/decisions/README.md`):
     done (2026-09-27): D034 refines D002, and D002's header and notes point to it.
  3. Doc 02 §9 (a short "Placement of the descriptor" paragraph with the table), §10.2 (SPDX lines), §11 step 1 ("Name chosen by the
     owner (Plotroom); clearance search pending; rename the repository before the first release").
  4. Later `NOTICE`, `CONTRIBUTING.md`, About box and window-title code follow the table. The README needs no change.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 02 §9 (naming checklist, repo name, disclaimer), §10.2 and §11 step 1, and the README heading, all re-read on
  2026-09-27. No clearance search was run in this pass. Not legal advice; doc 02 governs.

### Consistency review (2026-09-27)

- `AGENTS.md` ("Naming and Trademarks") lists the README, window title, splash, About box, installer and listings as surfaces that
  pair "Plotroom" with the descriptor. The recommended table above puts "No" in the window title and installer rows, so it contradicts
  `AGENTS.md` for those surfaces. The owner either amends `AGENTS.md` or the table changes for them; the conflict is recorded in
  OWQ-07, and `AGENTS.md` governs meanwhile. Identifiers (repository, crates, binary, installer file name, directories) carry no marks
  under either reading.

### Owner answers (2026-09-27)

- Decision record written from the owner's dated answer to OWQ-07, which resolves the conflict above by amending `AGENTS.md`. Re-read
  for this step: OWQ-07, D002, the README heading and disclaimer, and `AGENTS.md` "Naming and Trademarks" after its amendment in the
  same pass (checked against the table above: same surfaces on each side, the splash screen with the descriptor). This file edited
  neither `AGENTS.md` nor doc 02. No clearance search was run and nothing was renamed. Not legal advice; doc 02 governs.

### Consistency review of the owner answers (2026-09-27)

- The decision record now links D034, which states the same table (the splash with the descriptor, as here and in `AGENTS.md`), and
  folding step 2 is done (D002's header and notes point to D034). Steps 3–4 (doc 02, later code) remain, so the request stays
  `decided`, not `folded`.
