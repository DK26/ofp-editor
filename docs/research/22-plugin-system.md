# Plugin system for the editor and its AI harness

> Research note for `ofp-editor`, a standalone Rust re-implementation of the *Arma: Cold War Assault* / *Operation
> Flashpoint* mission editor with Preview, a campaign designer and a built-in, product-scoped AI agent.
> Written 2026-09-26. It stands alone. **Not legal advice:** §5 needs the same legal review as doc 02.

**Owner direction.** "We may allow a plugin system that would allow, for example, connecting the editor to a service,
which will extend harness capabilities." `AGENTS.md` ("Non-Negotiable Product Invariant") already allows extensions
only through user-installed, manifest-declared plugins that stay product-scoped. This note designs that system.

**Epistemic legend.** **[V]** checked against the cited file or URL (retrieved 2026-09-26). **[I]** our inference or
recommendation. **[U]** unknown or unverified. gnu.org refused connections during this session (and again at review),
so FSF FAQ wording comes from verbatim quotations found by search or from the FSF's own GPLv3-era FAQ draft on
gplv3.fsf.org, marked as such.

**Citation aliases** expand mechanically to `owner/repo@sha:`: `ICD:` = `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:`,
`CX:` = `openai/codex@e72da2b538:`, `OC:` = `anomalyco/opencode@b65de4d694:`, `PI:` = `earendil-works/pi@2b0a123de9:`,
`DSH:` = `deepseek-ai/deepseek-harness@477b4f4205:`.

---

## TL;DR

- **Three tiers, all user-installed and product-scoped [I]:** **T0 content packs** (data only: skills, workflows,
  templates, compositions, overlays, lint rules); **T1 local generators** (WebAssembly components in `wasmtime` with no
  ambient authority, only the host imports their grant allows); **T2 service connectors** (remote MCP servers over
  Streamable HTTP, limited to the tools and endpoints the manifest pins).
