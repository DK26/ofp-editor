# D045: Free models: presets on the user's own account, offered only where qualified per step kind

> **Status:** accepted · **Decided by:** owner (OWQ-24 b; direction of 2026-09-27) · **Decided:** 2026-09-27 (direction), 2026-09-28
> (OWQ-24) · **Recorded:** 2026-09-28 · **Scope:** which free cloud models and services Plotroom offers, in what form, and for which
> step kinds. Local models stay under D037. **Refines:** D021 (free-provider presets as provider data; doc 50 §6).
> **Related:** D004, D008, D010, D022, D023, D026, D031, D037, D044, D046, D047.
> **Open parts:** the preset list itself (fixed at release, item 7); the qualification bar and identity of a cloud setup (doc 48 §7.4
> item 1), the re-qualification cadence (doc 48 OQ11) and its triggers (DG012); who curates the dated preset data and how it is
> refreshed (doc 50 §6, a design-gap candidate); DG039 (downstream hosts; answered 2026-09-28 → D053); the wording for 18+ providers
> and a Hugging Face OAuth app (asked with OWQ-24, not answered by it); doc 50 OQ5 (whether Modular's policy covers ModelRun) and the
> spikes of OQ6–OQ8.

## Context

- The owner asked (2026-09-27) for "a free LLM service that is legal and OK to rely on", configured by default or at least offered for
  free (doc 50). No free service can ship working out of the box on a Plotroom-owned key: terms forbid disclosing or transferring keys
  and pooling accounts, free quotas belong to one account, Google requires paid services for apps used in the EEA, Switzerland and the
  UK, and a proxy would put a Plotroom server in the data path (doc 50 §1.3; D008). Readings of terms are ours, not legal advice.
- Free offers and free model ids churn: at least five free offers were cut or retired in 2026 (doc 50 §2.5). Most services' policies
  carry violence wording without a fiction exception, and several require users to be 18 or older (doc 50 §2.3–§2.4).
- The owner's direction of 2026-09-27, in the owner's words: "offer the user the free models that work perfectly with our harness".

## Decision

1. **Presets on the user's own account (OWQ-24 b).** "Connect a free model" presets sign in to, or set up, the user's own free
   account: OpenRouter first, by OAuth PKCE; then Cloudflare Workers AI (a guided token setup, Apache-2.0 models only) and Groq Free
   (the user's key). Option (b) also lists Hugging Face sign-in after a spike; the Answer line does not name it, so it stays a
   candidate under the same rules.
2. **No Plotroom-owned key, no proxy, no keyless default.**
3. **A dated disclosure card before any network call**: limits, the provider's age rule, the data route (behind an aggregator, the
   host that serves the model), training and retention, a content note on fictional military content, and "not legal advice". Wilco
   stays off by default (D004), nothing is sent before the user connects, and free cloud is shown as a taster beside local models.
4. **Only qualified free models are offered, per step kind** (the owner's direction). A free model is offered for a step kind (doc
   47: PICK, FILL, COMPOSE, DRAFT, EXPLAIN) only if its provider's terms allow the offer **and** it passed Plotroom's qualification for
   that step kind. Models that are not qualified are not offered; the user's own key-or-endpoint path (D023 decision 1) is unchanged.
5. **Dated and re-qualified.** The offered list carries each qualification's date and is re-qualified regularly, because free
   catalogues change. A qualification belongs to the setup it ran on (D022 item 4: per model setup and step shape); for a cloud setup
   the proposed identity is (provider, model, endpoint, precision, reasoning setting, date) (D021's amendment note, a proposal; open
   above). A D044 cloud screen of a local candidate is not a qualification and never sets a badge.
6. **Clean fallback.** When an offered free model disappears, loses its zero price or loses its qualification, nothing is lost: the
   user sees why and chooses what next (another offered model qualified for that step kind, a local model, their own key, or no AI).
   Never a silent switch (D023 decision 3). This is our reading of "falls back cleanly" beside decision 3.
7. **The preset list is fixed at release**, after the legal review before 1.0 (as D031 plans for the §7 wording) and the providers'
   written answers on fictional military content (Groq's exception route; OpenRouter or Modular on the ModelRun endpoint's policy;
   Cloudflare). Never presets: Google AI Studio's free tier, Mistral Free, the NVIDIA trial, Z.ai, Cohere's trial and Cerebras.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Listed providers only; the user pastes a key (OWQ-24 a) | No one-click path to a free model for non-experts |
| A Plotroom-owned key, a proxy or a keyless public endpoint (OWQ-24 c) | Key disclosure, transfer and pooling clauses; one shared OpenRouter key gives all users 50 requests a day together; Google's EEA, Swiss and UK rule; a proxy is a destination D008 does not allow |
| Offer every free model in the live catalogue | Free models differ widely on the harness's steps; the owner asked only for those that work with it |

## Consequences

- The provider layer (D021) carries the presets as dated, curated data: endpoint, free id resolved from the live catalogue at session
  start, privacy flags, age rule, data facts, policy links, first-seen and last-seen dates, and qualification per step kind with its
  date (doc 50 §4, §6; the data's shape is a proposal).
- OpenRouter presets send `zdr: true`, `data_collection: "deny"` and reasoning off (OWQ-24 b); aggregator safeguards are D046.
  Qualification runs Plotroom's synthetic suites (`tools/local-qual/`); on a host whose policy bans military uses or violent content,
  D047 applies.
- Capacity is shown honestly: at 50 free requests a day a Standard campaign run (about 650 calls) takes about 13 days (doc 50 §4 step
  8). Every limit, reset time and removal is visible in the run panel.
- Doc 50 §4's flow is the working design; its details beyond the items above (keychain storage, the free-only guard, "Check this
  model", OpenRouter's attribution headers kept off as OWQ-24's caveats say) stay proposals. The providers' written answers are
  owner actions, not yet recorded as sent.

## Sources

Owner direction of 2026-09-27; `OWNER-QUESTIONS.md` OWQ-24 (Answer of 2026-09-28); doc 50 (§1–§4, §2.3–§2.5, §6); doc 48 (§6.0,
§7.1, §7.4, OQ11); D004; D008; D021 (amendment notes); D022; D023; D031; D037; D044.

## Amendment notes

### 2026-09-28: DG039 decided by D053 (pointer)

A note under lifecycle item 5; [D053](D053-aggregator-downstream-hosts.md) governs (DG039 option B), decided under the owner's
delegation; the owner may overrule it on return. Item 3's disclosure card names the aggregator and every host the preset's setup may
reach before any call; the setup reaches only those hosts, adding one is a user action with a new card, and a response from any other
host, or with no served host reported, is flagged, never admitted, and pauses the setup until the user decides. The header's **Open
parts** gained a pointer; nothing above changed.
