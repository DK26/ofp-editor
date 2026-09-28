#!/usr/bin/env python3
"""Tests for the harness-preset checker and loader (presets/lint.py; D048, doc 55 section 3).

p01-p09: the committed draft presets pass the checker and are marked as untested hypotheses; the checker refuses the
negative controls of the staged checker it was ported from (a Pick presence penalty of 1.5, a step granting itself
Compose, a cascade route naming a model) and the loader rules the schema names but cannot express; the subset JSON
Schema validator holds at its boundaries; loading a preset resolves its base, hashes every file it read and refuses
unreadable, oversized, ambiguous or circular files with a message that names the fix.

Everything runs in-process on files the tests write into their own work folder; nothing touches the network.
The run-time side (how run.py applies a preset) is in test_presets_plan.py and test_presets_run.py.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""
import glob
import hashlib
import io
import json
import os
import unittest
from contextlib import redirect_stdout

import support
from support import TOOL, check, load_json

from presets import lint  # noqa: E402 - importable once support put the tool folder on sys.path

DRAFTS = os.path.join(TOOL, "presets", "drafts")
WORK = None


def setUpModule():
    global WORK
    WORK = support.make_work("presets")


def tearDownModule():
    support.remove_work(WORK)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def draft(name):
    """A deep copy of one committed draft preset (drafts/<name>.preset.json)."""
    return load_json(os.path.join(DRAFTS, name + ".preset.json"))


def folder(tag, *docs):
    """A fresh folder in the work area holding the default draft plus `docs` ((file name, dict) pairs); its path.

    Why: a preset's base is looked up next to it, so every loader case writes the base and its children together."""
    path = os.path.join(WORK, tag)
    os.makedirs(path, exist_ok=True)
    for name in os.listdir(path):
        os.remove(os.path.join(path, name))
    write(os.path.join(path, "default.preset.json"), draft("default"))
    for name, doc in docs:
        write(os.path.join(path, name), doc)
    return path


def write(path, doc):
    """Write a preset dict as UTF-8 JSON with LF line ends (the committed files' form)."""
    support.write_text(path, json.dumps(doc, ensure_ascii=False, indent=1) + "\n")


def schema():
    return lint.load_schema()


def errors_of(doc, merged=None):
    """Schema findings for `doc` plus the loader rules for (doc, merged); `merged` defaults to the doc merged onto the
    default draft (or the doc itself for the default)."""
    s = schema()
    if merged is None:
        merged = lint.merge_onto(draft("default"), doc) if "extends" in doc else doc
    return lint.validate(doc, s, s), lint.invariants(doc, merged, s)


# ── Basic functionality ──────────────────────────────────────────────────────

def p01_drafts_pass_the_checker_and_are_marked_untested():
    """Every committed draft preset loads with its base, passes the schema and the loader rules alone and merged, and
    says in its first note that it is an untested hypothesis.

    Why: the drafts are starting points for tuning (doc 55 section 4), not measured settings; a reader or a tool that
    meets one must be told so in the file itself, and a draft that fails the checker would teach the wrong format.
    """
    files = sorted(glob.glob(os.path.join(DRAFTS, "*.preset.json")))
    check(len(files) == 4, f"{len(files)} draft presets, want 4")
    for path in files:
        loaded = lint.load(path)
        check(not loaded["errors"], f"{os.path.basename(path)}: {loaded['errors']}")
        doc = loaded["doc"]
        check(doc["status"] == "draft" and doc["notes"][0].startswith("UNTESTED HYPOTHESIS PRESET"),
              f"{os.path.basename(path)} is not marked as an untested draft")
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = lint.main([])
    check(code == 0 and buf.getvalue().count("OK ") == 4, f"lint exit {code}: {buf.getvalue()}")
    return "4 drafts: schema, merged schema and loader rules clean; each opens with the untested-hypothesis note"


# ── Negative controls ported from the staged checker ─────────────────────────

