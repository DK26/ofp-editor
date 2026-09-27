#!/usr/bin/env python3
"""Plotroom / Wilco cost model (research tool; see docs/research/40-token-economy.md).

Estimates billed tokens and USD per workflow run for six harness strategies
(A-F, plus C+eff) across cloud model tiers, using prices verified live on
2026-09-27 (facts tables of the three verified research reports).

Tags used in assumption notes: [V] verified source, [I] inferred / our
arithmetic or design reading, [U] unknown (a placeholder to be measured).

Running it writes cost_model.json next to this file (git-ignored);
docs/research/data/cost-model.csv is derived from that output.

Token sizes use the repo convention of 3.5 bytes per token
(docs/research/data/catalog-sizes.csv rows 91-103), not tokenizer counts.
"""
import copy
import json
import math
import os

AS_OF = "2026-09-27"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "cost_model.json")

# ── Price table (USD per 1M tokens), all as_of 2026-09-27 ────────────────────
# inp/read/write/out = standard; write1h = Anthropic 1-hour TTL write;
# b_* = Batch (Anthropic: cache multipliers stack with the 50% batch discount,
# so b_read = 0.5*read and b_write = 0.5*write [I from "multipliers stack"]);
# off_* = DeepSeek off-peak. read None = no context caching available.
# cache_designed = how Strategy C caches; cache_default = what happens with no
# deliberate cache design (Strategies A/B).
PRICES = {
    # ---- Anthropic [V] platform.claude.com pricing + prompt-caching pages
    "claude-haiku-4-5": dict(
        provider="anthropic", inp=1.00, read=0.10, write=1.25, write1h=2.00, out=5.00,
        b_inp=0.50, b_read=0.05, b_write=0.625, b_write1h=1.00, b_out=2.50,
        min_prefix=4096, cache_designed="explicit", cache_default="none", ttl_s=300,
        think_default="none", think_lowest="none", tool_sys=496, claude47=False,
        note="retirement not sooner than 2026-10-15 [V]; no effort param, thinking only via budget_tokens"),
    "claude-sonnet-5": dict(
        provider="anthropic", inp=2.00, read=0.20, write=2.50, write1h=4.00, out=10.00,
        b_inp=1.00, b_read=0.10, b_write=1.25, b_write1h=2.00, b_out=5.00,
        min_prefix=1024, cache_designed="explicit", cache_default="none", ttl_s=300,
        think_default="high", think_lowest="none", tool_sys=354, claude47=True,
        note="$2/$10 is now standard; the $3/$15 increase will not occur [V]"),
    "claude-opus-5-5": dict(
        provider="anthropic", inp=4.00, read=0.20, write=5.00, write1h=8.00, out=20.00,
        b_inp=2.00, b_read=0.10, b_write=2.50, b_write1h=4.00, b_out=10.00,
        min_prefix=512, cache_designed="explicit", cache_default="none", ttl_s=300,
        think_default="medium", think_lowest="low", tool_sys=286, claude47=True,
        note="read 0.05x; thinking cannot be disabled; default effort medium [V]"),
    "claude-fable-5-1": dict(
        provider="anthropic", inp=10.00, read=0.25, write=12.50, write1h=20.00, out=50.00,
        b_inp=5.00, b_read=0.125, b_write=6.25, b_write1h=10.00, b_out=25.00,
        min_prefix=512, cache_designed="explicit", cache_default="none", ttl_s=300,
        think_default="high", think_lowest="low", tool_sys=286, claude47=True,
        note="read 0.025x; thinking always on [V]; tool_sys not listed, Opus value used [I]"),
    # ---- OpenAI [V] developers.openai.com pricing + prompt-caching guide
    # GPT-5.6+/GPT-6: caching on by default (implicit), writes 1.25x replace the
    # input rate; explicit mode: content after the last breakpoint billed at the
    # uncached rate with no write charge [V]. Implicit mode writes "changing
    # content" up to the latest eligible message [I from the guide's wording].
    "gpt-6-luna": dict(
        provider="openai", inp=0.10, read=0.01, write=0.125, write1h=None, out=0.50,
        b_inp=0.05, b_read=0.005, b_write=0.0625, b_write1h=None, b_out=0.25,
        min_prefix=1024, cache_designed="explicit", cache_default="implicit_write", ttl_s=1800,
        think_default="medium", think_lowest="none", tool_sys=0, claude47=False,
        note="released 2026-09-22; reasoning none..max, default medium [V]"),
    "gpt-6-sol": dict(
        provider="openai", inp=2.00, read=0.20, write=2.50, write1h=None, out=10.00,
        b_inp=1.00, b_read=0.10, b_write=1.25, b_write1h=None, b_out=5.00,
        min_prefix=1024, cache_designed="explicit", cache_default="implicit_write", ttl_s=1800,
        think_default="medium", think_lowest="none", tool_sys=0, claude47=False,
        note="EU residency is Standard-only (no Batch/Flex) [V]"),
    "gpt-6-astra": dict(
        provider="openai", inp=10.00, read=1.00, write=12.50, write1h=None, out=50.00,
        b_inp=5.00, b_read=0.50, b_write=6.25, b_write1h=None, b_out=25.00,
        min_prefix=1024, cache_designed="explicit", cache_default="implicit_write", ttl_s=1800,
        think_default="medium", think_lowest="low", tool_sys=0, claude47=False,
        note="rejects reasoning none (400) [V]; Flex availability [U]"),
    # ---- Google [V] ai.google.dev pricing + caching (page updated 2026-09-24)
    # Implicit caching (no write premium), minimum 4,096 tokens for 3.5-3.8 Flash
    # and 3.1 Pro. Explicit caches bill storage per hour: not used here.
    "gemini-3.8-flash": dict(
        provider="google", inp=0.75, read=0.075, write=0.75, write1h=None, out=3.75,
        b_inp=0.375, b_read=0.0375, b_write=0.375, b_write1h=None, b_out=1.875,
        min_prefix=4096, cache_designed="implicit", cache_default="implicit_free", ttl_s=600,
        think_default="medium", think_lowest="minimal", tool_sys=0, claude47=False,
        note="prices double from 2027-01-01 [V]; implicit TTL [U] (600 s assumed)"),
    "gemini-3.5-flash-lite": dict(
        provider="google", inp=0.30, read=None, write=0.30, write1h=None, out=2.50,
        b_inp=0.15, b_read=None, b_write=0.15, b_write1h=None, b_out=1.25,
        min_prefix=10**9, cache_designed="none", cache_default="none", ttl_s=0,
        think_default="minimal", think_lowest="minimal", tool_sys=0, claude47=False,
        note="CONFLICT between reports: one lists cached $0.03, another says context caching 'Not available'; modelled as no caching [U]"),
    "gemini-3.1-pro-preview": dict(
        provider="google", inp=2.00, read=0.20, write=2.00, write1h=None, out=12.00,
        b_inp=1.00, b_read=0.10, b_write=1.00, b_write1h=None, b_out=6.00,
        min_prefix=4096, cache_designed="implicit", cache_default="implicit_free", ttl_s=600,
        think_default="high", think_lowest="low", tool_sys=0, claude47=False,
        note="<=200K prompt tier; batch cached rate 0.10 [I]; lowest thinking level on Pro [U]"),
    # ---- DeepSeek [V] api-docs.deepseek.com pricing + kv_cache guide
    # Disk cache on by default, best-effort, no write premium; peak prices are
    # the default here (conservative); no batch tier, so E uses off-peak.
    "deepseek-flash": dict(
        provider="deepseek", inp=0.30, read=0.006, write=0.30, write1h=None, out=1.20,
        off_inp=0.15, off_read=0.003, off_out=0.60,
        min_prefix=64, cache_designed="auto", cache_default="auto_free", ttl_s=3 * 3600,
        think_default="none", think_lowest="none", tool_sys=0, claude47=False,
        note="thinking mode default [U] (modelled as non-thinking); min prefix unstated (64 assumed) [U]"),
    "deepseek-v4-pro": dict(
        provider="deepseek", inp=1.32, read=0.044, write=1.32, write1h=None, out=3.96,
        off_inp=0.66, off_read=0.022, off_out=1.98,
        min_prefix=64, cache_designed="auto", cache_default="auto_free", ttl_s=3 * 3600,
        think_default="none", think_lowest="none", tool_sys=0, claude47=False,
        note="thinking mode default [U]"),
    # ---- Mistral [V list prices; cached = 10% computed I]
    "mistral-small-4": dict(
        provider="mistral", inp=0.15, read=0.015, write=0.15, write1h=None, out=0.60,
        b_inp=0.075, b_read=0.0075, b_write=0.075, b_write1h=None, b_out=0.30,
        min_prefix=64, cache_designed="keyed", cache_default="none", ttl_s=300,
        think_default="none", think_lowest="none", tool_sys=0, claude47=False,
        note="caching only with prompt_cache_key; lifetime [U] (300 s assumed)"),
}

