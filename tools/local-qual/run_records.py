#!/usr/bin/env python3
"""Record helpers for run.py (tools/local-qual): what a finished call becomes in the JSONL output.

What it owns
------------
* ``interpret``: parses a reply into a record's ``parse_ok``, ``parse_mode`` and ``parsed`` and, for Pick, the chosen
  letter and key. A reasoning block is stripped before parsing; the open arms keep the free-form answer verbatim for
  grade_open.py.
* ``merge_repair``: folds a repair call into its decision's record (the final answer is the repair's; tokens, latency
  and cost add up, and both calls settle in the ledger through ``call_costs``).
* ``done_keys``: the decisions an output file already holds without error, which ``--resume`` skips.
* ``slug``: the file-name-safe form of a label or suite name.

How it fits
-----------
run.py's main loop calls these for every decision of the generate path; the logprob mode (logprob_pick.interpret) and
the multi-call scaffold arms (scaffold_run.interpret) fill their records themselves. Split out of run.py to keep each
file readable in one pass; run.py re-exports every name, so scripts that imported them from run.py work unchanged.
Standard library only.
"""
import json
import os
import re

from prompts import OPEN_VARIANTS, extract_json, strip_think


# What a repaired decision keeps of its first answer (under "first" in the record).
FIRST_FIELDS = ("raw", "parse_ok", "parse_mode", "parsed", "chosen_letter", "chosen_key", "correct",
                "prompt_eval_count", "eval_count", "latency_ms", "cost_usd", "cost_source", "call_id", "attempts",
                "http_status_history", "reasoning_tokens", "done_reason")


def slug(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")


def done_keys(path):
    """Keys of successful records already in `path` (for --resume); budget rows and malformed lines are skipped."""
    keys = set()
    if not os.path.exists(path):
        return keys
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict) or "budget_event" in r:
                continue
            try:
                if not r.get("error"):
                    keys.add((r["model"], r["suite"], r["item_id"], r["condition"], r["variant"], r["sample"]))
            except KeyError:
                continue
    return keys


def interpret(rec, content, error, extra, shape, base_variant, why):
    """Parse `content` into rec (parse_ok, parse_mode, parsed and, for Pick, the chosen letter and key).

    ``raw`` keeps the whole reply; any reasoning block is removed before parsing (``think_stripped``)."""
    content, stripped = strip_think(content or "")
    if stripped:
        rec["think_stripped"] = True
    if shape == "knowledge":
        rec["parse_ok"] = bool(content.strip()) and not error
        rec["parse_mode"] = "text"
        rec["parsed"] = content.strip() if rec["parse_ok"] else None
    elif shape == "pick" and base_variant in OPEN_VARIANTS:
        # Free-form answer: kept verbatim for grade_open.py, which maps it to an option key.
        text = content.strip()
        rec["parse_ok"] = bool(text) and not error
        rec["parse_mode"] = "text"
        rec["parsed"] = text if rec["parse_ok"] else None
        rec["open_answer"] = text if not error else None
    else:
        parsed, mode = extract_json(content) if not error else (None, "no_response")
        rec["parse_ok"] = parsed is not None
        rec["parse_mode"] = mode
        rec["parsed"] = parsed
    rec.update(extra)
    if shape == "pick":
        if base_variant in OPEN_VARIANTS:
            rec["chosen_letter"], rec["chosen_key"], rec["correct"] = None, None, None
            return
        choice = rec["parsed"].get("choice") if rec["parse_ok"] else None
        chosen_letter = choice.strip().upper() if isinstance(choice, str) else None
        rec["chosen_letter"] = chosen_letter
        rec["chosen_key"] = extra["letter_to_key"].get(chosen_letter) if chosen_letter else None
        rec["valid_choice"] = rec["chosen_key"] is not None
        rec["correct"] = rec["chosen_key"] == extra["correct_key"]
        if why and rec["parse_ok"]:
            rec["why"] = rec["parsed"].get("why")


def merge_repair(rec, res2, latency2, call_id, call_id2):
    """Fold a repair call into the decision record: the final answer is the repair's; tokens, latency and cost add."""
    first = {k: rec.get(k) for k in FIRST_FIELDS}
    rec.update({k: v for k, v in res2["extra"].items() if v is not None})
    rec["first"] = first
    rec["error"], rec["raw"], rec["done_reason"] = res2["error"], res2["content"], res2["done_reason"]
    rec["latency_ms"] = round((first["latency_ms"] or 0.0) + latency2, 1)
    for field in ("prompt_eval_count", "eval_count"):
        a, b = first.get(field), res2[field]
        rec[field] = a + b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
    if call_id2 is not None:
        # Both calls settle in the ledger through call_costs (budget.py reads it on --resume).
        c1, c2 = first.get("cost_usd") or 0.0, res2["extra"].get("cost_usd") or 0.0
        rec["cost_usd"] = round(c1 + c2, 12)
        rec["call_costs"] = {call_id: c1, call_id2: c2}
