#!/usr/bin/env python3
"""The free-only layer's second review and the Windows key scripts (cloud/*.ps1).

t51, t52 and t54-t57 each encode a hole found in review (the per-minute window across runs, key redaction, a
charge no response showed, two free runs on two ledgers, a wait across 00:00 UTC, the key variable left in
run.py's environment). t53 and t58 run the DPAPI key scripts through PowerShell with a random dummy key
(dpapi_round_trip.ps1, dpapi_trace.ps1, probe_env.py); they are skipped on other systems.

Every case runs run.py (or another tool script) as a child process against mock_server.py, in-process on
127.0.0.1: nothing is spent and no real endpoint is contacted. cloud_support.py holds the dummy keys, the
helpers and the final key sweep that fails the module if any key or key label reached a file or a console
transcript.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import io
import json
import os
import secrets
import subprocess
import sys
import unittest

import cloud_support
import support
from cloud_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = cloud_support.start("free-review")


def tearDownModule():
    cloud_support.finish()


# ── Second review of the free layer and the key scripts (t51-t58) ──────────────

def t51_rpm_window_carries_across_runs():
    """The per-minute window starts from the ledger's reserve rows, so a resume right after 18 attempts waits for the
    window instead of bursting past OpenRouter's 20 per minute."""
    import datetime as dt
    import time as _t
    free_state()
    led = out("rpm_ledger.jsonl")
    ts = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=56)).isoformat(timespec="seconds")
    with open(led, "w", encoding="utf-8") as f:
        for i in range(18):
            f.write(json.dumps({"budget_event": "reserve", "call_id": f"earlier{i}", "attempt": 1,
                                "reserved_usd": 0.0, "ts": ts}) + "\n")
            f.write(json.dumps({"budget_event": "settle", "call_id": f"earlier{i}", "cost_usd": 0.0, "ts": ts}) + "\n")
    t0 = _t.monotonic()
    p = run_free(free_args("rpm_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "2", "--out",
                                                  out("rpm.jsonl")])
    took = _t.monotonic() - t0
    recs = calls(rows(out("rpm.jsonl")))
    waits = [r["rate_gate"]["rate_wait_s"] for r in recs]
    check(p.returncode == 0 and waits[0] >= 0.9 and waits[1] == 0 and recs[0]["rate_gate"]["attempts_today"] >= 19,
          f"exit {p.returncode}, waits {waits}")
    q = run_free(free_args("rpm_fresh.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "2", "--out",
                                                 out("rpm_fresh.jsonl")])
    fresh = [r["rate_gate"]["rate_wait_s"] for r in calls(rows(out("rpm_fresh.jsonl")))]
    check(q.returncode == 0 and fresh == [0, 0], f"fresh ledger waits {fresh}")
    return (f"18 attempts 56 s ago in the ledger: the first call waited {waits[0]} s (run {took:.1f} s), counted as "
            f"attempt {recs[0]['rate_gate']['attempts_today']} today; a fresh ledger waits 0")


def t52_free_mode_redaction_of_keys_and_label():
    """Anything shaped like an OpenRouter key (the key in use, another key, the masked label) is redacted from every
    record and console line, even when a provider echoes it."""
    free_state()
    other = "sk-or-v1-" + "d" * 64
    found = []
    for i, body in enumerate(("ECHO_AUTH", {"error": {"code": 500, "message": f"bad key {other} ({LABEL})"}})):
        STATE.queue = [{"status": 500, "body": body}] * 2
        o = out(f"redact_free{i}.jsonl")
        p = run_free(free_args(f"redact_free{i}_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1",
                                                                   "--max-attempts", "2", "--out", o])
        err = calls(rows(o))[0]["error"]
        check(p.returncode == 2 and "[REDACTED]" in err and other not in read_text(o) + p.stdout
              + p.stderr and no_secrets(p, o), f"case {i}: exit {p.returncode}, error {err!r}")
        found.append(err.split("HTTP 500: ", 1)[-1])
    return f"errors as recorded: {found[0]!r}; {found[1]!r}"