TIERS_MAIN = {"cheap": "gpt-6-luna", "mid": "claude-sonnet-5", "frontier": "claude-opus-5-5"}
TIERS_ALL = [
    ("cheap", "gpt-6-luna"), ("cheap", "deepseek-flash"), ("cheap", "claude-haiku-4-5"),
    ("cheap", "gemini-3.5-flash-lite"), ("cheap", "mistral-small-4"),
    ("mid", "claude-sonnet-5"), ("mid", "gpt-6-sol"), ("mid", "gemini-3.8-flash"), ("mid", "deepseek-v4-pro"),
    ("frontier", "claude-opus-5-5"), ("frontier", "gpt-6-astra"), ("frontier", "claude-fable-5-1"),
    ("frontier", "gemini-3.1-pro-preview"),
]
# Strategy D router = cheapest model on the SAME provider (single BYOK key).
ROUTER_SAME_PROVIDER = {
    "anthropic": "claude-haiku-4-5", "openai": "gpt-6-luna", "google": "gemini-3.5-flash-lite",
    "deepseek": "deepseek-flash", "mistral": "mistral-small-4",
}

# ── Thinking (reasoning) tokens per call [U: unmeasured for Wilco steps] ─────
# Medium-effort baseline per step shape; level multipliers loosely follow the
# Anthropic cost guide's "low ~1/3 of the cost, xhigh 2.5x" on coding [I].
THINK_MED = {"pick": 300, "fill_enum": 400, "extract": 400, "fill_text": 500,
             "compose": 1500, "explain": 600, "chat": 1500, "compact": 1500}
LEVEL_MULT = {"none": 0.0, "minimal": 0.1, "low": 0.35, "medium": 1.0, "high": 1.6}

# ── Capsule building blocks (tokens, 3.5 bytes/token) ────────────────────────
CORE = 480        # prompts/design-sensibility/core.md: ~1,920 chars -> ~480 [V repo README]
LENS = 310        # one lens: 1,150-1,260 chars -> 290-320 [V repo README]
SHAPE = {"pick": 200, "fill_enum": 250, "extract": 300, "fill_text": 250, "compose": 400, "explain": 250}  # [I]
EXEMPLAR = {"pick": 120, "fill_enum": 150, "extract": 200, "fill_text": 180, "compose": 350, "explain": 200}  # [I]
N_EX_STANDARD = 2  # doc 25 §5.2: exemplars at Standard = 2
CARD = 200        # card <= 150 words (doc 30) [I]
FM_REF = 1150     # skills/field-manual/references/*.md ~3.2-5.5 KB -> ~1,150 [V repo sizes, I tokens]
PRIMER_SECTIONS = 1000  # part of mission-primer SKILL.md (8,164 B -> ~2,330 whole) [I]
PRIMER_WHOLE = 2330
EXPLAINER_SYS = 400
TASK = 40
MENU = 200        # <=7 one-line options + X/Q escapes (doc 25 §6.2) [I]
SLOT_SPEC = 150
FINDING = 150     # one repair finding (doc 25 §7.2) [I]
VARIANT_NOTE = 20  # per-candidate diversity suffix; Claude 5.x reject temperature [V]
REPAIR_RATE = {"pick": 0.03, "fill_enum": 0.08, "extract": 0.10, "fill_text": 0.12,
               "compose": 0.25, "explain": 0.05}  # P(a candidate needs a repair) [U]

