#!/usr/bin/env python3
"""Answer-blind reasoning scaffolds for the local-qual runner (``run.py --scaffold``; doc 59).

What it owns
------------
The pure parts of every scaffold arm: the text, schemas and decision rules that put *harness reasoning* in front of a
model, or use it in the model's place. Everything here is computed by code from facts the plain prompt already shows
(the request, the option labels and descriptions, the escape, and the reference card when the condition sends one).
Nothing here reads an item's answer, rationale or pool metadata: every function takes the **answer-blind view**
(``blind`` / ``blind_fill``), an allowlist copy of the item without those keys, so an answer-dependent scaffold cannot be
written by accident (doc 59 §5.1, test T-L1).

Arms (``--scaffold``), with doc 59's ids:

* ``why`` (S3): a bounded rationale field before the letter, 40-160 characters, both ends enforced by the schema.
* ``diff`` (S1): code-computed lines saying how the closest options differ in wording (``diff_block``).
* ``rule`` (S2): the one card sentence selected by lexical overlap with the request, in place of the whole card
  (``select_rule_sentence``).
* ``eliminate`` (S5): letter probabilities from one forward pass, keep the top k plus X, re-ask (``keep_top``).
* ``pairwise`` (S6): a round robin over the top m options, each pair asked in both orders (``pair_schedule``,
  ``aggregate_pairwise``).
* ``subq`` (S7-like): yes/no/unclear statements taken from the option clauses, aggregated by a code rule table
  (``subq_statements``, ``aggregate_subq``).
* ``prefill`` (S4): the diff lines placed at the start of the assistant turn, in the visible answer or inside the empty
  think block (``prefill_prompt``), continued under a menu-letter grammar (``continuation_grammar``).
* ``quote-first`` (S8, Fill): each quote-checked field gets a ``<field>_quote`` property generated first; code checks
  that the quote is verbatim (``quote_first_schema``, ``quote_first_post``).

How it fits
-----------
run.py builds the one-call arms (why, diff, rule, quote-first) through ``build_prompt_arm``; scaffold_run.py runs the
multi-call arms (eliminate, pairwise, subq, prefill) and calls the aggregation functions here. Standard library only;
no function here does I/O, so the same inputs always give the same text (test T-L9).
"""
import hashlib
import json
import random
import re

from prompts import ESCAPE_LETTER, PICK_LETTERS, card_block, compact
# The menu-independent algorithms live in scaffold_algos.py; re-exported because scaffold_run.py and the tests read
# them from this module.
from scaffold_algos import (DIFF_HEADING, MAX_PHRASES, STOPWORDS, _norm_text, _norm_token, _phrase,  # noqa: F401
                            _quote_list, _similarity, aggregate_pairwise, card_sentences, content_stems, diff_phrases,
                            keep_top, nearest_pairs, pair_schedule, rank_real, rule_card_text, select_rule_sentence,
                            stem)

# Bumped whenever a template, algorithm or aggregation rule below changes, so records made with different scaffold
# code never pool silently (each record carries it under scaffold.version).
# 2: the prefill tail restates the Pick system prompt's rule (version 1 asked for an option that "fits every part of
#    the request", a stricter, X-leaning test the diff arm does not get); quote-first keeps a field the quote_in_request
#    validator accepts (version 1 replaced any field that was not a byte-exact substring); a blank quote never counts.
SCAFFOLD_VERSION = "2"

PICK_ARMS = ("why", "diff", "rule", "eliminate", "pairwise", "subq", "prefill")
FILL_ARMS = ("quote-first",)
ARMS = ("none",) + PICK_ARMS + FILL_ARMS
# One request, built by build_prompt_arm and sent through run.py's normal call path.
PROMPT_ARMS = ("why", "diff", "rule", "quote-first")
# Several requests per decision, run by scaffold_run.ScaffoldRunner.
PROCEDURE_ARMS = ("eliminate", "pairwise", "subq", "prefill")
# These read letter probabilities (/completion with n_probs) or send a raw /completion: llama-server only.
LLAMACPP_ONLY = ("eliminate", "pairwise", "prefill")
LOGPROB_ARMS = ("eliminate", "pairwise")

