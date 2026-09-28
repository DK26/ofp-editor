#!/usr/bin/env python3
"""Shared fixtures of the scaffold-arm tests (test_scaffolds*.py).

What it owns
------------
* ``start(tag)`` / ``finish()``: one mock llama-server and Ollama (mock_reason.py, in-process on 127.0.0.1) and one
  work folder per test module; ``reset_mock()`` returns the mock to a clean state with the deterministic "model"
  below, before every case.
* The suites the tests read (``SUITES``; ``PICK_ITEMS`` and ``ITEMS`` over pick and pick-hard) and the staged pools
  (``POOL``). The pools are research material kept outside this folder: set ``LOCALQUAL_POOLS`` to the folder holding
  ``pick-pool.json`` and ``fill-pool.json`` to include them. Only their tune halves are ever loaded (``tune_only``),
  so the held-out halves stay unseen. Without them, the two checks that need a pool-shaped suite file (c12, d07) use
  ``pick_pool()``: a copy of pick-hard renamed ``pick-pool`` whose items all carry ``"split": "tune"``.
* A deterministic mock "model" that sees only the prompt (``model_chat``, ``model_dist``): its choices depend on the
  prompt text alone, through a hash of each menu line, never on an item's answer. Two runs with identical prompts get
  identical replies, which the answer-swap check (b02) relies on.
* Helpers the case functions call by name: ``out``, ``run_py``, ``lc_args``, ``rows``, ``posts``, ``write_suite``,
  ``words``.

The case functions were written against module globals, so each test module star-imports this module (``__all__``
lists what it gets) and keeps its own ``URL`` global, which its ``setUpModule`` sets from ``start``.
"""
import copy
import hashlib
import json
import os
import re
import subprocess
import sys

import support
from support import TOOL, check

import control_suite  # noqa: E402 - the tool's modules, importable once support put the tool on sys.path
import mock_reason  # noqa: E402
import scaffold_stats  # noqa: E402
import scaffolds as sc  # noqa: E402
from mock_reason import STATE, menu_of  # noqa: E402
from prompts import SYSTEM, build_pick_order, permute_options, sample_seed  # noqa: E402

HERE = support.TESTS_DIR
POOLS = os.environ.get("LOCALQUAL_POOLS")  # optional folder of the staged pools (see the module docs)
URL = None  # the mock's base URL of the running module (set by start)
WORK = None  # the running module's work folder (set by start)
_SERVER = None


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


SUITES = {n: _load(os.path.join(TOOL, "suites", n + ".json")) for n in ("pick", "pick-hard", "fill")}


def tune_only(name):
    """The staged pool `name` with only its tune items (the held-out half is never loaded into the fixtures)."""
    if not POOLS:
        return None
    path = os.path.join(POOLS, name + ".json")
    if not os.path.exists(path):
        return None
    suite = _load(path)
    suite["items"] = [it for it in suite["items"] if it.get("split") == "tune"]
    return suite


def pick_pool():
    """The staged pick pool's tune half, or without it a stand-in with the same shape: pick-hard's 30 items renamed
    (ids prefixed "SP-"), each marked ``"split": "tune"``, in a suite named ``pick-pool``.

    Why: c12 and d07 test how --suite-file, --split and scaffold_stats.py handle a pool file (its own suite name, a
    split field, records that only score with the file); a copy of a built-in suite exercises exactly that, and keeps
    both checks running on a machine without the research pools.
    """
    real = POOL["pick-pool"]
    if real:
        return real
    suite = copy.deepcopy(SUITES["pick-hard"])
    suite["suite"], suite["shape"] = "pick-pool", "pick"
    for it in suite["items"]:
        it["id"], it["split"] = "SP-" + it["id"], "tune"
    return suite


POOL = {"pick-pool": tune_only("pick-pool"), "fill-pool": tune_only("fill-pool")}
PICK_ITEMS = [it for n in ("pick", "pick-hard") for it in SUITES[n]["items"]] + (
    POOL["pick-pool"]["items"] if POOL["pick-pool"] else [])
ITEMS = {it["id"]: it for it in PICK_ITEMS}
PREFIX = '{"choice": "'
# The arm runs the leakage checks repeat: (arm, condition, extra flags).
ARM_RUNS = [("why", "none", []), ("diff", "none", []), ("diff", "cards", []), ("rule", "cards", []),
            ("eliminate", "none", []), ("eliminate", "cards", ["--scaffold-keep", "2"]), ("pairwise", "none", []),
            ("subq", "none", []), ("subq", "cards", []), ("prefill", "none", []),
            ("prefill", "cards", ["--prefill-channel", "think"])]

