"""Per-diagnostic repair rate in the live pilot: does a fed-back error disappear next round?

For every repair transition (round r -> r+1) of every episode, each error block in the
round-r feedback is classified (E-code; `+fix` when it carries the GUIDED custom
`fix:` note; `E0618-Refusal` for a payload written on a unit `Refusal` variant) and
counted as repaired when its first line no longer appears in the round r+1 feedback.
Crude on purpose: identical first lines (all Refusal E0618s read alike) count as
repaired only when every copy is gone. Reads the saved per-round feedback from the
`code/` folder next to each results file (`runner.py run --save-dir <results dir>/code`,
as live/drive_pilot.py runs it).

Usage: python analysis/fix_rates.py <out.json> <results1.jsonl> [...]   (stdlib only)
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def kind_of(block: str) -> str | None:
    m = re.match(r"error\[(E\d+)\]", block)
    if not m:
        return None
    if m.group(1) == "E0618" and "found `Refusal`" in block:
        return "E0618-Refusal"
    return m.group(1) + ("+fix" if "fix:" in block else "")


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
        seen, fixed = Counter(), Counter()
        for (rid, task, v, s), rs in by.items():
            rs.sort(key=lambda q: q["round"])
            for a, b in zip(rs, rs[1:]):
                fa = code_dir / rid / f"{task}_{v}_s{s}_R{a['round']}.feedback.txt"
                fb = code_dir / rid / f"{task}_{v}_s{s}_R{b['round']}.feedback.txt"
                if not fa.exists():
                    continue
                nxt = fb.read_text(encoding="utf-8") if fb.exists() else ""
                for blk in re.split(r"\n(?=error)", fa.read_text(encoding="utf-8")):
                    k = kind_of(blk)
                    if not k:
                        continue
                    seen[(v, k)] += 1
                    fixed[(v, k)] += blk.splitlines()[0] not in nxt
        report[model] = {f"{v}/{k}": f"{fixed[(v, k)]}/{n}" for (v, k), n in seen.most_common()}
    Path(out_path).write_text(json.dumps(report, indent=1), encoding="utf-8")
    for model, d in report.items():
        print(model)
        for k, val in d.items():
            print(f"  {k:28} {val}")


if __name__ == "__main__":
    main()
