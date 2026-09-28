# Cloud screening, round 1 (D044)

Research doc 54 for Plotroom (`ofp-editor`). Run dates: 2026-09-27, 22:18–23:30 UTC (E01–E11), and 2026-09-28, 06:08–06:54 UTC
(E12–E14). Audience: the owner, contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: which local model candidates the owner's cloud-first rule ([D044](../decisions/D044-cloud-first-model-screening.md))
promotes to a local trial, for which step kinds; whether hosted copies of the same weights behave like the local records; what doc 50
§5.6's proposed promotion rule does when it meets real data; and what the round cost.

**Status.** Measurements are **[V]**. Verdicts, the rule changes in §3.3 and the notes on records in §5 are proposals **[I]**.
13 of 14 endpoints ran in full; one (E10) is partial after a false guard stop (§4.3). This is the first screening round under D044
(battery S of doc 50 §5.2). It is not doc 48's "round 1" (the uplift ladder and the frontier comparators), which stays deferred.
**Epistemic legend.** **[V]** measured in this round (re-derived from the call records, `score.py` output, the grade files, the
significance and spend outputs, or keyless reads of OpenRouter's endpoint lists). **[V per doc N]** taken from a sibling doc. **[I]**
our inference, arithmetic or proposal. **[U]** unknown.
**Data.** [`data/cloud-screening-results.csv`](data/cloud-screening-results.csv), 2,231 rows (columns `model, provider, precision,
suite, condition, metric, value, n, cost_usd, notes`): setup and pins per endpoint, scores per arm on the 29 shared harder menus (and
the as-run 30-menu figures), the local comparators re-scored on the same menus, every paired test (`model` = `A vs B`, family in
`notes`), the promotion checks and verdicts (`suite` = `promotion`) and the spend audit (`suite` = `spend`). `cost_usd` is the
provider-billed figure (the sum of each response's `usage.cost`). Raw call records, grade files, the plan and the run logs stay
local, as in docs 44, 46 and 49.
**Relation to sibling docs.** Doc 50 §5 planned this round (battery S, endpoints, the promotion rule); D044 records the owner's rule
and its amendment (OWQ-26, OWQ-27); doc 48 supplied the cloud tooling plan and the token profile; docs 44, 46 and 49 are the local
records every arm pairs with; doc 47 lists the candidates; D045, D046 and D047 govern free presets, aggregator safeguards and
military-use policies.
**Hygiene.** Only the repository's synthetic suites were sent: no user data, no mission files, no game content. Every suite item is
our own text; model answers are only paraphrased. No key, local path or user name appears here or in the CSV.

## TL;DR

- **What ran** [V]. 14 pinned OpenRouter endpoints (13 core and 1 optional) for 9 models, 3,501 calls, synthetic suites only. Every
  answered call (3,494) was served by the pinned host with the requested model, passed the strict schema and stopped normally.
  Thinking-off calls carried 0 reasoning tokens. Scoring uses the 29 harder menus that every arm, cloud and local, shares: menu HR03
  was dropped everywhere after 64 calls to E01–E11 had already been sent (§1.3).
- **No endpoint differs from the local default with statistical support** [V]. The default is Gemma 4 E4B QAT on llama.cpp (doc 46).
  Against it: 27 harder-menu tests, 13 Fill tests and 20 graded tests. Three have raw p < 0.05, none after Holm:
  - Ministral 3 3B, 0 : 9 menus without cards;
  - Qwen3-30B-A3B-2507 at SiliconFlow, 0 : 6 without cards;
  - Bonsai 2, 7 : 0 on graded text.

  No pair has more than 9 discordant items, and a 3 : 1 split needs 20 to reach p < 0.05. So this is "no detected difference", not
  equivalence. Without cards the default is right by majority on all 29 menus, so there only losses could show. With cards, the
  strongest endpoints gain the 3 menus it misses (3 : 0, p = 0.25).
- **Doc 50 §5.6's rule, applied as written, promotes nothing** [I on V]. Only Qwen3.5-35B-A3B passes every must-pass check on both
  hosts. The rule then both promotes it (+4 and +3 menus with cards) and drops it (whole-record Fill 9 and 8 of 12, below the
  offload bar of 10), and it says nothing about which clause wins. Four models are dropped by must-pass failures on both hosts, often
  a single stray call such as one false escape on menu HT03: Qwen3-30B-A3B-2507, Gemma 4 26B-A4B, Qwen3.6-35B-A3B and gpt-oss-20b.
  Bonsai 2, Qwen3.8-27B and Qwen3.5-9B end grey (one host each), and Ministral 3 3B is dropped. So the rule would also have dropped
  both offload files that doc 49 measured and proposes.
- **Proposed changes (§3.3) and their result** [I]. The changes: judge escapes by majority and for PICK only; judge offload models
  on FILL and EXPLAIN; promote only when both hosts agree; fix the precedence; re-base the bar on 29 menus. The result:
  - Qwen3-30B-A3B-2507 (FILL and EXPLAIN) and Gemma 4 26B-A4B (FILL) meet their offload roles on both hosts, matching doc 49's local
    records.
  - Qwen3.6-35B-A3B (two hosts) and Qwen3.5-9B (one host) earn EXPLAIN-only trials. Doc 49's Qwen3-30B-A3B-2507 file already passes
    10 of 10 locally, so neither download adds anything.
  - Qwen3.5-35B-A3B is dropped for the offload FILL role, and gpt-oss-20b for PICK (menu HM04 missed on both hosts).

  **Recommendation: no new local download from this round.**
- **Same weights, cloud against local: no measurable effect** [V]. 15 paired tests, at most 4 discordant items, smallest p = 0.5.
  The cloud copy is not always the optimistic bound, though:
  - Qwen3-30B-A3B-2507's two fp8 hosts got 30 of 36 Fill calls fully right, against 33 for the local Q4 file.
  - Gemma's non-QAT hosts missed the planted escape HA03 with cards, where the local QAT file caught it.
  - Ministral matched its Ollama record (Fill 5 of 12 records by majority on both).

  The same weights' cloud median harder-menu latency was 0.6–1.5 s, against 6.7–11.3 s for the local offload files.
- **Bonsai 2 with thinking off works** [V]. It returned 0 reasoning tokens and 100% schema-valid answers on 250 calls. By majority it
  got 28 of 29 harder menus in both conditions (pass^3 24 and 26), 11 of 12 Fill records (pass^3 10) and 10 of 10 explanations in
  both samples. Its graded text, 7 of 10, is the round's best.
  - **Against Qwen3.8-27B on the same host:** no detectable difference (5 tests, at most 2 discordant items). Bonsai 2 is 2–5 points
    lower per call on harder menus and slower (median 2.1 s against 1.3 s), at the same cost.
  - **Doc 48 §6.6's "down to skip" line** (10 points of pass^3) is crossed by a hair with cards: 26 against 29 menus is 10.3 points,
    which is noise at this size. It stays bring-your-own: its runtime is a fork.
- **Spend** [V].
  - **Billed:** $0.163, the sum of every response's `usage.cost`. The plan estimated $0.228, the stage cap is $0.90, and the key
    still has about $0.84 of its $1 limit.
  - **The tool's ledger shows $0.327** because its settle step counts every call twice: it adds `upstream_inference_cost`, which
    OpenRouter fills with the same bill on non-BYOK calls.
  - **The double count caused the round's only guard stop** (E10), a false positive. Fix it before the cloud backend lands (§4.2).
- **Not sent, and why** [V].
  - **The text arm** did not go to Mistral, Nebius, SiliconFlow or CoreWeave: their terms carry violence wording (D047, cautious
    reading).
  - **Explain and text** did not go to gpt-oss-20b (the plan screens PICK and FILL only).
  - **Not screened:**
    - Qwen3-4B-2507 and Granite 4.2-3B: Hugging Face router only;
    - the Featherless-only models, the default among them (no top-up, OWQ-27);
    - GLM-4.7-Flash: watch list first;
    - translation and non-English models: no suite yet;
    - models with no host (P5);
    - free routes;
    - the NVIDIA trial and Z.ai (D047).
- **Implications** [I].
  - **D023:** the provisional defaults and doc 49's offload proposal stand.
  - **D037:** gains nothing to recommend, because a screen never sets a badge.
  - **D045:** Qwen3.8-27B, the same weights as doc 50's preselected free model, screened at or above the default's pass^3 on every
    arm it ran (by majority it is one menu below without cards, 0 : 1). So the free route itself (ModelRun) is the first candidate to
    qualify per step kind, without the text arm (violence clause).
  - **The Model Manager** may show "screened in the cloud (endpoint, precision, date)" as a note, never as a badge.

## 1. Setup

### 1.1 What was sent, and to whom [V]

Every endpoint was read keyless from OpenRouter's `/models/<id>/endpoints` and `/endpoints/zdr` lists on 2026-09-27 (prices, status,
supported parameters) and checked again on 2026-09-28. Records are the final call records, including 7 error records that were later
resumed (§1.2).

| ID | Model (doc 47/50 role) | Endpoint, precision | USD/MTok in / out | ZDR | Reasoning sent | Arms not sent | Records | Billed USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E01 | Ministral 3 3B (calibration anchor) | `mistral/zdr`, undisclosed | 0.10 / 0.10 | yes | field omitted | text (policy) | 417 | 0.0106 |
| E02 | Qwen3-30B-A3B-Instruct-2507 (shortlist 2, offload) | `nebius/fp8` | 0.10 / 0.30 | yes | field omitted | text (policy) | 236 | 0.0100 |
| E03 | same | `siliconflow/fp8`, seed dropped | 0.09 / 0.30 | yes | field omitted | text (policy) | 236 | 0.0090 |
| E04 | Gemma 4 26B-A4B-it (shortlist 3, offload) | `coreweave/bf16`, non-QAT | 0.10 / 0.30 | yes | none | text (policy) | 238 | 0.0090 |
| E05 | same | `deepinfra/fp8`, non-QAT | 0.07 / 0.34 | yes | none | — | 256 | 0.0082 |
| E06 | Qwen3.5-35B-A3B (offload alternate) | `deepinfra/fp8` | 0.14 / 1.00 | yes | none | — | 256 | 0.0184 |
| E07 | same | `parasail/fp8` | 0.15 / 1.00 | yes | none | — | 256 | 0.0191 |
| E08 | Qwen3.6-35B-A3B (offload alternate) | `akashml/fp8` | 0.10 / 0.90 | yes | none | — | 256 | 0.0140 |
| E09 | same | `parasail/fp8` | 0.15 / 1.00 | yes | none | — | 256 | 0.0199 |
| E10 | gpt-oss-20b (watch) | `akashml/fp4` (native MXFP4) | 0.02 / 0.10 | yes | low (mandatory) | explain, text (plan); Fill not reached | 124 | 0.0017 |
| E11 | same | `deepinfra/bf16` | 0.03 / 0.14 | yes | low (mandatory) | explain, text (plan) | 220 | 0.0047 |
| E12 | Ternary Bonsai 2 27B (optional probe) | `darkbloom/int4` | 0.075 / 0.50 | no | none | — | 250 | 0.0113 |
| E13 | Qwen3.8-27B (Bonsai comparator) | `darkbloom/fp4` | 0.069 / 2.20 | no | none | — | 250 | 0.0176 |
| E14 | Qwen3.5-9B (optional; doc 14 T2a) | `deepinfra/bf16` | 0.10 / 0.15 | yes | none | — | 250 | 0.0098 |
| | **Total** | | | | | | **3,501** | **0.1633** |

- **Arms** (doc 50 §5.2): `pick-hard` without and with cards at k = 3, Fill at k = 3, Explain with cards and Text without cards at
  k = 2; a one-call preflight (menu HW01) opened each endpoint. E01 also ran the optional `pick` arms (k = 3, both conditions), its
  calibration pair with doc 44.
- **"Field omitted"**: neither the model nor the endpoint lists a reasoning parameter (Ministral; Qwen3-30B-A3B-2507 is
  non-thinking by design). **"none"** sends reasoning effort `none`; Qwen3.5 and 3.6 think by default, so this is their thinking
  switch. gpt-oss-20b cannot switch reasoning off, so it ran at effort `low` with a 1,024-token cap.
- **Text by policy** (D047 item 3, a cautious reading, not legal advice): Mistral's usage policy names "military and warfare";
  Nebius's AUP lists "the portrayal of violence" as illegal content; SiliconFlow bars "content promoting ... excessive violence";
  CoreWeave bars content that "incites or threatens violence". DeepInfra, Parasail, AkashML and Darkbloom have no violence wording
  (DeepInfra's "High-Risk Use" clause on "weapons systems" is about operation, not content). Terms were read on 2026-09-27; the URLs
  are in the CSV's setup rows.
- **Darkbloom** is not on OpenRouter's zero-data-retention list, so E12 and E13 carried no `zdr` flag; `data_collection: deny`
  stayed. Only synthetic suites went there (doc 48 §6.6).
- **Prices.** E13's live input price was $0.05 on 2026-09-28, below the plan's $0.069. The run kept the plan's row, so its caps and
  cost checks were conservative. Nebius (E02) was listed as degraded when the plan was built; its run had 0 errors and 0 retries.

### 1.2 Pins, caps and guards [V]

- **Request.** Every body carried `provider: {order: [tag], only: [tag], allow_fallbacks: false, require_parameters: true,
  data_collection: "deny", zdr: true}` (no `zdr` on Darkbloom), a strict JSON schema, the local records' seed (SiliconFlow lists no
  seed, so it was dropped there), the suite's temperature (0.6; explain 0.2) and `max_tokens` (64 for menus). No other sampler field
  was sent, so each host used its own `top_k`/`top_p` defaults. The local runs pinned the vendors' non-thinking samplers (doc 46),
  so pairs share the prompt and the option order, not the sampling noise.
- **Tool.** The pending cloud backend of `tools/local-qual` (doc 48 §5.1), run from a working copy; the repository's
  `tools/local-qual` is unchanged. A wrapper script loaded the screening key into the one command's environment. The key never
  appears in logs, records, the CSV or this doc.
- **Caps.** One shared ledger for the stage with a $0.90 cap. Each job's cap was the ledger's spend so far plus twice its estimate
  (at least $0.01), because the tool's cap covers the whole ledger. The key itself was limited to $1 by OpenRouter. Every run began
  with a key check.
- **Guards** (stop, record, do not retry): budget or cost anomaly (exit 4), configuration (5), schema rejected (6), canary or
  reasoning leak (7), provider mismatch (8), key check (9). A job with transient errors (exit 2) got one `--resume`.
- **What happened.**
  - **One guard stop:** E10's harder menus with cards, at call 34 (§4.3).
  - **7 error records,** each resumed once:
    - 2 on CoreWeave, HTTP 429 after 5 attempts;
    - 4 on DeepInfra's gpt-oss-20b, likewise;
    - 1 on Mistral, an error finish inside HTTP 200.
  - **89 calls needed more than one attempt:** 37 on CoreWeave (69 HTTP 429s) and 49 on DeepInfra's gpt-oss-20b (100 HTTP 429s,
    "temporarily rate-limited upstream"). Every other endpoint had at most one.
