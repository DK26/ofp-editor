# Safe free-model testing: OpenRouter, Groq and Cloudflare Workers AI

Three providers, one pattern: each key is stored once, DPAPI-encrypted for your Windows user, and `run-cloud.ps1`
decrypts it into one `run.py` process; `run.py` keeps each provider's free limits on the client side and stops before
anything could be billed. Sections 1–10 below are OpenRouter's runbook; [Groq](#groq-free-plan) and
[Cloudflare Workers AI](#cloudflare-workers-ai-daily-free-allocation) follow it (D058 item 3).

| Provider | Store the key | Check it (no quota) | Run flag |
| --- | --- | --- | --- |
| OpenRouter | `set-openrouter-key.ps1` | `run-cloud.ps1 --key-status` | `--free-only` |
| Groq | `set-groq-key.ps1` | `run-cloud.ps1 --provider groq --key-status` | `--provider groq` |
| Cloudflare Workers AI | `set-cloudflare-token.ps1` (token and account id) | `run-cloud.ps1 --provider cloudflare --key-status` | `--provider cloudflare` |

`set-provider-key.ps1 -Provider <name>` and `remove-provider-key.ps1 -Provider <name>` run the matching store and remove
scripts, for one command to remember.

This is the runbook for the account owner. It covers running the local-qual suites against OpenRouter's **free**
model variants (ids ending in `:free`) with no way to spend money, a key that never sits in plaintext, and the free
tier's rate limits kept on the client side. It sets up an account, a key and a Windows machine for the first round.
All facts below were read on **2026-09-27**; step 5 and the HTTP 429 section (added 2026-09-28) rest on those
readings and on the project's own observations of 2026-09-28 (doc 52), not on a new reading of OpenRouter's pages.
OpenRouter changes its free catalogue without notice, so the tool re-checks them on every start.

Only an owner creates accounts and keys, changes settings, or pays. An agent never does, and never sees the key.

## What you get, and what you still decide

With `--free-only`, `run.py`:

- **refuses anything but one free model:** the id must be `<author>/<slug>:free` outside `openrouter/` (routers such
  as `openrouter/auto:free` can bill paid models). At every start and every resume, the exact id must be in the live
  public catalogue with **every price present exactly 0** (Decimal equality, so a router's `-1` fails), text output
  only, and every endpoint zero-priced. The catalogue is read **without the key**.
- **cannot spend:** the cap and every price are 0. Each response must report `usage.cost` exactly 0, no BYOK cost,
  and the requested model. Anything else stops the run at once with **exit 9**. `GET /key` is read at the start,
  every 10 attempts or fewer, and once more however the run ends (done, or stopped for any reason), and any rise in
  the key's usage is exit 9. Every reading is written to the ledger, and the next start on that ledger refuses
  (exit 9) if the key spent more since, so a charge that no response showed (a stream, a timeout, a killed run) is
  never forgotten. A ledger that ever recorded spending refuses to start again.
- **refuses a key that could spend:** a management key, a key with no credit limit, or a key with more than
  `--max-key-headroom-usd` (default 0) left on its limit is refused. Only non-secret fields of the key record are
  printed; its `label` (a partly masked key) and the account ids never are.
- **routes strictly:** it sends `provider.require_parameters: true` (an endpoint without strict structured outputs
  is skipped, never answering unconstrained), `allow_fallbacks: false`, and pins `provider.only` to the endpoints
  read at start. It refuses before sending when the endpoint lacks a parameter the run would send, and names the fix.
- **keeps the free limits:** one free run at a time on this Windows user, whatever its ledger (the limits are per
  account). At most 18 attempts in any 60 s (OpenRouter allows 20). At most 45 attempts per UTC day
  in the shared `--ledger` (the account allows 50 a day under 10 purchased credits), and never more than the
  account's remaining free requests minus 5. Every attempt counts, 429s and errors too. A 429 naming the daily quota
  ends the run (**exit 10**) with the time to resume. A per-minute 429 waits for its reset. Three 429s in a row also
  end it (exit 10). `--resume` after 00:00 UTC continues where it stopped.

Without a run, `--key-status` reads the key record alone, at no quota, and prints its credit limit, usage and today's
free-model requests (step 5).

What the tool cannot decide for you: **which providers may see the prompts.** That is an account setting (step 2).
Only the synthetic suite items in `suites/` are ever sent: our own text, no user content, no mission files, no
game content.

## 1. The account

1. Create a **separate OpenRouter account used only for these synthetic tests**. Account-level privacy toggles apply
   to every key on the account, and a guardrail can only tighten them, so a testing account must not also carry real
   user content.
2. Add **no payment method** and turn **Auto Top-Up off**. Free models work at a $0 balance, but a *negative* balance
   returns 402 even on free models.
3. Store **no provider keys (BYOK)** on this account: a request routed through one would bill that provider account.
4. Optional, and a spend decision for you alone: buying 10 credits once raises the free daily limit from 50 to 1,000
   requests for good (the tier follows lifetime purchases, not the balance). It also gives the account a positive
   balance, which makes the key limit in step 3 essential. Stay at 50 a day until the first round shows it is
   worth it.

## 2. Privacy settings (Settings → Privacy, and Settings → Observability)

Keep two OpenRouter settings **off** always. **"Input & Output Logging"** (Settings → Observability) stores every
prompt and completion in your account's logs for at least 3 months. The **use of inputs/outputs** setting (Settings →
Privacy, the one that offers a 1% discount) lets OpenRouter use your requests to improve its products. Then pick a
tier. Start at tier 0.

Two toggles govern free endpoints: **"Free endpoints that may train on request data"** and **"Free endpoints that
may publish prompts"**. With either off, free endpoints that train or publish are filtered out, and a request to one
fails with 404 *"No endpoints available matching your guardrail restrictions and data policy"*. The tool stops on
that (exit 5) without retrying. Settings exist for the account, the organisation and the key; **the strictest one
wins**. Enforcing Zero Data Retention (ZDR) also removes every free endpoint that retains prompts.

| Tier | Toggles (train / publish) | Extra body | Free text models expected to route (2026-09-27) |
| --- | --- | --- | --- |
| 0 (start here) | off / off | `--extra-body @tools/local-qual/cloud/provider-zdr.json` (`zdr: true`, `data_collection: deny`) | `qwen/qwen3.8-27b:free` (the only general model on the ZDR list) |
| 1 | off / off | none | adds Gemma 4 26B and 31B (Google AI Studio, keeps prompts 55 days, no training) and dots-3-note-preview (AtlasCloud, keeps prompts) |
| 2 | **on** / off | none | adds Nvidia Nemotron (3 Super 120B, 3 Ultra 550B, ...), Liquid LFM 2.5 2.6B and Thinking Machines Inkling, whose free terms allow training on prompts |

No free text endpoint needed the publish toggle on 2026-09-27; leave it off. **Never turn the training or publish
toggle on for an account whose keys carry real user content.** Tier 2 is acceptable here only because the account
sends nothing but the synthetic suites. The dashboard's guardrail **Eligibility Preview** shows which models the
current settings leave routable, without sending a prompt.

## 3. The key

In the testing account, create a key:

- **Name:** something distinct, such as `plotroom-local-qual-free-2026-09`, so it is easy to find and revoke.
- **Credit limit: 0**, with no reset. The tool refuses a key with no limit (a normal key cannot read the account
  balance, and new accounts may hold a small allowance), and any key with money left on its limit.
  Whether OpenRouter lets a key with a $0 limit call free models is not documented. If the first run stops with
  HTTP 402 (exit 4), set the smallest limit the dashboard accepts (for example $0.01) and pass
  `--max-key-headroom-usd 0.01`. If the key check says **no credit limit (unlimited)** although you entered 0, the
  dashboard stored no limit at all; do the same.
- **Expiry:** a date a few weeks out.
- **Optional guardrail:** an allowlist of exactly the `:free` ids you test, with the tier's privacy flags. With it,
  OpenRouter itself rejects any other model.

Copy the key once, straight into step 4. Do not paste it into chat, a file, an issue or a terminal command. Before
you copy it, check Settings → System → Clipboard in Windows: with **"Sync across your devices"** on, copied text is
sent to your other devices through your Microsoft account, so turn it off first. After step 4, copy something else
over the key and, if **Clipboard history** is on, delete the key's entry (Win+V).

## 4. Store the key (Windows)

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\set-openrouter-key.ps1
```

This asks for the key with hidden input and checks that it looks like an OpenRouter key (`sk-or-...`). It encrypts
the key with Windows DPAPI for your Windows user and writes it to `%LOCALAPPDATA%\plotroom-dev\secrets\openrouter.key`.
Only you, on this machine, can decrypt it, and the folder and file are readable by your user only. The script
refuses a path inside any git working tree. `-Force` replaces a stored key. `-ExecutionPolicy Bypass` applies to
this one command only. Run the key scripts with `powershell -File` as shown: it starts a fresh session without your
profile. The key never becomes a cmdlet argument, so PowerShell module logging, which some organisations turn on,
cannot record it. Run in-process instead (`& .\run-cloud.ps1`), the scripts switch `Set-PSDebug` tracing off for
your session, because trace level 2 would print the key.

## 5. Check the key and today's free allowance (no quota used)

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --key-status
```

This sends one request, `GET https://openrouter.ai/api/v1/key` with the stored key, and prints the key record's
non-secret fields in plain words: the credit limit and what is left of it, usage in all and today, BYOK usage, free
tier yes or no, management key yes or no, the expiry, today's free-model requests (used, limit, left) with the reset
at 00:00 UTC, the per-key rate limit, and whether a `--free-only` run would accept the key (`refused:` names the
fix). It sends no model request, so it spends nothing and uses none of the day's free requests. It writes no ledger
or file and takes no lock, so it also runs while a free run is active. The record's `label` (a partly masked copy of
the key) is never printed. Use it after step 4, before a round, or whenever a 429 elsewhere makes you wonder whether
this setup still works.

