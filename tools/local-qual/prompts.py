#!/usr/bin/env python3
"""Prompts, seeds and answer checks for the local-qual runner (tools/local-qual).

What it owns
------------
Everything that decides *what* one call asks, independent of the runtime that
serves it: the suite-to-shape map, per-shape temperatures, output caps and
system prompts; suite and sidecar loading; the per-(item, sample) seed and
menu permutation; one prompt builder per step shape, including the
harness-uplift variants (open and labels Pick arms, Pick and Fill without a
response schema, Fill with schema text only, Text without constraints); JSON
extraction from model text; and the code checks and messages of the optional
repair call.

How it fits
-----------
run.py calls ``build_call`` for each (item, sample), hands the user text and
schema to a backend (backends.py, cloud_backend.py) and parses the reply with
``extract_json``. The default ("plain") builders are unchanged from the
earlier run.py, byte for byte, so older runs stay comparable. Standard library
only.
"""
import hashlib
import json
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES_DIR = os.path.join(HERE, "suites")
# Stems, escape phrases and hand-written synonyms for the open Pick arms (this module reads the stems,
# grade_open.py the rest). It lives with the suites and declares itself a sidecar, so nothing tries to run it as a suite.
OPEN_SIDECAR = os.path.join(SUITES_DIR, "pick-open-aliases.json")
# Suite name -> step shape. The shape picks the prompt builder, the schema, the temperature, the output cap
# and the system prompt, so several suites can share one shape: `pick-hard` (doc 44 §5.4 item 4) is a harder
# instrument for the same Pick step. Records and output files keep the suite's own name, so the two Pick
# suites score separately.
SUITE_SHAPE = {"knowledge": "knowledge", "pick": "pick", "pick-hard": "pick", "fill": "fill", "explain": "explain",
               "text": "text"}
SUITES = tuple(SUITE_SHAPE)

# Temperatures from the spike plan: sampled steps (pick/fill/text) run warmer
# because the harness draws K candidates and votes or validates; knowledge and
# explanations run cooler because they should be stable facts.
TEMPERATURE = {"pick": 0.6, "fill": 0.6, "text": 0.6, "knowledge": 0.2, "explain": 0.2}
# Output caps (tokens). Generous enough for each shape; a cap stops a small
# model that loops from burning minutes of GPU time (or money). Override with --num-predict.
# pick_open: an answer of at most eight words (the open arms' instruction) fits easily in 48.
NUM_PREDICT = {"pick": 64, "pick_why": 200, "pick_open": 48, "fill": 320, "text": 120, "knowledge": 700,
               "explain": 320}
PICK_LETTERS = "ABCDEFG"  # at most 7 real options per menu (doc 21 §3.2)
ESCAPE_LETTER = "X"

SYSTEM = {
    "knowledge": "Answer briefly; if unsure, say so.",
    "pick": ("You are the decision step of a mission editor for Arma: Cold War Assault (Operation Flashpoint). "
             "Code has already computed a menu of valid options. Choose the single best option for the request. "
             "If no option fits, choose X. Answer with JSON only."),
    "fill": ("You fill one small typed record for a mission editor for Arma: Cold War Assault. Use only what the "
             "request says; never invent. Answer with JSON only."),
    "explain": ("You explain one editor finding to a mission maker for Arma: Cold War Assault. Use only the finding, "
                "the mission facts and the reference card if one is given. Do not invent commands or behaviour. "
                "Answer with JSON only."),
    "text": ("You write one short line of in-world text for a Cold War military mission set in 1985. Follow every "
             "constraint exactly. Answer with JSON only."),
}
# The open Pick arms (P0 open, P1 labels): no menu is computed for the model, so the system prompt cannot
# mention one; the answer is a name, mapped to an option key later by grade_open.py.
SYSTEM_OPEN = ("You are the decision step of a mission editor for Arma: Cold War Assault (Operation Flashpoint). "
               "Answer with the name of one editor option only. If nothing fits, answer none.")

