#!/usr/bin/env python3
"""Tests for how run.py turns a harness preset into its own flags (run_preset.py; D048, doc 55 section 3).

p10-p14: the knob plan maps each supported knob of one step kind (sampler, reasoning switch, schema mode, card policy,
scoring mode, the bounded why arm, output cap, context) to the run.py flag that sends it, with known values from the
committed drafts; it records every knob it leaves to offline analysis or the product runtime and why; it refuses
every knob run.py cannot honour, all at once, each refusal naming the knob and the fix; and a command-line flag that
contradicts a knob the preset sets is refused with the flag, the knob and the fix in one line.

Pure functions only: no file is written and nothing touches the network. The end-to-end runs are in
test_presets_run.py; the checker and loader in test_presets.py.
"""
import copy
import os
import unittest

import support
from support import TOOL, check

import run_preset  # noqa: E402 - importable once support put the tool folder on sys.path
from presets import lint  # noqa: E402

DRAFTS = os.path.join(TOOL, "presets", "drafts")


# ── Fixtures ─────────────────────────────────────────────────────────────────

def merged(name):
    """The merged settings of one committed draft (its base applied), as run.py sees them."""
    return lint.load(os.path.join(DRAFTS, name + ".preset.json"))["merged"]


def step(name, kind, **changes):
    """A deep copy of one draft's merged `kind` settings with dotted-path `changes` applied (a value of None removes
    the key), e.g. ``step("default", "pick", **{"scoring.mode": "letter_probs"})``."""
    s = copy.deepcopy(merged(name)["step_kinds"][kind])
    for path, value in changes.items():
        node = s
        parts = path.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        if value is None:
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = value
    return s


def fill_ok(name="default", **changes):
    """Fill settings run.py can run: the draft's, with judgement fields in the record (what docs 44 and 46 measured)
    and spans free-quoted, so a case isolates the one knob it changes."""
    base = {"decomposition.judgement_fields": "in_record_bands", "decomposition.spans": "free_quote_checked",
            "decomposition.record": "whole_record_prefill"}
    base.update(changes)
    return step(name, "fill", **base)


PICK_SAMPLER = {"temperature": 0.6, "top_p": 0.95, "top_k": 40, "min_p": 0, "presence_penalty": 0, "repeat_penalty": 1}


# ── Basic functionality: supported knobs become flags ────────────────────────

def p10_plan_maps_supported_knobs_to_run_flags():
    """Each supported knob becomes the run.py flag that sends it, with the draft's value: the six sampler values, the
    output cap, the schema mode, the thinking switch (off through the template kwarg, or no field for a template
    without one), the scoring mode, the why arm (off), and the bound context size.

    Why: a preset run must send exactly what the preset says, through the same code path as the equivalent flags, so
    its requests can be reproduced by hand and paired with flag-only runs (test_presets_run.py checks the bodies).
    """
    want_pick = dict(PICK_SAMPLER, num_predict=64, schema_mode="strict", think_mode="false", pick_mode="generate",
                     scaffold=None)
    cases = [
        ("default pick, llamacpp", step("default", "pick"), "pick", "llamacpp", None, want_pick),
        ("default pick, ollama", step("default", "pick"), "pick", "ollama", None, want_pick),
        ("qwen pick with its bound context", step("qwen3.5-4b-q4_k_m", "pick"), "pick", "llamacpp", 8192,
         dict(want_pick, top_k=20, num_ctx=8192)),
        ("granite pick: a template without a thinking switch", step("granite-4.1-3b-q4_k_m", "pick"), "pick",
         "llamacpp", None, dict(want_pick, think_mode="omit")),
        ("default pick, openai", step("default", "pick"), "pick", "openai", None,
         {k: v for k, v in dict(want_pick, reasoning="none").items() if k != "think_mode"}),
        ("default fill", fill_ok(), "fill", "llamacpp", None,
         dict(PICK_SAMPLER, num_predict=320, schema_mode="strict", think_mode="false", scaffold=None)),
        ("default text", step("default", "text"), "text", "llamacpp", None,
         dict(PICK_SAMPLER, num_predict=120, schema_mode="strict", think_mode="false")),
        ("default explain", step("default", "explain"), "explain", "llamacpp", None,
         dict(PICK_SAMPLER, temperature=0.2, num_predict=320, schema_mode="strict", think_mode="false")),
        ("cards off", step("default", "pick", **{"layout.cards.mode": "off"}), "pick", "llamacpp", None,
         dict(want_pick, condition="none")),
    ]
    for label, settings, kind, backend, ctx, want in cases:
        p = run_preset.plan(settings, kind, backend, ctx)
        check(not p["refusals"], f"{label}: refused {p['refusals']}")
        check(p["flags"] == want, f"{label}: flags {p['flags']}, want {want}")
        check(set(p["source"]) == set(p["flags"]), f"{label}: a flag without its knob: {p['source']}")
    return f"{len(cases)} step settings mapped to exactly the expected run.py flags"


