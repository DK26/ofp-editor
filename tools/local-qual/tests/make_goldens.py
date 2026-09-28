#!/usr/bin/env python3
"""Write the golden files the regression tests compare against (tests/golden/*.json).

Usage::

    python make_goldens.py local <baseline tool dir> [--current <tool dir>]
    python make_goldens.py scaffold <baseline tool dir>

What the goldens are
--------------------
Some checks do not test a feature: they prove that a change left existing measurements alone. Their reference is
an earlier version of the tool, so the reference output is frozen here once, from that version, and the tests
compare the current tool with it.

* ``local`` (tests t01, t02, t38): ``dump_payloads.py`` runs the baseline tool over 40 local command lines. The
  golden keeps, per command line, the number and SHA-256 of the request bodies it sent (``local-bodies.json``), and
  the baseline ``score.py`` summary of the records it wrote with the wall-clock latency keys removed
  (``local-summary.json``), together with the record fields the baseline runner wrote (``old_record_keys``): test t02
  projects the current runner's records onto those fields to rebuild the baseline's record format. With
  ``--current``, the script also dumps the current tool and checks that this projection reproduces the baseline's
  records exactly (apart from run_id, ts and latency_ms), which is what makes t02 a faithful stand-in for scoring
  the baseline's own files.
* ``scaffold`` (test a01): ``dump_bodies.py`` runs the baseline tool over its 69-command grid (plus three dry runs);
  the golden keeps per-run digests of the bodies, records and dry-run prints (``scaffold-regress.json``).

When to regenerate
------------------
Only deliberately. A suite edit changes the requests, so regenerate from the current tool with the edit in place
(the code did not change, so the current tool is its own baseline). A code change that is meant to change a default
request must say so in its change set and regenerate from the tool as it was before the change (for example a
checkout of the previous commit), never from the changed tool itself, or the test proves nothing.

The goldens in this repository were made from the tool before the cloud backend (``local``: the version measured in
docs 44 and 46) and from the tool with the cloud backend, logprob mode and cascade simulator but before the scaffold
arms (``scaffold``). Standard library only; nothing here touches the network (the scaffold dump starts the
in-process mock llama-server on 127.0.0.1).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from support import child_env, run_digests, sha256_lines  # noqa: E402

# score.py summary keys computed from wall-clock latency: they differ on every run, so the goldens leave them out.
LATENCY_KEYS = ("latency_p50_ms", "latency_p90_ms")
# Record fields that differ between two runs of the same command line.
VOLATILE = ("run_id", "ts", "latency_ms")


def read_tagged(path):
    """[(run index, line)] from a ``<n><TAB><line>`` file written by the dump scripts."""
    out = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            n, line = raw.rstrip("\n").split("\t", 1)
            out.append((int(n), line))
    return out


def dump(script, tool, work, *extra):
    """Run one dump script against `tool` into `work`; returns `work`."""
    p = subprocess.run([sys.executable, os.path.join(HERE, script), os.path.abspath(tool), work] + list(extra),
                       capture_output=True, text=True, encoding="utf-8", env=child_env(), timeout=900)
    if p.returncode != 0:
        raise SystemExit(f"{script} failed on {tool}: {p.stdout[-400:]} {p.stderr[-800:]}")
    print(p.stdout.strip())
    return work


def record_files(work):
    """The run<N>.jsonl record files of a dump, in run order."""
    runs = os.path.join(work, "runs")
    return [os.path.join(runs, f"run{n}.jsonl") for n in range(len(os.listdir(runs)))]


def records_of(work):
    """Every record a dump's runs wrote, in order."""
    out = []
    for path in record_files(work):
        with open(path, encoding="utf-8") as f:
            out += [json.loads(line) for line in f if line.strip()]
    return out


def summary(tool, files, work):
    """score.py's JSON summary (a list of groups) of `files`, scored by the given tool's scorer."""
    js = os.path.join(work, "summary.json")
    p = subprocess.run([sys.executable, os.path.join(tool, "score.py")] + files +
                       ["--csv", os.path.join(work, "summary.csv"), "--json", js],
                       capture_output=True, text=True, encoding="utf-8", env=child_env(), timeout=900)
    if p.returncode != 0:
        raise SystemExit(f"score.py failed: {p.stderr[-800:]}")
    with open(js, encoding="utf-8") as f:
        return json.load(f)