Two fields need care. The free-model count is the account's own counter, and it is not a real-time count: on
2026-09-28 it read 0 before and after an answered free call ([doc 52](../../../docs/research/52-rate-limits-and-ux.md),
re-check of that day), so the report says it can lag. The per-key `rate_limit` read `-1` requests per 10 s on that
day (shown as `none`), and the record itself marks the field deprecated; it is not the limit a free run meets. The
free-model limits count per account, so the report says so on the same line
([HTTP 429](#http-429-which-limit-and-who-shares-it)).

The launcher accepts `--key-status` without `--free-only`, because the command cannot spend; it still refuses any key
prefix (`sk-or-`, `gsk_`, `cfat_`, `cfut_`, `cfk_`) and `--api-key` in the arguments. Adding `--key-status` to any run line (step 6) works too: `run.py` then only reads
the key and names the flags it skipped. Without the launcher, `python tools/local-qual/run.py --key-status
--api-key-env OPENROUTER_API_KEY` does the same; `--base-url` defaults to OpenRouter's API for an `sk-or-` key, and
any other key needs `--base-url`.

| Exit | Meaning | What to do |
| --- | --- | --- |
| 0 | The report printed | Expect `credit limit: 0 USD` (step 3), `management key: no` and `free-only runs: accepted`. |
| 2 | Refused before sending (a flag) | Read the message; it names the flag to change. |
| 3 | No answer, or HTTP 5xx | Check the network connection; try again in a few minutes. |
| 5 | HTTP 401 or 403 (the key is revoked, expired, deleted or mistyped, or may not read its record); HTTP 404, a redirect, or a body that is not a key record | 401 or 403: create a new key (step 3) and store it with `set-openrouter-key.ps1 -Force`. Otherwise check `--base-url`. |
| 10 | HTTP 429 | Wait a minute and run it again; see [HTTP 429](#http-429-which-limit-and-who-shares-it). |

## 6. Dry run (sends nothing)

`run-cloud.ps1` decrypts the key into the environment of the one `python run.py` process it starts (variable
`OPENROUTER_API_KEY`), never into your PowerShell session, a command line, a file or the console. It passes every
other argument to `run.py` and adds `--api-key-env` itself. It refuses to run without `--free-only` (or `--key-status`,
step 5), refuses any argument containing a key prefix of any provider (`sk-or-`, `gsk_`, `cfat_`, `cfut_`, `cfk_`),
`--api-key`, or a key stored for another provider in the same folder, and refuses a key file readable by anyone else or
holding anything but a DPAPI blob. Pass JSON as a file
(`--extra-body @file.json`): quotes do not survive `powershell -File`. Name the output file with `--output` (the same
option as `run.py`'s `--out`): `powershell -File` reads `--out` as an abbreviation of its own `-OutVariable` and
`-OutBuffer` and stops with "the parameter name 'out' is ambiguous" before the launcher starts.

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 ^
  --backend openai --free-only --base-url https://openrouter.ai/api/v1 ^
  --model qwen/qwen3.8-27b:free --reasoning none --drop-params seed ^
  --extra-body @tools/local-qual/cloud/provider-zdr.json ^
  --ledger tools/local-qual/results/free-ledger.jsonl ^
  --suite pick --items PW01 --k 1 --dry-run
```

(`^` continues a line in cmd; in PowerShell end the line with a backtick instead, or write it on one line.) It
prints the request with `provider.require_parameters: true` and `allow_fallbacks: false`, and a worst case of
0 USD.

## 7. First run: one request

Drop `--dry-run` and run the same line. It uses one of the day's requests. At start the tool prints the key check
(credit limit, usage, today's free requests), the model's canonical slug and the pinned endpoint. After the call it
prints the key check at the end. This first call also settles several points that OpenRouter does not document:
whether a $0 key limit allows free calls, the exact `model` string a `:free` response carries, `usage.cost: 0` on
free models, and whether Qwen 3.8 routes a strict schema, since it lists structured outputs but not `response_format`.

| Exit | Meaning | What to do |
| --- | --- | --- |
| 0 | Done | Look at the record (below), then run a small battery. |
| 2 | Refused before anything was sent (a flag), or some calls failed | Read the message; it names the flag to change. |
| 4 | HTTP 402 | A $0 key limit blocks free calls, or the balance is negative. See step 3. |
| 5 | Configuration: the key check, 404 "no endpoints" (privacy settings, ZDR, a guardrail), a missing parameter, or another free run holds `%LOCALAPPDATA%\plotroom-dev\free-run.lock` | The message names the fix, for example `--drop-params seed` or `--schema-mode none`. Delete the lock only when no other run is active. |
| 7 | Reasoning on an effort-none call, or the canary failed | For a model that always reasons, use `--reasoning low` and a larger `--num-predict`. |
| 9 | **Free-only guard:** the model is not free now, a response was charged or came from another model, or the key's usage rose (during the run, or since the ledger's last reading) | Stop. Check the account's Activity page. If a charge is there, revoke the key (step 10) and start again with a new key and a new ledger. A ledger with any spend refuses further runs. If a free response named its model differently (for example without `:free`) at `usage.cost` 0, report the record: the check is deliberately strict. |
| 10 | The day's allowance is used up, or 429s held | Run the same command with `--resume` after the time printed (00:00 UTC). [HTTP 429](#http-429-which-limit-and-who-shares-it) tells the kinds apart. |

## 8. Daily routine

- Use **one ledger for every free run** (`--ledger tools/local-qual/results/free-ledger.jsonl`): the daily quota is
  per account, and the ledger is how runs share the count and the key's last reading. Free runs go one at a time:
  a second one, on any ledger, stops with exit 5 while the first holds `free-run.lock`.
- At 50 a day, plan about 45 calls: a one-item canary per new model, then one `--k 1` pass of a 30-item suite for
  one model. With the 1,000 tier, raise `--max-requests-per-day`; the account's own remaining count still applies.
- Stopped with exit 10? Run the same command with `--resume` on the next UTC day. Done calls are skipped, and the
  catalogue and key are checked again first.

Candidate models on 2026-09-27 (each has one free endpoint; the list changes without notice):

| Model | Tier | Flags it needs | Notes |
| --- | --- | --- | --- |
| `qwen/qwen3.8-27b:free` | 0 | `--drop-params seed` | Strict schema listed; no seed; reasons by default (efforts low, medium, xhigh). |
| `google/gemma-4-26b-a4b-it:free`, `google/gemma-4-31b-it:free` | 1 | arms without a response schema only | JSON mode only, no strict schema: Pick and Fill with `--schema-mode none`, the open and labels arms, and knowledge run; strict arms are refused before sending. Seed supported. |
| `dots-studio/dots-3-note-preview:free` | 1 | `--drop-params seed` | Strict schema. A preview: no removal date was listed at the last read, but every start reads `expiration_date` again. |
| `nvidia/nemotron-3-super-120b-a12b:free` | 2 | none | Strict schema, seed; reasons by default (efforts low, medium). |
| `liquid/lfm-2.5-2.6b:free` | 2 | `--reasoning low` | The small-model floor; reasoning is mandatory. |

## 9. Reading the results

Records go to `--output` (default `tools/local-qual/results/...`, git-ignored) and score with `score.py` as usual. Free
records add `free_only`, `canonical_slug`, `endpoint_tag`, `endpoint_name`, `provider_pin`, `endpoint_params`,
`key_start` (non-secret key fields), `free_daily_start`, and `rate_gate` (`attempts_today`, `requests_left_today`,
`rate_wait_s`). `cost_usd` is 0 on every call. The ledger's `budget_event` rows (`reserve` before each attempt,
`key` with each reading of the key's usage and the daily counter, `stop` with its reason) are the audit trail;
`score.py` and `--resume` skip them.

## 10. Revoking

- In the OpenRouter dashboard, **delete the key** (Settings → API Keys). This is what makes it useless everywhere.
- Then delete the local copy:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\remove-openrouter-key.ps1
```

- Revoke at once if the key ever showed up somewhere it should not (a screenshot, a log, a chat), or if a run ever
  ended with exit 9 and the Activity page shows a charge.

## HTTP 429: which limit, and who shares it

A 429 is not always about your account. The error body tells the four kinds apart (the run records keep it in
`error`; `--key-status` shows today's counter at no quota, step 5). The texts below are OpenRouter's error messages
as this project's own runs received them (doc 52, including its 2026-09-28 re-check) and as public bug reports quote
them (`rate_gate.py` lists those); OpenRouter's pages do not document them, so they can change:

| The error body contains | What it means | What to do |
| --- | --- | --- |
| `temporarily rate-limited upstream`, with `provider_name` (and, since 2026-09-28, `limit_source: upstream_provider_shared_pool`) in the error's metadata | The provider serving that free model is congested (doc 52 saw two machines on two networks refused alike). Not your fault, and not your account's limit; another machine does not help. | Route to another model, or wait and try later. The tool honours `Retry-After`; three 429s in a row end the run (exit 10). |
| `free-models-per-min` | More than 20 free-model requests in one minute on the account. | Back off; send no parallel bursts. The tool keeps 18 a minute and one free run at a time on this Windows user, but other projects and machines on the account add to the same count. |
| `free-models-per-day` | The account's daily cap (50 a day, or 1,000 after 10 credits were ever bought). | Wait for the reset at 00:00 UTC, then `--resume`. The tool stops at once (exit 10) and prints the time. |
| No OpenRouter JSON at all: an HTML page "Error 1015 … You are being rate limited", or (with `Accept: application/json`) JSON with `"cloudflare_error": true`, `"error_code": 1015`, `"error_name": "rate_limited"`; `Server: cloudflare` and `CF-RAY` headers, but no `X-RateLimit-*` headers and no `provider_name` | Cloudflare, in front of OpenRouter, is rate-limiting your network's address before OpenRouter sees the request: your own bursts, or a shared ISP address, VPN or proxy. The only 429 that depends on the machine or network rather than the account. A site owner may replace Cloudflare's body with its own (any 400–499 status, JSON allowed), so the missing `X-RateLimit-*` headers and provider metadata are the dependable tell (inference). | Stop sending, wait at least `Retry-After` (30 s by default), then resume slowly: repeated tries can extend the block. A 429 on a request with no key at all (`https://openrouter.ai/api/v1/models`) confirms it; another network (a phone hotspot) should work. If it persists at low volume, send OpenRouter support the `CF-RAY` values and UTC times. |

**The free limits are per account** ([limits](https://openrouter.ai/docs/api_reference/limits)): every key and every
machine on the account shares the same per-minute and daily counts, so a burst from another project on this account
can use up this setup's allowance, and more keys do not raise the limits. **Nothing in this setup binds the key to a
machine or an address:** the tool sends it as a bearer token in the `Authorization` header (`cloud_backend.py`) and the
runbook sets up no restriction, so treat the key as usable by whoever holds it (revoke it at once if it leaks, step
10). **The stored copy is bound:** the DPAPI file decrypts only for your Windows user on this machine (step 4), so a second
computer runs `set-openrouter-key.ps1` again. Prefer **one key per machine or project**: each key has its own credit
limit, can be revoked alone (step 10), and reports its own usage in its key record (`--key-status`). The free limits
stay shared across them.

## Limits of this setup

- **Windows only.** The key scripts use DPAPI. On Linux or macOS, keep the key in the system keychain and export it
  only into the one command's environment; `run.py`'s guards are the same.
- **One free run at a time per Windows user.** The lock sits beside the key store, so runs from another Windows user
  or another machine on the same account do not see it; the account's own counter (re-read at every key poll) and
  OpenRouter's own daily cap still stop them. A run killed hard leaves the lock behind (exit 5 until you delete it).
- **The per-response check sees a charge after the call that caused it.** On a key with a credit limit of 0 that
  call cannot be charged; with headroom allowed, at most one call's price can be. A charge no response shows is
  caught by the next key reading, at the latest at the next start on the same ledger. A new ledger has no earlier
  reading to compare with.
- **Privacy is set on the account**, not by the tool. The tool sends only synthetic items, and the tier is your
  choice.
- **`provider.max_price` with zeros** is accepted in `--extra-body` as an extra guard. OpenRouter documents that
  `max_price` stops a request from running when no endpoint meets it, but not how it treats a bound of 0; test it
  with one request before relying on it.
- **The plaintext key exists in memory during a run**, in the launcher and in `run.py` (.NET and Python strings
  cannot be wiped). DPAPI protects the stored file from other Windows users and other machines, not from programs
  running as you.

## Groq: free plan

`--provider groq` runs the suites on Groq's Free plan. Groq has no key record and no cost field, so the guarantee that
nothing is billed rests on the organisation staying on the Free plan; the tool checks every reply's limit headers
against that plan and keeps the plan's limits on the client side. Facts below were read on 2026-09-28.

**G1. The organisation.** Sign in at <https://console.groq.com> (Groq's terms require you to be 18 or older). Stay on
the Free plan: add **no payment method** and do not upgrade. Upgrading to the Developer tier needs a card, a US bank
account or a SEPA debit account, and only then can usage be billed; spend limits exist only on paid plans. If this
organisation carries other work, create a separate one for these synthetic tests (limits count per organisation).

**G2. Data controls.** Settings → Data Controls (<https://console.groq.com/settings/data-controls>), as an organisation
admin: turn **Zero Data Retention** on. By default Groq keeps no inference data, but may log inputs and outputs for up
to 30 days when troubleshooting errors or investigating abuse; with ZDR on it keeps none (batch and fine-tuning are then
off, which the tool does not use). Groq's services agreement does not let it train on inputs or outputs.

**G3. Check the limits.** Settings → Limits (<https://console.groq.com/settings/limits>) should show, for each model
below, 30 requests a minute, 1K a day, 8K tokens a minute and 200K tokens a day. Higher figures mean a paid tier: stop
and tell us before any run.

**G4 (optional). A project.** Create a project (for example `plotroom-local-qual`) and select it before creating the key:
keys belong to the project that is selected, and a project's limits can be set at or below the organisation's.

**G5. The key.** Turn off Windows' clipboard sync first (Settings → System → Clipboard → "Sync across your devices").
Then <https://console.groq.com/keys> → Create API Key, named for example `plotroom-local-qual-2026-09`. It is shown once:
copy it straight into G6.

**G6. Store it.**

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\set-groq-key.ps1
```

Hidden input; the key must start with `gsk_` followed by letters and digits. It is DPAPI-encrypted for your Windows
user in `%LOCALAPPDATA%\plotroom-dev\secrets\groq.key` with a user-only access list, as in step 4. Afterwards copy
something else over the clipboard and delete the key's entry from clipboard history (Win+V) if that is on.

**G7. Check it (no model runs, no tokens used).**

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --provider groq --key-status
```

One `GET https://api.groq.com/openai/v1/models` with the key. It prints `key: accepted`, each model of the free-plan
table as listed or not (active, context window, output cap), the reply's `x-ratelimit-*` headers, and whether they show
the Free plan. Whether Groq counts this read as a request is not documented; the first check will show whether it
carries the headers. Exit codes as in step 5: 0 report, 2 refused before sending, 3 no answer or 5xx, 5 the key or the
URL is wrong (401: create a new key and store it with `set-groq-key.ps1 -Force`), 10 a 429.

**G8. Dry run, then one request.**

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 ^
  --provider groq --model openai/gpt-oss-20b --reasoning low ^
  --ledger tools/local-qual/results/groq-ledger.jsonl ^
  --suite pick --items PW01 --k 1 --dry-run
```

The dry run prints the body without sending: `max_completion_tokens`, `reasoning_effort`, a strict-mode schema copy.
Drop `--dry-run` for the first real request. Its record settles what Groq's pages leave open: the `model` string of a
reply, the headers on a chat reply, and whether the strict schema is honoured (`schema_conformant`).

**What the guard does** (`providers.py`, `provider_gate.py`):

| Rule | Default | Why |
| --- | --- | --- |
| Model must be in `cloud/groq-free-limits.json` | the four below | Only models whose free limits were read are run; the table carries its source and date |
| Requests in any 60 s, per model | 28 (plan: 30) | A burst over it costs a 429 and a retry; the gate waits for room |
| Tokens in any 60 s, per model | 7,500 (plan: 8,000) | Prompt estimate plus the output cap reserved before sending, the reply's usage after; the reply's `x-ratelimit-remaining-tokens` is honoured too |
| Requests in any 24 hours, per model | 950 (plan: 1,000) | How Groq resets its day is not documented, so the last 24 hours count, never looser than a calendar day |
| Tokens in any 24 hours, per model | 190,000 (plan: 200,000) | No header reports tokens per day, so the ledger counts them |
| Groq's own requests left today | stop at 5 | `x-ratelimit-remaining-requests` less `--daily-reserve` |
| Limit headers above the Free plan, a reported cost, another model answering | exit 9 | The only live signs that the organisation could be billed |
| 429 naming a per-day limit (RPD, TPD) | exit 10 | Terminal; the resume time is printed. RPM or TPM: wait `retry-after` and retry |

Flags: `--rpm`, `--max-requests-per-day`, `--max-tokens-per-minute`, `--max-tokens-per-day` (never above the plan's
figures), `--daily-reserve`, `--max-consecutive-429`. Use one `--ledger` for every Groq run: the counts are per model and
organisation, and the ledger is how runs share them. One Groq run at a time per Windows user (`groq-run.lock` beside the
key store; delete it only when no run is active). Records add `provider`, `provider_caps`, `provider_table` and, per
call, `rate_gate` (requests and tokens in the minute and the last 24 hours, the server's counts left).

| Model | Flags it needs | Notes |
| --- | --- | --- |
| `openai/gpt-oss-20b`, `openai/gpt-oss-120b` | `--reasoning low` (or medium, high) | Production models; they always reason, so `--reasoning none` is refused; strict schema |
| `qwen/qwen3.8-27b` | `--reasoning none` works | Preview (may be removed at short notice); strict schema; efforts none, low, medium, high (sent with `reasoning_format: parsed`) |
| `openai/gpt-oss-safeguard-20b` | `--schema-mode none` | Preview; best-effort JSON only, so strict arms are refused |

The request follows Groq's OpenAI-compatible rules: `max_completion_tokens`, `reasoning_effort` instead of OpenRouter's
`reasoning` object, a strict-mode schema copy (every property required, `additionalProperties: false`; answers are still
checked against the suite's own schema), no `top_k`, `min_p` or `--repeat-penalty` (refused: Groq does not document
them), never `logprobs`, `n` or `messages[].name` (400 on Groq). A temperature of 0 becomes 1e-8 on Groq's side.

**Revoking.** Delete the key at <https://console.groq.com/keys>, then
`powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\remove-groq-key.ps1`. Revoke at once if the
key ever appears in a screenshot, log or chat.

## Cloudflare Workers AI: daily free allocation

`--provider cloudflare` runs the suites within Workers AI's free allocation of 10,000 neurons a day (reset at 00:00 UTC).
Replies carry no neuron or cost figure, so the tool computes each call's neurons from its usage and a dated table
(`cloud/cloudflare-neurons.json`), reserves every call's worst case before sending, and stops below the day's cap.
Facts below were read on 2026-09-28.

**C1. The plan.** Sign in at <https://dash.cloudflare.com> and keep the account on **Workers Free**; do not subscribe to
Workers Paid. On Workers Free, calls past the allocation fail (error 3036). On Workers Paid every neuron past it is billed
($0.011 per 1,000) and we found no spend cap: there the tool's own count is the only guard. If the account already has
Workers Paid, tell us before any run.

**C2. The account id.** Account home → Search (Ctrl+K) → "Copy account ID" (or Workers & Pages → Account details). It is
not a password, but it names your account: never paste it into chat, an issue or the repository. The store script asks
for it with hidden input.

**C3. A least-privilege token.** Manage account → Account API tokens → Create Token → Custom token. Name it, for example,
`plotroom-local-qual-2026-09`. Permissions: **Account · Workers AI · Read**, nothing else; account resources: this
account only; optionally Client IP Address Filtering for your address; TTL: an end date a few weeks out. Copy the token
once (it starts with `cfat_`), with clipboard sync off. Never use the Global API Key (`cfk_`: full access to the whole
account); the scripts and `run.py` refuse it, and a legacy token without a prefix. If the first key check or the first
request answers 403, edit the token and add Account · Workers AI · Edit (Cloudflare's REST guide names Read and Edit; the
API reference accepts either). A user token (My Profile → API Tokens, `cfut_`) with the same permission works too.

**C4. Store both.**

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\set-cloudflare-token.ps1
```

It asks for the account id, then the token, both with hidden input, and writes `cloudflare.key` and
`cloudflare-account.key` (DPAPI blobs, user-only access) in `%LOCALAPPDATA%\plotroom-dev\secrets`. `run-cloud.ps1
--provider cloudflare` decrypts both into the environment of the one `run.py` process (`CLOUDFLARE_API_TOKEN`,
`CLOUDFLARE_ACCOUNT_ID`); the id never enters a command line, and every record, ledger row and console line has it
replaced by `[ACCOUNT]`. Clear the clipboard afterwards as in G6.

**C5. Check it (no neurons used).**

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --provider cloudflare --key-status
```

It verifies the token (`GET /client/v4/accounts/<id>/tokens/verify` for an account token, `/user/tokens/verify` for a
user token), then searches the account's Workers AI models once per table model. It prints the token's status and
expiry, whether the account is reachable, which table models are listed, and the day's allocation. No model runs; each
read counts toward Cloudflare's general limit of 1,200 API requests per five minutes. 403 names the missing permission
(C3); 401 or an expired token: create a new one and store it with `set-cloudflare-token.ps1 -Force`.

**C6. Dry run, then one request.** In PowerShell keep the model id in double quotes (a leading `@` is PowerShell's
splatting sign); cmd passes it either way.

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 ^
  --provider cloudflare --model "@cf/google/gemma-4-26b-a4b-it" --reasoning none ^
  --ledger tools/local-qual/results/cloudflare-ledger.jsonl ^
  --suite pick --items PW01 --k 1 --dry-run
```

Drop `--dry-run` for the first request. Its record settles what the pages leave open: whether Workers AI Read alone may
run a chat completion, whether the model honours the JSON schema (`schema_conformant`; Workers AI "can't guarantee" it,
and the canary stops a run whose answers do not conform), and the error body shape. For models that reason
(`gpt-oss`, Qwen3.8) the tool sends `reasoning_effort`; the first request shows whether that field is taken.

**What the guard does:**

| Rule | Default | Why |
| --- | --- | --- |
| Model must be in `cloud/cloudflare-neurons.json` | 8 models | No rate, no worst case; the table carries its source and date |
| Neurons per UTC day, every model of the account | 9,000 (allocation: 10,000) | `--max-neurons-per-day`, never above the allocation; worst case (prompt estimate × in-rate + output cap × out-rate, per million tokens) reserved before sending, the reply's usage priced after |
| A reply priced above its worst case | exit 4 (CostAnomaly) | The table or the output cap does not hold; on Workers Paid the excess would be billed |
| 3036 (the day's allocation is used up) | exit 10 | Terminal until 00:00 UTC (community reports say it can linger after the reset: do not loop on it) |
| 3040 (capacity) | retried | Back off, then retry |
| 5035, 5016, 3023 (paid-only model, model terms, account blocked) | exit 5 | Configuration: the message names it |
| Requests a minute | 60 (limit: 300) | `--rpm`; whether Cloudflare counts per account or per model is not documented |

Use one `--ledger` for every Cloudflare run; one run at a time per Windows user (`cloudflare-run.lock`). After each
testing day, compare the Workers AI page's neurons with the tool's count (every run prints the day's count at its end,
and every record carries it in `rate_gate.neurons_today`). The request
always carries `max_tokens` (the default of 256 would silently cut answers); a seed of 0 goes as 1 (the range starts at
1); `min_p` and `--repeat-penalty` are refused (not documented there).

| Model | In / out neurons per million tokens | `--reasoning` |
| --- | --- | --- |
| `@cf/google/gemma-4-26b-a4b-it` | 9,091 / 27,273 | none (nothing is sent; a reply that reasons stops the run, exit 7) |
| `@cf/openai/gpt-oss-20b`, `@cf/openai/gpt-oss-120b` | 18,182 / 27,273; 31,818 / 68,182 | low, medium or high |
| `@cf/qwen/qwen3.8-27b` | 40,909 / 290,909 | low, medium or xhigh (reasoning dominates its cost) |
| `@cf/zai-org/glm-4.7-flash`, `@cf/ibm-granite/granite-4.0-h-micro` | 5,500 / 36,400; 1,542 / 10,158 | none |
| `@cf/mistralai/mistral-small-3.1-24b-instruct`, `@cf/qwen/qwen3-30b-a3b-fp8` | 31,876 / 50,488; 4,625 / 30,475 | none |

Worked examples: a Gemma 4 call of 2,300 tokens in and 300 out is about 29 neurons; a Qwen3.8 call of 2,000 in and 2,000
out about 664.

**Data use.** Cloudflare does not use your content to train models on Workers AI or to improve its services without your
explicit consent, and stores it only if you use a storage service with it.

**Revoking.** Delete the token under Account API tokens (or My Profile → API Tokens), then
`powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\remove-cloudflare-token.ps1` (both files).
Cloudflare also revokes a `cfat_` or `cfut_` token found in a public GitHub repository.

## Groq, Cloudflare and D047

Both providers' terms carry violence wording (Groq's acceptable-use policy lists "violence, violent extremism or
terrorism"; Cloudflare's developer-platform terms name content that "incites or exploits violence"). Under D047 item 3,
until suite items carry their own flag, `run.py` refuses the text and knowledge suites for both (doc 50 §5.9 reads them
as combat-flavoured): only pick, pick-hard, fill and explain run there, and only the synthetic items in `suites/`. Before
any military-themed item goes to either host, decide whether to ask them in writing (Groq's exception route; Cloudflare
has none we found): that is the pending outreach of OWQ-24.

## Sources (read 2026-09-27)

- Limits (20 requests per minute; 50 or 1,000 a day by lifetime credits; per account, more keys do not raise them;
  402 on a negative balance): <https://openrouter.ai/docs/api_reference/limits>
- Key record (`GET /api/v1/key`: `limit`, `limit_remaining`, `limit_reset`, `usage`, `usage_daily`, `byok_usage`,
  `is_free_tier`, `is_management_key`, `free_model_daily_requests` with its reset at UTC midnight, `rate_limit`, and
  the `label`): <https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key>
- Observed, not documented (this project's runs, [doc 52](../../../docs/research/52-rate-limits-and-ux.md) and its
  re-check of 2026-09-28): the 429 bodies and their `limit_source`; `rate_limit` reading `-1` requests per 10 s; the
  daily counter reading 0 before and after an answered free call.
- Free endpoints and privacy toggles, the 404 message, ZDR, strictest setting wins (updated 2026-09-23):
  <https://openrouter.zendesk.com/hc/en-us/articles/51690904755227>
- `openrouter/auto:free` can bill paid models: <https://openrouter.zendesk.com/hc/en-us/articles/51679572756123>
- Charges on free models from file and PDF parsing: <https://openrouter.zendesk.com/hc/en-us/articles/51678714631323>
- Provider selection (`require_parameters`, `allow_fallbacks`, `zdr`, `data_collection`, `max_price`):
  <https://openrouter.ai/docs/guides/routing/provider-selection>
- Zero Data Retention and the ZDR endpoint list: <https://openrouter.ai/docs/guides/features/zdr>
- Usage accounting (`usage.cost` is the amount charged, and full usage is always included; the old
  `usage: {include: true}` parameter has no effect): <https://openrouter.ai/docs/guides/guides/usage-accounting>
- Input & Output Logging (Settings → Observability; kept at least 3 months) and the separate use-of-inputs/outputs
  setting (Settings → Privacy): <https://openrouter.ai/docs/guides/features/input-output-logging>
- Guardrails (allowlists, Eligibility Preview): <https://openrouter.ai/docs/guides/features/guardrails>
- Live catalogue (keyless): <https://openrouter.ai/api/v1/models> and
  <https://openrouter.ai/api/v1/models/qwen/qwen3.8-27b:free/endpoints>
- `X-RateLimit-Reset` in epoch milliseconds (third-party report): <https://github.com/BerriAI/litellm/issues/9035>
- Cloudflare's edge 429 (read 2026-09-28): error 1015 means the site's rate-limiting rules blocked the visitor, and repeated
  tries may extend the block (<https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1015/>);
  HTML by default, JSON with `error_code`, `error_name`, `cloudflare_error`, `ray_id` and `retry_after` when the client asks
  for `application/json`, and 30 s `Retry-After` for 1015 (<https://developers.cloudflare.com/fundamentals/reference/error-responses/>);
  429 is the default status of a rate-limiting rule (<https://developers.cloudflare.com/waf/rate-limiting-rules/parameters/>).

## Sources for Groq and Cloudflare (read 2026-09-28)

Read through a summarising fetch; the quotes above were checked against the pages' wording as returned. Re-read a page
before relying on a figure that matters: Cloudflare's developer-platform terms were updated on the day of reading.

- Groq, OpenAI compatibility (base URL; `logprobs`, `logit_bias`, `top_logprobs` and `messages[].name` return 400; `n`
  must be 1; temperature 0 becomes 1e-8): <https://console.groq.com/docs/openai>; API reference (`max_completion_tokens`,
  `GET /openai/v1/models`): <https://console.groq.com/docs/api-reference>
- Groq, rate limits (30 requests and 8K tokens a minute, 1K requests and 200K tokens a day per model on the Free plan;
  per organisation; the `x-ratelimit-*` headers, requests per day and tokens per minute; `retry-after` on a 429):
  <https://console.groq.com/docs/rate-limits>; models (production and preview): <https://console.groq.com/docs/models>
- Groq, reasoning (`reasoning_effort`; Qwen3.8's `reasoning_format`, `raw` refused in JSON mode):
  <https://console.groq.com/docs/reasoning>; structured outputs (strict mode's rules; gpt-oss-safeguard-20b best effort):
  <https://console.groq.com/docs/structured-outputs>
- Groq, billing and spend limits (a payment method and an upgrade before any bill; spend limits on paid plans only):
  <https://console.groq.com/docs/billing-faqs>, <https://console.groq.com/docs/spend-limits>; data (no retention by
  default, logs up to 30 days for troubleshooting or abuse, ZDR): <https://console.groq.com/docs/your-data>; acceptable
  use: <https://console.groq.com/docs/legal/ai-policy>; the 18+ rule and no training on inputs or outputs:
  <https://console.groq.com/docs/legal/services-agreement>
- Groq's 429 message naming the window and the organisation (third-party quotes; Groq does not document the body):
  <https://theneuralbase.com/groq/errors/groq-rate-limit-requests-per-day-exceeded/>; the `gsk_` prefix (secret
  scanners; not in Groq's docs): <https://github.com/secretlint/secretlint/issues/1446>
- Cloudflare Workers AI, OpenAI compatibility (`<root>/accounts/<account id>/ai/v1`, bearer token):
  <https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/>; pricing (10,000 neurons a day
  free, reset at 00:00 UTC; the neuron rates; $0.011 per 1,000 on Workers Paid):
  <https://developers.cloudflare.com/workers-ai/platform/pricing/>; limits (300 requests a minute for text generation):
  <https://developers.cloudflare.com/workers-ai/platform/limits/>; errors (3036, 3040, 5035, 5016, 3023):
  <https://developers.cloudflare.com/workers-ai/platform/errors/>; JSON mode (not guaranteed; no streaming):
  <https://developers.cloudflare.com/workers-ai/features/json-mode/>
- Cloudflare tokens: formats (`cfat_`, `cfut_`, `cfk_`; leaked tokens revoked):
  <https://developers.cloudflare.com/fundamentals/api/get-started/token-formats/>; creating one:
  <https://developers.cloudflare.com/fundamentals/api/get-started/create-token/>; token verify (account and user):
  <https://developers.cloudflare.com/api/resources/accounts/subresources/tokens/methods/verify/> and
  <https://developers.cloudflare.com/api/resources/user/subresources/tokens/methods/verify/>; model search (Workers AI
  Read or Write): <https://developers.cloudflare.com/api/resources/ai/subresources/models/methods/list/>; the account id:
  <https://developers.cloudflare.com/fundamentals/account/find-account-and-zone-ids/>; API limits (1,200 requests per five
  minutes): <https://developers.cloudflare.com/fundamentals/api/reference/limits/>
- Cloudflare data use: <https://developers.cloudflare.com/workers-ai/platform/data-usage/>; developer-platform terms:
  <https://www.cloudflare.com/service-specific-terms-developer-platform/>