# ── The answer-blind view ────────────────────────────────────────────────────
# Allowlists, not denylists: a new metadata field added to a suite (split, traits, escape_kind, lures, twin...) stays
# out of every scaffold until someone adds it here on purpose.
PICK_VIEW_KEYS = ("id", "category", "request", "options", "escape", "card")
FILL_VIEW_KEYS = ("id", "kind", "request", "instructions", "schema", "validators", "card")
OPTION_KEYS = ("key", "label", "desc")


def _copy(value):
    """A deep copy through JSON, so a scaffold can never mutate the suite item it was given."""
    return json.loads(json.dumps(value))


def blind(item):
    """The answer-blind view of a Pick item: request, options (key, label, desc), escape, card, id and category.

    The option keys stay because code maps letters back to keys; they are never rendered into any text (the leakage
    tests check that no snake_case key appears in a scaffold)."""
    view = {k: _copy(item[k]) for k in PICK_VIEW_KEYS if k in item and k not in ("options", "escape")}
    view["options"] = [{k: o[k] for k in OPTION_KEYS if k in o} for o in item.get("options", [])]
    if "escape" in item:
        view["escape"] = {k: item["escape"][k] for k in OPTION_KEYS if k in item["escape"]}
    return view


def blind_fill(item):
    """The answer-blind view of a Fill item: request, instructions, schema, validators and card; never ``expected``,
    ``note``, ``lures``, ``tags`` or pool metadata. Validators stay: they are code checks (which field is quote-checked,
    word caps), not answers."""
    return {k: _copy(item[k]) for k in FILL_VIEW_KEYS if k in item}


def text_sha(text):
    """Short SHA-256 of a rendered scaffold, stored in every record (doc 59 §5.4: the id and hash, not only the text)."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


# ── The plain Pick prompt, rebuilt from the view ─────────────────────────────

REPLY = 'Reply as {"choice": "<letter>"}.'
# The bounded rationale of the why arm (doc 59 S3): 40-160 characters, both ends enforced by the schema. The legacy
# --why sets only maxLength 160; a bounded arm needs both ends (doc 59, findings for sibling docs, item 5).
WHY_MIN, WHY_MAX = 40, 160
REPLY_WHY = f'Reply as {{"why": "<one short reason, {WHY_MIN}-{WHY_MAX} characters>", "choice": "<letter>"}}.'


def menu(view, opts):
    """(letters, {letter: key}, menu text) for the real options in the order `opts`, the escape last as X.

    Byte-for-byte the menu prompts.build_pick_order renders (a regression test compares every item and order)."""
    letters = PICK_LETTERS[: len(opts)]
    letter_to_key = {letter: opt["key"] for letter, opt in zip(letters, opts)}
    letter_to_key[ESCAPE_LETTER] = view["escape"]["key"]
    text = "\n".join(f"{letter}) {opt['label']}: {opt['desc']}" for letter, opt in zip(letters, opts))
    text += f"\n{ESCAPE_LETTER}) {view['escape']['label']}"
    return letters, letter_to_key, text


def pick_schema(letters, why=False):
    """The Pick response schema; with ``why`` the bounded rationale comes first in properties and in ``required``
    (under constrained decoding the property order is the generation order, so a reason after the letter could not
    change it: doc 59 §2.3)."""
    enum = list(letters) + [ESCAPE_LETTER]
    if why:
        return {"type": "object",
                "properties": {"why": {"type": "string", "minLength": WHY_MIN, "maxLength": WHY_MAX},
                               "choice": {"type": "string", "enum": enum}},
                "required": ["why", "choice"]}
    return {"type": "object", "properties": {"choice": {"type": "string", "enum": enum}}, "required": ["choice"]}


def pick_user(view, condition, opts, block="", reply=REPLY, card_text=None):
    """(user text, schema, {letter: key}) of a lettered Pick over `opts`.

    With the defaults this is exactly the plain request. `block` is inserted after the menu and before the reply line
    (the dynamic tail; doc 40 R2); `card_text`, when given, replaces the card block (the rule arm)."""
    letters, letter_to_key, text = menu(view, opts)
    card = card_block(view, condition) if card_text is None else card_text
    user = f"Request: {view['request']}{card}\n\nOptions:\n{text}{block}\n\n{reply}"
    return user, pick_schema(letters, why=reply == REPLY_WHY), letter_to_key


def seeded_order(view, keys, tag, sample):
    """The option dicts for `keys` in a fresh seeded order for a follow-up call (tag names the phase).

    Seeded like prompts.permute_options (a str seed hashes with SHA-512), on the item id, the phase and the sample
    only, so the order never depends on the answer and a rerun reproduces it."""
    by_key = {o["key"]: o for o in view["options"]}
    opts = [by_key[k] for k in keys]
    random.Random(f"{tag}|{view['id']}|{sample}").shuffle(opts)
    return opts


# ── diff (S1): the lines, in menu order ─────────────────────────────────────
# The pairs and phrases come from scaffold_algos.py (nearest_pairs, diff_phrases; the algorithm is described there);
# only the letters are added here, from the menu the prompt shows.

def diff_lines(view, opts):
    """The diff arm's lines for the real options in menu order `opts` (scaffold_algos.py), without the heading."""
    letters, _, _ = menu(view, opts)
    letter_of = {o["key"]: letter for letter, o in zip(letters, opts)}
    by_key = {o["key"]: o for o in opts}
    rendered = []
    for k1, k2 in nearest_pairs(opts):
        # Render in menu order: the earlier letter first, so the lines read top to bottom like the menu.
        a, b = sorted((by_key[k1], by_key[k2]), key=lambda o: letter_of[o["key"]])
        pa, pb = diff_phrases(a, b)
        la, lb = letter_of[a["key"]], letter_of[b["key"]]
        rendered.append(((la, lb), f"- {la}) {a['label']} vs {lb}) {b['label']}: only {la} has {_quote_list(pa)}; "
                                   f"only {lb} has {_quote_list(pb)}."))
    return [line for _, line in sorted(rendered, key=lambda x: x[0])]


