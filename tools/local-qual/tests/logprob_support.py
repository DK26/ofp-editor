#!/usr/bin/env python3
"""Shared fixtures of the logprob Pick and cascade tests (test_logprob_*.py).

What it owns
------------
* ``start(tag)`` / ``finish()``: one mock llama-server (mock_llama.py, in-process on 127.0.0.1) and one work folder
  per test module.
* The suites the tests read (``SUITES``, ``ITEMS``) and ``LABEL``, the model label run.py derives from the mock's
  model file name.
* A scriptable mock "model": ``weights_dist`` turns per-option weights into the next-token list the mock returns,
  spread over the token variants a real vocabulary has for one letter ("A", " A", 'A"'), plus non-letter filler, so
  each test knows every probability by hand.
* Helpers the case functions call by name: ``out``, ``run_py``, ``lp_args``, ``rows``, ``item_for``,
  ``key_by_line``, ``letter_of``, ``completions``, ``close``.

The case functions were written against module globals, so each test module star-imports this module (``__all__``
lists what it gets) and keeps its own ``URL`` global, which its ``setUpModule`` sets from ``start``.
"""
import json
import os
import subprocess
import sys

import support
from support import TOOL, check, load_json

import cascade  # noqa: E402 - the tool's modules, importable once support put the tool on sys.path
import logprob_pick as lp  # noqa: E402
import mock_llama  # noqa: E402
from mock_llama import STATE, menu_of, render  # noqa: E402
from prompts import SYSTEM, permute_options, sample_seed  # noqa: E402

HERE = support.TESTS_DIR
URL = None  # the mock's base URL of the running module (set by start)
WORK = None  # the running module's work folder (set by start)
_SERVER = None


def _load(name):
    with open(os.path.join(TOOL, "suites", name + ".json"), encoding="utf-8") as f:
        return json.load(f)


SUITES = {n: _load(n) for n in ("pick", "pick-hard")}
ITEMS = {it["id"]: it for s in SUITES.values() for it in s["items"]}
LABEL = "Mock-4B-Q4_K_M"  # the label run.py derives from the mock's model file
PREFIX = '{"choice": "'
# Token variants of one letter and their shares of its probability ("A" 70%, " A" 20%, 'A"' 10%).
VARIANTS3 = (("{L}", 0.7), (" {L}", 0.2), ('{L}"', 0.1))
# Non-letter tokens that take a little of the mass, as a real next-token list always has.
FILLER = [("\n", 0.05), ("{", 0.03), ("The", 0.02)]
# PW01's hand-set weights and the renormalised probabilities they must give (see l03).
PW01_W = {"hold": 5, "sentry": 2, "none_fit": 1, "move": 1, "guard": 1}
PW01_P = {"hold": 0.5, "sentry": 0.2, "none_fit": 0.1, "move": 0.1, "guard": 0.1, "cycle": 0.0, "sad": 0.0}

__all__ = ["HERE", "TOOL", "check", "load_json", "cascade", "lp", "mock_llama", "STATE", "menu_of", "render", "SYSTEM",
           "permute_options", "sample_seed", "SUITES", "ITEMS", "LABEL", "PREFIX", "VARIANTS3", "FILLER", "PW01_W",
           "PW01_P", "close", "out", "run_py", "lp_args", "rows", "item_for", "key_by_line", "letter_of",
           "weights_dist", "completions"]


# ── Module lifecycle ─────────────────────────────────────────────────────────

def start(tag):
    """Start the mock llama-server and a fresh work folder for one test module; returns the mock's base URL."""
    global URL, WORK, _SERVER
    WORK = support.make_work(tag)
    STATE.reset()
    _SERVER, URL = mock_llama.start()
    return URL


def finish():
    """Stop the mock and remove the work folder."""
    global _SERVER
    if _SERVER is not None:
        _SERVER.shutdown()
        _SERVER.server_close()  # shutdown() only stops the loop; this closes the listening socket
        _SERVER = None
    support.remove_work(WORK)


# ── Helpers ──────────────────────────────────────────────────────────────────

def close(a, b, tol=1e-6):
    """True when two numbers (neither None) agree within `tol`."""
    return a is not None and b is not None and abs(a - b) <= tol


def out(name):
    """A path inside the running module's work folder."""
    return os.path.join(WORK, name)


def run_py(args, script="run.py"):
    """Run one of the tool's scripts as a child process (see support.child_env)."""
    return subprocess.run([sys.executable, os.path.join(TOOL, script)] + args, env=support.child_env(),
                          capture_output=True, text=True, encoding="utf-8", timeout=600)


def lp_args(out_name, *extra, suite="pick", items="PW01", k=1):
    """run.py arguments for a logprob run against the mock, written to the work folder's <out_name>."""
    return (["--backend", "llamacpp", "--base-url", URL, "--suite", suite, "--pick-mode", "logprob", "--items",
             items, "--k", str(k), "--wait", "5", "--out", out(out_name)] + list(extra))


def rows(path):
    """Every JSON line of a JSONL file ([] when it does not exist)."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def item_for(prompt):
    """The suite item whose request line is in the prompt (None for the preflight's 'ping')."""
    for it in ITEMS.values():
        if f"Request: {it['request']}\n" in prompt:
            return it
    return None


def key_by_line(item):
    """{menu line text: option key}: "label: desc" for the real options, the label alone for the escape."""
    m = {f"{o['label']}: {o['desc']}": o["key"] for o in item["options"]}
    m[item["escape"]["label"]] = item["escape"]["key"]
    return m


def letter_of(menu, item, key):
    """The letter the rendered menu gives option `key`."""
    keys = key_by_line(item)
    return next(letter for letter, text in menu.items() if keys[text] == key)


def weights_dist(weight, letter_share=0.9, variants=VARIANTS3, filler=FILLER, bias=None):
    """A mock model: each menu letter gets letter_share x (weight(item, key) + bias[letter]) / total, spread over
    the token variants (default "L" 70%, " L" 20%, 'L"' 10%), plus non-letter filler tokens."""
    def fn(menu, prompt):
        item = item_for(prompt)
        if item is None:
            return list(filler) or [("Hello", 1.0)]
        keys = key_by_line(item)
        w = {letter: weight(item, keys[text]) + (bias or {}).get(letter, 0.0) for letter, text in menu.items()}
        total = sum(w.values())
        entries = []
        for letter, x in w.items():
            if x > 0:
                entries += [(pat.format(L=letter), letter_share * x / total * share) for pat, share in variants]
        return entries + list(filler)
    return fn


def completions(menu_only=True):
    """The /completion bodies the mock received (only those with a menu, unless menu_only is False)."""
    return [r["body"] for r in STATE.paths("/completion") if not menu_only or "Options:" in r["body"]["prompt"]]
