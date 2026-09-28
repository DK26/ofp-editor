#!/usr/bin/env python3
"""End-to-end tests of ``run.py --preset`` (D048, doc 55 section 3) against the mock llama-server and Ollama.

p15-p21: a preset run sends byte for byte what the equivalent flags send, and every record carries the preset's id,
version, SHA-256 (and its base's), the flags it set, what it left out and whether the served model is the one it is
bound to; a template without a thinking switch gets no switch; the bounded why and letter-probability knobs run the
arms run.py already has; a flag that contradicts the preset, a knob run.py cannot honour, an invalid or withdrawn
preset file and a suite without a step kind are refused before any request; --resume refuses an output file whose
records of the same label were made with another preset hash, with a preset where the run has none, or without one
where the run has one; a dry run prints the preset's request.

Without --preset nothing changes: a01 (test_scaffolds.py) and t01 (test_cloud_regression.py) compare every existing
command line's requests and records with goldens frozen before this flag existed.

Runs against mock_reason.py (in-process on 127.0.0.1); no model runs.
"""
import hashlib
import json
import os
import shutil
import unittest

import scaffold_support
import support
from scaffold_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)
DRAFTS = os.path.join(TOOL, "presets", "drafts")
QWEN = os.path.join(DRAFTS, "qwen3.5-4b-q4_k_m.preset.json")
GRANITE = os.path.join(DRAFTS, "granite-4.1-3b-q4_k_m.preset.json")
DEFAULT = os.path.join(DRAFTS, "default.preset.json")
MOCK_LABEL = "Mock-4B-Q4_K_M"  # the served file's name without .gguf, run.py's llamacpp label (mock_reason /props)


def setUpModule():
    global URL
    URL = scaffold_support.start("presets-run")


def tearDownModule():
    scaffold_support.finish()


# ── Fixtures ─────────────────────────────────────────────────────────────────

def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def child(name, **pick_changes):
    """Write a preset extending default@0.1.0 with the given Pick settings into the work folder, next to a copy of
    the default draft (a preset's base is looked up next to it); returns its path."""
    folder_ = out("presets")
    os.makedirs(folder_, exist_ok=True)
    shutil.copy(DEFAULT, os.path.join(folder_, "default.preset.json"))
    doc = {"format": "plotroom.harness-preset/1", "preset_id": name, "version": "0.1.0", "status": "draft",
           "extends": "default@0.1.0", "binds_to": {"kind": "any"}, "step_kinds": {"pick": pick_changes},
           "provenance": {"created": "2026-09-28", "authors": ["test"], "tuning_runs": [], "held_out": []},
           "notes": ["test fixture"]}
    if name != "default":
        # Only the default may bind to any; a test child binds to the mock's file so the binding check matches.
        doc["binds_to"] = {"kind": "local-gguf", "model": {
            "repo": "example/Mock-4B-GGUF", "revision": "0" * 40, "file": "Mock-4B-Q4_K_M.gguf", "bytes": 1,
            "sha256": "0" * 64}, "quant_label": "Q4_K_M", "chat_template_sha256": None,
            "runtime": {"name": "llama.cpp", "build": "b1", "backend": "cpu"}, "context_tokens": 8192}
    path = os.path.join(folder_, name + ".preset.json")
    support.write_text(path, json.dumps(doc, indent=1) + "\n")
    return path


def chat_bodies():
    """The chat request bodies the mock saw, as one JSON text (so an int sent as a float, 0 against 0.0, differs)."""
    return json.dumps([b for _, b in posts("/v1/chat/completions", "/api/chat")])


def refused(args, *fragments):
    """Run run.py with `args`; it must exit 2 naming every fragment on stderr and send nothing at all."""
    reset_mock()
    p = run_py(args)
    check(p.returncode == 2 and all(f in p.stderr for f in fragments),
          f"exit {p.returncode}, stderr lacks {fragments}: {p.stderr[-700:]}")
    check(not STATE.requests, f"{len(STATE.requests)} requests sent before the refusal")
    return p.stderr


# ── Basic functionality ──────────────────────────────────────────────────────