- **Rejected [V]/[I]:** native dylibs (`libloading::Library::new` is `unsafe`, which AGENTS.md bans); plugin-spawned
  processes including local stdio MCP servers (MCP's own guidance warns of "Arbitrary code execution"); Lua or Rhai as
  a tier; MCP sampling; HTML plugin UI in v1.
- **Plugins propose; the editor applies [I].** A plugin tool returns typed proposals (`EditorCommand`s), findings,
  assets, a declarative panel or text. The host validates it against host-owned schemas, shows the diff, and applies it
  as one undo group tagged `Origin::Plugin`. No plugin writes files, edits the mission, launches Preview or calls
  another plugin.
- **Status [V]:** MCP revision **2026-07-28** is stateless JSON-RPC over stdio or Streamable HTTP, with OAuth 2.1 for
  HTTP only. Elicitation is the only client feature the overview lists; Sampling and Roots are still in the spec but
  **Deprecated** (SEP-2577). Tasks, Skills (SEP-2640 Final) and MCP Apps are opt-in extensions; `rmcp` 3.4.1
  implements the revision. `wasmtime` 49.0.1 ships monthly with a 24-month LTS every 12 majors (pin **48.x** and ship
  its security releases promptly: 2026 brought two CRITICAL sandbox escapes); fuel, epoch deadlines and `StoreLimits`
  bound CPU and memory. RUSTSEC-2026-0269 (a WASI filesystem escape) is why plugins get no WASI filesystem or sockets.
  We use wasmtime directly, not Extism, because `extism` 1.30.0 still depends on wasmtime 43, which is unpatched.
- **Licensing [V]/[I]:** our registry should require distributed T1 plugins to be **GPL-3.0-compatible**, because
  the FSF treats code using a GPL program's bindings as "effectively linked" (Blender says the same of its add-ons).
  Whether the law requires this is untested. **Proprietary remote services are fine**: they are never conveyed to
  users, GPL-3.0 has no network clause, and programs talking over sockets are "normally separate programs". **Add no
  plugin exception now:** under GPLv3 §7 a permission covering only part of the Program leaves "the entire Program ...
  governed by this License". The FSF adds that for other authors' code "you cannot authorize the exception for them",
  and that includes Bohemia's code. Ship the SDK, WIT and test kit as `MIT OR Apache-2.0`. *Superseded by
  [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 3 (2026-09-27, OWQ-03 (a)): the SDK,
  WIT and test kit are `GPL-3.0-or-later` for now, revisited at MVP step 3 only if plugin authors ask.*
- **Trust UX [I]:** one install review; one egress card the first time a plugin sends mission data (and on every
  agent-initiated send while untrusted mission text is in context); re-review only when the capability hash or a
  pinned tool definition changes; secrets in the OS keyring; a global off switch and `--safe-mode`.
- **MVP [I]:** (0) command registry, validator, provenance → (1) T0 packs → (2) T2 connectors (the owner's example)
  → (3) T1 WASM with SDK and conformance kit → (4) signed registry and community library. AGENTS.md wording: §7.4.

| Term | Meaning here |
|---|---|
| **Manifest / grant** | `plugin.toml` declares what a plugin adds, reads, may propose, contacts, needs and costs. The **grant** is the part of the manifest the user approved, keyed by its **capability hash** |
| **Proposal** | Typed editor commands a plugin suggests. Only the host turns them into an edit |
| **Component / WIT / host import** | A WebAssembly module with typed interfaces written in WIT. Its host imports are the only authority it has |
| **Connector** | A T2 plugin: a manifest plus a pinned remote MCP endpoint |
| **OFP addon** | A game PBO with `CfgPatches` that adds units or islands to the *game*. It is not an editor plugin (§1.1) |

---

## 1. Use cases that fit the invariant

### 1.1 Editor plugins versus game addons

| | Editor plugin (this note) | Game addon (PBO with `CfgPatches`) |
|---|---|---|
| Purpose | Extends the editor and its agent | Adds units, weapons, objects and islands to the *game* |
| Runs where | In the editor (data or WASM) or on a remote service | Only in the game. The editor never executes addon code or scripts |
| Editor's job | Install, grant, sandbox, disable | Read configs to build catalogs (`CfgVehicles`, `CfgWorlds`) and resolve `addOns[]`. A missing `CfgPatches` name fails the whole mission load with `LSNoAddOn` (doc 04 §5, §10) |
| Trust | Manifest plus the user's grant | Untrusted parser input: config text is data |
| License | The author's (GPL-compatible for T1, see §5) | The addon author's. Bohemia's own data is APL-SA (doc 02 §3) |
| Bridge | A T0 pack may ship our own `llm:` notes *about* an addon pack, but never the addon's files | — |

### 1.2 Catalogue

| # | Plugin (example) | Tier | Reads | Returns | Leaves the machine | Notes |
|---|---|---|---|---|---|---|
| 1 | **Radio Voice**: voices selected `sideChat`/`titleText` lines as OGG and proposes `CfgSounds`/`CfgRadio` entries | T2 | selected lines, cast voice profile | assets + proposal | line text, voice id | Licensed stock voices only; never clones real people or the OFP cast (doc 09 WN2). The editor's own tool makes `.lip` files. Output tagged "AI voice" |
| 2 | **Stringtable translator**: fills missing languages using a military glossary and flags machine-translated cells | T2 | source-language rows | proposal | source strings | Keys and placeholders are preserved and validated |
| 3 | **Community library**: import compositions (checkpoint, FOB, minefield), templates, briefing styles; publish your own | T2 | nothing to browse; the selection to publish | proposal / T0 pack | search terms; uploads only on an explicit "Publish" | Every item shows author and license. Imports are validated like a paste |
| 4 | **Hosted specialist model**: a community "SQS explainer" or "mission critic" | T2 | scripts or a mission summary | findings, text | the scoped data | Edits only if the manifest declares a proposal kind |
| 5 | **Tactical analysis**: line of sight, dead ground, ambush spots, landing zones | T1 | terrain, roads, groups | findings + overlay + proposal | nothing | Island data is APL-SA, so the analysis runs locally (doc 02 §3.4) |
| 6 | **Patrol generator**: "cautious 4-man loop around the village, cycle" | T1 | selection, terrain, locations | proposal | nothing | Same result for the same seed (doc 16 §4.2) |
| 7 | **Ambush builder**: pick a road bend; get a group in cover, a trigger and a sync | T1 | roads, terrain, catalog | proposal | nothing | |
| 8 | **Town population**: garrison and civilians, using probability of presence and placement radius | T1 | map objects, catalog | proposal | nothing | Respects engine limits (12 units per group, per-side group caps; doc 09) |
| 9 | **Convoy route**: road path from A to B with spacing, column formation, halt and ambush hooks | T1 | road graph | proposal | nothing | |
| 10 | **Extra lints**: OFPEC tags, stale `addOns[]`, multiplayer readiness, briefing marker links, unused triggers | T0 rules / T1 | whole mission | findings + fixes | nothing | Useful even with the agent off |
| 11 | **Exporters**: campaign flowchart SVG, printable briefing, Markdown design doc | T1 | mission / campaign | asset | nothing | Only the host writes the file, through its save dialog |
| 12 | **Campaign templates**: roster carry-over, branching three-act structure | T0 | — | content | nothing | Docs 18–19 |
| 13 | **Skills and workflows**: a "1985 radio procedure" skill; a "night raid in ten minutes" workflow | T0 | per step | — | nothing | `SKILL.md`, the same format the MCP Skills extension serves |
| 14 | **Catalog overlays**: `llm:` notes for vanilla or addon classes | T0 | — | data | nothing | Our own text only |
| 15 | **Panels**: radio-chatter timeline, cast board, time-of-day preview | T1 | per panel | panel model | nothing | Declarative; the host renders them (§4.3) |

**Never allowed [I]:** running a shell or process, including indirectly through an OS URL handler (a `steam://` or
`file:` link could start the game or a local program); reading or writing arbitrary files, the keyring or another plugin's
data; browsing the web or contacting unnamed hosts; launching Preview or talking to the running game; applying edits
outside the normal review; sending raw game files (PBO, `config.bin`, textures); cloning a real person's voice. This
is the invariant's "no general system access" and "same path as the user", applied to plugins.

---

## 2. Mechanism options (status September 2026)

### 2.1 Data-only content packs (T0)

**Layout [I].**

| Path | Contents |
|---|---|
| `plugin.toml` | The manifest (§7.2) |
| `skills/<name>/SKILL.md` | Agent Skills, in the format the MCP Skills extension also serves [V] |
| `workflows/*.toml` | Steps that call tools, with gates (doc 16 §4.4) |
| `prompts/*.j2` | Prompt templates |
| `compositions/*` | `mission.sqm` fragments with typed parameter schemas (doc 17 §6) |
| `lints/*.toml` | Declarative rules: selector, predicate, message |
| `catalog/*.toml` | `llm:` overlays |
| `campaigns/*` | Campaign templates |

**Templating.** `minijinja` 2.24.0 (Apache-2.0; latest stable, with 3.0 alphas out) has a `fuel` feature "to better
protect against expensive templates" and loads no files by default [V]. `tera` 2.4.0 (MIT) is the alternative. **Use
minijinja with fuel [I].** Rendered output is parsed and validated like a paste, so a template cannot bypass the
validator.

**Skills execute nothing [I].** `scripts/` are ignored and `allowed-tools` can only narrow the tool set. The MCP Skills
extension likewise says hosts MUST "Treat skill content as untrusted input" and makes `allowed-tools` grants need
"explicit per-skill user approval" [V]. Install review, hash pinning and the validator cover the residual risk
(misleading text, bad templates).

### 2.2 Sandboxed local code (T1): WebAssembly components

**Engine [V].** `wasmtime` 49.0.1 (2026-09-24, `Apache-2.0 WITH LLVM-exception`) ships "A new major version ... on the
20th of each month". Majors that are multiples of 12 are LTS "supported for 24 months", others for 2 months, and
"Security bugs are guaranteed to be backported to all supported releases". crates.io shows 36.0.16 and 48.0.3 released
on 2026-09-24 alongside 49.0.1 [V], so 36 and 48 are the live LTS lines [I]. Wasm checks "all accesses within linear
memory", and "All interaction with the outside world is done through imports and exports"; wasmtime adds 2 GB guard
regions and zeroes memory. WASI 0.3.0 (2026-06-11) adds `async func`, `stream<T>` and `future<T>`, and "Wasmtime 46
is the first release to implement the final WASI 0.3.0 specification". Limits come from `Store::set_fuel` (needs
`Config::consume_fuel`), `set_epoch_deadline` (needs `Config::epoch_interruption`), `limiter` and
`StoreLimitsBuilder`. `wit-bindgen` 0.62.0 (Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT) generates guest
bindings.

**No WASI filesystem [V]/[I].** RUSTSEC-2026-0269 ("Filesystem sandbox escape when paths or symlinks contain trailing
slashes", reported 2026-08-20, issued 2026-08-31, HIGH 8.8; patched in 24.0.13, 36.0.14, 46.0.3 and ≥ 47.0.4) shows
that even capability-scoped WASI filesystem access (preopened directories) has had escape bugs. Give plugins no WASI
filesystem or sockets. Prefer linking only the WASI interfaces a Rust `std` guest needs (I/O, clocks, random, CLI
stdio and environment), so a guest that imports `wasi:filesystem` or `wasi:sockets` fails to instantiate. If that
proves impractical, link `wasmtime-wasi` with an empty context: no preopens, sockets denied, empty environment, stdio
captured to the plugin log. Grant authority only through our own narrow imports [I]. Two more host choices follow
from the "same seed, same result" rule (§1.2) [I]: back `wasi:random` with a generator seeded from the call's `seed`,
and give guests a fixed clock. The exact `WasiCtxBuilder` hooks for this are unverified.

**Wasmtime is hardened, not flawless [V]/[I].** RustSec lists two CRITICAL wasmtime sandbox escapes from 2026-04-09:
"Miscompiled guest heap access enables sandbox escape on aarch64 Cranelift" (RUSTSEC-2026-0096, which affects aarch64 hosts
such as Apple Silicon Macs) and a Winch-backend escape (RUSTSEC-2026-0095). The same batch had several component-model
string-transcoding bugs. RUSTSEC-2026-0268 ("Guest controlled-size host heap allocation through WASIp3 streams",
MEDIUM) spares hosts that do not implement WASI p3. Consequences for us [I]:

- Use Cranelift, not Winch.
- Do not expose WASI p3 streams in v1.
- Disable Wasm proposals the SDK does not need.
- Treat every wasmtime security release as an editor patch release, because wasmtime is compiled into our binary.
- Keep T1 installs signed-registry-by-default (§3.2).

**Extism: skip [V]/[I].** `extism` 1.30.0 (BSD-3-Clause, 2026-06-04, the latest release) has convenient multi-language
PDKs. Its crates.io dependency list pins `wasmtime = "^43"`, `wasi-common = "^43"` and `wiggle = "^43"` [V]. Wasmtime
43 is outside every patched range of RUSTSEC-2026-0269 and past its two-month support window. A third-party issue says
"41.x", which is wrong about the version but right that Extism is stuck on an unpatched one. `wasi-common` is the
preview-1 WASI implementation, so Component Model and WIT support is likely missing [U].

**Prior art [V].** **Zed** builds Rust extensions for `wasm32-wasip2`, restricted by the user's
`granted_extension_capabilities` (`process:exec`, `download_file`, `npm:install`). Its docs warn that removing all
grants "will likely make many extensions non-functional", which suggests the default grants are broad [I]; ours start
narrow. **Iron Curtain D005** has capability
structs, elevated capabilities that are off by default and need a reason, re-prompts on a capability-hash change, and
fuel, memory and host-call limits (`ICD:src/modding/wasm-modules.md#L51-L91`, `#L148-L232`, `#L276-L305`). **Figma**
runs plugin code "on the main thread in a sandbox" that "does not expose browser APIs", with UI and network in an
iframe reached by "message passing". **Proxy-Wasm** keeps one ABI (v0.2.1, "widely implemented") across Envoy, NGINX
and ATS. Rust is the first-class guest; JS, Python and Go guests were not evaluated [U].

**Embedded scripting? No [V]/[I].** `mlua` 0.12.1 (MIT) offers Luau `sandbox()`, `set_memory_limit` and
`set_interrupt`, and safe `Lua::new` "will not allow to load unsafe standard libraries or C modules". But it is still
a C VM in our process, dynamically typed, a second language for authors, and no better isolated than WASM. `rhai`
1.26.1 (MIT OR Apache-2.0) is pure Rust and "designed to not bring down the host system", but niche and dynamic; keep
it only as a possible expression language for T0 lint predicates.

### 2.3 Service connectors (T2): MCP

**Protocol revision 2026-07-28 [V].**

| Area | What the spec says |
|---|---|
| Core | JSON-RPC 2.0 with "Stateless, self-contained requests"; "servers do not initiate JSON-RPC requests" (a server that needs input returns an `InputRequiredResult` and the client retries). Servers offer Resources, Prompts and Tools. The overview lists Elicitation as the only client feature. Roots and Sampling (and server Logging) remain in the spec but are **Deprecated** in 2026-07-28 (SEP-2577), with earliest removal in the first revision on or after 2027-07-28. Transports: stdio ("the standard streams of a client-launched subprocess") and Streamable HTTP |
| Authorization | "Authorization is **OPTIONAL**". HTTP transports "SHOULD conform". Clients MUST use RFC 9728 metadata, MUST send RFC 8707 resource indicators, and MUST validate the RFC 9207 `iss` response parameter. OAuth 2.1 is draft-13. Client ID Metadata Documents are SHOULD; DCR is deprecated. stdio "SHOULD NOT follow this specification, and instead retrieve credentials from the environment". "MCP clients MUST NOT send tokens to the MCP server other than ones issued by the MCP server's authorization server" |
| Tools | `inputSchema` (JSON Schema 2020-12 by default) and an optional `outputSchema`, whose structured results "Clients SHOULD validate". "Clients MUST consider tool annotations to be untrusted unless they come from trusted servers". Names SHOULD be 1–128 characters of `[A-Za-z0-9_.-]`. Aggregating clients SHOULD use "a disambiguation strategy such as prefixing tool names with a server identifier", not `serverInfo.name`. Clients SHOULD "Show tool inputs to the user before calling the server", validate, time out and log. New: `x-mcp-header` mirrors marked parameters into `Mcp-Param-*` HTTP headers, which network intermediaries can see |
| Elicitation | Form mode is "flat objects with primitive properties only" (enums and multi-select allowed): "Servers MUST NOT use form mode elicitation to request sensitive information". URL mode: the client "MUST NOT automatically pre-fetch the URL", needs consent, "MUST show the full URL", and opens it "in a secure manner that does not enable the client or LLM to inspect the content or user inputs" |
| Extensions | Tasks (long-running jobs). Skills (`io.modelcontextprotocol/skills`, SEP-2640 Final, merged 2026-09-13): `skill://` resources with a per-file SHA-256 manifest. "Persisted approval MUST bind to the complete set of file URIs and digests", any changed file revokes it, and hosts "MUST NOT retrieve files ahead of need, including on connection, listing, or approval". MCP Apps: HTML `ui://` resources in sandboxed iframes |
| Rust | `rmcp` 3.4.1 (2026-09-23, Apache-2.0) "implements the stable MCP `2026-07-28` specification" and has child-process (`transport-child-process`) and Streamable HTTP (`transport-streamable-http-client-reqwest`) clients. Doc 12 §3.4 already uses `rmcp` for our outbound server, so one crate serves both directions. Avoid `rig-rmcp`: at `rig@42f4e060ef` it depends on `rmcp = "2"` (`Cargo.toml#L262`), and crates.io has only a 0.0.0 placeholder (doc 12 §1.8) |

**What we use [I].**

| MCP feature | Use? | How |
|---|---|---|
| Streamable HTTP client | **Yes** | The only T2 transport (plus the GET-only `feed` kind for read-only catalogs, added 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md) item 3). HTTPS, or plain `http` to loopback for services the user runs (with a badge and an explicit toggle). A loopback origin must be typed in by the user; registry manifests may not pin loopback or private addresses, so a published plugin cannot aim the editor at local services [I] |
| stdio, with us spawning the server | **No** | That is native code running with the user's rights. MCP's best practices name "Arbitrary code execution" and ask for sandboxing [V]. Cross-platform OS sandboxing is out of scope for v1 |
| Tools | **Pinned** | Through the gate below |
| Resources | Read-only data | Library items. Links are never followed automatically |
| Prompts, Skills | As T0 content | Only after approval, bound to the digest manifest [V]. The review shows the frontmatter and file manifest that `skills/list` returns. File text is fetched only when the user opens it or the skill activates, as the extension requires [I] |
| Elicitation | **Yes** | Forms appear in our UI with the server named. URLs: `https:` only (`http:` only for loopback OAuth redirects), with no custom schemes. The full URL is shown with its domain highlighted, and after consent it opens in the system browser through a non-shell OS API [I]. MCP's rule "MUST NOT use shell commands (e.g., `cmd.exe`, `sh`, PowerShell) to open URLs", written for OAuth authorization URLs, is applied to every URL [V] |
| Tasks | Later | Batch TTS and translation |
| Sampling | **No** | Deprecated in 2026-07-28 (SEP-2577; migration: "Integrate directly with LLM provider APIs") [V]. It would let servers spend the user's model budget [I] |
| MCP Apps | **Not in v1** | Needs a webview inside egui (doc 06) |

**The product-scope gate [I].** This is how a general MCP server is held to product scope.

1. **Pin at review.** The manifest pins endpoint origins and allowed tools. Per tool it records an *effect* (`query`,
   `proposal`, `finding`, `asset`), host-owned input and output schema ids, and the SHA-256 of the server's tool
   definition (name, description, schemas) as reviewed.
2. **Filter `tools/list`.** Expose only pinned tools whose definitions still match. Codex filters by name with
   `enabled_tools`/`disabled_tools` (`CX:codex-rs/codex-mcp/src/tools.rs#L63-L96`) [V]; the hash adds rug-pull
   protection (on mismatch the tool is disabled and marked "changed, review").
3. **Host-built requests.** The model fills only parameters inside the host schema (which lines, which language). The
   host builds the payload from the scope-filtered snapshot, checks it against the pinned `inputSchema`, caps its size.
4. **Structured output only.** `structuredContent` must validate against the *host* output schema. Unstructured
   `content` becomes labelled display text, never commands.
5. **Convert.** Results become proposals, findings or assets, then are validated, diffed, confirmed and applied with
   provenance. Commands outside the grant's `proposes` are dropped with an error.
6. **Network.** Only pinned origins are reachable. OAuth discovery URLs are checked per MCP's SSRF guidance (block
   private ranges, validate each redirect, consider DNS pinning), which are SHOULDs for a desktop client [V]. MCP also
   warns "Avoid implementing IP validation manually", because of octal, hex and IPv4-mapped IPv6 tricks, so use a
   vetted classifier [V]. The guard must sit in the HTTP client that `rmcp` uses for both MCP and OAuth requests.
   Whether `rmcp` 3.4.1 accepts a caller-supplied `reqwest` client is unverified; confirm it in the spike [U].
   Parameters marked `x-mcp-header` must not carry mission text, because headers are visible to intermediaries [I].

The server may compute anything; only a typed, validated proposal the user sees can reach the mission.

### 2.4 Native dylib plugins: rejected

`libloading::Library::new` is `unsafe`: loading runs initialisation routines "conceptually the same [as] calling an
unknown foreign function" [V], and AGENTS.md forbids `unsafe` in production code [V]. Rust has no stable ABI [I]; a
native plugin has full privileges, can crash the editor and needs per-OS builds. Godot's GDExtension is native, and its
community built a RISC-V sandbox to regain isolation [V]. Dynamic linking that shares data structures also forms a
"single combined program" (§5) [V].

### 2.5 Comparison

| Option | Isolation | Capability control | UX | Dev ergonomics | Cross-platform | Perf | Rust maturity (2026-09) | Verdict |
|---|---|---|---|---|---|---|---|---|
| Content packs | Nothing runs | By construction | Copy and enable | Text files, hot reload | All | Trivial | `serde`/`toml`, `minijinja` 2.24 | **Adopt: T0** |
| WASM components (wasmtime + WIT) | Memory-safe sandbox, no ambient authority; engine escapes do occur and need prompt patching | Per import; fuel, epoch, memory | One review | Rust is good; WIT takes learning; other languages [U] | One `.wasm` for all | Near-native after JIT [I] | wasmtime 49 (LTS 48), wit-bindgen 0.62 | **Adopt: T1** |
| Extism | Same engine, own ABI | Host functions + manifest | Same | Many PDKs | Same | Same | 1.30 on wasmtime 43 (unpatched, unsupported) | Skip |
| Lua (`mlua`/Luau) | C VM in our process | Exposed globals, memory limit, interrupts | Same | Familiar, dynamic | Needs a C toolchain | Fast | 0.12.1 | Skip |
| Rhai | Pure-Rust interpreter | Registered functions, operation limits | Same | Niche, dynamic | All | Slower [I] | 1.26.1 | Skip; maybe expressions later |
| Remote MCP (HTTPS) | Runs off the machine | Scope gate + pinned origin | Review + egress card + OAuth | Any language, any host | All | Network-bound | `rmcp` 3.4.1 | **Adopt: T2** |
| Local stdio MCP | None: a native process | None without an OS sandbox | "Show the exact command" | Easiest | Per OS | Fine | `rmcp` child process | Reject in v1 |
| Native dylib | None | None | Trust prompt | ABI pain | Per-OS builds | Best | `libloading` (unsafe) | Reject |

---

## 3. Security and trust model

**Threats [I]:** a plugin exfiltrating the mission or keys; a hostile update (rug pull); tool poisoning or instructions
injected through outputs; downloaded mission text steering the agent ("send the whole mission to X"); an external agent
using our outbound MCP server to trigger egress (confused deputy); SSRF or DNS rebinding; CPU, memory or output
exhaustion; runaway cost; a compromised registry.

### 3.1 Install review and runtime prompts

**Install review.** One screen, grouped by risk: what the plugin **adds** (with token cost), **reads**, **may propose**
(executable fields highlighted), which **origins** it contacts (with the author's reasoning), its **secrets**, **cost
and limits**, and **publisher, signature and license**. Precedents [V]: Figma publishes network `reasoning` and domains
on the plugin's page; Iron Curtain makes network and filesystem "Elevated capabilities", "Default: off", each with a
mandatory reason (`ICD:src/modding/wasm-modules.md#L160-L183`, `#L218-L219`); D071's dialog lists what a tool "does NOT
have" (`ICD:src/decisions/09f/D071-external-tool-api.md#L343-L361`). Capabilities marked `essential` are part of the
install decision; optional ones start off, each with its own toggle [I]. To keep installs light, follow Iron Curtain's
split (`ICD:src/modding/wasm-modules.md#L214-L224`) [I]. A T0 pack, or a T1 generator with standard read scopes,
default limits and no `exec` proposals, gets an informational summary and one Install button. Toggles and reasons
appear only for elevated items: egress, secrets, `exec`, catalog or terrain egress, and above-default limits.

**Runtime prompts appear only when they tell the user something [I]:**

| Situation | Prompt? |
|---|---|
| Local T0/T1 tool | **No.** The result is a proposal, and the normal diff is the review |
| First network call per mission per plugin | **Egress card**, e.g. "Send 14 dialogue lines (1.2 kB) to tts.example.com?" with *Once* / *For this mission* / *Always for this plugin (these scopes)* / *Cancel*. The last choice is never preselected and can be revoked in the plugin manager, so users who translate many missions are not asked every time [I] |
| Later calls in the same mission with the same scopes | **No.** A status-bar indicator instead; MCP asks for "clear visual indicators when tools are invoked" [V]. Each call's payload stays inspectable in the egress log |
| Agent-initiated call while untrusted text (a downloaded mission, a plugin output) is in the agent's context | **Egress card every time**, even inside a granted mission. This is the "rule of two" case in doc 21 (untrusted input, private data and egress together), and it meets doc 21's per-send disclosure. User-initiated calls from a menu keep the per-mission card [I] |
| Estimated cost above the user's threshold | Yes, with the estimate |
| Capability hash, endpoint or pinned tool definition changed | **Re-review.** Iron Curtain re-prompts only on a `capability_manifest_hash` change (`ICD:src/modding/wasm-modules.md#L224`) [V] |
| Agent in Auto mode | Same caps. A plugin's *first* egress is never accepted automatically |
| Server elicitation | We render it, naming the server [V] |

**Deliberate deviation [V]/[I].** The MCP overview says "Hosts must obtain explicit user consent before invoking any
tool". That sentence is lowercase, and the spec's keywords are normative "when, and only when, they appear in all
capitals". The tools page asks, as SHOULDs, for a human "with the ability to deny tool invocations" and for showing
"tool inputs to the user before calling the server". We treat the install grant plus the egress card as standing
consent, and repeat the card where the risk rises (the rows above). Showing every payload before every call would
make batch translation or voicing tedious without adding a boundary, since the host builds the payload and the pinned
origin receives it. A per-plugin "always show payload" setting covers users who want the literal SHOULD.

### 3.2 Controls [V]/[I]

| Control | Design |
|---|---|
| **Network** | Only the host's HTTP client makes requests, and only to exact allowlisted origins. That client lives in a dedicated host crate, outside the agent crates that doc 21 §D1 bans from holding one [I]. HTTPS only, except loopback for services the user runs and enters. After DNS resolution, private, loopback and link-local addresses are blocked, then re-checked or pinned (IC V43 at `ICD:src/modding/wasm-modules.md#L95` and MCP's SSRF guidance agree) [V]. No redirects off the list. Size caps and timeouts everywhere. The editor never *launches* a local service, the same as the "local external" model tier (doc 17 §3). The editor never opens non-`https` URLs on a plugin's behalf [I] |
| **Secrets** | Stored in the OS credential store with `keyring` 4.2.0 (MIT OR Apache-2.0; Keychain, Windows Credential Manager, Secret Service) [V], with no machine-derived fallback (IC rule, doc 17 §3.1). Where no store works (for example a Linux desktop without Secret Service), keep the secret in memory for the session and ask again next time [I]. The host attaches `Authorization` headers itself, so WASM guests and the model never see secret values. Claude Code does the same: `sensitive` config goes into "the platform's secure credential store" and appears in skill content only as a placeholder [V]. OAuth tokens also go in the keyring (MCP: "MUST keep refresh tokens confidential in transit and storage") [V]. A static `bearer` key is for servers that do not implement MCP authorization. If a server advertises RFC 9728 metadata, use OAuth and send no other token [I]. OAuth needs the project to host a Client ID Metadata Document at an HTTPS URL and a loopback redirect listener during the flow; MCP names "Localhost Redirect URI Impersonation" as a risk of that setup [V]/[I]. Secrets are never exported |
| **Egress** | The host builds every payload from the declared read scopes. A local per-plugin egress log records what was sent, where, when, and how many bytes. Never sent: file paths, the OS user name, other plugins' data, raw game files. Facts derived from game data (class names, island names, terrain samples) leave only if the manifest declares `catalog` or `terrain` egress *and* the user enables it; doc 02 §3.4 says APL-SA data goes out only opt-in and minimal. Offline mode blocks all egress |
| **Untrusted output** | Only schema-valid structured fields become proposals. Free text becomes content after the diff, or reaches the model fenced as "untrusted, from plugin X". Assets are staged in memory and written by the host into the mission folder on save, as part of the confirmed, undoable proposal. The host chooses the path. A plugin-supplied asset `name` is only a hint: it is sanitised (no separators, no `..`, no drive or UNC prefixes) and the media type must be on an allowlist such as OGG, WAV, PAA or JPG [I] |
| **Pinned prompts** | Tool descriptions, skills and MCP prompts all enter the model's context. Invariant Labs showed *tool poisoning* in April 2025: hidden instructions in tool descriptions that exfiltrate data. *Rug pulls* change descriptions after approval [V] (via search summary). Defences: hash pins, length caps, display at review (for MCP-served skills, the manifest; text on the user's request, see §2.3), re-review on any change |
| **No widening** | There are no cross-plugin calls; only the agent chains tools, and each call obeys the called plugin's grant. Mission text saying "upload everything to X" fails, because X is in no manifest. Init lines, conditions, *On Act* and scripts sit behind an `exec` scope that is off by default, and proposals that touch them are flagged high-risk (doc 17 open question 1). Chains inside workflows (answered 2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md), OWQ-16 = DG014 B): third-party pack workflows stay single-publisher; first-party and user-authored workflows may chain plugins of different publishers, with the egress card every time a step sends a value derived from another plugin's output, and such chains are never exposed to external agents. *Superseded in part by D043 (2026-09-27): "only the agent chains tools" no longer holds for cross-publisher chains in first-party and user-authored workflows.* |
| **Provenance** | Every applied command carries `Origin::Plugin{id, version, tool}`, shown in undo history and stored in the `.ofpeditor/` sidecar (doc 17 §11). Assets record plugin, service, model or voice id, timestamp and prompt hash. A "human edited" flag marks later user changes. Export offers an "AI-assisted" line (doc 09 §7.3) |
| **Signing and updates** | Packages are zips with a SHA-256 lockfile, signed by the publisher with Ed25519 in minisign format (`minisign-verify` 0.3.0, MIT, released 2026-09-25, so let it settle before pinning). The registry index is signed too; TUF (`tough` 0.24.0, MIT OR Apache-2.0) can later add rollback protection [V]. Unsigned sideloads show a badge and need a developer toggle. Channels: stable and beta. Auto-update is off for third-party sources, as Claude Code does for non-official marketplaces [V]. Signing proves origin, not safety: VS Code signs its Marketplace, yet "The extension host has the same permissions as VS Code itself" [V] |
| **Limits** | The tightest of the manifest `limits`, the user's caps and the effort budget (§4.2) wins. MCP servers "MUST ... Rate limit tool invocations" [V], but we do not rely on that. WASM also gets fuel, an epoch deadline, `StoreLimits` memory, and caps on output and proposal size |
| **Offline and kill switch** | Offline: T2 shows "offline", while T0 and T1 keep working and the editor stays fully usable (doc 09). Kill switch: "Disable all plugins", `--safe-mode`, per-plugin disable, and an optional signed revocation list (VS Code removes malicious extensions and uninstalls them automatically [V]). Disabling unwinds registrations, as in deepseek-harness, where "registrations are effects that unwind when their plugin unloads" (`DSH:docs/architecture.md#L11-L13`) [V]. In Rust: RAII registration handles |