def p02_pick_presence_penalty_is_refused():
    """A Pick presence penalty of 1.5 (the vendor's recommendation for Qwen3.5) is refused by the schema and by the
    neutral-penalty rule, alone and merged.

    Why: D022 amendment item 5 fixes Pick and Fill penalties at neutral; on llama-server the penalty window covers the
    end of the prompt, and end-of-menu answers fell from 41 of 50 to 34 of 50 under it (doc 46 section 2.2).
    Ported negative control 1 of the staged preset checker.
    """
    bad = draft("qwen3.5-4b-q4_k_m")
    bad["step_kinds"]["pick"]["sampler"]["presence_penalty"] = 1.5
    found, rules = errors_of(bad)
    check(any("step_kinds.pick.sampler.presence_penalty" in e for e in found), f"schema: {found}")
    check(any("penalties must be neutral" in e and "Fix:" in e for e in rules), f"rules: {rules}")
    return f"refused: {len(found)} schema finding(s), {len(rules)} rule finding(s)"


def p03_a_step_granting_itself_compose_is_refused():
    """A preset that adds ``"granted": true`` under Compose is refused as an unknown key.

    Why: shape grants come only from qualification records (doc 21 section 3.3); a preset changes how Wilco asks,
    never what a model setup may do (D048 item 2). Ported negative control 2.
    """
    bad = draft("granite-4.1-3b-q4_k_m")
    bad["step_kinds"]["compose"] = {"granted": True}
    found, _ = errors_of(bad)
    check(any("step_kinds.compose" in e and "unknown key 'granted'" in e for e in found), f"schema: {found}")
    return "compose.granted refused as an unknown key"


def p04_a_cascade_route_naming_a_model_is_refused():
    """A cascade route that names a model instead of a route kind is refused.

    Why: a second stage is a user-made role binding (doc 55 section 7 item 9); a preset that routes to a model by name
    would send a user's decision to a model the user never chose. Ported negative control 3.
    """
    bad = draft("gemma-4-e4b-it-qat")
    bad["step_kinds"]["pick"]["cascade"] = {"route": "some-other-model"}
    found, _ = errors_of(bad)
    check(any("step_kinds.pick.cascade.route" in e and "some-other-model" in e for e in found), f"schema: {found}")
    return "cascade.route 'some-other-model' refused by the route enum"