def p15_preset_run_sends_what_its_flags_send_and_records_the_preset():
    """A run with the Qwen draft sends exactly the bodies of the same run with the preset's flags written out, and
    every record names the preset (id, version, SHA-256 of the file and of its base, the flags it set, what it left
    out, the decision overrides it did not apply) and says the served file is not the bound one.

    Why: the preset is only a way of writing flags down; if its requests differed from the flags' in any byte
    (0 sent as 0.0 included), preset runs and flag runs could not be paired. The hashes let doc 55's tuning protocol
    prove which exact file shaped each call; the binding check keeps a preset tried on another file from passing as
    a run on its own file (doc 55 section 3.5: never applied silently).
    """
    items = "HW01,HT03"
    reset_mock()
    p = run_py(lc_args("preset.jsonl", "--preset", QWEN, items=items))
    check(p.returncode == 0, f"preset run exit {p.returncode}: {p.stderr[-500:]}")
    with_preset = chat_bodies()
    label = MOCK_LABEL + "+qwen3.5-4b-q4_k_m@0.1.0"
    reset_mock()
    flags = ["--temperature", "0.6", "--top-p", "0.95", "--top-k", "20", "--min-p", "0", "--presence-penalty", "0",
             "--repeat-penalty", "1", "--num-predict", "64", "--num-ctx", "8192", "--schema-mode", "strict",
             "--think-mode", "false", "--label", label]
    q = run_py(lc_args("flags.jsonl", *flags, items=items))
    check(q.returncode == 0, f"flag run exit {q.returncode}: {q.stderr[-500:]}")
    check(chat_bodies() == with_preset, "the preset run's bodies differ from its flags' bodies")
    body = json.loads(with_preset)[0]
    check(body["top_k"] == 20 and body["min_p"] == 0.0 and body["chat_template_kwargs"] == {"enable_thinking": False},
          f"body {body}")
    recs = rows(out("preset.jsonl"))
    check(len(recs) == 2 and all(r["model"] == label and r["variant"] == "plain" for r in recs), "labels")
    pr = recs[0]["preset"]
    check(all(r["preset"] == pr for r in recs), "records disagree on the preset")
    check(pr["id"] == "qwen3.5-4b-q4_k_m" and pr["version"] == "0.1.0" and pr["status"] == "draft"
          and pr["sha256"] == sha(QWEN) and pr["file"] == "qwen3.5-4b-q4_k_m.preset.json"
          and pr["bases"] == [{"ref": "default@0.1.0", "file": "default.preset.json", "sha256": sha(DEFAULT)}]
          and pr["step_kind"] == "pick", f"preset record {pr}")
    check(pr["applied"]["top_k"] == 20 and pr["applied"]["num_ctx"] == 8192 and pr["applied"]["scaffold"] is None,
          f"applied {pr['applied']}")
    check("pick.voting.k_max" in {e["knob"] for e in pr["not_applied"]}, "not_applied")
    check(pr["overrides_not_applied"] == ["trigger.end_type", "replay.roll_scope", "module.pick"], "overrides")
    check(pr["binding"]["match"] is False and pr["binding"]["bound"] == "Qwen3.5-4B-Q4_K_M.gguf"
          and pr["binding"]["served"] == "Mock-4B-Q4_K_M.gguf", f"binding {pr['binding']}")
    check("Qwen3.5-4B-Q4_K_M.gguf" in p.stderr and "decision overrides" in p.stderr, f"stderr {p.stderr[-600:]}")
    check("preset" not in rows(out("flags.jsonl"))[0], "a flag-only run recorded a preset")
    return f"2 bodies identical to the flag run's; every record: sha256 {pr['sha256'][:12]}, base, flags, binding"