# Mission size: median official SP mission.sqm 64.6 KB (corpus-structure-stats.csv
# all-sp-playable) -> 18,460 tokens + briefing ~430 + description.ext ~290 [V data, I tokens]
DOC_MISSION = 19200
DOC_MISSION_P90 = 30800   # p90 105.2 KB
SYS_A = 6000   # naive agent: system 1,500 + primer 2,330 + ~12 tool schemas ~2,200 [I]
SESSION_S = 1800


def g(name, kind, shape, role, n, Kc, S, Dd, U, out, ex, bulk=False, kinds=1, clusters=None):
    """One decision group: n decisions of one DecisionKind (or `kinds` kinds)."""
    return dict(name=name, kind=kind, shape=shape, role=role, n=n, Kc=Kc, S=S, Dd=Dd, U=U,
                out=out, ex=ex, bulk=bulk, kinds=kinds, clusters=clusters)


def S_of(shape, lens=True, card=0, extra=0, n_ex=N_EX_STANDARD, core=True):
    return (CORE if core else 0) + (LENS if lens else 0) + SHAPE[shape] + card + extra + n_ex * EXEMPLAR[shape]


def EX_of(shape, n_ex=N_EX_STANDARD):
    return n_ex * EXEMPLAR[shape]


# ── Workflow definitions (Standard effort) ───────────────────────────────────
BRIEF = 250  # verbatim campaign brief [I]
WORKFLOWS = {}

# (1) campaign-from-brief: doc 25 §4.1 S0-S9, §4.5 counts for 8 missions.
WORKFLOWS["campaign-from-brief"] = dict(session=False, groups=[
    g("S0 intake Fill (quote-checked)", "s0", "extract", "router", 5, "one",
      S_of("extract", lens=False), BRIEF, TASK, 120, EX_of("extract")),
    g("S1 premise cards", "s1", "fill_text", "writer", 3, "one",
      S_of("fill_text"), BRIEF + 300, TASK + SLOT_SPEC, 250, EX_of("fill_text")),
    g("S2 bible rows", "s2row", "fill_text", "writer", 10, "creative",
      S_of("fill_text", card=CARD), BRIEF + 600, TASK + SLOT_SPEC, 150, EX_of("fill_text")),
    g("S2 home-town picks", "s2pick", "pick", "router", 5, "pick",
      S_of("pick"), BRIEF + 600, TASK + MENU, 45, EX_of("pick")),
    g("S3 graph-shape pick", "s3shape", "pick", "router", 1, "pick",
      S_of("pick"), BRIEF + 700, TASK + MENU, 45, EX_of("pick")),
    g("S3 beat picks", "s3beat", "pick", "router", 8, "pick",
      S_of("pick"), BRIEF + 700, TASK + MENU, 45, EX_of("pick")),
    g("S3 node names", "s3names", "fill_text", "writer", 1, "creative",
      S_of("fill_text"), BRIEF + 700, TASK + SLOT_SPEC, 120, EX_of("fill_text")),
    g("S4 consequence-archetype picks", "s4pick", "pick", "router", 4, "pick",
      S_of("pick"), BRIEF + 800, TASK + MENU, 45, EX_of("pick")),
    g("S4 guard constants", "s4fill", "fill_enum", "router", 4, "one",
      S_of("fill_enum", card=CARD), BRIEF + 800, TASK + SLOT_SPEC, 70, EX_of("fill_enum")),
    g("S5 concept picks (6 kinds x 8 missions)", "s5pick", "pick", "router", 48, "pick",
      S_of("pick"), BRIEF + 900, TASK + MENU, 45, EX_of("pick"), kinds=6),
    g("S5 concept enum fills", "s5fill", "fill_enum", "router", 8, "one",
      S_of("fill_enum", card=CARD), BRIEF + 900, TASK + SLOT_SPEC, 70, EX_of("fill_enum")),
    g("S7 text slots (22 x 8 missions)", "s7", "fill_text", "writer", 176, "creative",
      S_of("fill_text", card=CARD), BRIEF + 1000, TASK + SLOT_SPEC, 110, EX_of("fill_text"),
      bulk=True, kinds=4),
])

# (2) populate-town: doc 38 §8.2 (IntentFill before dispatch + one composition Pick).
WORKFLOWS["populate-town"] = dict(session=False, groups=[
    g("IntentFill (chat start)", "intent", "extract", "router", 1, "one",
      S_of("extract", lens=False), 40, TASK, 120, EX_of("extract")),
    g("composition Pick (+probability-of-presence reference)", "comp", "pick", "router", 1, "pick",
      S_of("pick", extra=917), 40 + 500, TASK + MENU, 45, EX_of("pick")),
])

# (3) write-briefing: doc 38 §8.3 (<=12 slots; 11 = Main, Plan, 3 OBJ_, 6 debriefings).
WORKFLOWS["write-briefing"] = dict(session=False, groups=[
    g("briefing slot Fills", "brief", "fill_text", "writer", 11, "creative",
      S_of("fill_text", card=CARD, extra=400), 30 + 1000, TASK + SLOT_SPEC, 90, EX_of("fill_text"),
      bulk=True),
])

# (4) cutscene director: doc 32 §5.3 tools for the headline 30-second intro
# (4 shots, title card, music, radio chatter) + one critique.
WORKFLOWS["cutscene-director"] = dict(session=False, groups=[
    g("IntentFill", "intent", "extract", "router", 1, "one", S_of("extract", lens=False), 60, TASK, 120, EX_of("extract")),
    g("cine.suggest template picks (4 shots)", "cpick", "pick", "router", 4, "pick",
      S_of("pick"), 60 + 700, TASK + MENU, 45, EX_of("pick")),
    g("cine.fill per shot (subject, mood, duration, caption)", "cfill", "fill_enum", "router", 4, "one",
      S_of("fill_enum", card=CARD), 60 + 700, TASK + SLOT_SPEC, 90, EX_of("fill_enum")),
    g("music pick", "mpick", "pick", "router", 1, "pick", S_of("pick"), 60 + 700, TASK + MENU, 45, EX_of("pick")),
    g("title card text", "title", "fill_text", "writer", 1, "creative",
      S_of("fill_text"), 60 + 700, TASK + SLOT_SPEC, 40, EX_of("fill_text")),
    g("screenplay.write radio chatter (Compose, 4 lines)", "screen", "compose", "writer", 1, "creative",
      S_of("compose", extra=PRIMER_SECTIONS), 60 + 700, TASK + SLOT_SPEC, 250, EX_of("compose")),
    g("cine.critique (phrase lint findings)", "crit", "explain", "explainer", 1, "one",
      EXPLAINER_SYS + PRIMER_SECTIONS + SHAPE["explain"] + EXEMPLAR["explain"], 60 + 700, 300, 200,
      EXEMPLAR["explain"]),
])