def p05_loader_rules_the_schema_cannot_express():
    """Each loader rule the schema names but cannot express refuses its violation, which the schema alone accepts,
    and says how to fix it; the unmodified drafts break none of them.

    Why: the schema's own description lists these rules (native tool calls and validator-only schema modes only on
    cloud endpoints, sidecar grammars only locally, no route to an undecided second stage); decision overrides are a
    free-form object in the schema, so only the loader can stop one from smuggling in an unknown knob or an
    unregistered decomposition; and a layout must have an id once merged, or the capsule has no layout to render.

    How: each case mutates a copy of a draft, first asserts that the schema alone accepts it (so the refusal is the
    rule's), then that the rules report a finding naming the knob and carrying "Fix:".
    """
    cloud = {"kind": "cloud-endpoint", "provider": "example", "model": "example/model", "endpoint": "chat",
             "precision": "bf16", "reasoning_setting": "off", "read_on": "2026-09-28"}

    def qwen(mutate):
        d = draft("qwen3.5-4b-q4_k_m")
        mutate(d)
        return d

    def pick_set(d, key, value):
        d["step_kinds"]["pick"][key] = value

    def no_layout_id(d):
        d["step_kinds"]["pick"]["layout"] = {"instruction_variant": "pick.plain.v1"}

    cases = [
        ("bound_second_stage", qwen(lambda d: pick_set(d, "cascade", {"route": "bound_second_stage"})), None,
         "cascade.route"),
        ("native tool call on a local file", qwen(lambda d: pick_set(d, "answer", {
            "form": "letter", "transport": "native_tool_call"})), None, "answer.transport"),
        ("validator-only mode on a local file", qwen(lambda d: pick_set(d, "schema_mode", "none_validate")), None,
         "schema_mode"),
        ("compact grammar on a cloud endpoint", qwen(lambda d: (d.update(binds_to=cloud),
                                                                 pick_set(d, "schema_mode", "gbnf_compact"))), None,
         "schema_mode"),
        ("verbatim spans on a cloud endpoint", qwen(lambda d: d.update(binds_to=cloud)), None, "decomposition.spans"),
        ("override with an unregistered decomposition", qwen(lambda d: d["decision_overrides"][0].update(
            settings={"decomposition": {"mode": "free_text"}})), None, "decision_overrides[0]"),
        ("override smuggling a grant", qwen(lambda d: d["decision_overrides"][0].update(
            settings={"granted": True})), None, "decision_overrides[0]"),
        ("layout without an id after merging", qwen(no_layout_id), "no-id-base", "layout"),
        ("binds to any but is not the default", qwen(lambda d: d.update(binds_to={"kind": "any"})), None,
         "binds_to"),
        ("a non-default preset without extends", qwen(lambda d: d.pop("extends")), "self", "extends"),
        ("no template hash outside a draft", qwen(lambda d: d.update(status="candidate")), None,
         "chat_template_sha256"),
        ("k_max above the Thorough ceiling", qwen(lambda d: pick_set(d, "voting", {"k_max": 6, "stop": "fixed"})),
         None, "voting.k_max"),
    ]
    s = schema()
    base_no_id = draft("default")
    del base_no_id["step_kinds"]["pick"]["layout"]["id"]
    for label, doc, base_kind, knob in cases:
        found = lint.validate(doc, s, s)
        check(not found, f"{label}: the schema alone already refuses it: {found}")
        if base_kind == "self":
            merged = doc
        else:
            merged = lint.merge_onto(base_no_id if base_kind == "no-id-base" else draft("default"), doc)
        rules = lint.invariants(doc, merged, s)
        check(any(knob in e and "Fix:" in e for e in rules), f"{label}: no finding naming {knob!r} with a fix: {rules}")
    for name in ("default", "qwen3.5-4b-q4_k_m", "gemma-4-e4b-it-qat", "granite-4.1-3b-q4_k_m"):
        d = draft(name)
        merged = lint.merge_onto(draft("default"), d) if "extends" in d else d
        check(not lint.invariants(d, merged, s), f"{name}: {lint.invariants(d, merged, s)}")
    return f"{len(cases)} rule violations refused with a fix (schema-clean each); the 4 drafts break none"


# ── Boundary tests of the validator ──────────────────────────────────────────

def p06_validator_boundaries_and_types():
    """The subset validator accepts values exactly at each range bound and refuses one step past it, never counts a
    boolean as an integer, requires exactly one oneOf branch, and lists the allowed keys when it meets an unknown one.

    Why: every knob's legal range is the schema's promise to the runtime (a temperature of 1.6 or a top_k of 101 is
    not a setting anyone tuned); JSON's true is a number in Python, so without the bool check ``"top_k": true`` would
    pass as 1; and an unknown-key message that names the allowed keys lets a person or a model fix a typo at once.
    """
    s = schema()

    def pick_sampler(**changes):
        d = draft("default")
        d["step_kinds"]["pick"]["sampler"].update(changes)
        return lint.validate(d, s, s)

    check(not pick_sampler(temperature=1.5) and pick_sampler(temperature=1.5000001), "temperature bound 1.5")
    check(not pick_sampler(temperature=0) and pick_sampler(temperature=-0.0000001), "temperature bound 0")
    check(not pick_sampler(top_k=100) and pick_sampler(top_k=101), "top_k bound 100")
    check(not pick_sampler(min_p=0.2) and pick_sampler(min_p=0.2000001), "min_p bound 0.2")
    check(pick_sampler(top_k=True) and pick_sampler(top_k=40.0), "a bool or a float passed as an integer")
    d = draft("default")
    d["step_kinds"]["pick"]["voting"]["k_max"] = 8
    ok8 = lint.validate(d, s, s)
    d["step_kinds"]["pick"]["voting"]["k_max"] = 9
    check(not ok8 and lint.validate(d, s, s), "k_max schema bound 8")
    both = draft("default")
    both["binds_to"] = {"kind": "any", "provider": "x"}
    check(any("oneOf" in e for e in lint.validate(both, s, s)), "binds_to matching no branch accepted")
    typo = draft("default")
    typo["step_kinds"]["pick"]["sampler"]["temprature"] = 0.6
    found = lint.validate(typo, s, s)
    check(any("unknown key 'temprature'" in e and "temperature" in e.split("allowed:", 1)[-1] for e in found),
          f"unknown-key message without the allowed keys: {found}")
    check(lint.validate(draft("default"), s, s) == lint.validate(draft("default"), s, s) == [], "not deterministic")
    return "range bounds exact at 0, 1.5, 100, 0.2 and 8; bool and float refused as integers; oneOf; allowed keys named"


