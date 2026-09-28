# D050: A UX standard for rate-limited operation, and a quota-aware router over user-authored route lists

> **Status:** accepted · **Decided by:** owner (go-ahead of 2026-09-28; doc 52's recommended options adopted) · **Decided:**
> 2026-09-28 · **Recorded:** 2026-09-28 · **Scope:** how Wilco behaves under provider rate limits, quotas and congested hosts on
> cloud setups: the standard it is held to, the router, and what the user sees. **Refines:** D023 decision 3 (read with route lists;
> see its note), D024 item 4 (a role binds to a route list per step kind), D026 item 2 (quota counted like money).
> **Related:** D004, D008, D009, D010, D021, D022, D045, D046, D047, D048, D049, D051. **Open parts:** doc 52 OQ6–OQ9 (congestion
> by time of day, Groq and Cloudflare mechanics, the tiny CPU stage, the quality of one cloud sample); cloud K per tier (doc 52 RG5 →
> DG021), lean capsules (RG6 → DG019, DG025, DG049), retry accounting (RG2 → DG016; the limit-outcome taxonomy → DG051), packing
> (RG7, not adopted); the release preset list, including Hugging Face's monthly credits (doc 52 OQ11), and the providers' written
> answers (D045 item 7; doc 52 OQ5); who curates the dated limit data (RG9, D045's open part); cross-model confidence escalation (doc
> 53 OQ2 → DG050, owner); DG039.

## Context

- The owner asked (2026-09-27) whether free providers' rate limits leave a UX "good enough for our standards". Doc 52 found that the
  limit that bit was shared upstream capacity, not the account quota: one free host answered 1 of 13 attempts in 17.6 minutes, and
  its `retry_after` hints said nothing about a throttle of over 15 minutes. In simulation no day completes on one free provider;
  every day completes on the user's own OpenRouter, Groq, Cloudflare and Hugging Face accounts behind a congestion-aware router
  with a local stage for Pick and Fill (doc 52 §2.3, §3.3–§3.6; simulated [I], with the placeholders it names).
- D023 decision 3 forbids silently moving a failed step to another model; doc 52 OQ2 asked how routing around a busy host fits it.
- The owner's go-ahead of 2026-09-28 (lightly edited): "Tiny models with no cloud availability should be tested directly on PC.
  Either way, except for GPG signing, we can do everything else." **Recommended option adopted under the owner's go-ahead; overrule
  on return.**

## Decision

1. **The UX standard (doc 52 §4; OQ1).** Rate-limited operation meets: **UX1** limit-induced interactive wait p90 ≤ 2 s a day,
   and each step's total response in its doc 53 latency class at p50; **UX2** any interactive wait over 10 s shows a non-modal card
   with the reason and choices; **UX3** at 60 s the code default stands, labelled and re-runnable in one click; **UX4** a light
   session and a mission build complete within one UTC day's free allowances on the recommended free setup, with nothing parked;
   **UX5** a campaign from a brief completes that day, or the plan card says before the run how long it will take, why, and the
   alternatives; **UX6** at least 99% of decisions answered, defaults kept for limits at most 1%, each labelled; **UX7** forecast
   cloud calls within ±15%, and a run shown as "fits today" never parks for quota; **UX8** every reroute, fallback, park and
   default kept is shown with its reason, no silent switch, and nothing is lost across a reset or restart; **UX9** at most 2
   immediate retries on one endpoint, no probe faster than a host's cooldown, and background work never spends the interactive
   reserve.
2. **The recommended free setup (OQ3).** The "connect a free model" flow leads to at least two free providers on the user's own
   accounts plus a local model for Pick and Fill; one provider alone is presented as a taster. The providers are those on D045
   item 7's release list (candidates today: OpenRouter, Groq, Cloudflare).
3. **Route lists, visible and user-authored (OQ2, RG1).** A role binds, per step kind, to an ordered route list of setups that the
   user wrote or accepted, shown on the plan card with its cost. On a **limit outcome** (upstream throttling, a spent allowance, a
   removed free model) the router may move a call to a later entry without a click per move; each move is recorded and shown with
   its reason. It never moves because a step failed its checks (that step still splits, D023 decision 3), never reaches a setup
   outside the list, and skips entries not qualified for the step kind unless the user accepted them as custom and unqualified.
   Under Confirm and Propose the stall card offers the choices and never times out into a yes; under Auto the list decides (D024).
4. **The router (doc 52 §5.1–§5.2).** Route around a congested host, never retry into it. One account per provider, created by the
   user; the router never creates, rotates or pools accounts or keys, never raises a cap and never uses cross-host fallbacks (D046
   pins routes). A quota ledger per account and pool reads the provider's own counters and headers, persists across restarts, and
   takes limits from dated data shipped with releases, never fetched from providers' pages (D008 item 5). Failed attempts are typed
   limit outcomes; a circuit breaker per serving endpoint cools, probes and demotes hosts, treating an upstream `Retry-After` as a
   floor and ignoring catalogue uptime. Interactive calls go first and keep a reserve of each allowance. Degrade downward: local,
   the route list, the paid backstop if enabled, then the code default or template text; never an unannounced bigger model.
5. **Paid backstop (OQ4, RG8).** Offered in the free flow as an opt-in on the user's own credits, never a default: a hard daily
   cap, two hosts per model, shown on the plan card. Once enabled it is the route list's last entry (doc 52 §5.2's `RouteList`), so
   item 3's "never outside the list" holds.
6. **Parking (OQ10).** A background run at a spent quota parks as `QuotaLimited` (`BudgetLimited` with the pool and reset time)
   and resumes automatically only if the user ticked that on the plan card for that run.
7. **Surfaces (doc 52 §5.4):** the plan card prices calls against today's allowances; a quota meter; the stall card; a background
   queue; per-decision reroute reasons in the inspector; the disclosure card's free-tier line computed per setup.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Best effort, no written standard (OQ1) | Nothing to test against; the owner asked for a standard |
| A click for every switch (OQ2, D023 read strictly) | A busy host raises a stall card at every call; a list written in advance keeps each switch the user's and visible |
| One free provider with retries | Fails every simulated day, even at 1,000 requests a day (doc 52 §3.6) |
| A Plotroom key, proxy or pooled accounts | Excluded by D045 item 2 and D008 |

## Consequences

- The provider seam (D021) gains the ledger, the limit-outcome taxonomy, host health and route lists as data; no provider library
  enters the domain crates. Doc 52 §5.2's type names and numbers (cooldown 15 s doubling to 10 minutes, a 70% background share,
  demotion below 50% of 10 attempts) are starting values [I], not rules.
- `tools/quota-sim`, doc 40 §7's replay tests and the run ledger check UX1–UX6; UX7–UX9 are design properties tested in code.
- Route-list entries are (preset, step kind) pairs with their own badges (D045 item 4; D048); none is qualified today, so free cloud
  stays custom and unqualified until qualification runs.
- Friction (D049): removes silent hangs and blind retries; adds the work of connecting two or three accounts, which the flow guides
  and the plan card justifies with numbers.
- Folding steps, not done here: doc 52's status line and §6; doc 38 §4.6 ("transport retries … never switch models") now reads with
  item 3; D024 and D026 pointer notes; D045's capacity line (doc 52 §6.3 item 1).

## Sources

Owner's question of 2026-09-27 and go-ahead of 2026-09-28; doc 52 (TL;DR, §2–§6, open questions); `tools/quota-sim/`; doc 40 §7;
doc 53 §4.3; D008; D021; D023; D024; D026; D045; D046; D048.