def diff_block(view, opts):
    """The diff text inserted after the menu (with its heading), or "" for a menu of fewer than two options."""
    lines = diff_lines(view, opts)
    return ("\n\n" + DIFF_HEADING + "\n" + "\n".join(lines)) if lines else ""


# ── subq (S7-like): statements from option clauses, aggregated by code ───────
# Statements: each real option's description split at ";" into clauses (commas stay inside a clause, because many
# descriptions list items with commas). Identical clauses (after _norm_text) become one statement shared by every option
# that has it. Statements follow the seeded menu order, so they carry no ranking; option labels are not shown, so the
# model judges what each clause says, not which option it belongs to.
# Aggregation rule table (code, per option over its statements):
#   any "no"                            -> the option is eliminated
#   no option left                      -> X (decided by code)
#   one survivor with the most "yes"    -> that option (decided by code), when its yes count is at least 1
#   otherwise (a tie at the top, or no "yes" among survivors)
#                                       -> one final Pick over the tied top survivors (all survivors when none has a yes)
#                                          plus X, in a fresh seeded order
# A reply that does not parse, or misses a statement, is no decision (wrong, not an error), as in the plain arm.
SUBQ_VALUES = ("yes", "no", "unclear")
# The subq call's own system prompt: the Pick system prompt speaks of choosing one option, which this call does not do
# (the final Pick, when the rule table ties, keeps the Pick system prompt).
SUBQ_SYSTEM = ("You check requests for a mission editor for Arma: Cold War Assault (Operation Flashpoint). For each "
               "statement, say whether the request needs it. Answer with JSON only.")
SUBQ_INSTRUCTION = ('For each statement below, answer "yes" if the request needs it, "no" if the request rules it out '
                    'or needs something different, and "unclear" if the request does not say.')


def option_clauses(opt):
    """The clauses of an option's description (split at ';'), stripped, empty ones dropped."""
    return [c.strip() for c in opt["desc"].split(";") if c.strip()]


def subq_statements(opts):
    """(statements, {statement id: [option keys]}): distinct clauses in menu order, ids s1, s2, ..."""
    statements, owners, seen = [], {}, {}
    for o in opts:
        for clause in option_clauses(o):
            norm = _norm_text(clause)
            if norm not in seen:
                sid = f"s{len(statements) + 1}"
                seen[norm] = sid
                statements.append((sid, clause))
                owners[sid] = []
            if o["key"] not in owners[seen[norm]]:
                owners[seen[norm]].append(o["key"])
    return statements, owners


