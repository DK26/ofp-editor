# D032: Contribution terms: DCO, and AI-assisted work signed off by a human

> **Status:** accepted · **Decided by:** owner (OWQ-05) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** every contribution to this repository: code, docs, data, skills and packs. **Refines:** D001 (its open part OWQ-05).
> **Related:** D006, D013, D014, D031, D035. **Open parts:** none (`CONTRIBUTING.md` and the CI check are still to be written).

## Context

- A contributor licence agreement buys relicensing flexibility that CWR-derived code cannot use, since that code is locked to the GPL,
  and it deters community contributors (doc 02 §10.5). The Developer Certificate of Origin (DCO) 1.1 is lightweight and common.
- AI-assisted contributions are routine. CWR-CE forbids AI trailers in commits; other projects require them (doc 02 §10.5).
- Provenance matters here: ported code needs `Derived-From:` headers and its upstream tests (D013), game data is never committed
  (D001 item 3), and private sources are never named (D014).

## Decision

1. Contributions use the **DCO 1.1** (`git commit -s`), checked on every pull request. There is **no CLA**.
2. **Inbound = outbound**: contributions are licensed `GPL-3.0-or-later` including the project's §7 additional permissions (D031
   item 1).
3. **AI assistance is allowed.** The human contributor signs off and answers for provenance and hygiene: licences, `Derived-From:`
   headers, ported tests, no game data, no private references. An agent never signs off for a human.
4. An **`Assisted-by:` trailer is optional**: neither required nor forbidden.

## Alternatives considered

- DCO with the `Assisted-by:` trailer required (OWQ-05 b): a rule nobody can check; responsibility sits with the sign-off either way.
- DCO with AI trailers forbidden, as in CWR-CE (OWQ-05 c): discourages a disclosure that helps reviewers.
- A CLA (OWQ-05 d): relicensing flexibility the project cannot use, and a deterrent (doc 02 §10.5).

## Consequences

- `CONTRIBUTING.md` states the DCO, inbound = outbound, the `Derived-From:` rule, "never commit game data or wiki text", the AI policy
  and the public-repository rules (doc 02 §11 step 5; D014).
- A DCO check (the DCO GitHub App or a CI job) runs once CI exists (doc 02 §10.4).
- Patches proposed to CWR-CE (D035 item 3) follow CE's own contribution rules, including its ban on AI trailers, not ours.
- Relicensing later would need every contributor's consent (doc 02 §5).

## Sources

Doc 02 (§5, §10.4, §10.5, §11 step 5, open question "AI-contribution policy"); `OWNER-QUESTIONS.md` OWQ-05; D001; D013; D014.