# (5) 30-minute interactive session: 12 requests = 4 explain, 5 small edits,
# 3 lint-fix requests (2 findings each). clusters = request clusters per kind.
EXPL_S = EXPLAINER_SYS + PRIMER_SECTIONS + SHAPE["explain"] + EXEMPLAR["explain"]
WORKFLOWS["session-30min"] = dict(session=True, groups=[
    g("IntentFill per request", "intent", "extract", "router", 12, "one",
      S_of("extract", lens=False), 50, TASK, 120, EX_of("extract"), clusters=12),
    g("explain/teach answers", "explainer", "explain", "explainer", 4, "one",
      EXPL_S, 60 + 600, FM_REF, 250, EXEMPLAR["explain"], clusters=7),
    g("edit Picks", "editpick", "pick", "router", 5, "pick", S_of("pick"), 50 + 600, TASK + MENU, 45,
      EX_of("pick"), clusters=5),
    g("edit parameter Fills", "editfill", "fill_enum", "router", 2, "one",
      S_of("fill_enum", card=CARD), 50 + 600, TASK + SLOT_SPEC, 70, EX_of("fill_enum"), clusters=2),
    g("lint-fix Picks among computed fixes", "fixpick", "pick", "router", 6, "pick",
      S_of("pick"), 50 + 500, TASK + MENU, 45, EX_of("pick"), clusters=3),
    g("finding explanations", "explainer", "explain", "explainer", 6, "one",
      EXPL_S, 50 + 500, 150, 120, EXEMPLAR["explain"], kinds=0, clusters=7),
])

# ── Naive chat agent (Strategy A) turn scripts [I] ──────────────────────────
# Each turn = one API request: static + history + current document + user msg.
# History keeps prior user msgs, assistant outputs (incl. file text written as
# tool arguments) and tool results; old document snapshots are dropped.
def naive_turns(wf, kn=None):
    fix_turns = int((kn or KNOBS)["a_fix_turns"])
    T = []
    if wf == "campaign-from-brief":
        base = 5000  # outline 2,000 + bible 1,500 + description/flow 1,500 re-attached
        T += [dict(user=BRIEF, doc=0, out=2000, tool=0), dict(user=30, doc=2000, out=1500, tool=0),
              dict(user=30, doc=3500, out=1500, tool=300), dict(user=30, doc=base, out=1500, tool=300)]
        for _ in range(8):  # per mission: write sqm (~6K tokens, smaller than official), fix, briefing, dialogue
            T += [dict(user=30, doc=base, out=6200, tool=300)]
            T += [dict(user=30, doc=base + 6000, out=1650, tool=200)] * fix_turns
            T += [dict(user=30, doc=base + 6000, out=950, tool=100), dict(user=30, doc=base + 6800, out=1350, tool=100)]
        T += [dict(user=60, doc=base + 7600, out=1000, tool=600)] * 3  # final lint-fix passes
    elif wf == "populate-town":
        T = [dict(user=40, doc=DOC_MISSION, out=150, tool=2300),   # lookups: catalog + places
             dict(user=0, doc=DOC_MISSION, out=2400, tool=400),    # place ~15 units as tool args
             dict(user=0, doc=DOC_MISSION, out=800, tool=150),     # fix crew-seat / water errors
             dict(user=0, doc=DOC_MISSION, out=250, tool=0)]       # summary
    elif wf == "write-briefing":
        T = [dict(user=40, doc=DOC_MISSION, out=1100, tool=300),   # whole briefing.html + prose
             dict(user=0, doc=DOC_MISSION, out=1000, tool=100),    # lint fix: rewrite
             dict(user=30, doc=DOC_MISSION, out=900, tool=0)]      # "make it terser": rewrite
    elif wf == "cutscene-director":
        T = [dict(user=60, doc=DOC_MISSION, out=2050, tool=300),   # intro.sqs + config + prose
             dict(user=0, doc=DOC_MISSION, out=1500, tool=100),    # fix script errors
             dict(user=50, doc=DOC_MISSION, out=1700, tool=100),   # preview feedback rewrite
             dict(user=30, doc=DOC_MISSION, out=1600, tool=0)]     # final tweak
    elif wf == "session-30min":
        for _ in range(4):
            T += [dict(user=60, doc=DOC_MISSION, out=400, tool=0)]
        for _ in range(5):
            T += [dict(user=50, doc=DOC_MISSION, out=450, tool=300), dict(user=0, doc=DOC_MISSION, out=200, tool=0)]
        for _ in range(3):
            T += [dict(user=30, doc=DOC_MISSION, out=150, tool=800), dict(user=0, doc=DOC_MISSION, out=800, tool=200)]
    return T


# ── Knobs (defaults = base case) ─────────────────────────────────────────────
KNOBS = dict(
    K_pick=3.0, K_creative=2.0,          # doc 25 §5.2 Standard
    repair_mult=1.0, out_mult=1.0, think_mult=1.0,
    h_run=0.90,                          # stage-prefix hit rate in a workflow run [I]
    h_within=0.95,                       # hit rate for calls seconds apart (samples, repairs) [I]
    h_parallel=0.30,                     # Strategy B: implicit hits on K samples sent in parallel [U]
    h_batch=0.60,                        # batch cache hits best-effort 30-98% [V range, I point]
    h_escalate=0.50,                     # escalated decisions are sparse [I]
    h_chat=0.90,                         # naive chat: auto-cache hits on the append-only prefix [I]
    escalate=0.15,                       # D: router decisions re-run on the tier [I; ~13% fail at low in Anthropic guide]
    escalate_eff=0.10,                   # C+eff: same model, re-run at default effort [I]
    f_escalate=0.0,                      # F: local failures keep default (doc 25 principle 5)
    exemplars_in_prefix=True,            # C needs frozen, un-rotated exemplars ahead of the digest
    tok_mult_claude=1.0,                 # 1.3 = Claude 4.7+ tokenizer (~30% more tokens) [V]
    doc_scale=1.0, H_max=150000,         # naive agent compacts history above 150K [I]
    a_cache="default",                   # naive agent: provider-default caching only
    a_fix_turns=1,                       # naive agent: error-fix turns per generated mission [U]
    writer_effort_G="low",               # G: Draft-text effort (Opus 5.5 lowest is low anyway)
    pad_to_min=False,                    # grow stage prefix past a 4,096 minimum (Haiku 4.5, Gemini 3.x)
    session_ttl1h=False,
    router_override=None,
)


