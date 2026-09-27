# Licensing and Trademarks: Code License, Game-Data Rules, Model Weights and Naming

> **Not legal advice.** This is engineering research by project contributors. Before the first public
> release, have a lawyer or an experienced FOSS-licensing volunteer review §6 (recommendation) and §9 (naming).

**Scope.** This document chooses the license for this project's own code. It also covers what we may do with
Bohemia Interactive's code (GPL) and game data (APL-SA), how to handle model weights for the AI harness, and how to
name the product without infringing trademarks. It stands alone: terms are defined in §1.

**Pinned sources.** `BohemiaInteractive/CWR@ffc61838b7` ("3.05", 2026-08-18) and `ofpisnotdead-com/CWR-CE@b67bf3bd62`
(2026-09-21). Also `iron-curtain-engine/iron-curtain@7b7fac7fa5`, `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`,
and the harness reference repos listed in §7.1. Web sources were retrieved on 2026-09-26.

**Epistemic legend.** **[V]** = verified by reading the source (citation given). **[I]** = inferred, our reading or
legal reasoning. **[U]** = unknown or unverified.

---

## TL;DR

- **License the project as `GPL-3.0-or-later`, the same license as CWR and CWR-CE.** GPLv3 is the only license family
  that lets us translate Bohemia's editor C++ (`UIArcade*.cpp`, `ArcadeTemplate*`) into Rust. It also keeps code
  flowing both ways with CWR-CE. It matches the copyleft norm of Arma tooling (HEMTT, armake2, CBA, ACE3). **[V]/[I]**
