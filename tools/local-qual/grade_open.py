#!/usr/bin/env python3
"""Map the open Pick arms' free-form answers to option keys (tools/local-qual).

What it does
------------
The open arms (run.py ``--variant open`` or ``labels``, doc P0/P1) hide the
lettered menu, so the model answers with a name ("HOLD", "seek and destroy",
"none of these"). This script turns each answer into one of the item's option
keys, or the escape key, in a separate, auditable step, and writes a **grade
file** that score.py consumes (``score.py --open-grades <file>``). It never
sees or uses the request, so the mapping cannot solve the task for the model.

Alias mapping (grader ``alias-v1``)
-----------------------------------
Aliases per option are built in code from the option's label and key, plus the
hand-written synonyms and escape phrases in ``suites/pick-open-aliases.json``:
the whole label; the key with ``-`` and ``_`` read as spaces; a leading code on
its own and the rest of the label ("AM07 Dark night raid" gives "am07" and
"dark night raid"); the parts of a label split at " / " when it has no digits
("Spawn zone / ambient population"); CamelCase split into words
("SquadSelection" gives "squad selection"); and timer labels without the words
min, mid and max ("Countdown, min 60 / mid 90 / max 120" gives
"countdown 60 90 120"). An alias that two options of one item would share is
dropped from both.

Answers and aliases are normalised the same way: casefold, ``&`` read as
"and", punctuation turned into spaces, spaces collapsed. Then, in order:

1. the whole answer equals one option's alias -> that key (``exact``);
2. the whole answer is an escape phrase -> the escape key (``escape``);
3. whole-word alias occurrences inside the answer, keeping only the longest of
   overlapping matches ("tr unload" wins over the "unload" inside it): exactly
   one option and no leading escape phrase -> that key (``substring``); no
   option but the answer starts with an escape phrase -> the escape key
   (``escape``);
4. anything else -> ``unmapped``, which score.py counts as wrong.

Judge mapping (secondary)
-------------------------
``--judge-sheet`` writes one row per unmapped answer for a pinned judge model:
the answer text, the option labels and descriptions and the escape, and never
the request. The judge's rows come back in the grade-file format with
``map_mode: "judge"`` and ``grader: "judge:<model id>"``; score.py reports the
accuracy with them as ``judge_mapped_accuracy`` next to the alias-only
``accuracy``.

Grade file rows (JSONL)
-----------------------
``{"grade_of": {"run_id", "model", "suite", "item_id", "condition",
"variant", "sample"}, "answer_sha", "open_answer", "mapped_key", "map_mode",
"map_detail", "grader", "sidecar_sha", "ts"}``. ``answer_sha`` (sha256 of the
answer, first 16 hex digits) ties a grade to the exact answer; score.py
ignores a grade whose answer no longer matches the record.

Standard library only.
"""
import argparse
import datetime as _dt
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES_DIR = os.path.join(HERE, "suites")
RESULTS_DIR = os.path.join(HERE, "results")
SIDECAR = os.path.join(SUITES_DIR, "pick-open-aliases.json")
OPEN_VARIANTS = ("open", "labels")
GRADER = "alias-v1"
_CODE_RE = re.compile(r"^([A-Za-z]{1,2}\d{1,3})\s+(.+)$")
JUDGE_INSTRUCTIONS = (
    "Below is one short answer a model gave when asked to name an editor option, and the list of valid options. "
    "Decide which single option the answer names. Reply with that option's key; with the escape key if the answer "
    "says that nothing fits; or with null if the answer names none of them or more than one. Judge only what the "
    "answer says: you do not see the task, and you must not guess which option would have been right.")


# ── Normalising and aliases ──────────────────────────────────────────────────

