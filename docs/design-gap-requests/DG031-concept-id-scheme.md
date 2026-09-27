# DG031: Flat or dotted ids for Standing Orders entries and cards

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: lint → entry links, Drill lesson `teaches` lists, `explain_concept` lookups, and
> workflow `knowledge` references; until decided they cannot resolve against the seed files (doc 33 OQ11).

## Context

- **Doc 33 §3.1–§3.4**: entry ids are "stable, dotted, lowercase (`waypoint.cycle`, `trigger.countdown-vs-timeout`)", with typed
  YAML front matter (`card`, `facts` with grounding, `anchors`, `lints`); `ConceptId` is a newtype; the example entry is
  `entity.game-logic` with related ids `waypoint.and-or`, `sync.rendezvous`; lessons are `drill.a4`.
- **The seed skill** (`skills/standing-orders/`, formerly `skills/field-manual/`; `name: standing-orders`) uses flat file ids
  (`cycle-waypoint`, `game-logic`, `placement-radius`) with fixed Markdown sections, and says "workflow steps cite
  `standing-orders:<id>`".
- **Doc 38 §3.5**: `knowledge = { …, cards = ["trigger.condition-context"], skills = ["standing-orders:placement-radius"] }`: dotted
  card ids and flat skill ids side by side; built-in skills use `<skill>:<entry>`, packs `<pack>:<skill>#<section>`.
- **Doc 30 §4.4, §4.6**: card ids are dotted (`trigger.condition-context`, `sqs.line-classes`, `briefing.html`).
- **`skills/mission-primer/references/idioms.md`** cites Standing Orders pages by flat name (I06, I07, I08, I10, I13).
- **Doc 33 OQ11 and pedagogy finding 10**: pick the canonical scheme and a migration date.

## The gap

Two id schemes for the same entries, and doc 30 cards share the dotted namespace with doc 33 concepts (`trigger.*`) without a rule
that keeps them unique. A link written today in one scheme will not resolve in the other.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Dotted ids everywhere; rename the seed files | Hierarchical, groupable, matches doc 30 and doc 33's types | File renames; old flat links break |
| B | Flat slugs everywhere | Matches the seed files and the primer | Loses grouping; doc 33's design and doc 30's cards need renaming |
| C | Dotted id is canonical (front matter `id:`); the file name stays a readable slug and is listed as an alias; lookups accept both, links and new references always emit the dotted id | No broken links during migration; the Agent Skills layout (files one level deep) is unaffected | Two spellings exist until aliases are retired |

## Recommended resolution (proposal)

Option C, with one namespace shared by Standing Orders entries and doc 30 cards (see DG032): a CI check refuses duplicate ids and
aliases, and every id referenced from lints, lessons, workflows, the primer and cards must resolve. Workflow references become
`standing-orders:<dotted-id>` (for example `standing-orders:unit.placement-radius`). Migration date: the seed files gain `id:` and
`aliases:` front matter in the same change that lands the doc 33 phase 1 parser, before any lint or lesson link is written.

## What it would change

- Doc 33 §3.1 (aliases field), §3.3 (file name versus id), OQ11 and finding 10: answered.
- `skills/standing-orders/references/*.md`: `id:` and `aliases:` front matter; SKILL.md's index shows dotted ids; its "Ids" line.
- Doc 38 §3.5 and §8.2 examples: dotted ids after the skill prefix.
- Doc 30 §4.4–§4.6: card ids registered in the shared namespace.
- `skills/mission-primer/references/idioms.md`: citations may keep page names (aliases resolve).

## Affected docs

Docs 30, 33, 38; `skills/standing-orders/`; `skills/mission-primer/`; DG032.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 33 §3.1–§3.4, §5.5, OQ11 and pedagogy finding 10; the seed skill's SKILL.md (still at `skills/field-manual/`,
  already named `standing-orders`); doc 38 §3.5; doc 30 §4.4 and §4.6; idioms.md's verification note, re-read on 2026-09-27. The
  example `unit.placement-radius` is illustrative only.
- 2026-09-27 (supersedes "still at `skills/field-manual/`" above): the seed skill's folder has since been moved with `git mv` to
  `skills/standing-orders/`, matching its `name`; the Context bullet already uses the new path.