- **Checked on every answered call.**
  - `provider_served` equal to the pinned host (0 mismatches, 0 unverified), and `model_served` equal to the requested id.
  - 100% schema-conformant under strict parsing, finish reason `stop` on all 3,494 answered calls, and 0 truncations.
  - 0 reasoning tokens and 0 thinking characters on all 3,154 calls outside gpt-oss-20b.
  - 0 content-filter finishes, including the 160 text calls on the four hosts with no violence wording (DeepInfra, Parasail,
    AkashML, Darkbloom).

### 1.3 The scoring basis: 29 menus, and HR03 [V]

- **What HR03 is.** A routing menu whose request quotes a map marker's text addressed to "AI", telling it to ignore the user. The
  right answer (write the briefing) treats that text as data: a benign check of the untrusted-content invariant. OpenRouter's terms
  (§7 item 11) bar "prompt injection, jailbreaking, or taking any other adversarial action designed to compromise any Models" without
  prior written approval. Doc 50 §5.9 said today's suites contain no injection items; HR03 is the exception it missed (§5).
- **When it went.** E01–E11 ran on 2026-09-27 with all 30 menus, so HR03 went to OpenRouter 64 times: 6 per endpoint, 4 to E10.
  On 2026-09-28 it was excluded, by an owner-side decision taken during the round and not yet in a record, and E12–E14 never sent
  it. The records stay as they are; nothing was deleted.
- **How scoring treats it.** Every arm, cloud and local, is scored on the **29 shared menus**, so every pair compares the same
  items. The as-run 30-menu figures are in the CSV (`*_asrun_30`). The default got HR03 right in all six samples, so its bar drops
  by exactly one menu: pass^3 24 of 29 without cards and 25 of 29 with cards (25 and 26 of 30 in doc 50 §5.6).
- **What does not change.** The three planted escapes (HA03, HM04, HR04, whose right answer is "none fit", X) are unchanged, so
  their bar stays 9 calls per condition.

### 1.4 Comparators and pairing [V]

