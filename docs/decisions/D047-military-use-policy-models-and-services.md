# D047: Models and services whose policies ban military uses or violent content

> **Status:** accepted · **Decided by:** owner (OWQ-26 a) · **Decided:** 2026-09-28 · **Recorded:** 2026-09-28
> **Scope:** Plotroom's own evaluations (tests, screening, qualification) and presets that involve a model whose use policy bans
> military or warfare uses, or a hosted service whose usage policy bans military uses or violent content.
> **Refines:** D037 (the testing question its Consequences leave as "a separate call", doc 48 OQ9) and D044 (its open part OWQ-26 and
> the interim practice in its Consequences). **Related:** D008, D011, D045, D046.
> **Open parts:** which suite items count as combat-flavoured (no per-item flag exists yet); which host policies count as
> violent-content clauses (doc 50 §2.3's bands are a reading; the legal review before 1.0); the providers' written answers (D045
> item 7); label wording for such results.

## Context

- D037 keeps any model whose use policy bans military or warfare uses off the recommended list, and leaves whether Plotroom's own
  evaluations may test one as a separate call (doc 48 OQ9, row O3: Muse-Glimmer-30B's policy bans "Military, warfare …
  applications").
- Hosted services add their own clauses (doc 50 §2.3): Mistral's hosted Usage Policy names "military and warfare" content; the NVIDIA
  API trial bans "violent content"; Z.ai bars "military purposes" end use and "violent" content; Groq, Cloudflare, Modular (the
  ModelRun host) and Google have violence wording. These readings are ours, not legal advice.
- The suites are editor operations over code-owned menus plus English flavour text, so the risk of testing is low (OWQ-26).

## Decision

1. **Synthetic suites only.** Plotroom's own evaluations may test such models, and may run on such services, with the repository's
   synthetic suites only. The results are labelled and never become a recommendation or a preset. D037 is unchanged.
2. **Services with incompatible terms are not used at all**: the NVIDIA API trial and Z.ai, for no test, screen, qualification or
   preset. This drops doc 48 round 0's runs Z13 and Z15, which use NVIDIA-served `:free` endpoints.
3. **Combat-flavoured items never go to hosts with violent-content clauses.**
4. **Presets follow D045**: no test result makes a preset; the preset list is fixed after the legal review and the providers' written
   answers.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| No tests on such models or services (OWQ-26 b) | Drops O3 and, unless its scope sentence exempts open weights, Mistral's hosted API, for little risk avoided |
| Test them and allow them as custom presets with a warning (OWQ-26 c) | Moves use-policy risk onto users who trust a preset; departs from D037's principle |

## Consequences

- Doc 48: O3, R01 and R14 may run under items 1 and 3; Z13 and Z15 are dropped; Z14 (Liquid) is not a service named in item 2. D044's
  screening hosts exclude the NVIDIA trial and Z.ai, and its interim practice is now this rule.
- Item 3 needs a per-item flag in the suites and a per-host policy flag in the runner's host data, so that the runner refuses to send a
  flagged item to a flagged host (proposal for `tools/local-qual`). Until the flags exist, a cautious reading, not an owner decision:
  the suites doc 50 §5.9 calls combat-flavoured (text, knowledge, briefing items) are not sent to such hosts. That touches doc 48
  round 0's knowledge and text arms on the ModelRun endpoint and battery S's text arm (D044 P1).
- A content-filter finish reason is recorded as its own outcome, never as a wrong answer or an error (doc 50 §5.9; proposal).
- The same principle as D037's covers services and presets: incompatible never, ambiguous only after the legal review and, where
  the wording is unqualified, the provider's written answer (doc 50 §2.3; D045 item 7).

## Sources

`OWNER-QUESTIONS.md` OWQ-26 (Answer of 2026-09-28); doc 48 (rows O3, R01, R14, Z13–Z15; OQ9); doc 50 (§2.2, §2.3, §5.9); doc 14 §6;
D037; D044.

## Notes

- This is Plotroom's D047. Docs 12, 13, 14, 17 and 34 cite Iron Curtain's decision D047 (its LLM configuration) by path or as
  "D047" in context; it is unrelated (README, "Numbering and labels").