def normalise(text):
    """Casefold, '&' -> 'and', punctuation and underscores -> spaces, collapse spaces."""
    s = str(text or "").casefold().replace("&", " and ")
    s = re.sub(r"[^\w\s]|_", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def auto_aliases(option):
    """Aliases built from one option's label and key (see the module docs)."""
    label, key = option.get("label", ""), option.get("key", "")
    out = {normalise(label), normalise(key.replace("-", " ").replace("_", " "))}
    m = _CODE_RE.match(label.strip())
    if m:
        out.update({normalise(m.group(1)), normalise(m.group(2))})
    if " / " in label and not re.search(r"\d", label):
        out.update(normalise(part) for part in label.split(" / "))
    elif "/" in label and not re.search(r"\d", label):
        out.update(normalise(part) for part in label.split("/"))
    out.add(normalise(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", label)))
    if re.search(r"\b(min|mid|max)\b", label, re.I):
        out.add(normalise(re.sub(r"\b(min|mid|max)\b", " ", label, flags=re.I)))
    return {a for a in out if a}


def item_aliases(item, sidecar):
    """{option key: set of aliases} for one item, with shared aliases dropped; returns (aliases, dropped)."""
    by_key_syn = sidecar.get("synonyms_by_key", {})
    per_item = {it.get("id"): it for it in sidecar.get("items", []) if isinstance(it, dict)}
    item_syn = (per_item.get(item["id"]) or {}).get("synonyms", {})
    aliases = {}
    for opt in item["options"]:
        al = auto_aliases(opt)
        al.update(normalise(s) for s in by_key_syn.get(opt["key"], []))
        al.update(normalise(s) for s in item_syn.get(opt["key"], []))
        aliases[opt["key"]] = {a for a in al if a}
    owners = {}
    for key, als in aliases.items():
        for a in als:
            owners.setdefault(a, set()).add(key)
    dropped = sorted(a for a, keys in owners.items() if len(keys) > 1)
    for key in aliases:
        aliases[key] -= set(dropped)
    return aliases, dropped


def map_answer(answer, aliases, escape_key, escape_phrases):
    """(key or None, map_mode, detail) for one answer; see the module docs for the rules."""
    a = normalise(answer)
    if not a:
        return None, "unmapped", "empty answer"
    exact = sorted(k for k, als in aliases.items() if a in als)
    if len(exact) == 1:
        return exact[0], "exact", ""
    phrases = sorted({normalise(p) for p in escape_phrases if normalise(p)}, key=len, reverse=True)
    if a in phrases:
        return escape_key, "escape", "escape phrase"
    padded = f" {a} "
    spans = []
    for key, als in aliases.items():
        for al in als:
            start = padded.find(f" {al} ")
            while start != -1:
                spans.append((start, start + len(al), key))
                start = padded.find(f" {al} ", start + 1)
    # Longest match wins: drop a match that lies inside a longer match of another option.
    keep = [s for s in spans
            if not any(o[2] != s[2] and o[0] <= s[0] and s[1] <= o[1] and (o[1] - o[0]) > (s[1] - s[0])
                       for o in spans)]
    keys = sorted({s[2] for s in keep})
    leading_escape = any(a == p or a.startswith(p + " ") for p in phrases)
    if len(keys) == 1 and not leading_escape:
        return keys[0], "substring", ""
    if not keys and leading_escape:
        return escape_key, "escape", "answer starts with an escape phrase"
    if keys or leading_escape:
        return None, "unmapped", "ambiguous: " + ", ".join(keys) + (" + escape phrase" if leading_escape else "")
    return None, "unmapped", "no alias found"


def answer_sha(text):
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


GRADE_KEY_FIELDS = ("run_id", "model", "suite", "item_id", "condition", "variant", "sample")


def grade_key(rec):
    return {k: rec.get(k) for k in GRADE_KEY_FIELDS}


# ── Consuming a grade file (score.py, uplift.py) ─────────────────────────────

def read_jsonl(patterns):
    """JSON objects from JSONL files or globs; lines that are not JSON objects are skipped."""
    rows = []
    for pattern in patterns or []:
        for path in sorted(glob.glob(pattern)) or ([pattern] if os.path.exists(pattern) else []):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(row, dict):
                        rows.append(row)
    return rows


def apply_grades(recs, patterns, items_by_suite):
    """Put the grade files' mapped keys onto the open-arm Pick records (in place); returns counts.

    Each open record without an error gets ``chosen_key`` and ``map_mode`` from its alias grade and
    ``_graded`` True; when the alias mapping left it unmapped, ``_judge_key`` from a judge row. A grade counts
    only if its ``answer_sha`` matches the record's answer (otherwise it is stale), and a judge key only if it
    is one of the item's option keys, its escape key, or null. ``items_by_suite`` is {suite: {item id: item}}.
    """
    alias, judge = {}, {}
    for row in read_jsonl(patterns):
        g = row.get("grade_of")
        if not isinstance(g, dict):
            continue
        key = tuple(g.get(k) for k in GRADE_KEY_FIELDS)
        (judge if row.get("map_mode") == "judge" else alias)[key] = row
    stats = {}

    def count(name):
        stats[name] = stats.get(name, 0) + 1
    for r in recs:
        if r.get("variant") not in OPEN_VARIANTS or r.get("error"):
            continue
        answer = r.get("open_answer") if r.get("open_answer") is not None else (r.get("raw") or "")
        key = tuple(r.get(k) for k in GRADE_KEY_FIELDS)
        g = alias.get(key)
        if g is None or g.get("answer_sha") != answer_sha(answer):
            count("ungraded" if g is None else "stale")
            r["_graded"] = False
            continue
        r["_graded"] = True
        r["chosen_key"] = g.get("mapped_key")
        r["map_mode"] = g.get("map_mode")
        j = judge.get(key)
        if r["map_mode"] == "unmapped" and j is not None and j.get("answer_sha") == answer_sha(answer):
            item = items_by_suite.get(r.get("suite"), {}).get(r.get("item_id"))
            valid = ({o["key"] for o in item["options"]} | {item["escape"]["key"]}) if item else set()
            if j.get("mapped_key") is None or j.get("mapped_key") in valid:
                r["_judge_key"] = j.get("mapped_key")
                count("judged")
            else:
                count("judge_invalid")
        count(r["map_mode"] or "?")
    return stats


# ── Loading ──────────────────────────────────────────────────────────────────

def load_items():
    """{suite name: {item id: item}} for every runnable suite with Pick items."""
    out = {}
    for path in sorted(glob.glob(os.path.join(SUITES_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            suite = json.load(f)
        if suite.get("shape", suite.get("suite")) == "pick":
            out[suite["suite"]] = {it["id"]: it for it in suite["items"]}
    return out


def load_open_records(patterns):
    recs = []
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)) or ([pattern] if os.path.exists(pattern) else []):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(r, dict) and "seed" in r and r.get("variant") in OPEN_VARIANTS \
                            and not r.get("error"):
                        recs.append(r)
    return recs


# ── Main ─────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description="Map open-arm Pick answers to option keys (writes a grade file).")
    ap.add_argument("inputs", nargs="*", default=[os.path.join(RESULTS_DIR, "*.jsonl")],
                    help="run.py JSONL files or globs (default results/*.jsonl); only open/labels records are read")
    ap.add_argument("--out", default=os.path.join(RESULTS_DIR, "grades", "open-grades.jsonl"),
                    help="grade file to write (default results/grades/open-grades.jsonl, outside score.py's default "
                         "results/*.jsonl glob)")
    ap.add_argument("--judge-sheet", default=None, help="also write the unmapped answers as a judge sheet (JSONL)")
    ap.add_argument("--sidecar", default=SIDECAR)
    args = ap.parse_args(argv)

    with open(args.sidecar, "rb") as f:
        raw = f.read()
    sidecar, sidecar_sha = json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()[:16]
    items = load_items()
    recs = load_open_records(args.inputs)
    if not recs:
        print("no open-arm records found", file=sys.stderr)
        return 1

    counts, judge_rows, now = {}, [], _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    alias_cache = {}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fout:
        for r in recs:
            item = items.get(r.get("suite"), {}).get(r.get("item_id"))
            if item is None:
                print(f"warning: no item {r.get('suite')}/{r.get('item_id')}; skipped", file=sys.stderr)
                continue
            ck = (r["suite"], item["id"])
            if ck not in alias_cache:
                alias_cache[ck], dropped = item_aliases(item, sidecar)
                if dropped:
                    print(f"note: {r['suite']}/{item['id']}: shared aliases dropped: {', '.join(dropped)}",
                          file=sys.stderr)
            answer = r.get("open_answer") if r.get("open_answer") is not None else (r.get("raw") or "")
            key, mode, detail = map_answer(answer, alias_cache[ck], item["escape"]["key"],
                                           sidecar.get("escape_phrases", []))
            counts[mode] = counts.get(mode, 0) + 1
            row = {"grade_of": grade_key(r), "answer_sha": answer_sha(answer), "open_answer": answer,
                   "mapped_key": key, "map_mode": mode, "map_detail": detail, "grader": GRADER,
                   "sidecar_sha": sidecar_sha, "ts": now}
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            if mode == "unmapped":
                judge_rows.append({
                    "grade_of": grade_key(r), "answer_sha": answer_sha(answer), "answer": answer,
                    "options": [{"key": o["key"], "label": o["label"], "desc": o["desc"]} for o in item["options"]],
                    "escape": dict(item["escape"]), "instructions": JUDGE_INSTRUCTIONS,
                    "reply_as": {"grade_of": "<copied>", "answer_sha": "<copied>", "mapped_key": "<key or null>",
                                 "map_mode": "judge", "grader": "judge:<model id>"}})
    if args.judge_sheet:
        with open(args.judge_sheet, "w", encoding="utf-8", newline="\n") as f:
            for row in judge_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"graded {sum(counts.values())} answers: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
          + f" -> {args.out}" + (f"; {len(judge_rows)} rows for the judge -> {args.judge_sheet}"
                                 if args.judge_sheet else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