---

## 4. Harness integration

### 4.1 Registration, namespacing, versioning [V]/[I]

**Registration.** Plugin tools join the built-in `ToolRegistry` with `source = Plugin(PluginId)` and the model-facing
name `<plugin>__<tool>`. Claude Code says "Every component is namespaced under" the plugin name, and opencode registers
MCP tools "with server name as prefix" (`OC:packages/web/src/content/docs/mcp-servers.mdx#L388`) [V]. The prefix is
the registry-unique plugin id, never the server's self-reported `serverInfo.name`, which MCP says "SHOULD NOT be relied
upon for disambiguation" [V]. Names are sanitised per provider as Codex does (doc 10 §2) [U]. Keep plugin ids short,
because provider tool-name limits (often 64 characters) apply after prefixing [U]. Tools reach the model only while
their plugin is enabled for the mission, and the plugin manager shows each plugin's token cost as Claude Code does
("Every turn" / "When invoked") [V], because each MCP server "adds to the context" (`OC:.../mcp-servers.mdx#L14`) [V].
Every plugin tool is also a menu or palette command, so it works with the agent off (doc 17 §2).

**Versioning.** WIT package `ofp:plugin@1.x.y` and manifest `api = 1`; the host supports the current and previous
major. Payloads carry schema ids (`editor-commands@1`, `mission-snapshot@1`) generated with `schemars`, with a CI drift
test between WIT and schemas. Like Proxy-Wasm's long-lived v0.2.1, keep the ABI small and grow through versioned payloads.

