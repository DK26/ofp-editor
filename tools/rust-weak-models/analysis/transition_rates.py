"""Round-level clearance rates for doc 64 (stdlib only).

For every repair transition r -> r+1 (both rounds generated, round r failed to compile),
classify round r's feedback by which error *kinds* it contains and ask whether round r+1's
feedback still contains that kind at all. Unlike fix_rates.py this counts a kind once per
transition, so repeated identical first lines (all E0618-Refusal blocks read alike) do not
bias the rate downwards.

Kinds: E0618-Refusal (payload on a unit Refusal variant), E0277+fix (GUIDED custom note),
E0277-q (`?` conversion / Try errors), E0277-other, E0308, E0599, E0432/E0433 (paths).
Also counts transitions whose next round compiles. Reads the saved per-round feedback from
the `code/` folder next to each results file (`runner.py run --save-dir <results dir>/code`).
This is the script behind doc 64 §4.5's clearance table.

Usage: python analysis/transition_rates.py <out.json> <results1.jsonl> [...]
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def kinds(text: str) -> set:
    out = set()
    for blk in re.split(r"\n(?=error)", text):
        m = re.match(r"error\[(E\d+)\]: ?(.*)", blk)
        if not m:
            continue
        code, head = m.group(1), m.group(2)
        if code == "E0618" and "found `Refusal`" in head:
            out.add("E0618-Refusal")
        elif code == "E0277" and "fix:" in blk:
            out.add("E0277+fix")
        elif code == "E0277" and ("`?`" in head):
            out.add("E0277-q")
        elif code == "E0277":
            out.add("E0277-other")
        elif code in ("E0432", "E0433"):
            out.add("E0432/3")
        elif code in ("E0308", "E0599"):
            out.add(code)
    return out


def main() -> None:
    out_path, files = sys.argv[1], sys.argv[2:]
    report = {}
    for f in files:
        rows = [json.loads(x) for x in Path(f).read_text(encoding="utf-8").splitlines() if x.strip()]
        model = next(r["model"] for r in rows if r["kind"] == "run")
        code_dir = Path(f).resolve().parent / "code"
        by = defaultdict(list)
        for r in rows:
            if r["kind"] == "round" and "gen" in r:
                by[(r["run_id"], r["task"], r["variant"], r["sample"])].append(r)
        seen, cleared = Counter(), Counter()
        for (rid, task, v, s), rs in by.items():
            rs.sort(key=lambda q: q["round"])
            for a, b in zip(rs, rs[1:]):
                if a.get("compile_ok"):
                    continue
                fa = code_dir / rid / f"{task}_{v}_s{s}_R{a['round']}.feedback.txt"
                fb = code_dir / rid / f"{task}_{v}_s{s}_R{b['round']}.feedback.txt"
                if not fa.exists():
                    continue
                ka = kinds(fa.read_text(encoding="utf-8"))
                kb = kinds(fb.read_text(encoding="utf-8")) if fb.exists() else set()
                for k in ka:
                    seen[(v, k)] += 1
                    cleared[(v, k)] += k not in kb
                seen[(v, "any-compile-fail")] += 1
                cleared[(v, "any-compile-fail")] += bool(b.get("compile_ok"))
        report[model] = {f"{v}/{k}": f"{cleared[(v, k)]}/{n}" for (v, k), n in sorted(seen.items())}
    Path(out_path).write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