class Tally:
    FIELDS = ["unc", "wr", "rd", "out_vis", "out_think", "calls", "usd", "local_in", "local_out", "local_calls"]

    def __init__(self):
        for f in self.FIELDS:
            setattr(self, f, 0.0)

    def add(self, o):
        for f in self.FIELDS:
            setattr(self, f, getattr(self, f) + getattr(o, f))
        return self

    def as_dict(self):
        d = {f: getattr(self, f) for f in self.FIELDS}
        d["input_tokens"] = self.unc + self.wr + self.rd
        d["output_tokens"] = self.out_vis + self.out_think
        return d


def price(model, t, mode="std", ttl1h=False):
    """Price a tally's token categories for a model (per-1M prices)."""
    P = PRICES[model]
    if mode == "batch" and P["provider"] == "deepseek":
        mode = "offpeak"   # DeepSeek has no batch tier; off-peak is half price [V]
    if mode == "std":
        pi, pr, pw, po = P["inp"], P["read"], P["write"], P["out"]
        if ttl1h and P.get("write1h"):
            pw = P["write1h"]
    elif mode == "batch":
        pi, pr, pw, po = P["b_inp"], P["b_read"], P["b_write"], P["b_out"]
        if ttl1h and P.get("b_write1h"):
            pw = P["b_write1h"]
    elif mode == "offpeak":
        pi, pr, pw, po = P["off_inp"], P["off_read"], P["off_inp"], P["off_out"]
    if pr is None:
        pr = pi
    if pw is None:
        pw = pi
    t.usd += (t.unc * pi + t.wr * pw + t.rd * pr + (t.out_vis + t.out_think) * po) / 1e6
    return t


def K_of(grp, kn):
    return kn["K_pick"] if grp["Kc"] == "pick" else (kn["K_creative"] if grp["Kc"] == "creative" else 1.0)


def run_group(grp, model, effort, cache, kn, h_stage, h_dec, mode="std", ttl1h=False, n=None, local=False):
    """Expected tokens/USD for one decision group on one model.

    cache: 'none' | 'default' (provider behaviour with no cache design, B) |
           'designed' (Strategy C: frozen stage prefix + optional decision breakpoint).
    """
    t = Tally()
    n = grp["n"] if n is None else n
    if n <= 0:
        return t
    P = None if local else PRICES[model]
    tok = kn["tok_mult_claude"] if (P and P["claude47"]) else 1.0
    K = K_of(grp, kn)
    r = REPAIR_RATE[grp["shape"]] * kn["repair_mult"]
    rep = min(r + r * r, 2.0)  # expected repair calls per sample, R = 2 at Standard
    S, Dd, U = grp["S"], grp["Dd"], grp["U"]
    if cache == "designed" and not kn["exemplars_in_prefix"]:
        S, U = S - grp["ex"], U + grp["ex"]
    if (cache == "designed" and kn.get("pad_to_min") and P and P["read"] is not None
            and S < P["min_prefix"] <= 8192):
        S = P["min_prefix"] + 16   # grow the shared card/exemplar pack past the provider minimum
    if K > 1:
        U += VARIANT_NOTE
    S, Dd, U = S * tok, Dd * tok, U * tok
    outv = grp["out"] * kn["out_mult"] * tok
    think = 0.0 if local else THINK_MED[grp["shape"]] * LEVEL_MULT[effort] * kn["think_mult"]
    fin = FINDING * tok
    calls_first = n * K
    calls_rep = n * K * rep
    calls = calls_first + calls_rep
    prompt = S + Dd + U
    rep_extra = calls_rep * (fin + outv)
    if local:
        t.local_in = calls * prompt + rep_extra
        t.local_out = calls * outv
        t.local_calls = calls
        return t
    t.calls = calls
    t.out_vis = calls * outv
    t.out_think = calls * think
    cm = {"none": "none", "default": P["cache_default"], "designed": P["cache_designed"]}[cache]
    minp = P["min_prefix"]
    if cm == "none" or P["read"] is None:
        t.unc = calls * prompt + rep_extra
    elif cache == "default":
        # doc 25 §4.4 order: task line, digest, core+lens, menu, exemplars, schema.
        premium = cm == "implicit_write"
        shared = TASK * tok + Dd + min(S, (CORE + LENS) * tok)

        def put(x):
            if premium and prompt >= minp:
                t.wr += x
            else:
                t.unc += x
        put(n * prompt)                       # first sample: whole prompt new
        m = n * (K - 1)
        if shared >= minp:
            t.rd += m * shared * kn["h_parallel"]
            put(m * shared * (1 - kn["h_parallel"]))
            put(m * (prompt - shared))
        else:
            put(m * prompt)
        if prompt >= minp:                    # repairs extend the previous prompt
            t.rd += calls_rep * prompt * h_dec
            put(calls_rep * prompt * (1 - h_dec))
        else:
            put(calls_rep * prompt)
        put(rep_extra)
    else:  # designed
        stage_ok = S >= minp and calls >= 2
        dec_ok = K >= 2 and (S + Dd) >= minp
        kinds = min(grp.get("kinds", 1), n)
        first_other = n - kinds
        if stage_ok:
            t.wr += S * kinds
            t.rd += S * first_other * h_stage
            t.wr += S * first_other * (1 - h_stage)
        elif dec_ok:
            t.wr += S * n
        else:
            t.unc += S * n
        if dec_ok:
            t.wr += Dd * n
        else:
            t.unc += Dd * n
        t.unc += U * n
        mcalls = calls - n
        if dec_ok:
            t.rd += (S + Dd) * mcalls * h_dec
            t.wr += (S + Dd) * mcalls * (1 - h_dec)
        else:
            if stage_ok:
                t.rd += S * mcalls * h_dec
                t.wr += S * mcalls * (1 - h_dec)
            else:
                t.unc += S * mcalls
            t.unc += Dd * mcalls
        t.unc += U * mcalls + rep_extra
    return price(model, t, mode, ttl1h)


