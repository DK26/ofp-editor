#!/usr/bin/env python3
"""Shared fixtures of the cloud-backend and free-mode tests (test_cloud*.py and test_free_mode*.py).

What it owns
------------
* The dummy secrets: ``KEY`` (a paid-endpoint test key), ``FREE_KEY`` (an OpenRouter-shaped key) and ``LABEL`` (the
  partly masked copy of it that OpenRouter's ``GET /key`` returns and that must never be shown). All are random per
  process and never real. ``SWEEP`` lists every secret-like string; the DPAPI tests add their own dummies to it.
* ``LOGS``: every console transcript a tool process printed, searched for those secrets when a module finishes.
* ``start(tag)`` / ``finish()``: one mock OpenAI-compatible server (mock_server.py, in-process on 127.0.0.1) and one
  work folder per test module. ``start`` also points ``LOCALAPPDATA`` and ``XDG_STATE_HOME`` into the work folder, so
  the per-user free-run lock and anything else keyed to the user's app-data folder stays out of the real profile
  (every child process inherits this). ``finish`` runs the final key sweep: no secret may appear in any file the
  module's tests wrote or in any console transcript; a leak fails the module (reported by unittest as an error in
  ``tearDownModule``).
* The helpers the case functions call by name: ``out``, ``run_tool``, ``rows``, ``calls``, ``base``, the free-mode
  argument builders and checks.

The case functions were written against module globals, so each test module star-imports this module (``__all__``
lists what it gets) and keeps its own ``URL`` global, which its ``setUpModule`` sets from ``start``.

Nothing here contacts a real endpoint or spends anything.
"""
import datetime as _dt
import json
import os
import secrets
import subprocess
import sys

import mock_server
import support
from mock_server import STATE
from support import TOOL, check, load_json, read_text, write_text

HERE = support.TESTS_DIR  # the helper scripts (dump_payloads.py, dpapi_*.ps1, probe_env.py) live next to the tests
KEY = "sk-mock-" + secrets.token_hex(16)
ENV_NAME = "CLOUDQUAL_TEST_KEY"
# Free-mode tests use an OpenRouter-shaped key; its GET /key "label" is a partly masked copy that must never be shown.
FREE_KEY = "sk-or-v1-" + secrets.token_hex(32)
LABEL = FREE_KEY[:12] + "..." + FREE_KEY[-3:]
SWEEP = [KEY, FREE_KEY, LABEL]  # every secret-like string the final sweep looks for (dummy keys are added)
LOGS = []  # every stdout/stderr the tool printed, scanned for the key at the end
FREE_MODEL = "mock/free-model:free"

URL = None  # the mock's API base of the running module (set by start)
WORK = None  # the running module's work folder (set by start)
_SERVER = None
_SAVED_ENV = {}
_REDIRECTED_ENV = ("LOCALAPPDATA", "XDG_STATE_HOME")

__all__ = ["HERE", "KEY", "ENV_NAME", "FREE_KEY", "LABEL", "SWEEP", "LOGS", "FREE_MODEL", "STATE", "TOOL", "check",
           "load_json", "read_text", "write_text", "mock_server", "out", "run_py", "run_tool", "rows", "calls", "base", "chat_bodies", "user_text",
           "root_url", "refused", "free_key", "free_state", "free_args", "run_free", "no_secrets", "stop_rows",
           "_age_reserve_rows", "free_lock_path"]


# ── Module lifecycle ─────────────────────────────────────────────────────────

def start(tag):
    """Start the mock server and a fresh work folder for one test module; returns the mock's API base URL."""
    global URL, WORK, _SERVER
    WORK = support.make_work(tag)
    os.makedirs(out("grades"))
    for name in _REDIRECTED_ENV:
        _SAVED_ENV[name] = os.environ.get(name)
        os.environ[name] = out("appdata")
    STATE.reset()
    _SERVER, URL = mock_server.start()
    return URL


def finish():
    """Stop the server, restore the environment, sweep every file and transcript for secrets, remove the folder."""
    global _SERVER
    if _SERVER is not None:
        _SERVER.shutdown()
        _SERVER.server_close()  # shutdown() only stops the loop; this closes the listening socket
        _SERVER = None
    for name in _REDIRECTED_ENV:
        if _SAVED_ENV.get(name) is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = _SAVED_ENV[name]
    leaked = []
    for root, _, files in os.walk(WORK):
        for name in files:
            with open(os.path.join(root, name), encoding="utf-8", errors="replace") as f:
                text = f.read()
            leaked += [os.path.relpath(os.path.join(root, name), WORK) for s in SWEEP if s in text]
    leaked += [f"console transcript {i}" for i, s in enumerate(LOGS) for k in SWEEP if k in s]
    n_logs = len(LOGS)
    LOGS.clear()
    support.remove_work(WORK)
    check(not leaked, f"final key sweep: {len(leaked)} places contain a key or the key label ({len(SWEEP)} secrets; "
                      f"every file of the work folder and {n_logs} console transcripts scanned): {leaked[:5]}")


# ── Helpers ──────────────────────────────────────────────────────────────────

def out(name):
    """A path inside the running module's work folder."""
    return os.path.join(WORK, name)


