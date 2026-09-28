# DG051: One outcome taxonomy at the provider seam

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round). Blocks: the provider seam's error types (D021), the router's limit outcomes (D050 item
> 4), admission's intake order and what qualification counts; doc 51 §4.5–§4.7 and doc 52 §5.2's `LimitOutcome` stay
> `proposal-only`.

## Context

- **Doc 51 §4.5.** Intake and admission in order: transport classification; finish and truncation (`Truncated`,
  `ThinkingExhausted`); reasoning split (counted, never journaled); deterministic cleanup from a closed list (BOM, whitespace, one
  outer fence, text before the last closing reasoning tag), each application logged; on the no-schema channel exactly one
  envelope-shaped JSON value, else `AmbiguousAnswer`; strict serde; validation against the full original schema; domain validators;
  settlement as `Admitted{value, deviations, flags}` or `Rejected{finding}`, flags never counting as first-pass successes.
- **Doc 51 §4.6–§4.7, §6.1 items 2–5.** Two enums, `ProviderFailure` (rate limits by scope, quota, capacity, context, capability,
  business errors in HTTP 200, stream watchdogs, auth, transport, cancelled) and `InvalidAnswer` (empty, thinking only, truncated,
  thinking exhausted, tag leak, placeholder, ambiguous, parse error, filtered, finish mismatch), and a table of which outcomes count
  against model accuracy, endpoint dependability or neither. Items 2–5: admission tolerance on the no-schema transport against doc 21
  §8.2's "schema violations are refused"; ambiguous answers; the taxonomy; mandatory-reasoning endpoints.
- **Doc 52 §5.2, RG2; D050 item 4.** The router's `LimitOutcome` (upstream throttled, account rate limited, quota exhausted, payment
  required, no endpoint for policy, model gone, content filtered), each mapped to one router action; D050: "Failed attempts are typed
  limit outcomes". D050 routes RG2's accounting to DG016.
- **DG016** (open) defines turns and transport retries; **doc 56 WR2** asks for a closed list of retryable faults, and **§9 tension
  5** accepts cleanup only if logged and never counted as first-pass. **D045 item 5; doc 48 §5.4**: dependability counts for free
  models.

## The gap

Two overlapping proposals type the same failures (a 429 is a `ProviderFailure::RateLimited` in doc 51 and a `LimitOutcome` in doc 52),
and no document fixes one taxonomy that the adapter, router, ledger, qualification and inspector share. Doc 51's non-blocking
deviations sit uneasily with doc 21 §8.2's strict admission until the allowed list is fixed.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Separate enums per concern (adapter failures, router limit outcomes, admission findings), mapped where needed | Each module owns its type | The same event is typed twice; qualification and the router can disagree about what counted |
| B | One taxonomy at the seam: doc 51 §4.7's `ProviderFailure` and `InvalidAnswer` with its counting table; `LimitOutcome` as the router's reading of the limit variants; intake in doc 51 §4.5's order; the only tolerated deviations are §4.5 step 4's closed cleanup list, each logged and never first-pass; two envelope-shaped values is a blocking `AmbiguousAnswer`; mandatory-reasoning endpoints run Pick and Fill at the floor level with a reasoning-sized cap from the profile (DG045) | One truth for routing, the ledger, qualification and the inspector; consistent with doc 21 §8.2 and doc 56 tension 5 | Merging two proposals; each crate's `Error` enum (AGENTS.md) must map into it |

## Recommended resolution (proposal)

B (doc 51 §4.5–§4.7, doc 52 §5.2, D050 item 4). DG016 keeps the accounting (what is a turn, what a transport retry).

## What it would change

- D021 (the seam's types); doc 52 §5.2 (`LimitOutcome` defined from the shared taxonomy); doc 21 §8.2 (a note on the closed cleanup
  list); doc 38 §4.6; the qualification counting rules (doc 21 §12.3; D045 item 5).
- Tests first (proposal): every provider fixture maps to exactly one variant; a platform 429 and an upstream 429 map to different
  variants and different router actions; a cleaned answer is admitted with its flag and never counted as first-pass; two envelopes
  settle `AmbiguousAnswer`.

## Affected docs

D021; D045; D050; doc 21 (§8.2, §12.3); doc 38 §4.6; doc 48 §5.4; doc 51 (§4.5–§4.7, §6.1); doc 52 (§5.2, §6.2); doc 56 (WR2, §9);
DG016; DG045.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 51 §6.1 items 2–5 and doc 52 RG2 (its taxonomy half; the accounting half is DG016's, as D050 says), re-read on
  2026-09-28 with D050, DG016 and doc 21 §8.2.