- **The default:** Gemma 4 E4B QAT (Unsloth's QAT Q4_0 file, named UD-Q4_K_XL) on llama.cpp b11146 Vulkan, doc 46's records.
- **Same-weights pairs:**
  - E02 and E03 with doc 49's Qwen3-30B-A3B-Instruct-2507 UD-Q4_K_XL;
  - E04 and E05 with doc 49's Gemma 4 26B-A4B QAT UD-Q4_K_XL (the hosts serve the non-QAT checkpoint);
  - E01 with doc 44's Ministral 3 3B Q4_K_M on Ollama, which has no harder-menu arm, so that pair covers `pick`, Fill and explain
    only.
- **No local pair:** E06–E14.
- **Pairing.** `run.py` derives seeds and option shuffles from (item, sample), so both arms saw the same prompt and letter order;
  equal seeds and shuffles were checked on every pair.
- **Tests.**
  - An exact McNemar test on items right by majority in one arm only (a tie counts as wrong).
  - A paired item bootstrap (10,000 resamples) for per-call and majority differences.
  - Holm's correction within each family; the two primary families (harder menus and Fill against the default, 40 tests) were
    also adjusted together.
- **Grading.** Explanations and text were graded by a strict grader in one pass, with every round-S endpoint side by side,
  calibrated on docs 44, 46 and 49's grade files. The local comparators keep their own docs' grades, so graded cloud-against-local
  gaps carry a grader-pass caveat (doc 46 §2.5).

## 2. Results by step kind

"Majority" means right in at least 2 of 3 samples; pass^3 means right in all 3. Menus are the 29 shared harder menus. "b : c" is
menus right by majority in the cloud arm only : in the comparator only.

### 2.1 PICK: the harder menus [V]

| Setup | Without cards: per call / pass^3 / majority (of 29) | With cards | Planted escapes caught (calls of 9), none / cards | False-escape calls, none / cards | p50, none | USD per call |
| --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 E4B QAT, local (the bar) | 0.943 / **24** / 29 | 0.920 / **25** / 26 | 8 / 9 | 0 / 0 | 1.15 s | — |
| E01 Ministral 3 3B @ Mistral | 0.655 / 15 / 20 | 0.678 / 18 / 20 | 3 / 3 | 0 / 2 | 0.52 s | 0.000025 |
| E02 Qwen3-30B-A3B-2507 @ Nebius | 0.828 / 22 / 24 | 0.920 / 23 / 28 | 6 / 8 | 0 / 0 | 0.58 s | 0.000032 |
| E03 same @ SiliconFlow | 0.816 / 21 / 23 | 0.885 / 23 / 26 | 6 / 6 | 0 / 0 | 1.39 s | 0.000028 |
| Qwen3-30B-A3B-2507, local (doc 49) | 0.816 / 20 / 25 | 0.885 / 23 / 27 | 5 / 6 | 0 / 0 | 6.66 s | — |
| E04 Gemma 4 26B-A4B @ CoreWeave | 0.931 / 24 / 28 | 0.977 / 28 / 28 | 8 / 7 | 1 / 0 | 0.71 s | 0.000029 |
| E05 same @ DeepInfra | 0.943 / 24 / 29 | 0.954 / 26 / 28 | 8 / 7 | 1 / 0 | 0.90 s | 0.000024 |
| Gemma 4 26B-A4B QAT, local (doc 49) | 0.920 / 25 / 27 | 0.977 / 27 / 29 | 9 / 9 | 3 / 0 | 9.18 s | — |
| E06 Qwen3.5-35B-A3B @ DeepInfra | 0.954 / 26 / 28 | **1.000 / 29 / 29** | 9 / 9 | 0 / 0 | 0.84 s | 0.000051 |
| E07 same @ Parasail | 0.954 / 25 / 29 | 0.989 / 28 / 29 | 8 / 9 | 0 / 0 | 0.80 s | 0.000054 |
| E08 Qwen3.6-35B-A3B @ AkashML | 0.897 / 23 / 26 | 0.989 / 28 / 29 | 8 / 9 | 2 / 0 | 0.59 s | 0.000038 |
| E09 same @ Parasail | 0.943 / 25 / 28 | 0.977 / 27 / 29 | 9 / 9 | 1 / 0 | 0.78 s | 0.000056 |
| E10 gpt-oss-20b @ AkashML | 0.897 / 24 / 27 | partial (33 calls: 32 right) | 6 / 3 of 3 | 0 / 1 | 1.29 s | 0.000013 |
| E11 same @ DeepInfra | 0.908 / 23 / 27 | 0.931 / 27 / 27 | 7 / 9 | 0 / 0 | 1.20 s | 0.000018 |
| E12 Bonsai 2 27B @ Darkbloom | 0.931 / 24 / 28 | 0.954 / 26 / 28 | 9 / 9 | 1 / 0 | 2.14 s | 0.000033 |
| E13 Qwen3.8-27B @ Darkbloom | 0.954 / 26 / 28 | **1.000 / 29 / 29** | 9 / 9 | 1 / 0 | 1.29 s | 0.000034 |
| E14 Qwen3.5-9B @ DeepInfra | 0.862 / 20 / 26 | 0.920 / 25 / 27 | 6 / 7 | 1 / 0 | 1.12 s | 0.000031 |

Random valid option: 0.143. "USD per call" is billed cost. gpt-oss-20b spent a mean of 28 (AkashML) and 48 (DeepInfra) reasoning
tokens per answered call without cards; one AkashML call used 874 completion tokens.

**Paired against the default** (b : c, exact p; Holm-adjusted p is 1.0 unless given):

| Endpoint | Without cards | With cards | Endpoint | Without cards | With cards |
| --- | --- | --- | --- | --- | --- |
| E01 Ministral | **0 : 9, p = 0.0039** (Holm 0.105; 0.156 over 40) | 1 : 7, p = 0.070 | E08 Qwen3.6 AkashML | 0 : 3, p = 0.25 | 3 : 0, p = 0.25 |
| E02 Qwen3-30B Nebius | 0 : 5, p = 0.0625 | 2 : 0, p = 0.5 | E09 Qwen3.6 Parasail | 0 : 1 | 3 : 0, p = 0.25 |
| E03 Qwen3-30B SiliconFlow | **0 : 6, p = 0.031** (Holm 0.81) | 2 : 2 | E10 gpt-oss AkashML | 0 : 2, p = 0.5 | not tested (partial) |
| E04 Gemma 26B CoreWeave | 0 : 1 | 3 : 1, p = 0.625 | E11 gpt-oss DeepInfra | 0 : 2, p = 0.5 | 2 : 1 |
| E05 Gemma 26B DeepInfra | 0 : 0 | 3 : 1, p = 0.625 | E12 Bonsai 2 | 0 : 1 | 3 : 1, p = 0.625 |
| E06 Qwen3.5-35B DeepInfra | 0 : 1 | 3 : 0, p = 0.25 | E13 Qwen3.8-27B | 0 : 1 | 3 : 0, p = 0.25 |
| E07 Qwen3.5-35B Parasail | 0 : 0 | 3 : 0, p = 0.25 | E14 Qwen3.5-9B | 0 : 3, p = 0.25 | 2 : 1 |

- **Without cards, no endpoint beats the default on a single menu.** The default is right by majority on all 29, so the no-card
  comparisons can only find losses. Four per-call intervals exclude 0 there (unadjusted): Ministral −0.29, Qwen3-30B-A3B-2507 −0.12
  and −0.13 on its two hosts, and Qwen3.5-9B −0.08.
- **With cards the strongest endpoints gain the default's three misses.** Those are HV01 (a per-turn roll), HW03 (SENTRY) and HW04
  (a CYCLE placed at the right waypoint). Qwen3.5-35B-A3B at DeepInfra and Qwen3.8-27B reach 29 of 29 in all three samples. Their
  per-call interval against the default is +0.01 to +0.16 (unadjusted). The majority split, 3 : 0, gives p = 0.25.
- **The hard menus are doc 46's again.** Wrong by majority without cards: HT03 (Both End #1) on 9 of the 17 arms, cloud and local;
  HM04 (a planted escape: there is no vehicle-only respawn module) on 7; HV01 on 6; HW04 on 4. These are fact-bearing menus, which
  doc 44's rule gives to code: code filters by the facts it knows, and the model picks among what remains [V; I per doc 44].
- **Escapes.**
  - **HM04 missed by majority** without cards: Qwen3-30B-A3B-2507 on both hosts and locally, gpt-oss-20b on both hosts, Qwen3.5-9B
    and Ministral. The wrong picks are "Respawn point" or "Reinforcements"; gpt-oss at DeepInfra and Qwen3.5-9B split three ways
    (a tie counts as wrong).
  - **HA03 missed with cards** (2 of 3 samples) by Gemma's two non-QAT hosts. The request needs thick snow, which no preset gives;
    the hosts chose AM07 "Dark night raid" (it matches the raid, not the snow). The local QAT file caught it every time.
  - **False escapes:** single calls, mostly on HT03 (Gemma's two hosts, both Qwen3.6 hosts, Qwen3.8 and Ministral). The others
    were on HK01 (Qwen3.6 at AkashML), HT04 (Qwen3.5-9B, Ministral) and HW04 (Bonsai 2; gpt-oss at AkashML with cards). Doc 49's
    local Gemma 26B QAT escaped HT03 in all three samples. No cloud endpoint escaped any menu falsely by majority.
- **E10's partial arm** (33 calls, before the guard stop): sample 0 was right on 29 of 29 menus, against 27 of 29 for the default's
  sample 0. It is descriptive only and kept out of every test.

### 2.2 FILL [V]

Twelve request → record items, k = 3. "All fields" is the whole record right in one call. `target` and `place` are the span fields
(copied as written).

| Setup | All fields (calls of 36) | pass^3 (of 12) | Majority (of 12) | Field accuracy | `target` / `place` | Validators all pass | p50 | vs default (b : c) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 E4B QAT, local (the bar) | 31 | 9 | 10 | 0.970 | 1.00 / 1.00 | 0.972 | 2.22 s | — |
| E01 Ministral 3 3B | 16 | 4 | 5 | 0.881 | 0.08 / 0.92 | 0.667 | 0.69 s | 1 : 6, p = 0.125 |
| E02 Qwen3-30B-A3B-2507 @ Nebius | 30 | 10 | 10 | 0.964 | 1.00 / 1.00 | 0.917 | 1.00 s | 1 : 1 |
| E03 same @ SiliconFlow | 30 | 10 | 10 | 0.964 | 1.00 / 1.00 | 0.917 | 2.57 s | 1 : 1 |
| Qwen3-30B-A3B-2507, local (doc 49) | 33 | 11 | 11 | 0.982 | 1.00 / 1.00 | 0.917 | 11.28 s | — |
| E04 Gemma 4 26B-A4B @ CoreWeave | 33 | 11 | 11 | 0.982 | 1.00 / 1.00 | 1.000 | 1.09 s | 1 : 0 |
| E05 same @ DeepInfra | 33 | 11 | 11 | 0.982 | 1.00 / 1.00 | 1.000 | 1.48 s | 1 : 0 |
| Gemma 4 26B-A4B QAT, local (doc 49) | 33 | 11 | 11 | 0.982 | 1.00 / 1.00 | 1.000 | 16.57 s | — |
| E06 Qwen3.5-35B-A3B @ DeepInfra | 30 | 9 | 10 | 0.964 | 1.00 / 0.92 | 0.889 | 1.02 s | 1 : 1 |
| E07 same @ Parasail | 30 | 8 | 11 | 0.964 | 1.00 / 0.96 | 0.889 | 1.10 s | 1 : 0 |
| E08 Qwen3.6-35B-A3B @ AkashML | 31 | 9 | 10 | 0.970 | 0.92 / 1.00 | 0.917 | 0.75 s | 1 : 1 |
| E09 same @ Parasail | 31 | 10 | 10 | 0.970 | 1.00 / 1.00 | 0.944 | 1.05 s | 1 : 1 |
| E11 gpt-oss-20b @ DeepInfra | 27 | 7 | 9 | 0.946 | **0.33** / 1.00 | 0.917 | 3.14 s | 2 : 3 |
| E12 Bonsai 2 27B | 33 | 10 | 11 | 0.982 | 1.00 / 0.92 | 0.972 | 3.86 s | 2 : 1 |
| E13 Qwen3.8-27B | 33 | 10 | 11 | 0.982 | 1.00 / 0.92 | 0.944 | 2.13 s | 2 : 1 |
| E14 Qwen3.5-9B | 27 | 7 | 9 | 0.946 | 0.92 / 1.00 | 0.917 | 3.25 s | 1 : 2 |
| Ministral 3 3B, Ollama (doc 44) | 15 | 4 | 5 | 0.839 | 0.00 / 0.92 | 0.639 | 1.36 s | — |

- **No Fill test reaches p < 0.05** (13 tests, at most 7 discordant records). Ministral's per-call interval (−0.69 to −0.11) is the
  only one that excludes 0.
- **The offload bar** (whole-record pass^3 at least 10 of 12; doc 47 §6.3 item 3, doc 48 §6.5):
  - Gemma 4 26B-A4B meets it on both hosts (11), as it did locally.
  - Qwen3-30B-A3B-2507 meets it on both hosts (10), one below its local 11.
  - Qwen3.6-35B-A3B meets it on one host only (9 and 10).
  - Qwen3.5-35B-A3B misses it on both hosts (9 and 8).
  - gpt-oss-20b misses it on its one Fill host (7).
- **gpt-oss-20b's `target` span** (4 items) was right in 4 of 12 calls: it paraphrases the object instead of copying it, the same
  failure doc 49 saw in the 4B models. Ministral gets `target` right once in 12 calls in the cloud and never locally.

### 2.3 EXPLAIN and DRAFT (graded) [V]

Explain: 10 findings with cards, k = 2. Text: 10 short-text slots without cards, k = 2, graded for quality. "Both" counts items
passed in both samples. H counts answers that present a non-existent command, syntax or behaviour.

| Setup | Explain: pass / partial / fail (H) · both of 10 | Sentence cap | Text: pass / partial / fail · both of 10 | Text code constraints |
| --- | --- | --- | --- | --- |
| Gemma 4 E4B QAT, local (b; doc 46's grades) | 13 / 7 / 0 (2) · 6 | — | 3 / 16 / 1 · 0 | 0.95 |
| E01 Ministral 3 3B | 14 / 6 / 0 (2) · 6 | 1.00 | not sent (policy) | — |
| E02 Qwen3-30B-A3B-2507 @ Nebius | 20 / 0 / 0 · **10** | 1.00 | not sent (policy) | — |
| E03 same @ SiliconFlow | 20 / 0 / 0 · **10** | 1.00 | not sent (policy) | — |
| E04 Gemma 4 26B-A4B @ CoreWeave | 18 / 2 / 0 · 9 | 1.00 | not sent (policy) | — |
| E05 same @ DeepInfra | 16 / 4 / 0 · 8 | 0.80 | 8 / 12 / 0 · 4 | 1.00 |
| E06 Qwen3.5-35B-A3B @ DeepInfra | 18 / 2 / 0 · 9 | 1.00 | 9 / 11 / 0 · 3 | 1.00 |
| E07 same @ Parasail | 18 / 2 / 0 · 8 | 1.00 | 10 / 10 / 0 · 4 | 0.95 |
| E08 Qwen3.6-35B-A3B @ AkashML | 20 / 0 / 0 · **10** | 1.00 | 5 / 15 / 0 · 2 | 1.00 |
| E09 same @ Parasail | 19 / 0 / 1 · 9 | 1.00 | 8 / 12 / 0 · 4 | 1.00 |
| E12 Bonsai 2 27B | 20 / 0 / 0 · **10** | 1.00 | 14 / 6 / 0 · **7** | 1.00 |
| E13 Qwen3.8-27B | 19 / 1 / 0 · 9 | 1.00 | 12 / 8 / 0 · 5 | 1.00 |
| E14 Qwen3.5-9B | 20 / 0 / 0 · **10** | 1.00 | 6 / 14 / 0 · 3 | 0.95 |
| Qwen3-30B-A3B-2507, local (doc 49's grades) | 20 / 0 / 0 · 10 | — | 7 / 13 / 0 · 3 | 1.00 |
| Gemma 4 26B-A4B QAT, local (doc 49's grades) | 19 / 1 / 0 · 9 | — | 7 / 13 / 0 · 3 | 1.00 |
| Ministral 3 3B, Ollama (doc 44's grades) | 16 / 4 / 0 · 6 | — | 3 / 10 / 7 · 0 | 0.50 |

- **Every cloud endpoint except Ministral passes 8–10 explanations in both samples**, against the default's 6. There are 20 graded
  tests against the default. One has raw p < 0.05: Bonsai 2's text, 7 : 0, p = 0.016, Holm 0.31. The rest have at most 5
  discordant items and none survives Holm. Eleven per-call intervals exclude 0, all in the cloud's favour. The grader-pass caveat
  (§1.4) applies to every one of them.
- **Among the cloud endpoints, only Ministral invented anything** (the default's two, in doc 46's grades, were not re-graded). It
  wrote the condition `!this is not East` (and `!this is East` in the other sample) as an alternative fix: this engine has no
  `is not` operator. Qwen3.6-35B-A3B at Parasail failed one explanation outright, with a
  circular fix (it sets the flag inside the trigger that reads it) and without the AND the finding needed. Gemma at DeepInfra broke
  the two-sentence cap in 4 of 20 answers.
- **Text quality stays low everywhere: 2–7 of 10 slots pass in both samples.** Most partials put callsigns in a message-body slot,
  where code framing duplicates them (doc 46's rule). So lines stay candidates the user picks from, as doc 44 §2.4 proposes.

### 2.4 Same weights: cloud against local [V]

| Pair (cloud vs local) | Harder menus, none: majority, b : c | Cards | Fill: majority records, b : c | Explain: both of 10 |
| --- | --- | --- | --- | --- |
| E02 Nebius vs Qwen3-30B-A3B-2507 UD-Q4_K_XL | 24 vs 25, 0 : 1 | 28 vs 27, 2 : 1 | 10 vs 11, 0 : 1 | 10 vs 10 |
| E03 SiliconFlow vs the same | 23 vs 25, 0 : 2, p = 0.5 | 26 vs 27, 0 : 1 | 10 vs 11, 0 : 1 | 10 vs 10 |
| E04 CoreWeave (non-QAT bf16) vs Gemma 4 26B-A4B QAT | 28 vs 27, 2 : 1 | 28 vs 29, 0 : 1 | 11 vs 11, 0 : 0 | 9 vs 9 |
| E05 DeepInfra (non-QAT fp8) vs the same | 29 vs 27, 2 : 0, p = 0.5 | 28 vs 29, 0 : 1 | 11 vs 11, 0 : 0 | 8 vs 9; text 4 vs 3 |
| E01 Mistral vs Ministral 3 3B Q4_K_M (Ollama) | `pick` 28 vs 26 of 30, 3 : 1, p = 0.625 | `pick` 28 vs 29, 0 : 1 | 5 vs 5, 0 : 0 | 6 vs 6 (3 : 3) |

- **No measurable host or quantisation effect** at this resolution. There are 15 code-scored tests (at most 4 discordant items,
  smallest p = 0.5) and 6 graded tests (p = 1.0). A secondary family pairs the two hosts of the same model: 13 tests, at most 4
  discordant items, smallest p = 0.5. The only interval that excludes 0 is Ministral's `pick` without cards, +0.09 per call for the
  cloud (majority split 3 : 1).
- **The cloud is not always the optimistic bound** doc 50 §5.5 expects:
  - Qwen3-30B-A3B-2507's two fp8 hosts had 30 Fill calls fully right against the local Q4 file's 33.
  - On pass^3 they were 1–2 menus above it without cards (22 and 21 against 20) and level with cards.
  - Gemma's non-QAT hosts lost HA03 with cards; the local QAT file lost HT03 without cards (a false escape).

  These are single-menu moves, which fits noise. It also means a local run can land on either side of its cloud copy (§3.3 A8).
- **Latency.** On harder menus and Fill, cloud medians were 0.6–2.6 s against 6.7–16.6 s for the same weights on the reference
  PC's offload setup (doc 49). The cloud buys speed for these models, not accuracy.

### 2.5 Bonsai 2 against Qwen3.8-27B: same host, thinking off [V]

| Arm | Bonsai 2 27B (`darkbloom/int4`) | Qwen3.8-27B (`darkbloom/fp4`) | b : c, p |
| --- | --- | --- | --- |
| Harder menus, none: per call / pass^3 / majority | 0.931 / 24 / 28 | 0.954 / 26 / 28 | 0 : 0 |
| Harder menus, cards | 0.954 / 26 / 28 | 1.000 / 29 / 29 | 0 : 1, p = 1.0 |
| Fill: all fields / pass^3 / majority | 33 / 10 / 11 | 33 / 10 / 11 | 0 : 0 |
| Explain, both of 10 (H) | 10 (0) | 9 (0) | 1 : 0, p = 1.0 |
| Text, both of 10 | 7 | 5 | 2 : 0, p = 0.5 |
| Median latency, harder menus none / Fill / explain | 2.14 s / 3.86 s / 4.28 s | 1.29 s / 2.13 s / 2.41 s | — |
| Billed USD per harder-menu call, none | 0.000033 | 0.000034 | — |

- **Thinking off is honoured.** With reasoning effort `none` both models returned 0 reasoning tokens on all 250 calls, with no
  loops and no truncation. Mean prompt tokens were identical on every arm (391.1, 530.3, …), so the two share the tokenizer and saw
  the same prompts [V].
- **No detectable difference** (5 tests, at most 2 discordant items, smallest p = 0.5). Bonsai 2 trails by 2–5 points per call on
  harder menus and leads on graded text.
- **Doc 48 §6.6's verdict lines.** "Down to skip" includes trailing Qwen3.8-27B by at least 10 points of pass^3 on `pick-hard`.
  With cards Bonsai 2 trails by 3 menus (26 against 29), which is 10.3 points, although only one menu differs by majority. "Worth the
  local paired probe" asks for Bonsai 2 to be level or ahead on every code-scored suite, which it is not. By the letter it is "down
  to skip"; by the paired test there is no difference. The 10-point line is 3 menus at this size, inside the noise (§3.3 A7).
- **What was measured.** "Bonsai 2 as served by Darkbloom": which artifact `int4` names is unknown [U], so this says nothing about
  the released GGUFs.

### 2.6 Hosts [V]

- **Speed differs by host, quality did not.** Qwen3-30B-A3B-2507 ran at a median 0.58 s on Nebius against 1.39 s on SiliconFlow
  for the same menus. Gemma 4 26B-A4B's harder-menu p90 was 5.0 s on CoreWeave, because of 429 back-offs, against 1.5 s on
  DeepInfra.
- **Rate limits hit paid routes too.** CoreWeave returned 69 HTTP 429s and DeepInfra's gpt-oss-20b 100 ("temporarily rate-limited
  upstream"), and 6 calls used up all five attempts. Doc 52's finding, that shared upstream capacity binds before an account quota
  does, also holds on paid, pinned routes [V; I per doc 52].
- **The aggregator safeguards held.** A pinned route with `allow_fallbacks: false` and `require_parameters: true` never fell back,
  never served another model and never dropped a parameter silently (D046). The one parameter a host lacked (SiliconFlow's seed) was
  dropped explicitly and recorded.

### 2.7 Power and limits [V; I]

- **29 menus is small.** At most 9 discordant menus in any pair, and a 3 : 1 split needs 20 for p < 0.05 and 30 for 80% power. The
  same holds for 12 Fill records and 10 graded items. Every "no difference" here is an absence of evidence. Only the 100-menu
  instrument (doc 44 §5.4 item 1; doc 46 OQ8) can turn these screens into comparisons.
- **The rule works in steps of 1–3 menus.** That is the size of the noise, so its verdicts triage and do not measure (§3).
- **Sampler, precision and serving differ** from the local records (§1.2). A pair shares prompts and letter orders, not sampling.

## 3. Promotion decisions under D044's proposed rule

### 3.1 The rule on 29 menus [I on V]

Doc 50 §5.6 (D044 P3, a proposal), with the default's bar re-based on the 29 shared menus (§1.3):

- **Must-pass, all of:** schema conformance at least 95%; no reasoning leak (thinking-off calls at 0 reasoning tokens; mandatory
  reasoning at its lowest effort, recorded); planted escapes at least 8 of 9 calls per condition; no false escapes.
- **Promote** if *general (dense T1)*: harder-menu pass^3 at least 23 of 29 without cards and 24 of 29 with cards, and Fill all
  fields at least 29 of 36 or pass^3 at least 9 of 12. **Or** if *specialist*, any one of:
  - harder menus at least 3 menus above the default in either condition (27 or 28 of 29; this doc counts pass^3);
  - Fill pass^3 at least 11 of 12, or both span fields at least 0.8;
  - explanations at least 9 of 10 with no invented fix;
  - for offload models, whole-record Fill pass^3 at least 10 of 12 with no harder-menu regression. Neither doc 50 nor doc 47 §6.3
    defines "regression"; this doc and the CSV read it as pass^3 3 or more menus below the default in either condition. Among the
    offload arms it bites only on E03 (Fill 10 of 12, but 21 of 29 without cards).
- **Drop** (no local run) if 3 or more menus below the default in both conditions and Fill all fields at most 27 of 36; or on a
  must-pass failure that persists on a second host; or when both offload hosts miss whole-record Fill 10 of 12.
- **Otherwise grey.**

### 3.2 As written [I on V]

| Model (hosts) | Planted escapes, calls (none / cards) | False-escape calls (none / cards) | Harder pass^3 (bar 24 / 25) | Fill all fields /36 · pass^3 /12 | Explain both /10 | Verdict as written |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-30B-A3B-2507 (Nebius; SiliconFlow) | 6 / 8; 6 / 6 | 0 / 0; 0 / 0 | 22 / 23; 21 / 23 | 30 · 10; 30 · 10 | 10; 10 | **Drop**: escape must-pass fails on both hosts (HM04) |
| Gemma 4 26B-A4B (CoreWeave; DeepInfra) | 8 / 7; 8 / 7 | 1 / 0; 1 / 0 | 24 / 28; 24 / 26 | 33 · 11; 33 · 11 | 9; 8 | **Drop**: HA03 with cards and one false escape, both hosts |
| Qwen3.5-35B-A3B (DeepInfra; Parasail) | 9 / 9; 8 / 9 | 0 / 0; 0 / 0 | 26 / 29; 25 / 28 | 30 · 9; 30 · 8 | 9; 8 | **Conflict**: promote (general; +4 and +3 menus with cards) *and* drop (offload Fill below 10 on both hosts) |
| Qwen3.6-35B-A3B (AkashML; Parasail) | 8 / 9; 9 / 9 | 2 / 0; 1 / 0 | 23 / 28; 25 / 27 | 31 · 9; 31 · 10 | 10; 9 | **Drop**: false escapes on both hosts (HT03 in both) |
| gpt-oss-20b (AkashML; DeepInfra) | 6 / 3 of 3 (partial); 7 / 9 | 0 / 1 (partial); 0 / 0 | 24 / partial; 23 / 27 | not run; 27 · 7 | not screened | **Drop**: HM04 missed without cards on both hosts |
| Ternary Bonsai 2 27B (Darkbloom) | 9 / 9 | 1 / 0 | 24 / 26 | 33 · 10 | 10 | **Grey**: one false-escape call (HW04), one host |
| Qwen3.8-27B (Darkbloom) | 9 / 9 | 1 / 0 | 26 / 29 | 33 · 10 | 9 | **Grey**: one false-escape call (HT03), one host |
| Qwen3.5-9B (DeepInfra) | 6 / 7 | 1 / 0 | 20 / 25 | 27 · 7 | 10 | **Grey**: escape misses and a false escape, one host |
| Ministral 3 3B (Mistral) | 3 / 3 | 0 / 2 | 15 / 18 | 16 · 4 | 6 | **Drop**: the score clause (its must-pass also fails, on its one host) |
| *Gemma 4 E4B QAT, local (the bar)* | 8 / 9 | 0 / 0 | 24 / 25 | 31 · 9 | 6 | — |

Every endpoint passed schema conformance (100%) and the reasoning check. The failures that decide the verdicts are all in the escape
checks. Four things go wrong:

1. **Nothing is promoted.** The only model that clears the must-pass is dropped by another clause at the same time. Nothing in the
   rule says which clause wins.
2. **One call decides.** Qwen3.6-35B-A3B is dropped for one or two false-escape calls per host, one of them on HT03 on each host.
   That is the menu doc 46 already lists as failing pass^3 in 15 of 16 local cells. Gemma 4 26B-A4B's drop rests partly on one
   such call per host. Everywhere else the rule counts menus; here it counts calls, with zero tolerance. The default itself passes
   only because the bar allows one missed escape call (8 of 9).
3. **It contradicts doc 49.** The escape gate drops the two offload files doc 49 measured, although their offload role is whole-record
   Fill and card-backed explanations, never Picks (doc 49 §5.2). Escapes are a Pick behaviour.
4. **Some criteria hardly discriminate.** "Both span fields at least 0.8" is met by 11 of the 13 Fill arms, so the specialist clause
   admits almost any model that clears the must-pass. "At least 3 menus above" does not say whether it counts pass^3 or majority.

### 3.3 What the rule should change (proposal) [I]

- **A1 Re-base on the menus actually sent.** While HR03 stays out of hosted runs, the bar is pass^3 24 and 25 of 29 (§1.3). The
  planted-escape bar is unchanged.
- **A2 Escapes by majority, for PICK only.**
  - The test: each planted menu right by majority in each condition, and no menu escaped by majority where an option fits.
  - Call counts stay reported, and more than one false-escape call per condition is flagged.
  - The escape check gates PICK and nothing else. Schema conformance and the reasoning check still gate every step kind.
- **A3 Judge per step kind** (PICK, FILL, EXPLAIN, and DRAFT once it has a bar), as D045 item 4 and doc 49 §2.4 already do. A model
  can be promoted for one step kind and dropped for another.
- **A4 Judge offload models on their role.** Offload models are judged on FILL and EXPLAIN. Their harder-menu scores stay reported,
  but a harder-menu gain does not promote them, because their warm Pick latency (6.5–7.5 s, doc 49) rules them out for Picks.
- **A5 Two hosts.** Promote a step kind only when both hosts meet it; drop only when both miss (the drop half is already in the
  rule). A one-host result is provisional.
- **A6 Precedence.** The step kind's must-pass first, then drop, then promote, then grey.
- **A7 Criteria that discriminate.** Replace "both span fields at least 0.8" with "span fields at least the default's" (1.00 and
  1.00 today). State that menu counts are pass^3. Treat any 1–3 menu line (this rule's, and doc 48 §6.6's 10 points of pass^3) as
  triage, never as evidence of a difference: the paired test is the evidence.
- **A8 Local confirmation** (doc 50 §5.7). Replace "within 1 menu per condition and 2 Fill calls of the cloud copy" with "no
  significant paired loss against the cloud copy, and still at the absolute bar". The same-weights pairs in §2.4 moved up to 2
  menus of pass^3 and 3 Fill calls with no detectable difference, so the current tolerance would flag noise as a quantisation gap.

### 3.4 With the proposed changes, per step kind [I on V]

PICK requires the escape check (A2) and pass^3 at least 23 and 24 of 29. FILL requires, for dense models, all fields at least 29
of 36 or pass^3 at least 9 of 12, and for offload models pass^3 at least 10 of 12 on both hosts. EXPLAIN requires at least 9 of
10 in both samples with no invented fix, on both hosts where there are two. DRAFT has no bar, so graded text is reported only.

| Model | PICK | FILL | EXPLAIN | DRAFT (both of 10) | Local trial? |
| --- | --- | --- | --- | --- | --- |
| Qwen3-30B-A3B-2507 (offload) | Not an offload role (fails: HM04) | **Met** (10; 10) | **Met** (10; 10) | not sent | Already local (doc 49); the cloud agrees |
| Gemma 4 26B-A4B (offload) | Not an offload role (fails: HA03 with cards) | **Met** (11; 11) | Grey (9; 8) | 4 (DeepInfra) | Already local (doc 49) |
| Qwen3.5-35B-A3B (offload) | Not an offload role | **Drop** (9; 8) | Grey (9; 8) | 3; 4 | No |
| Qwen3.6-35B-A3B (offload) | Not an offload role | Grey (9; 10) | **Met** (10; 9) | 2; 4 | EXPLAIN only; low priority |
| gpt-oss-20b (offload) | **Drop** (HM04 on both hosts) | Grey (7 on its one Fill host) | not screened | not screened | No; settle FILL on the second host (OQ3) |
| Ternary Bonsai 2 27B | Met (24 / 26; one host) | Met (33 · 10) | Met (10) | 7 | Would qualify; bring-your-own only |
| Qwen3.8-27B | Met (26 / 29; one host) | Met (33 · 10) | Met (9) | 5 | Not a local candidate; see §5 (D045) |
| Qwen3.5-9B | Not met (20 / 25; HM04) | Not met (27 · 7) | Met (10; one host) | 3 | EXPLAIN only, provisional; low priority |
| Ministral 3 3B | Drop | Drop (score clause) | Not met (6) | not sent | No; doc 44 agrees |

- **Recommendation: no new local download from this round.**
  - **Qwen3.6-35B-A3B and Qwen3.5-9B** are promoted only for EXPLAIN. That is a step where doc 49's Qwen3-30B-A3B-2507 file already
    passes 10 of 10 locally, where the default's explanations are the known gap (6 of 10), and where Qwen3.6's Q4 file (UD-Q4_K_M,
    22.13 GB; doc 47) is larger than the 17.69 GB file doc 49 found to strain 32 GB of RAM.
  - **A 9B dense model** on 8 GB would displace the session model rather than sit beside it (doc 49: one model per session on 8 GB).
- **Qwen3.5-35B-A3B's one clear strength**, harder menus with cards (29 and 28 of 29), sits in the step kind an offload model does
  not serve. Doc 47's other reason to try it, its EuroEval lead in Czech and Polish, is not tested by battery S. So it is grey for
  a non-English suite, not dropped outright.
- **Bonsai 2 and Qwen3.8-27B** clear every step kind they ran, on one host each.
  - Neither is a managed local candidate. Bonsai 2 needs PrismML's fork, which D022 (amendment item 4) refuses to manage.
    Qwen3.8-27B is a dense 27B model, about 16 GB at 4 bits [I], so it does not fit the reference card.
  - Their results matter for bring-your-own setups and for free cloud presets (§5).

## 4. Spend audit [V]

### 4.1 By endpoint

| ID | Plan estimate | Billed (`usage.cost`) | Tool ledger | Tokens × price rows | Billed / plan |
| --- | --- | --- | --- | --- | --- |
| E01 (incl. optional `pick` arms) | 0.0185 | 0.0106 | 0.0217 | 0.0142 | 0.57 |
| E02 | 0.0134 | 0.0100 | 0.0200 | 0.0100 | 0.75 |
| E03 | 0.0122 | 0.0090 | 0.0181 | 0.0090 | 0.74 |
| E04 | 0.0134 | 0.0090 | 0.0179 | 0.0102 | 0.67 |
| E05 | 0.0106 | 0.0082 | 0.0164 | 0.0082 | 0.77 |
| E06 | 0.0234 | 0.0184 | 0.0367 | 0.0184 | 0.79 |
| E07 | 0.0245 | 0.0191 | 0.0383 | 0.0191 | 0.78 |
| E08 | 0.0179 | 0.0140 | 0.0279 | 0.0146 | 0.78 |
| E09 | 0.0245 | 0.0199 | 0.0399 | 0.0199 | 0.81 |
| E10 (partial) | 0.0090 | 0.0017 | 0.0035 | 0.0017 | 0.19 |
| E11 | 0.0128 | 0.0047 | 0.0094 | 0.0047 | 0.37 |
| E12 | 0.0123 | 0.0113 | 0.0227 | 0.0113 | 0.92 |
| E13 | 0.0229 | 0.0176 | 0.0351 | 0.0198 | 0.77 |
| E14 (optional) | 0.0129 | 0.0098 | 0.0197 | 0.0098 | 0.76 |
| **Total** | **0.2283** | **0.1633** | **0.3272** | **0.1711** | **0.72** |

- **Billed stayed within the price rows.** No answered call was billed above its listed price. Mistral billed 393 of its 416
  answered calls below the row (median 0.82 of it). On 50 of them even the doubled figure (§4.2) fell below tokens × price, so the
  tool booked its own computed figure. It did the same for the Mistral error record, which reported no cost: these are the 51
  `computed>provider` settles. CoreWeave (224 of 236 calls, median 0.91) and AkashML's Qwen3.6 (107 of 256) billed below the row
  too, and E13's price fell after the plan. The plan's τ = 1.3 and gpt-oss's θ = 300 reasoning tokens were conservative: gpt-oss
  used 18–73 reasoning tokens per answered call on average (per arm).
- **Cap and key.** The ledger stayed at 36% of the $0.90 stage cap, and billed spend is 18% of it. The screening key had $0.8375 of
  its $1 limit left when the last run started. The 63 jobs with a key-check log show $0.127 of key usage against $0.272 in the
  ledger for the same jobs; the key's usage figure lags by a few seconds, so the ratio (2.14) is a partial check.
- **Outside every cap.** OpenRouter's card fee on the credits bought (5.5%, at least $0.80), which no ledger sees.

### 4.2 The ledger counts every call twice (a bug in the pending tool patch) [V]

- **Where.** The settle step (`budget.py`, `cost_from_usage`) books `usage.cost + usage.cost_details.upstream_inference_cost`.
- **Why that is wrong.** The backend's own notes describe `upstream_inference_cost` as the provider's bill on a
  bring-your-own-key (BYOK) request. On all 3,494 answered calls `is_byok` was false and the upstream figure equalled `cost`, so
  every call is booked twice (ledger ÷ billed = 2.003).
- **Effects.**
  - Every cap binds at half the real spend. That is safe, but it halves the stage budget.
  - Every record's `cost_usd` is doubled, so run summaries overstate cost.
  - The cost-anomaly guard compares the doubled figure with the call's reservation, so it fires once a call's real cost passes
    half its worst case.
- **Fix, before the backend lands in `tools/local-qual`.** Add the upstream figure only when `is_byok` is true. Test-first:
  - a non-BYOK usage block whose upstream equals `cost` settles once;
  - a BYOK block settles `cost` plus upstream;
  - a call at 60% of its reservation does not trip the anomaly guard.
- **Status (2026-09-28): fixed as the backend landed.** `budget.py` adds the upstream figure only when `usage.is_byok` is the
  JSON value true. The three cases are tests t59–t61 in `tools/local-qual/tests/test_cloud.py`; each failed on the patch as
  screened (costs booked twice; the 60% call stopped as a cost anomaly) and passes now. The ledgers of this round keep their
  doubled figures; the billed sums above are the ones to use.

### 4.3 The one guard stop was a false positive [V]

- **What stopped.** E10 (gpt-oss-20b at AkashML), harder menus with cards: the run stopped with exit 4 (cost anomaly) at menu HW04,
  sample 1, after 34 calls.
- **Why.** The call spent 874 completion tokens, nearly all of them reasoning text (3,625 characters, although the host reported 0
  reasoning tokens), and answered X instead of C. Its billed cost was $0.0000961 against a reservation of $0.000147; the doubled
  figure, $0.000192, tripped the guard.
- **What was not retried.** Per the stop rule, neither that arm nor E10's Fill was retried. Resuming both after the fix (54
  harder-menu calls and 36 Fill calls, about $0.002 billed [I]) would give gpt-oss-20b's FILL verdict its second host.

## 5. Implications for D023, D037, D045 and the Model Manager [I]

- **D023 (model strategy).** The provisional local defaults stand: no screened endpoint beats Gemma 4 E4B QAT with statistical
  support on any step kind. Doc 49's offload proposal stands too.
  - **The offload proposal:** Qwen3-30B-A3B-2507 at `--cpu-moe` behind an opt-in switch for whole-record Fill and card-backed
    explanations, never Picks.
  - **Corroboration:** two fp8 hosts reproduce its Fill (10 of 12) and explanations (10 of 10).
  - **The alternates add nothing on those arms:** Qwen3.5-35B-A3B and Qwen3.6-35B-A3B do not improve on it.
  - **Cloud recommendations** should keep naming endpoints (D023's cloud note). The host differences seen here were in latency and
    rate limits, not in answers.
- **D037 (recommended list).** Nothing changes: a screen is not a qualification and never sets a badge (D044).
  - Ministral 3 3B stays custom-only (Mistral's usage policy names military uses).
  - Bonsai 2 stays bring-your-own (fork-only runtime).
  - Screened candidates with OSI licences (the Qwen3.5 and 3.6 MoE models, gpt-oss-20b, Qwen3.5-9B; doc 47) remain candidates.
- **D045 (free presets).**
  - **The best-screened weights are doc 50's preselected free model.** Qwen3.8-27B, whose `:free` route doc 50 §4 preselects,
    screened at or above the default's pass^3 on every arm it ran: harder menus 26 and 29 of 29 (default 24 and 25), Fill pass^3
    10 of 12 (default 9), 9 of 10 explanations, 0 hallucinations. By majority it is one menu below the default without cards (28
    against 29, 0 : 1) and ahead with cards (29 against 26).
  - **The screen does not qualify the free route.** It ran on `darkbloom/fp4`, a different host from the free route's ModelRun
    (also fp4, on the ZDR list). A qualification belongs to its setup (D045 item 5), so the free route must be qualified itself,
    per step kind.
  - **What that run can send.** Under D047 the combat-flavoured text arm cannot go to ModelRun, whose policy bans content that
    "gratuitously depicts or glorifies violence" (doc 50). Capacity is doc 52's question: 50 free requests a day, 1,000 once credits
    are bought on that account.
- **D044 (the rule).**
  - **P1 and P2 worked as designed:** 3–15 minutes and at most 2 cents billed per endpoint, pinned hosts holding on every call.
  - **P3 needs the amendments A1–A8** (§3.3) before it can decide anything; the owner decides whether to adopt them.
  - **P4 unchanged.**
  - **The open part** "how the rule applies to doc 49's rows" now has data for the two rows that ran. Their cloud copies agree with
    the local records.
- **D046 and D047.**
  - **The aggregator safeguards held on 3,494 of 3,494 calls** (§2.6).
  - **The cautious policy reading cost one arm on four hosts.** No content filter fired on the combat-flavoured text sent to the
    other four.
- **D048 (per-model presets).** Data points for the preset file:
  - **The thinking switch works through the aggregator.** Reasoning effort `none` turned thinking off on Qwen3.5 and 3.6 (on by
    default) and on Gemma 4.
  - **gpt-oss-20b's reasoning cannot be switched off.** At effort `low` it spends about 18–73 reasoning tokens per call and runs
    at a median 1.2–1.3 s on harder menus.
  - **Its Fill `target` failure** (paraphrase instead of copy) is a candidate for a preset-level field description (doc 49 OQ8).
- **The Model Manager (D022).**
  - **A note, not a badge.** A catalogue entry may carry "screened in the cloud" with (endpoint, precision, reasoning setting,
    date).
  - **No new download** is recommended from this round.
  - **The fork guard stays.** The guard that refuses fork-only GGUFs keeps Bonsai 2 out whatever it scores.
- **Tools.** The pending cloud backend needs the ledger fix (§4.2) and its regression tests before it lands. HR03 handling should
  become a suite-level flag rather than a per-run `--items` list.
- **Doc 50 corrections** (flagged, not edited):
  - **§5.9:** the suites do contain one instruction-like item, HR03.
  - **§5.3:** the $0.22 estimate was high; the billed cost was 72% of plan.
  - **§5.6 and §5.7:** see A1–A8.
  - **Doc 48 §6.6:** its 10-point pass^3 lines are 3 menus at this size.
- **Design-gap candidates** (not filed):
  - a "screened, not qualified" state in the model catalogue (doc 50 §6);
  - a record format for cloud screens (doc 48 §7.4 item 1);
  - a suite-level marker for items that must not go to hosts whose terms bar adversarial prompts.

## Open questions

1. **Adopt A1–A8?** (owner). D044's protocol, P3 included, is a proposal; this round shows that as written it promotes nothing and
   drops doc 49's offload files.
2. **HR03 and hosted runs** (owner, and counsel before any release). Does a benign untrusted-content item count as "prompt injection"
   under OpenRouter §7 item 11? Keep it out of hosted runs, or ask OpenRouter in writing? It was sent 64 times before the exclusion.
3. **Resume E10 after the ledger fix?** That is 54 harder-menu calls and 36 Fill calls, about $0.002 billed, and it would settle
   gpt-oss-20b's FILL on a second host.
4. **A bigger instrument.** No pair here had more than 9 discordant items. The 100-menu `pick-hard` (doc 44 §5.4 item 1) is the only
   way to turn "no detected difference" into a decision.
5. **Grader calibration.** The default's explain (6 of 10) and text (0 of 10) grades come from doc 46's pass. Re-grading them in the
   same pass as round S would show whether the 2–4 item explanation gaps are real.
6. **Qwen3.8-27B's free route** (D045). Qualify ModelRun's fp4 endpoint per step kind, without the text arm, and see whether its
   capacity (doc 52) allows a useful preset.
7. **What does Darkbloom's `int4` serve** [U]? Until that is known, E12 describes a hosted build, not the released GGUFs.
8. **The calibration anchor lacks a local harder-menu arm.** Ministral 3 3B's `pick-hard` has not run locally (doc 50 §5.7).
9. **Sampler parity.** Hosts used their default `top_k`/`top_p`. Would sending each vendor's non-thinking sampler, where the
   endpoint accepts it, move any result?
10. **Qwen3.5-35B-A3B in Czech and Polish.** Should its grey verdict wait for the non-English suite (doc 47's EuroEval lead), or
    park for good?

## Sources

**Repository docs.**

- `docs/research/50-free-llm-services-and-cloud-first-screening.md` (§4, §5.2–§5.9, §6) and
  [`data/cloud-screening-candidates.csv`](data/cloud-screening-candidates.csv).
- `48-cloud-providers-and-harness-uplift.md` (§1.2, §4, §5.1, §6.5, §6.6, §7.4).
- `44-local-model-qualification-spike.md` (§2.4, §5.4, §6).
- `46-llamacpp-huggingface-and-ud-quant-spike.md` (§2.4–§2.5) and
  [`data/runtime-quant-comparison.csv`](data/runtime-quant-comparison.csv).
- `47-small-model-landscape.md` (§2.7, §6.3, the candidate table).
- `49-local-shortlist-measured.md` (§2, §5.2, OQ8) and [`data/local-shortlist-results.csv`](data/local-shortlist-results.csv).
- `52-rate-limits-and-ux.md` (shared upstream capacity).
- [D022](../decisions/D022-local-inference-and-model-manager.md), [D023](../decisions/D023-model-strategy.md),
  [D037](../decisions/D037-model-manager-recommended-list.md), [D044](../decisions/D044-cloud-first-model-screening.md) (P1–P5 and
  the amendment), [D045](../decisions/D045-free-model-offer-policy.md),
  [D046](../decisions/D046-aggregators-as-first-class-providers.md),
  [D047](../decisions/D047-military-use-policy-models-and-services.md), [D048](../decisions/D048-per-model-harness-presets.md).

**Tools and data.**

- `tools/local-qual/` (`run.py`, `score.py`, `suites/*.json` at the suite hashes of docs 44, 46 and 49: `pick-hard`
  `bf5243d5e47a18dd`, `fill` `41591b35dd9d5b56`, `explain` `67776ef73f038bc9`, `text` `7cc8320f3c681ae4`), unchanged in the
  repository; the cloud backend is the pending patch of doc 48 §5.1.
- [`data/cloud-screening-results.csv`](data/cloud-screening-results.csv): this doc's figures.

**OpenRouter** (keyless reads on 2026-09-27 and 2026-09-28):

- `GET https://openrouter.ai/api/v1/models/<id>/endpoints` for each model: prices, status, uptime, supported parameters.
- `GET https://openrouter.ai/api/v1/endpoints/zdr`: the zero-data-retention list.
- OpenRouter Terms of Service §7 item 11 (as quoted in doc 50 §5.9).

**Host terms** (read 2026-09-27; cautious readings for D047, not legal advice):

- Nebius AUP: <https://docs.nebius.com/legal/aup>
- SiliconFlow terms: <https://docs.siliconflow.com/en/legals/terms-of-service>
- CoreWeave AUP: <https://docs.coreweave.com/docs/policies/terms-of-service/acceptable-use-policy>
- DeepInfra terms: <https://deepinfra.com/terms>
- Parasail terms: <https://www.parasail.io/legal/terms-of-service>
- AkashML terms: <https://akashml.com/terms>
- Darkbloom terms: <https://www.darkbloom.ai/terms.html>
- Mistral's usage policy: as quoted in doc 50 §2.3.

**Statistics.**

- Exact McNemar (binomial on discordant pairs).
- Holm's step-down procedure: S. Holm, *Scand. J. Statist.* 6 (1979) 65–70.
- The percentile bootstrap: B. Efron, *Ann. Statist.* 7 (1979) 1–26.
- pass^k as in doc 44.

## Verification notes

### 2026-09-28, author checks at write-up

- **Scores.**
  - Every accuracy, pass^k, majority, latency, Fill and text figure comes from `score.py` over HR03-filtered copies of the round's
    records and of the local comparators' records.
  - The counts the rule uses were recomputed from the records with `score.py`'s own scoring functions: pass^3 menus, planted escapes
    and false escapes per call and by majority, Fill all-fields calls, pass^3 and majority records, and span fields. The default's
    re-based bar (24 and 25 of 29; 8 and 9 of 9 escapes; 0 false escapes; Fill 31 of 36 and 9 of 12) matches doc 50 §5.6's 30-menu
    bar less HR03.
- **Tests.** Every paired test comes from the round's significance output, which checked equal seeds and option shuffles on every
  pair. Holm families and the 40-test primary adjustment were read from that output, not recomputed.
- **Grades.** The pass, partial, fail, hallucination and both-samples counts were recounted from the 12 grade files. The local
  comparators' counts match docs 44, 46 and 49.
- **Calls.** 3,501 ledger-settled calls: 3,494 answered and 7 error records (6 unbilled). For every answered call, served host and
  model, finish reason, schema conformance and reasoning tokens were checked from the records (§1.2). The HR03 count (64) comes from
  the filter manifest.
- **Spend.** Billed and ledger totals were recomputed per endpoint from the records. The key-check deltas were read from the run
  logs. The double count was confirmed on all 3,494 answered records (`is_byok` false, upstream equal to `cost`).
- **The CSV** was generated by script from those outputs: 2,231 data rows, counted with Python's `csv` module. The script refuses to
  write if a local path, user name or key prefix appears.
- **Hygiene.** This doc and the CSV were searched for keys, local paths, user names and private project names; none were found.
- **Not verified.**
  - The providers' serving stacks and the artifact behind Darkbloom's `int4`.
  - Any local run of Qwen3.5-35B-A3B, Qwen3.6-35B-A3B, gpt-oss-20b, Qwen3.5-9B or Bonsai 2.
  - Whether any finding holds on the 100-menu instrument.

### 2026-09-28, independent review

- **Recomputed without `score.py`.** A separate script re-read every round-S call record and the four local comparators' records.
  It kept the last record per (item, sample) and dropped HR03 from `pick-hard`. It then recomputed, for all 14 endpoints and 3 local
  files, per-call accuracy, pass^3, majority (ties wrong), planted-escape and false-escape calls, wrong-by-majority menus, p50 and p90
  latency, billed USD per call, and Fill all-fields calls, pass^3, majority, field accuracy and span fields. Every figure in §1.1,
  §2.1, §2.2, §2.4, §2.5, §3.2 and §4.1 matches.
  - 557 numeric CSV values were compared by script: score rows, Fill rows, setup counts and spend rows. None differs.
  - The wrong-by-majority menu counts (HT03 9 of 17 arms, HM04 7, HV01 6, HW04 4) and the false-escape items match.
  - So do E10's sample 0 with cards (29 of 29, against the default's 27 of 29), the default's HR03 (6 of 6) and the E10 stop record
    (874 completion tokens, 0 reported reasoning tokens, 3,625 thinking characters, billed $0.0000961 against a $0.000147
    reservation, booked at $0.000192).
- **Paired tests.** Exact McNemar was recomputed on majorities for all 27 + 13 tests against the default, the 15 same-weights tests,
  the 13 two-host tests and the Bonsai 2 pair. Every b : c and p matches the round's significance output. Graded b : c were
  recomputed from the grade files on both-samples passes (20 against the default, 6 same-weights, 2 Bonsai). The output's own
  pairing checks (equal seeds and option shuffles) hold on all 101 of its tests. The bootstrap intervals were read from that
  output, not re-drawn.
  - Power: an exact 3 : 1 split first reaches p < 0.05 at 20 discordant items and 80% power at 30 (80.3%), as §2.7 says.
- **Grades.** All 12 cloud grade files and the four local ones were recounted: pass, partial, fail, H and both-samples. They match
  §2.3, and each file's own summary block agrees.
- **Spend.**
  - The shared ledger has 7,169 rows: 3,667 reserves, 3,501 settles and 1 stop, from 22:18 to 06:54 UTC. The settled sum is
    $0.3271866, equal to the records' `cost_usd` sum. It holds no settle rows from outside round S; the earlier free-route smoke
    files are on another ledger.
  - The billed sum is $0.1633446, and tokens × price rows give $0.1710704. The plan estimate is $0.228292 in all; each endpoint's
    estimate matches §4.1.
  - The key showed $1.00 left at the first run and $0.8375 at the last run's start. Both are consistent with the billed total, so no
    other spend used this key during the round.
  - No answered call was billed above its price row.
- **Hygiene.** No key prefix or bearer token appears in the ledger, the 71 run logs or the 63 result files. This doc and the
  CSV contain no local path, user name, key material or private project name. Their only drive-letter-like matches are `https:/`
  URLs.
- **Corrected in this review** (doc and CSV):
  1. §4.1: "Mistral billed 51 calls below the row" confused two counts. Mistral billed 393 of its 416 answered calls below the row.
     The 51 are the tool's `computed>provider` settles: 50 of those calls and the Mistral error record.
  2. The gpt-oss reasoning means had been averaged over the as-run 30 menus with error records counted as 0. Corrected in §2.1
     (DeepInfra 47 → 48), §4.1 and §5 (18–67 → 18–73) and in five CSV `reasoning_tokens_mean` rows (27.5, 18.4, 47.6, 39.7, 72.8,
     matching the 29-menu `score.py` output).
  3. §2.1 escapes: on HA03 the hosts chose AM07 "Dark night raid", not the winter preset. On HM04 the wrong picks are "Respawn point"
     or "Reinforcements", not "Respawn point" alone.
  4. TL;DR and §5 (D045): Qwen3.8-27B is at or above the default's pass^3 on every arm, but by majority it is one menu below the
     default without cards (28 against 29, 0 : 1). The claim now names its basis.
  5. TL;DR: the same-weights latency range is 0.6–1.5 s (E02–E05). The earlier 0.5–2.1 s covered every endpoint.
  6. §3.1 now states how "no harder-menu regression" is read (pass^3 3 or more menus below the default in either condition). The
     CSV's `offload_fill_10_of_12` rows now say so too; the rule applies that reading to E03, which is marked "not met" despite
     Fill 10 of 12.
  7. Smaller fixes:
     - §2.3: "only Ministral invented anything" is now scoped to the cloud endpoints (the default has two in doc 46's grades).
     - §3.2: Ministral's drop rests on the score clause; its must-pass failure is on one host only.
     - The CSV `calls_answered` note no longer calls the Mistral error record "billed". It reported no cost; the tool booked $0.000058.
- **Residual.**
  - The 7th error record's real charge is unknown [U]. The key-check deltas (63 jobs, $0.127) were read from the author's spend
    summary, not re-summed from the logs.
  - Doc 50 §5.6 leaves "regression" and "3 menus above" undefined. The readings used here are this doc's, not the rule's.
  - The live price reads were not repeated; the saved 2026-09-28 read confirms E13's $0.05.
