# Free LLM services and cloud-first screening

Research doc 50 for Plotroom (`ofp-editor`). Research date: 2026-09-27 (UTC); the legal pages were re-read late on 2026-09-27 UTC in
the verification pass (2026-09-28 is the records' calendar date for that pass, not a UTC date). Audience: the owner, contributors and
LLM coding agents; it is meant to be read alone.
Questions answered (owner, 2026-09-27, lightly edited): (1) "Find a free LLM service that is legal and OK to rely on, so we can maybe
publish the tool with those models configured by default, or at the very least offered for free." (2) "Any model that could fit and
run locally on our PC should first be tested in the cloud. Only if it yields promising results in benchmarks do we try it locally as
well. The idea is to save time."

**Status.** Research and proposals. **Nothing was run**: no account was created, no key was used, no prompt was sent to any model and
no money was spent. The only network calls were page reads and keyless catalogue reads (OpenRouter `/api/v1/models`, per-model
`/endpoints`, `/endpoints/zdr` and `/providers`; the Hugging Face router's `/v1/models` and model provider mappings; Featherless,
OVHcloud, NVIDIA and Vercel `/v1/models`). The owner's rule for direction 2 is recorded in
[D044](../decisions/D044-cloud-first-model-screening.md); the protocol in §5 is a proposal. The owner questions this doc raises are
OWQ-24 to OWQ-27 in [`OWNER-QUESTIONS.md`](../decisions/OWNER-QUESTIONS.md); the owner answered them on 2026-09-28 →
[D045](../decisions/D045-free-model-offer-policy.md), [D046](../decisions/D046-aggregators-as-first-class-providers.md),
[D047](../decisions/D047-military-use-policy-models-and-services.md) and D044's amendment note (DG039 filed).
**Not legal advice.** Every reading of a provider's terms here is ours and may be wrong. The quotes are there so that the owner, and
counsel before any release, can check them; terms change, so re-read them before relying on any.
**Epistemic legend.** **[V]** verified on 2026-09-27 or 2026-09-28 against the cited primary source (a provider's terms, policy, pricing
or docs page, or a public keyless API). **[V-3p]** a third-party report (a tracker, blog or re-test) not confirmed at the source.
**[V per doc N]** taken from a sibling doc. **[I]** our inference, proposal or arithmetic. **[U]** unknown.
**Quotes** are short verbatim extracts as the fetch tool rendered them. **Prices** are USD per million tokens (MTok), read on
2026-09-27 between about 20:30 and 21:00 UTC from the pinned endpoint's row.
**Data.** [`data/free-llm-services.csv`](data/free-llm-services.csv): 23 rows (`service, free_models, limits, structured_output,
data_use, eu, terms_third_party_app, terms_default_preconfig, terms_shared_key, content_policy_military_fiction, verdict, read_on,
sources`). [`data/cloud-screening-candidates.csv`](data/cloud-screening-candidates.csv): 47 rows, one per candidate and screening
endpoint (`model, free_endpoint, paid_endpoint, price_in, price_out, precision, strict_schema, screening_cost_usd, local_fallback,
notes, read_on`).
**Relation to sibling docs.** Doc 40 (token economy; a Standard campaign run makes about 650 calls), docs 44 and 46 (local
measurements; the bar a candidate must meet), doc 47 (small-model candidates and the local plan), doc 48 (cloud providers; round 0 on
OpenRouter's free models, round 1 deferred until doc 49), doc 49 (in progress: doc 47's shortlist measured locally). Records: D004,
D008, D021, D022, D023, D026, D037 and the new D044.
**Hygiene.** Public sources only. Screening sends only the repository's synthetic suites: no user data, no mission files, no game
content. No private project, local path or user name appears here.

## TL;DR

- **No free service can be shipped "working out of the box" with a Plotroom-owned key** [V quotes; I reading; not legal advice]. Terms
  forbid disclosing or transferring credentials (a key inside a public GPL binary is disclosed) and pooling accounts; free quotas are
  per account (one shared OpenRouter key would give *all* users 50 requests a day); Google allows "only Paid Services when making API
  Clients available to users in the European Economic Area, Switzerland, or the United Kingdom"; NVIDIA's and Cohere's trials exclude
  production. A Plotroom proxy would add an outbound destination and put the maintainers in the data path (D008). And at least five free
  offers were cut or retired in 2026 alone (§2.5), so a shipped default would break silently.
- **"Offered for free" is feasible as a one-click connect to the user's own free account** (§4), with Wilco still off by default
  (D004). **OpenRouter** is the best fit: OAuth PKCE with no app registration ("Localhost callbacks are supported on any port"), then a
  preselected free model resolved from the live catalogue, today `qwen/qwen3.8-27b:free` (Apache-2.0 weights; the only free generalist
  on OpenRouter's zero-data-retention list; fp4). Its catches: 18+ only, 50 requests a day (1,000 after 10 credits are bought once),
  models "as-available", reasoning on by default (must be sent off), and its only ZDR host, ModelRun (Modular), has a use policy that
  bans content that "gratuitously depicts or glorifies violence".
- **Other candidates with the user's own account** [V]: **Cloudflare Workers AI** (contractually no training; 10,000 neurons a day,
  roughly 450 harness calls with product-sized prompts [I]; Apache-2.0 models such as Gemma 4 26B-A4B; but a token setup, JSON mode that
  "can't guarantee" the schema, and its own clause against content that "incites or exploits violence"); **Groq Free** (no training;
  strict schemas on gpt-oss-20b/120b and Qwen3.8-27B; but 18+, "not for consumer use", an AUP item on "violence", 8K tokens a minute
  and four free-tier model removals in ten weeks); **Hugging Face sign-in** (the best OAuth, age 13+, but only $0.10 a month).
- **Not as presets:** Google AI Studio's free tier (content used for training and read by human reviewers outside the EEA, UK and
  Switzerland; bars apps "likely to be accessed by individuals under the age of 18"), Mistral Free (trains unless opted out; its Usage
  Policy names "military and warfare" content), the NVIDIA API trial ("violent content"; no production), Z.ai (no "military purposes"
  end use), Cohere's trial, Cerebras (now card-gated: $5 that expires in 30 days) and GitHub Models (retired 2026-07-30).
- **Content policies matter for a war-game editor** (§2.3). Most services have violence wording; few have a fiction exception (Google's
  "artistic considerations"; Groq's exception process). Two are incompatible (NVIDIA trial, Z.ai). Proposal: apply D037's logic to
  services, so no preset ships before a legal review and, where the wording is ambiguous, the provider's written answer (OWQ-24, OWQ-26;
  answered 2026-09-28 → D045, D047).
- **Capacity honesty** [I]: a Standard campaign run (about 650 calls, doc 40) takes about 13 days on OpenRouter's 50 free requests a
  day. Free cloud is a taster and a screening path; local models (D022) are the only free path with no expiry, and a paid key the
  everyday cloud path.
- **Cloud-first screening (owner rule, D044)**: a 256-call battery **S** (pick-hard with and without cards, Fill, Explain, Text, same
  seeds as the local records) costs $0.001–0.025 per endpoint. Screening the five offload-class models on two ZDR strict-schema hosts
  each, Bonsai 2 27B with its comparator and one calibration anchor is **about $0.22 on 13 endpoints** [I]; Qwen3-4B-Instruct-2507 fits
  inside Hugging Face's free credits. The real spending floor is OpenRouter's card fee ($0.80 minimum). It saves about 84 GB of
  downloads and 4–31 minutes of offloaded prompt processing per model and run.
- **What the cloud cannot screen** [V]: no host serves Granite 4.1 3B, Spark-X2.5-4B, NuExtract3, MiniCPM5-2B, Granite 4.0 1B, H-1B or
  H-Tiny, or most watch rows; the default (Gemma 4 E4B QAT), Qwen3.5-4B, Qwen3.5-2B, Gemma 4 E2B and Nanbeige4.1-3B are served only by
  Featherless (the $50-a-month Developer plan; its $25 Chat plan excludes API traffic and benchmarking). CPU-tier latency, memory
  fit and fork-only runtimes are local questions anyway.
- **Promotion rule (proposal, §5.6):** must-pass checks (schema conformance at least 95%, no reasoning leak, planted escapes at least
  8/9 per condition, no false escapes); promote to a local Q4 trial when within one menu or two Fill calls of the default's bar
  (pick-hard pass^3 25/30 and 26/30; Fill 31/36) or clearly better on a specialist axis; drop only on a clear miss confirmed on a second
  host; everything else grey. **The cloud screens; only the local run on the pinned runtime qualifies** (D022, D037).
- **Precision caveat** (§5.5): cloud copies run at bf16 or fp8, so a cloud pass is an optimistic bound for a local Q4 file, weakest
  for models of 4B and under and for Gemma 4 26B-A4B's QAT build; gpt-oss's fp4 hosts serve the same MXFP4 numerics as the local file.
  Serving defects can also make a host worse than local, so a drop needs clean serving and two agreeing hosts.

## 1. What "legal and OK to rely on" means for Plotroom

### 1.1 The fixed frame [V per the records]

- Wilco is optional and **off by default**; the user brings the model, cloud or local; every core feature works with no AI (D004 item
  3; D023 decision 1).
- Outbound traffic goes only to the model provider the user configured, the declared endpoints of enabled plugins and download or feed
  sources the user enabled; every source is off by default and blocked in offline mode (`AGENTS.md`; D008 items 1–2). The editor never
  fetches web or pricing pages (D008 item 5).
- The provider seam is OpenAI-compatible, pins model ids in an editable `models.toml` with dated prices, and probes each endpoint (D021).
- Saving users' API costs is a usability requirement (D026).
- Plotroom is a public GPL-3.0-or-later desktop app. Anything in the binary or the repository, a key included, is public.

### 1.2 Three levels of "free" [I]

| Level | What the user gets | Whose account and key | Verdict |
| --- | --- | --- | --- |
| **L0 Listed** | The provider appears in the list; the user pastes a key | The user's | Fine wherever the terms allow third-party apps |
| **L1 Connect preset** | One-click sign-in (OAuth) or a guided key setup; Plotroom pre-fills the endpoint, a pinned free model, privacy flags and a dated disclosure card | The user's | Feasible (§4), subject to OWQ-24 |
| **L2 Works out of the box** | A Plotroom-owned key in the binary, a Plotroom proxy, or a keyless public endpoint used by default | Plotroom's, or nobody's | Ruled out (§1.3) |

### 1.3 Why L2 is ruled out [V quotes; I reading; not legal advice]

Most terms do allow a developer's own application to serve end users: OpenRouter's Terms extend duties to "your customers (to the
extent you incorporate the Service into your own products and services)"; Groq's Services Agreement §3.1 allows making the services
"available to End Users through your Customer Applications"; Cerebras lets users "distribute or allow access to your integration of the
APIs within your applications to end users"; Mistral's licence is "non-sublicensable (except to its End Users)". The barriers are
elsewhere:

1. **The credential.** A key in a public binary is disclosed. OpenRouter: "You are responsible for maintaining the confidentiality and
   security of all API keys". Z.ai: "keep your created key(s) securely, prevent any form of leakage, do not share or publicly disclose
   your key(s)". Hugging Face: "You may not disclose your password to any third party".
2. **Transfer and pooling.** OpenRouter bars attempts to "sell or otherwise transfer the access granted under these Terms" (§7 item 14)
   and creating multiple accounts as a single user; Groq bars "(c) sell, resell, sublicense, transfer, or distribute any of the Cloud
   Services except as expressly approved by Groq" and "registering multiple accounts or orchestrating usage between multiple
   organizations", and §3.2 adds "Customer will only make its Account available to Authorized Account Users" and "Customer may not
   resell or lease access to its Account"; Mistral bars "(h) buy, sell, or transfer API keys or any type of Mistral AI account";
   Cerebras bars "Buy, sell or transfer API keys without our prior written consent"; Ollama is "one account per person".