def subq_user(view, condition, opts):
    """(user text, schema, statements, owners) of the subq call. The menu is not shown: only the statements."""
    statements, owners = subq_statements(opts)
    lines = "\n".join(f"{sid}: {text}" for sid, text in statements)
    reply = "Reply as {" + ", ".join(f'"{sid}": "yes|no|unclear"' for sid, _ in statements) + "}."
    user = f"Request: {view['request']}{card_block(view, condition)}\n\n{SUBQ_INSTRUCTION}\n{lines}\n\n{reply}"
    schema = {"type": "object",
              "properties": {sid: {"type": "string", "enum": list(SUBQ_VALUES)} for sid, _ in statements},
              "required": [sid for sid, _ in statements], "additionalProperties": False}
    return user, schema, statements, owners


def subq_cap(n_statements):
    """Output cap for the subq reply: about 7 tokens per '"sN": "unclear", ' plus the braces, with headroom for a
    template that pretty-prints or fences JSON (Gemma 4 adds about 9 tokens per reply, doc 59 findings item 2)."""
    return 32 + 10 * n_statements


def aggregate_subq(parsed, statements, owners, order_keys):
    """(decision, detail) by the rule table above. decision is ("key", k), ("escape", None), ("final", [keys]) or
    ("none", None) when the reply is unusable."""
    ids = [sid for sid, _ in statements]
    if not isinstance(parsed, dict) or any(parsed.get(sid) not in SUBQ_VALUES for sid in ids):
        return ("none", None), {"rule": "unparsed"}
    per = {k: {"yes": 0, "no": 0, "unclear": 0, "n": 0} for k in order_keys}
    for sid in ids:
        for k in owners.get(sid, []):
            if k in per:
                per[k][parsed[sid]] += 1
                per[k]["n"] += 1
    survivors = [k for k in order_keys if per[k]["no"] == 0]
    detail = {"per_option": per, "survivors": survivors}
    if not survivors:
        detail["rule"] = "no_survivor"
        return ("escape", None), detail
    top = max(per[k]["yes"] for k in survivors)
    tied = [k for k in survivors if per[k]["yes"] == top]
    if top >= 1 and len(tied) == 1:
        detail["rule"] = "unique_top"
        return ("key", tied[0]), detail
    detail["rule"] = "tie_final_pick" if top >= 1 else "no_yes_final_pick"
    return ("final", tied if top >= 1 else survivors), detail


# ── prefill (S4): a code-built skeleton at the start of the assistant turn ───
# Template handling (documented in scaffold_run.py as well):
# * The prompt is rendered by llama-server's POST /apply-template from the plain request's own chat body (messages,
#   response_format, chat_template_kwargs.enable_thinking=false, model), exactly as the logprob mode renders it, so the
#   rendered prompt ends with the template's generation prefix for a thinking-off answer.
# * content channel: skeleton + ANSWER_PREFIX are appended after that prefix; they become the first words of the
#   model's visible answer. Works with any template, because nothing template-specific is edited.
# * think channel: only when the rendered prompt ends with the empty think block EMPTY_THINK (the Qwen3 / Qwen3.5
#   templates render it when thinking is off); the block is replaced by "<think>\n" + skeleton + "\n</think>\n\n" and
#   ANSWER_PREFIX follows. Any other template is refused (the preflight stops the run), never edited by guesswork.
# * The continuation is generated by POST /completion under continuation_grammar: exactly one menu letter or X, then
#   the closing '"}'. No response_format goes to /completion (a JSON-schema grammar would demand a fresh "{" where the
#   prefill has already opened the object).
ANSWER_PREFIX = '{"choice": "'
EMPTY_THINK = "<think>\n\n</think>\n\n"
PREFILL_HEAD = "Before answering, the editor lists how the closest options differ:"
# The tail restates the Pick system prompt ("Choose the single best option for the request. If no option fits, choose
# X.") and nothing more, so the prefill arm differs from the diff arm only in where the diff lines sit (the assistant
# turn instead of the user turn). A stricter wording ("fits every part of the request") would add an X-leaning
# instruction of its own and confound the channel comparison; such wording is a separate framing arm (doc 59 S12).
PREFILL_TAIL = "Now pick the single best option for the request; X if no option fits."
PREFILL_CAP = 8  # one letter and '"}' are 2-3 tokens; 8 leaves room for a tokenizer that splits the tail


