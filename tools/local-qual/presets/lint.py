#!/usr/bin/env python3
"""Standard-library checker for harness presets (tools/local-qual/presets; D048, doc 55 section 3).

What it owns
------------
1. ``validate``: a JSON Schema subset validator (type, const, enum, pattern, minimum, maximum, minItems, maxItems,
   required, properties, additionalProperties false, items, $ref, oneOf, allOf) that returns one readable finding
   per problem; an unknown key's finding lists the keys allowed there. ``format`` is not checked.
2. ``read_preset``: reads one file strictly. A preset shapes every request of a run, so anything that would read
   differently than it looks is refused: more than ``MAX_PRESET_BYTES``, bytes that are not UTF-8, a duplicate key
   (JSON parsers keep the last one silently), NaN or Infinity (NaN compares false with every bound, so it would pass
   each range check), or a value that is not one object.
3. ``load``: a preset with its bases. ``extends`` names a base as ``id@version``, looked up among the ``*.json`` files
   in the preset's own folder; bases are merged root first (``merge_onto``), and the result carries the SHA-256 of
   the file and of every base read, so a record can name the exact bytes behind its requests.
4. ``invariants``: the loader rules the schema cannot express, ported from the staged draft checker (neutral Pick and
   Fill penalties, D022 amendment item 5; no step-shape grant; K and R ceilings; only the default binds to any; every
   other preset extends a base; a null template hash only in a draft) plus the rules the schema's own description
   names (native tool calls and validator-only schema modes only on cloud endpoints, the sidecar's grammars only
   locally, no route to an undecided second stage), a layout id after merging, and decision overrides checked as the
   step settings they become (the schema leaves their ``settings`` free-form).
5. ``main``: ``python tools/local-qual/presets/lint.py [FILE ...]`` checks the given files (default: every draft)
   and exits 1 when any has a finding.

How it fits
-----------
run_preset.py loads a preset through ``load`` for ``run.py --preset`` and refuses one with any finding, so the checker
and the runner never disagree. The negative controls that prove each rule refuses its violation are unit tests
(tests/test_presets.py). Not ported from the staged checker: the knob-ledger and tuning-plan checks, the rules that
need facts read from GGUF headers (a documents channel or an enable_thinking switch only on a template that has one),
and the rule that verbatim spans need the compact grammar (the 0.1.0 Qwen draft predates it; run_preset.py refuses
both knobs anyway). They arrive with the 0.2.0 presets that carry ledgers and pins (doc 55 section 3.3).

Every finding and every ``PresetError`` says what to change ("Fix: ..."). Standard library only, like the rest of
the tool; this is research tooling, not product code.
"""
import copy
import glob
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "schema", "harness-preset.schema.json")
DRAFTS_DIR = os.path.join(HERE, "drafts")
# Parser-safety cap on one preset file. The drafts are 3-5 KB and doc 55's draft-2 files with knob ledgers 25-37 KB;
# a larger file is not a preset, and the cap bounds what a stray or hostile file can make the checker read.
MAX_PRESET_BYTES = 256 * 1024
# Longest extends chain (bases read for one preset). The format expects one level (a model preset extends the
# default); eight leaves room for local custom presets on top while bounding the reads of a runaway chain.
MAX_CHAIN = 8
# The Thorough effort level's K (samples) and the repair ceiling R; the runtime clamps both further to the chosen
# effort level (doc 55 section 3.3, "k_max", "r_max").
THOROUGH_K, MAX_R = 5, 3
STEP_KINDS = ("pick", "fill", "compose", "text", "explain")
# Schema modes that only validate after the fact: for cloud endpoints that enforce no schema (a local runtime always
# can enforce a grammar).
VALIDATOR_ONLY = ("json_mode_validate", "none_validate")
# Keys by which a preset might try to grant itself a step shape; shape grants come only from qualification records.
GRANT_KEYS = ("granted", "grant", "shape")
_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


class PresetError(ValueError):
    """A preset file that cannot be read or resolved at all (unreadable, not one JSON object, too large, a missing,
    ambiguous or circular base). The message names the file and ends with the fix. Findings about a readable preset's
    content are not raised: ``load`` returns them in ``errors``."""


# ── The schema subset validator ──────────────────────────────────────────────