def run_chat(wf, model, kn):
    """Strategy A: naive chat agent, full document re-attached every turn."""
    P = PRICES[model]
    tok = kn["tok_mult_claude"] if P["claude47"] else 1.0
    static = (SYS_A + P["tool_sys"]) * tok
    cm = P["cache_default"] if kn["a_cache"] == "default" else kn["a_cache"]
    if P["read"] is None:
        cm = "none"
    premium = cm in ("implicit_write", "anth_auto")
    minp = P["min_prefix"]
    think = THINK_MED["chat"] * LEVEL_MULT[P["think_default"]] * kn["think_mult"]
    t = Tally()
    H, H_prev, reset = 0.0, None, False

    def request(prompt, common):
        if cm == "none":
            t.unc += prompt
            return
        rd = common * kn["h_chat"] if common >= minp else 0.0
        rest = prompt - rd
        t.rd += rd
        if premium and prompt >= minp:
            t.wr += rest
        else:
            t.unc += rest

    for i, tn in enumerate(naive_turns(wf, kn)):
        doc = tn["doc"] * kn["doc_scale"] * tok if tn["doc"] in (DOC_MISSION,) else tn["doc"] * tok
        user, out, tool = tn["user"] * tok, tn["out"] * kn["out_mult"] * tok, tn["tool"] * tok
        prompt = static + H + doc + user
        common = 0.0 if i == 0 else (static if reset else static + H_prev)
        reset = False
        request(prompt, common)
        t.calls += 1
        t.out_vis += out
        t.out_think += think
        H_prev = H
        H = H + user + out + tool
        if H > kn["H_max"]:          # naive auto-compaction (model-written summary)
            request(static + H, static + H_prev)
            t.calls += 1
            t.out_vis += 4000 * tok
            t.out_think += THINK_MED["compact"] * LEVEL_MULT[P["think_default"]] * kn["think_mult"]
            H, reset = 4000 * tok, True
    return price(model, t)


def session_h(wf, grp, model, kn, ttl1h=False):
    """Stage hit rate for an interactive session: exponential gaps between the
    request clusters that use this kind, against the provider's TTL."""
    P = PRICES[model]
    ttl = 3600 if (ttl1h and P["provider"] == "anthropic") else P["ttl_s"]
    same = [x for x in WORKFLOWS[wf]["groups"] if x["kind"] == grp["kind"]]
    C = max(x["clusters"] or 1 for x in same)
    n_k = sum(x["n"] for x in same)
    p_first = 1 - math.exp(-ttl / (SESSION_S / C)) if ttl > 0 else 0.0
    if n_k <= 1:
        return 0.0, kn["h_within"]
    h = ((C - 1) * p_first + max(n_k - C, 0) * kn["h_within"]) / (n_k - 1)
    return min(h, 1.0), kn["h_within"]


def hits(wf, grp, model, kn, ttl1h=False):
    if WORKFLOWS[wf]["session"]:
        return session_h(wf, grp, model, kn, ttl1h)
    return kn["h_run"], kn["h_run"]


LEVEL_ORDER = ["none", "minimal", "low", "medium", "high"]


def clamp_effort(model, target):
    """Requested effort, raised to the model's lowest level and capped at its default."""
    P = PRICES[model]
    lo, hi = LEVEL_ORDER.index(P["think_lowest"]), LEVEL_ORDER.index(P["think_default"])
    i = LEVEL_ORDER.index(target)
    return LEVEL_ORDER[max(lo, min(i, hi))]


def strategy(wf, S, tier, kn):
    """Run one workflow under one strategy with `tier` as the bound model."""
    Pt = PRICES[tier]
    T = Tally()
    if S == "A":
        return T.add(run_chat(wf, tier, kn))
    ttl1h = kn["session_ttl1h"] and WORKFLOWS[wf]["session"]
    router = kn["router_override"] or ROUTER_SAME_PROVIDER[Pt["provider"]]
    for grp in WORKFLOWS[wf]["groups"]:
        is_router = grp["role"] == "router"
        if S == "B":
            hs, hd = hits(wf, grp, tier, kn)
            T.add(run_group(grp, tier, Pt["think_default"], "default", kn, hs, hd))
        elif S == "C":
            hs, hd = hits(wf, grp, tier, kn, ttl1h)
            T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, hs, hd, ttl1h=ttl1h))
        elif S == "C+eff":
            hs, hd = hits(wf, grp, tier, kn, ttl1h)
            if is_router:
                T.add(run_group(grp, tier, Pt["think_lowest"], "designed", kn, hs, hd, ttl1h=ttl1h))
                T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, kn["h_escalate"], hd,
                                ttl1h=ttl1h, n=grp["n"] * kn["escalate_eff"]))
            else:
                T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, hs, hd, ttl1h=ttl1h))
        elif S in ("D", "E"):
            if is_router:
                hs, hd = hits(wf, grp, router, kn, ttl1h)
                T.add(run_group(grp, router, PRICES[router]["think_lowest"], "designed", kn, hs, hd, ttl1h=ttl1h))
                T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, kn["h_escalate"], kn["h_within"],
                                ttl1h=ttl1h, n=grp["n"] * kn["escalate"]))
            else:
                hs, hd = hits(wf, grp, tier, kn, ttl1h)
                if S == "E" and grp["bulk"]:
                    T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, kn["h_batch"], kn["h_batch"],
                                    mode="batch", ttl1h=True))
                else:
                    T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, hs, hd, ttl1h=ttl1h))
        elif S == "G":   # all levers: D routing + E batch + effort pinned on Draft text / Compose
            if is_router:
                hs, hd = hits(wf, grp, router, kn, ttl1h)
                T.add(run_group(grp, router, PRICES[router]["think_lowest"], "designed", kn, hs, hd, ttl1h=ttl1h))
                T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, kn["h_escalate"], kn["h_within"],
                                ttl1h=ttl1h, n=grp["n"] * kn["escalate"]))
            else:
                target = kn["writer_effort_G"] if grp["shape"] == "fill_text" else "medium"
                eff = clamp_effort(tier, target)
                hs, hd = hits(wf, grp, tier, kn, ttl1h)
                if grp["bulk"]:
                    T.add(run_group(grp, tier, eff, "designed", kn, kn["h_batch"], kn["h_batch"], mode="batch", ttl1h=True))
                else:
                    T.add(run_group(grp, tier, eff, "designed", kn, hs, hd, ttl1h=ttl1h))
                if eff != Pt["think_default"]:   # validator failures re-run at the default effort, same model
                    T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, kn["h_escalate"], kn["h_within"],
                                    ttl1h=ttl1h, n=grp["n"] * kn["escalate_eff"]))
        elif S == "F":
            if is_router:
                T.add(run_group(grp, None, "none", "designed", kn, 0, 0, local=True))
                if kn["f_escalate"] > 0:
                    T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, kn["h_escalate"],
                                    kn["h_within"], n=grp["n"] * kn["f_escalate"]))
            else:
                hs, hd = hits(wf, grp, tier, kn, ttl1h)
                T.add(run_group(grp, tier, Pt["think_default"], "designed", kn, hs, hd, ttl1h=ttl1h))
    return T


