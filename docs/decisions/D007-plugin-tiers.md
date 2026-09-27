# D007: Plugin tiers: T0 content packs, T1 WebAssembly, T2 remote connectors

> **Status:** accepted · **Decided by:** owner, on doc 22's recommendation · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** every extension of the editor and of Wilco. **Related:** D001, D006, D008, D019, D020, D030.
> **Open parts:** DG014 = OWQ-16 (cross-plugin chains; answered 2026-09-27 → D043); OWQ-03 (SDK licence; answered 2026-09-27 → D031);
> DG030 item 4 = OWQ-17 (registry operator; answered 2026-09-27 → D038); doc 22 OQ4 (a general host-mediated `net.fetch` for
> plugins: not adopted).

## Context

The owner asked for "a plugin system that would allow, for example, connecting the editor to a service, which will extend harness
capabilities" (doc 22 header). `AGENTS.md` allows extensions only through user-installed, manifest-declared plugins that stay
product-scoped, with untrusted outputs and edits through the same typed undoable commands.

## Decision

1. Three tiers, all installed and enabled by the user, all declared in a manifest (`plugin.toml`: what the plugin adds, reads, may
   propose, contacts, needs and costs); the user's approval of the manifest is the **grant**, keyed by its capability hash:

   | Tier | What it is | What runs |
   | --- | --- | --- |
   | **T0 content pack** | Skills, workflows, prompt templates, compositions and templates, lint rules, overlays, campaign templates | Nothing |
   | **T1 local generator** | A WebAssembly component in `wasmtime`, only the host imports its grant allows; fuel, epoch deadlines, memory limits; no WASI filesystem or sockets | Sandboxed code |
   | **T2 service connector** | A remote MCP server over Streamable HTTP, limited to pinned tools and endpoints; plus the read-only `feed` kind (D008) | Remote service |

2. **Plugins propose; the editor applies.** A plugin returns typed proposals, findings, assets, a declarative panel or text; the host
   validates them against host-owned schemas, shows a diff and applies one undo group tagged as plugin origin. No plugin writes files,
   edits the mission, launches Preview or calls another plugin.
3. **Trust UX**: one install review; an egress card the first time a plugin sends mission data, and on every agent-initiated send while
   untrusted text is in context; re-review when the capability hash or a pinned tool definition changes; secrets in the OS keyring; a
   global off switch and a `--safe-mode` start.
4. **Rejected mechanisms**: native dynamic libraries (loading them needs `unsafe`); plugin-spawned processes, including local stdio MCP
   servers; Lua or Rhai as a tier; MCP sampling; HTML plugin UI in v1.
5. T1 plugins distributed through Plotroom's registry must be GPL-3.0-compatible (doc 22 §5; D001).
6. **Delivery order** (doc 22 §7): command registry, validator and provenance → T0 → T2 → T1 with SDK and conformance kit → signed
   registry and community library.

## Alternatives considered

- Extism instead of direct `wasmtime`: it still depended on an unpatched `wasmtime` major at research time (doc 22 TL;DR).
- A scripting-language tier (Lua, Rhai): a second code runtime with ambient-authority risks and no gain over WASM.
- Local stdio MCP servers: arbitrary code execution on the user's machine, which the invariant forbids.

## Consequences

- `wasmtime` stays on a pinned long-term-support line and its security releases ship promptly (doc 22 TL;DR).
- **Label clash**: plugin tiers T0–T2 and model tiers T0–T3 (doc 14 §6) share labels. Write "plugin tier T1" or "model tier T1" until
  DG005's code registry settles the spelling.
- Skills in packs execute nothing (D019); templates render under fuel (D020); pack workflows may only tighten policy (D025).
- Mod knowledge overlays and identity blocks (faction packs, site templates, radio packs) are T0 data (doc 42 §2.5; doc 36 §5).
- The pack registry holds only Plotroom packs and is a user-enabled source (D008, D030).

## Sources

Doc 22 (TL;DR, §1–§3, §5, §7, OQ4); doc 14 §6; doc 36 §5; doc 38 §6; doc 42 (§2.5, §3.4, §5); `AGENTS.md`.

## Amendment notes

### 2026-09-27: refined by D031, D038 and D043 (pointers)

The plugin SDK, WIT files and test kit are GPL-3.0-or-later for now (OWQ-03 (a); D031 item 3). The registry has no operator until
it is scheduled, then the project's own GitHub organisation (DG030 item 4; D038 item 4). Third-party pack workflows stay
single-publisher; first-party and user-authored workflows may chain plugins, with the egress card every time (DG014 option B;
D043); item 2's "no plugin calls another plugin" is unchanged. The header gained pointers; nothing above changed.