def t53_dpapi_key_scripts_round_trip():
    """set-openrouter-key.ps1 stores a DPAPI blob with a user-only access list; run-cloud.ps1 hands the key to one
    child process through its environment only; refusals start no child; run.py's --output alias passes through
    ``powershell -File`` (where --out cannot, see t62); remove-openrouter-key.ps1 deletes the key.

    Why: the key must never be plaintext on disk, in a command line or in this session, and the launcher must work
    exactly as the runbook starts it.

    How: a random dummy key only; the PowerShell side is dpapi_round_trip.ps1 (14 PASS/FAIL lines), with probe_env.py
    standing in for run.py where the test needs to see what the child received.
    """
    if os.name != "nt":
        return "skipped (not Windows)"
    free_state()
    dummy = "sk-or-v1-" + secrets.token_hex(32)
    SWEEP.append(dummy)
    env = dict(os.environ, CLOUDQUAL_DUMMY_KEY=dummy, PYTHONIOENCODING="utf-8")
    for k in (ENV_NAME, "OPENROUTER_API_KEY", "LLAMA_API_KEY"):
        env.pop(k, None)
    work = out("secrets")
    p = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                        os.path.join(HERE, "dpapi_round_trip.ps1"), "-Tool", TOOL, "-Work", work, "-BaseUrl", URL,
                        "-Python", sys.executable, "-Probe", os.path.join(HERE, "probe_env.py")],
                       env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    LOGS.append(p.stdout + p.stderr)
    lines = [ln for ln in p.stdout.splitlines() if ln.startswith(("PASS ", "FAIL "))]
    fails = [ln for ln in lines if ln.startswith("FAIL ")]
    auth = [r["headers"].get("Authorization") for r in STATE.requests if r["path"].endswith("/chat/completions")]
    check(p.returncode == 0 and len(lines) == 14 and not fails, f"exit {p.returncode}; {fails or p.stderr[-400:]}")
    check(auth == [f"Bearer {dummy}"], f"the run launched by run-cloud.ps1 sent {len(auth)} calls with the stored key: "
                                       f"{[a == f'Bearer {dummy}' for a in auth]}")
    check(dummy not in p.stdout + p.stderr, "the dummy key was printed")
    return "; ".join(ln[5:].split(":", 1)[0] for ln in lines) + " all PASS; " + " | ".join(
        ln.split(": ", 1)[1] for ln in lines[:2] + lines[3:5])


def t54_unseen_charge_is_caught_on_every_stop_and_across_runs():
    """A charge that lands after a run's last key read is never forgotten: every stop of a started free run reads the
    key once more (a rise is exit 9), and each ledger keeps the key's last usage, so the next start on it refuses
    (exit 9, nothing sent) when the usage rose in between.

    Why: free reservations are 0, so the ledger's spent total cannot show a charge the response did not report (a
    stream or proxy page, a timeout); before this, only a run that finished normally read the key at the end, and
    every start took the key's current usage as a fresh baseline, so a killed or fatally stopped run's charge vanished.
    """
    # ── (a) A fatal stop after a charged call: a non-JSON 200 is a config stop whose cost the body cannot show ──
    free_state()
    STATE.key_usage_per_chat = 0.0001
    STATE.queue = [{"status": 200, "body": 'data: {"choices": []}\n\ndata: [DONE]\n\n'}]
    o = out("unseen_a.jsonl")
    p = run_free(free_args("unseen_a_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out", o])
    stops = [r["stop"] for r in stop_rows(o)]
    check(p.returncode == 9 and STATE.count() == 1 and "usage rose" in p.stderr and stops[-1:] == ["NotFree"],
          f"fatal stop with a charge: exit {p.returncode}, {STATE.count()} calls, stops {stops}")
    # ── (b) A run that ended without its final key read (killed): the ledger's last reading is the baseline ──
    STATE.reset()
    free_state()
    led = "unseen_b_ledger.jsonl"
    p1 = run_free(free_args(led) + ["--suite", "pick", "--k", "1", "--limit", "2", "--out", out("unseen_b1.jsonl")])
    key_rows = [r for r in rows(out(led)) if r.get("budget_event") == "key"]
    allowed = {"budget_event", "usage", "byok_usage", "usage_daily", "free_model_daily_requests", "ts"}
    check(p1.returncode == 0 and len(key_rows) >= 2 and all(set(r) <= allowed for r in key_rows)
          and no_secrets(p1, out(led)), f"first run: exit {p1.returncode}, key rows {key_rows}")
    STATE.key["usage"] = 0.0001  # billed after the last reading (a run killed before its end check)
    n = STATE.count()
    p2 = run_free(free_args(led) + ["--suite", "pick", "--k", "1", "--limit", "2", "--out", out("unseen_b2.jsonl")])
    check(p2.returncode == 9 and STATE.count() == n and "since this ledger" in p2.stderr
          and stop_rows(out("unseen_b2.jsonl"))[-1]["stop"] == "NotFree",
          f"start after an unseen charge: exit {p2.returncode}, {STATE.count() - n} calls, {p2.stderr[-300:]!r}")
    # ── (c) Boundary: a reading equal to the ledger's last one starts; BYOK usage counts the same way ──
    STATE.reset()
    free_state(usage=0.0001)
    p3 = run_free(free_args("unseen_c.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out",
                                                 out("unseen_c1.jsonl")])
    p4 = run_free(free_args("unseen_c.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out",
                                                 out("unseen_c2.jsonl")])
    STATE.key["byok_usage"] = 0.002
    p5 = run_free(free_args("unseen_c.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out",
                                                 out("unseen_c3.jsonl")])
    check(p3.returncode == 0 and p4.returncode == 0 and p5.returncode == 9 and STATE.count() == 2,
          f"equal usage: exit {p3.returncode}, {p4.returncode}; BYOK rise: exit {p5.returncode}; {STATE.count()} calls")
    return ("non-JSON 200 while the key's usage rose: exit 9 NotFree (was a plain config stop, exit 5); a charge after "
            "the last reading of a finished run: the next start on that ledger exit 9 with 0 calls; key rows hold only "
            "usage figures and the daily counter; equal usage starts twice, a BYOK rise refuses")