### 4.2 Effort budgets, workflows and skills

Effort levels come from doc 17 §4. The numbers are placeholders [I].

| | Quick | Standard | Thorough |
|---|---|---|---|
| T0/T1 calls per turn | ≤ 3 | ≤ 10 | ≤ 25 |
| T2 calls per turn | 0 unless the user invoked it | ≤ 3 | ≤ 10 |
| Egress per turn | 0 | ≤ 64 kB | ≤ 512 kB |
| Repair passes on invalid plugin output | 0 | 1 | 2 |

**Workflows [I].** A step names a tool (`uses = "radio-voice/synthesize_lines"`) and the workflow declares
`requires = ["radio-voice >=1.2"]`; a missing or disabled plugin skips the step with an explanation (`optional = true`)
or blocks the workflow. The callable set is the intersection of declared tools, enabled plugins and grants. Skills may
mention plugin tools but never grant them. (Publisher rule for `requires`, answered 2026-09-27 →
[D043](../decisions/D043-cross-plugin-chaining-in-workflows.md) item 1: load-time validation refuses a third-party pack
workflow whose `requires` names a plugin of another publisher; first-party and user-authored workflows follow items
2–4.)

### 4.3 UI surfaces and the shared command layer

**UI surfaces [I].** Menu and palette entries, map context actions ("Generate patrol here"), inspector sections and
progress with cancel, plus declarative panels (forms from flat JSON Schema as in MCP elicitation, tables, Markdown, map
overlays of typed points, polylines, areas and labels) rendered by the host in egui (doc 06). Plugins draw no pixels
and ship no HTML in v1, which is Figma's split between plugin logic and a host-controlled UI.

```
                EditorCommand registry + MissionQuery (typed Rust; schemars → JSON Schema)
    ┌─────────────────┬───────────────────┬──────────────────────┬───────────────────────────────┐
  GUI dialogs      Built-in agent      Plugins T0/T1/T2         Outbound MCP server `ofp-mcp`
  (the user)       (tool calls)        (proposals only)         (external agents; loopback + token)
    └──── validate → semantic diff → confirm → apply as one undo group, tagged with Origin ───────┘
```