def p16_template_without_a_thinking_switch_gets_none_on_ollama():
    """The Granite draft (reasoning switch 'not_applicable') on Ollama sends no ``think`` field, and its body equals
    the flag run with ``--think-mode omit``; the binding is recorded as not checked, since Ollama does not report its
    file.

    Why: sending a switch the template does not read is at best noise and at worst a template error; the preset says
    there is none, so none is sent.
    """
    common = ["--backend", "ollama", "--base-url", URL, "--model", "mock", "--suite", "pick", "--items", "PW01",
              "--k", "1"]
    reset_mock()
    p = run_py(common + ["--preset", GRANITE, "--out", out("granite.jsonl")])
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-500:]}")
    with_preset = chat_bodies()
    body = json.loads(with_preset)[0]
    check("think" not in body and body["options"]["top_k"] == 40 and body["options"]["num_predict"] == 64,
          f"body {body}")
    reset_mock()
    q = run_py(common + ["--think-mode", "omit", "--temperature", "0.6", "--top-p", "0.95", "--top-k", "40",
                         "--min-p", "0", "--presence-penalty", "0", "--repeat-penalty", "1", "--num-predict", "64",
                         "--schema-mode", "strict", "--label", "mock+granite-4.1-3b-q4_k_m@0.1.0",
                         "--out", out("granite-flags.jsonl")])
    check(q.returncode == 0 and chat_bodies() == with_preset, f"flag run differs (exit {q.returncode})")
    rec = rows(out("granite.jsonl"))[0]
    check(rec["think_sent"] is False and rec["preset"]["binding"]["match"] is None, f"record {rec['preset']}")
    return "no think field sent; body equals --think-mode omit; binding not checked on Ollama"


def p17_the_why_and_letter_probability_knobs_run_their_arms():
    """A preset with ``answer.why.mode: before`` runs the bounded why arm (variant scaffold-why) with the preset's
    output cap, and one with ``scoring: letter_probs, rotations 2`` runs the logprob mode (variant logprob-perm2);
    both send what ``--scaffold why --num-predict 64`` and ``--pick-mode logprob --permute 2`` send.

    Why: a preset knob must land on the arm run.py already measures, so its records pair with the flag arm's; the
    why arm's cap comes from the preset (64 here), not from the arm's default (200), because the preset owns it.
    """
    why = child("why-first", answer={"form": "letter", "field": "choice", "why": {"mode": "before"},
                                     "transport": "response_format"})
    reset_mock()
    p = run_py(lc_args("why.jsonl", "--preset", why))
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-500:]}")
    with_preset = chat_bodies()
    schema = json.loads(with_preset)[0]["response_format"]["json_schema"]["schema"]
    check(schema["properties"]["why"]["minLength"] == 40 and json.loads(with_preset)[0]["max_tokens"] == 64,
          f"why body {with_preset[:300]}")
    check(rows(out("why.jsonl"))[0]["variant"] == "scaffold-why", "variant")
    reset_mock()
    q = run_py(lc_args("why-flags.jsonl", "--scaffold", "why", "--num-predict", "64", "--temperature", "0.6",
                       "--top-p", "0.95", "--top-k", "40", "--min-p", "0", "--presence-penalty", "0",
                       "--repeat-penalty", "1"))
    check(q.returncode == 0 and chat_bodies() == with_preset, "why: the flag arm sends other bodies")
    lp = child("letter-probs", scoring={"mode": "letter_probs", "rotations": 2})
    reset_mock()
    p = run_py(lc_args("lp.jsonl", "--preset", lp))
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-500:]}")
    sent = json.dumps(posts("/apply-template", "/completion", "/v1/chat/completions"))
    rec = rows(out("lp.jsonl"))[0]
    check(rec["variant"] == "logprob-perm2" and "pick.sampler.temperature" in {
        e["knob"] for e in rec["preset"]["not_applied"]}, f"logprob record {rec.get('variant')}")
    reset_mock()
    q = run_py(lc_args("lp-flags.jsonl", "--pick-mode", "logprob", "--permute", "2"))
    check(q.returncode == 0 and json.dumps(posts("/apply-template", "/completion", "/v1/chat/completions")) == sent,
          "logprob: the flag arm sends other requests")
    return "why arm: scaffold-why at cap 64, bodies = flag arm; letter_probs: logprob-perm2, requests = flag arm"


# ── Error paths: refused before any request ──────────────────────────────────