__all__ = ["HERE", "TOOL", "check", "control_suite", "mock_reason", "scaffold_stats", "sc", "STATE", "menu_of",
           "SYSTEM", "build_pick_order", "permute_options", "sample_seed", "SUITES", "POOL", "PICK_ITEMS", "ITEMS",
           "PREFIX", "ARM_RUNS", "_load", "tune_only", "pick_pool", "_h", "model_dist", "user_of", "model_chat",
           "reset_mock", "out", "run_py", "lc_args", "rows", "posts", "write_suite", "words"]


# ── Module lifecycle ─────────────────────────────────────────────────────────

def start(tag):
    """Start the mock server and a fresh work folder for one test module; returns the mock's base URL."""
    global URL, WORK, _SERVER
    WORK = support.make_work(tag)
    reset_mock()
    _SERVER, URL = mock_reason.start()
    return URL


def finish():
    """Stop the mock and remove the work folder."""
    global _SERVER
    if _SERVER is not None:
        _SERVER.shutdown()
        _SERVER.server_close()  # shutdown() only stops the loop; this closes the listening socket
        _SERVER = None
    support.remove_work(WORK)


# ── A deterministic mock "model" that sees only the prompt ───────────────────

def _h(text):
    """A stable 32-bit hash of a text (SHA-256 based, so it is the same on every machine and run)."""
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def model_dist(menu, prompt):
    """Letter probabilities from a hash of each menu line (plus a small X share)."""
    w = {letter: 1 + _h(text) % 9 for letter, text in menu.items()}
    total = sum(w.values())
    return [(letter, 0.9 * x / total) for letter, x in w.items()] + [("\n", 0.1)]


def user_of(body):
    """The last user message of a chat body ("" when there is none)."""
    msgs = body.get("messages") or []
    return next((m.get("content") for m in reversed(msgs) if m.get("role") == "user"), "") or ""


def model_chat(body):
    """Pick: the menu letter with the largest line hash; subq: yes/no/unclear by statement hash; Fill: a record built
    from the schema (enums take their first value, strings the request's first three words)."""
    user = user_of(body)
    ids = re.findall(r"^(s\d+): (.*)$", user, flags=re.M)
    if ids:
        return json.dumps({sid: sc.SUBQ_VALUES[_h(text) % 3] for sid, text in ids})
    menu = menu_of(user)
    if menu:
        return json.dumps({"choice": max(menu, key=lambda letter: _h(menu[letter]))})
    m = re.search(r'Request: "(.*)"', user)
    words_ = (m.group(1) if m else "").split()[:3]
    schema = ((body.get("response_format") or {}).get("json_schema") or {}).get("schema") or body.get("format") or {}
    result = {}
    for k, spec in (schema.get("properties") or {}).items():
        if "enum" in spec:
            result[k] = spec["enum"][0]
        elif spec.get("type") == "string":
            result[k] = " ".join(words_)
        else:
            result[k] = None
    return json.dumps(result)


def reset_mock():
    """A clean mock with the prompt-only model above (what every case starts from)."""
    STATE.reset()
    STATE.chat_fn = model_chat
    STATE.dist_fn = model_dist


# ── Helpers ──────────────────────────────────────────────────────────────────

def out(name):
    """A path inside the running module's work folder."""
    return os.path.join(WORK, name)


def run_py(args, script="run.py"):
    """Run one of the tool's scripts as a child process (see support.child_env)."""
    return subprocess.run([sys.executable, os.path.join(TOOL, script)] + args, env=support.child_env(),
                          capture_output=True, text=True, encoding="utf-8", timeout=900)


def lc_args(out_name, *extra, suite="pick-hard", items="HW01", k=1):
    """run.py arguments for a llama-server run against the mock, written to the work folder's <out_name>."""
    a = ["--backend", "llamacpp", "--base-url", URL, "--k", str(k), "--wait", "5", "--out", out(out_name)]
    if suite:
        a += ["--suite", suite]
    if items:
        a += ["--items", items]
    return a + list(extra)


def rows(path):
    """Every JSON line of a JSONL file ([] when it does not exist)."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def posts(*paths):
    """Bodies of the POST requests the mock saw (optionally only these paths), in order."""
    with STATE.lock:
        return [(r["path"], r["body"]) for r in STATE.requests
                if r["body"] is not None and (not paths or r["path"] in paths)]


def write_suite(name, suite):
    """Write a suite dict to the work folder (for --suite-file) and return its path."""
    path = out(name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(suite, f, ensure_ascii=False, indent=1)
    return path


def words(text):
    """The lower-case word set of a text (letters, digits, '#' and apostrophes)."""
    return set(re.findall(r"[a-z0-9#']+", (text or "").lower()))