3. **Capacity.** Free limits belong to the account: "Making additional accounts or API keys will not affect your rate limits, as we
   govern capacity globally" (OpenRouter). One shared key would split 50 requests a day among every Plotroom user.
4. **Liability and the data path.** Cloudflare: "You acknowledge and agree that you are solely responsible for the acts of your End
   Users." A Plotroom proxy would also be a new outbound destination that D008 item 1 does not allow, and would make the maintainers a
   processor of users' mission text.
5. **Service-specific bars.** Google: "You may use only Paid Services when making API Clients available to users in the European
   Economic Area, Switzerland, or the United Kingdom." NVIDIA's trial is "for limited trial purposes only and without use of the API
   Service or Generated Content in production"; Cohere's "trial keys are rate limited and are not permitted to be used for production or
   commercial purposes".
6. **Keyless public endpoints.** OVHcloud's anonymous tier ("Anonymous: 2 requests per minute, per IP and per model") is EU-hosted and
   stores nothing, but its pages say nothing about third-party apps defaulting to it [U]; a written answer from OVHcloud would be needed
   first. Pollinations now needs keys and publishes no data terms; LLM7.io is an anonymous gateway of unknown standing. Neither is fit.
7. **Volatility** (§2.5): a free default that disappears leaves every install broken, which D023 decision 3 (never a silent switch)
   does not allow.

### 1.4 Criteria for an L1 preset (proposal) [I]

| # | Criterion | Why |
| --- | --- | --- |
| C1 | The terms allow a third-party app to use the user's own account (OAuth or a user-supplied key) | L1 is the user's account |
| C2 | No Plotroom-owned key, proxy or server in the data path | §1.3; D008 |
| C3 | Free-tier data use is stated: no training, or training clearly disclosed with an opt-out; retention stated | Glass box (D010); user trust |
| C4 | The content or use policy tolerates fictional military content, or the provider has confirmed so in writing | The product's domain (§2.3) |
| C5 | Age and audience rules can be shown before sign-up; no clause barring apps likely used by under-18s | The game is rated M 17+ (§2.4) |
| C6 | Available in the EU, UK and the community's other regions, or the card says where it is not | §2.4 |
| C7 | A stable offer with a visible failure mode: limits, reset time and removals are shown, never a silent switch | D023 decision 3 |
| C8 | Technical fit: OpenAI-compatible, reasoning can be switched off, a strict schema is enforced or the D009 validator carries the load | D021; D009 |
| C9 | Nothing in the terms bars the evaluation Plotroom runs on it (benchmarking clauses, red-teaming clauses) | §5.9 |

## 2. Services

### 2.1 Summary [V unless marked; ranked by fit for an L1 preset]

| Service | Free offer | Limits | Strict schema | Free-tier data use | Content policy (fictional war game) [I] | Verdict [I] |
| --- | --- | --- | --- | --- | --- | --- |
| **OpenRouter** `:free` | 17 free ids (Qwen3.8-27B, Gemma 4 26B/31B, Nemotron 3 family, LFM 2.5, dots-3, Inkling, Laguna, Ling 3.0 specialists, a safety classifier) | 20/min; 50/day, 1,000/day after 10 credits bought; per account | Per endpoint (Qwen3.8-27B `:free` lists `structured_outputs`; Gemma `:free` only `response_format`) | Per endpoint; with `zdr` and `data_collection: "deny"` only 3 free text endpoints remain; NVIDIA, Liquid and Thinking Machines free endpoints train | Defers to model and host terms; ModelRun's AUP has violence wording | **Best L1 route** (PKCE); taster capacity |
| **Cloudflare Workers AI** | 10,000 neurons a day on Free and Paid plans; Gemma 4 26B-A4B, gpt-oss-20b/120b, Qwen3.8-27B, GLM-4.7-Flash, Granite 4.0 H Micro, Mistral Small 3.1 | Daily, reset 00:00 UTC; past it requests "fail with an error" | JSON mode, not guaranteed | No training (service terms and docs); the docs page adds no service improvement, the terms allow use "as needed to provide and improve the Services" | Own clause: "incites or exploits violence" | **L1 candidate** (guided token) |
| **Groq Free** | gpt-oss-20b, gpt-oss-120b, Qwen3.8-27B (+ a safeguard model) | 30/min, 1K/day, 8K tokens/min, 200K tokens/day per model | `strict: true` on the three | No training; no retention by default; self-serve ZDR | "violence" item; exception on request | **L1 candidate** (user key) |
| **Hugging Face** Inference Providers | $0.10/month routed credits | Credit-bound | Per provider flag, not always enforced | HF stores no bodies; provider's policy applies | Hub content policy; routed provider's AUP | L1 sign-in after a spike; too small to call free |
| **Ollama Cloud** Free | "Starter usage credits", starter models, 1 concurrent request | Token-metered; amount unpublished [U] | [U] | "never logged or trained on" | "harmful, offensive, or illegal content" | Watch; measure the quota first |
| **OVHcloud** anonymous | Qwen3.5-9B, Qwen3.8-27B, gpt-oss-20b/120b, Mistral Small 3.2 and more | 2/min per IP per model; keys need a payment method | Documented; enforcement [U] | "never stored or used for model training" | Not reviewed | Screening only; ask before any default |
| **Google AI Studio** free | Gemini 3.5–3.8 Flash, Flash-Lite, 2.5 Pro/Flash; Gemma 4 26B/31B (free only) | Shown only in AI Studio; "not guaranteed" | Subset; "always validate" | Used for training, human review, outside EEA/UK/CH | No content that "facilitates" "Violence or the incitement of violence"; "artistic" exceptions | Synthetic screening only; never a preset |
| **Mistral** Free | $10/month API credits | Unpublished; "evaluation and prototyping" | Prompt-injected schema, no guarantee | Trains unless opted out | Names "military and warfare" content | Screening after opt-out and OWQ-26; no preset |
| **Scaleway** | First 1,000,000 tokens, once | Card needed (EUR 1 check) | Strict per its docs | Zero retention by default | Not reviewed | One-off EU screening |
| **Together** | Ternary Bonsai 27B listed at $0 | $5 minimum deposit | JSON mode | Stores prompts until ZDR is enabled | Not reviewed | Bonsai 27B screening only |
| **Cerebras** | $5 that expires in 30 days, after a verified card | 5/min, 1M tokens/day | Strict (subset) | No retention | "promotes hatred, violence, or harm" | No longer free; bars benchmarking |
| **Cohere** trial | 1,000 calls a month | 20/min | Rejects length limits | Terms allow use to improve and share [V] | "weapons" activities | Not production; bars benchmarking |
| **Z.ai** | GLM-4.7-Flash, GLM-4.5-Flash, GLM-4.6V-Flash | 1 concurrent [V-3p] | `json_object` only | Not stored (API) | "violent" content; no "military purposes" end use; AI-output marking | **Incompatible** |
| **NVIDIA API trial** | Nemotron 3 family and many open models | About 40/min [V-3p] | Varies | Used to improve products, "including AI models" | "violent content" | **Incompatible** |

Also surveyed, not fit (details in the CSV): Alibaba Model Studio (1M tokens per model for 90 days, Singapore, billing starts
automatically unless a guard is switched on), SambaNova (20 requests a day per model; six of seven models answered 402 in a
2026-09-07 re-test [V-3p]), Vercel AI Gateway (Hobby plan non-commercial), SiliconFlow (friction, rotating free list), Pollinations,
Puter.js, LLM7.io, GitHub Models (retired) and Chutes (free tier retired).

### 2.2 Service notes

**OpenRouter** (Terms last updated 2026-08-31, <https://openrouter.ai/terms>; limits <https://openrouter.ai/docs/api/reference/limits>;
OAuth <https://openrouter.ai/docs/guides/overview/auth/oauth>; all read 2026-09-27, terms re-read 2026-09-28) [V]:

- Age: "You must be at least 18 years of age to use the Service." Availability: models are provided "only on an 'as-available' basis",
  and "OpenRouter may add or remove Models from the Service at any time". Every free id carried a null `expiration_date`.
- Resale: no use "for purposes of reselling API access to Models or otherwise developing a competing service". Countries (§5.7):
  "certain Model Providers do not authorize users ... (ii) who are located in certain countries or regions, to access their Models",
  and those models may not be reached "by using virtual private networks and proxies".
- Content: §7 item 8 bars input "not in compliance with the Terms of Service for the Model or Provider you are using"; §6.7 lets
  OpenRouter "screen, remove, edit, or block any Inputs that in our sole judgment violates these Terms or is otherwise objectionable or
  illegal"; §5.6 makes the user "solely responsible for selecting the Models ... and determining whether each Model and the applicable
  Model Terms are appropriate for your use case".
- Data: "Some Models may store or train on your Inputs ... Where possible, OpenRouter has opted out of model training with the Models
  it uses." Prompt logging is opt-in. `data_collection: "deny"` uses "only providers which do not collect user data", and per-request
  `zdr` "can only ensure ZDR is enabled, not override" account settings, so request flags only tighten.
- **The only free ZDR generalist** is `qwen/qwen3.8-27b:free`, served by ModelRun at fp4 with `structured_outputs`; OpenRouter links
  that provider to Modular's terms (last modified 2026-08-17, <https://www.modular.com/legal/terms>: "A User must be at least 18 years
  of age"). Modular's Acceptable AI Use Policy (last modified 2026-03-30, <https://www.modular.com/legal/aup>) covers "the Modular
  Platform, including but not limited to the MAX Platform, Modular Cloud" and, in §11 "User Safety", bans content that
  "gratuitously depicts or glorifies violence, including violent images". Whether it covers ModelRun is [U]; the provider page reads
  "ModelRun [by Modular]". The model defaults to reasoning on (`xhigh`), so every call must send it off.
- Gemma 4 `:free` is served by Google AI Studio (precision "unknown", `response_format` only, not ZDR); OpenRouter links that provider
  to Google Cloud's terms, not the Gemini API terms, so which data clause governs this endpoint is [U] (doc 48 records no training and
  55-day retention). `inkling:free` and `inkling-small:free` are served under Thinking Machines' Free Research API Tier terms (last
  updated 2026-08-20), which license Customer Content "including to train, fine-tune, evaluate, and improve the Company Models and other
  AI models ... during and after the Term" and forbid getting around limits "by rotating accounts, keys, or credentials".
- Red teaming (§7 item 11): no "Red Teaming of Models" without "OpenRouter's prior written approval", defined in the same item as
  "prompt injection, jailbreaking, or taking any other adversarial action designed to compromise any Models and/or violate any Model
  Terms"; §8 "allows Red Teaming only for legitimate research purposes and requires users interested in Red Teaming to first submit a
  written request". (§5.9 is "Provider Requirements", not this clause.)