def run_py(script, args, env_extra=None, drop_key=False):
    """Run one of the tool's scripts as a child process with the test key in ENV_NAME; the transcript goes to LOGS."""
    env = support.child_env()
    if not drop_key:
        env[ENV_NAME] = KEY
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, os.path.join(TOOL, script)] + args, env=env, capture_output=True,
                       text=True, encoding="utf-8", timeout=600)
    LOGS.append(p.stdout + p.stderr)
    return p


def run_tool(args, **kw):
    """run.py with `args` (see run_py)."""
    return run_py("run.py", args, **kw)


def rows(path):
    """Every JSON line of a JSONL file (records and ledger rows alike)."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def calls(rs):
    """The call records among ledger rows: they carry a seed, budget events do not."""
    return [r for r in rs if "seed" in r and "budget_event" not in r]


def base(url, **over):
    """run.py arguments for a paid-mode run at the mock: 1 USD per million tokens, fast retries, no reasoning."""
    args = ["--backend", "openai", "--model", "mock/model-1", "--base-url", url, "--api-key-env", ENV_NAME,
            "--reasoning", "none", "--price-in", "1.0", "--price-out", "1.0", "--retry-base-s", "0.01",
            "--retry-cap-s", "0.05", "--price-as-of", "2026-09-27", "--price-source", "mock"]
    return args


def chat_bodies():
    """The bodies of the chat completions the mock received, in order."""
    return [r["body"] for r in STATE.requests if r["path"].endswith("/chat/completions")]


def user_text(body):
    """The user message of a chat body."""
    return next(m["content"] for m in body["messages"] if m["role"] == "user")


def root_url():
    """The mock's scheme://host:port, for redirect targets outside the API prefix."""
    return URL.rsplit("/api/v1", 1)[0]


def refused(p, needle):
    """True when a run was refused before sending (exit 2) with `needle` in its message."""
    return p.returncode == 2 and needle in p.stderr


# ── Free-only mode ───────────────────────────────────────────────────────────

def free_key(**over):
    """A GET /key record for a free-testing key (credit limit 0, nothing spent), in OpenRouter's documented shape,
    including the fields that must never be shown: the masked label and the account ids."""
    k = {"label": LABEL, "limit": 0, "limit_remaining": 0, "limit_reset": None, "include_byok_in_limit": False,
         "usage": 0, "usage_daily": 0, "usage_weekly": 0, "usage_monthly": 0, "byok_usage": 0, "byok_usage_daily": 0,
         "byok_usage_weekly": 0, "byok_usage_monthly": 0, "is_free_tier": True, "is_management_key": False,
         "is_provisioning_key": False, "expires_at": "2099-12-31T23:59:59Z", "allowed_data_regions": ["global"],
         "creator_user_id": "user_mock_creator_42", "organization_id": None, "workspace_id": "ws-mock-workspace-7",
         "rate_limit": {"interval": "1h", "note": "This field is deprecated and safe to ignore.", "requests": 1000}}
    k.update(over)
    return k


def free_state(**over):
    """The mock as a free account: zero prices (usage.cost 0), a free key, 50 free requests a day."""
    STATE.price_in = STATE.price_out = 0.0
    STATE.key = free_key(**over)
    STATE.free_daily_limit = 50


def free_args(ledger, model=FREE_MODEL, url=None):
    """run.py arguments for a free-only run at the mock with the shared ledger `ledger` (in the work folder)."""
    return ["--backend", "openai", "--free-only", "--model", model, "--base-url", url or URL, "--api-key-env",
            ENV_NAME, "--reasoning", "none", "--retry-base-s", "0.01", "--retry-cap-s", "0.05",
            "--ledger", out(ledger)]


def run_free(args, **kw):
    """run.py with the OpenRouter-shaped dummy key in ENV_NAME."""
    kw.setdefault("env_extra", {ENV_NAME: FREE_KEY})
    return run_tool(args, **kw)


def no_secrets(p, *paths):
    """Neither the key, its masked label nor the account ids from GET /key reach the console or the files."""
    text = p.stdout + p.stderr + "".join(read_text(x) for x in paths if os.path.exists(x))
    return not any(s in text for s in (FREE_KEY, LABEL, "user_mock_creator_42", "ws-mock-workspace-7"))


def stop_rows(path):
    """The budget_event "stop" rows of a file (none when it does not exist)."""
    return [r for r in rows(path) if r.get("budget_event") == "stop"] if os.path.exists(path) else []


def _age_reserve_rows(path, days=1):
    """Move every reserve row of a ledger `days` back (a simulated day boundary: the quota resets at 00:00 UTC)."""
    lines = []
    for r in rows(path):
        if r.get("budget_event") == "reserve":
            t = _dt.datetime.fromisoformat(r["ts"]) - _dt.timedelta(days=days)
            r["ts"] = t.isoformat(timespec="seconds")
        lines.append(json.dumps(r))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def free_lock_path():
    """The per-user free-run lock the runner's children use (LOCALAPPDATA / XDG_STATE_HOME point into the work folder)."""
    return os.path.join(out("appdata"), "plotroom-dev", "free-run.lock")
