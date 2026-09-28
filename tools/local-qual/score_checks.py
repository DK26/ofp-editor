#!/usr/bin/env python3
"""The code checks score.py applies to answers (tools/local-qual): schema, spans, words, names and sentences.

What it owns
------------
Pure functions of an answer and an item, with no I/O: ``validate_schema`` (the JSON-schema subset the suites use),
``norm_span`` (how a quoted span is compared), ``check_validator`` (one Fill validator), ``text_checks`` (the Text
suite's constraints), ``banned_hits``, ``name_violations``, ``sentence_count`` and ``words``.

How it fits
-----------
score.py scores every record with these; uplift.py, prompts.py (the repair check) and cloud_run.py (the canary's
schema check) use the same functions through score.py, so repair, scoring and the arm comparisons always agree.
Split out of score.py to keep each file readable in one pass; score.py re-exports every name. Standard library only.
"""
import re


WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")


NAME_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def norm_span(text):
    """Normalise a span for comparison: lower case, collapse spaces, trim punctuation and quotes."""
    s = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    return s.strip(" .,;:!?\"'`")


def words(text):
    return WORD_RE.findall(text or "")


def validate_schema(value, schema, path="$"):
    """Validate `value` against the JSON-schema subset the suites use.

    Supports type, enum, properties, required, additionalProperties (bool),
    minLength/maxLength, items, minItems/maxItems. Returns a list of errors.
    """
    errs = []
    typ = schema.get("type")
    types = typ if isinstance(typ, list) else ([typ] if typ else [])
    py = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}

    def is_type(t):
        if t == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if t == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        return isinstance(value, py.get(t, object))

    if types and not any(is_type(t) for t in types):
        return [f"{path}: expected {typ}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not in enum")
    if isinstance(value, str):
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: length {len(value)} > {schema['maxLength']}")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append(f"{path}: length {len(value)} < {schema['minLength']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value:
                errs.append(f"{path}: missing {req}")
        if schema.get("additionalProperties") is False:
            for extra in value:
                if extra not in props:
                    errs.append(f"{path}: unexpected {extra}")
        for k, sub in props.items():
            if k in value:
                errs.extend(validate_schema(value[k], sub, f"{path}.{k}"))
    if isinstance(value, list):
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: {len(value)} items > {schema['maxItems']}")
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append(f"{path}: {len(value)} items < {schema['minItems']}")
        if "items" in schema:
            for i, v in enumerate(value):
                errs.extend(validate_schema(v, schema["items"], f"{path}[{i}]"))
    return errs


def banned_hits(text, banned):
    low = (text or "").lower()
    return [b for b in banned if re.search(r"(?<![a-z0-9])" + re.escape(b.lower()) + r"(?![a-z0-9])", low)]


def name_violations(text, allowed, allowlist):
    """Capitalised tokens that are not allowed names.

    Checked: every capitalised token that does not start a sentence; every
    all-caps token of two or more letters; and a sentence-initial token that is
    directly followed by a comma (an address such as "Ivan, move"). Other
    sentence-initial tokens are exempt, because ordinary words are capitalised
    there; this is a known blind spot (see README).
    """
    ok = {a.lower() for a in allowed} | {a.lower() for a in allowlist}
    bad = []
    s = text or ""
    for m in NAME_TOKEN_RE.finditer(s):
        tok = m.group(0)
        if not tok[0].isupper():
            continue
        before = s[: m.start()].rstrip(" \"'([")
        sentence_start = before == "" or before[-1] in ".!?:;\n" or before.endswith(("--", "—"))
        after = s[m.end():]
        address = after.startswith(",")
        all_caps = len(tok) >= 2 and tok.isupper()
        if sentence_start and not all_caps and not address:
            continue
        if tok.lower() not in ok:
            bad.append(tok)
    return bad


def sentence_count(text):
    """Count sentences: a break is [.!?] + whitespace + a capital letter or opening quote.

    Requiring the capital keeps SQS code such as "? !alive leader1 : exit" from
    counting as a sentence break.
    """
    t = (text or "").strip()
    if not t:
        return 0
    parts = [p for p in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(“])", t) if p.strip()]
    return len(parts)


def check_validator(v, value, request, banned):
    """Apply one fill validator. Returns True/False, or None when it does not apply."""
    chk = v["check"]
    if chk == "enum":
        return None  # covered by the schema check; kept in the suite for readers
    if not isinstance(value, str):
        return False
    if chk == "quote_in_request":
        if value.strip() == "":
            return bool(v.get("allow_empty"))
        return norm_span(value) in norm_span(request)
    if chk == "max_chars":
        return len(value) <= v["value"]
    if chk == "max_words":
        return len(words(value)) <= v["value"]
    if chk == "non_empty":
        return value.strip() != ""
    if chk == "no_digits":
        return not re.search(r"\d", value)
    if chk == "banned_words":
        return not banned_hits(value, banned)
    if chk == "names_from_request":
        # Proper names in the text must come from the request (facts come from code or the user).
        req_tokens = {t.lower() for t in NAME_TOKEN_RE.findall(request)}
        return not name_violations(value, req_tokens, [])
    return None


def text_checks(item, text, suite):
    c = item["constraints"]
    nw = len(words(text))
    checks = {
        "max_words": nw <= c["max_words"],
        "min_words": nw >= c.get("min_words", 1),
        "banned_words": not banned_hits(text, suite.get("banned_words", [])),
    }
    if c.get("no_digits"):
        checks["no_digits"] = not re.search(r"\d", text)
    if c.get("names_check", True):
        checks["names_subset"] = not name_violations(text, c["allowed_names"], suite.get("name_allowlist", []))
    return checks, nw