def prefill_skeleton(view, opts):
    """The code-built text of the prefill arm: the diff lines of this menu between a fixed head and tail.

    The tail restates the Pick step's general rule (see PREFILL_TAIL); it names no option, so it is a card-style rule,
    not a verdict (doc 59 §5.1 item 5)."""
    lines = diff_lines(view, opts)
    return PREFILL_HEAD + "\n" + "\n".join(lines) + "\n" + PREFILL_TAIL


def prefill_prompt(rendered, skeleton, channel):
    """(full /completion prompt, None) or (None, why not) for the rendered template prompt and the channel."""
    if channel == "content":
        return rendered + skeleton + "\n" + ANSWER_PREFIX, None
    if channel == "think":
        if not rendered.endswith(EMPTY_THINK):
            return None, ("the rendered prompt does not end with an empty think block "
                          f"({EMPTY_THINK!r}); the think channel needs a Qwen3-style template with thinking off")
        return rendered[: -len(EMPTY_THINK)] + "<think>\n" + skeleton + "\n</think>\n\n" + ANSWER_PREFIX, None
    return None, f"unknown prefill channel {channel!r}"


def continuation_grammar(letters):
    """GBNF for the continuation after ANSWER_PREFIX: one of `letters` (the menu's letters and X), then '"}'."""
    alts = " | ".join(f'"{letter}"' for letter in letters)
    return f'root ::= ({alts}) "\\"}}"'


# ── quote-first (S8, Fill) ───────────────────────────────────────────────────
# Each field checked by a "quote_in_request" validator gets a "<field>_quote" property placed before every other
# property (and first in "required"), so under constrained decoding the model copies the span before it fills the
# record. Code then checks the quote is verbatim: an exact, case-sensitive substring of the request ("" only where the
# validator allows an empty value; a blank quote such as " " never counts, although it is a substring of almost any
# request). The final record keeps the model's own field whenever the item's quote_in_request validator accepts it
# (in_request: the same normalised containment as score.py's check_validator, so a correct span in another case or
# with a trailing full stop is not overwritten); when the validator would reject it and the quote is verbatim, the
# quote replaces it (the model's copy step wins over its paraphrase). The "_quote" keys are removed from the scored
# record, so score.py validates it against the item's own schema unchanged.
QUOTE_SUFFIX = "_quote"
QUOTE_CAP = 400  # fill's 320 plus about 25 tokens for each of up to three quotes


def span_fields(view):
    """The quote-checked fields of a Fill item, in the schema's property order, with their allow_empty flags."""
    allow = {}
    for v in view.get("validators", []):
        if v.get("check") == "quote_in_request":
            allow[v["field"]] = allow.get(v["field"], False) or bool(v.get("allow_empty"))
    order = list(view["schema"].get("properties", {}))
    return [(f, allow[f]) for f in order if f in allow] + [(f, a) for f, a in allow.items() if f not in order]


def quote_first_schema(view):
    """The item schema with one "<field>_quote" string property per span field, placed first."""
    schema = view["schema"]
    props = {}
    for f, _ in span_fields(view):
        sub = {"type": "string"}
        if "maxLength" in schema["properties"].get(f, {}):
            sub["maxLength"] = schema["properties"][f]["maxLength"]
        props[f + QUOTE_SUFFIX] = sub
    props.update(schema.get("properties", {}))
    out = {k: v for k, v in schema.items() if k not in ("properties", "required")}
    out["type"] = "object"
    out["properties"] = props
    out["required"] = [f + QUOTE_SUFFIX for f, _ in span_fields(view)] + list(schema.get("required", []))
    out["additionalProperties"] = False
    return out


def quote_first_lines(view):
    """The glossary lines appended to the item's instructions, one per span field."""
    lines = []
    for f, allow_empty in span_fields(view):
        tail = '; "" if the request has none.' if allow_empty else "."
        lines.append(f"- {f}{QUOTE_SUFFIX}: fill this first. Copy, character for character, the words of the request "
                     f"that {f} needs{tail}")
    return "\n".join(lines)