- **Carry Bohemia's GPLv3 §7 "Additional Terms" verbatim** in a `NOTICE` file shipped with every source and binary
  distribution. The terms require it ("Any propagation or conveyance of this program must include this copyright notice
  and these terms"), and they cost us nothing to comply with. **[V]**
- **Add one additional permission of our own (GPLv3 §7):** mission files, scripts and templates that the editor writes
  into user output are not subject to the GPL. Mission makers can then license their missions however they want.
  **[I]**, precedent: Bison exception, iron-curtain D051. (Answered 2026-09-27 →
  [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 1: the §6.2 draft plus an explicit
  coverage list, with a legal review before 1.0.)
- **Optional permissive lane:** a generic LLM-harness crate that contains no game code and no CWR-derived code may be
  `MIT OR Apache-2.0`. Decide **now**, because DCO contributions cannot later be relicensed from GPL without every
  author's consent. Format and editor crates stay GPL. **[I]**, precedent: iron-curtain D051/D076. *Superseded by
  [D001](../decisions/D001-licence-gpl-3-or-later.md) (owner, 2026-09-26; noted 2026-09-27): there is no permissive
  lane, and the plugin SDK is GPL too ([D031](../decisions/D031-generated-content-permission-and-licence-scope.md)
  item 3).*
- **Game data is APL-SA** (NonCommercial, "ArmaOnly", ShareAlike, Attribution). This covers both the Steam demo and the
  full game. **Load it at runtime from the user's install. Never commit, bundle, convert-and-ship or auto-upload it.**
  No evidence was found that the demo data is licensed differently: Bohemia's CWR README points demo and full-game data
  at APL-SA. The Steam demo page calls the demo an "official asset pack" but does not itself name APL-SA or
  NonCommercial. **[V]** sources / **[I]** conclusion
- **HEMTT crates cannot be linked into our GPL-3.0 binary.** Their metadata says `GPL-2.0` and no "or later" grant was
  found. armake2 is `GPL-2.0-or-later` and is compatible. The standard Rust permissive licenses (MIT, Apache-2.0, BSD,
  ISC, Zlib) and MPL-2.0 are all fine to use. **[V]/[I]**
- **Model weights are data that sits next to the program ("aggregate"), not derivative works of it.** Default
  downloads should only offer OSI-licensed weights: Apache-2.0 (Qwen3.6, Gemma 4, SmolLM3) or MIT (Phi-4-mini).
  Llama and Gemma ≤3 carry pass-through use restrictions, so users must bring those themselves. Do not bundle weights
  inside the GPL release archive. **[V]/[I]** (Answered 2026-09-27 →
  [D037](../decisions/D037-model-manager-recommended-list.md): the recommended list takes only OSI licences with no
  field-of-use restriction that passed Plotroom's qualification; everything else installs as "custom".)
- **Rename the product and repo before any release.** Drop "OFP", "Operation Flashpoint", "Arma" and "Poseidon" from the
  name, crate names, binary, window title and logo. Refer to the game only nominatively, e.g. "a mission editor for
  *Arma: Cold War Assault*", and add Bohemia's disclaimer. "OPERATION FLASHPOINT" is attributed to Electronic Arts;
  "ARMA" belongs to Bohemia. **[V]/[I]** (The name is Plotroom, [D002](../decisions/D002-name-and-naming-system.md);
  descriptor placement, clearance search and rename before the first release answered 2026-09-27 →
  [D034](../decisions/D034-descriptor-placement-and-names-delegation.md).)
- **Process:** DCO sign-off (`git commit -s`, as iron-curtain does), SPDX headers plus REUSE 3.3, a `Derived-From:`
  provenance tag on ported files, `license = "GPL-3.0-or-later"` in `[workspace.package]`, a modern-syntax
  `cargo-deny` allow-list and `cargo-about` notices in releases. **[V]/[I]** (DCO answered 2026-09-27 →
  [D032](../decisions/D032-contribution-terms-dco.md).)
- **Never copy Bohemia Community Wiki (BIKI) text** into the repo or a shipped RAG corpus. The wiki reportedly restricts
  its content to non-commercial use (unverified: the page returns HTTP 403). Even without that term, no GPL-compatible
  license for BIKI text is known, so copying is not allowed by default. Take command and format facts from the GPL
  source instead. **[U]** term / **[I]** rule

---

## 1. Glossary

| Term | Meaning |
|---|---|
| **CWR** | `BohemiaInteractive/CWR`: Bohemia's official, locked source release of *Arma: Cold War Assault Remastered* (engine codename **Poseidon**). The game was first released in 2001 as *Operation Flashpoint: Cold War Crisis* (OFP). |
| **CWR-CE** | `ofpisnotdead-com/CWR-CE`: the community continuation of CWR. It accepts PRs and uses the same license. |
| **GPL-3.0-or-later** | GNU GPL v3 "or any later version" (SPDX id). Copyleft: distributed derivative works must be GPL and ship with their source. |
| **§7 Additional Terms** | GPLv3 section 7 lets a licensor add *additional permissions* (removable by downstream) or a closed list of *non-permissive terms* (a)–(f), such as trademark and indemnity terms. Other added restrictions are "further restrictions" that recipients may remove. |
| **APL-SA** | *Arma Public License Share Alike*, Bohemia's content license: Attribution, NonCommercial, ArmaOnly, ShareAlike. |
| **ArmaOnly** | APL-SA term: "primarily intended for or directed towards the use in any of existing and future Arma games". |
| **Derivative work / port** | A translation of a program into another language. Legally this is an *adaptation*, which needs the copyright holder's permission (here: the GPL). |
| **Clean-room** | An implementation written only from specifications and observed behaviour, without copying protected expression. |
| **Aggregate** | GPLv3 §5: separate works placed on one medium that do not form a larger program. The GPL does not spread to the other parts. |
| **DCO** | Developer Certificate of Origin: a per-commit `Signed-off-by:` attestation, used instead of a CLA. |
| **REUSE / SPDX** | FSFE's spec for per-file machine-readable licensing (`SPDX-License-Identifier`, `LICENSES/`, `REUSE.toml`). |
| **HEMTT / armake2** | Community build tools written in Rust for Arma 3 (PBO, config and preprocessor handling). |
| **BIKI** | Bohemia Interactive Community Wiki (community.bistudio.com), which documents commands and formats. |

---

## 2. What upstream says (verified)

### 2.1 The license header and the §7 Additional Terms (verbatim)

The two repos have byte-identical `LICENSE` files (SHA-256 `AD3E819B…94D0CE`). The file is the GPLv3 text with a
header and a trailer. **[V]**

Header (`BohemiaInteractive/CWR@ffc61838b7:LICENSE#L1-L3`):

```
Bohemia Interactive has released ARMA: Cold War Assault Source Code 
under the GNU General Public License v3.0 or later below, with additional terms
per Section 7 thereof applied (see the bottom of this document).
```

Trailer (`BohemiaInteractive/CWR@ffc61838b7:LICENSE#L682-L721`), quoted exactly with line breaks preserved:

```
ADDITIONAL TERMS per Section 7 of GNU GPL

Any propagation or conveyance of this program must include this copyright 
notice and these terms.

No trademark or publicity rights are granted. This license does not grant you
any right, title or interest in "ARMA", any other Bohemia Interactive 
trademark, or "OPERATION FLASHPOINT" trademark. You may not distribute 
any modification of this program using any Bohemia Interactive trademark or 
"OPERATION FLASHPOINT" trademark. You may not claim any affiliation or association 
with Bohemia Interactive or its affiliates, representatives and employees.

You may not misrepresent the origins of this program; any modified versions of
the program must be marked as such and not identified as the original program.

If you convey this program (or any modifications thereof) and assume
contractual liability for the program to its recipients, you agree to
indemnify Bohemia Interactive for any liability that those contractual
assumptions impose on Bohemia Interactive, and any other liability arising 
from or related to your assumptions of liability.

The following disclaimer supplements the disclaimers in the Section 15 of GNU GPL:
TO THE MAXIMUM EXTENT PERMISSIBLE UNDER APPLICABLE LAW, THIS PROGRAM IS 
PROVIDED TO YOU "AS IS," WITHOUT WARRANTY OF ANY KIND, AND YOUR USE IS AT YOUR SOLE RISK. 
THE ENTIRE RISK OF SATISFACTORY QUALITY AND PERFORMANCE RESIDES WITH YOU. 
BOHEMIA INTERACTIVE DISCLAIMS ANY AND ALL EXPRESS, IMPLIED OR STATUTORY WARRANTIES, 
INCLUDING IMPLIED WARRANTIES OF MERCHANTABILITY, SATISFACTORY QUALITY, FITNESS FOR ANY PURPOSE, 
NONINFRINGEMENT OF THIRD PARTY RIGHTS, AND WARRANTIES (IF ANY) ARISING FROM A
COURSE OF DEALING, USAGE, OR TRADE PRACTICES. BOHEMIA INTERACTIVE DOES NOT WARRANT 
AGAINST INTERFERENCE WITH YOUR ENJOYMENT OF THE PROGRAM; THAT THE PROGRAM WILL 
MEET YOUR REQUIREMENTS; THAT OPERATION OF THE PROGRAM WILL BE UNINTERRUPTED OR 
ERROR-FREE, OR THAT THE PROGRAM WILL BE COMPATIBLE WITH THIRD PARTY SOFTWARE 
OR THAT ANY ERRORS IN THE PROGRAM WILL BE CORRECTED. NO ADVICE OR COMMUNICATION 
MADE BY BOHEMIA INTERACTIVE, ITS AFFILIATES, REPRESENTATIVES OR EMPLOYEES SHALL CREATE A 
WARRANTY. SOME JURISDICTIONS MAY NOT ALLOW THE EXCLUSION OF OR LIMITATIONS ON 
IMPLIED WARRANTIES OR THE LIMITATIONS ON THE APPLICABLE STATUTORY RIGHTS OF A 
CONSUMER, THEREFORE SOME OR ALL OF THE ABOVE EXCLUSIONS AND LIMITATIONS MAY NOT APPLY 
TO YOU.

[END OF ADDITIONAL TERMS]
```

No explicit `Copyright (C) … Bohemia` line exists anywhere in `LICENSE`. The only copyright line is the FSF's own, at
`#L9`. The "copyright notice" the terms refer to is therefore best read as the three-line header. **[V]** for the
absence, **[I]** for the reading. Engine sources carry **no SPDX or per-file license headers**. For example,
`engine/Poseidon/UI/Map/UIArcade.cpp#L1-L15` starts directly with `#include`s. **[V]**

### 2.2 README, CONTRIBUTING and credits

- The README splits the release into three parts, **code, name and data**
  (`BohemiaInteractive/CWR@ffc61838b7:README.md#L6-L18`). **[V]**
  - Code: "licensed under GPL-3.0-or-later with additional terms under Section 7 … provided it stays GPL".
  - Name: "'ARMA', 'Operation Flashpoint', and the logos are *not* granted … A fork must be renamed and must not present
    itself as 'Arma' or as an official Bohemia Interactive product."
  - Data: "Models, textures, sounds, missions, and voices … are not GPL; they ship separately under the APL-SA license.
    A free Demo is available on Steam."
- The trademark attribution reads: *"ARMA" is a registered trademark of BOHEMIA INTERACTIVE a.s. "OPERATION FLASHPOINT"
  is a registered trademark of Electronic Arts Inc.* (`README.md#L62-L64`, repeated in `CREDITS.md#L83-L85`). **[V]**
- `thirdparty/` (glad, the RenderDoc header, khrplatform) is excluded from the GPL. vcpkg and Cargo dependencies keep
  their own licenses (`README.md#L56-L60`, `THIRD_PARTY_NOTICES.md#L24-L25`, `#L537-L569`). **[V]**
- CWR's contribution rules say "source changes are governed by the same GPL-3.0-or-later terms, including the Section 7
  additional terms" and that modified versions "must be marked as modified"
  (`BohemiaInteractive/CWR@ffc61838b7:CONTRIBUTING.md#L41-L52`). **[V]**
- CWR-CE adds an inbound=outbound clause: "By contributing source changes here, you agree that your contribution is
  provided under the same GPL-3.0-or-later license terms, including the additional Section 7 terms"
  (`ofpisnotdead-com/CWR-CE@b67bf3bd62:CONTRIBUTING.md#L80-L87`). CWR-CE uses no DCO or CLA.
  It also bans AI co-author trailers (`#L59-L72`). **[V]**
- Bohemia points developers to CWR-CE as "the community release authors" (`CREDITS.md#L40-L41`,
  `CONTRIBUTING.md#L34-L39`). **[V]**
- CWR-CE is named *"Arma: Cold War Assault - Remastered - Community Edition"*
  (`ofpisnotdead-com/CWR-CE@b67bf3bd62:README.md#L1`), even though the same README says a fork "must be renamed"
  (`#L14`). **[V]** Bohemia appears to tolerate this for a project it endorses. That tolerance is **not** a license, and
  we should not rely on it. **[I]**

### 2.3 License anomalies to know about

- **The Rust crates in CWR declare `license = "MIT"`, but the repo LICENSE says the whole source is GPL.** This covers
  `engine/Trident/Cargo.toml#L6` and `mserver/{Archive,CLI,Client,MasterService}/Cargo.toml#L6`, the same in both repos.
  No per-crate LICENSE file exists, and `THIRD_PARTY_NOTICES.md#L568-L569` says "The project's own code remains under
  GPL-3.0-or-later". **[V]**
  - **Our stance:** treat Trident, including its harness protocol client and schema, as GPL-3.0-or-later. Under our
    GPL choice this ambiguity becomes harmless. It would block a permissive crate from reusing Trident code. **[I]**
- GitHub's license detector reports CWR and CWR-CE as `NOASSERTION` ("Other"), because the §7 text is appended to the
  GPL body (GitHub API, retrieved 2026-09-26). **[V]** Lesson: keep our `LICENSE` file as the pure GPL text and put the
  additional terms in a separate file (§10.1).
- CWR's fixture policy says fixtures must be authored or synthetic, "Do not copy assets from game packages, demo
  packages …" (`BohemiaInteractive/CWR@ffc61838b7:tests/fixtures/ASSET_SOURCES.md#L3-L6`). This matches our AGENTS.md
  rule. Because those fixtures are GPL, a GPL project may reuse them with attribution. **[V]/[I]**

### 2.4 Mapping Bohemia's terms onto GPLv3 §7

GPLv3 §7 allows only these non-permissive additions: (a) warranty and liability disclaimers, (b) preservation of legal
notices, (c) no misrepresentation of origin and marking of modifications, (d) limits on publicity use of names,
(e) "Declining to grant rights under trademark law", and (f) indemnification limited to liability that contractual
assumptions "directly impose". Anything else is a "further restriction" that a recipient "may remove"
(`LICENSE#L366-L401`). **[V]**

| Bohemia term (LICENSE line) | §7 basis | Assessment |
|---|---|---|
| Include "this copyright notice and these terms" (#L684-L685) | (b) | Permitted. **We comply.** |
| No trademark or publicity rights granted (#L687-L689) | (e), (d) | Permitted. |
| "You may not distribute any modification … using any Bohemia Interactive trademark or 'OPERATION FLASHPOINT' trademark" (#L689-L691) | (e)/(c) | This is a positive prohibition, which is broader than just "declining to grant". Arguably part of it is a removable further restriction. **[I]** We comply anyway, because it matches trademark law and Bohemia's rules. |
| No claim of affiliation (#L691-L692) | (c)/(d) | Permitted. |
| Mark modified versions; do not misrepresent origin (#L694-L695) | (c) | Permitted. It overlaps with GPL §5(a) (`#L219`). |
| Indemnify BI "… and any other liability arising from or related to your assumptions of liability" (#L697-L701) | (f) | The tail goes beyond (f)'s "directly impose" and is arguably removable. **[I]** Irrelevant in practice: we never assume contractual liability to users. |
| Supplementary warranty disclaimer (#L703-L719) | (a) | Permitted. |

**Conclusion.** We never need to argue that any of these terms is removable. Complying fully costs a NOTICE file, a
name without trademarks, a "modified" marking and no warranty promises. **[I]**

---

## 3. Game data: APL-SA, the Steam demo, and Bohemia's content rules

### 3.1 What the APL-SA says

Source: <https://www.bohemia.net/community/licenses/arma-public-license-share-alike>, which shows "Updated 21/08/2026".
Quotes are as retrieved. **[V]**

- Summary: "you are free to adapt (i.e. modify, rework or update) and share (i.e. copy, distribute or transmit) the
  material under the following conditions: Attribution, Noncommercial, Arma Only, Share Alike". Also: "You may not
  convert or adapt this material to be used in other games than Arma."
- §2(a)(1) grant: "a worldwide, royalty-free, non-sublicensable, non-exclusive, irrevocable license … to: reproduce and
  Share the Licensed Material, in whole or in part, for NonCommercial and ArmaOnly purposes only; and produce, reproduce,
  and Share Adapted Material for NonCommercial and ArmaOnly purposes only."
- Definitions:
  - **ArmaOnly** = "primarily intended for or directed towards the use in any of existing and future Arma games".
  - **NonCommercial** = "not primarily intended for or directed towards commercial advantage or monetary compensation".
  - **Share** = "provide material to the public by any means or process that requires permission under the Licensed
    Rights".
- Technical modifications are allowed ("in all media and formats … make technical modifications necessary to do so").
  "Patent and trademark rights are not licensed". ShareAlike: the adapter's license "must be this Public License, or an
  Arma Public Share Alike Compatible License". Attribution: retain creator identification and the copyright notice, and
  indicate the APL-SA license.
- The license terminates automatically on breach and is reinstated if the breach is cured within 30 days.
- The page does not call itself a Creative Commons derivative, although its structure closely mirrors CC BY-NC-SA 4.0.
  **[I]**

### 3.2 Which data is APL-SA: demo and full game

- **Full game** (Steam app 65790): the store text says the source is under "GNU GPL v3.0-or-later" and "Game data and
  assets remain under Bohemia's Arma Public License Share Alike (APL-SA)". Legal line: "© 2026 BOHEMIA INTERACTIVE a.s.
  ARMA® and BOHEMIA INTERACTIVE® are registered trademarks of BOHEMIA INTERACTIVE a.s." **[V]** (Steam appdetails API).
- **Free demo** (Steam app 4819000, released 22 Jun 2026): "An official asset pack. The demo doubles as a sanctioned
  asset pack for the Arma community. The bundled game data is provided as raw material you are free to study, modify and
  build new Arma content from." It also says users may "Use the bundled assets to create new missions, mods and content
  for Arma". **[V]**
- **No evidence was found that the demo data is licensed more permissively than APL-SA.** The Steam demo text does
  **not** name APL-SA and does not mention NonCommercial; it restates only the Arma-only and share idea ("adapt, remix
  and share work with the community") and defers to the GitHub repo. The APL-SA link comes from Bohemia's CWR README,
  which points both demo and full game data at APL-SA (`README.md#L66-L83`; same in CWR-CE `README.md#L109-L128`).
  **[V]** sources / **[I]** conclusion
- Unknown: whether pre-remaster retail data (original OFP/CWA 1.99 discs, older GOG builds) is also APL-SA, or only the
  remaster's data. **[U]**
- The CWR-CE build docs say the demo data works with the *full* game binary "to unlock usage of additional features
  (like the editor)" (`ofpisnotdead-com/CWR-CE@b67bf3bd62:docs/build/win.md#L11`). **[V]** A demo-only user could
  therefore use our editor too (see §3.4). **[I]**

### 3.3 Bohemia's "Game Content Usage Rules" (general, not a license)

Source: <https://www.bohemia.net/en/community/game-content-usage-rules>, "Updated: 21/08/2026". **[V]**

- "Do not redistribute our games or any files extracted from it, do not reverse engineer it, do not hack it, do not
  alter our games."
- "You may develop your own game content, tools, plug-ins and other utilities or services for both noncommercial and
  commercial use as long as it is your original creation, without using the content, tool or any other intellectual
  property of Bohemia Interactive."
- "You may use our trademarks and logos only as fair use. Anything you have created should not appear to be an official
  product of Bohemia Interactive." On logos: "No. Please create your own original logo." On domains: "We would prefer if
  you choose your own original name".
- Suggested disclaimer: "This website is not affiliated or authorized by Bohemia Interactive a.s. Bohemia Interactive,
  ARMA, DAYZ and all associated logos and designs are trademarks or registered trademarks of Bohemia Interactive a.s."
- Monetisation: donations are allowed only if access stays free and unrestricted.

**How the rules interact with the licenses.** For CWA the specific licenses govern: GPL for code, APL-SA for data.
Reading GPL-documented formats is not "reverse engineering". Our tool is "original creation" plus GPL-licensed code. It
reads data from the user's install and never incorporates it. **[I]** Bohemia has not confirmed this reading
(see Open questions). (How to ask, answered 2026-09-27 →
[D035](../decisions/D035-outreach-and-security-disclosure.md) item 2: one letter from the owner; not sent yet.)

### 3.4 Questions and answers for our editor

| Question | Answer | Status |
|---|---|---|
| May the editor **load** configs, `resource.bin`, fonts, PAA textures and WRP maps **from the user's install at runtime**? | **Yes.** It is use by a lawful owner, for an Arma game, non-commercially. APL-SA grants reproduction for NonCommercial + ArmaOnly purposes, and the GPL engine itself works the same way. | [I], high confidence |
| May it **cache** decoded data (rasterised map tiles, decoded textures) on the user's disk? | Yes, locally. This is a "technical modification necessary" for use. Never sync or upload caches. Add "clear cache", and redact game data from auto-generated bug reports. | [I] |
| May we **commit or bundle** BI icons, fonts, cursors, textures, `resource.cpp` layouts or stringtables in our repo or releases? | **No.** Bundling would push NC + ArmaOnly + ShareAlike terms into a GPL release, which conflicts with the GPL's freedom to sell and with our "synthetic fixtures only" rule. It also violates Bohemia's usage rule "do not redistribute … any files extracted". Ship our own fallback theme (see doc 05). | [V] rules / [I] conflict |
| May a **non-Bohemia product** (our editor) use APL-SA data? | Yes, if the use is for making content for an Arma game. **Do not** add features that export BI assets for other games or engines (APL-SA: "may not convert or adapt this material to be used in other games than Arma"). | [V] text / [I] application |
| Is the **free Steam demo** data licensed differently? | No evidence of that. Treat it as APL-SA. Whether the Steam Subscriber Agreement or a demo EULA restricts using demo data with third-party tools is unknown. | [V]/[U] |
| **Screenshots** of the editor showing BI textures or fonts in our README or website? | They reproduce APL-SA material. Keep them NonCommercial and Arma-related, and caption them "Contains game data © Bohemia Interactive a.s., used under APL-SA". Prefer screenshots in the fallback theme. | [I] |
| **Sending** game-data snippets (class names, stringtable lines) to a cloud LLM? | Probably not "Share", which the license defines as "to the public", but it does copy data to a third party. Default to minimal, derived facts; make it opt-in; never upload raw files. | [I] |
| **Training** a model on game texts, missions or stringtables? | Avoid. The weights might count as APL-SA "Adapted Material", making them NC and Arma-only under ShareAlike. Train only on our own synthetic data and permissively licensed datasets. | [U]/[I] |
| **CI** tests using game data? | No. Use synthetic fixtures only; CWR's GPL fixtures are acceptable with attribution. | [V] (`ASSET_SOURCES.md`) |

### 3.5 BIKI (wiki) content is non-commercial

- The BIKI reportedly states that its content "may only be for personal, non-commercial entertainment use only" and
  that derived works must "remain licensed non-commercial" (unverified). This came from a search snippet of
  <https://community.bistudio.com/wiki/Meta:General_disclaimer>; the page, its `action=raw` form and the MediaWiki API
  all returned HTTP 403 on 2026-09-26, so the wording could not be confirmed. **[U]** Whatever the exact term, no
  GPL-compatible license for BIKI text is known, so the rules below hold by default. **[I]**
- Non-commercial terms are incompatible with the GPL. **Do not paste BIKI prose** (command descriptions, format pages)
  into code comments, docs or a bundled RAG corpus. **[I]**
- Facts from BIKI (command names, arities, format fields) are not protected expression (see §4.2) and may be
  re-expressed in our own words. **[I]**
- Better source for the agent's command catalogue: the GPL engine source (command registration tables), plus our own
  wording. **[I]**

---

## 4. Is our Rust code a derivative work of CWR?

### 4.1 Translating C++ to Rust

- EU Software Directive 2009/24/EC Art. 4(1)(b) reserves to the rightholder "The translation, adaptation, arrangement
  and any other alteration of a computer program". **[V]** (<https://eur-lex.europa.eu/eli/dir/2009/24/oj/eng>)
- GPLv3 defines "modify" as copying from or adapting "all or part of the work in a fashion requiring copyright
  permission" (`LICENSE` §0). **[V]**
- Therefore: **porting `UIArcade*.cpp`, `UIMap*.cpp`, `ArcadeTemplate*` or the ParamFile parser function-by-function
  into Rust creates a work based on CWR.** Distributing it requires GPL-3.0(-or-later) plus Bohemia's §7 terms. **[I]**,
  consensus reading.
- **Do we have to carry the §7 terms?** Yes, for the CWR-derived material. The terms demand it (#L684-L685). GPLv3 lets
  a recipient strip only *additional permissions* (#L359-L361) and *further restrictions* (#L393-L397). §7(a)–(f) terms
  that are properly added travel with the material. **[V]/[I]**
- Our distributed binary contains ported code, so every distribution of the program (source or binary) must include
  the NOTICE with those terms. **[I]**

### 4.2 What stays free: facts, formats, interfaces

- Art. 1(2) of the same Directive: "Ideas and principles which underlie any element of a computer program, including
  those which underlie its interfaces, are not protected by copyright under this Directive". **[V]**
- CJEU *SAS Institute v WPL* (C-406/10, 2 May 2012): "neither the functionality of a computer program nor the
  programming language and the format of data files used in a computer program … constitute a form of expression of
  that program". **[V]** (EUR-Lex 62010CJ0406, operative part point 1.) The ruling interprets Directive 91/250/EEC,
  which 2009/24/EC codified. WPL had no access to SAS's source code, a fact that does not hold for us (see below).
- Therefore **file layouts, enum values, field names, protocol messages and observed behaviour are free facts**.
  Examples: the `mission.sqm` grammar, `RscDisplayArcade*` field semantics, the harness JSON schema. Re-expressing them
  in new code is not porting. **[I]**
- **The practical catch.** Our contributors (and LLM agents) will read CWR constantly, because it is the ground truth.
  Line-by-line "translation while looking" is porting, not clean-room. A credible permissive clean-room claim needs a
  discipline that is hard to keep in this project. That is why the default in §6 is GPL for everything that touches
  CWR knowledge. **[I]**

### 4.3 Why "-or-later" and not "-only"

- CWR grants "v3.0 or later" (#L1-L3, §14 at #L577-L579). **[V]**
- We *could* narrow our distribution to v3-only. Doing so would stop CWR-CE, which is "or later", from taking our code
  without also narrowing. It also gains nothing concrete. Match upstream: **`GPL-3.0-or-later`**. **[I]**

---

## 5. Options compared

| Option | Can include ported CWR code? | Community fit | Rust-ecosystem reuse of our crates | Admin cost | Verdict |
|---|---|---|---|---|---|
| **GPL-3.0-or-later** (match upstream) | **Yes** | Same as CWR and CWR-CE. Arma tooling is copyleft (§7.2). | Reusable only by GPL-3-compatible projects. **Not** usable by GPL-2.0-only HEMTT. | **Lowest**: one license, no provenance split | **Recommended default** |
| GPL-3.0-only | Yes (narrowed) | Slight friction with CWR-CE ("or later") | Same as above | Low | No benefit |
| AGPL-3.0-or-later | Only by combining under GPLv3 §13 (#L557); the CWR parts stay GPL | Unusual for desktop tools | Worse | Medium (network clause) | Reject. Revisit only for a hosted agent service. |
| MPL-2.0 | **No**: GPL code cannot be relicensed to MPL | Neutral | Good (file-level copyleft) | Medium | Reject for the app |
| MIT OR Apache-2.0 (Rust norm) | **No** | Welcome in Rust, unusual in Arma tooling | Best | High: strict clean-room discipline, and no reading CWR while coding | Reject for the app. Use only for isolated generic crates. |
| **Split**: GPL app + permissive generic crates | App: yes. Permissive crates: no. | Good (iron-curtain precedent) | Best for the generic parts | Medium: provenance tags, two deny configs, per-crate CONTRIBUTING rules | **Adopt narrowly** (harness core only; see §6) |

Practical costs of a split, based on iron-curtain experience (`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`):

- *D051 GPL decision:* `src/decisions/09c/D051-gpl-license.md#L112-L127`.
- *D076 separate permissive repos:* `src/decisions/09a/D076-standalone-crates.md#L12`, `#L27-L48`.

The costs:

1. Contributors must know which crate they are in. Mitigations: a per-crate license in CODE-INDEX.md and CODEOWNERS
   gates.
2. Nothing CWR-derived may ever land in a permissive crate. Enforce it with CI (§10.4).
3. Two `cargo-deny` policies are needed.
4. Relicensing later is impractical. D051 notes relicensing needs "consent from all copyright holders under the DCO"
   (`#L81-L84`). **[V]**

---

## 6. Recommendation

**6.1 Main workspace: `GPL-3.0-or-later`, carrying Bohemia's §7 terms.** Rationale:

- Porting the original editor's behaviour is the fastest route to "visually accurate and similar to the original". The
  GPL is the only license that permits it. **[I]**
- It matches CWR and CWR-CE exactly, so fixes can flow both ways. We can also reuse CWR's GPL test fixtures and treat
  Trident's ambiguous MIT/GPL metadata as GPL without worrying. **[V]/[I]**
- The Arma and OFP tooling community is copyleft by habit (§7.2). Bohemia's own README frames the release as "provided
  it stays GPL". **[V]**
- One license means no provenance bookkeeping inside the main workspace, and it is the simplest option for LLM coding
  agents to follow. **[I]**

**6.2 Our own §7 additional permission for editor output** (draft, to be reviewed; put it in `NOTICE`; answered
2026-09-27 → [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 1: this draft with
"Plotroom" filled in, plus an explicit coverage list, with a legal review before 1.0):

```
Additional permission under GNU GPL version 3 section 7 (Generated Content Exception):
Mission files (e.g. mission.sqm), scripts (SQS/SQF), description.ext, stringtables, briefings
and other content that this program writes on behalf of its user -- including any portions of
this program's built-in templates, snippets and examples that are copied into such output --
may be used, modified and distributed under terms of the user's choice. This permission does
not apply to the program itself, and covers only material whose copyright holders have
granted it (see CONTRIBUTING.md). Material derived from Bohemia Interactive's CWR source is
excluded unless Bohemia Interactive grants the same permission.
```

- *Why:* without it, a mission that embeds our GPL template scripts could itself arguably be GPL-bound. That would
  scare mission makers, who often mix in APL-SA content. **[I]**
- *Precedents:* GCC and Bison exceptions; iron-curtain's modding permission
  (`iron-curtain-engine/iron-curtain@7b7fac7fa5:LICENSE#L1-L16`). **[V]**
- *Constraints:*
  - Templates must be **original**, not ported from CWR, since we cannot grant permissions over Bohemia's code.
  - CONTRIBUTING must say contributions are licensed "GPL-3.0-or-later including the project's §7 additional
    permissions". **[I]** (Adopted 2026-09-27 → [D032](../decisions/D032-contribution-terms-dco.md) item 2.)
- Separately, plain program output is not covered by the GPL unless it contains program code. The permission removes
  the remaining doubt. **[I]**

**6.3 Permissive lane: narrow, decided now.**

- Candidate: the **generic harness core**, meaning provider adapters, the tool-call loop, effort levels, workflow engine
  and budget/guard logic, with **no** game types and **no** CWR-derived code. It could be `MIT OR Apache-2.0` in a
  separate repo (preferred, as iron-curtain D076 does) or in an isolated in-repo crate. It would be reusable in other
  Rust projects, such as iron-curtain. **[I]**
- **Format, editor, preview and game-knowledge crates stay GPL.** A clean-room permissive format crate should be created
  only when a concrete external consumer needs it. HEMTT is the example: it is GPL-2.0-only and could never consume our
  GPL-3 crates. Such a crate must be written from specifications and tests, with no CWR code open. **[I]**
- If the owner prefers zero overhead, drop the lane: everything GPL is legally fine. The only cost is that others cannot
  reuse the harness under MIT. **[I]**

*Superseded by [D001](../decisions/D001-licence-gpl-3-or-later.md) (owner, 2026-09-26; noted 2026-09-27): the owner
dropped the lane, so there is no permissive crate, and the plugin SDK, WIT files and test kit are GPL-3.0-or-later too
([D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 3). The permissive-lane parts of §5,
§10.1, §10.3–§10.5 and §11 step 6 lapse with it.*

**6.4 Docs.** Prose under `docs/` may use `CC-BY-SA-4.0`, as iron-curtain's design docs do
(`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:LICENSE-DOCS#L1-L7`; the code repo has no LICENSE-DOCS).

- CC declared BY-SA 4.0 one-way compatible with GPLv3 on 2015-10-08, so docs text can flow into GPL code
  (<https://creativecommons.org/share-your-work/licensing-considerations/compatible-licenses/>). **[V]**
- Quoted CWR code and license text keep their own licenses: mark them, or keep quotes short. **[I]**
- Alternative: keep docs GPL too, for a single license everywhere.

*Superseded by [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 2 (2026-09-27,
OWQ-02 (a)): docs are `GPL-3.0-or-later`, the alternative above; quoted third-party text still keeps its own licence.*

---

## 7. Dependencies and community norms

### 7.1 Compatibility with a GPL-3.0-or-later binary

| License | Into GPL-3.0? | Source / note |
|---|---|---|
| MIT, MIT-0, BSD-2/3-Clause, ISC, Zlib, 0BSD, BSL-1.0, CC0-1.0, Unlicense, Unicode-3.0 / DFS-2016 | Yes | Standard FSF listing. The listing page (gnu.org) was unreachable during this session. **[I]** high confidence |
| Apache-2.0 (also `WITH LLVM-exception`) | **Yes, one-way**. Not compatible with GPL-2.0. | ASF: "Apache 2 software can therefore be included in GPLv3 projects" (<https://www.apache.org/licenses/GPL-compatibility.html>). **[V]** |
| MPL-2.0 | Yes, unless marked "Incompatible With Secondary Licenses" | Mozilla MPL 2.0 FAQ Q14. **[V]** |
| LGPL-2.1-or-later / LGPL-3.0 | Yes | **[I]** |
| GPL-2.0-**or-later** | Yes (use it under v3) | **[I]** |
| GPL-2.0-**only** | **No** | FSF: "GPLv2 is, by itself, not compatible with GPLv3" (license-list, via search; gnu.org unreachable, quote not re-fetched). **[I]** high confidence |
| AGPL-3.0 | Combinable (§13), but deny by policy | `LICENSE#L557`. **[V]** |
| CC-BY-NC-*, APL/APL-SA, BIKI terms, SSPL, BUSL, "non-standard" | No | NC or field-of-use restrictions. **[I]** |

Real candidates, checked 2026-09-26:

| Candidate | License | Verdict |
|---|---|---|
| **HEMTT** crates, e.g. `hemtt-pbo` (monorepo `libs/*`) | `license = "GPL-2.0"` in `libs/pbo/Cargo.toml`. LICENSE is plain GPLv2 with no "or later" notice. crates.io: `hemtt-pbo` 1.0.0, 2023. **[V]** | Treat as **GPL-2.0-only**; the SPDX id `GPL-2.0` is deprecated and equals `-only`. (GPLv2 §9's "any version" option applies only when no version is specified; the metadata names v2, so do not rely on it.) **Cannot be linked.** Invoking the `hemtt` CLI as a separate process is aggregation. [I] Could ask upstream for "or later". |
| **armake2** | `GPL-2.0-or-later` (Cargo.toml, crates.io 0.3.0, updated 2018-12-22) **[V]** | Compatible, but stale. Use as reference or a fork only. |
| CWR **Trident** / mserver crates | Metadata MIT, repo GPL-3.0+ (§2.3) **[V]** | Compatible either way; treat as GPL. |
| `ring` ≥ 0.17.10 | `Apache-2.0 AND ISC` (≤ 0.17.9 was "non-standard") **[V]** | OK. Pin ≥ 0.17.10. |
| `aws-lc-sys` 0.45 | Multi-license expression (ISC, Apache-2.0, MIT, BSD-3-Clause, MIT-0 …) **[V]** | Probably OK. Confirm with cargo-deny. |
| `llama-cpp-2` 0.1.157, `candle-core` 0.11 | `MIT OR Apache-2.0` **[V]** | OK (local inference). |
| rig, pi, opencode, tinyagent, deepseek-harness | MIT (repo LICENSE at pinned commits) **[V]** | OK to depend on or borrow code. Keep MIT notices. |
| openai/codex, headroom | Apache-2.0 plus a `NOTICE` file **[V]** | OK. Borrowed code must carry their NOTICE content (Apache §4(d)). |
| Wine "Tahoma" fonts (metric-compatible fallback) | LGPL **[V]** (Wikipedia *Tahoma (typeface)*; Fedora `wine-tahoma-fonts`) | OK as a bundled fallback font. SIL OFL fonts are also fine as separate font files. [I] |

### 7.2 What the community uses

| Project | License | Source |
|---|---|---|
| BohemiaInteractive/CWR, CWR-CE | GPL-3.0-or-later + §7 terms | §2 **[V]** |
| HEMTT (Arma 3 build system, active 2026-09) | GPL-2.0 (treated as only) | GitHub API + Cargo metadata **[V]** |
| armake2 | GPL-2.0-or-later | Cargo.toml **[V]** |
| ACE3 | GPL-2.0-**or-later**, plus a `.pbo` redistribution exception and a "name must not look official" clause. Some folders are APL / CC. | `acemod/ACE3` LICENSE preamble **[V]** |
| CBA_A3 | GPLv2 text (GitHub: GPL-2.0; no "or later" notice found) | **[V]** |
| ofpisnotdead-com org | Mostly **no license**. `rust-pbo-wasm` is MIT. | GitHub org API **[V]** |
| Bohemia content and tools | APL / APL-SA / APL-ND for content; "BI's Tools End User License" (personal, non-commercial) | <https://www.bohemia.net/community/licenses> **[V]** |
| iron-curtain (same owner) | GPL-3.0 + §7 modding permission, DCO; standalone crates `MIT OR Apache-2.0`; docs CC-BY-SA-4.0 | `LICENSE#L1-L16`, `CONTRIBUTING.md#L91-L100` **[V]** |

The community uses copyleft for engine and mod code (GPL-2/3). Rust Arma tooling (HEMTT, armake2) is GPL-2. The
permissive exceptions are small utilities. **GPL-3.0-or-later is squarely within norms.** **[I]**

---

## 8. Model weights and the AI harness

**Aggregation, not derivation.** Our GPL program loads a weights file as data at runtime, through llama.cpp or candle.
The weights are not "combined … such as to form a larger program". Shipping or downloading them next to the binary is an
"aggregate" (GPLv3 §5, `LICENSE#L240-L248`). **[V]** text, **[I]** application. Consequences:

- The GPL does not reach the weights, and the weights' license does not reach our code.
- A weights license *with use restrictions* makes the bundle non-free and forces pass-through obligations on us as
  redistributor. Do not embed weights with `include_bytes!`; keep them as separate files. **[I]**

| Family (example checked) | Weights license | Redistribution obligations | Our policy |
|---|---|---|---|
| Qwen3.6 (`Qwen/Qwen3.6-35B-A3B`, 2026-04) | Apache-2.0, ungated **[V]** (HF API). An HF search of the Qwen org (2026-09-26) found only 27B and 35B-A3B checkpoints (plus FP8), all Apache-2.0, and no smaller Qwen3.6 model. | License copy; any NOTICE; state changes (quantisation counts as a modification) | Default-download OK |
| Gemma 4 (`google/gemma-4-E4B-it`, 2026) | Apache-2.0 **[V]** (Google OSS blog 2026-04-02, HF API). Google's docs also link a Prohibited Use Policy; whether it binds Gemma 4 is unknown **[U]**. | As Apache-2.0 | Default-download OK, with caveat |
| Gemma ≤ 3 / 3n | Gemma Terms of Use (modified 2026-04-01; excludes Gemma 4) **[V]** | Must include the use restrictions "as an enforceable provision in any agreement", give a copy of the terms, and ship a Notice: "Gemma is provided under and subject to the Gemma Terms of Use found at ai.google.dev/gemma/terms" **[V]** | Bring-your-own only |
| Llama 3.2 (`meta-llama/Llama-3.2-3B-Instruct`, gated) | Llama 3.2 Community License **[V]** | Copy of the agreement; display "Built with Llama"; Notice "Llama 3.2 is licensed under the Llama 3.2 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved."; comply with the Acceptable Use Policy; 700M-MAU clause **[V]** | Bring-your-own only |
| Phi-4-mini-instruct | MIT, ungated **[V]** | Keep the notice | Default-download OK |
| SmolLM3-3B | Apache-2.0 **[V]** | As Apache-2.0 | Default-download OK |
| gpt-oss-20b | Apache-2.0 **[V]** | As Apache-2.0 | OK (large) |
| LiquidAI LFM2.5 (`LiquidAI/LFM2.5-1.2B-Instruct`) | LFM Open License v1.0 (`lfm1.0`, custom), ungated. Commercial use is not licensed for entities with annual revenue of US$10M or more. **[V]** (HF API, model `LICENSE`) | License copy; mark modified files; keep notices **[V]** | Bring-your-own only |
| Cloud APIs (OpenAI, Anthropic, DeepSeek …) | Provider terms; the user brings their own key | None for our code | Provider-specific output terms **[U]** |

*Superseded in part by [D037](../decisions/D037-model-manager-recommended-list.md) (2026-09-27, OWQ-19 (a)): "Default-download
OK" now marks a candidate only; the recommended list also needs Plotroom's qualification, and a model whose use policy may be
a binding field-of-use limit (the Gemma 4 caveat) is not recommended until that is resolved.*

**Rules for the harness.**

1. The release archive contains **no weights**.
2. First-run download fetches from the rightsholder's host, pinned by hash, with the license shown and explicitly
   accepted.
3. The default list contains OSI licenses only. (Answered 2026-09-27 →
   [D037](../decisions/D037-model-manager-recommended-list.md) item 1: OSI licences with no field-of-use restriction,
   and only models that passed Plotroom's qualification.)
4. Anything under custom terms is "bring your own path/URL". (Answered 2026-09-27 → D037 item 2: everything else,
   including any Hugging Face file the user names, installs as "custom" with its licence and use policy shown, an
   explicit acceptance, and an "unqualified" badge until qualified.)
5. A project fine-tuned model inherits its base's license. Train only on data we can license (§3.4). Publish the data
   provenance manifest, with every dataset pinned by hash. **[I]**

**Generated content.** The US Copyright Office concluded that "purely AI-generated material" from prompts is not
copyrightable (Part 2 report, published 2025-01-29). **[V]** date; the exact quote was not re-read, since the PDF could
not be parsed (unverified). Dialogue and briefings the agent writes may therefore be unowned unless a
human edits them. That matters to authors, not to our license. The Generated Content Exception (§6.2) covers our
templates. **[I]** (Its coverage list, answered 2026-09-27 →
[D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 1, also names AI-written text.)

---

## 9. Trademarks and naming

**Owners.**

- **"ARMA" is a registered trademark of BOHEMIA INTERACTIVE a.s.** (Steam legal notice; CWR README). **[V]**
- **"OPERATION FLASHPOINT" is attributed by Bohemia to Electronic Arts Inc.** (`README.md#L62`). **[V]** This is
  consistent with the history:
  - Codemasters kept the OFP name when Bohemia split from it (Wikipedia, *Operation Flashpoint: Cold War Crisis*).
    **[V]**
  - EA completed its acquisition of Codemasters on 18 Feb 2021 (EA 8-K). **[V]**
  - Unverified: whether the registry lists EA or a Codemasters subsidiary as holder, and the registration's status in
    each jurisdiction. **[U]**

**What binds us.**

1. Bohemia's §7 terms (quoted in §2.1): no trademark rights; do not distribute a modification "using" BI or OFP marks;
   no affiliation claims. Read literally, "using" could cover any mention inside the distributed program, not only its
   name. Bohemia's README frames the rule as naming ("A fork must be renamed"). So keep in-program mentions to the
   disclaimer and plain compatibility text. **[I]**
2. Bohemia's usage rules: fair use only, not "official"-looking, no logos, prefer original names.
3. Ordinary trademark law. Referential use to indicate a product's intended purpose is generally allowed:
   US "nominative fair use", and EUTMR Art. 14(1)(c). **[I]**, not re-verified this session.

**The repo name `ofp-editor`.**

- "OFP" is the universal abbreviation of the EA mark. A product literally called "OFP Editor" is the textbook
  "distribute a modification … using … 'OPERATION FLASHPOINT' trademark". **[I]**
- Community sites have used "OFP" for decades (OFPEC, ofpisnotdead.com) without known enforcement. **[U]** That
  tolerance is not a license, and our GPL distribution is contractually bound by the §7 term.
- **Rename before the first release.** GitHub keeps redirects after a rename. (Answered 2026-09-27 →
  [D034](../decisions/D034-descriptor-placement-and-names-delegation.md) item 2; not done yet.)

**Naming checklist.**

1. The product, repo, crate names, binary, window title, installer and icon contain none of: `Arma`, `ARMA`,
   `OFP`, `Flashpoint`, `Cold War Assault`, `Cold War Crisis`, `Poseidon` (BI's engine codename), `Bohemia`/`BI`, or
   BI island names such as `Everon`, `Malden`, `Kolgujev` and `Nogova` (their status is unknown; avoid them).
   (Adopted 2026-09-27 → [D034](../decisions/D034-descriptor-placement-and-names-delegation.md) item 1: the descriptor
   is kept out of the window title, installer, icon, repository, crate and binary names.)
2. Run a clearance search: USPTO, EUIPO, WIPO Global Brand DB, crates.io, GitHub, Steam and ModDB. (Answered
   2026-09-27 → D034 item 2: recorded here for Plotroom, Wilco, Plotline, the Tote and Teller before the first
   release; not done yet. Later user-facing names clear this checklist too, item 3.)
3. Use an original logo and original UI chrome for the product identity. BI fonts, cursors and textures appear only
   when loaded at runtime from the install.
4. **Nominative use is fine in body text:** "a standalone mission editor for *Arma: Cold War Assault* (originally
   released as *Operation Flashpoint: Cold War Crisis*)", and a button "Preview in game". Use plain text, not
   stylised marks. **[I]**
5. Do not claim "official", "remastered", "endorsed" or "by Bohemia".

Example names are **unchecked**; they only illustrate the style: *Sitrep*, *Fireteam Studio*, *Waypoint Studio*.
(The name is now Plotroom: [D002](../decisions/D002-name-and-naming-system.md).)

**Disclaimer.** Put it in the README footer, the About box and the website (placement answered 2026-09-27 →
[D034](../decisions/D034-descriptor-placement-and-names-delegation.md) item 1; `<Product>` reads "Plotroom", item 2):

```
<Product> is an independent, community-made tool. It is not affiliated with, endorsed by, or
authorized by Bohemia Interactive a.s. or Electronic Arts Inc. ARMA and Bohemia Interactive are
trademarks or registered trademarks of Bohemia Interactive a.s. OPERATION FLASHPOINT is a
registered trademark of Electronic Arts Inc. These names are used only to identify the game this
tool is designed to work with. <Product> contains code derived from the Arma: Cold War Assault
source code released by Bohemia Interactive under GPL-3.0-or-later with additional terms; this is
a modified version and is not the original program. Game data is not included and is licensed by
Bohemia Interactive under the APL-SA.
```

---

## 10. Compliance mechanics

### 10.1 Files at the repo root

| File | Content |
|---|---|
| `LICENSE` | The **unmodified** GPLv3 text, so GitHub and crates tooling detect "GPL-3.0". |
| `NOTICE` | Project copyright; "SPDX: GPL-3.0-or-later"; the Generated Content Exception (§6.2); **Bohemia's header and Additional Terms verbatim** (`LICENSE#L1-L3`, `#L682-L721`), with a scope note ("apply to this program, which contains material derived from BohemiaInteractive/CWR"); the trademark disclaimer (§9). (The exception's wording, answered 2026-09-27 → [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 1: the §6.2 draft plus an explicit coverage list.) |
| `LICENSES/` (REUSE) | `GPL-3.0-or-later.txt`, `CC-BY-SA-4.0.txt` (docs), `LicenseRef-CWR-Section7-Terms.txt` (the BI terms), and `MIT.txt` + `Apache-2.0.txt` if the permissive lane exists. *Superseded in part 2026-09-27: no `CC-BY-SA-4.0.txt`, because docs are GPL-3.0-or-later ([D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 2), and no `MIT.txt` or `Apache-2.0.txt`, because there is no permissive lane ([D001](../decisions/D001-licence-gpl-3-or-later.md)) and the plugin SDK is GPL too (D031 item 3).* |
| `THIRD_PARTY_NOTICES` | Generated per release by `cargo about generate`, as CWR itself recommends (`THIRD_PARTY_NOTICES.md#L548-L553`). **[V]** |
| `CONTRIBUTING.md` | DCO, inbound=outbound per crate, provenance rules, AI-assistance policy. (Answered 2026-09-27 → [D032](../decisions/D032-contribution-terms-dco.md): DCO and no CLA; one inbound = outbound licence, GPL-3.0-or-later with the §7 permissions, not per crate; AI assistance allowed with a human sign-off and an optional `Assisted-by:` trailer.) |

### 10.2 Headers (SPDX + REUSE 3.3)

REUSE 3.3 (2024-11-14) wants `SPDX-FileCopyrightText` and `SPDX-License-Identifier` in every file. Files that cannot
hold a comment get `.license` sidecars or entries in `REUSE.toml`. `.reuse/dep5` is deprecated.
**[V]** (<https://reuse.software/spec-3.3/>)

```rust
// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 <Product> contributors
// Additional permissions under GPLv3 section 7 apply; see NOTICE.
```

The last line is needed because we add our own §7 permission (§6.2). Whoever adds §7 terms must put a statement or a
pointer "in the relevant source files" (#L403-L406). **[V]** text / **[I]** application.

(Answered 2026-09-27: `<Product>` reads "Plotroom" in these headers,
[D034](../decisions/D034-descriptor-placement-and-names-delegation.md) item 2; files under `docs/` carry
`GPL-3.0-or-later` headers too, [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 2.)

Ported file, which also carries the §5(b) notice that the work is under the GPL "and any conditions added under
section 7" (#L222-L225) and a modification date (GPL §5(a), #L219):

```rust
// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 <Product> contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp
// Modified: translated to Rust and changed, 2026-MM-DD. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
```

`Derived-From:` is our own tag, not SPDX. CI greps for it (§10.4). SPDX has no listed identifier for Bohemia's terms.
A `WITH AdditionRef-…` expression is possible in newer SPDX versions, but REUSE and cargo support for it is unverified
**[U]**. Keep the file-level id plain `GPL-3.0-or-later` and point to NOTICE. **[I]**

### 10.3 Cargo metadata and cargo-deny

```toml
# Cargo.toml (workspace root)
[workspace.package]
license = "GPL-3.0-or-later"      # SPDX 2.3 expression; `/` separator is deprecated
# members: `license.workspace = true`; app crates also `publish = false`
# permissive-lane crate only: license = "MIT OR Apache-2.0"
```

Cargo docs: crates.io reads `license` as an SPDX 2.3 expression (license list 3.20). `license-file` is for non-standard
licenses. **[V]** (<https://doc.rust-lang.org/cargo/reference/manifest.html>)

```toml
# deny.toml -- GPL workspace policy (current cargo-deny syntax)
[licenses]
confidence-threshold = 0.9
allow = [
  "GPL-3.0-or-later", "GPL-2.0-or-later", "LGPL-2.1-or-later", "LGPL-3.0-or-later", "MPL-2.0",
  "Apache-2.0", "Apache-2.0 WITH LLVM-exception", "MIT", "MIT-0", "BSD-2-Clause", "BSD-3-Clause",
  "ISC", "Zlib", "0BSD", "BSL-1.0", "CC0-1.0", "Unlicense", "Unicode-3.0", "Unicode-DFS-2016",
]
# Not allowed: GPL-2.0-only / "GPL-2.0", AGPL-*, SSPL-1.0, BUSL-1.1, CC-BY-NC-*, OpenSSL, unreviewed LicenseRef-*
exceptions = []   # per-crate additions only after review, with a comment
[licenses.private]
ignore = false    # also check our own crates' declared licenses
```

- The current cargo-deny docs list `unlicensed`, `deny`, `copyleft`, `allow-osi-fsf-free` and `default` as **removed**
  keys. **[V]** (<https://embarkstudios.github.io/cargo-deny/checks/licenses/cfg.html>)
- iron-curtain's `deny.toml` still uses `unlicensed` and `copyleft`, and the deprecated id `"GPL-3.0"`
  (`iron-curtain-engine/iron-curtain@7b7fac7fa5:deny.toml#L8-L25`). **[V]** Do not copy it verbatim.
- A permissive-lane crate is checked with a second config (`deny-permissive.toml`) whose allow-list contains **no
  copyleft**. Run it via `cargo deny --manifest-path <crate>/Cargo.toml --config deny-permissive.toml check licenses`.
  `--config` and `--manifest-path` are top-level options that go *before* the `check` subcommand; `check` itself has
  no `--config` flag. **[V]** (cargo-deny docs `cli/common`; `src/cargo-deny/check.rs` and `main.rs` on `main`,
  2026-09-26)

### 10.4 Provenance and CI gates

1. PR template checkbox: "Contains code translated or copied from CWR / CWR-CE? If yes: `Derived-From:` header added."
2. CI check: no file with `Derived-From: BohemiaInteractive/CWR` or `ofpisnotdead-com/CWR-CE` inside a
   permissive-licensed crate, and permissive crates may not depend on GPL workspace crates.
3. CI check: no files with game-data extensions (`.pbo`, `.paa`, `.pac`, `.p3d`, `.wrp`, `.bin` configs, `.fxy`)
   outside approved synthetic-fixture folders. Every fixture needs a REUSE entry that states its origin.
4. `reuse lint` and `cargo deny check licenses` in CI. CODE-INDEX.md lists each crate's license.

### 10.5 Contributions: DCO rather than a CLA

- **DCO 1.1** (<https://developercertificate.org/>, `git commit -s`, enforced by the DCO GitHub App or a CI check).
  iron-curtain already uses it (`CONTRIBUTING.md#L91-L100`). **[V]** It is lightweight and community-friendly.
  (Answered 2026-09-27 → [D032](../decisions/D032-contribution-terms-dco.md) item 1: DCO 1.1, no CLA.)
- A **CLA** would buy relicensing flexibility we cannot use anyway, because CWR-derived code is locked to GPL. It would
  also deter the community. **[I]**
- **Inbound = outbound**, per crate: GPL-3.0-or-later including the project's §7 additional permissions, or
  `MIT OR Apache-2.0` for the permissive lane. This follows CWR-CE's model (`CONTRIBUTING.md#L85-L87`). **[V]**
  *Superseded in part 2026-09-27: one licence for every contribution, `GPL-3.0-or-later` including the §7
  permissions ([D032](../decisions/D032-contribution-terms-dco.md) item 2), because there is no permissive lane
  ([D001](../decisions/D001-licence-gpl-3-or-later.md)).*
- **AI-assisted work:** the human contributor signs off and is responsible for provenance. Agents never sign off for a
  human. Whether to require an `Assisted-by:` trailer, or to forbid AI trailers as CWR-CE does, is a policy choice
  (Open questions). (Answered 2026-09-27 → D032 items 3–4: AI assistance is allowed, the human signs off, and the
  `Assisted-by:` trailer is optional, neither required nor forbidden.)

### 10.6 Binary releases (GPL §4–6)

- Each release attaches a source archive or tag link: §6(d), equivalent access from the same place.
- Ship `LICENSE`, `NOTICE` and `THIRD_PARTY_NOTICES` inside the archive.
- The About dialog shows the "Appropriate Legal Notices": copyright, no warranty, license and source link, Bohemia's
  terms and the trademark disclaimer. GPLv3 §5(d) asks for this in interactive UIs (#L235-L238). **[V]** However,
  §5(d) also says a work "need not" add them if the original Program's UIs do not show them. CWR's engine C++ contains
  no GPL or warranty strings, so this is best practice rather than a strict duty. **[I]**
- The window title and About box say the program is a modified, independent work, never "Arma" (§7(c)).

---

## 11. Concrete steps (in order)

1. Pick a new product name (§9 checklist, clearance search) and rename the GitHub repo. (The name is Plotroom,
   [D002](../decisions/D002-name-and-naming-system.md); clearance search and rename before the first release, answered
   2026-09-27 → [D034](../decisions/D034-descriptor-placement-and-names-delegation.md) item 2; not done yet.)
2. Add `LICENSE` (pure GPLv3), `NOTICE` (BI terms verbatim + §6.2 exception + disclaimer), `LICENSES/` and `REUSE.toml`.
   (The §6.2 wording with its coverage list: answered 2026-09-27 →
   [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 1.)
3. Set `[workspace.package] license = "GPL-3.0-or-later"`, and `publish = false` on app crates.
4. Add `deny.toml` (§10.3), `reuse lint` and the provenance and game-data gates (§10.4) to CI from the first commit.
5. Write `CONTRIBUTING.md`: DCO, per-crate inbound=outbound, `Derived-From:` rule, "never commit game data or BIKI
   text", AI policy. (Answered 2026-09-27 → [D032](../decisions/D032-contribution-terms-dco.md): one inbound =
   outbound licence, not per crate; `Assisted-by:` optional.)
6. Decide the permissive lane **before** any harness code lands. If yes: separate repo `MIT OR Apache-2.0` with its own
   deny config. (Decided 2026-09-26 → [D001](../decisions/D001-licence-gpl-3-or-later.md): no permissive lane.)
7. Build a model registry with license metadata and a license-acceptance UI. Default list: OSI licenses only.
   (Answered 2026-09-27 → [D037](../decisions/D037-model-manager-recommended-list.md): OSI licences with no
   field-of-use restriction, and qualified; everything else "custom".)
8. Email Bohemia (and optionally EA) with our name, disclaimer and data policy. Ask for written comfort on nominative use
   and on using demo data with our editor. (Answered 2026-09-27 →
   [D035](../decisions/D035-outreach-and-security-disclosure.md) item 2: one letter from the owner after the name
   clearance and before the first public release, also asking about 1.99 data, the MIT metadata and extension overlays
   for Bohemia's campaigns; answers are recorded in this doc. Not sent yet.)
9. Before 1.0: legal review of `NOTICE`, the exception wording and the name. (Still open: an open part of D031.)

---

## Open questions

- **Bohemia confirmation:** is loading APL-SA data (including the free demo's) in a third-party GPL editor acceptable
  under their reading? Does their "do not reverse engineer" rule have any bearing when the code is GPL? **[U]**
  (How it is asked, answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 2: in
  the owner's one letter to Bohemia; not sent yet.)
- **Demo EULA:** does the Steam Subscriber Agreement or a demo-specific EULA restrict demo data use outside the demo
  binary? No EULA link was found in the Steam API data. **[U]** (Related: the same letter asks about loading the
  demo's data in a GPL editor, D035 item 2; not sent yet.)
- **Pre-remaster data:** is original OFP/CWA 1.99 retail or GOG data also APL-SA? Should the editor support it? **[U]**
  (The licence part is asked in the same letter, D035 item 2; not sent yet.)
- **The "OPERATION FLASHPOINT" registration:** exact holder entity, jurisdictions and live status. **[U]**
- **Trident's MIT metadata vs GPL LICENSE:** should we ask CWR-CE to clarify? This only matters if a permissive crate
  wants Trident code. **[U]** (Answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md)
  item 2: the owner's letter to Bohemia asks about the MIT metadata; not sent yet.)
- **HEMTT relicensing:** would HEMTT adopt "GPL-2.0-or-later"? That would allow linking its crates. **[U]**
- **Gemma 4:** does Google's Prohibited Use Policy apply contractually on top of Apache-2.0? **[U]** (Until resolved,
  [D037](../decisions/D037-model-manager-recommended-list.md) keeps such a model off the recommended list.)
- **BIKI terms:** what is the exact wording of the wiki's content license? The page returns HTTP 403 to automated
  fetches, so a human should read it once. **[U]**
- **Model trained on GPL CWR code or docs:** what license status do the weights have? This is unsettled law. **[U]**
- **AI-contribution policy:** do we allow `Assisted-by:` trailers (common in agent-heavy projects) or follow CWR-CE's
  ban? This is a project decision. (Answered 2026-09-27 → [D032](../decisions/D032-contribution-terms-dco.md), OWQ-05
  (a): allowed and optional, neither required nor forbidden.)
- **Docs license:** CC-BY-SA-4.0 (like iron-curtain) or GPL-only for simplicity? This is a project decision.
  (Answered 2026-09-27 → [D031](../decisions/D031-generated-content-permission-and-licence-scope.md) item 2, OWQ-02
  (a): `GPL-3.0-or-later`.)

---

## Sources

**Code at pinned commits**

- `BohemiaInteractive/CWR@ffc61838b7`:
  - `LICENSE#L1-L3`, `#L219`, `#L235-L248`, `#L348-L410`, `#L557`, `#L577-L579`, `#L682-L721`
  - `README.md#L6-L18`, `#L49-L83`
  - `CONTRIBUTING.md#L34-L52`
  - `CREDITS.md#L40-L41`, `#L83-L85`
  - `THIRD_PARTY_NOTICES.md#L1-L25`, `#L537-L569`
  - `engine/Trident/Cargo.toml#L6`, `mserver/*/Cargo.toml#L6`
  - `tests/fixtures/ASSET_SOURCES.md#L1-L15`
  - `engine/Poseidon/UI/Map/UIArcade.cpp#L1-L15`
  - `apps/README.md`
- `ofpisnotdead-com/CWR-CE@b67bf3bd62`:
  - `LICENSE` (identical to CWR)
  - `README.md#L1`, `#L10-L20`, `#L92-L128`
  - `CONTRIBUTING.md#L59-L72`, `#L80-L95`
  - `docs/build/win.md#L11`
  - `engine/Trident/Cargo.toml#L6`
- `iron-curtain-engine/iron-curtain@7b7fac7fa5`: `LICENSE#L1-L16`, `deny.toml#L1-L45`, `CONTRIBUTING.md#L91-L100`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`:
  - `LICENSE-DOCS#L1-L53`
  - `src/decisions/09c/D051-gpl-license.md#L1-L127`
  - `src/decisions/09a/D076-standalone-crates.md#L10-L48`
- LICENSE headers at the pinned commits:
  - MIT: `0xPlaygrounds/rig@42f4e060ef`, `earendil-works/pi@2b0a123de9`, `anomalyco/opencode@b65de4d694`,
    `askbudi/tinyagent@1b85dc351f`, `deepseek-ai/deepseek-harness@477b4f4205`
  - Apache-2.0 + NOTICE: `openai/codex@e72da2b538`, `headroomlabs-ai/headroom@7968122658`

**Web** (retrieved 2026-09-26)

- Bohemia licenses and rules:
  - APL-SA: <https://www.bohemia.net/community/licenses/arma-public-license-share-alike>
  - Bohemia license index: <https://www.bohemia.net/community/licenses>
  - Game Content Usage Rules: <https://www.bohemia.net/en/community/game-content-usage-rules>
  - BIKI disclaimer (via search): <https://community.bistudio.com/wiki/Meta:General_disclaimer>
- Steam store API: demo <https://store.steampowered.com/api/appdetails?appids=4819000>; full game
  <https://store.steampowered.com/api/appdetails?appids=65790>
- GitHub API: <https://api.github.com/repos/BohemiaInteractive/CWR>, <https://api.github.com/repos/ofpisnotdead-com/CWR-CE>,
  <https://api.github.com/orgs/ofpisnotdead-com/repos>, <https://api.github.com/repos/BrettMayson/HEMTT>,
  <https://api.github.com/repos/KoffeinFlummi/armake2>, <https://api.github.com/repos/acemod/ACE3>,
  <https://api.github.com/repos/CBATeam/CBA_A3>
- Community tool license files:
  - HEMTT: <https://raw.githubusercontent.com/BrettMayson/HEMTT/main/Cargo.toml>,
    <https://raw.githubusercontent.com/BrettMayson/HEMTT/main/libs/pbo/Cargo.toml>,
    <https://raw.githubusercontent.com/BrettMayson/HEMTT/main/LICENSE>
  - armake2: <https://raw.githubusercontent.com/KoffeinFlummi/armake2/master/Cargo.toml>
  - ACE3: <https://raw.githubusercontent.com/acemod/ACE3/master/LICENSE>
  - CBA_A3: <https://raw.githubusercontent.com/CBATeam/CBA_A3/master/LICENSE.md>
- crates.io API: <https://crates.io/api/v1/crates/hemtt-pbo>, <https://crates.io/api/v1/crates/armake2>,
  <https://crates.io/api/v1/crates/ring>, <https://crates.io/api/v1/crates/aws-lc-sys>,
  <https://crates.io/api/v1/crates/llama-cpp-2>, <https://crates.io/api/v1/crates/candle-core>
- License compatibility:
  - ASF on GPL: <https://www.apache.org/licenses/GPL-compatibility.html>
  - MPL 2.0 FAQ: <https://www.mozilla.org/en-US/MPL/2.0/FAQ/>
  - FSF license list (unreachable directly; cited via search): <https://www.gnu.org/licenses/license-list.html>
  - CC compatible licenses: <https://creativecommons.org/share-your-work/licensing-considerations/compatible-licenses/>
- EU law:
  - Directive 2009/24/EC: <https://eur-lex.europa.eu/eli/dir/2009/24/oj/eng> (text read from
    <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32009L0024>)
  - CJEU C-406/10 *SAS Institute v WPL*: <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:62010CJ0406>
- Operation Flashpoint history and ownership:
  - <https://en.wikipedia.org/wiki/Operation_Flashpoint:_Cold_War_Crisis>
  - EA completes Codemasters acquisition (8-K):
    <https://www.sec.gov/Archives/edgar/data/712515/000071251521000028/a991pressrelease1.htm>
- Model licenses:
  - Gemma 4 blog: <https://opensource.googleblog.com/2026/03/gemma-4-expanding-the-gemmaverse-with-apache-20.html>
  - Gemma 4 license: <https://ai.google.dev/gemma/docs/gemma_4_license>
  - Gemma Terms of Use: <https://ai.google.dev/gemma/terms>
  - Llama 3.2 license: <https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama3_2/LICENSE>
  - HF model API: <https://huggingface.co/api/models/Qwen/Qwen3.6-35B-A3B>,
    <https://huggingface.co/api/models/google/gemma-4-E4B-it>,
    <https://huggingface.co/api/models/google/gemma-3-4b-it>,
    <https://huggingface.co/api/models/microsoft/phi-4-mini-instruct>,
    <https://huggingface.co/api/models/meta-llama/Llama-3.2-3B-Instruct>,
    <https://huggingface.co/api/models/HuggingFaceTB/SmolLM3-3B>,
    <https://huggingface.co/api/models/openai/gpt-oss-20b>,
    <https://huggingface.co/api/models/LiquidAI/LFM2.5-1.2B-Instruct>
  - LFM Open License v1.0: <https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct/raw/main/LICENSE>
- US Copyright Office, *Copyright and AI Part 2*:
  <https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf>
  (publication date from <https://www.copyright.gov/ai/>)
- HF model search: <https://huggingface.co/api/models?author=Qwen&search=Qwen3.6>,
  <https://huggingface.co/api/models?author=google&search=gemma-4>
- Tooling and specifications:
  - REUSE 3.3: <https://reuse.software/spec-3.3/>
  - Cargo manifest: <https://doc.rust-lang.org/cargo/reference/manifest.html>
  - cargo-deny license config: <https://embarkstudios.github.io/cargo-deny/checks/licenses/cfg.html>
  - cargo-deny common CLI options: <https://embarkstudios.github.io/cargo-deny/cli/common.html>,
    <https://raw.githubusercontent.com/EmbarkStudios/cargo-deny/main/src/cargo-deny/main.rs>
  - DCO: <https://developercertificate.org/>
- Fonts: Wine Tahoma: <https://en.wikipedia.org/wiki/Tahoma_(typeface)>,
  <https://packages.fedoraproject.org/pkgs/wine/wine-tahoma-fonts/index.html>

---

## Verification notes

Adversarial fact-check, 2026-09-26. Primary sources were re-read in local clones at the pinned SHAs and fetched live.

**Confirmed.**

- CWR `LICENSE`: header at #L1-L3, Additional Terms at #L682-L721 (quoted text matches), 721 lines. There is no
  Bohemia copyright line.
- CWR-CE `LICENSE` has the same SHA-256 (`AD3E819B…94D0CE`).
- GPLv3 line pointers are correct: §0 "modify" #L89-L90, §5 #L219-L248, §7 #L348-L410, §13 #L557, §14 #L577-L579.
- The `license = "MIT"` at line 6 of all five Rust crates holds in both repos. `THIRD_PARTY_NOTICES.md#L568-L569` and
  #L548-L553 are correct.
- README, CONTRIBUTING, CREDITS and `ASSET_SOURCES.md` quotes are correct, as are the CWR-CE README (#L1, #L14),
  CONTRIBUTING (#L59-L72, #L85-L87) and `docs/build/win.md#L11`. `UIArcade.cpp` has no license header.
- iron-curtain `LICENSE#L1-L16`, `CONTRIBUTING.md#L91-L100` and `deny.toml#L8-L25` are correct. So are D051 and D076.
- LFM2.5 weights: `lfm1.0` (LFM Open License v1.0) per the HF API and the model's `LICENSE` file, including the
  US$10M revenue threshold for commercial use.
- Harness repo licenses: MIT for rig, pi, opencode, tinyagent and deepseek-harness; Apache-2.0 + NOTICE for codex and
  headroom.
- Live pages: APL-SA and the Usage Rules (both "Updated 21/08/2026"), the Steam appdetails for 65790 and 4819000 (demo
  released 22 Jun 2026), and the GitHub API (`NOASSERTION` for both CWR repos; GPL-2.0 for HEMTT and CBA_A3).
- HEMTT `libs/pbo` `license = "GPL-2.0"` with plain GPLv2 text; armake2 `GPL-2.0-or-later` (0.3.0, 2018-12-22). The
  ACE3 preamble is correct.
- crates.io data for ring, aws-lc-sys, llama-cpp-2 0.1.157 and candle-core 0.11.0. HF licenses for all listed models.
- Gemma blog (2026-04-02), Gemma ToU (modified 2026-04-01; excludes Gemma 4), and the Llama 3.2 §1.b and 700M terms.
- CC BY-SA 4.0 to GPLv3 (8 Oct 2015, one-way), ASF, MPL Q14, REUSE 3.3, Cargo `license` docs and the removed
  cargo-deny keys.
- EA 8-K (2021-02-18), Wikipedia on the OFP name, CJEU C-406/10 operative part (2 May 2012), Directive Art. 4(1)(b).

**Changed.**

- The Directive Art. 1(2) quote said "underline"; it now reads "underlie" and gives the full sentence.
- §3.2 and TL;DR: the Steam demo text does not name APL-SA or NonCommercial. The APL-SA link for the demo rests on the
  CWR README, and the conclusion is now marked [I].
- BIKI "non-commercial" term (TL;DR, §3.5): downgraded to [U]. The page returns 403, including its raw and API forms.
  The rule to avoid copying BIKI text still holds by default.
- §10.3: fixed the `cargo deny` command. `--config` is a top-level option and goes before `check`.
- §10.2: the generic header now points to NOTICE, as §7 requires for our own added permission. The ported-file note
  now cites §5(b).
- §10.6: §5(d) does not require notices when the original UI lacks them; they are now marked best practice.
- §6.4: the LICENSE-DOCS citation now points to the design-docs repo, not the code repo.
- Added notes on:
  - the SAS v WPL facts (WPL had no source access, per para. 44);
  - GPLv2 §9 for HEMTT;
  - Qwen3.6 sizes;
  - a literal-reading caveat on the §7 "using" trademark term.

**Not verified.**

- The FSF license-list quote (gnu.org unreachable).
- The US Copyright Office quote (the PDF was unparseable; only the date was confirmed).
- EUTMR Art. 14(1)(c) (EUR-Lex returned an empty page).
- The exact holder of the "OPERATION FLASHPOINT" registration (still [U], as in §9).

**Owner answers folded, 2026-09-27.** Pointers only, no analysis rewritten: the TL;DR, §3.3, §6.2, §8, §9, §10.1,
§10.2, §10.5, §11 and the open questions now point to D031, D032, D034, D035 and D037 (and to D001 and D002 where the
permissive lane and the name are concerned). Superseded notes: the permissive lane (TL;DR, §6.3, §10.1, §10.5; D001
and D031 item 3), the CC-BY-SA docs licence (§6.4, §10.1; D031 item 2) and "Default-download OK" in §8 (D037). Still to
do: the clearance search, the rename, the Bohemia letter (nothing sent yet) and the legal review before 1.0.