def p11_plan_records_what_it_leaves_out():
    """Knobs that shape no single request (voting, the repair ceiling, cascade thresholds, the facet cap of an unused
    decomposition) are listed as not applied with the reason; frequency_penalty 0 is listed as not sent; decision
    overrides of the run's step kind are listed by DecisionKind.

    Why: nothing a preset says may vanish silently (D010's glass box, doc 55 section 3.6); a reader of a record must
    see which parts of the preset the run measured and which it left to score.py, uplift.py, cascade.py or the product
    runtime.
    """
    p = run_preset.plan(step("default", "pick"), "pick", "llamacpp")
    got = {e["knob"] for e in p["not_applied"]}
    want = {"pick.voting.k_max", "pick.voting.stop", "pick.repair.r_max", "pick.repair.message", "pick.cascade.route",
            "pick.decomposition.facet_cap"}
    check(got == want, f"not applied {sorted(got)}, want {sorted(want)}")
    check(all(e.get("why") for e in p["not_applied"] + p["adapted"]), "an entry without its reason")
    check([e["knob"] for e in p["adapted"]] == ["pick.sampler.frequency_penalty"], f"adapted {p['adapted']}")
    q = merged("qwen3.5-4b-q4_k_m")
    check(run_preset.overrides_for(q, "pick") == ["trigger.end_type", "replay.roll_scope", "module.pick"]
          and run_preset.overrides_for(q, "fill") == [], "overrides by step kind")
    e = run_preset.plan(step("default", "explain"), "explain", "llamacpp")
    check({x["knob"] for x in e["not_applied"]} == {"explain.repair.r_max", "explain.repair.message"},
          f"explain not applied {e['not_applied']}")
    return f"{len(want)} Pick knobs listed as not applied with reasons; frequency_penalty 0 as not sent; 3 overrides"


# ── Error paths: knobs run.py cannot honour ──────────────────────────────────

