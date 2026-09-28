# DG059: The witness surface of config span patches

> Design-gap request (`AGENTS.md`, "Design Authority"; "Witness and guard types": a change to a witness or guard type's public
> surface is a design decision). Filed 2026-09-29 by the SP-09 change set that created `crates/plotroom-config`. Status: **open**.
> **Decision by: technical** (design round, with SP-10's measurements and the needs of `plotroom-mission`'s lens in M1).
> Blocks: nothing in M0; the surface below is **implementation placeholder** until decided, and M1's lens builds on it.

## Context

- **Core-document-model §3.1, §4 item 2, §12 R2**: edits are span patches; an edit changes bytes only inside the patched spans;
  `verify_round_trip_each_commit` checks it after every commit.
- **Doc 04 §12.3 items 2 and 6**: changing a value replaces only its raw lexeme; changed numbers are spelled by a writer profile.
- **Roadmap SP-09**: "a patch leaves bytes outside its span unchanged; offsets from a relative-length green tree".
- **`AGENTS.md`**: witnesses have private constructors, no `Default`/`Deserialize`/`From<Inner>`, `#[must_use]` messages that name
  the next action, and a trybuild case per misuse.

## The gap

SP-09 needed a patch API to prove its exit criteria, and no document fixes its shape. The spike landed this surface in
`plotroom-config` (`src/cst/lexeme.rs`, `src/cst/patch.rs`, `src/text.rs`), with trybuild cases in `tests/ui/`:

| Type | Proves | Built by |
| --- | --- | --- |
| `EntryValueLexeme`, `ElementValueLexeme` | The bytes read back as exactly one value in their context (entry value or array element), checked by rules and by parsing a synthetic statement | `quoted`, `int`, `float(value, WriterProfile)`, `bare` |
| `EntryValueRef<'cst>`, `ElementValueRef<'cst>` | The value exists in this tree revision; borrows the tree and is checked against its root `Arc` when used | `ConfigCst::entry_value(path)`, `ConfigCst::element_value(path, indices)` |
| `Patched` (`#[must_use]`) | The patched tree re-parses to itself and stays within the size cap | `ConfigCst::replace_entry_value`, `replace_element_value` |
| `ByteEdit` | The declared change; `check_outside_unchanged` (`#[must_use]`) proves no other byte changed | returned inside `Patched` |
| `TextSpan` | `start <= end` | `TextSpan::new`, `at`, `empty_at` |

Open points the spike could not settle alone:

1. **References across edits.** A reference is valid for one revision only; after a patch the caller looks the value up again. The
   lens (M1) may want references that survive unrelated edits (rebased by the `ByteEdit`), or stable node ids.
2. **Quoted values before whitespace.** `x = 5 ;` cannot take a quoted value: the game drops `x = "a" ;` and the rest of the class
   (`ParamFile.cpp#L1798-L1803`). The patch is refused with `QuotedValueNeedsAdjacentTerminator`, but no API removes the whitespace.
   A `replace_entry_value_tight` that declares the wider span (value plus whitespace) would remove this friction.
3. **Verification cost.** Each patch re-parses the whole text to prove the structure is unchanged (O(file)). Re-reading only the
   enclosing statement is cheaper but must account for state that crosses statements (the preprocessor's quote and line-start
   state). SP-10 measures whether the whole-file check fits the commit budget.
4. **What else is patchable.** Inserting and deleting entries (doc 04 §12.3 item 2: a new key at the engine's canonical position,
   with the parent's indent and line ending), replacing a sub-array, renaming a class, and editing enum or `__EXEC` values are not
   offered.
5. **Names.** `EntryValueLexeme`/`ElementValueLexeme` and `replace_entry_value`/`replace_element_value` name the context; the
   command layer (`plotroom-commands`) may prefer one generic operation with a context parameter.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Keep the spike's surface for M1; add `_tight`, insertion and deletion as separate typed operations when the lens needs them | Each operation keeps one proof; small, reviewable steps | More API names |
| B | One generic `patch(ref, lexeme)` with the context in the types (`Lexeme<Entry>`, `Lexeme<Element>`) | One entry point | Phantom context labels are not proofs (`AGENTS.md`); the proof must still be per context |
| C | Stable node ids and references that survive edits | The lens can hold references | Ids must be minted and re-matched (core-document-model §7); larger change |

## Recommended resolution (proposal)

Option A for M1, with point 2's `_tight` variant added when the lens first writes a quoted value, point 3 decided by SP-10, and
point 1 revisited if the lens needs references across edits (then option C, aligned with doc 45 OQ4).

## What it would change

`crates/plotroom-config/src/cst/{lexeme,patch}.rs` and their trybuild cases (`tests/ui/`); `CODE-INDEX.md` §5 (guard types);
core-document-model §3.1 (the patch operations) once decided.

## Affected docs

`docs/architecture/core-document-model.md` §3.1, §4, §12; `docs/roadmap/spikes-and-probes.md` (SP-09, SP-10); `CODE-INDEX.md`.

## Decision record

Open.

## Verification notes

### Filing (2026-09-29)

- Filed with the code: every row of the table above is implemented and tested in `crates/plotroom-config` (unit tests
  `cst/tests_patch.rs`, property test `tests/prop_patch.rs`, trybuild cases `tests/ui/*.rs`). Core-document-model §3.1, §4, §12 and
  doc 04 §12.3 were re-read; SP-10's measurement has not been made.