# ── Harness-uplift variants ──────────────────────────────────────────────────
# Each variant removes one harness mechanism from the default ("plain") request; see the module docs.
VARIANTS = {
    "pick": ("plain", "why", "open", "labels", "noschema"),
    "fill": ("plain", "noschema", "schematext"),
    "text": ("plain", "bare"),
    "explain": ("plain",),
    "knowledge": ("plain",),
}
OPEN_VARIANTS = ("open", "labels")
# Variants that may add one repair call (--repair); the record's variant gets a "-repair" suffix
# ("repair" alone for the plain request).
REPAIRABLE = {"pick": ("plain", "noschema"), "fill": ("plain", "noschema", "schematext")}
# --schema-mode is a readable alias for the schema variants.
SCHEMA_MODE_VARIANT = {"strict": "plain", "none": "noschema", "text": "schematext"}


# ── Suite loading and seeding ────────────────────────────────────────────────

def load_suite(name):
    """Load suites/<name>.json and return (suite dict, sha256 of the file)."""
    path = os.path.join(SUITES_DIR, name + ".json")
    with open(path, "rb") as f:
        raw = f.read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()[:16]


def load_sidecar(path=OPEN_SIDECAR):
    """Load the open-arm sidecar (stems, escape phrases, synonyms); returns (dict, sha256 prefix)."""
    with open(path, "rb") as f:
        raw = f.read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()[:16]