def t55_one_free_run_at_a_time_per_account():
    """Free runs on different ledgers cannot run side by side: a per-user lock keeps OpenRouter's per-account limits
    (20 a minute, 50 a day) from being counted twice; a stale lock blocks with the fix named; paid runs ignore it.

    Why: the ledger lock only serialises runs that share a ledger, so two free runs on two ledgers each kept their own
    minute window and day count and together could send up to twice the client caps.
    """
    import time
    free_state()
    STATE.delay_s = 0.4
    env = dict(os.environ, PYTHONIOENCODING="utf-8", **{ENV_NAME: FREE_KEY})
    env.pop("LLAMA_API_KEY", None)
    a = subprocess.Popen([sys.executable, os.path.join(TOOL, "run.py")] + free_args("par_a_ledger.jsonl") +
                         ["--suite", "pick", "--k", "1", "--limit", "4", "--out", out("par_a.jsonl")], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    deadline = time.monotonic() + 30
    while STATE.count() == 0 and time.monotonic() < deadline:
        time.sleep(0.05)
    b = run_free(free_args("par_b_ledger.jsonl") + ["--suite", "fill", "--k", "1", "--limit", "3", "--out",
                                                    out("par_b.jsonl")])
    sa, ea = a.communicate(timeout=120)
    LOGS.append(sa + ea)
    STATE.delay_s = 0.0
    fill_calls = sum(1 for r in STATE.requests if r["body"] and "Fill these fields" in json.dumps(r["body"]))
    check(b.returncode == 5 and fill_calls == 0 and "another free-only run" in b.stderr,
          f"second free run on another ledger: exit {b.returncode}, {fill_calls} calls, {b.stderr[-300:]!r}")
    check(a.returncode == 0 and len(calls(rows(out("par_a.jsonl")))) == 4 and not os.path.exists(free_lock_path()),
          f"first run: exit {a.returncode}; lock left: {os.path.exists(free_lock_path())}")
    # A lock left by a killed free run blocks the next one (fail closed) and names the file; a paid run is not blocked.
    os.makedirs(os.path.dirname(free_lock_path()), exist_ok=True)
    write_text(free_lock_path(), '{"pid": 1}')
    n = STATE.count()
    c = run_free(free_args("par_c_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out",
                                                    out("par_c.jsonl")])
    d = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--ledger",
                              out("par_d_ledger.jsonl"), "--out", out("par_d.jsonl")])
    os.remove(free_lock_path())
    check(c.returncode == 5 and "free-run.lock" in c.stderr and d.returncode == 0 and STATE.count() == n + 1,
          f"stale lock: free exit {c.returncode}, paid exit {d.returncode}, {STATE.count() - n} calls")
    return ("free run B on its own ledger while A ran: exit 5, 0 calls; A finished 4 calls and removed the lock; a "
            "stale lock blocks a free run (exit 5, file named) but not a paid run")


