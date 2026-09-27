# D014: Public-repository hygiene and our own words

> **Status:** accepted (invariant) · **Decided by:** owner (`AGENTS.md`) · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** every committed file: code, docs, skills, prompts, data, tools, commit messages. **Related:** D001, D002, D013.

## Context

The repository is public. Anything committed may be read by anyone. `AGENTS.md`, "Public Repository Hygiene", is authoritative. The
research also drew on sources whose text may not be copied (Bohemia's wiki, proprietary tool documentation, community tutorials) and on
game data licensed under the APL-SA.

## Decision (summary; `AGENTS.md` governs)

1. Never reference private or unpublished projects, repositories, documents or benchmarks in any committed file: no names, links, file
   paths, quotes, measurements or distinctive coined terms from them.
2. Ideas from non-public sources may be used only restated as this project's own principles, in this project's own words, without
   attribution.
3. Local-only notes that need such references live under `/private/`, which is git-ignored; nothing moves from there into tracked files
   until those references are removed.
4. Every change set is searched for such references before it is committed.

## Related content rules (restated from research; same spirit)

- All prose in docs, skills and prompt packs is our own. Public sources are cited, not copied; proprietary tools' documentation is used
  for ideas only (doc 38 "Hygiene"; doc 40 "Hygiene").
- No Bohemia wiki (BIKI) text in the repository or in any shipped corpus; command and format facts come from the GPL source (doc 02
  TL;DR).
- No game data, mod content or other redistribution-restricted assets are committed; fixtures are synthetic (`AGENTS.md` fixture rules;
  doc 20). Runs over a local install publish only aggregates; their scripts and outputs stay outside the repository (doc 42 header;
  doc 43 Sources).
- Community pages are cited only as evidence, with at most a short attributed quote (doc 33 header, following doc 28's rules).

## Alternatives considered

None was seriously considered: the repository is public by the owner's choice, and the rules protect contributors and third parties.

## Consequences

- Reviews include a hygiene check; an automated grep for known forbidden patterns in CI is a proposal.
- Public outreach texts (OWQ-09 to OWQ-12) follow the same rules.
- When a research doc needs a non-public fact, it states the conclusion in our words or marks the item unknown; it never cites the
  private source.

## Sources

`AGENTS.md` ("Public Repository Hygiene", test-fixture rules); doc 02 TL;DR; doc 20 TL;DR; doc 28 (quoting rules); doc 33 header;
doc 38 header; doc 40 header; doc 42 header; doc 43 Sources.
