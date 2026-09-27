# D019: Skills use the standard SKILL.md format

> **Status:** accepted · **Decided by:** owner · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** built-in skills, user "styles", skills in T0 packs, skills served to external agents. **Related:** D006, D007, D020, D027,
> D028. **Open parts:** DG032 (one knowledge store and tool family); the design-sensibility pack's evaluation.

## Context

The owner proposed supporting `SKILL.md` so that people can add their own styles, and keeping the public Agent Skills format because it
does not tie the work to Plotroom's harness: the same skills work when an external agent drives the editor through its MCP server.
Docs 22 §2.1, 30 and 38 already use Agent Skills; `skills/mission-primer/` and `skills/standing-orders/` exist in this format.

## Decision

1. Skills, including user-added **styles**, use the Agent Skills `SKILL.md` format with its standard frontmatter (`name`,
   `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). Plotroom's own extensions go only into namespaced `metadata`
   keys.
2. **Safe profile** in Plotroom: the body, `references/` and `assets/` are used; `scripts/` are **never executed** by the harness (only a
   T1 plugin could ever run code, D007); `allowed-tools` may only **narrow** to product tool names; skill content is untrusted input.
3. **Weak models do not choose skills.** The harness activates them deterministically from the user's chosen style and each workflow
   step's declared tags; strong in-app models may also select from descriptions.
4. In the UI, **Styles** are skills with a style kind. The design-sensibility prompt pack (`prompts/design-sensibility/`, v0.2,
   unevaluated) is to become the default house-style skill once its evaluation passes.
5. Skills ship in T0 packs (D007) and are served to external agents through Plotroom's MCP server.

## Alternatives considered

- A custom skill format: locks skills to Plotroom and loses familiarity for authors.
- Executing skill scripts, as some agent hosts allow: violates the product-scoped invariant (D006).
- Letting every model pick skills from descriptions: unreliable for weak models (doc 30 TL;DR, "Activation").

## Consequences

- The skill loader is a pure, size-capped parser that is permissive on unknown keys; tests prove that `scripts/` never run and that
  `allowed-tools` never widens the tool set.
- The primer skill stays within its word budget (doc 30 §5.2); detail moves into `references/`, and primer section numbers cited by
  workflow capsules are updated when they change.
- "Styles" is a user-facing name and clears doc 02 §9 before release (OWQ-08).
- Skills written by users stay local unless shared as a T0 pack.

## Sources

README ("Extensible"); doc 22 §2.1; doc 30 (TL;DR, §4–§5); doc 33 §3; doc 38 §1.1; `prompts/design-sensibility/README.md`;
`skills/mission-primer/SKILL.md`; `skills/standing-orders/SKILL.md`.

## Amendment notes

### 2026-09-27: pointer to D034

The Consequences' naming route (OWQ-08) is settled: the design round names "Styles" and the other pending terms in one names table,
clears each through doc 02 §9, and the owner reviews the table before the first release (OWQ-08 (a); D034 item 3). Nothing above
changed.