# ── Loading: bases, hashes and refusals ──────────────────────────────────────

def p07_load_resolves_the_base_and_hashes_every_file():
    """Loading a preset merges it onto its base found next to it, and reports the SHA-256 of the preset file and of
    every base it read; two loads give the same result.

    Why: a record must name the exact bytes that shaped its request (doc 55 section 3.6: id, version and hash with
    every call); a diff preset means nothing without the base it was merged onto, so the base's hash is part of that.
    """
    path = os.path.join(DRAFTS, "qwen3.5-4b-q4_k_m.preset.json")
    a, b = lint.load(path), lint.load(path)
    check(a == b, "two loads differ")
    with open(path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    with open(os.path.join(DRAFTS, "default.preset.json"), "rb") as f:
        base_sha = hashlib.sha256(f.read()).hexdigest()
    check(a["sha256"] == sha and a["file"] == "qwen3.5-4b-q4_k_m.preset.json", f"hash {a['sha256']}")
    check(a["bases"] == [{"ref": "default@0.1.0", "file": "default.preset.json", "sha256": base_sha}],
          f"bases {a['bases']}")
    pick = a["merged"]["step_kinds"]["pick"]
    check(pick["sampler"]["top_k"] == 20 and pick["answer"]["field"] == "choice" and pick["voting"]["k_max"] == 3,
          f"merge: {pick}")
    check(a["merged"]["binds_to"]["kind"] == "local-gguf" and a["merged"]["preset_id"] == "qwen3.5-4b-q4_k_m",
          "identity fields came from the base")
    check("knob_ledger" not in a["merged"], "a ledger survived the merge")
    return f"qwen draft merged onto default@0.1.0; sha256 {sha[:12]} and base {base_sha[:12]} recorded; deterministic"


def p08_load_refuses_bad_files_with_a_fix():
    """Unreadable, non-JSON, non-object, duplicate-key, non-finite and oversized files, a missing, ambiguous or
    circular base and a chain deeper than the cap are refused, each with a message that says what to do.

    Why: a preset shapes every request of a run; a file read wrongly (a duplicate key silently taking the last value,
    NaN slipping past every range check because NaN compares false) would change requests without anyone seeing it.
    The size and depth caps bound the work a hostile or broken file can cause.

    How: the size cap is checked on both sides with a small cap passed in: a file of exactly the cap loads, one byte
    more is refused.
    """
    d = folder("bad")
    seen = []

    def refused(path, *fragments, **kw):
        try:
            lint.load(path, **kw)
        except lint.PresetError as e:
            msg = str(e)
            check(all(f in msg for f in fragments), f"{os.path.basename(path)}: {msg!r} lacks {fragments}")
            seen.append(msg)
            return msg
        raise AssertionError(f"{os.path.basename(path)} was accepted")

    def raw(name, text):
        p = os.path.join(d, name)
        support.write_text(p, text)
        return p

    refused(os.path.join(d, "missing.json"), "missing.json", "cannot read")
    refused(raw("notjson.json", "{ not json"), "not valid UTF-8 JSON")
    refused(raw("array.json", "[1, 2]"), "a JSON array", "one JSON object")
    refused(raw("dup.json", '{"format": "a", "format": "b"}'), "duplicate key 'format'")
    refused(raw("nan.json", '{"x": NaN}'), "NaN")
    refused(raw("inf.json", '{"x": -Infinity}'), "-Infinity")
    small = raw("small.json", '{"a": 1}')  # 8 bytes
    check(lint.read_preset(small, max_bytes=8)[0] == {"a": 1}, "a file of exactly the cap was refused")
    refused(small, "8 bytes", "7-byte cap", max_bytes=7)
    orphan = draft("qwen3.5-4b-q4_k_m")
    orphan["extends"] = "default@9.9.9"
    refused(raw("orphan.json", json.dumps(orphan)), "default@9.9.9", "copy the base")
    twin = draft("default")
    twin["notes"] = ["a second file with the same id and version"]
    write(os.path.join(d, "default-copy.json"), twin)
    refused(raw("child.json", json.dumps(draft("qwen3.5-4b-q4_k_m"))), "default@0.1.0", "keep one")
    os.remove(os.path.join(d, "default-copy.json"))
    a, b = draft("qwen3.5-4b-q4_k_m"), draft("gemma-4-e4b-it-qat")
    a["extends"], b["extends"] = f"{b['preset_id']}@{b['version']}", f"{a['preset_id']}@{a['version']}"
    write(os.path.join(d, "a.json"), a)
    write(os.path.join(d, "b.json"), b)
    refused(os.path.join(d, "a.json"), "circular")
    chain = []
    for i in range(lint.MAX_CHAIN + 2):
        c = draft("qwen3.5-4b-q4_k_m")
        c["preset_id"] = f"chain-{i:02d}"
        c["extends"] = "default@0.1.0" if i == 0 else f"chain-{i - 1:02d}@0.1.0"
        chain.append(os.path.join(d, f"chain-{i:02d}.json"))
        write(chain[-1], c)
    check(not lint.load(chain[lint.MAX_CHAIN - 1])["errors"], "a chain at the depth cap was refused")
    refused(chain[lint.MAX_CHAIN], f"more than {lint.MAX_CHAIN}")
    return f"{len(seen)} refusals, each naming its fix; the size and depth caps hold on both sides"


def p09_lint_command_reports_each_finding():
    """``presets/lint.py FILE`` prints OK or FAIL per file with every finding and exits 1 when any file fails, 0 when
    all pass.

    Why: the checker is how a person or a model editing a preset learns what is wrong before a run is refused; a
    failing file that exited 0 would be read as clean by any script that chains it.
    """
    bad = draft("qwen3.5-4b-q4_k_m")
    bad["step_kinds"]["pick"]["sampler"]["mirostat"] = 2
    d = folder("cli", ("bad.json", bad), ("good.json", draft("granite-4.1-3b-q4_k_m")))
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = lint.main([os.path.join(d, "bad.json"), os.path.join(d, "good.json")])
    text = buf.getvalue()
    check(code == 1 and "FAIL bad.json" in text and "OK   good.json" in text and "unknown key 'mirostat'" in text,
          f"exit {code}: {text}")
    return "exit 1 with the failing file's finding printed; the clean file reported OK"


# ── unittest wiring ──────────────────────────────────────────────────────────

class PresetCheckerTests(support.CaseTestCase):
    """The harness-preset checker and loader (see the module docs)."""

    cases = (p01_drafts_pass_the_checker_and_are_marked_untested,
             p02_pick_presence_penalty_is_refused,
             p03_a_step_granting_itself_compose_is_refused,
             p04_a_cascade_route_naming_a_model_is_refused,
             p05_loader_rules_the_schema_cannot_express,
             p06_validator_boundaries_and_types,
             p07_load_resolves_the_base_and_hashes_every_file,
             p08_load_refuses_bad_files_with_a_fix,
             p09_lint_command_reports_each_finding)


if __name__ == "__main__":
    unittest.main()