- Attribution is optional. `X-OpenRouter-App-Visibility: hidden` keeps an app out of public rankings, and apps using a localhost
  callback "will not appear in the OpenRouter marketplace or rankings" (<https://openrouter.ai/docs/app-attribution>).

**Cloudflare Workers AI** (pricing, updated 2026-09-17; data usage, updated 2026-04-21; Developer Platform service-specific terms, page
showing "Last updated: September 28, 2026"; Self-Serve Subscription Agreement, last updated 2025-09-12; read 2026-09-27/28) [V]:

- "10,000 Neurons per day at no charge" on Workers Free and Workers Paid, reset at 00:00 UTC; paid use costs "$0.011 per 1,000
  Neurons". Gemma 4 26B-A4B costs 9,091 / 27,273 neurons per MTok in / out; gpt-oss-20b 18,182 / 27,273; Qwen3.8-27B 40,909 / 290,909.
  Kimi, GLM-5.x and DeepSeek V4 need a paid plan.
- Data: "Cloudflare does not use your Customer Content to (1) train any AI models made available on Workers AI or (2) improve any
  Cloudflare or third-party services" (the data-usage docs page). The service terms say "Unless otherwise agreed, Cloudflare does not
  use any Customer Content to train generative AI tools", but also that Cloudflare "does not reference or use any Customer Content
  except as needed to provide and improve the Services", so "no training" is contractual and "no service improvement" rests on the
  docs page.
- Content, in the Workers AI section of the service terms: content "that we determine in our sole judgment to be illegal, harmful, or
  in violation of the Agreement may be blocked or removed", including "(c) content that discloses sensitive personal information,
  incites or exploits violence, or is intended to defraud the public"; also "any suspected violation of applicable third-party terms
  may result in immediate suspension of Cloudflare Services", and users "agree to the applicable third-party terms, including any
  acceptable use policies or other restrictions on use of such model". So model licences add their own rules: Gemma 4, gpt-oss, Qwen3
  and Granite are Apache-2.0; the Llama models carry Meta's use policy and should not be defaults.
- Structured output: "Workers AI can't guarantee that the model responds according to the requested JSON Schema"; a failure returns
  "JSON Mode couldn't be met", and JSON mode does not stream. The documented model list is old, so the D009 validator carries the load.
- Setup: an account id and an API token. "If you permit third parties to access your Cloudflare account (e.g., by providing your API
  token or using OAuth), you do so at your sole risk." Whether a third-party OAuth path exists is [U] (a spike).

**Groq Free** (rate limits, structured outputs, your data, deprecations; Services Agreement "Last Modified: June 22, 2026"; AUP
"Effective: October 15, 2025"; read 2026-09-27/28) [V]:

- gpt-oss-20b, gpt-oss-120b, gpt-oss-safeguard-20b and Qwen3.8-27B each get 30 requests a minute, 1K a day, 8K tokens a minute and
  200K tokens a day; "Rate limits apply at the organization level, not individual users." "Cached tokens do not count towards your rate
  limits", and prompt caching is automatic on the gpt-oss models.
- `strict: true` constrained decoding on "GPT-OSS 20B, GPT-OSS 120B, and Qwen 3.8 27B"; "Streaming and tool use are not currently
  supported with Structured Outputs"; every field must be required with `additionalProperties: false`.
- "Groq is not permitted to use Inputs or Outputs for training or fine-tuning any AI Model Services or other models, unless explicitly
  granted permission or instructed by Customer." "By default, Groq does not retain customer data for inference requests"; "All
  customers may enable Zero Data Retention (ZDR) in Data Controls settings."
- "Cloud Services and the AI Model Services under this Agreement are not for consumer use." "You must be 18 years of age or older to
  access or use the Cloud Services."
- AUP: no use "for child sexual abuse or exploitation, violence, violent extremism or terrorism, hate speech, harassment, or
  non-consensual intimate imagery or sexually explicit content that is illegal" (how far "that is illegal" reaches back is a reading
  question [U]) nor "to perform a lethal function in a weapon without human authorization or control"; also
  bans any "illegal, offensive, invasive, discriminatory, dangerous, harmful ... purpose". Exception route: "Customers who have
  implemented adequate safeguards and require additional flexibility for lawful business or research purposes, may contact Groq to
  request an exception."
- History: free- and developer-tier models were removed on 2026-07-17 (qwen3-32b, llama-4-scout), 2026-08-16 (llama-3.1-8b-instant,
  llama-3.3-70b-versatile) and 2026-09-14 (qwen3.6-27b, replaced by qwen3.8-27b), and compound and compound-mini were retired for
  everyone on 2026-09-21.

**Hugging Face** (OAuth, Inference Providers pricing and security; ToS "Effective Date: September 15, 2022"; read 2026-09-27/28) [V]:
"You can create or use OAuth apps without a client secret. This is useful for native apps, CLIs"; public apps use "device code or
authorization code flows with PKCE"; loopback redirects accept any port; the `inference-api` scope lets an app "Make inference requests
to Inference Providers on behalf of the user". Free users get "$0.10, subject to change" a month. "Hugging Face does not store any user
data for training purposes. We do not store the request body or response when routing requests through Hugging Face. Logs are kept for
debugging purposes for up to 30 days, but no user data or tokens are stored." Accounts from "at least age 13". Its OpenID metadata
lists only client-secret token authentication, which disagrees with the public-app docs [U; spike].

**Google AI Studio and the Gemini API free tier** (Additional Terms, "Effective March 23, 2026", page last updated 2026-04-28; pricing
updated 2026-09-24; Prohibited Use Policy last modified 2024-12-17; read 2026-09-27/28) [V]:

- "When you use Unpaid Services, including, for example, Google AI Studio and the unpaid quota on Gemini API, Google uses the content
  you submit to the Services and any generated responses to provide, improve, and develop Google products and services and machine
  learning technologies"; "human reviewers may read, annotate, and process your API input and output"; "Do not submit sensitive,
  confidential, or personal information to the Unpaid Services." Exception: "If you're in the European Economic Area, Switzerland, or
  the United Kingdom, the terms under 'How Google uses Your Data' in 'Paid Services' apply to all Services".
- "Use of Google AI Studio and Gemini API is for developers building with Google AI models for professional or business purposes, not
  for consumer use." "You must be 18 years of age or older to use the APIs." No use in API clients "directed towards or is likely to be
  accessed by individuals under the age of 18".
- Safety: "You may not attempt to bypass these protective measures ... Applications with less restrictive safety settings may be
  subject to Google's review and approval." War-game briefings may trip the default filters. The Prohibited Use Policy bars
  "generating or distributing content that facilitates" a list that includes "Violence or the incitement of violence", and "may make
  exceptions to these policies based on educational, documentary, scientific, or artistic considerations".
- Gemma 4 is free-tier only on the Gemini API (paid tier "Not available"; free tier "Used to improve our products: Yes"); structured
  output for Gemma is not documented [U].

**Mistral Free** (pricing; help articles; Commercial Terms effective 2026-09-25; Usage Policy effective 2026-06-11; read 2026-09-27/28)
[V]: "$10 /mo in API credits"; "Free mode (the default) has the lowest limits, intended for evaluation and prototyping"; in free mode
"we may use your data (input and output) to train our artificial intelligence models", with an opt-out. The Commercial Terms: "Mistral
AI will not use Customer Data or Outputs to train its artificial intelligence models except (a) when you (i) opted-in to training on a
Mistral AI Product set to opt-out by default or (ii) have not opted-out of training on a Mistral AI Product set to opt-in by default".
The Usage Policy lists, under illegal activities, "Content related to activities with high-risk of physical harm, such as weapons
development, military and warfare, management, or operation of critical infrastructure in energy, transportation, and water", and
states "Use of the Mistral AI Products to conduct or generate any activity or content that promotes, incites, threatens, or glorifies
violence is not permitted." Its scope: "This Usage Policy does not apply to Mistral AI Products deployed on a customer's
infrastructure, on the infrastructure of our partners, or to our open-source AI models and products." So Apache-licensed Mistral
weights served by others are outside it, and whether it reaches Apache models on Mistral's own API is [U].

**OVHcloud AI Endpoints** (getting started, updated 2026-03-19; free-API page; keyless `/v1/models`; read 2026-09-27) [V]:
"Anonymous: 2 requests per minute, per IP and per model"; "Access keys created from Public Cloud projects in Discovery mode (without a
payment method) cannot use the service"; user data is "never stored or used for model training"; hosted in Gravelines, France. The
keyless list served Qwen3.5-9B, Qwen3.8-27B, Qwen3.6-27B, gpt-oss-20b and -120b, Mistral Small 3.2 and others.

**Scaleway** (pricing, read 2026-09-27) [V]: "You benefit from a free tier on the first 1,000,000 tokens. You'll be charged from token
number 1,000,001." Ordering needs a card checked with a EUR 1 authorisation [V-3p via Scaleway's billing docs]. Zero retention by
default; Paris.

**Ollama Cloud** (pricing, cloud docs, ToS "Last updated: May 2026"; read 2026-09-27/28) [V]: "Starter usage credits included",
"Includes access to starter models", one concurrent request; "Prompt or response data is never logged or trained on"; "Usage is
measured in tokens at each model's rates"; "Ollama is one account per person"; "we may route to Europe and Singapore for additional
capacity"; "You must be at least 18 years old to use our services"; no "harmful, offensive, or illegal content". Its native API is the
one D022 already reaches for local Ollama.

**Cerebras** (rate limits; Terms of Use "Effective August 27, 2024"; read 2026-09-27/28) [V]: "New accounts receive $5 in free credits
after adding a verified payment method. These credits expire 30 days after they're granted." Its own FAQ answers "Is there a
permanently free tier? No." The Terms bar use "for benchmarking or competitive analysis of the Service" and content that "promotes
hatred, violence, or harm" or "otherwise may be harmful or objectionable (in our sole discretion)".

**Cohere trial** (pricing, rate limits, Terms of Use last updated 2022-09-07, Usage Policy 2024-11-21; read 2026-09-27/28) [V]: "API
calls made from a Trial API key are free. However, trial keys are rate limited and are not permitted to be used for production or
commercial purposes"; 1,000 calls a month. The Terms reserve rights to "IMPROVE AND ENHANCE THE COHERE SOLUTION ... AND BENCHMARK THE
FOREGOING, INCLUDING BY SHARING API DATA AND FINETUNING DATA WITH THIRD PARTIES" and state "YOU MAY NOT ACCESS THE COHERE SOLUTION FOR
PURPOSES OF MONITORING AVAILABILITY, PERFORMANCE OR FUNCTIONALITY, OR FOR ANY OTHER BENCHMARKING OR COMPETITIVE PURPOSES". The Usage
Policy bans "Any activities that relate to the production, sale, trafficking, or marketing of weapons or controlled substances."

**Z.ai** (Terms of Use last updated 2026-04-14; pricing; read 2026-09-27/28) [V]: GLM-4.7-Flash, GLM-4.5-Flash and GLM-4.6V-Flash are
free. The Terms bar "f) Creating or disseminating obscene, pornographic, violent, murderous, terroristic, or criminal incitement
content", state "Our service shall not be used for any prohibited end use, including military purposes", and require "AI-generated
Outputs shall be prominently marked at reasonable locations to indicate that it is generated by AI." The "military purposes" sentence
sits in the export-control section, so on a plain reading it targets real military end uses rather than fiction [I]; the "violent"
content item and the marking duty are enough on their own to keep Z.ai out. Zhipu and related entities were
added to the US Entity List effective 2025-01-16 (Federal Register 2025-00704). The MIT-licensed GLM-4.7-Flash weights carry none of
these service terms when run locally or on another host.

**NVIDIA API trial** (Trial Terms of Service "v. September 19, 2025", PDF text extracted and read 2026-09-27/28) [V]: §1.2 "for limited
trial purposes only and without use of the API Service or Generated Content in production"; "you may only use the API Service for
internal testing and evaluation purposes, not in production"; §4.2 users "may not copy, sell, rent, sublicense, transfer or distribute
or make available to others any portion of the API Service or Generated Content"; §4.11 "You will not use the API Service to create or
distribute to others any defamatory, obscene, pornographic, vulgar, offensive, or violent content"; §2.6(f) content must not "be
violent or threatening or promote violence"; §3.3 NVIDIA may use "(iv) User Content and Generated Content to improve NVIDIA products
and services, including AI models". OpenRouter's NVIDIA provider row links these terms, so they govern the NVIDIA-served `:free`
Nemotron endpoints (doc 48 round 0, runs Z13 and Z15).

