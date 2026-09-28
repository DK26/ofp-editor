# Safe free-model testing on OpenRouter

This is the runbook for the account owner. It covers running the local-qual suites against OpenRouter's **free**
model variants (ids ending in `:free`) with no way to spend money, a key that never sits in plaintext, and the free
tier's rate limits kept on the client side. It sets up an account, a key and a Windows machine for the first round.
All facts below were read on **2026-09-27**; OpenRouter changes its free catalogue without notice, so the tool
re-checks them on every start.

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

## 5. Dry run (sends nothing)

`run-cloud.ps1` decrypts the key into the environment of the one `python run.py` process it starts (variable
`OPENROUTER_API_KEY`), never into your PowerShell session, a command line, a file or the console. It passes every
other argument to `run.py` and adds `--api-key-env` itself. It refuses to run without `--free-only`, refuses any
argument containing `sk-or-` or `--api-key`, and refuses a key file readable by anyone else or holding anything but
a DPAPI blob. Pass JSON as a file
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

## 6. First run: one request

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
| 9 | **Free-only guard:** the model is not free now, a response was charged or came from another model, or the key's usage rose (during the run, or since the ledger's last reading) | Stop. Check the account's Activity page. If a charge is there, revoke the key (step 9) and start again with a new key and a new ledger. A ledger with any spend refuses further runs. If a free response named its model differently (for example without `:free`) at `usage.cost` 0, report the record: the check is deliberately strict. |
| 10 | The day's allowance is used up, or 429s held | Run the same command with `--resume` after the time printed (00:00 UTC). |

## 7. Daily routine

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

## 8. Reading the results

Records go to `--output` (default `tools/local-qual/results/...`, git-ignored) and score with `score.py` as usual. Free
records add `free_only`, `canonical_slug`, `endpoint_tag`, `endpoint_name`, `provider_pin`, `endpoint_params`,
`key_start` (non-secret key fields), `free_daily_start`, and `rate_gate` (`attempts_today`, `requests_left_today`,
`rate_wait_s`). `cost_usd` is 0 on every call. The ledger's `budget_event` rows (`reserve` before each attempt,
`key` with each reading of the key's usage and the daily counter, `stop` with its reason) are the audit trail;
`score.py` and `--resume` skip them.

## 9. Revoking

- In the OpenRouter dashboard, **delete the key** (Settings → API Keys). This is what makes it useless everywhere.
- Then delete the local copy:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\remove-openrouter-key.ps1
```

- Revoke at once if the key ever showed up somewhere it should not (a screenshot, a log, a chat), or if a run ever
  ended with exit 9 and the Activity page shows a charge.

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

## Sources (read 2026-09-27)

- Limits (20 requests per minute; 50 or 1,000 a day by lifetime credits; per account; 402 on a negative balance):
  <https://openrouter.ai/docs/api_reference/limits>
- Key record (`GET /api/v1/key`, `free_model_daily_requests`, reset at UTC midnight):
  <https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key>
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