def load_schema(path=SCHEMA_PATH):
    """The harness-preset JSON Schema (draft 2 of doc 55 section 3.3)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _resolve(ref, root):
    """The schema node a local ``#/$defs/...`` reference points to."""
    node = root
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def _is_type(value, t):
    # JSON true and false are ints in Python; the schema's integers and numbers never mean booleans.
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[t])


def validate(value, schema, root, path="$"):
    """Findings (strings, ``"<path>: <problem>"``) for `value` against `schema`; [] when it conforms.

    ``root`` is the whole schema, for ``$ref``. Deterministic: the same input always gives the same list in the same
    order. A oneOf that matches no branch reports the closest branch's first findings, so a binding with one wrong
    field says which field, not only that no branch matched."""
    errs = []
    if "$ref" in schema:
        errs += validate(value, _resolve(schema["$ref"], root), root, path)
    for sub in schema.get("allOf", ()):
        errs += validate(value, sub, root, path)
    if "oneOf" in schema:
        results = [validate(value, s, root, path) for s in schema["oneOf"]]
        ok = sum(1 for r in results if not r)
        if ok == 0:
            closest = min(results, key=len)
            errs.append(f"{path}: matches none of the {len(results)} oneOf branches; closest: "
                        + "; ".join(closest[:3]))
        elif ok > 1:
            errs.append(f"{path}: matches {ok} oneOf branches (want exactly 1)")
    if "const" in schema and value != schema["const"]:
        errs.append(f"{path}: {value!r} != const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not in {schema['enum']}")
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(value, t) for t in types):
            errs.append(f"{path}: type {type(value).__name__} not in {types}")
            return errs
    if isinstance(value, float) and not math.isfinite(value):
        # read_preset refuses NaN and Infinity; this guards a dict built in memory.
        errs.append(f"{path}: {value!r} is not a finite number")
        return errs
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        errs.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errs.append(f"{path}: {value} > maximum {schema['maximum']}")
    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errs.append(f"{path}: missing required '{req}'")
        props = schema.get("properties", {})
        for key, sub in value.items():
            if key in props:
                errs += validate(sub, props[key], root, f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unknown key {key!r} (allowed: {', '.join(props)})")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: more than {schema['maxItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                errs += validate(item, schema["items"], root, f"{path}[{i}]")
    return errs


# ── Merging a diff onto its base ─────────────────────────────────────────────

def deep_merge(base, diff):
    """`diff` applied onto a deep copy of `base`: objects merge key by key, anything else (lists included) replaces."""
    out = copy.deepcopy(base)
    for key, val in diff.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


# Fields that describe one file, not a setting: the merged view takes them from the preset itself, never from its
# base (a base's binding, status or badges are not the child's). decision_overrides are settings and are inherited.
_OWN_FIELDS = ("preset_id", "version", "status", "extends", "binds_to", "provenance", "badges", "notes")


def merge_onto(base, preset):
    """The settings a diff `preset` describes once applied onto `base` (a base preset or an already merged chain).

    Identity fields come from `preset` alone (``_OWN_FIELDS``); the knob ledger is dropped, since it explains one
    file's choices and is not a setting."""
    merged = deep_merge(base, preset)
    for key in _OWN_FIELDS:
        if key in preset:
            merged[key] = copy.deepcopy(preset[key])
        else:
            merged.pop(key, None)
    merged.pop("knob_ledger", None)
    return merged


# ── Loader rules the schema cannot express ───────────────────────────────────

def _step_rules(step, s, bind_kind):
    """(knob sub-path, problem) pairs for one step kind's settings `s` under a binding of kind `bind_kind`."""
    found = []

    def sub(key):
        v = s.get(key)
        return v if isinstance(v, dict) else {}

    for key in GRANT_KEYS:
        if key in s:
            found.append((key, "a preset cannot grant a step shape; shape grants come only from qualification "
                               "records (doc 21 section 3.3). Fix: remove the key"))
    k_max = sub("voting").get("k_max")
    if isinstance(k_max, int) and k_max > THOROUGH_K:
        found.append(("voting.k_max", f"{k_max} is above the Thorough ceiling of {THOROUGH_K} (the runtime clamps "
                                      f"it further to the chosen effort level). Fix: set it to {THOROUGH_K} or less"))
    r_max = sub("repair").get("r_max")
    if isinstance(r_max, int) and r_max > MAX_R:
        found.append(("repair.r_max", f"{r_max} is above the repair ceiling of {MAX_R}. Fix: set it to {MAX_R} or "
                                      f"less"))
    if "layout" in s and "id" not in sub("layout"):
        found.append(("layout", "no layout id after merging onto the base; the runtime renders only named layouts "
                                "(DG019). Fix: set layout.id, or extend a base that sets it"))
    if sub("cascade").get("route") == "bound_second_stage":
        found.append(("cascade.route", "'bound_second_stage' is refused until the two-stage role binding is decided "
                                       "(doc 55 section 7 item 9). Fix: use user_card, code_default, same_model_reask "
                                       "or none"))
    if sub("answer").get("transport") == "native_tool_call" and bind_kind != "cloud-endpoint":
        found.append(("answer.transport", "native_tool_call is allowed only on a cloud endpoint (doc 55 section "
                                          "1.4). Fix: use response_format"))
    mode = s.get("schema_mode")
    if bind_kind == "local-gguf" and mode in VALIDATOR_ONLY:
        found.append(("schema_mode", f"{mode} is for cloud endpoints that enforce no schema; a local runtime always "
                                     f"enforces one. Fix: use json_schema_strict (or gbnf_compact)"))
    if bind_kind == "cloud-endpoint" and mode == "gbnf_compact":
        found.append(("schema_mode", "gbnf_compact needs the local sidecar's grammar, which a cloud endpoint cannot "
                                     "take. Fix: use json_schema_strict, or a validator-only mode where the endpoint "
                                     "enforces no schema"))
    if bind_kind == "cloud-endpoint" and sub("decomposition").get("spans") == "verbatim_grammar":
        found.append(("decomposition.spans", "verbatim_grammar needs the local sidecar's per-request grammar. Fix: "
                                             "use free_quote_checked (the quote check) on a cloud endpoint"))
    return found


def _fmt(where, found):
    return [f"{where}.{k}: {text}" if k else f"{where}: {text}" for k, text in found]


def invariants(p, merged, schema):
    """Findings of the loader rules for preset `p`, whose settings merged onto its bases are `merged`.

    Call it on a preset that passed the schema; each finding names its knob and ends with the fix."""
    errs = []
    bind = p.get("binds_to") if isinstance(p.get("binds_to"), dict) else {}
    kind = bind.get("kind")
    if kind == "any" and p.get("preset_id") != "default":
        errs.append("$.binds_to: only the default preset may bind to 'any' (D048 item 7: it is the general "
                    "fallback). Fix: bind this preset to its model file (kind local-gguf) or endpoint (kind "
                    "cloud-endpoint)")
    if p.get("preset_id") != "default" and "extends" not in p:
        errs.append("$.extends: missing; every preset except the default is a diff of a base (doc 55 section 3.1). "
                    "Fix: add \"extends\": \"default@<version>\"")
    if kind == "local-gguf" and bind.get("chat_template_sha256") is None and p.get("status") != "draft":
        errs.append("$.binds_to.chat_template_sha256: null is allowed only while status is 'draft'. Fix: read the "
                    "template hash from the GGUF header (tokenizer.chat_template), or set status back to 'draft'")
    steps = merged.get("step_kinds") if isinstance(merged.get("step_kinds"), dict) else {}
    for step in ("pick", "fill"):
        s = (steps.get(step) or {}).get("sampler") if isinstance(steps.get(step), dict) else None
        if isinstance(s, dict) and s and (s.get("presence_penalty") != 0 or s.get("frequency_penalty") != 0
                                          or s.get("repeat_penalty") != 1):
            errs.append(f"$.step_kinds.{step}.sampler: penalties must be neutral (presence 0, frequency 0, repeat 1) "
                        f"for Pick and Fill (D022 amendment item 5). Fix: set presence_penalty 0, frequency_penalty "
                        f"0 and repeat_penalty 1")
    for step, s in steps.items():
        if isinstance(s, dict):
            errs += _fmt(f"$.step_kinds.{step}", _step_rules(step, s, kind))
    for i, ov in enumerate(merged.get("decision_overrides") or []):
        if not isinstance(ov, dict) or ov.get("step_kind") not in STEP_KINDS or not isinstance(ov.get("settings"),
                                                                                                 dict):
            continue  # the schema already reported it
        step = ov["step_kind"]
        where = f"$.decision_overrides[{i}].settings"
        combined = deep_merge(steps.get(step) if isinstance(steps.get(step), dict) else {}, ov["settings"])
        for e in validate(combined, schema["$defs"][f"{step}Settings"], schema, where):
            errs.append(f"{e}. Fix: an override may set only its step kind's own knobs, to values the schema lists "
                        f"(decision kind {ov.get('decision_kind')})")
        # Only what the override itself breaks: a rule the plain step already breaks is reported once, above.
        plain = set(_step_rules(step, steps.get(step) if isinstance(steps.get(step), dict) else {}, kind))
        errs += _fmt(where, [f for f in _step_rules(step, combined, kind) if f not in plain])
    return errs


# ── Reading and loading preset files ─────────────────────────────────────────

def _object_pairs(pairs):
    """json object hook that refuses a duplicate key (the standard parser would keep the last value silently)."""
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate key {key!r}")
        obj[key] = value
    return obj


def _no_constant(token):
    """json hook for NaN, Infinity and -Infinity, which are not JSON and would slip past every range check."""
    raise ValueError(f"{token} is not a JSON number")


def read_preset(path, max_bytes=MAX_PRESET_BYTES):
    """(the JSON object, the raw bytes) of one preset file, read strictly (see the module docs); raises PresetError.

    A UTF-8 byte-order mark is accepted (editors on Windows add one); the hash is always of the bytes as stored."""
    name = os.path.basename(path)
    try:
        size = os.path.getsize(path)
        if size > max_bytes:
            raise PresetError(f"{name} is {size} bytes, over the {max_bytes}-byte cap; a preset is a few KB of "
                              f"settings, so this is not one. Fix: pass the preset file itself")
        with open(path, "rb") as f:
            raw = f.read(max_bytes + 1)
    except OSError as e:
        raise PresetError(f"cannot read preset file {path} ({e.strerror or e}). Fix: check the path; it is read "
                          f"relative to the current folder") from None
    if len(raw) > max_bytes:
        raise PresetError(f"{name} grew past the {max_bytes}-byte cap while it was read. Fix: pass a finished file")
    try:
        doc = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_object_pairs, parse_constant=_no_constant)
    except (ValueError, RecursionError) as e:
        raise PresetError(f"{name} is not valid UTF-8 JSON: {e}. Fix: correct the file (presets/lint.py checks it "
                          f"on its own)") from None
    if not isinstance(doc, dict):
        kind = {list: "array", str: "string", bool: "boolean", type(None): "null"}.get(type(doc), "number")
        raise PresetError(f"{name} holds a JSON {kind}, not an object. Fix: a preset is one JSON object (format "
                          f"plotroom.harness-preset/1)")
    return doc, raw


