# DG002: Where the product name and its descriptive subtitle may appear

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
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

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 02 §9 (naming checklist, repo name, disclaimer), §10.2 and §11 step 1, and the README heading, all re-read on
  2026-09-27. No clearance search was run in this pass. Not legal advice; doc 02 governs.