def p12_plan_refuses_what_run_py_cannot_honour():
    """Every knob value run.py cannot send is refused, naming the knob and the fix, and all of a preset's refusals are
    reported together.

    Why: running such a preset anyway would measure a different harness under the preset's name, the one mislabelled
    result a tuning protocol cannot detect afterwards. Reporting them all at once saves a person or a model one
    failed start per knob.
    """
    cases = [
        ("compact grammar (gemma)", step("gemma-4-e4b-it-qat", "pick"), "pick", "llamacpp", ["pick.schema_mode"]),
        ("verbatim spans and per-field Picks (qwen fill)", step("qwen3.5-4b-q4_k_m", "fill"), "fill", "llamacpp",
         ["fill.decomposition.spans", "fill.decomposition.judgement_fields"]),
        ("closed fields as Picks (granite fill)", step("granite-4.1-3b-q4_k_m", "fill"), "fill", "llamacpp",
         ["fill.decomposition.record", "fill.decomposition.spans", "fill.decomposition.judgement_fields"]),
        ("why longer than the arm's bound", step("default", "pick", **{"answer.why": {"mode": "before",
                                                                                       "max_chars": 200}}),
         "pick", "llamacpp", ["pick.answer.why.max_chars"]),
        ("a thinking budget locally", step("default", "pick", reasoning={"mode": "budget", "budget_tokens": 64}),
         "pick", "llamacpp", ["pick.reasoning.mode"]),
        ("thinking on locally", step("default", "pick", reasoning={"mode": "on"}), "pick", "ollama",
         ["pick.reasoning.mode"]),
        ("a system think token", step("default", "pick", **{"reasoning.switch": "system_think_token"}), "pick",
         "llamacpp", ["pick.reasoning.switch"]),
        ("letter probabilities on ollama", step("default", "pick", **{"scoring.mode": "letter_probs"}), "pick",
         "ollama", ["pick.scoring.mode"]),
        ("calibrated letter probabilities", step("default", "pick", **{"scoring.mode": "letter_probs_calibrated"}),
         "pick", "llamacpp", ["pick.scoring.mode"]),
        ("option-text scoring", step("default", "pick", **{"scoring.mode": "option_text"}), "pick", "llamacpp",
         ["pick.scoring.mode"]),
        ("cyclic re-asks with sampled votes", step("default", "pick", **{"scoring.permutation": "cyclic_reask"}),
         "pick", "llamacpp", ["pick.scoring.permutation"]),
        ("the documents channel", step("default", "pick", **{"layout.cards.mode": "documents_channel"}), "pick",
         "llamacpp", ["pick.layout.cards.mode"]),
        ("exemplars", step("default", "pick", **{"layout.exemplars.count": 2}), "pick", "llamacpp",
         ["pick.layout.exemplars.count"]),
        ("a JSON-array menu", step("default", "pick", **{"layout.option_rendering": "json_array"}), "pick",
         "llamacpp", ["pick.layout.option_rendering"]),
        ("the system text folded into the user turn", step("default", "pick", **{
            "layout.system_message": "fold_into_first_user"}), "pick", "llamacpp", ["pick.layout.system_message"]),
        ("another instruction variant", step("default", "pick", **{"layout.instruction_variant": "pick.ibm.v1"}),
         "pick", "llamacpp", ["pick.layout.instruction_variant"]),
        ("the answer field 'answer'", step("default", "pick", **{"answer.field": "answer"}), "pick", "llamacpp",
         ["pick.answer.field"]),
        ("extract-then-dispatch for every menu", step("default", "pick", **{"decomposition.mode": "extract_dispatch"}),
         "pick", "llamacpp", ["pick.decomposition.mode"]),
        ("a frequency penalty on text", step("default", "text", **{"sampler.frequency_penalty": 0.5}), "text",
         "llamacpp", ["text.sampler.frequency_penalty"]),
        ("JSON mode on Fill", fill_ok(schema_mode="json_mode_validate"), "fill", "llamacpp", ["fill.schema_mode"]),
        ("no schema on text", step("default", "text", schema_mode="none_validate"), "text", "llamacpp",
         ["text.schema_mode"]),
        ("tagged plain text", step("default", "text", envelope="tagged_plain_text"), "text", "llamacpp",
         ["text.envelope"]),
        ("a code-chosen fix", step("default", "explain", **{"decomposition.mode": "explanation_plus_code_fix"}),
         "explain", "llamacpp", ["explain.decomposition.mode"]),
        ("the bounded why on a paid endpoint", step("default", "pick", **{"answer.why.mode": "before"}), "pick",
         "openai", ["pick.answer.why.mode"]),
        ("a why before a letter read from probabilities", step("default", "pick", **{
            "answer.why.mode": "before", "scoring.mode": "letter_probs"}), "pick", "llamacpp",
         ["pick.answer.why.mode"]),
        ("a knob run.py does not know", step("default", "pick", **{"sampler.mirostat": 2}), "pick", "llamacpp",
         ["pick.sampler.mirostat"]),
    ]
    for label, settings, kind, backend, knobs in cases:
        refusals = run_preset.plan(settings, kind, backend)["refusals"]
        for knob in knobs:
            check(any(r.startswith(knob + " ") and "Fix:" in r for r in refusals),
                  f"{label}: no refusal of {knob} with a fix: {refusals}")
        check(len(refusals) == len(knobs), f"{label}: {len(refusals)} refusals, want {len(knobs)}: {refusals}")
    check(not run_preset.plan(step("default", "pick"), "pick", "llamacpp")["refusals"], "the default Pick refused")
    return f"{len(cases)} unsupported settings refused, {sum(len(c[4]) for c in cases)} knobs named, each with a fix"