def _ref(doc):
    return f"{doc.get('preset_id')}@{doc.get('version')}"


def index_folder(folder, max_bytes=MAX_PRESET_BYTES):
    """({"id@version": [paths]}, files skipped) over the ``*.json`` files of `folder` that read as presets.

    A file that is not a preset (unreadable, not an object, no string id and version) is skipped and counted: a stray
    file in the folder must not block loading, but the not-found message mentions how many were skipped."""
    index, skipped = {}, 0
    try:
        names = sorted(os.listdir(folder or "."))
    except OSError as e:
        raise PresetError(f"cannot list the preset folder {folder!r} ({e.strerror or e}). Fix: check the path") \
            from None
    for name in names:
        if not name.lower().endswith(".json"):
            continue
        path = os.path.join(folder, name)
        try:
            doc, _ = read_preset(path, max_bytes)
        except PresetError:
            skipped += 1
            continue
        if not isinstance(doc.get("preset_id"), str) or not isinstance(doc.get("version"), str):
            skipped += 1
            continue
        index.setdefault(_ref(doc), []).append(path)
    return index, skipped


def load(path, schema=None, max_bytes=MAX_PRESET_BYTES):
    """One preset with its bases, checked. Raises PresetError when a file cannot be read or resolved.

    Returns {"file": base name, "sha256": of the file's bytes, "doc": the file's object, "merged": its settings
    merged onto its bases (None when the file fails the schema), "bases": [{"ref", "file", "sha256"}] nearest first,
    "errors": every schema and rule finding of the file, its bases and the merged result}. A preset is usable only
    when ``errors`` is empty."""
    schema = schema if schema is not None else load_schema()
    doc, raw = read_preset(path, max_bytes)
    name = os.path.basename(path)
    result = {"file": name, "sha256": hashlib.sha256(raw).hexdigest(), "doc": doc, "merged": None, "bases": [],
              "errors": validate(doc, schema, schema)}
    if result["errors"]:
        return result
    # ── Walk the extends chain (nearest base first) ──
    chain, order, cur, index, skipped = [], [_ref(doc)], doc, None, 0
    folder = os.path.dirname(path)
    while "extends" in cur:
        target = cur["extends"]
        if target in order:
            raise PresetError(f"{name}: the extends chain is circular ({' -> '.join(order)} -> {target}). Fix: "
                              f"make the chain end at the default preset, which extends nothing")
        if len(chain) >= MAX_CHAIN:
            raise PresetError(f"{name} extends more than {MAX_CHAIN} bases (the chain reaches {target}). Fix: extend "
                              f"a base closer to the default")
        if index is None:
            index, skipped = index_folder(folder, max_bytes)
        paths = index.get(target, [])
        if not paths:
            note = f"; {skipped} other .json file(s) there are not presets" if skipped else ""
            raise PresetError(f"{name} extends {target}, but no preset file in its folder declares that id and "
                              f"version{note}. Fix: copy the base preset file into the same folder as {name}")
        if len(paths) > 1:
            raise PresetError(f"{name} extends {target}, which {len(paths)} files in its folder declare "
                              f"({', '.join(os.path.basename(p) for p in paths)}). Fix: keep one; a preset's id and "
                              f"version must name exactly one file")
        bdoc, braw = read_preset(paths[0], max_bytes)
        berr = validate(bdoc, schema, schema)
        if berr:
            result["errors"] = [f"base {target} ({os.path.basename(paths[0])}): {e}" for e in berr]
            return result
        chain.append((target, paths[0], bdoc, braw))
        order.append(target)
        cur = bdoc
    # ── Merge root first, checking every level's own rules ──
    errors, merged = [], None
    for target, bpath, bdoc, _ in reversed(chain):
        merged = merge_onto({}, bdoc) if merged is None else merge_onto(merged, bdoc)
        errors += [f"base {target} ({os.path.basename(bpath)}): {e}" for e in invariants(bdoc, merged, schema)]
    merged = merge_onto({}, doc) if merged is None else merge_onto(merged, doc)
    if chain:
        errors += [f"merged: {e}" for e in validate(merged, schema, schema)]
    errors += invariants(doc, merged, schema)
    result.update(merged=merged, errors=errors, bases=[
        {"ref": t, "file": os.path.basename(bp), "sha256": hashlib.sha256(br).hexdigest()} for t, bp, _, br in chain])
    return result


