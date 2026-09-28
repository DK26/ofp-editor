"""Per-round timing and outcome peek for a live results JSONL, for watching a run in progress.

Usage: python analysis/peek.py <results.jsonl> [n_last]"""
import json
import sys

rows = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
rounds = [r for r in rows if r.get("kind") == "round"]
for r in rounds[-n:]:
    g = r.get("gen") or {}
    t = g.get("timings") or {}
    print(f"{r['task']} {r['variant']:6} R{r['round']} gen={g.get('gen_ms', 0)/1000:6.1f}s "
          f"prompt_n={t.get('prompt_n')} cache_n={t.get('cache_n')} pp/s={t.get('prompt_per_second', 0):.0f} "
          f"out={t.get('predicted_n')} tg/s={t.get('predicted_per_second', 0):.1f} fin={g.get('finish_reason')} "
          f"think={g.get('reasoning_chars')} build={r.get('build_ms', 0)/1000:.1f}s test={r.get('test_ms', 0)/1000:.1f}s "
          f"mode={r.get('failure_mode')} codes={','.join(r.get('diag_codes') or [])[:60]} ctx={r.get('context_est_tokens')}")
eps = [r for r in rows if r.get("kind") == "episode"]
print(f"episodes: {len(eps)}; rounds: {len(rounds)}")