STRATS = ["A", "B", "C", "C+eff", "D", "E", "F", "G"]


def run_all(kn=KNOBS, tiers=TIERS_ALL, wfs=None):
    rows = []
    for wf in (wfs or WORKFLOWS):
        for label, model in tiers:
            for S in STRATS:
                t = strategy(wf, S, model, kn).as_dict()
                rows.append(dict(workflow=wf, strategy=S, tier=label, tier_model=model,
                                 input_tokens=round(t["input_tokens"]), cached_read_tokens=round(t["rd"]),
                                 cache_write_tokens=round(t["wr"]), output_tokens=round(t["output_tokens"]),
                                 thinking_tokens=round(t["out_think"]), calls=round(t["calls"], 1),
                                 local_tokens=round(t["local_in"] + t["local_out"]), usd=round(t["usd"], 4)))
    return rows


def lookup(rows, wf, S, model):
    for r in rows:
        if r["workflow"] == wf and r["strategy"] == S and r["tier_model"] == model:
            return r
    raise KeyError((wf, S, model))


def savings(rows):
    out = []
    for wf in WORKFLOWS:
        for label, model in TIERS_ALL:
            u = {S: lookup(rows, wf, S, model)["usd"] for S in STRATS}
            f = lambda a, b: round(u[a] / u[b], 2) if u[b] > 0 else None
            best = min((S for S in STRATS if S != "A"), key=lambda S: u[S])
            out.append(dict(workflow=wf, tier_model=model, A_over_B=f("A", "B"), A_over_C=f("A", "C"),
                            A_over_best=f("A", best), best=best, B_over_C=f("B", "C"),
                            C_over_Ceff=f("C", "C+eff"), C_over_D=f("C", "D"), D_over_E=f("D", "E"),
                            C_over_F=f("C", "F"), A_over_G=f("A", "G"), B_over_G=f("B", "G"),
                            B_over_best=f("B", best)))
    return out


def sens(name, changes, wfs=("campaign-from-brief", "session-30min"),
         models=("gpt-6-luna", "claude-sonnet-5", "claude-opus-5-5"), strats=("A", "B", "C", "C+eff", "D", "E", "F", "G")):
    res = []
    for label, kv in changes:
        kn = dict(KNOBS)
        kn.update(kv)
        for wf in wfs:
            for m in models:
                for S in strats:
                    res.append(dict(sweep=name, setting=label, workflow=wf, tier_model=m, strategy=S,
                                    usd=round(strategy(wf, S, m, kn).usd, 4)))
    return res