def write(name, data):
    path = os.path.join(HERE, "golden", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"wrote {os.path.relpath(path, HERE)}")


def make_local(baseline, current):
    """local-bodies.json and local-summary.json from the baseline tool (see the module docs)."""
    work = dump("dump_payloads.py", baseline, tempfile.mkdtemp(prefix="golden-local-"))
    with open(os.path.join(work, "grid.json"), encoding="utf-8") as f:
        grid = json.load(f)
    digests = run_digests(grid, read_tagged(os.path.join(work, "bodies.jsonl")))
    write("local-bodies.json", {
        "about": "Per-run digests of the request bodies dump_payloads.py captures from the local backends (test t01). "
                 "Frozen from the tool before the cloud backend; see make_goldens.py.",
        "runs": digests, "total_bodies": sum(d["n"] for d in digests)})
    old = records_of(work)
    old_keys = sorted({k for r in old for k in r})
    groups = summary(baseline, record_files(work), work)
    for g in groups:
        for k in LATENCY_KEYS:
            g.pop(k, None)
    write("local-summary.json", {
        "about": "score.py's summary of the records the local command lines of dump_payloads.py wrote, latency keys "
                 "removed (tests t02 and t38), and the record fields that tool version wrote (t02 projects the "
                 "current records onto them). Frozen from the tool before the cloud backend; see make_goldens.py.",
        "latency_keys_removed": list(LATENCY_KEYS), "old_record_keys": old_keys, "groups": groups})
    if current:
        # The claim t02 rests on: the current runner's records, cut down to the old fields, are the old records.
        new = records_of(dump("dump_payloads.py", current, tempfile.mkdtemp(prefix="golden-current-")))
        keys = set(old_keys)
        strip = lambda r: {k: v for k, v in r.items() if k not in VOLATILE}  # noqa: E731
        bad = [i for i, (a, b) in enumerate(zip(old, new)) if strip(a) != strip({k: v for k, v in b.items() if k in keys})]
        print(f"projection check: {len(old)} baseline records, {len(new)} current records, "
              f"{len(bad)} differ after projecting onto the {len(keys)} old fields" + (f" (first: {bad[:3]})" if bad else ""))
        if len(old) != len(new) or bad:
            raise SystemExit("the projection does not reproduce the baseline records; do not use this golden for t02")


def make_scaffold(baseline):
    """scaffold-regress.json from the baseline tool (see the module docs)."""
    work = dump("dump_bodies.py", baseline, os.path.join(tempfile.mkdtemp(prefix="golden-scaffold-"), "d"))
    with open(os.path.join(work, "grid.json"), encoding="utf-8") as f:
        grid = json.load(f)
    with open(os.path.join(work, "dryrun.json"), encoding="utf-8") as f:
        dry = json.load(f)
    bodies = run_digests(grid, read_tagged(os.path.join(work, "bodies.jsonl")))
    records = run_digests(grid, read_tagged(os.path.join(work, "records.jsonl")))
    write("scaffold-regress.json", {
        "about": "Per-run digests of the request bodies, records (volatile fields removed) and dry-run prints of "
                 "dump_bodies.py's grid (test a01). Frozen from the tool before the scaffold arms; see make_goldens.py.",
        "bodies": bodies, "records": records,
        "dry_runs": [{"first_line": t.split("\n", 1)[0], "sha256": sha256_lines([t])} for t in dry],
        "total_bodies": sum(d["n"] for d in bodies), "total_records": sum(d["n"] for d in records)})


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write tests/golden/*.json from a baseline copy of the tool.")
    ap.add_argument("which", choices=("local", "scaffold"))
    ap.add_argument("baseline", help="the tool folder whose behaviour the golden freezes")
    ap.add_argument("--current", default=None, help="local only: also check t02's record projection on this tool")
    a = ap.parse_args(argv)
    if a.which == "local":
        make_local(os.path.abspath(a.baseline), a.current and os.path.abspath(a.current))
    else:
        make_scaffold(os.path.abspath(a.baseline))
    return 0


if __name__ == "__main__":
    sys.exit(main())
