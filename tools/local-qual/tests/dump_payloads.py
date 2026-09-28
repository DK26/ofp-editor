#!/usr/bin/env python3
"""Dump every request body run.py sends through the Ollama and llama-server backends, without a server.

Usage: python dump_payloads.py <tool dir> <output dir>

What it does
------------
It imports run.py and backends.py from <tool dir>, swaps the two local backend classes for subclasses whose ``chat``
records the JSON body (and whose probes answer without the network), then calls the real ``run.main()`` over a grid
of command lines: every suite, both conditions, --why for the Pick suites, sampler pins, --think-mode omit,
--temperature and --num-predict overrides, k = 3, both backends, and the llama-server bearer key from the environment
and from --api-key.

Output, in <output dir>:

* ``grid.json``: the command lines, in run order (without the ``--out`` each run gets);
* ``bodies.jsonl``: one captured body per line as ``<run index><TAB><JSON>``, where the JSON holds the backend, the
  body and, for llama-server, the Authorization header the client would send;
* ``runs/run<N>.jsonl``: the records each run wrote.

Why
---
The bodies of these command lines are the requests every earlier measurement (docs 44 and 46) sent. Their per-run
digests are frozen in ``golden/local-bodies.json`` from the tool as it was before the cloud backend; test t01 checks
that the current tool still sends exactly those bytes, and t02/t38 score the records against
``golden/local-summary.json``. The mapping of backend classes happens by attribute on the ``run`` module, so run.py
must keep constructing its local backends through its own module-level names.
"""
import io
import json
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

tool_dir, out_dir = sys.argv[1], sys.argv[2]
sys.path.insert(0, tool_dir)
sys.dont_write_bytecode = True
import backends  # noqa: E402
import run  # noqa: E402

CAPTURED = []  # (run index, JSON line)
CURRENT = {"run": 0}


def canned(content):
    """A backend result as the local clients return it, with fixed token counts and timings."""
    return {"error": None, "think_sent": True, "content": content, "thinking_chars": 0, "prompt_eval_count": 1,
            "eval_count": 1, "eval_duration": 1, "prompt_eval_duration": 1, "load_duration": None,
            "total_duration": 2, "done_reason": "stop", "extra": {}}


class RecOllama(backends.OllamaBackend):
    """The Ollama client with the network replaced: the probe answers at once and chat records the body."""

    def probe(self, model):
        return {"runtime_version": "test", "model_file": None, "quant": "Q4_K_M", "model": model}

    def chat(self, body):
        CAPTURED.append((CURRENT["run"], json.dumps({"backend": "ollama", "body": body}, ensure_ascii=False)))
        return canned('{"choice": "A"}')


class RecLlama(backends.LlamaServerBackend):
    """The llama-server client with the network replaced; the Authorization header is captured with the body."""

    def wait_ready(self, max_wait_s=180.0):
        return True, None

    def probe(self, model):
        return {"runtime_version": "test", "model_file": "m.gguf", "quant": "Q4_K_M", "model": model or "m",
                "n_ctx": 8192, "total_slots": 1, "server_sampler_defaults": {},
                "thinking_kwarg_changes_prompt": True}

    def chat(self, body):
        CAPTURED.append((CURRENT["run"], json.dumps({"backend": "llamacpp", "auth": self.http.headers.get("Authorization"),
                                                     "body": body}, ensure_ascii=False)))
        return canned('{"choice": "A"}')


run.OllamaBackend = RecOllama
run.LlamaServerBackend = RecLlama

# ── The grid (unchanged from the check that first froze these requests) ──────
grid = []
for suite in ("pick", "pick-hard", "fill", "explain", "text", "knowledge"):
    for condition in ("none", "cards"):
        whys = (False, True) if suite in ("pick", "pick-hard") else (False,)
        for why in whys:
            base = ["--suite", suite, "--condition", condition, "--k", "3"] + (["--why"] if why else [])
            grid.append(["--backend", "ollama", "--model", "qwen3.5:4b-q4_K_M"] + base)
            grid.append(["--backend", "llamacpp", "--base-url", "http://127.0.0.1:8080"] + base)
# Overrides and pins on a few suites.
for suite in ("pick", "fill", "text"):
    extra = ["--suite", suite, "--k", "2", "--top-k", "20", "--top-p", "0.95", "--min-p", "0.0",
             "--presence-penalty", "1.5", "--repeat-penalty", "1.1", "--temperature", "0.3", "--num-predict", "99"]
    grid.append(["--backend", "ollama", "--model", "hf.co/u/r:Q4", "--think-mode", "omit", "--num-ctx", "4096"]
                + extra)
    grid.append(["--backend", "llamacpp", "--model", "router-name", "--think-mode", "omit"] + extra)
# llama-server bearer key: from the environment (default) and from --api-key. Both are dummies.
os.environ["LLAMA_API_KEY"] = "env-key-123"
grid.append(["--backend", "llamacpp", "--suite", "pick", "--k", "1", "--limit", "2"])
grid.append(["--backend", "llamacpp", "--suite", "pick", "--k", "1", "--limit", "2", "--api-key", "argv-key-456"])

runs_dir = os.path.join(out_dir, "runs")
os.makedirs(runs_dir, exist_ok=True)
for n, argv in enumerate(grid):
    CURRENT["run"] = n
    out = os.path.join(runs_dir, f"run{n}.jsonl")
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        code = run.main(argv + ["--out", out])
    if code != 0:
        raise SystemExit(f"run.main exited {code} for {argv}: {sink.getvalue()[-500:]}")
with open(os.path.join(out_dir, "grid.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(grid, f)
with open(os.path.join(out_dir, "bodies.jsonl"), "w", encoding="utf-8", newline="\n") as f:
    for n, line in CAPTURED:
        f.write(f"{n}\t{line}\n")
print(f"{len(grid)} command lines, {len(CAPTURED)} request bodies -> {out_dir}")