def main():
    rows = run_all()
    sv = savings(rows)
    S = []
    S += sens("stage cache hit rate h_run", [(f"h_run={h}", dict(h_run=h)) for h in (0.5, 0.7, 0.9, 0.98)],
              wfs=("campaign-from-brief",), strats=("C", "D", "E", "G"))
    S += sens("repairs (repair-rate multiplier)", [(f"x{m}", dict(repair_mult=m)) for m in (0, 1, 2, 3)],
              wfs=("campaign-from-brief",), strats=("B", "C", "D", "G"))
    S += sens("escalation rate (D)", [(f"e={e}", dict(escalate=e)) for e in (0.05, 0.15, 0.40)],
              wfs=("campaign-from-brief", "session-30min"), strats=("D",))
    S += sens("visible output length", [(f"x{m}", dict(out_mult=m)) for m in (0.5, 1, 2)],
              wfs=("campaign-from-brief",), strats=("A", "B", "C", "D", "G"))
    S += sens("thinking tokens", [(f"x{m}", dict(think_mult=m)) for m in (0, 1, 2)],
              wfs=("campaign-from-brief", "session-30min"), strats=("A", "B", "C", "C+eff", "D", "G"))
    S += sens("candidates K (pick, creative)", [("K=1,1", dict(K_pick=1, K_creative=1)),
                                                ("K=2.2(adaptive),2", dict(K_pick=2.2, K_creative=2)),
                                                ("K=3,2 (Standard)", dict(K_pick=3, K_creative=2)),
                                                ("K=5,4", dict(K_pick=5, K_creative=4))],
              wfs=("campaign-from-brief",), strats=("B", "C", "D", "G"))
    S += sens("exemplars rotated (not in cached prefix)", [("in prefix", dict(exemplars_in_prefix=True)),
                                                           ("rotated, after digest", dict(exemplars_in_prefix=False))],
              wfs=("campaign-from-brief",), strats=("C",))
    S += sens("Claude 4.7+ tokenizer (+30% tokens)", [("x1.0", dict(tok_mult_claude=1.0)),
                                                      ("x1.3", dict(tok_mult_claude=1.3))],
              models=("claude-sonnet-5", "claude-opus-5-5"), strats=("A", "C", "D"))
    S += sens("naive agent document size", [("0.5x median", dict(doc_scale=0.5)), ("median 19.2K", dict(doc_scale=1.0)),
                                            ("p90 30.8K", dict(doc_scale=DOC_MISSION_P90 / DOC_MISSION))],
              wfs=("session-30min",), strats=("A",))
    S += sens("naive agent with Anthropic automatic caching", [("no cache_control", dict(a_cache="default")),
                                                                ("top-level automatic caching", dict(a_cache="anth_auto"))],
              wfs=("campaign-from-brief", "session-30min"), models=("claude-sonnet-5", "claude-opus-5-5"), strats=("A",))
    S += sens("D router choice (Anthropic tiers)", [("same-provider claude-haiku-4-5", dict(router_override=None)),
                                                   ("cross-provider gpt-6-luna", dict(router_override="gpt-6-luna")),
                                                   ("cross-provider deepseek-flash", dict(router_override="deepseek-flash"))],
              wfs=("campaign-from-brief", "session-30min"), models=("claude-sonnet-5", "claude-opus-5-5"), strats=("D",))
    S += sens("session Anthropic TTL", [("5 min", dict(session_ttl1h=False)), ("1 hour (2x write)", dict(session_ttl1h=True))],
              wfs=("session-30min",), models=("claude-sonnet-5", "claude-opus-5-5"), strats=("C", "C+eff"))
    S += sens("pad stage prefix to provider cache minimum", [("no padding", dict(pad_to_min=False)),
                                                             ("pad to minimum", dict(pad_to_min=True))],
              wfs=("campaign-from-brief", "session-30min"),
              models=("claude-haiku-4-5", "gemini-3.8-flash", "gemini-3.1-pro-preview"), strats=("C",))
    S += sens("naive agent fix turns per mission", [(f"{k} fix turn(s)", dict(a_fix_turns=k)) for k in (1, 3)],
              wfs=("campaign-from-brief",), strats=("A",))
    S += sens("G Draft-text effort", [(f"writer={e}", dict(writer_effort_G=e)) for e in ("none", "low", "medium")],
              wfs=("campaign-from-brief",), strats=("G",))
    S += sens("F local failures escalated to cloud", [("0% (keep default)", dict(f_escalate=0.0)), ("20%", dict(f_escalate=0.2))],
              wfs=("campaign-from-brief",), strats=("F",))

    # workflow shape summary
    wsum = {}
    for wf, W in WORKFLOWS.items():
        dec = sum(x["n"] for x in W["groups"])
        calls_B = strategy(wf, "B", "claude-sonnet-5", KNOBS).calls
        wsum[wf] = dict(decisions=dec, cloud_calls_B=round(calls_B, 1), naive_turns=len(naive_turns(wf)),
                        groups=[{k: v for k, v in x.items()} for x in W["groups"]])

    headline = []
    for wf in WORKFLOWS:
        for label, m in TIERS_MAIN.items():
            u = {Sx: lookup(rows, wf, Sx, m)["usd"] for Sx in STRATS}
            headline.append(dict(workflow=wf, tier=label, model=m, usd={k: round(v, 4) for k, v in u.items()}))
    doc = dict(
        as_of=AS_OF,
        strategies={
            "A": "naive chat agent: static 6K system+tools, full document re-attached each turn, append-only history, prose/file outputs, provider-default caching only",
            "B": "Plotroom baseline at Standard effort: typed Pick/Fill/Draft capsules (doc 25 §4.4 order), K=3 Picks, K=2 creative, R<=2, provider-default thinking (doc 21 §7.1), no cache design",
            "C": "B + designed caching: frozen stage prefix first (system, core+lens, cards, frozen exemplars, schema), breakpoint, then digest; second breakpoint after digest when K>=2; explicit mode on OpenAI",
            "C+eff": "C + Pick/Fill pinned to lowest effort on the same model; 10% re-run at default effort",
            "D": "C + Pick/Fill routed to the same-provider cheap router at lowest effort; 15% escalated to the bound model",
            "E": "D + batch (DeepSeek: off-peak) for bulk Draft text (campaign S7, briefing slots)",
            "F": "C with Pick/Fill on a local model ($0) and Draft text/Compose/explain on the cloud tier; local failures keep defaults",
            "G": "all levers: D + E + Draft text at low effort and Compose/explain at <=medium, 10% re-run at default",
        },
        headline=headline,
        legend="[V] verified live/primary; [I] inferred or our arithmetic; [U] unknown placeholder",
        prices={k: dict(v, as_of=AS_OF) for k, v in PRICES.items()},
        knobs=KNOBS,
        blocks=dict(CORE=CORE, LENS=LENS, SHAPE=SHAPE, EXEMPLAR=EXEMPLAR, CARD=CARD, FM_REF=FM_REF,
                    PRIMER_SECTIONS=PRIMER_SECTIONS, MENU=MENU, SLOT_SPEC=SLOT_SPEC, FINDING=FINDING,
                    REPAIR_RATE=REPAIR_RATE, THINK_MED=THINK_MED, LEVEL_MULT=LEVEL_MULT,
                    DOC_MISSION=DOC_MISSION, DOC_MISSION_P90=DOC_MISSION_P90, SYS_A=SYS_A),
        workflows=wsum,
        results=rows,
        savings=sv,
        sensitivity=S,
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)

    # compact console table: main tiers
    print(f"{'workflow':22} {'S':6} " + " ".join(f"{m:>18}" for m in TIERS_MAIN.values()))
    for wf in WORKFLOWS:
        for Sx in STRATS:
            cells = []
            for m in TIERS_MAIN.values():
                r = lookup(rows, wf, Sx, m)
                cells.append(f"${r['usd']:.4f}/{r['input_tokens']/1000:.0f}K/{r['output_tokens']/1000:.1f}K")
            print(f"{wf:22} {Sx:6} " + " ".join(f"{c:>18}" for c in cells))
    print()
    for wf in WORKFLOWS:
        print(wf, wsum[wf]["decisions"], "decisions;", wsum[wf]["cloud_calls_B"], "B calls;", wsum[wf]["naive_turns"], "naive turns")


if __name__ == "__main__":
    main()