def sample_seed(item_id, sample):
    """Stable 31-bit seed per (item, sample); identical across conditions so runs pair up."""
    digest = hashlib.sha256(f"{item_id}|{sample}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) & 0x7FFFFFFF


def permute_options(item, sample):
    """Return the item's real options in a seeded order (escape excluded).

    random.Random seeded with a str hashes it with SHA-512 (seed version 2), so
    the order is reproducible across machines and Python 3 versions.
    """
    opts = list(item["options"])
    random.Random(f"perm|{item['id']}|{sample}").shuffle(opts)
    return opts


# ── Prompt builders (one per suite) ──────────────────────────────────────────

def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def card_block(item, condition):
    card = item.get("card")
    if condition == "cards" and card:
        return "\n\n[REFERENCE CARD]\n" + card
    return ""


def build_pick(item, condition, sample, why):
    return build_pick_order(item, condition, permute_options(item, sample), why)


def build_pick_order(item, condition, opts, why=False):
    """The lettered Pick prompt for the real options in the order `opts` (the escape is always last, as X).

    build_pick passes the seeded order of (item, sample); the logprob mode (logprob_pick.py) also passes rotations
    of it. Returns (user text, schema, extra record fields), the fields describing this order.
    """
    letters = PICK_LETTERS[: len(opts)]
    letter_to_key = {letter: opt["key"] for letter, opt in zip(letters, opts)}
    letter_to_key[ESCAPE_LETTER] = item["escape"]["key"]
    menu = "\n".join(f"{letter}) {opt['label']}: {opt['desc']}" for letter, opt in zip(letters, opts))
    menu += f"\n{ESCAPE_LETTER}) {item['escape']['label']}"
    enum = list(letters) + [ESCAPE_LETTER]
    if why:
        # Doc 21 §3.2: a short bounded reason comes before the answer.
        schema = {"type": "object",
                  "properties": {"why": {"type": "string", "maxLength": 160},
                                 "choice": {"type": "string", "enum": enum}},
                  "required": ["why", "choice"]}
        reply = 'Reply as {"why": "<one short reason>", "choice": "<letter>"}.'
    else:
        schema = {"type": "object", "properties": {"choice": {"type": "string", "enum": enum}},
                  "required": ["choice"]}
        reply = 'Reply as {"choice": "<letter>"}.'
    user = f"Request: {item['request']}{card_block(item, condition)}\n\nOptions:\n{menu}\n\n{reply}"
    answer = item["answer"]
    if answer == item["escape"]["key"]:
        correct_letter, correct_pos = ESCAPE_LETTER, len(opts)
    else:
        correct_pos = [o["key"] for o in opts].index(answer)
        correct_letter = letters[correct_pos]
    extra = {"letter_to_key": letter_to_key, "options_order": [o["key"] for o in opts],
             "n_options": len(opts), "correct_key": answer, "correct_letter": correct_letter,
             "correct_pos": correct_pos}
    return user, schema, extra


def open_stem(item, sidecar):
    """The one-line question an open arm asks: the item's own stem if the sidecar has one, else its category's."""
    per_item = {it.get("id"): it for it in sidecar.get("items", []) if isinstance(it, dict)}
    stem = (per_item.get(item["id"]) or {}).get("stem") or sidecar.get("category_stems", {}).get(item["category"])
    if not stem:
        raise KeyError(f"no open-arm stem for item {item['id']} (category {item['category']!r}) in the sidecar")
    return stem


def build_pick_open(item, condition, sample, variant, sidecar):
    """P0 (open): request + stem, no menu. P1 (labels): also the option names, without letters or descriptions.

    The names follow the same seeded permutation as the lettered menu of the same (item, sample), so every
    arm pairs item by item; the escape is never listed (the system prompt says to answer none).
    """
    opts = permute_options(item, sample)
    stem = open_stem(item, sidecar)
    user = f"Request: {item['request']}{card_block(item, condition)}\n\n{stem}"
    if variant == "labels":
        user += "\nValid names: " + ", ".join(o["label"] for o in opts)
    user += "\nAnswer in at most eight words."
    answer = item["answer"]
    correct_pos = len(opts) if answer == item["escape"]["key"] else [o["key"] for o in opts].index(answer)
    extra = {"options_order": [o["key"] for o in opts], "n_options": len(opts), "correct_key": answer,
             "correct_letter": None, "correct_pos": correct_pos, "stem": stem}
    return user, None, extra


def build_fill(item, condition, variant="plain"):
    if variant == "noschema":
        # F0: the field glossary only; no schema text and no response schema.
        user = (f"Request: \"{item['request']}\"{card_block(item, condition)}\n\n{item['instructions']}\n\n"
                "Answer with JSON only.")
        return user, None, {}
    user = (f"Request: \"{item['request']}\"{card_block(item, condition)}\n\n{item['instructions']}\n\n"
            f"JSON schema:\n{compact(item['schema'])}")
    # F1 (schematext): the same prompt, but the server is not told to enforce the schema.
    return user, (None if variant == "schematext" else item["schema"]), {}


def build_explain(item, condition):
    user = (f"Finding {item['code']} ({item['severity']}): {item['message']}\n"
            f"Mission facts: {item['context']}{card_block(item, condition)}\n\n"
            "Explain what is wrong and why in one sentence (explanation), and the fix in one sentence (fix). "
            "At most two sentences in total.\n\n"
            f"JSON schema:\n{compact(item['schema'])}")
    return user, item["schema"], {}


def build_text(item, condition, variant="plain"):
    if variant == "bare":
        # T0: the slot and its context only; the constraint list is the harness mechanism removed.
        user = (f"Slot: {item['slot']}\nContext: {item['context']}{card_block(item, condition)}\n\n"
                f"JSON schema:\n{compact(item['schema'])}")
        return user, item["schema"], {}
    c = item["constraints"]
    lines = [f"- at most {c['max_words']} words"]
    if c.get("names_check", True):
        names = ", ".join(c["allowed_names"]) if c["allowed_names"] else "none"
        lines.append(f"- names, callsigns and places you may use: {names}; use no other names")
    if c.get("no_digits"):
        lines.append("- no digits")
    lines.append(f"- era: {c['era']}")
    lines.append(f"- tone: {c['tone']}")
    user = (f"Slot: {item['slot']}\nContext: {item['context']}{card_block(item, condition)}\n\nConstraints:\n"
            + "\n".join(lines) + f"\n\nJSON schema:\n{compact(item['schema'])}")
    return user, item["schema"], {}


def build_knowledge(item, condition):
    return item["prompt"] + card_block(item, condition), None, {}


def build_call(suite, item, condition, sample, why, variant="plain", sidecar=None):
    """(user text, schema to enforce or None, extra record fields) for one call.

    `variant` is the base variant (without "-repair"); "plain" and "why" take exactly the earlier code paths.
    """
    if suite == "pick":
        if variant in OPEN_VARIANTS:
            return build_pick_open(item, condition, sample, variant, sidecar)
        user, schema, extra = build_pick(item, condition, sample, why)
        # P2 (noschema): the same lettered menu and reply line, but no response schema.
        return user, (None if variant == "noschema" else schema), extra
    if suite == "fill":
        return build_fill(item, condition, variant)
    if suite == "explain":
        return build_explain(item, condition)
    if suite == "text":
        return build_text(item, condition, variant)
    return build_knowledge(item, condition)


# ── Response parsing ─────────────────────────────────────────────────────────

def strip_think(content):
    """(answer text, True if reasoning was removed): drops ``<think>...</think>`` blocks and an unclosed leading
    ``<think>`` (a reply cut off while still thinking has no answer). A reasoning model, or a template that ignores
    the thinking switch, can put a draft answer inside the block; parsing the raw text would score that draft
    (``extract_json`` takes the first JSON object) instead of the final answer.

    Lives here (moved from run.py, which re-exports it) so the multi-call scaffold arms parse replies the same way."""
    text = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
    if text.lstrip().startswith("<think>"):
        text = ""
    return (text, True) if text != content else (content, False)


def extract_json(text):
    """Parse a JSON object from model text.

    Returns (obj or None, mode). Grammar-constrained output is normally plain
    JSON ("strict"); the fallback finds the first balanced {...} span, for
    runtimes or models that wrap output in a code fence ("extracted").
    """
    s = (text or "").strip()
    try:
        obj = json.loads(s)
        return (obj, "strict") if isinstance(obj, dict) else (None, "not_object")
    except (ValueError, TypeError):
        pass
    start = s.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for pos, ch in enumerate(s[start:], start):
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(s[start:pos + 1])
                        if isinstance(obj, dict):
                            return obj, "extracted"
                    except ValueError:
                        pass
                    break
        start = s.find("{", start + 1)
    return None, "failed"


# ── Repair checks (--repair) ─────────────────────────────────────────────────

# How a failing Fill validator is named in the repair message (the message names the field and the check,
# as a product validator would; it never gives the right answer).
VALIDATOR_WORDS = {
    "quote_in_request": "quoted text not found in the request",
    "max_chars": "longer than {value} characters",
    "max_words": "more than {value} words",
    "non_empty": "empty",
    "no_digits": "contains digits",
    "banned_words": "uses a word that does not fit the era",
    "names_from_request": "uses a name that is not in the request",
}


def check_failure(shape, item, suite_def, parsed, extra):
    """The first code check the answer fails, as a short message for the repair call, or None if it passes.

    Pick: the reply must be JSON naming one letter of the menu. Fill: the reply must be JSON, valid against the
    item's schema, and pass every validator of the item (score.py's own checks, so repair and scoring agree).
    """
    if shape == "pick":
        if parsed is None:
            return "the reply was not the JSON object asked for"
        choice = parsed.get("choice")
        letter = choice.strip().upper() if isinstance(choice, str) else None
        if not letter or letter not in extra.get("letter_to_key", {}):
            return "the choice was not one letter from the menu"
        return None
    if shape == "fill":
        from score import check_validator, validate_schema  # score.py is a sibling module with no side effects
        if parsed is None:
            return "the reply was not a JSON object"
        errs = validate_schema(parsed, item["schema"])
        if errs:
            return f"schema check failed: {errs[0]}"
        for v in item["validators"]:
            ok = check_validator(v, parsed.get(v["field"]), item["request"], suite_def.get("banned_words", []))
            if ok is False:
                return f"{v['field']}: " + VALIDATOR_WORDS.get(v["check"], v["check"]).format(value=v.get("value"))
        return None
    return None


def repair_message(shape, failure):
    if shape == "pick":
        return f'Your answer was rejected: {failure}. Answer with one letter from the menu, as {{"choice": "<letter>"}}.'
    return f"Your answer was rejected: {failure}. Answer again with the corrected JSON only."