def p18_conflicts_and_unsupported_presets_are_refused_before_any_request():
    """A flag that contradicts the preset, a preset knob run.py cannot honour, a suite without a step kind, an unknown
    knob, a withdrawn or missing preset file and a card condition the preset turns off each stop the run with exit 2,
    naming what to change, before a single request; a flag that agrees with the preset runs.

    Why: a refused run costs nothing; a run that silently measured another harness under the preset's name would
    cost a tuning round and could not be detected afterwards.
    """
    base = lc_args("refused.jsonl", items="PW01", suite="pick")
    bad = child("typo", sampler={"temperature": 0.6, "top_p": 0.95, "top_k": 40, "min_p": 0, "presence_penalty": 0,
                                 "frequency_penalty": 0, "repeat_penalty": 1, "mirostat": 2})
    gone = child("gone")
    doc = json.loads(support.read_text(gone))
    doc["status"] = "withdrawn"
    support.write_text(gone, json.dumps(doc) + "\n")
    no_cards = child("no-cards", layout={"cards": {"mode": "off"}})
    cases = [
        (["--preset", DEFAULT, "--temperature", "0.3"], ["--temperature 0.3", "pick.sampler.temperature", "Fix:"]),
        (["--preset", DEFAULT, "--variant", "noschema"], ["--variant", "Fix:"]),
        (["--preset", DEFAULT, "--scaffold", "diff"], ["--scaffold diff", "doc 59"]),
        (["--preset", os.path.join(DRAFTS, "gemma-4-e4b-it-qat.preset.json")],
         ["pick.schema_mode", "gbnf_compact", "Fix:"]),
        (["--preset", bad], ["unknown key 'mirostat'", "allowed:"]),
        (["--preset", gone], ["withdrawn"]),
        (["--preset", out("presets/none.preset.json")], ["none.preset.json", "cannot read"]),
        (["--preset", no_cards, "--condition", "cards"], ["--condition cards", "pick.layout.cards.mode"]),
    ]
    for extra, fragments in cases:
        refused(base + extra, *fragments)
    refused(lc_args("refused.jsonl", "--preset", DEFAULT, suite="knowledge", items="K01"), "knowledge", "step kind")
    reset_mock()
    ok = run_py(lc_args("agree.jsonl", "--preset", DEFAULT, "--temperature", "0.6", items="PW01", suite="pick"))
    check(ok.returncode == 0 and rows(out("agree.jsonl"))[0]["preset"]["id"] == "default",
          f"an agreeing flag was refused: {ok.stderr[-400:]}")
    return f"{len(cases) + 1} refusals with exit 2 and no request; an agreeing --temperature runs"


def p19_resume_refuses_records_of_another_preset_hash():
    """``--resume`` into a file whose records were made with another version of the preset file (same id and version,
    other bytes) is refused before any call; with the same bytes it resumes and skips the recorded decisions.

    Why: --resume skips decisions by (model, suite, item, condition, variant, sample); an edited preset keeps all of
    those, so without this check a run would silently mix two harnesses in one file under one label.
    """
    path = child("resumable", sampler={"temperature": 0.3, "top_p": 0.9, "top_k": 20, "min_p": 0,
                                       "presence_penalty": 0, "frequency_penalty": 0, "repeat_penalty": 1})
    args = lc_args("resume.jsonl", "--preset", path, suite="pick", items="PW01,PW02")
    reset_mock()
    check(run_py(args).returncode == 0, "first run failed")
    first = sha(path)
    original = support.read_text(path)
    doc = json.loads(original)
    doc["notes"].append("edited after the first run")
    support.write_text(path, json.dumps(doc, indent=1) + "\n")
    reset_mock()
    p = run_py(args + ["--resume"])
    check(p.returncode == 2 and first[:12] in p.stderr and sha(path)[:12] in p.stderr and "--resume" in p.stderr,
          f"exit {p.returncode}: {p.stderr[-500:]}")
    check(not posts("/v1/chat/completions"), "a call was sent before the refusal")
    support.write_text(path, original)
    reset_mock()
    p = run_py(args + ["--resume"])
    check(p.returncode == 0 and not posts("/v1/chat/completions") and len(rows(out("resume.jsonl"))) == 2,
          f"resume with the same bytes: exit {p.returncode}, {len(posts('/v1/chat/completions'))} calls")
    return f"edited preset refused on --resume (hashes {first[:12]} and the edit's named); unchanged bytes resume"