# ── Command line ─────────────────────────────────────────────────────────────

def main(argv=None):
    """Check the preset files named in `argv` (default: every drafts/*.preset.json); 0 when all pass, 1 otherwise."""
    args = sys.argv[1:] if argv is None else list(argv)
    if any(a in ("-h", "--help") for a in args):
        print("usage: lint.py [PRESET.json ...]  (default: every presets/drafts/*.preset.json)\n\n" + __doc__)
        return 0
    files = args or sorted(glob.glob(os.path.join(DRAFTS_DIR, "*.preset.json")))
    if not files:
        print("no preset files to check")
        return 1
    schema = load_schema()
    failed = 0
    for path in files:
        name = os.path.basename(path)
        try:
            loaded = load(path, schema)
        except PresetError as e:
            loaded, errs = None, [str(e)]
        else:
            errs = loaded["errors"]
        failed += 1 if errs else 0
        line = f"{'OK' if not errs else 'FAIL':4s} {name}"
        if loaded is not None:
            doc = loaded["doc"]
            steps = sorted(doc.get("step_kinds") or {}) if isinstance(doc.get("step_kinds"), dict) else []
            line += (f"  status={doc.get('status')} extends={doc.get('extends', '-')} sha256={loaded['sha256'][:12]} "
                     f"step_kinds={steps} overrides={len(doc.get('decision_overrides') or [])}")
        print(line)
        for e in errs:
            print("     -", e)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