**Together** (model page, read 2026-09-27) [V]: Ternary Bonsai 27B, the first-generation ternary model on Qwen3.6-27B, is listed at
"Input price $0.00 / 1M tokens" and "Available free on Together AI serverless infrastructure", with no end date or limit stated; a $5
minimum credit purchase is required. The direct API keeps prompts until an org admin enables ZDR (doc 48 §2.5), so synthetic suites
only.

**Retired or dead** [V]: "As of July 30, 2026, GitHub Models is now retired. The playground, model catalog, inference API, and bring
your own key (BYOK) are no longer available to any customer" (closed to new customers 2026-06-16, about 29 days' notice of full
retirement). Chutes shows no free tier; its $5-depositor free tier ended 2026-03-15 [V-3p].

### 2.3 Content and use policies for a military war-game editor [V quotes; I bands; not legal advice]

Plotroom's users write fictional combat: briefings, radio chatter, weapons loadouts, casualties. The table sorts services by how their
wording reads against that; none of them was asked.

| Band | Service or model | The clause | Exception or route |
| --- | --- | --- | --- |
| **No clause of its own** | OpenRouter | Defers to the Model and Provider terms (§7 item 8); may block "otherwise objectionable" input | None needed; the host decides |
| | gpt-oss, Qwen3, Gemma 4 (Apache-2.0 weights) | gpt-oss: "By using OpenAI gpt-oss-20b, you agree to comply with all applicable law." | Host terms still apply on top |
| **Ambiguous, with an exception** | Google (Gemini API, Gemma via Google) | Content that "facilitates" "Violence or the incitement of violence" | "exceptions ... based on educational, documentary, scientific, or artistic considerations" |
| | Groq | "violence" among prohibited uses | "may contact Groq to request an exception" |
| **Ambiguous, no exception** | Cloudflare Workers AI | "incites or exploits violence" | None; fiction unlikely to "incite", "exploits" is vague |
| | ModelRun (Modular AUP) | "gratuitously depicts or glorifies violence"; "Design, market, help distribute or utilize weapons, explosives, dangerous materials or other systems designed to cause harm to or loss of human life" | None |
| | Mistral (hosted, own products) | "weapons development, military and warfare" under illegal activities; content that "glorifies violence" | Scope excludes partners' infrastructure and "our open-source AI models" |
| | Cerebras | "promotes hatred, violence, or harm"; "harmful or objectionable (in our sole discretion)" | None |
| | Cohere | "weapons" production, sale, trafficking or marketing | Authorised research only |
| | Llama models (Meta AUP) | "Military, warfare ..." under activities that "present a risk of death or bodily harm"; "Violence or terrorism" under illegal activity | None |
| | Ollama Cloud | "harmful, offensive, or illegal content" | None |
| **Incompatible** | NVIDIA API trial | "offensive, or violent content"; no production; no distribution of Generated Content | None |
| | Z.ai | "violent, murderous, terroristic" content; no "military purposes" end use (export-control section); mandatory AI marking | None |
| | Muse-Glimmer-30B (weights, doc 48 O3) | Usage Policy bans "Military, warfare … applications" | Blocked on the owner (OWQ-26) |

Readings [I]: most clauses target incitement, glorification, real-world harm or illegality; a game briefing about a fictional
counter-attack is none of these on a plain reading, but "exploits violence", "military and warfare" and "violent content" are not
qualified by any of those words. Hosted safety filters may also refuse combat text, so the runner and the product must record a
content-filter finish reason as its own outcome, never as a model error (§5.9). Proposal: the D037 principle extended to services. A
service whose policy is incompatible is never a preset and never used for screening; an ambiguous one is a preset only after the legal
review and, where the wording is unqualified, the provider's written answer (OWQ-24, OWQ-26). *(Answered 2026-09-28 →
[D045](../decisions/D045-free-model-offer-policy.md) item 7 and [D047](../decisions/D047-military-use-policy-models-and-services.md).)*

### 2.4 Age, audience and region [V; I]

- **Age.** 18+: OpenRouter, Groq, Google, Ollama, Modular; age of majority: NVIDIA, Cohere, Thinking Machines; 13+ or the local age of
  digital consent: Hugging Face, Cerebras; Z.ai's service is "not directed to, or intended for, the individual under 18". The game is
  rated M 17+ by the ESRB ("Blood and Violence"), and part of its modding community is plausibly under 18 [I]. Plotroom collects no
  ages, so the connect card must show each provider's age rule verbatim, and Google's clause on apps "likely to be accessed by
  individuals under the age of 18" rules it out as a preset.
- **Consumer use.** Google ("not for consumer use") and Groq ("not for consumer use") aim at developers and businesses. Whether a
  hobbyist's own key for personal mission-making is "consumer use" is a question for counsel or the providers, not for Plotroom [I].
- **Region.** Google's available regions include every listed EU state, the UK, Switzerland, Ukraine and Kazakhstan, and omit Russia,
  Belarus, China, Hong Kong, Iran, North Korea, Cuba and Syria. Mistral's sanctions list names Cuba, Iran, North Korea, Syria and "the
  Crimea, Donetsk, and Luhansk regions of Ukraine"; Z.ai names "Iran, North Korea, Cuba, Crimea, Donetsk, or Zaporizhzhia"; OpenRouter
  lets model providers exclude countries (§5.7). Russian-speaking players are part of the community, so availability differs by user and
  the card must say so [I].

### 2.5 Free tiers are volatile [V; V-3p where marked]

| Date | Change |
| --- | --- |
| 2025-10-15 | Zed removed its free plan's 50 hosted prompts a month ("LLM bills have become our biggest expense") |
| 2026-03-15 | Chutes retired its free requests for $5 depositors [V-3p] |
| 2026-05-15 | Roo Code shut down, with its router and free "stealth" models |
| 2026-06-16 → 07-30 | GitHub Models closed to new customers, then retired |
| 2026-07-17 → 09-21 | Groq removed free- and developer-tier models four times |
| about 2026-08-14 | Mistral's free plan restructured to $10 of monthly credits [V-3p] |
| by 2026-09-07 | Cerebras's no-card free tier replaced by card-gated trial credits; a re-test got HTTP 402 [V-3p for the re-test] |
| 2026-09 | Ollama moved its cloud plans to usage credits [V-3p] |

Free model ids churn too: aider's hard-coded `deepseek/deepseek-r1:free` is no longer in OpenRouter's catalogue, and Mantella changed
its free default twice. Rule [I]: resolve free models from the live catalogue at each session start, show first-seen and last-seen
dates, and never substitute silently (D023 decision 3).

### 2.6 Corrections to doc 48 and its CSV (flagged, not edited here) [V]

- **Cerebras.** Doc 48 §2.1's row and TL;DR list a "Free trial (1M tokens/day at 5 RPM)"; the limits still match, but the trial now
  needs a verified payment method and its $5 expires in 30 days. The same applies to the gpt-oss-120b Cerebras row and the Qwen3.8-27B
  `free_tier` note in `cloud-candidates.csv`. That row's role cell says "about 61 min per battery at 5 RPM", which is doc 44's 304-call
  battery; battery B's 484 calls take about 97 minutes.
- **gpt-oss-20b.** Doc 48 R03's `coreweave/fp4` read status −2 over 30 minutes at 20:56 UTC but 99.62% over one day and is still ZDR;
  `akashml/fp4` ($0.02/$0.10) is cheaper and ZDR; `parasail/fp4` ($0.03/$0.15) is not cheaper. The cheapest endpoint overall,
  `darkbloom/fp8` ($0.018/$0.09), is not ZDR, so unpinned routing lands there.
- **Featherless.** For a harness, the floor in doc 48's "$25–50/month minimum" is $50. The $25/month Chat plan has "Unlimited tokens"
  but "is limited to human typed interactive chat use only", and its FAQ says "What isn't covered is app or API traffic, reselling,
  background automation and benchmarking" (<https://featherless.ai/pricing>, read 2026-09-27). The Developer plan is "$50 /credits per
  month", "Billed per token", and its credits never expire, so a screen of the Featherless-only models costs one $50 top-up, most of
  which stays as credit.