def p13_plan_runs_the_why_and_letter_probability_arms():
    """``answer.why.mode: before`` runs run.py's bounded why arm under the preset's own output cap;
    ``scoring.mode: letter_probs`` runs the logprob mode with ``rotations`` as --permute and lists the sampler and the
    output cap as not applied; on the paid backend the reasoning knob becomes --reasoning.

    Why: these are the two harness mechanisms of doc 53 and doc 59 a draft-2 preset can express; each must land on the
    arm run.py already measures, not on a look-alike, and a knob that the arm makes irrelevant must say so.
    """
    w = run_preset.plan(step("default", "pick", **{"answer.why.mode": "before"}), "pick", "llamacpp")
    check(w["flags"]["scaffold"] == "why" and w["flags"]["num_predict"] == 64 and not w["refusals"], f"why {w}")
    lp = run_preset.plan(step("default", "pick", scoring={"mode": "letter_probs", "rotations": 2}), "pick",
                         "llamacpp")
    check(lp["flags"] == {"pick_mode": "logprob", "permute": 2, "schema_mode": "strict", "think_mode": "false",
                          "scaffold": None}, f"letter_probs flags {lp['flags']}")
    skipped = {e["knob"] for e in lp["not_applied"]}
    check({"pick.sampler.temperature", "pick.sampler.top_k", "pick.output_cap_tokens"} <= skipped,
          f"letter_probs not applied {sorted(skipped)}")
    check("pick.scoring.rotations" in {e["knob"] for e in lp["adapted"]}, "rotations not described")
    cloud = [
        ({"mode": "off", "switch": "chat_template_kwargs.enable_thinking", "value": False}, "none"),
        ({"mode": "off", "switch": "not_applicable", "value": None}, "omit"),
        ({"mode": "budget", "budget_tokens": 128}, '{"max_tokens": 128}'),
        ({"mode": "on", "switch": "reasoning_effort", "value": "low"}, "low"),
    ]
    for reasoning, want in cloud:
        got = run_preset.plan(step("default", "pick", reasoning=reasoning), "pick", "openai")
        check(got["flags"].get("reasoning") == want and "think_mode" not in got["flags"],
              f"openai {reasoning}: {got['flags']} {got['refusals']}")
    return "why arm with the preset's cap 64; logprob with --permute 2 and 4 knobs not applied; 4 cloud reasoning maps"


# ── Error paths: flags that contradict the preset ────────────────────────────