def p21_resume_without_the_preset_refuses_its_records():
    """``--resume`` without ``--preset`` into a file whose records of the same label (one ``--label`` for both runs)
    were made with a preset is refused before any call, and so is the reverse: a preset run resuming flag-only
    records under one ``--label``.

    Why: p19's hash check used to run only when the resuming run had a preset, so a flag-only ``--resume`` under the
    preset run's ``--label`` skipped the preset's decisions and wrote the rest with the command line's own sampler
    into the same group: two harnesses under one label, which p19 exists to prevent.
    """
    path = child("labelled", sampler={"temperature": 0.3, "top_p": 0.9, "top_k": 20, "min_p": 0,
                                      "presence_penalty": 0, "frequency_penalty": 0, "repeat_penalty": 1})
    args = lc_args("labelled.jsonl", "--label", "same-label", suite="pick", items="PW01,PW02")
    reset_mock()
    first = run_py(args + ["--preset", path, "--limit", "1"])
    check(first.returncode == 0 and len(rows(out("labelled.jsonl"))) == 1, f"preset run: exit {first.returncode}")
    reset_mock()
    p = run_py(args + ["--resume"])
    check(p.returncode == 2 and sha(path)[:12] in p.stderr and "no --preset" in p.stderr,
          f"flag-only resume of preset records: exit {p.returncode}: {p.stderr[-500:]}")
    # The label needs the server probe, so the refusal comes after it (as in p19); no model call may go out.
    check(not posts("/v1/chat/completions") and len(rows(out("labelled.jsonl"))) == 1,
          "a call was sent before the refusal")
    flag_args = lc_args("flag-first.jsonl", "--label", "other-label", suite="pick", items="PW01,PW02")
    reset_mock()
    check(run_py(flag_args + ["--limit", "1"]).returncode == 0, "flag-only first run failed")
    reset_mock()
    q = run_py(flag_args + ["--preset", path, "--resume"])
    check(q.returncode == 2 and "no preset" in q.stderr and not posts("/v1/chat/completions"),
          f"preset resume of flag-only records: exit {q.returncode}: {q.stderr[-500:]}")
    reset_mock()
    r = run_py(lc_args("plain-resume.jsonl", suite="pick", items="PW01") + ["--resume"])
    check(r.returncode == 0, f"a plain --resume without presets was refused: {r.stderr[-300:]}")
    return "flag-only --resume of preset records refused, and the reverse; plain --resume unaffected"


def p20_dry_run_prints_the_preset_request():
    """``--dry-run`` with a preset prints the first request with the preset's values, and the preset's summary (id,
    status, hash, the flags it set) on stderr, without touching the network.

    Why: the dry run is how a user checks a preset before spending a model's time on it; it must show the request the
    preset makes, not the default one.
    """
    reset_mock()
    p = run_py(lc_args("dry.jsonl", "--preset", QWEN, "--dry-run", items="PW01", suite="pick"))
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-400:]}")
    body = json.loads(p.stdout[: p.stdout.index("\n}\n") + 2])
    check(body["top_k"] == 20 and body["temperature"] == 0.6 and not STATE.requests, f"dry body {body}")
    check("qwen3.5-4b-q4_k_m@0.1.0" in p.stderr and "draft" in p.stderr and sha(QWEN)[:12] in p.stderr
          and "--top-k 20" in p.stderr, f"summary: {p.stderr[-500:]}")
    return "dry run shows top_k 20 and temperature 0.6; the summary names the preset, its status, hash and flags"


# ── unittest wiring ──────────────────────────────────────────────────────────

class PresetRunTests(support.CaseTestCase):
    """run.py --preset end to end (see the module docs)."""

    cases = (p15_preset_run_sends_what_its_flags_send_and_records_the_preset,
             p16_template_without_a_thinking_switch_gets_none_on_ollama,
             p17_the_why_and_letter_probability_knobs_run_their_arms,
             p18_conflicts_and_unsupported_presets_are_refused_before_any_request,
             p19_resume_refuses_records_of_another_preset_hash,
             p20_dry_run_prints_the_preset_request,
             p21_resume_without_the_preset_refuses_its_records)

    def setUp(self):
        reset_mock()


if __name__ == "__main__":
    unittest.main()
