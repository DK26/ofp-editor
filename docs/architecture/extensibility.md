# Extensibility: packs, plugins, skills, feeds and the MCP server

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`), a decided DG or an owner answer (`OWQ-nn`, all answered 2026-09-27). Type sketches are not compiled and names are
> not final.
> **Part of:** [architecture overview](README.md). **Main sources:** doc 22; doc 30 §4.6; doc 31 §4.8; doc 33 §5.6; doc 34 (row 22,
> mo rows); doc 36 §5; doc 38 §6, §9; doc 42 §2.5, §3–§5; doc 45 §2.8, §4.2, §4.4, §5; D006–D008, D019, D020, D025, D030; DG007,
> DG014, DG028, DG029, DG030; OWQ-03, OWQ-12, OWQ-15–OWQ-17.

Extensions exist only as plugins and packs the user installs and enables, declared in manifests, held to every product-scope rule
(`AGENTS.md`; D006; D007). **Plugins propose; the editor applies.** A plugin's output is untrusted data admitted through the same
command path as a user gesture, and lands as one undo group with a plugin origin ([commands-undo-history.md §4](commands-undo-history.md)).

## 1. Principles

1. **Narrower than Wilco.** Plugins read only through granted `MissionQuery` scopes and receive read-only events
   (`DocumentChanged(OpSummary)`, `SelectionChanged`, `ModeChanged`). No process, file, `eval` or AST-mutating hook exists in any ABI
   (doc 45 §2.8).
2. **One definition format** for everything structured (DG007 option C, proposal; §4).
3. **Same rules for first-party and community content.** Built-in content ships as built-in packs through the same loader, verified
   against compiled-in hashes (doc 34 mo22).
4. **Nothing in a downloaded mission or campaign enables anything.** Content lists the packs and plugins it requests; the user reviews
   manifests; nothing runs until enabled (doc 45 §2.8).
5. **Trust is keyed by plugin id plus content hash**, never by an id read from a downloaded file (LDtk's spoofable key; doc 45 §2.8).
6. **A failed or cancelled plugin run leaves the document and history untouched** (doc 45 §2.2 item 7).

## 2. Tiers (D007)

| Tier | What it is | What runs | Crate | Phase (D007 delivery order) |
| --- | --- | --- | --- | --- |
| T0 content pack | Data: skills, workflows, modules, rule-sets, compositions, presets, templates, lint rules, overlays, tours, tips, identity blocks | Nothing | `plotroom-packs` (L5, pure loader) | v1 (built-ins and sideloads, RG0) |
| T2 service connector | A remote MCP server over Streamable HTTP with pinned tools and endpoints | Remote service | `plotroom-plugin-host` (L7) | v1.x |
| `feed` connector | A read-only T2 kind for catalog lookups (D008; DG028 decided) | Remote GET | `plotroom-plugin-host` (L7) | v1.x, after DG029's outreach (OWQ-12) |
| T1 local generator | A WebAssembly component in wasmtime | Sandboxed code | `plotroom-plugin-host` (L7) | v1.x, after T2 |

Rejected: native dynamic libraries (they need `unsafe`), plugin-spawned processes including local stdio MCP servers, Lua or Rhai,
MCP sampling, HTML plugin UI in v1 (D007 item 4). Plugin tiers T0–T2 and model tiers (doc 14 §6) share labels; write "plugin tier
T1" until DG005 settles the spelling.

## 3. T0 content packs

### 3.1 Content kinds

| Kind | Examples | Sources |
| --- | --- | --- |
| `workflow` | Community workflows, built-in `core/*` workflows | doc 38 §6 |
| `module`, `rule-set` | Mission and campaign modules; rule templates; rule-override scenarios as typed presets | doc 31 §4.8; DG004; doc 36 cv38 (I36-31) |
| `composition`, `preset` | Our own composition library (fireteam, squad, weapons team, motorised and mechanised sections, armour platoon, patrol, checkpoint crew, civilians) per side, resolved by role tags; attribute and module presets | doc 35 rc33 (I35-MOD2); doc 37 |
| `template` | Mission templates with named anchors per mode family; legacy template import as canonical with Remastered deltas as metadata (rc40); CTI, Hub War, set-piece and co-op families in v1.x | doc 35 rc34–rc40 (I35-TPL) |
| `skill` | SKILL.md folders; knowledge only: a skill executes nothing and grants nothing | D019; doc 38 §3.5 |
| `card`, `overlay` | Knowledge cards and mod knowledge overlays; overlay text appears only inside code-selected cards | doc 42 §2.5; doc 30 §4.6 (I42-17-30) |
| `tour`, `tip`, `lesson` | Drill lessons and tours; a plugin may ship tips and tours only for its own tools | doc 33 §5.6; doc 34 le03, le05 (I34-22) |
| `identity` | Faction packs, site templates, radio packs | doc 36 cv35 (I36-22-27) |
| `settings`, `script-library` | Settings presets; script-library entries | doc 34 mo17, mo11 (I34-22) |
| `lens` | Design-sensibility lenses, evaluated versions only | `prompts/design-sensibility/`; doc 38 §3.5 |
| `lint` | Declarative lint rules | doc 22 §2.1 |

- **Pack workflows only tighten.** They cannot add step kinds, code steps, types, checks, providers or wider tool sets; pack roles only
  narrow (doc 38 §6.1; doc 38 AT-W14: a hostile pack gains nothing).
- **Pack-built output is vanilla and never second-class** (doc 36 cv36); sharing is export and import with review (cv37).
- Hook and pack-kind references are generated from the registry, with one example pack each (doc 36 cv34).

### 3.2 Loader and lints

The loader is pure and strict on structure (extending doc 22 §7.1 step 4; I42-22, I34-22):

- manifest schema and `format` version; unknown keys and oversize files refused;
- every sentence template has named, typed slots; a missing, unknown or repeated slot is a load error (doc 45 §4.2);
- minijinja templates render under fuel, with our own markers escaped (D020);
- Unicode lint: bidi controls, zero-width characters, variation selectors, tag characters and private-use characters (doc 42 §6.4);
- SPDX licence per item (doc 34 mo13) and the **licence split**: content that reaches missions must be CC0, MIT, Apache or CC-BY;
  editor-only content may be any GPL-compatible licence, CC-BY-SA-4.0 included, which is refused for mission-reaching content (doc 42
  §5.2; owner, OWQ-17 item 3 = DG030 item 3);
- deprecation metadata `{ level, removal_in, replacement }`;
- `[activation] mods`, so a mod overlay activates only with its mod set (doc 34 mo04);
- `ai` and `ai_usage` disclosure fields (doc 34 mo12).

### 3.3 Contribution sets

```rust
pub struct ContributionSet { owner: PackOrPluginId, commands: Vec<CommandId>, rules: Vec<DiagCode>, fixes: Vec<FixId>,
                             glyphs: Vec<GlyphId>, tips: Vec<TipId>, workflows: Vec<WorkflowId> }
```

Each pack or plugin owns a namespaced contribution set whose ids cannot shadow built-ins; disabling, uninstalling or reloading drops
exactly that set (doc 45 §2.8). An API-version mismatch disables the plugin with a reason and never exits the editor.

### 3.4 Vendoring

A mission that uses a pack module pins the content-hashed `ModuleDef`, with its origin, licence and minimum Plotroom version, in its
sidecar (`modules.lock`), so it opens and lowers without the pack. Vendoring is refused when the licence forbids embedding. Upgrades
show the notes and the per-instance lowering diff and apply as one group. The pack manager records why each pack is installed
(`UserChosen`, `DependencyOf`, `RequiredBy`) and removes only orphans (doc 45 §4.4, §5).

### 3.5 Built-in packs

`content/builtin/` holds the first-party packs, verified against compiled-in hashes: the vanilla overlay, the community mod directory
(ids, names, sizes, revisions and links only; doc 42 §4; it ships only after the channel maintainers are asked, D030 item 6 and
DG029, so the roadmap places it in v1.4), the legacy-template import map, Standing Orders and Drill content, the
composition library, attribute and module presets, and **one reconciled module catalogue** as data. Folding doc 35 rc14–rc31 and doc
34's ed and cw rows into doc 31 §4.6 is a documentation merge (I35-MOD, I34-31, I34-MERGE); the architecture's contribution is that the
catalogue is a single data file, so duplicates cannot survive.

## 4. One definition format (DG007)

```toml
format = "plotroom-workflow/1"     # also plotroom-module/1, plotroom-rule-set/1, plotroom-composition/1, plotroom-preset/1
id = "core/give-patrol"
```

- UTF-8 TOML; `format` is the first key; unknown keys and oversize files refused; one pure loader and validator family
  (`plotroom-workflow` for workflows, `plotroom-packs` for the others), per `AGENTS.md`'s parser rules.
- Templates stay separate minijinja text files referenced by id.
- Every file carries its format major; upgrades are typed migrations with dry run; a started run is pinned to its definition snapshot
  (doc 38 §6.3).
- The research docs' `ofpe.*` module keys become `core.*` (D002 item 4).

## 5. Skills (D019)

- Skills use the standard SKILL.md format (Agent Skills). The repository's `skills/mission-primer` and `skills/standing-orders` are the
  first two.
- A "safe profile" applies: no scripts in a skill are executed, and activation is deterministic (a step declares the skills it uses;
  weak models never pick skills themselves) ([agent-runtime.md §8](agent-runtime.md)).
- `xtask` generates the Standing Orders SKILL.md index from the registry, checked in CI (DG033 item 1 proposal).

## 6. T1 local generators (v1.x)

- WebAssembly components in wasmtime on a pinned long-term-support line, with its security releases shipped promptly (D007).
- WIT package `plotroom:plugin@1` (renamed from doc 22's working name, D002). Host functions carry `since`; the linker exposes only
  functions at or below the manifest's API version.
- Fuel, epoch deadlines and `StoreLimits` bound CPU and memory; no WASI filesystem or sockets; `wasi:random` is seeded. Calls run on
  the blocking pool.
- Components return typed proposals, findings or assets only; plugin-supplied lowerings are sandboxed T1 functions, never AST hooks
  (doc 45 §4.5).
- Distributed T1 plugins must be GPL-3.0-compatible (D007 item 5). The SDK, WIT and test kit are GPL-3.0-or-later for now (owner,
  OWQ-03 (a)); doc 22's permissive recommendation is revisited at its phase 3 only if plugin authors ask.

## 7. T2 service connectors and feeds (v1.x)

- An rmcp client over Streamable HTTP; endpoints and tool definitions pinned in the manifest; OAuth over HTTP only; secrets in the OS
  keyring (doc 22 §2.3).
- Plugin tools join the tool registry as `<plugin>__<tool>` and reach a model only while enabled for that project; the plugin manager
  shows their schema token cost (doc 40 R5).
- Client guards: SSRF (including IPv4-mapped IPv6 and redirect chains), oversize output, non-https elicitation URLs, hostile asset
  names (doc 22 §3.2).
- **The `feed` kind** (D008 item 3; DG028): GET-only against a pinned or user-typed HTTPS origin; a fixed host-owned response schema;
  enum filters only, no model-written parameters and no mission data; no secrets; no download routes; the allowlist checked on the final
  request path; ids percent-encoded as one path segment; no redirects off the origin; size, depth and time caps. It sends only the
  target game version and, on detail routes, a channel mod id. The first-party "Community catalog" feed is off by default and waits
  for the channel maintainers' non-objection (owner, OWQ-12 = DG029 option A: one message per channel from the owner or a named
  maintainer; non-objection is a written reply that does not object, or no objection 30 days after an acknowledging reply).
- **Cross-plugin chaining** inside a workflow is decided (owner, OWQ-16 = DG014 option B): allowed only in first-party and
  user-authored workflows; the loader refuses a third-party pack workflow whose `requires` names a plugin of another publisher; any
  step that sends a value derived from another plugin's output shows the egress card **every time**, naming both plugins and the
  payload; such workflows are never exposed to external agents (§10).

## 8. Manifest, grants and trust

```toml
# plugin.toml (doc 22 §7.2, extended). Proposal-only; keys are illustrative.
id = "example.voice"
api = "1"
kind = "t2"
license = "GPL-3.0-or-later"
provides = ["tool"]
reads = ["mission.lines"]
proposes = ["briefing.line.set_audio"]

[[tool]]
name = "synthesize_line"
effect = "asset"                      # query | proposal | finding | asset; never "apply"

[network]                             # T2 only
endpoints = ["https://voice.example.org/mcp"]

[secrets]
api_key = { keyring = true }

[limits]
calls_per_run = 50
output_bytes = 1048576

[disclosure]
ai = true
ai_usage = "text-to-speech"

[activation]
mods = []
```

- The user's approval of the manifest is the **grant**, stored in the host's grant store keyed by plugin id plus capability hash,
  never inside the package. A changed capability hash or pinned tool definition marks the plugin Modified and keeps it off until it is
  re-reviewed with a diff (doc 38 §6.1).
- **Egress:** only `plotroom-net` sends requests, and each needs an `EgressGrant`. Grants are issued only by Settings, the plugin manager
  and the Model Manager after a user gesture. An egress card appears on a plugin's first send of mission data and on every
  agent-initiated send while untrusted text is in context; the host builds the payload; an egress log records every send (D007
  item 3; D008).
- A global off switch and a `--safe-mode` start disable every plugin.

## 9. Registry phases

| Phase | What | When |
| --- | --- | --- |
| RG0 | Built-ins plus sideloaded packs from a file the user picks | v1 |
| RG1 | A Git-hosted, curated index of per-version manifests with minisign signatures over the index and each manifest (dependencies, licence, version ranges); immutable versions; yank lists and `replaced_by`; CI that runs `plotroom check` and pack lints per target profile | v1.x |
| RG2 | Throttled community submissions | later |
| RG3 | TUF-style metadata | later |

The registry is a user-enabled source (D008 item 4): off by default, blocked offline, its origin shown and reviewed like a T2 origin,
pack files fetched only from origins the signed index allowlists and checked against the pack hash before unpacking. The agent never
initiates registry traffic. The registry holds Plotroom packs only, never game mods (D030), and no third-party mod metadata: the
built-in community mod directory is refreshed at each release plus the opt-in feed's live refresh (OWQ-17 item 2). **Operator (owner,
OWQ-17 item 4):** none until the registry is scheduled; then the project's own organisation with doc 42 §5.3's governance.

## 10. The outbound MCP server (`plotroom-mcp`)

- Allowed because it adds no capability (`AGENTS.md` "Outbound exposure"; D006 item 4). Opt-in, **loopback only**, token-authenticated.
  **It ships in v1** (owner, OWQ-15 (a)).
- Tools and resources are generated from the command registry and `MissionQuery` (with a hidden list and a depth cap) plus
  `workflow.list`, `workflow.start`, `workflow.status` and `workflow.cancel`; the primer is offered as an Agent Skill (doc 38 §9).
- **Approvals stay in the editor.** An externally started run waits for an editor click; `ask` and `approve` steps are answered only in
  the editor (doc 38 AT-W15); `workflow.decide` for external deciders comes after v1 (OWQ-15 (a)), journaled with an `External`
  origin and excluded from model qualification. Workflows that chain plugins (§7) are never exposed (OWQ-16).
- MCP requests can never carry `UserIntent` ([commands-undo-history.md §4.4](commands-undo-history.md)), so external direct command
  proposals always wait for confirmation regardless of the autonomy setting (proposal).
- **Plugin tools are never re-exported**, so an external agent cannot cause egress through a plugin (doc 22 §4.3).

## 11. Licensing

- Everything in this repository is GPL-3.0-or-later (D001). T1 plugins in our registry must be GPL-3.0-compatible; remote T2 services
  may be proprietary.
- The plugin SDK, WIT files and test kit are GPL-3.0-or-later for now (OWQ-03 (a); revisit at the T1 phase if plugin authors ask).
- The generated-content permission (OWQ-01 (b): doc 02's draft plus an explicit coverage list, legal review before 1.0) covers
  template and pack text that flows into users' missions through lowering; mission-reaching pack content stays within the licence
  split (§3.2).

## 12. Open questions

1. *Decided 2026-09-27:* cross-plugin chaining (DG014 option B, OWQ-16; §7).
2. Whether a narrow interface-only licence exception for the SDK is ever wanted (OWQ-03 (a) revisits it at doc 22's phase 3).
3. *Decided 2026-09-27:* the registry operator, directory freshness and CC-BY-SA handling (DG030, OWQ-17; §3.2, §9).
4. Whether external direct command proposals may ever auto-apply under Auto autonomy (this file proposes: never).
5. Which built-in packs are in v1: those the v1 module list needs (the wave-1 modules whose probes pass on `Cwr`, OWQ-14 (a)).

## Verification notes

### Owner answers folded (2026-09-27)

- Folded from `OWNER-QUESTIONS.md` (answers of 2026-09-27) and the DG014, DG029 and DG030 texts: §3.2 (OWQ-17 item 3), §6 and §11
  (OWQ-03, OWQ-01), §7 (OWQ-12, OWQ-16), §9 (OWQ-17 items 2 and 4), §10 (OWQ-15, OWQ-16), §12. Item 1 of OWQ-17 (the mod-install
  hand-off) lives in [game-integration.md](game-integration.md) §3 and §12.