def p14_conflicting_flags_name_the_flag_the_knob_and_the_fix():
    """A command-line flag that sets a knob the preset also sets is refused when the values differ (and accepted when
    they agree); the flags a preset expresses differently (--variant, --why, --calibration, --condition open, a
    --scaffold arm without a preset field) are refused whenever given. ``explicit_flags`` finds exactly the flags on
    the command line.

    Why: one run, one source of truth. A record that says "preset X" must not carry a temperature or an arm that
    X does not describe; and a message that names the flag, the knob and the fix is one the user or a model can act
    on without reading the code.
    """
    pick = step("default", "pick")
    p = run_preset.plan(pick, "pick", "llamacpp")

    def refusals(explicit, settings=pick, plan=p, backend="llamacpp"):
        return run_preset.conflicts(plan, explicit, settings, "pick", backend)

    bad = [
        ({"temperature": 0.3}, ["--temperature 0.3", "pick.sampler.temperature", "Fix:"]),
        ({"num_predict": 32}, ["--num-predict 32", "pick.output_cap_tokens"]),
        ({"variant": "noschema"}, ["--variant", "Fix:"]),
        ({"why": True}, ["--why", "answer.why.mode", "Fix:"]),
        ({"scaffold": "diff"}, ["--scaffold diff", "doc 59", "Fix:"]),
        ({"condition": "open"}, ["--condition open", "Fix:"]),
        ({"calibration": "t.json"}, ["--calibration", "Fix:"]),
    ]
    for explicit, fragments in bad:
        msgs = refusals(explicit)
        check(len(msgs) == 1 and all(f in msgs[0] for f in fragments), f"{explicit}: {msgs}")
    for explicit in ({"temperature": 0.6}, {"scaffold": "none"}, {"condition": "cards"}, {"k": 5}, {"repair": True},
                     {"schema_mode": "strict"}, {"suite": "pick", "out": "x.jsonl"}):
        check(not refusals(explicit), f"{explicit} refused: {refusals(explicit)}")
    no_repair = step("default", "pick", repair={"r_max": 0})
    msgs = refusals({"repair": True}, settings=no_repair, plan=run_preset.plan(no_repair, "pick", "llamacpp"))
    check(len(msgs) == 1 and "pick.repair.r_max" in msgs[0], f"--repair with r_max 0: {msgs}")
    q = step("qwen3.5-4b-q4_k_m", "pick")
    msgs = refusals({"think_mode": "omit"}, settings=q, plan=run_preset.plan(q, "pick", "llamacpp"))
    check(len(msgs) == 1 and "--think-mode omit" in msgs[0] and "pick.reasoning" in msgs[0], f"think: {msgs}")
    op = run_preset.plan(pick, "pick", "openai")
    check(not refusals({"reasoning": "none"}, plan=op, backend="openai")
          and not refusals({"reasoning": '{"effort": "none"}'}, plan=op, backend="openai"), "equal reasoning refused")
    check(len(refusals({"reasoning": "low"}, plan=op, backend="openai")) == 1, "--reasoning low accepted")
    msgs = refusals({"drop_params": "seed,temperature"}, plan=op, backend="openai")
    check(len(msgs) == 1 and "temperature" in msgs[0] and "pick.sampler.temperature" in msgs[0], f"drop: {msgs}")
    ex = run_preset.explicit_flags(["--suite", "pick", "--temperature", "0.6", "--output", "x.jsonl", "--why"])
    check(ex == {"suite": "pick", "temperature": 0.6, "out": "x.jsonl", "why": True}, f"explicit {ex}")
    check(run_preset.explicit_flags([]) == {}, "flags found in an empty command line")
    return f"{len(bad) + 4} conflicts refused with flag, knob and fix; 7 agreeing or unrelated flags accepted"


# ── unittest wiring ──────────────────────────────────────────────────────────

class PresetPlanTests(support.CaseTestCase):
    """How a harness preset becomes run.py's flags (see the module docs)."""

    cases = (p10_plan_maps_supported_knobs_to_run_flags,
             p11_plan_records_what_it_leaves_out,
             p12_plan_refuses_what_run_py_cannot_honour,
             p13_plan_runs_the_why_and_letter_probability_arms,
             p14_conflicting_flags_name_the_flag_the_knob_and_the_fix)


if __name__ == "__main__":
    unittest.main()