def t56_rate_gate_day_edge_and_whole_second_ledger_times():
    """A per-minute wait that crosses 00:00 UTC counts the attempt in the new day (after a forced key poll); ledger
    times, written in whole seconds, keep an attempt in the minute window until a full minute after it could have
    been sent.

    Why: the day check ran before the wait, so an attempt sent just after midnight was booked to the old day and the
    new day's account counter was not read first; a stamp truncated to the second let a resumed run drop an attempt
    from the window up to a second early and burst past OpenRouter's 20 a minute.
    """
    import datetime as dt
    import rate_gate as rg
    utc = dt.timezone.utc
    t = [dt.datetime(2026, 9, 27, 23, 59, 30, tzinfo=utc).timestamp()]
    midnight = dt.datetime(2026, 9, 28, tzinfo=utc).timestamp()
    polls = []

    def sleep(s):
        t[0] += s

    def poll():
        polls.append(t[0])
        return None, {"used": 0, "limit": 50, "remaining": 50}
    g = rg.RateGate(rpm=1, per_day=5, server={"used": 10, "limit": 50, "remaining": 40}, poll=poll, poll_every=10,
                    clock=lambda: t[0], sleep=sleep)
    check(g.before_attempt() is None and g.used_local == 1, "first attempt")
    check(g.before_attempt() is None, "second attempt (waits past midnight)")
    check(g.day == dt.date(2026, 9, 28) and g.used_local == 1 and len(polls) == 1 and polls[0] >= midnight
          and g.server_remaining == 49, f"day {g.day}, used {g.used_local}, polls {polls}, left {g.server_remaining}")
    # ── Whole-second ledger stamps: 60.5 s after the stamp the attempt may be 59.6 s old, so it stays ──
    stamp = dt.datetime(2026, 9, 27, 12, 0, 0, tzinfo=utc)
    seed = [{"budget_event": "reserve", "ts": stamp.isoformat(timespec="seconds")}]
    inside = rg.RateGate(rpm=1, rows=seed, clock=lambda: stamp.timestamp() + 60.5)
    outside = rg.RateGate(rpm=1, rows=seed, clock=lambda: stamp.timestamp() + 61.0)
    check(len(inside.window) == 1 and len(outside.window) == 0,
          f"window at +60.5 s: {len(inside.window)}, at +61 s: {len(outside.window)}")
    return ("wait from 23:59:31 crossed midnight: attempt counted 1 on 2026-09-28 after 1 forced poll (49 left); a "
            "whole-second stamp stays in the window at +60.5 s and leaves at +61 s")


def t57_key_variable_leaves_the_run_environment():
    """Once run.py has read the key, the variable is gone from its environment, so no process it starts inherits it.

    Why: run-cloud.ps1 gives the key to run.py alone; a helper process started later (a grader, a shell-out in a future
    change) would otherwise inherit it silently.
    """
    import contextlib
    import run as runmod
    free_state()
    os.environ[ENV_NAME] = FREE_KEY
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            code = runmod.main(free_args("envpop_ledger.jsonl") + ["--suite", "pick", "--items", "PW01", "--k", "1",
                                                                   "--out", out("envpop.jsonl")])
        present = ENV_NAME in os.environ
        child = subprocess.run([sys.executable, "-c", f"import os; print(os.environ.get({ENV_NAME!r}) is None)"],
                               capture_output=True, text=True)
    finally:
        os.environ.pop(ENV_NAME, None)
    LOGS.append(sink.getvalue())
    child_sees = child.stdout.strip() != "True"
    check(code == 0 and not present and not child_sees,
          f"exit {code}; variable still in run.py's environment: {present}; a child started afterwards sees it: "
          f"{child_sees}")
    return "in-process free run: exit 0; the variable was removed after reading, and a child started afterwards sees none"


def t58_key_scripts_under_powershell_tracing():
    """With Set-PSDebug -Trace 2 on in the calling session (the scripts run in-process), neither storing a key with a
    trailing space nor launching a run prints any 16-character piece of the key to the console.

    Why: trace level 2 prints every variable assignment with its value (the first 55 characters of the key, most of
    its secret part), and a transcript would save it to disk.

    How: dpapi_trace.ps1 runs in a child powershell.exe whose whole console output is captured here and searched for
    every 16-character window of the dummy key's secret part; the dummy is never printed.
    """
    if os.name != "nt":
        return "skipped (not Windows)"
    found = []
    for which in ("set", "run"):
        dummy = "sk-or-v1-" + secrets.token_hex(32)
        SWEEP.append(dummy)
        env = dict(os.environ, PROBE_DUMMY=dummy)
        p = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                            os.path.join(HERE, "dpapi_trace.ps1"), "-Tool", TOOL, "-Work", out("trace"), "-Python",
                            sys.executable, "-Which", which], env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        text = p.stdout + p.stderr
        secret = dummy[len("sk-or-v1-"):]
        pieces = sum(1 for i in range(len(secret) - 15) if secret[i:i + 16] in text)
        traced = text.count("DEBUG:")
        found.append((which, p.returncode, traced, pieces))
    check(all(code == 0 and traced > 0 and pieces == 0 for _, code, traced, pieces in found), str(found))
    return "; ".join(f"{w}: {tr} trace lines, {pc} key pieces" for w, _, tr, pc in found)


# ── unittest wiring ──────────────────────────────────────────────────────────

class FreeReviewTests(support.CaseTestCase):
    """Second-review checks of free mode and the key scripts (see the module docs)."""

    cases = (t51_rpm_window_carries_across_runs,
             t52_free_mode_redaction_of_keys_and_label,
             t53_dpapi_key_scripts_round_trip,
             t54_unseen_charge_is_caught_on_every_stop_and_across_runs,
             t55_one_free_run_at_a_time_per_account,
             t56_rate_gate_day_edge_and_whole_second_ledger_times,
             t57_key_variable_leaves_the_run_environment,
             t58_key_scripts_under_powershell_tracing)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