**Queries** use one scoped `MissionQuery` (WIT imports for T1, host-built payloads for T2, MCP resources and tools on
`ofp-mcp`, doc 12 §3.4). **Edits** from every door are `Proposal<EditorCommand>` values admitted by the validator (doc
16 §4.3's `Proposal<T>` → `Admitted<T>`). Plugin tools are **not** re-exported through `ofp-mcp` in v1, so an external
agent cannot trigger egress on the user's behalf [I].

### 4.4 Testing [I]

`ofp-plugin-sdk` and `ofp-plugin-testkit` (`MIT OR Apache-2.0`; *superseded by
[D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 3, 2026-09-27: `GPL-3.0-or-later` for
now*) provide a mock host over synthetic missions only
(AGENTS.md fixture rules). Author conformance checks: golden proposals, seed determinism, schema validation of every
output, graceful `denied` handling, fuel and memory exhaustion, output caps, and prompt-injection fixtures (mission
text such as "ignore previous instructions ...") that must never reach `exec` fields. Connectors are tested against an
`rmcp` stub server for pin drift, SSRF (including IPv4-mapped IPv6 and redirect chains), oversize output, non-`https`
elicitation URLs (`steam:`, `file:`, `javascript:` must be refused) and hostile asset names (`../`, absolute paths).
Host adversarial tests load malicious components (infinite loops, memory bombs, huge or invalid-UTF-8 output, schema
violations, imports of `wasi:filesystem` or `wasi:sockets` that must fail to instantiate) and check seed determinism
with the seeded `wasi:random`. `ofp plugin check` lints manifests, and the
registry shows a conformance badge.

---

## 5. Licensing with a GPL-3.0-or-later host

### 5.1 What the texts say

| Source | Wording | Status |
|---|---|---|
| FSF FAQ, plug-ins | "If the main program dynamically links plug-ins, and they make function calls to each other and share data structures, we believe they form a single combined program, which must be treated as an extension of both the main program and the plug-ins." | [V] via a quoting article. The FSF's GPLv3-era draft FAQ on gplv3.fsf.org says "single program" [V] |
| FSF FAQ, exceptions for other authors' code (GPLv3-era draft, Q30) | "Only the copyright holders for the program can legally authorize this exception. ... But if you want to use parts of other GPL-covered programs by other authors in your code, you cannot authorize the exception for them." | [V] via `gplv3.fsf.org/wiki/index.php/FAQ_Update`; current gnu.org wording unverified [U] |
| FSF FAQ, fork/exec | "If the main program uses fork and exec to invoke plug-ins, and they establish intimate communication by sharing complex data structures, or shipping complex data structures back and forth, that can make them one single combined program. A main program that uses simple fork and exec to invoke plug-ins and does not establish intimate communication between them results in the plug-ins being a separate program." | [V] search excerpt |
| FSF FAQ `#MereAggregation` | "pipes, sockets and command-line arguments are communication mechanisms normally used between two separate programs. So when they are used for communication, the modules normally are separate programs." It is "a legal question, which ultimately judges will decide". | [V] |
| FSF FAQ, interpreters | "when the interpreter is extended to provide 'bindings' to other facilities ..., the interpreted program is effectively linked to the facilities it uses through these bindings. So if these facilities are released under the GPL, the interpreted program that uses them must be released in a GPL-compatible way." | [V] search excerpt |
| FSF FAQ, plug-in licenses | "If the main program and the plugins are a single combined program then this means you must license the plug-in under the GPL or a GPL-compatible free software license and distribute it with source code in a GPL-compliant way." | [V] search excerpt |
| GPLv3 §7 | "If additional permissions apply only to part of the Program, that part may be used separately under those permissions, but the entire Program remains governed by this License without regard to the additional permissions." Also: "You may place additional permissions on material, added by you to a covered work, for which you have or can give appropriate copyright permission." Recipients "may at your option remove any additional permissions". | [V] SPDX text |
| GPLv3 §2 | "You may make, run and propagate covered works that you do not convey, without conditions". Private combination is unrestricted. | [V] |
| FSF interface exception | Permits combining with "independent modules that communicate ... solely through the [interface]", "provided that you include the source code of that other code when and as the GNU GPL requires distribution of source code". It is void for a version where you "modify the [interface]" (SPDX `GPL-3.0-interface-exception`). It admits GPL-incompatible *free* modules, not closed ones | [V] text / [I] reading |
| Classpath exception | Permits linking "with independent modules to produce an executable, regardless of the license terms of these independent modules" (SPDX `Classpath-exception-2.0`, written for GPL-2.0). It is the usual template when closed modules are the goal | [V] |
| Blender | Scripts using its Python API, "if published", must be shared "under a GPL compliant license" | [V] |

### 5.2 Tier by tier

| Tier | Mechanism | Closest FSF position | Consequence | Status |
|---|---|---|---|---|
| T0 content | Data read by the host | Not a program; like a mission | Any license. Must not contain BI game data (APL-SA). (Plotroom's pack licence allowlist, answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 3: CC-BY-SA-4.0 only for editor-only content; mission-reaching content under CC0-1.0, MIT, Apache-2.0 or CC-BY-4.0) | [I] |
| T1 WASM | In-process component calling GPL host imports | Interpreter "bindings" or dynamic linking → combined program | Registry policy: distributed plugins must be **GPL-3.0-compatible**, e.g. MIT, Apache-2.0, BSD-2/3-Clause, ISC, Zlib, MPL-2.0 (unless marked "Incompatible With Secondary Licenses"), LGPL-2.1-or-later, LGPL-3.0, GPL-2.0-or-later, GPL-3.0. Not GPL-2.0-only, BSD-4-Clause or proprietary licenses (doc 02 §7.1). Private use of anything is unrestricted (GPLv3 §2) | [I]; no FSF statement on WASM [U]; courts have not tested the plug-in theory [U] |
| T2 remote MCP | A separate program on another machine, over sockets, using a public protocol | "normally separate programs" | Proprietary services are fine. The service is never conveyed to users, GPL-3.0 (unlike AGPL) has no network-interaction clause, we ship none of its code, and the manifest is data | [I] |
| Rejected: local stdio | Separate process over pipes | Separate unless "intimate" | Legally fine; rejected for security | [I] |
| Rejected: native dylib | Shared address space | Combined program | GPL-compatible only | [V]/[I] |
| Outbound `ofp-mcp` | External agent over stdio or a socket | Separate programs | Any agent | [I] |

Keep the T2 wire format a **published, versioned product schema** (commands, findings, snapshots), never internal
structs. That keeps connectors "at arm's length" even though the payloads are rich [I].

### 5.3 A plugin exception? Not now

**What we could do.** GPLv3 §7 lets us add a permission to *our own* code, like Iron Curtain D051's modding exception
(`ICD:src/decisions/09c/D051-gpl-license.md#L25-L41`) or a Classpath-style exception. The FSF interface-exception
template would not reach closed plugins, because it still requires the other code's source "when and as the GNU GPL
requires" (§5.1).

**Why it would not cover the whole program [V]/[I].** Our binary contains CWR-derived code (doc 02 §4.1), and Bohemia's
Additional Terms grant no such permission (doc 02 §2.1). We may place permissions only on material "for which you have
or can give appropriate copyright permission", and a permission covering part of the Program leaves "the entire
Program ... governed by this License without regard to the additional permissions". The FSF says the same in plain
words: for "parts of other GPL-covered programs by other authors ... you cannot authorize the exception for them".
Distributing a proprietary in-process plugin that forms a combined work with the editor would therefore still need
Bohemia's permission for the CWR-derived parts. It would also need permission from every CWR-CE contributor whose code
we import (doc 02 §2.2 shows CWR-CE takes community contributions under inbound=outbound GPL) [I].

**Iron Curtain's contrary claim [V]/[I].** D051 argues ("Why the Modding Exception Survives Combination with EA's GPL
Code", `#L45-L57`) that mods touch only Iron Curtain's own interfaces. That is a claim about *what a mod combines
with*, not a reading of §7, and it is untested. It is also weaker for us than for Iron Curtain. Their EA-derived code
sits in format parsers that mods never call (D051's D076 table, `#L112-L123`). Our plugin-facing domain (the mission
model and editor commands) is where doc 02 §4.1 expects ported `UIArcade*`/`ArcadeTemplate*` code to live [I]. D051
also cites "Blender (GPL) + Python scripts (any license)" (`#L15-L19`), which Blender's own license page contradicts:
"such scripts (if published) are being shared under a GPL compliant license" [V].

**Recommendation [I].**

1. No plugin exception in v1.
2. Distributed T1 plugins need a GPL-3.0-compatible license, enforced as registry policy. Zed has required an accepted
   license for registry extensions since 2025-10-01 [V]. A docs mirror (zedhub.dev) lists only "MIT, Apache 2.0";
   zed.dev did not show that section when fetched [U].
3. Proprietary integrations go through T2.
4. The SDK, WIT and test kit are `MIT OR Apache-2.0` with no CWR-derived code (doc 02 §6.3 permissive lane). The
   payload schemas they ship describe mission fields and formats, which are free facts under doc 02 §4.2. Write them
   as our own schemas, not as a dump of ported types. *Licence superseded by
   [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 3 (2026-09-27, OWQ-03 (a)):
   `GPL-3.0-or-later` for now, since registry T1 plugins must be GPL-3.0-compatible anyway; revisited at MVP step 3
   only if plugin authors ask. Doc 02's permissive lane does not exist (D001).*
5. Revisit only if Bohemia (and any imported CWR-CE contributors) grant a matching permission. Showing that the host
   imports reach only our original code is Iron Curtain's argument, not the FSF's, so it is not enough on its own. For
   closed plugins, use a Classpath-style permission scoped to `ofp:plugin`. For GPL-incompatible *free* plugins only,
   use the FSF interface exception.
6. Adding any exception later also needs every DCO contributor's consent for their code, unless CONTRIBUTING grants
   it in advance (open question 10). (The DCO is adopted: answered 2026-09-27 →
   [D032](../decisions/D032-contribution-terms-dco.md); [D031](../decisions/D031-generated-content-permission-and-licence-scope.md)'s
   Consequences restate this rule.)
7. Include this section in the pre-1.0 legal review.

Content a plugin writes into a mission falls under the plugin's or service's terms; our templates fall under the
Generated Content Exception (doc 02 §6.2) [I]. (Its wording, answered 2026-09-27 →
[D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 1: the doc 02 §6.2 draft plus an
explicit coverage list that includes first-party pack content copied into missions.)

---

## 6. Prior-art lessons

| Product | Model | Sandbox / permissions | Lesson for us |
|---|---|---|---|
| **VS Code** | JS extension host | "same permissions as VS Code itself"; publisher-trust prompt since 1.97; signed, scanned Marketplace [V] | Signing and scanning do not make unsandboxed code safe |
| **Zed** | Rust → `wasm32-wasip2` extensions, including MCP servers [V] | User grants for `process:exec`, `download_file`, `npm:install`, apparently broad by default [I]; license requirement [V] | WASM plus grants works in a Rust desktop app. We grant nothing like `process:exec`, and our defaults start narrow |
| **Figma** | Sandboxed thread + UI iframe [V] | `networkAccess.allowedDomains` + `reasoning`; unlisted domains blocked by CSP; reasons public [V] | Keep logic apart from UI and network; publish the reasons |
| **Obsidian** | JS plugins | "cannot reliably restrict plugins"; Restricted Mode by default; automated scans [V] | Off by default is UX, not enforcement |
| **Blender** / **Blender MCP** | Python add-ons; manifest `permissions` (`files`, `network`, `clipboard`, `camera`, `microphone`) with reasons [V] | Declared, not enforced: a third-party issue shows undeclared clipboard use [V]/[I]. `execute_blender_code` runs arbitrary Python over an unauthenticated socket (doc 15) [V] | Declared-only permissions are theatre; arbitrary-code tools are the anti-pattern |
| **Godot GDExtension** | Native shared libraries [V] | None; the community built a libriscv-based RISC-V sandbox, itself shipped as a GDExtension (`libriscv/godot-sandbox`) [V] | Native means full trust |
| **JetBrains** | JVM plugins | Author and Marketplace signatures. IDEs have verified them since 2021.2, with a warning dialog for unsigned or revoked plugins, and 2021.2.1 added a custom truststore property [V] | A good signing chain, but no sandbox |
| **Claude Code** | `.claude-plugin/plugin.json` bundling skills, agents, hooks, MCP/LSP servers [V] | "can execute arbitrary code on your machine with your user privileges"; namespacing; `sensitive` config; SHA-256-pinned archives; third-party auto-update off [V] | Copy namespacing, sensitive config, pinning, token-cost display and update policy; do not copy hooks or `bin/` |
| **Codex** | MCP client on `rmcp` (pinned `=3.2.0` at `CX:codex-rs/Cargo.toml#L444`); plugins bundle `skills`, `hooks`, `mcpServers`, `apps` (`CX:codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md#L3-L68`) [V] | `enabled_tools`/`disabled_tools`; discovers `.codex-plugin`, `.claude-plugin` and `.cursor-plugin` manifests (`CX:codex-rs/exec-server-protocol/src/protocol.rs#L49-L53`) and recognises a cross-vendor "Agent Plugins v1" schema (`CX:codex-rs/utils/plugins/src/plugin_namespace.rs#L12-L18`) [V] | The ecosystem is converging on "plugin = skills + MCP servers"; our filter extends Codex's |
| **opencode** | JS/TS plugins auto-loaded from folders or npm (installed with Bun), given Bun's shell `$` (`OC:packages/web/src/content/docs/plugins.mdx#L20-L25`, `#L48`, `#L107-L122`) [V] | None | In-process scripting with a shell is the opposite of our invariant |
| **pi** | TS extensions and packages | Extensions "run with those same permissions"; project trust "does not make that content ... safe" (`PI:packages/coding-agent/docs/security.md#L3-L7`) [V] | Trust prompts are not a boundary |
| **deepseek-harness** | Everything is a Cordis plugin with reversible registration (`DSH:docs/architecture.md#L11-L13`) [V] | Sandbox backends for processes | Reversible registration makes a clean kill switch |
| **Iron Curtain** | YAML → Lua → WASM tiers (`ICD:src/04-MODDING.md#L5-L22`); D071 JSON-RPC and MCP with permission tiers (`ICD:src/decisions/09f/D071-external-tool-api.md#L70-L85`) [V] | Capabilities, elevated-off defaults, reasons, hash-keyed re-review, DNS-rebinding defence, fuel and host-call limits (`ICD:src/modding/wasm-modules.md#L51-L305`) [V] | Adopt nearly all of it except Lua. Our T2 is the "service" tier Iron Curtain lacks |
| **Envoy / Proxy-Wasm** | WASM filters [V] | One host-defined ABI (v0.2.1) across hosts [V] | Small, stable ABI; versioned payloads |

---

## 7. Recommendation

### 7.1 The tiered model and MVP order

| Tier | What | Runs | Can | Cannot |
|---|---|---|---|---|
| **T0 content pack** | Skills, workflows, prompts, compositions and templates (minijinja + fuel), lint rules, overlays, campaign templates | Nothing runs | Feed the agent, templater and validator | Execute anything; widen tool access |
| **T1 local generator** | WASM component (`wasmtime` LTS, WIT `ofp:plugin@1`) | In-process sandbox (Cranelift); fuel, epoch and memory limits; minimal WASI with no filesystem or sockets, seeded random | Read granted scopes; return proposals, findings, assets, panels | Touch files, network or processes; apply edits |
| **T2 service connector** | Manifest + pinned remote MCP endpoint (Streamable HTTP, OAuth 2.1) | On the service's machine | Receive payloads the host builds; return typed results through the gate | Reach unpinned tools or origins; see secrets or raw files |
| Rejected | Native dylibs, local stdio MCP, Lua/Rhai tiers, sampling, HTML UI (v1) | — | — | — |

| Step [I] | Scope | Exit evidence |
|---|---|---|
| **0. Prerequisites** | `EditorCommand` registry, `MissionQuery` scopes, validator, semantic diff, undo groups, `Origin` (doc 17 ranked items 1–3) | Tests prove the GUI and the agent share one apply path |
| **1. T0 packs** | Manifest v1; plugin manager (install from folder or zip, enable, disable, kill switch); skills, workflows, compositions, lints, overlays | Fixtures; hash-pinned review; safe-mode test |
| **2. T2 connectors** | `rmcp` Streamable HTTP client, scope gate, egress card and log, keyring, OAuth, limits, offline state; stringtable translator first, then Radio Voice | Stub-server tests: pin drift, SSRF, oversize output, secrets never logged, non-`https` URL refusal, hostile asset names; a spike confirming `rmcp` uses our guarded HTTP client |
| **3. T1 WASM** | wasmtime 48 LTS host, WIT `ofp:plugin@1`, SDK and test kit, patrol and ambush reference plugins, declarative panels | Adversarial component suite; determinism tests; a documented process for shipping wasmtime security releases |
| **4. Distribution** | Signed index (minisign, then TUF), channels, revocation list, community-library connector | Signature and rollback tests |

The outbound `ofp-mcp` server can ship any time after step 0, because it uses the same registry. (Answered 2026-09-27
→ [D036](../decisions/D036-v1-contents-and-release-split.md) item 6, OWQ-15 (a): the opt-in MCP server ships in v1;
workflows using T2 plugin tools and cross-publisher chains are not exposed through it (D036's Consequences;
[D043](../decisions/D043-cross-plugin-chaining-in-workflows.md) item 4).)

### 7.2 Manifest sketch (`plugin.toml`)

```toml
[plugin]
id = "radio-voice"                 # kebab-case, registry-unique; namespace for tools
name = "Radio Voice"
version = "1.2.0"
api = 1                            # ofp:plugin major (T1) / host payload-schema major (T2)
kind = "connector"                 # "content" | "wasm" | "connector"
license = "LicenseRef-Proprietary" # T2 may be anything; T1 must be GPL-3.0-compatible (SPDX)
min_editor = "0.9.0"

[provides]
tools = ["synthesize_lines", "list_voices"]
workflows = ["workflows/voice-radio-chatter.toml"]
skills = ["skills/radio-procedure"]

[[tool]]
name = "synthesize_lines"
effect = "asset"                   # "query" | "proposal" | "finding" | "asset"  (never "apply")
input = "dialogue-lines@1"         # host-owned schema ids
output = "audio-clips@1"
reads = ["dialogue.selected", "cast.voice_profile"]
proposes = ["sound.add", "radio.add"]
essential = true

[network]                          # T2 only; T1 has no [network] in v1
transport = "mcp-streamable-http"
endpoints = ["https://api.example.com/mcp"]
reasoning = "Sends the selected line text and chosen voice id to the TTS service"

[secrets]
api_key = { label = "API key", kind = "bearer", store = "os-keyring" }   # or kind = "oauth" (required if the server advertises MCP auth)

[limits]
calls_per_minute = 20
max_request_bytes = 262144
max_response_bytes = 16777216
timeout_ms = 30000

[disclosure]
generated = "ai-voice"
voice_source = "licensed-stock"    # registry policy: no cloning of real people

# [pins] is NOT part of the package. Shown for illustration only: the installer writes it to the host's grant
# store, keyed by plugin id. A package that ships its own [pins] is rejected.
# [pins]
# tool_definition_sha256 = { synthesize_lines = "…", list_voices = "…" }
# capability_hash = "…"            # over license/provides/tool/network/secrets/limits/disclosure (and [wasm] for T1)
```

A T1 plugin replaces `[network]` and `[secrets]` with `[wasm]` (`component`, `sha256`, `fuel_per_call`, `memory_mb`,
`deadline_ms`). Unknown keys are rejected (`serde(deny_unknown_fields)`), like Claude Code's strict `userConfig`
options ("An unknown key inside one is an error"; Claude Code only strips unknown *top-level* manifest fields with a
warning) [V]/[I]. Pins live outside the package, as in Iron Curtain's local grant store
(`ICD:src/modding/wasm-modules.md#L234-L259`). Otherwise an author could ship pre-approved hashes [I].

### 7.3 WIT and Rust sketches [I]

```wit
package ofp:plugin@1.0.0;

interface types {
  /// JSON text, validated host-side against a versioned host schema such as "editor-commands@1".
  type json = string;
  enum effect { query, proposal, finding, asset }
  record tool-descriptor { name: string, title: string, effect: effect, input-schema: string, output-schema: string }
  enum severity { error, warning, advice }
  record finding { code: string, severity: severity, object: option<string>, field: option<string>,
                   message: string, fix: option<json> }
  record asset { name: string, media-type: string, bytes: list<u8> }
  record proposal { title: string, commands: json, rationale: option<string> }
  record panel { title: string, model: json }        // declarative: form / table / markdown / map overlay
  variant tool-output { proposal(proposal), findings(list<finding>), assets(list<asset>), panel(panel), text(string) }
  variant host-error { denied(string), invalid(string), limit-exceeded(string), not-found(string), unavailable(string) }
}

interface mission-query {                             // every call is checked against the grant's read scopes
  use types.{json, host-error};
  selection: func() -> result<json, host-error>;
  query: func(scope: string, filter: json) -> result<json, host-error>;   // "groups", "markers", "triggers", ...
  catalog: func(filter: json) -> result<json, host-error>;                // local-only, never egress
  terrain-height: func(x: f32, z: f32) -> result<f32, host-error>;
  roads-in: func(min-x: f32, min-z: f32, max-x: f32, max-z: f32) -> result<json, host-error>;
}

interface host-log {
  log: func(level: u8, message: string);
  progress: func(fraction: f32, note: string);        // drives the host progress bar and cancel
}

interface tool {
  use types.{tool-descriptor, json, tool-output, host-error};
  describe: func() -> list<tool-descriptor>;
  invoke: func(name: string, input: json, seed: u64) -> result<tool-output, host-error>;
}

world generator { import mission-query; import host-log; export tool; }
```

```rust
/// Host-side core types (proposal; names illustrative). Fields private; transitions enforce invariants.
pub struct PluginId(Box<str>);                        // newtype, validated kebab-case
pub enum ReadScope { Selection, MissionMeta, Groups, Triggers, Markers, Scripts, Briefing,
                     Stringtable, Dialogue, CastProfile, Campaign, Catalog, Terrain, Roads }
pub enum ProposalKind { PlaceUnits, AddWaypoints, AddTriggers, AddMarkers, SetStrings, SetBriefing,
                        AddSound, AddRadio, CampaignEdit, Exec /* high-risk, off by default */ }
pub struct Grant { capability_hash: Sha256, reads: BTreeSet<ReadScope>,
                   proposes: BTreeSet<ProposalKind>, endpoints: Vec<AllowedOrigin>, limits: Limits }
pub enum PluginState {                                // enum state machine, no boolean flags
    Installed { manifest: Manifest },
    Enabled { manifest: Manifest, grant: Grant, registrations: RegistrationSet /* RAII: drop = unregister */ },
    NeedsReview { manifest: Manifest, previous: Grant, diff: CapabilityDiff },
    Disabled { manifest: Manifest, reason: DisableReason },
}
pub enum Origin { User, Agent { model: ModelId }, Plugin { id: PluginId, version: Version, tool: ToolName } }

/// Plugin output starts untrusted; only `admit` yields what `apply` accepts (doc 16 §4.3).
pub struct Untrusted<T>(T);
impl Untrusted<RawToolOutput> {
    pub fn admit(self, schema: &HostSchema, grant: &Grant, validator: &Validator)
        -> Result<Admitted<PluginResult>, PluginError> { /* schema → scope → validator */ }
}
```

Keep the WIT envelope small and stable. Large, evolving domain data travels as JSON validated against versioned host
schemas. Whether that data should become typed WIT records is an open question.

### 7.4 AGENTS.md wording this implies

In "Non-Negotiable Product Invariant", replace the current "Extensions only through the plugin system" bullet with
the three bullets below. Keep the other bullets unchanged.

```markdown
- **Extensions only through the plugin system.** The agent's capabilities may be extended only by plugins the user
  explicitly installs and enables. Exactly three kinds exist: data-only content packs (skills, workflows, prompt and
  mission templates, compositions, catalog overlays, declarative lint rules); sandboxed WebAssembly components that
  the editor runs with no ambient authority, only the host imports their grant allows; and service connectors reached
  over MCP Streamable HTTP (HTTPS, or loopback to a service the user runs and enters), limited to the tools and
  endpoints their manifest pins. Native-code plugins, plugin-launched processes (including locally spawned MCP servers
  and OS URL handlers), embedded general-purpose script interpreters, and any other ad-hoc tool loading are not
  allowed. The design lives in `docs/` (plugin system research and its decision record).
- **Plugins propose; the editor applies.** Every plugin manifest declares its typed tools, workflows and skills, the
  mission and campaign data it may read, the edits it may propose, the endpoints it contacts, the secrets it needs,
  and its limits. The host enforces these declarations; a request outside the grant fails instead of prompting.
  Plugin results are untrusted data: they are validated against host-owned schemas and reach the mission only as
  proposals through the same typed, validated, undoable commands the user uses, tagged with the plugin's provenance.
  Text from plugins (descriptions, skills, outputs) can never widen a grant, and no plugin calls another plugin.
- **Egress is disclosed and bounded.** Before a plugin first sends mission data off the machine, the user sees what
  will be sent and to which host. File paths, user names and raw game files are never sent. Secrets live in the OS
  keyring, are attached by the host, and are never visible to plugin code or the model. The editor stays fully
  usable offline and with every plugin disabled, and one switch disables all plugins.
```

---

## Open questions

1. **Registry governance.** Who hosts and moderates the index (takedowns, voice-cloning policy, name squatting)? Could
   an OFP community site run it? [U] (Answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md)
   item 4, OWQ-17 = DG030 item 4: no operator until the registry is scheduled; then the project's own GitHub
   organisation runs it with doc 42 §5.3's governance. A community site as operator was not chosen.)
2. **Payload typing.** Should payloads be full WIT records, or JSON validated against versioned schemas as proposed
   here? Decide after a spike with two reference plugins. [I]
3. **Guests and footprint.** How mature are componentize-js/py and TinyGo on WASI 0.3? How much do wasmtime and
   Cranelift add to binary size and startup? Would the Pulley interpreter help? Winch had a CRITICAL sandbox escape
   in 2026 (RUSTSEC-2026-0095), so keep it out unless it matures [U]/[V].
4. **REST-only services.** Should T1 get a host-mediated `net.fetch` (allowlisted, secrets injected) so it can adapt
   TTS or translation services that have no MCP server? Or should we require MCP? [I] (answered 2026-09-27 →
   [D008](../decisions/D008-outbound-network-sources.md) items 3 and 5: no general `net.fetch`; read-only catalogs use the GET-only
   `feed` connector kind.)
5. **Legal.** Is a component that calls host imports through the canonical ABI "linked" in the FSF's sense? Should we
   ask Bohemia for a plugin permission? Is sending class or island names to a service a "Share" under APL-SA (doc 02
   §3.4)? [U]
6. **Voice policy.** How can the registry verify "licensed stock voices" beyond self-declaration? [U]
7. **Deferred features.** Is HTML UI (MCP Apps, which needs a webview in egui) ever worth it? Should plugin tools
   ever be re-exported through `ofp-mcp`? What trust signal should a loopback service the user runs need? [I]
   (Re-export answered in part 2026-09-27: v1's MCP server does not expose workflows that use T2 plugin tools,
   [D036](../decisions/D036-v1-contents-and-release-split.md) item 6 and its Consequences; cross-publisher chains are
   never exposed,
   [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md) item 4.)
8. **Defaults.** The limits and effort budgets need measurement. [I]
9. **Doc 21 (agent doctrine).** Reconcile the skill and workflow formats in §4 here with the workflow definition
   format in `21-agent-doctrine.md` and the Selector seam in `16-decision-models.md`. The install review is §3.1 here,
   and per-send egress disclosure is covered by the §3.1 prompt table (the egress card repeats for agent-initiated
   sends while untrusted text is in context). [I]
10. **Keeping an exception possible.** If the owner may someday want a Classpath-style plugin permission (for example
    after a grant from Bohemia), CONTRIBUTING should say now that contributions also carry that future permission for
    the plugin interface. Otherwise every DCO contributor must consent later (doc 02 §5, cost 4). [I]
11. **OAuth plumbing.** Who hosts the editor's Client ID Metadata Document (a stable HTTPS URL), and does `rmcp`'s auth
    module route discovery requests through our SSRF-guarded client? [U]

---

## Sources

| Group | Sources |
|---|---|
| Iron Curtain design docs (`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`) | `src/decisions/09c/D005-wasm-mods.md#L1-L12`; `src/modding/wasm-modules.md#L27-L123`, `#L148-L259`, `#L276-L314`; `src/04-MODDING.md#L5-L45`; `src/decisions/09f/D071-external-tool-api.md#L6-L20`, `#L70-L85`, `#L257-L278`, `#L320-L361`; `src/decisions/09c/D051-gpl-license.md#L1-L123` |
| Codex (`openai/codex@e72da2b538`) | `codex-rs/Cargo.toml#L444`; `codex-rs/codex-mcp/src/tools.rs#L63-L103`; `codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md#L1-L89`; `codex-rs/utils/plugins/src/plugin_namespace.rs#L1-L18`; `codex-rs/exec-server-protocol/src/protocol.rs#L49-L53` |
| opencode (`anomalyco/opencode@b65de4d694`) | `packages/web/src/content/docs/plugins.mdx#L12-L122`, `#L278-L309`; `packages/web/src/content/docs/mcp-servers.mdx#L6-L17`, `#L347-L394` |
| pi, deepseek-harness, rig | `earendil-works/pi@2b0a123de9:packages/coding-agent/docs/security.md#L3-L53`, `.../docs/packages.md#L19-L21`; `deepseek-ai/deepseek-harness@477b4f4205:docs/architecture.md#L9-L27`; `0xPlaygrounds/rig@42f4e060ef:Cargo.toml#L262` |
| Sibling notes (`docs/research/`) | 02 (§2.1, §2.2, §3.4, §4.1, §4.2, §5, §6.2, §6.3, §7.1), 04 (§5, §10), 06, 09 (§6, §7, WN2), 10 (§2), 11, 12 (§1.8, §3.4), 15 (§6.5), 16 (§4.2–§4.4), 17 (§2–§6, §11), 18, 19, 21 (§D1, §D4, "Tensions") |
| MCP 2026-07-28 (retrieved 2026-09-26) | <https://modelcontextprotocol.io/specification/latest> and its `/2026-07-28/basic/transports`, `/basic/authorization`, `/client/elicitation`, `/client/roots`, `/server/tools`, `/deprecated` pages; <https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices>; <https://modelcontextprotocol.io/extensions/apps/overview>; <https://modelcontextprotocol.io/extensions/skills/overview>; <https://modelcontextprotocol.io/community/working-groups/skills-over-mcp>; <https://github.com/modelcontextprotocol/mcpb> |
| Rust crates and runtimes | <https://github.com/modelcontextprotocol/rust-sdk>; <https://docs.wasmtime.dev/stability-release.html>; <https://docs.wasmtime.dev/security.html>; <https://docs.rs/wasmtime/latest/wasmtime/struct.Store.html>; <https://wasi.dev/releases/wasi-p3>; <https://rustsec.org/advisories/RUSTSEC-2026-0269.html>; <https://rustsec.org/advisories/RUSTSEC-2026-0268.html>; <https://rustsec.org/packages/wasmtime.html>; <https://github.com/leaderiop/SpecForge/issues/10>; `https://crates.io/api/v1/crates/<name>` for `rmcp`, `rig-rmcp`, `wasmtime`, `extism` (plus `/1.30.0/dependencies`), `minijinja` (`/versions`), `mlua`, `rhai`, `keyring`, `tera`, `minisign-verify`, `tough`, `wit-bindgen`; <https://docs.rs/minijinja/2.24.0/minijinja/>; <https://docs.rs/rmcp/latest/rmcp/transport/index.html>; <https://docs.rs/mlua/latest/mlua/struct.Lua.html>; <https://rhai.rs/book/safety/index.html>; <https://docs.rs/libloading/latest/libloading/struct.Library.html> |
| Prior art | Zed <https://zed.dev/docs/extensions/capabilities>, <https://zed.dev/docs/extensions/developing-extensions>, mirror <https://zedhub.dev/extensions/developing-extensions>; Figma <https://developers.figma.com/docs/plugins/how-plugins-run/>, <https://developers.figma.com/docs/plugins/making-network-requests>; <https://github.com/proxy-wasm/spec>; VS Code <https://code.visualstudio.com/docs/configure/extensions/extension-runtime-security>; <https://obsidian.md/help/plugin-security>; Blender <https://developer.blender.org/docs/features/extensions/schema/1.0.0/>, <https://www.blender.org/about/license/>, <https://github.com/scenario-labs/blender-plugin/issues/16>; Godot <https://github.com/libriscv/godot-sandbox> (upstream; <https://github.com/fireflyk64/godot-sandbox> is a fork; GDExtension docs via search summary); <https://plugins.jetbrains.com/docs/intellij/plugin-signing.html>; Claude Code <https://code.claude.com/docs/en/plugins-reference>, <https://code.claude.com/docs/en/discover-plugins>, <https://code.claude.com/docs/en/plugins/security>; <https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks> (via search summary) |
| GPL | FSF FAQ <https://www.gnu.org/licenses/gpl-faq.html> (unreachable again on 2026-09-26; wording via <https://tech.popdata.org/the-gpl-license-and-linking-still-unclear-after-30-years/>, search excerpts, and the FSF's GPLv3-era FAQ draft <https://gplv3.fsf.org/wiki/index.php/FAQ_Update>); <https://spdx.org/licenses/GPL-3.0-or-later.html>; <https://spdx.org/licenses/GPL-3.0-interface-exception.html>; <https://spdx.org/licenses/Classpath-exception-2.0.html> |

---

## Verification notes

**2026-09-26, adversarial review.** Each decision-critical claim was re-checked against live sources (MCP spec pages,
crates.io API, RustSec, SPDX, vendor docs) and the pinned local clones. gnu.org still refused connections, so FSF
wording was checked against the FSF's own GPLv3-era FAQ draft on gplv3.fsf.org.

**Confirmed as written.**

- MCP 2026-07-28 is stateless ("Stateless, self-contained requests"; "servers do not initiate JSON-RPC requests").
- Its two transports are stdio and Streamable HTTP.
- OAuth applies to HTTP, and stdio "SHOULD NOT" use it.
- "Clients MUST consider tool annotations to be untrusted unless they come from trusted servers" appears on the tools
  page.
- The overview says "Hosts must obtain explicit user consent before invoking any tool" (lowercase, so not normative).
- SEP-2640 is Final (merged 2026-09-13), and the Skills extension has digest-bound approval.
- The best-practices page lists "Arbitrary code execution" for local servers and asks for sandboxing (SHOULD). It
  gives SSRF guidance and the "MUST NOT use shell commands" URL rule.
- Crate versions and licenses: `rmcp` 3.4.1 (2026-09-23, Apache-2.0; child-process and Streamable HTTP clients),
  `wasmtime` 49.0.1 (2026-09-24), `extism` 1.30.0 (2026-06-04, BSD-3-Clause), `mlua` 0.12.1 (MIT), `rhai` 1.26.1,
  `keyring` 4.2.0 (MIT OR Apache-2.0), `tera` 2.4.0 (MIT), `minijinja` 2.24.0 (latest stable), `wit-bindgen` 0.62.0,
  `tough` 0.24.0, `minisign-verify` 0.3.0 and `libloading` (`Library::new` is `unsafe`).
- Wasmtime release, LTS and backport policy wording, and the RUSTSEC-2026-0269 facts.
- GPLv3 §7 and §2 wording (SPDX); Blender's add-on license sentence.
- Claude Code quotes (arbitrary code, namespacing, `sensitive` storage, third-party auto-update off by default).
- VS Code, Obsidian, Figma, Proxy-Wasm and Blender manifest-permission quotes.
- Every pinned-clone citation (Codex, opencode, pi, deepseek-harness, Iron Curtain D005/D051/D071).

**Corrected.**

1. "Elicitation is the only client feature" was incomplete. Roots, Sampling, server Logging and DCR are
   **Deprecated** in 2026-07-28 (SEP-2577 / PR #2858), with earliest removal on or after 2027-07-28. Sampling was
   described as absent; it is deprecated.
2. Tool-name length and characters, and server-prefixing, are SHOULDs, and `serverInfo.name` must not be the prefix.
   Added the RFC 9207 `iss` MUST, `x-mcp-header`, and the URL-mode "MUST NOT automatically pre-fetch".
3. The "MUST NOT use shell commands" rule comes from MCP's *OAuth authorization URL* section, not elicitation. We now
   apply it to all URLs and allow `https:` only, because OS URL handlers (`steam://`, `file:`) could launch the game
   or local programs, which the invariant forbids.
4. Extism: crates.io shows `extism` 1.30.0 depending on `wasmtime`/`wasi-common`/`wiggle` `^43`, not 41.x as the
   third-party issue said. The conclusion (unpatched, unsupported) stands and is now primary-sourced.
5. `rig-rmcp` on rmcp 2.x is now [V] (`rig@42f4e060ef:Cargo.toml#L262`).
6. The FSF interface-exception template requires shipping the other code's *source*, so it cannot enable proprietary
   in-process plugins. §5.3 now names a Classpath-style permission for that case.
7. JetBrains verification dates from 2021.2 (2021.2.1 added a truststore property).
8. Godot sandbox citation moved to upstream `libriscv/godot-sandbox`.
9. The D051 quote was fixed to its actual heading.
10. T1 license list was made precise (BSD-2/3-Clause, MPL-2.0 caveat, GPL-2.0-only excluded).

**Added after review [I].**

- Wasmtime's 2026 CRITICAL escapes (RUSTSEC-2026-0095 Winch, -0096 aarch64 Cranelift) and the WASIp3-streams
  advisory (-0268), with consequences: Cranelift only, no p3 streams, prompt patch releases.
- Minimal WASI linking, plus a seeded `wasi:random` and a fixed clock for seed determinism.
- Registry manifests may not pin loopback or private origins.
- Asset-name sanitisation and host-chosen paths.
- `[pins]` moved out of the author-controlled package.
- Bearer-versus-OAuth rule; CIMD hosting and the loopback-redirect risk; Linux keyring fallback.
- MCP Skills' "MUST NOT retrieve files ahead of need" applied to the review screen.
- Usability: an Iron Curtain-style light install for non-elevated plugins, and an "Always for this plugin" egress
  choice.
- Security: a per-send card for agent-initiated calls while untrusted text is in context, which reconciles with doc
  21's per-send disclosure and "rule of two". The deviation from MCP's "show tool inputs" SHOULD is now explicit.
- Licensing: the FSF's "you cannot authorize the exception for them" quote; CWR-CE contributors; the observation that
  our plugin-facing domain is where CWR-derived code lives (weakening the Iron Curtain argument for us); the "not
  conveyed / no AGPL clause" basis for T2; and open questions 10–11.

**Still unverified [U].**

- Current gnu.org FAQ wording (only the GPLv3-era draft and third-party quotations were reachable).
- Whether `rmcp` 3.4.1 accepts a caller-supplied HTTP client and routes OAuth discovery through it.
- Exact `WasiCtxBuilder` hooks for seeded random and fixed clocks.
- Zed's accepted-license list on zed.dev itself.
- Invariant Labs details (search summary only).
- Guest-language maturity on WASI 0.3.
- Whether any court would treat a WASM component as "linked".

**2026-09-27, owner answers folded by pointer.** The TL;DR licensing bullet, §3.2 "No widening", §4.2 workflows,
§4.4, the §5.2 T0 row, §5.3 items 4 and 6 and its closing paragraph, §7.1 and open questions 1 and 7 now point to
D031, D032, D036, D038 and D043. Superseded notes: the permissive SDK, WIT and test-kit licence (D031 item 3) and, in
part, "only the agent chains tools" (D043). No analysis was rewritten; open questions 5 and 10 stay open.
