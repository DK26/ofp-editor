#!/usr/bin/env python3
"""Regression checks: the local backends' requests and scores are unchanged since the tool before the cloud backend.

Docs 44 and 46 measured local models with the Ollama and llama-server backends; every later change (the cloud
backend, harness-uplift variants, logprob mode, scaffold arms) must leave those requests and their scoring exactly
as they were, or new runs would no longer pair item by item with the old ones.

The reference is frozen in tests/golden/ (see make_goldens.py): per-command digests of the request bodies the tool
sent before the cloud backend (``local-bodies.json``), and that version's score.py summary of the records it wrote
(``local-summary.json``). ``setUpModule`` runs dump_payloads.py once over the same 40 command lines (every suite,
both conditions, --why, sampler pins and overrides, both backends, the bearer key from the environment and from the
command line) with the network replaced, and the three cases compare its output with the goldens.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""
import json
import os
import subprocess
import sys
import unittest

import support
from support import TOOL, check

WORK = None  # this module's work folder
DUMP = None  # dump_payloads.py's output folder inside it


def setUpModule():
    """Dump the current tool's local request bodies and records once; the three cases read the dump."""
    global WORK, DUMP
    WORK = support.make_work("cloud-regression")
    DUMP = os.path.join(WORK, "dump")
    p = subprocess.run([sys.executable, os.path.join(support.TESTS_DIR, "dump_payloads.py"), TOOL, DUMP],
                       capture_output=True, text=True, encoding="utf-8", env=support.child_env(), timeout=900)
    check(p.returncode == 0, f"dump_payloads.py failed: {p.stdout[-300:]} {p.stderr[-800:]}")


def tearDownModule():
    support.remove_work(WORK)


# ── Helpers ──────────────────────────────────────────────────────────────────

def dump_grid():
    """The dump's command lines, in run order."""
    with open(os.path.join(DUMP, "grid.json"), encoding="utf-8") as f:
        return json.load(f)


def record_files():
    """The record file of each dump run, in run order."""
    return [os.path.join(DUMP, "runs", f"run{n}.jsonl") for n in range(len(dump_grid()))]


def score(files, name):
    """The current score.py's JSON summary (a list of groups) of `files`."""
    js = os.path.join(WORK, name + ".json")
    p = subprocess.run([sys.executable, os.path.join(TOOL, "score.py")] + files +
                       ["--csv", os.path.join(WORK, name + ".csv"), "--json", js],
                       capture_output=True, text=True, encoding="utf-8", env=support.child_env(), timeout=900)
    check(p.returncode == 0, f"score.py failed: {p.stderr[-600:]}")
    with open(js, encoding="utf-8") as f:
        return json.load(f)


def summary_diffs(golden, groups):
    """(differences, new keys): every golden value the current summary does not reproduce, matched by group identity
    (model, suite, condition, variant), and the keys only the current summary has."""
    ident = lambda g: (g.get("model"), g.get("suite"), g.get("condition"), g.get("variant"))  # noqa: E731
    got = {ident(g): g for g in groups}
    diffs = []
    for g in golden["groups"]:
        cur = got.get(ident(g))
        if cur is None:
            diffs.append((ident(g), "group missing"))
            continue
        diffs += [(ident(g), k, v, cur.get(k)) for k, v in g.items() if cur.get(k) != v]
    extra_groups = set(got) - {ident(g) for g in golden["groups"]}
    diffs += [(i, "group not in the golden") for i in sorted(extra_groups, key=str)]
    skip = set(golden["latency_keys_removed"])
    new_keys = sorted(set(groups[0]) - set(golden["groups"][0]) - skip) if groups else []
    return diffs, new_keys


# ── Cases ────────────────────────────────────────────────────────────────────

def t01_regression_local_request_bodies_byte_identical():
    """The Ollama and llama-server request bodies are byte-identical to the pre-cloud tool's for every existing path.

    Why: docs 44 and 46 compare models, quants and runtimes item by item; one changed byte in a default request
    would silently break that pairing for every run made after the change.

    How: per command line, the number and SHA-256 of the captured bodies (with llama-server's Authorization header)
    must equal golden/local-bodies.json; a mismatch names the first command line that differs.
    """
    golden = support.load_golden("local-bodies.json")
    tagged = []
    with open(os.path.join(DUMP, "bodies.jsonl"), encoding="utf-8") as f:
        for raw in f:
            n, line = raw.rstrip("\n").split("\t", 1)
            tagged.append((int(n), line))
    got = support.run_digests(dump_grid(), tagged)
    diff = support.compare_digests("request bodies", golden["runs"], got)
    check(diff is None, diff)
    return (f"{golden['total_bodies']} request bodies over {len(golden['runs'])} command lines identical to the "
            f"pre-cloud tool's")


def t02_regression_scorer_backward_compatible():
    """The current score.py reproduces every summary value the pre-cloud score.py computed on the pre-cloud runner's
    records.

    Why: results files written before the cloud backend (docs 44 and 46) must keep scoring the same, so old and new
    runs can be read side by side.

    How: the current runner's records, cut down to the fields the pre-cloud runner wrote (golden old_record_keys),
    are the pre-cloud records (make_goldens.py --current checked this, apart from run_id, ts and latency_ms); the
    current score.py's summary of them must reproduce every value of golden/local-summary.json, whose wall-clock
    latency keys are left out.
    """
    golden = support.load_golden("local-summary.json")
    keep = set(golden["old_record_keys"])
    old_dir = os.path.join(WORK, "old-format")
    os.makedirs(old_dir, exist_ok=True)
    files = []
    for path in record_files():
        target = os.path.join(old_dir, os.path.basename(path))
        with open(path, encoding="utf-8") as src, open(target, "w", encoding="utf-8", newline="\n") as dst:
            for line in src:
                if line.strip():
                    rec = json.loads(line)
                    dst.write(json.dumps({k: v for k, v in rec.items() if k in keep}, ensure_ascii=False) + "\n")
        files.append(target)
    diffs, new_keys = summary_diffs(golden, score(files, "old-format"))
    check(not diffs, f"{len(diffs)} summary values differ: {diffs[:5]}")
    return (f"{len(golden['groups'])} groups, every pre-cloud summary value reproduced on old-format records; new "
            f"keys only: {', '.join(new_keys)}")


def t38_local_records_score_the_same_with_the_new_runner():
    """Records the current run.py writes for the local backends, scored by the current score.py, give the pre-cloud
    pipeline's summary.

    Why: the runner and the scorer both changed since docs 44 and 46; this is the end-to-end check that a local run
    made today is scored as it would have been then.

    How: the current score.py's summary of the dump's records must reproduce every value of golden/local-summary.json
    (latency keys left out: they measure wall-clock time).
    """
    golden = support.load_golden("local-summary.json")
    groups = score(record_files(), "current")
    diffs, _ = summary_diffs(golden, groups)
    check(len(groups) == len(golden["groups"]) and not diffs, f"{len(diffs)} values differ: {diffs[:5]}")
    return f"{len(groups)} groups from the current runner's local records equal the pre-cloud pipeline's (latency excluded)"


# ── unittest wiring ──────────────────────────────────────────────────────────

class LocalRegressionTests(support.CaseTestCase):
    """The local backends' requests and scores against the pre-cloud goldens (see the module docs)."""

    cases = (t01_regression_local_request_bodies_byte_identical,
             t02_regression_scorer_backward_compatible,
             t38_local_records_score_the_same_with_the_new_runner)


if __name__ == "__main__":
    unittest.main()
