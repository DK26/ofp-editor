#!/usr/bin/env python3
"""Write a hint-only control suite: the same menus and answers, with the request blanked or swapped (doc 59 T-L6).

What it owns
------------
A scaffold may make the answer easy only because the request plus code's facts make it easy (doc 59 §5.2). The
hint-only control tests that: every Pick item keeps its options, escape, card and answer, but its request is replaced,
so a model can only be right by chance, by the menu's own priors, or because the scaffold points at the answer by
itself. Run the control suite through run.py --suite-file for the plain arm and a scaffold arm; the scaffold's
hint-only accuracy must stay within 10 points of chance and within 10 points of the plain arm's (experiment-plan.json,
rule SR3).

* ``--mode blank``: the request becomes BLANK_REQUEST.
* ``--mode swap``: the request becomes another item's request, from a different category. Items are taken in id order
  and item i receives the request of the first item at or after i + n // 2 (cyclically) whose category differs, so
  no item keeps its own request and the menu has nothing to match (a derangement by construction).

The output names itself "<suite>-hint-<mode>" (so its records never pool with the real suite's) and declares the same
shape. Item metadata (split and the pool fields) is kept, so --split still selects the tuning half.
"""
import argparse
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLANK_REQUEST = "No request was given for this decision."


def control(suite, mode):
    """The control suite dict for `suite` (a Pick suite dict) and `mode` (blank or swap)."""
    if suite.get("shape", suite.get("suite")) != "pick":
        raise ValueError("the hint-only control applies to Pick suites only")
    out = copy.deepcopy(suite)
    out["suite"] = f"{suite['suite']}-hint-{mode}"
    out["shape"] = "pick"
    out["notes"] = (f"Hint-only control of {suite['suite']} (control_suite.py --mode {mode}): menus, cards and answers "
                    f"unchanged, requests {'blanked' if mode == 'blank' else 'swapped with another category'}.")
    items = sorted(out["items"], key=lambda it: it["id"])
    n = len(items)
    originals = [it["request"] for it in items]
    for i, it in enumerate(items):
        if mode == "blank":
            it["request"] = BLANK_REQUEST
            continue
        for step in range(n):
            j = (i + n // 2 + step) % n
            if j != i and items[j].get("category") != it.get("category"):
                it["request"] = originals[j]
                it["control_request_from"] = items[j]["id"]
                break
        else:
            raise ValueError(f"no item of another category to swap with {it['id']}")
    out["items"] = items
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write a hint-only control suite (requests blanked or swapped).")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--suite", help="a suite under suites/ (pick or pick-hard)")
    src.add_argument("--suite-file", help="a Pick suite file outside suites/ (for example the staged pool)")
    ap.add_argument("--mode", choices=("blank", "swap"), required=True)
    ap.add_argument("--out", required=True, help="where to write the control suite JSON")
    args = ap.parse_args(argv)
    path = args.suite_file or os.path.join(HERE, "suites", args.suite + ".json")
    with open(path, encoding="utf-8") as f:
        suite = json.load(f)
    try:
        out = control(suite, args.mode)
    except ValueError as e:
        ap.error(str(e))
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"wrote {args.out}: suite {out['suite']}, {len(out['items'])} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
