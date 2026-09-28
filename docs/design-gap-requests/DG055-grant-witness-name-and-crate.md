# DG055: The grant witness: one name, one scope, one crate

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round; the level names are D034 item 3's). Blocks: the grant type and its executors (doc 63 §9.2);
> `AGENTS.md` ("Witness and guard types") makes a new witness's public surface a design decision with negative compile tests.

## Context

- **D051 items 2 and 4** (2026-09-28): freedom levels FR0–FR8; a grant belongs to (setup, harness preset, `DecisionKind`, level,
  domain) and is set only by qualification. D051's open parts include "the grant witness's name and crate (doc 62 §6.3)".
- **Doc 63 §9.2, §9.4, §13 item 7.** Sketch: `Grant<L: Level>` with a private constructor, sealed `Level` markers, an `AtLeast<Min>`
  trait with `#[diagnostic::on_unimplemented]` notes, and an `EffectiveGrant` enum that callers `match`. Placement is open: the sketch
  puts `Grant` in `plotroom-evals` and `run_draft` in `plotroom-wilco`, but crate-map §2.2 has no edge between them;
  qualification-record types live in `plotroom-provider` (crate-map §9); "probably belongs in `plotroom-provider` or `plotroom-decide`
  (an allowed edge), with minting behind one function that only the runtime may call". §9.4 option 2: a layering check that only the
  runtime calls `grant::effective`.
- **Doc 62 §6.3, §10 item 7.** The same witness as `ShapeGrant<S: Shape>`; and whether the grant should instead be "a broader grant
  that also carries autonomy (D024)".
- **`AGENTS.md`**, "Witness and guard types", "Diagnostics as Guidance" and "Negative Compile Tests": private constructor, bound to
  what was checked, no `Default`, `Deserialize`, `From<Inner>`, `DerefMut` or public fields; guidance names the sanctioned API;
  misuse is proven by `trybuild` UI tests. (This settles doc 63 §9.4 option 3 and doc 62 §10 items 1 and 3 at the rule level.)
- **D024.** Effort, autonomy and role binding are three separate dials.

## The gap

One witness has two names and two parameter vocabularies (levels in doc 63, shapes in doc 62), an open question whether it also
carries autonomy, and no crate that the crate map allows both its minting and its use from.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | `Grant<L: Level>` over D051's levels, proving step size only (doc 63 §9.2) | Matches D051's vocabulary; autonomy stays D024's separate dial | — |
| B | `ShapeGrant<S: Shape>` over the four shapes (doc 62 §6.3) | The type-guidance study's name | D051 item 2 refines shapes into levels |
| C | A broader grant that also carries autonomy (doc 62 §10 item 7) | One witness for "may this step run this way" | Merges two of D024's dials; autonomy is a user setting, not a qualification result |

Crate: (i) `plotroom-provider`, where qualification records live; (ii) `plotroom-decide`, an allowed edge; (iii) `plotroom-evals`,
which needs a `plotroom-wilco` → `plotroom-evals` edge that crate-map §2.2 does not allow.

## Recommended resolution (proposal)

A, because D051 made levels the vocabulary and D024 keeps autonomy separate; crate (i) or (ii) per doc 63 §9.2's review note, decided
with the crate map; minting behind one function only the runtime calls, enforced by a layering check (doc 63 §9.4 option 2), and
misuse proven by `trybuild` UI tests as `AGENTS.md` requires. User-facing words for the levels stay with D034 item 3.

## What it would change

- Doc 63 §9.2 (name and crate); doc 62 §6.3 (a pointer); `docs/architecture/crate-map.md` (§2.2 edges, §9); `CODE-INDEX.md` (the
  newtype and witness table) when the code lands.
- Tests first (doc 63 T-L15; `AGENTS.md` "Negative Compile Tests"): `effective` never returns a grant without a record; a crate other
  than the runtime calling `grant::effective` fails the layering check; UI tests show that a lower grant cannot call a higher-level
  executor and that no crate can build a grant literal.

## Affected docs

D051; D024; D034; `AGENTS.md` (type-safety sections); doc 62 (§6.3, §10); doc 63 (§9, §11, §13); `docs/architecture/crate-map.md`.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 63 §13 item 7 and doc 62 §10 item 7 (one candidate in two docs), re-read on 2026-09-28 with D051, D024 and `AGENTS.md`'s
  type-safety sections as they stood that day (the "Negative Compile Tests" section was present).