def quote_first_user(view, condition):
    """(user text, schema) of the quote-first Fill: the plain Fill prompt with the quote lines and the quote schema."""
    schema = quote_first_schema(view)
    user = (f"Request: \"{view['request']}\"{card_block(view, condition)}\n\n{view['instructions']}\n"
            f"{quote_first_lines(view)}\n\nJSON schema:\n{compact(schema)}")
    return user, schema


def verbatim(value, request, allow_empty):
    """True when `value` is an exact substring of the request ("" only when allowed; never a blank like " ")."""
    if not isinstance(value, str):
        return False
    if not value.strip():
        return value == "" and bool(allow_empty)
    return value in request


def _norm_span(text):
    """score.py's norm_span, mirrored (scaffolds.py imports nothing from the scorer): lower case, runs of whitespace
    collapsed, surrounding punctuation and quotes trimmed. A test checks the two agree."""
    s = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    return s.strip(" .,;:!?\"'`")


def in_request(value, request, allow_empty):
    """True when the item's quote_in_request validator accepts `value` (score.py check_validator, mirrored)."""
    if not isinstance(value, str):
        return False
    if value.strip() == "":
        return bool(allow_empty)
    return _norm_span(value) in _norm_span(request)


def quote_first_post(parsed, view):
    """(record for scoring, detail) from a quote-first reply; see the rule above. `parsed` None gives (None, {})."""
    if not isinstance(parsed, dict):
        return None, {}
    fields = span_fields(view)
    names = {f + QUOTE_SUFFIX for f, _ in fields}
    record = {k: v for k, v in parsed.items() if k not in names}
    detail = {}
    for f, allow_empty in fields:
        q = parsed.get(f + QUOTE_SUFFIX)
        v = parsed.get(f)
        q_ok = verbatim(q, view["request"], allow_empty)
        v_ok = in_request(v, view["request"], allow_empty)
        replaced = (not v_ok) and q_ok
        if replaced:
            record[f] = q
        cap = view["schema"]["properties"].get(f, {}).get("maxLength")
        detail[f] = {"quote": q, "quote_verbatim": q_ok, "model_value": v, "value_in_request": v_ok,
                     "value_verbatim": verbatim(v, view["request"], allow_empty), "replaced": replaced,
                     "quote_at_cap": isinstance(q, str) and cap is not None and len(q) >= cap}
    return record, detail


# ── One-call arms: the request of run.py's normal path ───────────────────────

def build_prompt_arm(arm, item, condition, opts=None):
    """(user text, schema, scaffold info) of a one-call arm for `item` (a full suite item: it is blinded here first).

    Pick arms need `opts`, the sample's seeded option order (prompts.permute_options), so the menu is the one the
    plain request of the same (item, sample) shows. The caller's option dicts come from the full item, so only their
    order is used: each is replaced by the view's copy of the same key (key, label, desc), and no other field of a
    suite's option object can reach a scaffold. The info holds the arm, the version, the scaffold text and its hash,
    and arm details; run.py adds the per-call tokens and latency."""
    if arm == "quote-first":
        view = blind_fill(item)
        user, schema = quote_first_user(view, condition)
        text = quote_first_lines(view)
        return user, schema, {"arm": arm, "version": SCAFFOLD_VERSION, "text": text, "text_sha": text_sha(text),
                              "span_fields": [f for f, _ in span_fields(view)]}
    view = blind(item)
    by_key = {o["key"]: o for o in view["options"]}
    opts = [by_key[o["key"]] for o in opts]
    info = {"arm": arm, "version": SCAFFOLD_VERSION}
    if arm == "why":
        user, schema, _ = pick_user(view, condition, opts, reply=REPLY_WHY)
        text = REPLY_WHY
    elif arm == "diff":
        block = diff_block(view, opts)
        user, schema, _ = pick_user(view, condition, opts, block=block)
        text = block.strip("\n")
    elif arm == "rule":
        sentence, detail = select_rule_sentence(view)
        user, schema, _ = pick_user(view, condition, opts, card_text=rule_card_text(sentence))
        text = sentence or ""
        info["rule"] = detail
    else:
        raise ValueError(f"{arm!r} is not a one-call scaffold arm")
    info.update(text=text, text_sha=text_sha(text))
    return user, schema, info