- **Mistral.** The hosted Usage Policy's "military and warfare" item bears on doc 48's R14 and R01 (Mistral's own API), softened by its
  scope sentence (§2.2).
- **OpenRouter free catalogue.** The 17th `:free` id is `nvidia/nemotron-3.5-content-safety:free`, a classifier; `liquid/lfm-2.5-2.6b:free`
  has mandatory reasoning, so round 0's Z14 cannot run it with thinking off (doc 48 already plans effort low).

## 3. How other open-source apps offer "free" AI

### 3.1 What they did [V unless marked; sources in §Sources]

| App | Free path | Outcome | Lesson [I] |
| --- | --- | --- | --- |
| aider (CLI) | Asks once "Login to OpenRouter or create a free account?"; OAuth PKCE (S256) on a loopback port 8484–8584; picks a free model if the account is free tier | Works in production; the hard-coded free id no longer exists; the key sits in a plaintext file | Copy the PKCE mechanics; never hard-code a free id; keep keys out of files |
| Continue | A vendor-proxied "free trial" | Silently switched to GPT-3.5 (issue #913); local configs failed when its service was down; acquired, repository read-only | A vendor proxy ends with the vendor; never silently downgrade |
| Cline | Rotating free promotions through its own account | "Free model usage may be used to help improve model performance and quality"; telemetry leaked clicked prompt text while off (#3361) | Promotions rotate and train; a telemetry switch must be tested, not trusted |
| Roo Code | Free "stealth" models on its router; OpenRouter OAuth over a custom URI scheme without PKCE | Shut down 2026-05-15 | Avoid OAuth without PKCE; a vendor router is a single point of failure |
| Kilo Code | "kilo-auto/free" routes to free models | Warns: Auto Free "may route your requests to providers that log prompts and outputs and use them to improve their services"; acquired 2026-07-15 | Copy the plain warning; never auto-route user content to training hosts |
| Zed | $0 plan with own keys; hosted prompts removed | Keys in the OS keychain; data sharing opt-in; "disable all AI features" | Keychain storage; an AI-off switch; whose terms apply is stated |
| Jan | Downloads a default model at first launch; cloud by pasted key | "That's between you and them - Jan just makes the introduction" | Good disclosure; the automatic download conflicts with D008 |
| Open WebUI, LibreChat, AnythingLLM | No free model; bring your own; LibreChat keys expire on a user-chosen timer; AnythingLLM shows a privacy card per provider | AnythingLLM's telemetry switch leaked (#5496) | List every default connection; per-provider cards with facts, not only links |
| Copilot for Obsidian | Own keys or local models | "Choose your data route deliberately" | State the data route |
| Blender extensions | Online access off by default | "Extension must not send data to any remote locations without authorization from the user"; no keys "blocking functionality" | Matches D008 and the No-AI path |
| Mantella (a game mod) | Out of the box: OpenRouter with "Gemma 4 26B A4B (free)", key pasted into a text file | Works for a combat-game community; default changed twice; no privacy notice although that endpoint keeps prompts 55 days | The closest analogue: it works, with churn and no disclosure |

### 3.2 Three patterns and how they fared [V; I]

(a) Free usage paid by the app's vendor (Continue, Cline, Roo, Kilo, Zed): every one ended, rotated or changed owner in 2025–2026.
(b) Platform free tiers (GitHub Models, Gemini CLI's free tier): cut or retired. (c) The user's own account on a neutral provider,
reached by OAuth or a pasted key (aider, Mantella, LibreChat, Jan, AnythingLLM): survived, though the individual free model ids churn.
Plotroom can only take pattern (c) (§1.3).

### 3.3 Off-limits: consumer-subscription sign-in [V]

Anthropic: "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests
through Free, Pro, or Max plan credentials on behalf of their users." Google, on Gemini CLI: "Using third-party software, tools, or
services to harvest or piggyback on Gemini CLI's OAuth authentication to access our backend services is a direct violation". Plotroom
never offers such a sign-in.

## 4. Recommended flow: "Connect a model" (proposal)

**Status: implementation placeholder.** It depends on OWQ-24 (which services) and OWQ-25 (aggregators as first-class providers), and
needs a design-gap request before code (doc 48 §7.4 items 1–2 are its nearest candidates). *(2026-09-28: OWQ-24 answered →
[D045](../decisions/D045-free-model-offer-policy.md), OWQ-25 → [D046](../decisions/D046-aggregators-as-first-class-providers.md);
item 2 filed as [DG039](../design-gap-requests/DG039-downstream-hosts-behind-aggregators.md), open, which steps 1 and 5–7 wait
on.)* Wilco stays off by default (D004), nothing touches the network before the user picks, and Wilco can never start the flow or
change its settings (`AGENTS.md`; D008 item 2).

0. **Entry.** Settings → Wilco → "Connect a model" shows three equal cards: "On this PC (free, offline)" through the Model Manager
   (D022, D037); "Free cloud model with your own account"; "Your own key or endpoint". Nothing is preselected.
1. **Disclosure card before any network call**, built only from dated, curated data shipped with the release: the provider and, for an
   aggregator, the host that will serve the model; what "free" means (limits, reset time, "as-available", may disappear any day); the
   provider's age rule verbatim; the data route ("your mission text, briefings and names go to OpenRouter and then to ModelRun"; no
   Plotroom server, no shared key); training and retention as a dated fact; a content note ("fictional military content is judged under
   each provider's and model's policy; some may refuse it"); links to each policy; "Not legal advice". The button reads "Continue to
   OpenRouter".
2. **OAuth PKCE** [V mechanics; I design]: the system browser, never an embedded webview (RFC 8252 §8.12: "native apps MUST NOT use
   embedded user-agents"); always `S256` (RFC 8252 §6: public native clients "MUST implement" PKCE); one listener on an ephemeral
   loopback port with a random path and `state`, a 5-minute timeout and `key_label=Plotroom`. RFC 8252 §8.3 prefers the `127.0.0.1`
   literal ("the use of localhost is NOT RECOMMENDED"); whether OpenRouter accepts it is [U]. Fallbacks: OpenRouter's headless mode
   ("A code_challenge is required"; the code "expires after 10 minutes"), then a pasted key. Exchange at
   `https://openrouter.ai/api/v1/auth/keys`.
3. **Key storage** in the OS keychain, never in settings, project files or logs; `sk-or-*` redacted everywhere. "Disconnect" deletes
   the local copy and links to the provider's key page to revoke it.
4. **Key check without a prompt**: `GET /api/v1/key` returns `limit`, `limit_remaining`, `is_free_tier`,
   `free_model_daily_requests`, `expires_at` and `allowed_data_regions`. A key with no limit gets a warning; the OAuth flow has no
   parameter to set one [V].
5. **"Free only" guard, on by default** (the product form of doc 48 §6.0's guard): only `<author>/<slug>:free` ids outside
   `openrouter/`, listed at price exactly 0 in the live catalogue at session start; `provider: {only: [endpoint], allow_fallbacks:
   false, require_parameters: true}`; stop on any `usage.cost` other than 0, a BYOK cost, or an unexpected model or provider.
6. **"Which models are free today"**: once the user has chosen OpenRouter, it is "the model provider the user configured" (D008 item
   1), so reading its keyless catalogue fits; cached with its date and blocked offline. Each row shows model, host, headquarters,
   precision, context, 1-day uptime, structured-output support, ZDR, licence and use-policy flags (as D037 does for local files), a
   per-endpoint qualification badge defaulting to "unqualified", and first-seen and last-seen dates. The API has no training or
   retention field, so those labels come from Plotroom's curated data or read "unknown" [V].
7. **Privacy default**: every request sends `zdr: true` and `data_collection: "deny"`, which today admits only
   `qwen/qwen3.8-27b:free` among free generalists. Free endpoints that keep or train on prompts sit behind an explicit per-model opt-in
   with a red label, and Plotroom never asks the user to enable OpenRouter's "may publish prompts" toggle.
8. **Capacity honesty** [I on doc 40]: at 50 requests a day, a Standard campaign run (about 650 calls) takes about 13 days; the card
   says so and presents free cloud as a taster. On Cloudflare, a product Pick capsule of about 2.3K tokens (doc 40 §5.1) costs about
   21 neurons on Gemma 4 26B-A4B, so the free allowance covers roughly 450 calls a day, about 1.5 days per campaign run; on Groq's
   200K tokens a day it is roughly 80 calls, more on gpt-oss when prefixes cache. The run panel shows requests left and the reset time. A daily-cap 429, a guardrail 404
   ("no endpoint meets your privacy setting"), a vanished model or a 402 each give a visible choice, never a silent switch (D023
   decision 3).
9. **"Check this model"** runs Plotroom's synthetic suites under the free-only guard, shows first how much quota it will use ("30 of
   your 50 free requests today"), and sets the per-endpoint badge; the same machinery serves §5 (doc 48 §7.4 item 4).

Other providers follow the same card: Cloudflare as a guided token setup (Apache-2.0 models only, never Llama), Groq as a user key with
strict schemas, Hugging Face sign-in after a spike on its public-client token exchange. Attribution headers stay off
(`X-OpenRouter-App-Visibility: hidden` if any are sent). Registering Plotroom as an OAuth app with Hugging Face, and asking OVHcloud,
Groq and Modular in writing about presets and fictional military content, are owner steps (OWQ-24).

## 5. Cloud-first screening

### 5.1 The rule and what a cloud copy can tell us

The owner's rule (D044): a model that could run on the reference PC is first screened on a cloud copy of the same weights, and tried
locally only if the screen is promising. What a cloud copy is [I on doc 48 §4]: the same weights at a different precision (usually bf16
or fp8, sometimes fp4), under a different engine, chat template and schema implementation, on one host whose serving may be defective.
So it answers "is this model worth a 14–22 GB download and a tuning session?" It does not answer "does the Q4 file on the pinned
`llama-server` build pass?", which only the local run can, and which alone sets a badge (D022 item 4; D037).

### 5.2 Battery S (proposal) [I on V]

| Suite (arm) | k | Calls | Input tokens (local) | Visible output (local) |
| --- | --- | --- | --- | --- |
| pick-hard, no card | 3 | 90 | 27,180 | 630 |
| pick-hard, cards | 3 | 90 | 39,690 | 630 |
| fill | 3 | 36 | 15,516 | 1,800 |
| explain, cards | 2 | 20 | 6,100 | 1,680 |
| text, no card | 2 | 20 | 3,240 | 380 |
| **S** | | **256** | **91,726** | **5,120** |

Per-call means come from doc 48 §1.2. With prices P in USD/MTok, the cloud-to-local token ratio τ (planned at 1.3) and θ reasoning
tokens per call:

```text
USD(S) = τ × (0.0917 × P_in + 0.00512 × P_out) + 0.000256 × θ × P_out
```

S is 53% of battery B's calls, 62% of its input and 46% of its output; the formula reproduces doc 48's B figure for Ministral ($0.0205)
when B's coefficients are used. Why these suites: they carry exactly the metrics of doc 47 §6.3's rule for replacing the default and
its offload bar; they use the local records' k and item seeds, so every cloud call pairs item by item with a later local run (menu order
is seeded by item and sample); `pick` is at the ceiling (the default's pass^3 is 0.967 in both conditions) and separates models less
than `pick-hard` (3 discordant menus against 19 in doc 46); `knowledge` scored 0 of 24 without cards for every build and is not in the
decision rule. S is the suite set doc 47 already specifies for the Bonsai paired probe. At 30 menus only differences of about 10
points stand out from noise (doc 44 §6), so S screens and never qualifies.

### 5.3 Availability and cost per candidate (prices 2026-09-27; τ = 1.3; reasoning off unless stated) [V hosts; I costs]

Every row, with its second host, precision and notes, is in
[`data/cloud-screening-candidates.csv`](data/cloud-screening-candidates.csv).

| Candidate (doc 47 role) | Screen endpoint(s), all on OpenRouter's ZDR list unless marked | Precision | S cost (USD) | Free same-weights route | Verdict [I] |
| --- | --- | --- | --- | --- | --- |
| Qwen3-30B-A3B-Instruct-2507 (shortlist 2, offload) | `nebius/fp8` $0.10/$0.30; `siliconflow/fp8` $0.09/$0.30 | fp8 | 0.0139 + 0.0127 | None (Cloudflare's `qwen3-30b-a3b-fp8` is the hybrid-thinking checkpoint, a different model) | **Screen first** |
| Gemma 4 26B-A4B-it (shortlist 3, offload) | `coreweave/bf16` $0.10/$0.30; `deepinfra/fp8` $0.07/$0.34 | bf16, fp8 (non-QAT) | 0.0139 + 0.0106 | OpenRouter `:free` and Gemini API (no schema; not ZDR or trains); Cloudflare (≈1,270 neurons); Scaleway 1M tokens | **Screen first** |
| Qwen3.5-35B-A3B (alternate) | `deepinfra/fp8` $0.14/$1.00; `parasail/fp8` $0.15/$1.00 | fp8 | 0.0234 + 0.0245 | None | **Screen first**; thinking on by default |
| Qwen3.6-35B-A3B (alternate) | `akashml/fp8` $0.10/$0.90; `parasail/fp8` $0.15/$1.00 | fp8 | 0.0179 + 0.0245 | Scaleway 1M tokens (EU) | **Screen first**; thinking on by default |
| gpt-oss-20b (watch) | `akashml/fp4` $0.02/$0.10; `deepinfra/bf16` $0.03/$0.14 | fp4 (native MXFP4), bf16 | 0.0107 + 0.0153 at θ = 300 | Groq Free (strict); OVHcloud anonymous; Cloudflare (≈4,440 neurons) | **Screen first**; reasoning mandatory, lowest "low" |
| Ternary Bonsai 2 27B (optional probe) | `darkbloom/int4` $0.075/$0.50 (**not ZDR**) | int4 label [U] | 0.0123 | None | **Screen first**; synthetic only |
| Qwen3.8-27B (Bonsai comparator) | `darkbloom/fp4` $0.069/$2.20 (not ZDR) | fp4 | 0.0229 | OpenRouter `:free` (ModelRun fp4, ZDR); Groq Free; OVHcloud | With Bonsai only |
| Ministral 3 3B (doc 44, measured) | `mistral/zdr` $0.10/$0.10 | undisclosed | 0.0126 | Mistral Free (trains unless opted out) | Calibration anchor |
| Qwen3-4B-Instruct-2507 (shortlist 1) | nscale via the HF router $0.01/$0.03 | undisclosed | 0.0014 | HF free credits (≈70 runs of S a month) | Screen in parallel |
| Granite 4.2-3B (carry-over) | DeepInfra via the HF router $0.03/$0.12, schema flag false | undisclosed | 0.0044 | HF free credits | Local first; cloud no-schema arms optional |
| Qwen3.5-9B (doc 14 T2a) | `deepinfra/bf16` $0.10/$0.15 | bf16 | 0.0129 | OVHcloud anonymous; HF credits | Optional |
| GLM-4.7-Flash (new; not in doc 47) | Cloudflare $0.06/$0.40 (JSON mode not guaranteed); DeepInfra via HF (schema flag true) | [U] | ≈0.0098 (≈890 neurons, inside the free allowance) | Cloudflare free allowance; Z.ai free (terms incompatible: do not use) | Add to doc 47's offload watch first |
| Gemma 4 E4B QAT (the default), Qwen3.5-4B, Qwen3.5-2B, Gemma 4 E2B, Nanbeige4.1-3B | Featherless only ($50/month Developer credits; the $25 Chat plan excludes API traffic and benchmarking) | Original checkpoints; FP16 under 5B per doc 48 | 0.012–0.013 each (Nanbeige ≈0.065 with reasoning) + plan | None | Local; Featherless only for a calibration month |
| Granite 4.1 3B, Spark-X2.5-4B, NuExtract3, MiniCPM5-2B, Granite 4.0 1B / H-1B / H-Tiny, and the watch rows | None found (OpenRouter, HF providers, Featherless's 22,049 models, Cloudflare, NVIDIA) | — | — | — | **Local only** |
| Hy-MT2 7B / 1.8B / 30B-A3B, Bielik-11B | `tencent/fp8`; Public AI via HF | fp8; undisclosed | n/a until a translation or non-English suite exists (≈$0.01 and $0.05 per 256 calls) | None | Wait for the suite |

**Totals** [I]: first hosts (the five offload-class models, Bonsai 2, its comparator and the Ministral anchor) $0.128; second hosts for
the five offload-class models $0.088; **$0.22 on 13 endpoints and 3,328 calls**; Qwen3-4B-2507 adds a 14th endpoint inside HF's free
credits. A $1 key limit covers τ uncertainty and preflights. The floor is OpenRouter's card fee (5.5%, minimum $0.80) on the credit
bought; buying 10 credits once also lifts the `:free` limit to 1,000 requests a day, which fits round 0 into one day (doc 48 §6.0).
Doc 47's "skip" rows (Nemotron 3 Nano 30B-A3B, LFM2.5-8B-A1B, Olmo 3 7B, GigaChat 3.1, Seed-X) are out of scope.

### 5.4 Zero-spend routes, and why paid pinned endpoints are recommended [V; I]

| Route | Serves (same weights) | Limit for S | Catch |
| --- | --- | --- | --- |
| OpenRouter `:free` | Qwen3.8-27B (ZDR, strict flag); Gemma 4 26B-A4B (no schema) | 256 calls ≈ 6 days at 50 a day, 1 day at 1,000 | Doc 48 round 0 already plans these |
| Groq Free | gpt-oss-20b, Qwen3.8-27B with `strict: true` | S on gpt-oss-20b ≈ 202,700 tokens with reasoning; about one day's 200K TPD, less with cached prefixes | 8K tokens a minute: about 25 minutes minimum |
| Cloudflare Workers AI | Gemma 4 26B-A4B (≈1,270 neurons), gpt-oss-20b (≈4,440), Qwen3.8-27B (≈6,810) | Several runs a day | Schema not guaranteed |
| Hugging Face credits | Qwen3-4B-2507 (nscale), Granite 4.2-3B, Qwen3.5-9B | $0.10 a month | Schema per provider flag |
| OVHcloud anonymous | Qwen3.5-9B, Qwen3.8-27B, gpt-oss-20b | 2 a minute per model: about 2 hours per model, models in parallel | Terms silent on use by tools [U] |
| Scaleway | Gemma 4 26B-A4B, Qwen3.6-35B-A3B | 1M tokens once ≈ 7 runs of S | Card required |
| Google AI Studio | Gemma 4 26B/31B | Unpublished | Trains outside EEA/UK/CH; synthetic only |

Recommendation [I]: the harness screen runs on **paid, pinned, ZDR, strict-schema endpoints**, because cents buy comparability
(enforced schema, known precision, two hosts, no training) and the free routes give single hosts, missing schemas or data terms that
fit synthetic suites only. Free routes serve smoke tests, no-schema arms and round 0. Each account is the owner's to create; agents never
create accounts or handle keys.

### 5.5 Precision and serving caveat [I on V doc 48 §4.1, doc 46]

- fp8 is near-lossless and INT4 weight-only recovered 99.36% on Llama 3.1; doc 46 found no detectable difference between Q4_K_M and
  UD-Q4_K_XL. So a cloud copy is usually an **optimistic bound** for the local Q4 file: a cloud loss is informative, a cloud win
  provisional.
- The bound is weakest where it matters: models of 4B or less lose the most at 4 bits (Llama-3.2-1B lost 16 IFEval points); Gemma 4
  26B-A4B's QAT Q4 agrees with its BF16 QAT checkpoint on the top token only 85.63% of the time while the hosts serve the non-QAT
  checkpoint; Qwen3.6-35B-A3B at Q8_0 already has a KL divergence of 0.177 on tool calls.
- The bound can point the other way: serving defects (templates, reasoning parsers, schema engines that accept a schema and ignore it)
  can make a host worse than local. gpt-oss's fp4 hosts serve the same MXFP4 numerics as the local GGUF, so a gap there is engine,
  Harmony template or grammar, not precision. Doc 44's zero parse failures came from local grammars and do not carry over.
- So a **drop** needs clean serving (the conformance canary passes, no reasoning leak) and, for the offload rows, two hosts that agree
  (doc 48 §4.3). Never reject a model on a single free host's result.

### 5.6 Promotion rule (proposal) [I]

The bar is the provisional default's local record (Gemma 4 E4B QAT on llama.cpp, doc 46 §2.4–§2.5): `pick-hard` pass^3 25/30 without
cards and 26/30 with cards; planted escapes 8/9 and 9/9 with no false escapes; Fill all fields right per call 0.861 (31/36) and
whole-record pass^3 9/12; explanations passing both samples 6/10.

- **Must-pass, all of:** strict-schema conformance at least 95% of calls; zero reasoning tokens on thinking-off calls (or the lowest
  effort, recorded, for mandatory-reasoning models); planted escapes caught at least 8/9 in each condition; no false escapes.
- **Promote to a local Q4 trial if either:**
  - *General (dense T1)*: `pick-hard` pass^3 at least 24/30 without cards and 25/30 with cards, and Fill all fields at least 29/36 per
    call or whole-record pass^3 at least 9/12. That is within one menu or two calls of the default; the tolerance is small because the
    cloud copy already has the precision advantage.
  - *Specialist*: `pick-hard` at least 3 menus above the default in either condition; or Fill pass^3 at least 11/12, or both span fields
    at least 0.8; or explanations at least 9/10 with no invented fix; or, for offload models, whole-record Fill pass^3 at least 10/12
    with no `pick-hard` regression (doc 47 §6.3 item 3).
- **Drop (no local run):** 3 or more menus below the default in both `pick-hard` conditions and Fill all fields at most 27/36; or a
  must-pass failure that persists on a second host; or, for offload rows, both hosts miss whole-record Fill 10/12 (doc 48 §6.5).
- **Otherwise grey:** go local only for a secondary advantage (memory, CPU tier, Czech, Polish or Russian, no thinking switch to get
  wrong, a cleaner licence); else park until the 100-menu instrument (doc 44 §5.4 item 1).

### 5.7 Local confirmation at Q4 and calibration [I]

- Run the same battery S (same seeds, k = 3 and k = 2) on the pinned `llama-server` build with the exact file the Model Manager would
  ship. The promotion stands if the local Q4 run is within 1 menu per `pick-hard` condition and 2 Fill calls of its cloud copy, or still
  meets doc 47 §6.3.
- A local drop of 3 or more menus in both conditions is a quantisation or engine gap: apply doc 48 §4.3 (a Q8 GGUF on the same engine)
  before rejecting, and consider a larger quant where memory allows.
- Badges come only from local qualification (doc 21's bar; D022 item 4; D037). A cloud screen never sets a user-facing badge.
  *(2026-09-28: this covers screens of local candidates; a free cloud setup offered under
  [D045](../decisions/D045-free-model-offer-policy.md) is qualified on that setup itself, per step kind; see D044's amendment note.)*
- Calibrate first with one anchor measured on both sides: Ministral 3 3B (`mistral/zdr`, $0.013; its local `pick-hard` arm must run
  first) or Qwen3-4B-2507 (nscale, $0.0014; after its doc 49 run). Featherless is the only way to calibrate the default itself (a $50
  Developer top-up, OWQ-27). *(Answered 2026-09-28: OWQ-27 (b), without the top-up; D044's amendment note.)*

### 5.8 Order, time saved and conflicts with recorded plans [I on V]

- **Where it saves time:** the offload and Bonsai rows. The five offload files total about 84 GB (Qwen3-30B-A3B-2507 17.69, Gemma 4
  26B-A4B QAT 14.25, Qwen3.5-35B-A3B 17.49, Qwen3.6-35B-A3B 22.13, gpt-oss-20b 12.11), about 39 minutes of downloading at doc 46's
  35–37 MB/s, before `--n-cpu-moe` tuning. Under offload, S's 91.7K prompt tokens take about 4–31 minutes per model and run at
  50–370 tokens/s on the Pascal card; PrismML's Bonsai fork needs about 1.5–2.5 hours per arm. In the cloud S takes about 4–13 minutes
  per endpoint at 1–3 s a call, with endpoints in parallel.
- **Where it does not:** dense 1–4B models run S locally in about 6–9 minutes, and most have no host. The cloud buys only parallelism
  while the GPU is busy.
- **Suggested order:** (1) land the cloud backend of `tools/local-qual` and run one calibration pair; (2) the four offload models on two
  ZDR hosts each, then gpt-oss-20b at fp4 and bf16, then Bonsai 2 with its comparator (synthetic suites only); (3) Qwen3-4B-2507 on
  nscale; (4) local Q4 runs only for models that pass.
- **Conflicts to settle, not settled here:** doc 48's status line defers round 1 until doc 49 and lands the cloud backend only after
  doc 49's local run; doc 47 §6.1–§6.2 put local runs first. D044 applies the owner's rule to models not yet run locally; the schedule
  change for the tool patch and any spend are OWQ-27. Round 1 proper (the uplift ladder and frontier comparators) stays deferred.
  *(Answered 2026-09-28 → D044's amendment note: the patch lands after doc 49's run, not before its remaining rows; the spend is
  option (b); round 1 stays deferred.)*

### 5.9 Terms that bear on screening [V quotes; not legal advice]

- **Benchmarking clauses:** Cerebras bars use "for benchmarking or competitive analysis of the Service"; Cohere bars access "FOR ANY
  OTHER BENCHMARKING OR COMPETITIVE PURPOSES"; Featherless's $25 Chat plan excludes "benchmarking" (the Developer plan's table
  allows production API use and background automation and says nothing about benchmarking [U]). None of these is a screening host on
  those terms. Cloudflare's Self-Serve Agreement §2.2.2 allows benchmarks, but a published one must "include ... all information
  necessary to replicate such benchmark tests" and grants Cloudflare the same right; this matters only if host-by-host results are
  published. Its §2.2.1(e) also bars introducing "software or automated agents or scripts into the Services so as to produce multiple
  accounts, generate automated searches, requests or queries, or to strip or mine data"; API calls are Workers AI's documented use, so
  we read this as aimed at abuse of the web services, not at an API client [I; not legal advice].
- **Red teaming:** OpenRouter bars adversarial testing ("prompt injection, jailbreaking, or taking any other adversarial action designed
  to compromise any Models and/or violate any Model Terms", §7 item 11) without prior written approval. Today's suites contain no
  injection items; a future suite testing resistance to untrusted mission text must not run through OpenRouter without that approval.
- **Content filters:** the runner records a content-filter finish reason as its own category, never as a wrong answer or an error.
- **Services whose terms are incompatible** (NVIDIA trial, Z.ai) are not used for screening; combat-flavoured suites (text, knowledge,
  briefing items) never go to them (OWQ-26). *(Answered 2026-09-28 → D047: those two services are not used at all, and
  combat-flavoured items never go to any host with a violent-content clause.)*

## 6. Implications for D021, D022, D023, D037 and the Model Manager [I]

- **D021 (provider layer).** Add free-provider presets as dated, curated data (endpoint, pinned free id resolved live, privacy flags,
  age rule, data facts, policy links, first-seen and last-seen); OAuth PKCE on loopback; keys in the OS keychain; the free-only guard;
  the serving host shown per call; reasoning sent explicitly; content-filter outcomes as their own category. These extend the
  proposals in D021's amendment note. *(2026-09-28: the presets, offered per step kind only where qualified, are
  [D045](../decisions/D045-free-model-offer-policy.md); the route, privacy flags and serving host per call are
  [D046](../decisions/D046-aggregators-as-first-class-providers.md); the other items stay proposals.)*
- **D022 (Model Manager).** "Check this model" gains a cloud counterpart that shares the harness with §5; a cloud screen is recorded
  per (endpoint, precision, date) and never shown as a badge. The Manager's catalogue could carry a "screened in the cloud" note beside
  licence and use-policy flags.
- **D023 (model strategy).** No change to the three paths. Free cloud is a taster; local is the only free path with no expiry; free
  tiers are volatile, so every failure is a visible choice (decision 3). The owner's direction (1) is answered by L1, not L2.
- **D037 (recommended list).** Its use-policy rule is about local files. Proposal: the same principle for services (§2.3), decided by
  the owner in OWQ-24 and OWQ-26. *(Answered 2026-09-28 → D045, D047.)*
- **D044 (new).** Records the cloud-first rule; the protocol of §5 stays a proposal until the owner adopts it.
- **Design-gap candidates** (to be filed in `docs/design-gap-requests/`): free-provider preset data and its refresh (who curates it,
  how often, what happens when a free id disappears); a "screened, not qualified" state in the model catalogue; doc 48 §7.4 items 1
  (cloud artifact identity) and 2 (aggregators and the outbound-traffic invariant), which OWQ-25 would settle. *(2026-09-28: OWQ-25
  answered → D046; item 2 filed as DG039; the other candidates are not filed yet.)*
- **Folding steps** for later: doc 48 §2.1 and `cloud-candidates.csv` (Cerebras, §2.6); a row for this doc and its two data files in
  `docs/README.md`.

## Open questions

1. Which free services, if any, Plotroom presets, and how (OWQ-24). *(Answered 2026-09-28 →
   [D045](../decisions/D045-free-model-offer-policy.md).)*
2. Aggregators as first-class providers (doc 48 OQ10 → OWQ-25). *(Answered 2026-09-28 →
   [D046](../decisions/D046-aggregators-as-first-class-providers.md); DG039 filed.)*
3. Testing models or services whose policies ban military uses or violent content (doc 48 OQ9 → OWQ-26). *(Answered 2026-09-28 →
   [D047](../decisions/D047-military-use-policy-models-and-services.md).)*
4. Spend and schedule for screening candidates with no free endpoint (OWQ-27). *(Answered 2026-09-28 →
   [D044](../decisions/D044-cloud-first-model-screening.md)'s amendment note: 10 credits once, a $1 screening key, the backend after
   doc 49's run.)*
5. Does Modular's AUP govern the ModelRun endpoint that serves `qwen/qwen3.8-27b:free` [U]? Ask OpenRouter or Modular.
6. Does OpenRouter accept a `127.0.0.1` callback (RFC 8252 §8.3) as well as `localhost` [U]? A spike.
7. Does Hugging Face's token endpoint accept public PKCE clients despite its OpenID metadata [U]? A spike.
8. Does Cloudflare offer a third-party OAuth route to Workers AI [U]? A spike.
9. Would OVHcloud allow a desktop tool to preset its anonymous tier, and would Groq grant an exception for fictional military content
   [U]? Owner outreach (OWQ-24).
10. Does Featherless's $25 Chat plan allow a batch harness? Answered on review: no; its pricing page excludes "app or API traffic,
    reselling, background automation and benchmarking", so a Featherless screen needs the $50 Developer plan (OWQ-27).
11. How large is Ollama Cloud's free starter allowance, and which models are "starter models" [U]?
12. Do failed requests count against OpenRouter's free daily limit [U]? (doc 48 §6.0 already counts every attempt.)

## Sources

All pages read on 2026-09-27 UTC; legal pages re-read late the same UTC day (the pass the records date 2026-09-28). Raw snapshots
were kept with the research notes, outside the repository.

**Keyless catalogues.** <https://openrouter.ai/api/v1/models> · `https://openrouter.ai/api/v1/models/<author>/<slug>/endpoints` (Qwen3.8-27B
and `:free`, Gemma 4 26B-A4B and `:free`, Gemma 4 31B `:free`, Qwen3-30B-A3B-2507, Qwen3.5-35B-A3B, Qwen3.6-35B-A3B, gpt-oss-20b,
Ministral 3B, Bonsai 2 27B, Nemotron 3 Super `:free`, LFM 2.5 `:free`, Hy-MT2, Granite 4.0 H Micro) · <https://openrouter.ai/api/v1/endpoints/zdr> ·
<https://openrouter.ai/api/v1/providers> · <https://router.huggingface.co/v1/models> ·
`https://huggingface.co/api/models/<repo>?expand[]=inferenceProviderMapping` (every candidate in §5.3) · <https://api.featherless.ai/v1/models> ·
<https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/models> · <https://integrate.api.nvidia.com/v1/models> · <https://ai-gateway.vercel.sh/v1/models>.

**OpenRouter.** <https://openrouter.ai/terms> (last updated 2026-08-31) · <https://openrouter.ai/docs/api/reference/limits> ·
<https://openrouter.ai/docs/guides/overview/auth/oauth> · <https://openrouter.ai/docs/use-cases/oauth-pkce> ·
<https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key> · <https://openrouter.ai/docs/guides/routing/provider-selection> ·
<https://openrouter.ai/docs/guides/privacy/provider-logging> · <https://openrouter.ai/docs/app-attribution> · <https://openrouter.ai/docs/faq>.
Hosts behind free endpoints: <https://www.modular.com/legal/terms> (2026-08-17) · <https://www.modular.com/legal/aup> (2026-03-30) ·
<https://thinkingmachines.ai/legal/tml-free-research-api-tier-terms-of-service.pdf> (2026-08-20).

**Cloudflare.** <https://developers.cloudflare.com/workers-ai/platform/pricing/> (2026-09-17) ·
<https://developers.cloudflare.com/workers-ai/platform/data-usage/> (2026-04-21) · <https://developers.cloudflare.com/workers-ai/features/json-mode/> ·
<https://developers.cloudflare.com/workers-ai/models/> · <https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/> ·
<https://www.cloudflare.com/service-specific-terms-developer-platform/> · <https://www.cloudflare.com/terms/> (2025-09-12).

**Groq.** <https://console.groq.com/docs/rate-limits> · <https://console.groq.com/docs/structured-outputs> · <https://console.groq.com/docs/your-data> ·
<https://console.groq.com/docs/deprecations> · <https://console.groq.com/docs/prompt-caching> · <https://console.groq.com/docs/legal/services-agreement>
(2026-06-22) · <https://console.groq.com/docs/legal/ai-policy> (2025-10-15) · <https://console.groq.com/docs/badge>.

**Hugging Face.** <https://huggingface.co/docs/hub/oauth> · <https://huggingface.co/.well-known/openid-configuration> ·
<https://huggingface.co/docs/inference-providers/pricing> · <https://huggingface.co/docs/inference-providers/security> ·
<https://huggingface.co/terms-of-service> (2022-09-15) · <https://huggingface.co/content-policy> (2025-04-10).

**Google.** <https://ai.google.dev/gemini-api/terms> · <https://ai.google.dev/gemini-api/docs/pricing> (2026-09-24) ·
<https://ai.google.dev/gemini-api/docs/rate-limits> (2026-09-02) · <https://ai.google.dev/gemini-api/docs/available-regions> (2026-04-28) ·
<https://ai.google.dev/gemini-api/docs/structured-output> (2026-09-23) · <https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api> (2026-07-02) ·
<https://ai.google.dev/gemma/terms> · <https://policies.google.com/terms/generative-ai/use-policy> (2024-12-17) ·
<https://github.com/google-gemini/gemini-cli/discussions/20632>.

**Mistral.** <https://mistral.ai/pricing> · <https://legal.mistral.ai/terms/commercial-terms-of-service> (2026-09-25) ·
<https://legal.mistral.ai/terms/usage-policy> (2026-06-11) ·
<https://help.mistral.ai/en/articles/698531-why-am-i-hitting-api-rate-limits-and-how-do-i-increase-them> ·
<https://help.mistral.ai/en/articles/347617-do-you-use-my-user-data-to-train-your-artificial-intelligence-models> ·
<https://help.mistral.ai/en/articles/455207-can-i-opt-out-of-my-input-or-output-data-being-used-for-training>.

**Other services.** OVHcloud: <https://docs.ovhcloud.com/en/guides/public-cloud/ai-machine-learning/ai-endpoints-getting-started> (2026-03-19),
<https://docs.ovhcloud.com/en/guides/public-cloud/ai-machine-learning/ai-endpoints-capabilities>, <https://www.ovhcloud.com/en/public-cloud/free-ai-api/>.
Scaleway: <https://www.scaleway.com/en/pricing/model-as-a-service/>, its data-privacy and billing docs. Ollama: <https://ollama.com/pricing>,
<https://docs.ollama.com/cloud>, <https://ollama.com/terms>. Cerebras: <https://inference-docs.cerebras.ai/support/rate-limits>,
<https://www.cerebras.ai/terms-of-service>, <https://www.cerebras.ai/privacy-policy>. Cohere: <https://cohere.com/pricing>,
<https://docs.cohere.com/docs/rate-limits>, <https://cohere.com/terms-of-use>, <https://docs.cohere.com/docs/usage-policy>. Z.ai:
<https://docs.z.ai/legal-agreement/terms-of-use>, <https://docs.z.ai/guides/overview/pricing>, <https://docs.z.ai/legal-agreement/privacy-policy>,
Federal Register 2025-00704. NVIDIA: <https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf>.
Together: <https://www.together.ai/models/prism-ml-ternary-bonsai-27b>, <https://www.together.ai/pricing>. Alibaba:
<https://www.alibabacloud.com/help/en/model-studio/new-free-quota>. SambaNova: <https://docs.sambanova.ai/docs/en/models/rate-limits>. Vercel:
<https://vercel.com/docs/ai-gateway/pricing>. SiliconFlow: <https://docs.siliconflow.com/en/legals/terms-of-service>. Pollinations:
<https://raw.githubusercontent.com/pollinations/pollinations/master/APIDOCS.md>. Puter: <https://developer.puter.com/pricing/>. Featherless:
<https://featherless.ai/pricing>, <https://featherless.ai/docs/plans>. GitHub: <https://github.blog/changelog/2026-07-30-github-models-is-now-retired/>,
<https://github.blog/changelog/2026-06-16-github-models-is-no-longer-available-to-new-customers/>. Anthropic:
<https://code.claude.com/docs/en/legal-and-compliance>. Model policies: <https://huggingface.co/openai/gpt-oss-20b/raw/main/USAGE_POLICY>,
<https://dev.meta.ai/llama/llama4/use-policy/>. Rating: <https://www.esrb.org/ratings/6389/operation-flashpoint/>. RFC 8252:
<https://www.rfc-editor.org/rfc/rfc8252.html>.

**Other apps.** aider: <https://raw.githubusercontent.com/Aider-AI/aider/main/aider/onboarding.py>, <https://aider.chat/HISTORY.html>. Continue:
<https://github.com/continuedev/continue/issues/913>, <https://github.com/continuedev/continue>. Cline: <https://docs.cline.bot/getting-started/free-models>,
<https://github.com/cline/cline/issues/3361>. Roo Code: <https://github.com/RooCodeInc/Roo-Code>. Kilo: <https://kilo.ai/docs/getting-started/using-kilo-for-free>,
<https://www.anaconda.com/press/anaconda-acquires-kilo-code>. Zed: <https://zed.dev/pricing>, <https://zed.dev/blog/pricing-change-llm-usage-is-now-token-based>,
<https://zed.dev/docs/ai/privacy-and-security>. Jan: <https://www.jan.ai/docs/desktop/privacy>. Open WebUI: <https://docs.openwebui.com/getting-started/quick-start/>.
LibreChat: <https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/custom_endpoint>. AnythingLLM:
<https://github.com/Mintplex-Labs/anything-llm/issues/5496>. Copilot for Obsidian: <https://docs.obsidiancopilot.com/settings/>. Blender:
<https://extensions.blender.org/terms-of-service/>. Mantella: <https://art-from-the-machine.github.io/Mantella/pages/installation.html>,
<https://github.com/art-from-the-machine/Mantella/releases>.

**Third-party reports** [V-3p]: <https://dev.to/orca_forge/kurezitutokadobu-yao-deshi-eruwu-liao-llm-apipurobaidamatome2026nian-ban--4cdk>
(re-test 2026-09-07) · <https://anarlog.so/blog/mistral-api-key/> · <https://agentdeals.dev/vendor/cerebras> · <https://ollamatps.com/limits/> ·
<https://chutes.ai/news/community-announcement-february> · <https://community.groq.com/t/can-i-connect-to-regional-api-endpoints-with-groqcloud/835>
(redirected to groq.com on 2026-09-27; kept for the record).

**Repository.** Docs 40 (§5.1, the campaign row), 44 (§5.4, §6), 46 (§2.4–§2.5), 47 (§2.5, §2.7, §5, §6), 48 (§1.2, §2, §4, §6.0,
§6.5, §6.6, §7.4, OQ9, OQ10); D004, D008, D009, D010, D021, D022, D023, D026, D037; `docs/research/data/cloud-candidates.csv`,
`slm-candidates.csv`.

## Verification notes

### 2026-09-27/28, author checks at write-up

- **Method.** Four passes (inventory, terms, how other apps onboard, screening availability) read providers' own pages and keyless
  catalogues; two verification passes re-read the legal pages (late on 2026-09-27 UTC; "2026-09-28" in the records is the calendar
  date of that pass) and the catalogues (2026-09-27 20:56 UTC). No account
  was created, no key was used and nothing was sent to a model.
- **Corrections made in verification and reflected above:** the shared-key argument rests on credential disclosure, pooling,
  per-account capacity and liability, not on a blanket ban on apps (§1.3); OpenRouter has content (§6.7, §7 item 8) and country (§5.7)
  clauses; Cloudflare has its own violence clause; Meta's "Military, warfare" item sits under activities that "present a risk of death
  or bodily harm"; Mistral's training clause is quoted exactly and its Usage Policy has a scope sentence; ModelRun links to Modular's
  terms and AUP; Thinking Machines' free tier trains; Cerebras and Cohere bar benchmarking; OpenRouter bars red teaming without approval;
  Groq's compound retirement applied to everyone; Groq cached tokens do not count toward limits; Featherless's floor is the $25 Chat
  plan (superseded by the review below: that plan excludes API traffic, so the floor is $50); the paid screen is 13 endpoints and
  3,328 calls, not 11 and 2,800; the Gemini terms page reads "Effective March 23, 2026" and
  "Last updated 2026-04-28".
- **Arithmetic.** S's totals are §5.2's per-suite products of doc 48 §1.2's means. Every S cost in §5.3 and the CSV comes from §5.2's
  formula at the pinned prices; the 13-endpoint total ($0.2152), Cloudflare neuron counts (Gemma 1,266; gpt-oss-20b 4,444 at θ = 300;
  Qwen3.8-27B 6,814; GLM-4.7-Flash ≈890), Groq's 202,700 tokens, the 83.67 GB of offload files and the 4–31 minute prompt-processing
  range were recomputed.
- **Not verified:** anything a live call would show (schema enforcement per host, reasoning-off behaviour, served precision, τ, content
  filters on combat text); whether ModelRun is bound by Modular's AUP; OVHcloud's and Groq's answers on presets and fictional military
  content; Ollama's free allowance; the pages that did not render (Cerebras's inference PDF, Mistral's consumer terms, Poolside's
  terms).
- **Hygiene.** No private or unpublished project, local path, user name or e-mail address appears in this doc or its two CSV files
  (searched). Nothing here is legal advice.

### 2026-09-28, review pass (reads on 2026-09-27 between about 21:10 and 22:30 UTC)

- **Scope and method.** Reviewed this doc, both CSVs, D044, OWQ-24 to OWQ-27 and the pointers in docs 47 and 48. Re-read the
  providers' own pages and the keyless catalogues; no account, key or model call was used. Nothing here is legal advice.
- **Confirmed at the source** (verbatim where quoted above): OpenRouter's Terms (last updated 2026-08-31: 18+, API-key
  confidentiality, §7 items 3, 4, 8, 11 and 14, §5.1, §5.4, §5.6, §5.7, §6.7), limits page (20/min, 50/day, 1,000/day from 10
  credits, "Making additional accounts or API keys will not affect your rate limits", 402 on a negative balance), OAuth page ("any
  port", headless `code_challenge`, 10-minute code, no spend-limit parameter) and card fee (5.5%, $0.80 minimum); the live catalogue
  (17 `:free` ids as listed; only `qwen3.8-27b:free` on ModelRun fp4 and the two Ling specialists are free text endpoints on the ZDR
  list; null `expiration_date`; every §5.3 and CSV price and ZDR flag for the 13 paid endpoints, and darkbloom and plain `mistral` not
  ZDR); OpenRouter's provider rows linking ModelRun to Modular, Google AI Studio to Google Cloud's terms and NVIDIA to the trial terms;
  Cloudflare's pricing (10,000 neurons, $0.011 per 1,000, 00:00 UTC reset, the neuron rates), data-usage page, Workers AI service terms
  (violence clause, third-party model terms, "solely responsible for the acts of your End Users", page "Last updated: September 28,
  2026") and Self-Serve Agreement (§2.2.1(a), §2.2.2, "sole risk"); Groq's rate limits (30/1K/8K/200K on all four models), Services
  Agreement (June 22, 2026; §2 age, §3.1, §3.2, §4.2 training), AUP (October 15, 2025), your-data page and deprecation history;
  Google's Gemini API terms (effective 2026-03-23, updated 2026-04-28) and Prohibited Use Policy; Mistral's Usage Policy (2026-06-11);
  Modular's AUP (2026-03-30); Cerebras's trial FAQ and Terms; Cohere's trial clause and 1,000 calls a month; Z.ai's content, export
  and key clauses; OVHcloud's anonymous limit and payment-method rule; Hugging Face's $0.10 credits, routing-security text and OAuth
  (public apps, loopback any port, `inference-api`); Ollama's pricing FAQ and Terms (May 2026); Scaleway's 1,000,000-token free tier;
  Together's $0.00 Bonsai listing; the NVIDIA trial terms (v. September 19, 2025: §1.2, §1.4, §2.6(f) and (j), §3.3, §4.11); GitHub
  Models' retirement; Anthropic's consumer-login clause; the ESRB rating ("rated M for Mature 17+ ... with Blood and Violence").
  §5's arithmetic (battery S totals, every S cost, $0.2152 on 13 endpoints and 3,328 calls, neuron counts, Groq tokens, 83.67 GB)
  was recomputed and matches.
- **Corrected in this pass:** (1) Featherless: the $25 Chat plan excludes "app or API traffic, reselling, background automation and
  benchmarking", so a harness needs the $50 Developer plan (§2.6, §5.3, §5.7, §5.9, open question 10, the screening CSV, OWQ-27 and
  D044 P5; the author's note above is marked superseded). (2) OpenRouter's red-teaming definition sits in §7 item 11, not §5.9 (which is
  "Provider Requirements"), and continues "designed to compromise any Models and/or violate any Model Terms"; §8's research route is
  added. (3) The legal re-read was late on 2026-09-27 UTC, not "2026-09-28 (UTC)". (4) Google's policy bars content that "facilitates"
  violence; the qualifier was missing from §2.1, §2.3 and the CSV. (5) Cloudflare's "no service improvement" rests on the docs page,
  while the service terms allow use "as needed to provide and improve the Services"; only "no training" is contractual. (6) Groq's AUP
  item is now quoted in full, and its §3.2 account clauses are added to the shared-key argument. (7) Verbatim fixes: Modular's
  "gratuitously" (lower case, §11), Modular's weapons item in full, Google's "How Google uses Your Data". (8) Z.ai's "military
  purposes" sentence is marked as sitting in the export-control section. (9) CSV cells softened where a reading was stated as a grant:
  Cloudflare's third-party access is "contemplated, at the user's sole risk", not "allowed"; the Hugging Face button quote is about
  design, not permission. (10) The Groq regional-endpoint source (a community thread) now redirects to groq.com; marked. (11) D044:
  the owner's words are quoted beside the restated rule, with "the same weights" marked as a reading; the NVIDIA/Z.ai hold and the
  "round 1 stays deferred" line are labelled as interim practice and reading, not owner decisions; OWQ-27 option (a) now says it
  would narrow D044; OWQ-27's "for good" became "under today's published rule". (12) Doc 47's pointer no longer attributes the
  "hosted copy" qualifier to the owner; doc 48's pointer calls battery S a proposal and notes the Featherless floor. (13) §5.9 gains
  Cloudflare's §2.2.1(e) automated-requests clause with our reading.
- **Links.** All 131 URLs in this doc, the CSVs, D044 and the owner questions were requested: all resolve except the Groq community
  thread (redirect to the home page), `https://openrouter.ai/api/v1/auth/keys` (a POST-only endpoint named, not linked), Pollinations'
  GitHub file (rate-limited, 429) and Scaleway (a local certificate-chain error; the page itself read fine). Relative links resolve.
  Both CSVs parse with Python's `csv` module: 23 rows by 13 columns and 47 rows by 11 columns, no ragged rows, numeric price cells.
- **Not re-checked:** the Thinking Machines PDF, Mistral's Commercial Terms, Cerebras's age rule, Hugging Face's age rule and ToS
  password clause, OVHcloud's Gravelines location, and the other-apps table (§3).

### 2026-09-28, owner answers (pointers)

- The owner answered OWQ-24 to OWQ-27 on 2026-09-28 with the recommended options, and directed on 2026-09-27 that only free models
  that work with the harness are offered: allowed by their provider's terms, qualified per step kind, dated, re-qualified, with a
  clean fallback. Records: D045 (OWQ-24 and that direction), D046 (OWQ-25), D047 (OWQ-26), D044's amendment note (OWQ-27); DG039
  filed (downstream hosts behind an aggregator, open).
- Dated pointers were added to the status block, TL;DR, §2.3, §4's status line, §5.8, §5.9, §6 and open questions 1–4. The text,
  figures and proposals above are unchanged; where they differ from a record, the record governs (for example, the tool patch lands
  after doc 49's run, not first as §5.8's suggested order proposed).
- Verification (2026-09-28): §5.7 gained two pointers (its badge sentence covers screens of local candidates, not D045's qualified
  free cloud setups; the Featherless top-up was not chosen), and §6's D021 bullet gained a pointer to D045 and D046. §4's status line
  was re-wrapped. No text, figure or proposal changed.
