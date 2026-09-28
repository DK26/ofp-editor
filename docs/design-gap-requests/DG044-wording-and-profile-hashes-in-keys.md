# DG044: Question wording, model profile and language in the qualification and calibration keys

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round). Blocks: the qualification record and badge format beyond D051 item 4's parts; the
> calibration table key (doc 53 §4.2; doc 55 `scoring.calibration`); doc 60 P-02 and P-07 stay `proposal-only`.

## Context

- **D051 item 4** (2026-09-28): a grant belongs to (setup, harness preset, `DecisionKind`, level, domain: target profile, language,
  mod-set class) and DG012's triggers void it. This settles doc 55 §7 item 1 (the preset in the key) and doc 63 §13 item 3 (level and
  domain).
- **DG012** (open) proposes keying qualification by (model setup, `DecisionKind`, prompt-template version, lens pack version,
  exemplar pack version, schema id), with a major change voiding and a minor change marking it "requalifying".
- **Doc 60 P-02, §4 item 1.** The question text is "a hashed, versioned artifact in every key" (run record, calibration,
  qualification): changing one character of a question's description changes the hash, marks the badges `requalifying`, and makes
  the calibration lookup return `Uncalibrated`. **P-07, §4 item 10**: the calibration key is (form, wording hash, menu size, language);
  nothing keys calibration by prompt language today (doc 16 OQ4).
- **Doc 51 §4.8.** "A badge records the preset and profile hashes; a change to any field that reaches the wire voids it for the
  affected step kinds, exactly like a changed template hash." The profile is the probed-facts record of DG045.
- **Doc 55 §3.2, §4.5** bind a preset to the model file, runtime and template; **doc 53 §4.2** routes by calibrated margins.

## The gap

D051 names the parts of a grant but not two inputs later docs show can move accuracy: the exact wording code renders for a question
(a pack version may not change when one description is reworded) and the model profile's facts. Calibration tables, which route
decisions (doc 53 §4.2), have no key at all. Doc 51 §4.8 voids a badge on any wire change, while DG012 proposes that minor changes
only mark it "requalifying".

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | D051's key only; wording covered by prompt-pack versions (DG012) | Fewer keys | A reworded question inside one pack version keeps its badge and its calibration (doc 60 P-02's case) |
| B | D051's key plus the question-wording hash and the profile hash; calibration keyed by (preset, `DecisionKind`, form, wording hash, menu size, language); whether a change voids or marks requalifying follows DG012 | Every input known to move accuracy is in a key; one voiding rule | More requalification; the hashes must be canonical (doc 56 WR7) |
| C | As B, with doc 51 §4.8's rule that any wire change voids | Strictest | Every typo fix voids badges (DG012 option A's cost) |

## Recommended resolution (proposal)

B for the keys, since docs 51, 55 and 60 each add their part and none argues against the others. The voiding rule stays DG012's
question; this request records doc 51 §4.8's stricter reading there as an argument for DG012 option A.

## What it would change

- DG012's record format (two more keys); agent-runtime §5 (`ModelRequested` carries the wording hash); doc 55 §3.2 and §4.5; doc 53
  §4.2 and §5.3 item 4 (calibration key); D037 badge text.
- Tests first (doc 60 P-02, P-07): one changed character changes the hash, marks the badges `requalifying` and makes calibration
  return `Uncalibrated`; a calibration lookup with any key part different returns `Uncalibrated`.

## Affected docs

D051; DG012; doc 51 §4.8; doc 53 (§4.2, §5.3); doc 55 (§3.2, §4.5, §7); doc 60 (P-02, P-07, §4); doc 63 §4.4;
`docs/architecture/agent-runtime.md` §5; D037; DG045.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 60 §4 items 1 and 10, doc 55 §7 item 1, doc 63 §13 item 3 and doc 51 §4.8, re-read on 2026-09-28 with D051 and DG012.
  Written after D051 appeared the same day, so the preset, level and domain parts are cited as decided there and not re-proposed.
