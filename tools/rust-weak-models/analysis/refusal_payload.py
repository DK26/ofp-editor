"""Supplementary pilot analysis: how much of the compile failure is one shared-spec slip.

`mb_spec::Refusal` has unit variants (only `Many(Vec<Problem>)` carries data). Small
models often write `Refusal::OutOfMap(label)`; rustc 1.98 answers with E0618 "expected
function, found `Refusal`" and no fix hint. Per (model, variant) this reports:
  - episodes whose code ever used a payload on a unit Refusal variant,
  - rounds whose only compile errors are that E0618 (one mechanical fix from compiling),
  - repair rounds that resubmitted byte-identical code (the loop stalled).
Reads the JSONL results and the saved per-round code and feedback from the `code/` folder
next to each results file (`runner.py run --save-dir <results dir>/code`). Stdlib only.

Usage: python analysis/refusal_payload.py <out.json> <results1.jsonl> [...]
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

UNIT = r"(?!Many\b)[A-Z][A-Za-z]*"
PAYLOAD = re.compile(rf"Refusal::{UNIT}\s*[({{]")
ERR = re.compile(r"^error(?:\[(E\d+)\])?: (.*)$", re.M)


def main() -> None:
    out_path, files = sys.argv[1], sys.argv[2:]
    report = {}
    for f in files:
        rows = [json.loads(x) for x in Path(f).read_text(encoding="utf-8").splitlines() if x.strip()]
        model = next(r["model"] for r in rows if r["kind"] == "run")
        code_dir = Path(f).resolve().parent / "code"
        eps = [r for r in rows if r["kind"] == "episode"]
        rounds = [r for r in rows if r["kind"] == "round" and "gen" in r]
        per = defaultdict(lambda: {"episodes": 0, "episodes_payload": 0, "compile_fail_rounds": 0,
                                   "rounds_only_refusal_e0618": 0, "rounds_with_refusal_e0618": 0,
                                   "repair_rounds": 0, "repair_rounds_identical": 0})
        payload_eps = set()
        by_ep = defaultdict(list)
        for r in rounds:
            by_ep[(r["task"], r["variant"], r["sample"])].append(r)
            stem = f"{r['task']}_{r['variant']}_s{r['sample']}_R{r['round']}"
            code_p = code_dir / r["run_id"] / f"{stem}.rs"
            fb_p = code_dir / r["run_id"] / f"{stem}.feedback.txt"
            code = code_p.read_text(encoding="utf-8") if code_p.exists() else ""
            if PAYLOAD.search(code):
                payload_eps.add((r["task"], r["variant"], r["sample"]))
            if r.get("failure_mode") == "compile":
                a = per[r["variant"]]
                a["compile_fail_rounds"] += 1
                fb = fb_p.read_text(encoding="utf-8") if fb_p.exists() else ""
                errs = ERR.findall(fb)
                ref = [e for e in errs if e[0] == "E0618" and "found `Refusal`" in e[1]]
                a["rounds_with_refusal_e0618"] += bool(ref)
                a["rounds_only_refusal_e0618"] += bool(errs) and len(ref) == len(errs)
        for key, rs in by_ep.items():
            rs.sort(key=lambda x: x["round"])
            a = per[key[1]]
            for x, y in zip(rs, rs[1:]):
                a["repair_rounds"] += 1
                a["repair_rounds_identical"] += bool(x.get("code_sha256")) and x.get("code_sha256") == y.get("code_sha256")
        for e in eps:
            a = per[e["variant"]]
            a["episodes"] += 1
            a["episodes_payload"] += (e["task"], e["variant"], e["sample"]) in payload_eps
        report[model] = dict(per)
    Path(out_path).write_text(json.dumps(report, indent=1), encoding="utf-8")
    for model, per in report.items():
        for v, a in sorted(per.items()):
            print(f"{model:30} {v:6} eps {a['episodes']:3}  payload-eps {a['episodes_payload']:3}  "
                  f"compile-fail rounds {a['compile_fail_rounds']:3}  with Refusal-E0618 {a['rounds_with_refusal_e0618']:3}  "
                  f"only Refusal-E0618 {a['rounds_only_refusal_e0618']:3}  identical resubmits "
                  f"{a['repair_rounds_identical']}/{a['repair_rounds']}")


if __name__ == "__main__":
    main()
