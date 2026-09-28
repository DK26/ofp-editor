#!/usr/bin/env python3
"""``run.py --preset FILE``: a data-only harness preset (D048; doc 55 section 3) becomes the flags that send it.

What it owns
------------
* ``apply``: loads and checks the preset through presets/lint.py (schema, bases, loader rules), takes the settings of
  the step kind the suite exercises, turns each knob into the run.py flag that sends it (``plan``), refuses what
  run.py cannot honour and every command-line flag that contradicts the preset (``conflicts``), sets the flags on
  the parsed arguments and prints a summary. Everything here runs before any request.
* ``finish``: after the server probe, records the preset (id, version, status, SHA-256 of the file and its bases,
  the flags it set, what it adapted or left out, the decision overrides it did not apply, and whether the served
  model is the one it is bound to) into ``run_info``, so every record carries it; the label gains
  ``+<id>@<version>`` unless ``--label`` is given, so preset runs never pool or resume with flag-only runs.
* ``check_resume``: every ``--resume``, with or without ``--preset``, refuses an output file whose records of the
  same label were made with other preset bytes, with a preset when the run has none, or without one when it has one
  (an edited preset keeps its id and version, and one ``--label`` can name a preset run and a flag-only run alike;
  --resume would skip decisions made the other way).

Why flags
---------
A preset is only a way of writing flags down: every supported knob maps to a flag run.py already had, converted to
the flag's Python type, so a preset run's requests are byte-identical to the same flags typed out (tests p15-p17),
and the rest of run.py needs no preset-specific branch. Without ``--preset`` nothing here runs.

Knobs fall into four groups (``plan``): *applied* (sampler, output cap, schema mode, thinking switch, card policy,
Pick scoring mode and rotations, the bounded why, bound context), *fixed* (the one value run.py runs, the measured
harness of docs 44 and 46 that the default preset names: any other value is refused), *policies* over several calls
(voting, the repair ceiling, cascade thresholds, calibration: listed as not applied, since score.py, uplift.py,
cascade.py or the product runtime apply them), and anything else, which is refused. Nothing a preset says is
dropped silently (D010). Refusals and conflict messages each name the knob or flag and end with "Fix: ...".
Standard library only.
"""
import argparse
import json
import os
import sys

import cloud_run
import run_cli
import scaffolds
from presets import lint

# run.py's step shapes that a preset has settings for; the knowledge suite has no step kind in the preset format.
STEP_KIND = {"pick": "pick", "fill": "fill", "text": "text", "explain": "explain"}
SAMPLER_FLAGS = ("temperature", "top_p", "top_k", "min_p", "presence_penalty", "repeat_penalty")
# The Python types argparse gives these flags. A preset value is converted the same way, so a preset run sends
# exactly the bytes of its flags (JSON 0 would otherwise go out as 0, the flag's as 0.0).
FLAG_TYPES = {"temperature": float, "top_p": float, "top_k": int, "min_p": float, "presence_penalty": float,
              "repeat_penalty": float, "num_predict": int, "num_ctx": int, "permute": int}
LOCAL_BACKENDS = ("ollama", "llamacpp")
# Refusals and findings shown in one error message at most; the rest are counted.
MAX_SHOWN = 20
# Knobs whose only runnable value is what run.py already does: (value, or {step kind: value}; what run.py does).
# These are the measured harness of docs 44 and 46, which the default preset names with the ids below.
RUNNER_VALUES = {
    "layout.id": ("static_first.v1", "the one capsule layout run.py renders: system prompt, then the request, the "
                                     "menu or record, the card and the reply line"),
    "layout.instruction_variant": ({"pick": "pick.plain.v1", "fill": "fill.plain.v1", "text": "text.slot.v1",
                                    "explain": "explain.card.v1"}, "run.py's own prompts, which the default preset "
                                                                   "names with these ids"),
    "layout.system_message": ("pack", "the system prompt goes in the template's system role"),
    "layout.cards.format": ("prose", "cards are sent as the suite's prose"),
    "layout.option_rendering": ("letter_label_desc", "menus are rendered 'A) label: description'"),
    "layout.exemplars.count": (0, "run.py sends no exemplars"),
    "answer.form": ("letter", "the answer is a menu letter"),
    "answer.field": ("choice", "the reply field is \"choice\""),
    "answer.transport": ("response_format", "the answer is constrained by a response schema"),
    "decomposition.mode": ({"pick": "direct", "explain": "explanation_and_fix"},
                           "one direct call per decision; the explanation and the fix come from the model"),
    "decomposition.record": ("whole_record_prefill", "Fill asks for the whole record in one call"),
    "decomposition.spans": ("free_quote_checked", "spans are free text that code checks against the request"),
    "decomposition.judgement_fields": ("in_record_bands", "judgement fields stay in the record, described by "
                                                          "code-written bands (what docs 44 and 46 measured)"),
    "envelope": ("json_object", "the line comes inside a one-field JSON object"),
}
# Knobs that shape no single request: policies over several calls, applied by the product runtime or replayed
# offline. (path prefix, why run.py leaves it out); listed in each record under preset.not_applied.
POLICIES = (
    ("voting.", "run.py sends --k independent samples; voting and its stop rule are computed offline (score.py, "
                "uplift.py)"),
    ("repair.", "the repair ceiling is a product runtime policy; run.py sends at most one repair call, and only with "
                "--repair"),
    ("cascade.", "cascade thresholds and routes are replayed offline (cascade.py)"),
    ("scoring.calibration.", "calibration changes the confidence, never the chosen option; cascade.py fits and "
                             "applies it offline"),
    ("on_budget", "Compose only; run.py has no Compose suite"),
    ("decomposition.facet_cap", "used only by the facets decomposition, which run.py does not run"),
    ("checker", "an advisory checker is a second model pass after the answer; run.py measures the answer only"),
)


# ── The knob plan (pure) ─────────────────────────────────────────────────────

def _flatten(node, prefix=""):
    """(dotted path, value) for every leaf of a settings object; lists and scalars are leaves."""
    for key, value in node.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            yield from _flatten(value, path + ".")
        else:
            yield path, value


def plan(settings, kind, backend, context_tokens=None):
    """How run.py runs one step kind's merged `settings` on `backend` ("ollama", "llamacpp" or "openai").

    Returns {"flags": {argparse dest: value}, "source": {dest: (knob path, knob value)}, "adapted": [{knob, value,
    why}] (sent in run.py's own form), "not_applied": [{knob, value, why}], "refusals": [str]}; a plan with refusals
    must not run. Pure: no I/O, the same inputs always give the same plan."""
    leaves = dict(_flatten(settings))
    out = {"flags": {}, "source": {}, "adapted": [], "not_applied": [], "refusals": []}
    done = set()

    def get(path):
        return leaves.get(path)

    def mark(*paths):
        done.update(p for p in paths if p in leaves)

    def flag(dest, value, path, consume=True):
        out["flags"][dest] = FLAG_TYPES[dest](value) if dest in FLAG_TYPES and value is not None else value
        out["source"][dest] = (f"{kind}.{path}", leaves.get(path))
        if consume:
            mark(path)

    def refuse(path, text):
        out["refusals"].append(f"{kind}.{path} = {json.dumps(leaves.get(path))}: {text}")
        mark(path)

    def note(group, path, why, value=None):
        out[group].append({"knob": f"{kind}.{path}", "value": leaves.get(path, value), "why": why})
        mark(path)

    # ── Pick scoring decides whether a sampler and an output cap apply at all ──
    logprob = False
    if kind == "pick" and "scoring.mode" in leaves:
        mode = get("scoring.mode")
        if mode == "generate_vote":
            flag("pick_mode", "generate", "scoring.mode")
        elif mode == "letter_probs" and backend != "llamacpp":
            refuse("scoring.mode", "letter-probability scoring reads token probabilities from llama-server's "
                                   "/completion (run.py --pick-mode logprob). Fix: run with --backend llamacpp, or "
                                   "use a copy with scoring.mode 'generate_vote'")
        elif mode == "letter_probs":
            flag("pick_mode", "logprob", "scoring.mode")
            logprob = True
        elif mode == "letter_probs_calibrated":
            refuse("scoring.mode", "run.py reads uncalibrated letter probabilities; calibration changes the "
                                   "confidence, never the chosen option. Fix: use 'letter_probs' and fit the "
                                   "temperature offline (cascade.py calibrate)")
        else:
            refuse("scoring.mode", "run.py has no option-text scoring. Fix: use 'generate_vote' or 'letter_probs'")
    if "scoring.rotations" in leaves:
        if logprob:
            flag("permute", get("scoring.rotations"), "scoring.rotations")
            note("adapted", "scoring.rotations", "sent as --permute: every rotation is read on every decision; "
                                                 "stopping at the first confident pass ('at most') is replayed "
                                                 "offline by cascade.py")
        else:
            note("not_applied", "scoring.rotations", "rotations apply to letter-probability scoring only")
    if get("scoring.permutation") == "cyclic_reask" and not logprob:
        refuse("scoring.permutation", "cyclic re-asks rotate the menu for letter-probability scoring; with "
                                      "generate_vote every sample already gets its own seeded order (per_sample). "
                                      "Fix: set it to 'per_sample', or scoring.mode to 'letter_probs'")
    mark("scoring.permutation")

    # ── The bounded why (Pick) and the scaffold arm, which the preset owns ──
    schema_mode = get("schema_mode")
    if kind == "pick":
        why_paths = [p for p in leaves if p.startswith("answer.why.")]
        if get("answer.why.mode") == "before":
            max_chars = get("answer.why.max_chars")
            if max_chars is not None and max_chars != scaffolds.WHY_MAX:
                refuse("answer.why.max_chars", f"run.py's bounded why arm (doc 59 S3) takes {scaffolds.WHY_MIN}-"
                                               f"{scaffolds.WHY_MAX} characters, both ends in the schema. Fix: set "
                                               f"max_chars to {scaffolds.WHY_MAX} or leave it out")
            elif backend not in LOCAL_BACKENDS:
                refuse("answer.why.mode", "the bounded why runs as run.py's --scaffold why, which is local-only "
                                          "(ollama, llamacpp). Fix: run on a local backend, or use a copy with "
                                          "answer.why.mode 'off'")
            elif logprob:
                refuse("answer.why.mode", "a leading why cannot come before a letter read from one forward pass "
                                          "(scoring.mode letter_probs). Fix: set answer.why.mode 'off', or "
                                          "scoring.mode 'generate_vote'")
            elif schema_mode not in (None, "json_schema_strict"):
                refuse("answer.why.mode", "the why's bounds live in the response schema. Fix: use schema_mode "
                                          "json_schema_strict")
            else:
                flag("scaffold", "why", "answer.why.mode")
        else:
            flag("scaffold", None, "answer.why.mode")
            if "answer.why.max_chars" in leaves:
                note("not_applied", "answer.why.max_chars", "used only when answer.why.mode is 'before'")
        mark(*why_paths)
    elif kind == "fill":
        # The doc 59 Fill arm (quote-first) has no field in the draft-2 format; the preset's spans knob describes the
        # plain request, so it owns --scaffold (the knob itself is checked with the fixed values below).
        flag("scaffold", None, "decomposition.spans", consume=False)

    # ── Schema mode ──
    if "schema_mode" in leaves:
        if logprob and schema_mode != "json_schema_strict":
            refuse("schema_mode", "letter-probability scoring reads the plain lettered request. Fix: use "
                                  "json_schema_strict")
        elif schema_mode == "json_schema_strict":
            flag("schema_mode", "strict", "schema_mode")
        elif schema_mode == "none_validate" and kind in ("pick", "fill"):
            flag("schema_mode", "none", "schema_mode")
        elif schema_mode == "none_validate":
            refuse("schema_mode", f"run.py's {kind} requests always carry the response schema; the arm without one "
                                  f"exists for Pick and Fill only. Fix: use json_schema_strict")
        elif schema_mode == "json_mode_validate":
            refuse("schema_mode", "run.py has no JSON-mode (json_object) arm. Fix: use json_schema_strict, or "
                                  "none_validate for an arm without a schema")
        else:
            refuse("schema_mode", "run.py cannot build the sidecar's compact GBNF grammar (doc 55 section 4.3 lists "
                                  "it as tooling still to build). Fix: run a copy with json_schema_strict, which "
                                  "llama-server compiles to a grammar itself")

    # ── Thinking ──
    reasoning_paths = [p for p in leaves if p.startswith("reasoning.")]
    if reasoning_paths:
        _reasoning(get, flag, refuse, note, backend)
        mark(*reasoning_paths)

    # ── Sampler and output cap ──
    for path in [p for p in leaves if p.startswith("sampler.")]:
        key = path.split(".", 1)[1]
        if logprob and key in SAMPLER_FLAGS + ("frequency_penalty",):
            note("not_applied", path, "letter-probability scoring reads the distribution before any sampler; one "
                                      "token is generated at temperature 0")
        elif key in SAMPLER_FLAGS:
            flag(key, get(path), path)
        elif key == "frequency_penalty" and get(path) == 0:
            note("adapted", path, "not sent: run.py sends no frequency_penalty, and 0 (off) is the default of every "
                                  "runtime it talks to")
        elif key == "frequency_penalty":
            refuse(path, "run.py cannot send a frequency penalty. Fix: set it to 0")
    if "output_cap_tokens" in leaves:
        if logprob:
            note("not_applied", "output_cap_tokens", "letter-probability scoring generates exactly one token")
        else:
            flag("num_predict", get("output_cap_tokens"), "output_cap_tokens")

    # ── Card policy: 'declared' leaves --condition to the run (both card conditions are runs of the preset) ──
    cards = get("layout.cards.mode")
    if cards == "off":
        flag("condition", "none", "layout.cards.mode")
    elif cards == "documents_channel":
        refuse("layout.cards.mode", "run.py sends cards in the user turn only; a template's documents channel "
                                    "(Granite 4.x) is not implemented. Fix: use 'declared' (cards under --condition "
                                    "cards) or 'off'")
    mark("layout.cards.mode")
    if context_tokens is not None:
        out["flags"]["num_ctx"] = int(context_tokens)
        out["source"]["num_ctx"] = ("binds_to.context_tokens", context_tokens)

    # ── Fixed knobs: run.py's own value, or a refusal ──
    for path, (want, what) in RUNNER_VALUES.items():
        want = want.get(kind) if isinstance(want, dict) else want
        if path not in leaves or path in done or want is None:
            continue
        if leaves[path] == want and not isinstance(leaves[path], bool):
            mark(path)
        else:
            refuse(path, f"run.py runs only {json.dumps(want)} here ({what}). Fix: run a copy of the preset with "
                         f"{kind}.{path} = {json.dumps(want)} and a new version, so its records group apart")
    # Exemplar details mean nothing without exemplars (the count is checked above).
    mark(*[p for p in leaves if p.startswith("layout.exemplars.")])
    if get("checker") == "none":
        mark("checker")

    # ── Policies over several calls: listed, not applied ──
    for path in [p for p in leaves if p not in done]:
        why = next((w for prefix, w in POLICIES if path == prefix or path.startswith(prefix)), None)
        if why is not None:
            note("not_applied", path, why)
    # ── Anything left is a knob run.py does not know ──
    for path in sorted(p for p in leaves if p not in done):
        refuse(path, "run.py does not know this knob. Fix: remove it, or check its spelling against "
                     "presets/schema/harness-preset.schema.json")
    return out


def _reasoning(get, flag, refuse, note, backend):
    """The thinking knob: an off switch locally (run.py cannot switch thinking on or cap it there), --reasoning on
    the paid backend."""
    mode, switch, value, budget = (get("reasoning.mode"), get("reasoning.switch"), get("reasoning.value"),
                                   get("reasoning.budget_tokens"))
    if backend in LOCAL_BACKENDS:
        if mode != "off":
            refuse("reasoning.mode", "run.py switches thinking off, or leaves the template's default "
                                     "(--think-mode omit); it cannot switch thinking on or cap it on a local "
                                     "runtime. Fix: set reasoning.mode 'off'")
        elif switch == "not_applicable":
            flag("think_mode", "omit", "reasoning.switch")
        elif switch not in (None, "chat_template_kwargs.enable_thinking", "from_profile"):
            refuse("reasoning.switch", f"run.py's off switch is enable_thinking false (llama-server) or think false "
                                       f"(Ollama); it cannot send {switch!r}. Fix: use "
                                       f"chat_template_kwargs.enable_thinking, or not_applicable for a template "
                                       f"without a switch")
        elif value not in (None, False):
            refuse("reasoning.value", "with mode 'off' the switch value must be false (or null). Fix: set it to "
                                      "false")
        else:
            flag("think_mode", "false", "reasoning.switch" if switch else "reasoning.mode")
            if switch == "from_profile":
                note("adapted", "reasoning.switch", "run.py has no model profiles; it sends its own off switch "
                                                    "(Ollama think false, llama-server enable_thinking false), and "
                                                    "each record's thinking_chars shows whether thinking stayed off")
        if mode == "off" and budget is not None:
            note("not_applied", "reasoning.budget_tokens", "applies to reasoning.mode 'budget' only")
        return
    if mode == "off":
        flag("reasoning", "omit" if switch == "not_applicable" else "none", "reasoning.mode")
    elif mode == "budget" and isinstance(budget, int):
        flag("reasoning", json.dumps({"max_tokens": budget}), "reasoning.budget_tokens")
    elif mode == "budget":
        refuse("reasoning.mode", "mode 'budget' needs reasoning.budget_tokens. Fix: add budget_tokens (16-2048)")
    elif value in cloud_run.REASONING_EFFORTS and value != "none":
        flag("reasoning", value, "reasoning.value")
    else:
        refuse("reasoning.value", f"with mode 'on' run.py sends an effort word as --reasoning "
                                  f"({', '.join(e for e in cloud_run.REASONING_EFFORTS if e != 'none')}). Fix: set "
                                  f"reasoning.value to one of them")


def overrides_for(merged, kind):
    """The DecisionKinds whose overrides target `kind`. run.py's items carry no DecisionKind (the registry is doc 38's
    open question), so these are recorded as not applied: those menus run the step's own setting."""
    return [ov.get("decision_kind") for ov in merged.get("decision_overrides") or []
            if isinstance(ov, dict) and ov.get("step_kind") == kind]


# ── Flags on the command line ────────────────────────────────────────────────

def explicit_flags(argv):
    """{argparse dest: value} of the flags actually given in `argv` (not their defaults).

    How: every dest starts as a private marker object in the namespace, so argparse neither fills in a default nor
    converts one; whatever is not the marker afterwards was on the command line."""
    ap = run_cli.build_parser()
    marker = object()
    ns = argparse.Namespace(**{dest: marker for dest in vars(ap.parse_args([]))})
    ap.parse_args(list(argv), namespace=ns)
    return {k: v for k, v in vars(ns).items() if v is not marker}


def _flag(dest):
    return "--" + dest.replace("_", "-")


def _show(value):
    return "none" if value is None else str(value)


def _same(dest, given, value):
    """Does a flag's command-line value say what the preset's does?"""
    if dest == "scaffold":
        return (None if given in (None, "none") else given) == value
    if dest == "reasoning":
        try:
            return cloud_run.parse_reasoning(given) == cloud_run.parse_reasoning(value)
        except ValueError:
            return False
    return given == value


def conflicts(p, explicit, settings, kind, backend):
    """Messages for the command-line flags (`explicit`, from ``explicit_flags``) that contradict plan `p`; [] if none.

    A flag that sets a knob the preset sets is refused when the values differ; the flags a preset expresses in
    another form (--variant, --why, --calibration, --condition open) whenever given; --repair when the preset allows
    no repair call; --drop-params when it would drop a sampler value the preset sets."""
    msgs = []
    for dest, value in p["flags"].items():
        if dest not in explicit or _same(dest, explicit[dest], value):
            continue
        knob, knob_value = p["source"][dest]
        given = explicit[dest]
        if dest == "scaffold":
            msgs.append(f"--scaffold {given} conflicts with --preset: {knob} is {json.dumps(knob_value)}, so the "
                        f"preset runs {'the bounded why arm' if value == 'why' else 'no scaffold arm'}, and the "
                        f"draft-2 preset format has no field for the other doc 59 arms (doc 59 section 4.4 proposes "
                        f"them). Fix: drop --scaffold, or run the arm without --preset")
        else:
            msgs.append(f"{_flag(dest)} {_show(given)} conflicts with --preset: {knob} is {json.dumps(knob_value)}, "
                        f"which run.py sends as {_flag(dest)} {_show(value)}. Fix: drop {_flag(dest)}, or change "
                        f"{knob} in a copy of the preset (with a new version, so its records group apart)")
    if "variant" in explicit:
        msgs.append(f"--variant {explicit['variant']} cannot be combined with --preset: the uplift rungs remove "
                    f"harness parts the preset describes (its schema_mode sets --schema-mode). Fix: drop --variant, "
                    f"or run the rung without --preset")
    if explicit.get("why"):
        msgs.append("--why cannot be combined with --preset: pick.answer.why.mode says whether a why comes first. "
                    "Fix: drop --why, or set answer.why.mode 'before' in a copy of the preset (run.py then runs the "
                    "bounded why arm, doc 59 S3)")
    if explicit.get("condition") == "open":
        msgs.append("--condition open cannot be combined with --preset: the open arm hides the menu the preset's "
                    "answer form reads. Fix: drop --condition open, or run it without --preset")
    if "calibration" in explicit:
        msgs.append("--calibration cannot be combined with --preset: a draft-2 preset reads uncalibrated letter "
                    "probabilities (scoring.mode letter_probs), and calibration changes the confidence, never the "
                    "choice. Fix: drop --calibration and apply the fit offline with cascade.py")
    r_max = (settings.get("repair") or {}).get("r_max") if isinstance(settings.get("repair"), dict) else None
    if explicit.get("repair") and r_max == 0:
        msgs.append(f"--repair conflicts with --preset: {kind}.repair.r_max is 0 (no repair call). Fix: drop "
                    f"--repair, or raise r_max in a copy of the preset")
    if backend == "openai" and explicit.get("drop_params"):
        for name in sorted({x.strip() for x in str(explicit["drop_params"]).split(",")}):
            if name in p["flags"] and name in SAMPLER_FLAGS:
                msgs.append(f"--drop-params {name} would drop {p['source'][name][0]}, which the preset sets. Fix: "
                            f"run a copy of the preset without that knob's step on this endpoint, or an endpoint "
                            f"that takes {name}")
    return msgs


# ── run.py's hooks ───────────────────────────────────────────────────────────

def _bullets(lines):
    shown = "\n".join("  - " + x for x in lines[:MAX_SHOWN])
    return shown + (f"\n  ... and {len(lines) - MAX_SHOWN} more" if len(lines) > MAX_SHOWN else "")


def apply(ap, args, shape, argv):
    """Load, check and apply ``args.preset`` for a run of step shape `shape`; argparse's exit 2 on any refusal.

    Sets the preset's flags on `args` and returns {"record": the object every record will carry under "preset",
    "binds_to": the merged binding} for ``finish``."""
    try:
        loaded = lint.load(args.preset)
    except lint.PresetError as e:
        ap.error(f"--preset: {e}")
    name, doc, merged = loaded["file"], loaded["doc"], loaded["merged"]
    # Withdrawn first: a withdrawn preset must not be applied at all, so its other findings would only distract.
    if doc.get("status") == "withdrawn":
        ap.error(f"--preset {name} is withdrawn (status 'withdrawn': it must not be applied). Fix: use the preset "
                 f"that replaces it, or the default preset")
    if loaded["errors"]:
        ap.error(f"--preset {name} is not a valid harness preset (presets/schema/harness-preset.schema.json and the "
                 f"loader rules of presets/lint.py):\n{_bullets(loaded['errors'])}\nFix: correct the knobs above; "
                 f"'python tools/local-qual/presets/lint.py {name}' checks the file on its own")
    kind = STEP_KIND.get(shape)
    if kind is None:
        ap.error(f"--preset: suite {args.suite} (shape {shape}) has no step kind in a harness preset (pick, fill, "
                 f"compose, text, explain). Fix: run {args.suite} without --preset")
    settings = (merged.get("step_kinds") or {}).get(kind)
    if not isinstance(settings, dict):
        ap.error(f"--preset {name} has no step_kinds.{kind}. Fix: add it, or extend the default preset, which sets "
                 f"every step kind")
    bind = merged.get("binds_to") or {}
    p = plan(settings, kind, args.backend, bind.get("context_tokens") if bind.get("kind") == "local-gguf" else None)
    if p["refusals"]:
        ap.error(f"--preset {name}: run.py cannot run {len(p['refusals'])} {kind} knob(s) as written (the preset "
                 f"stays valid; these need harness tooling run.py does not have):\n{_bullets(p['refusals'])}")
    msgs = conflicts(p, explicit_flags(argv), settings, kind, args.backend)
    if msgs:
        ap.error(f"--preset {name}:\n{_bullets(msgs)}")
    for dest, value in p["flags"].items():
        setattr(args, dest, value)
    record = {"id": doc["preset_id"], "version": doc["version"], "status": doc["status"], "file": name,
              "sha256": loaded["sha256"], "extends": doc.get("extends"), "bases": loaded["bases"],
              "prompt_pack": merged.get("prompt_pack"), "step_kind": kind, "applied": dict(p["flags"]),
              "adapted": p["adapted"], "not_applied": p["not_applied"],
              "overrides_not_applied": overrides_for(merged, kind)}
    status = doc["status"] + (", an untested hypothesis" if doc["status"] == "draft" else "")
    print(f"preset {record['id']}@{record['version']} ({status}; {name}, sha256 {record['sha256'][:12]}) for "
          f"{kind}: " + " ".join(f"{_flag(d)} {_show(v)}" for d, v in p["flags"].items())
          + (f"; not applied: {', '.join(e['knob'] for e in p['not_applied'])}" if p["not_applied"] else ""),
          file=sys.stderr, flush=True)
    if record["overrides_not_applied"]:
        print(f"note: preset {record['id']}: decision overrides not applied (run.py's items carry no DecisionKind, so "
              f"those menus run the step setting above): {', '.join(record['overrides_not_applied'])}",
              file=sys.stderr, flush=True)
    return {"record": record, "binds_to": bind}


def binding(bind, backend_name, info, model):
    """Is the served model the one the preset is bound to? {"kind", "bound", "served", "match" (True, False, or None
    when the runtime cannot tell), "why"}."""
    kind = bind.get("kind")
    if kind == "any":
        return {"kind": kind, "bound": None, "served": None, "match": True,
                "why": "the default preset binds to any setup"}
    if kind == "local-gguf":
        bound = (bind.get("model") or {}).get("file")
        if backend_name == "llamacpp":
            served = info.get("model_file")
            return {"kind": kind, "bound": bound, "served": served, "match": (served == bound) if served else None,
                    "why": "llama-server's model file" if served else "llama-server did not report its model file"}
        if backend_name == "ollama":
            return {"kind": kind, "bound": bound, "served": model, "match": None,
                    "why": "not checked: Ollama does not report the model file"}
        return {"kind": kind, "bound": bound, "served": model, "match": False,
                "why": "a preset bound to a local file, run on a cloud endpoint"}
    bound = bind.get("model")
    if backend_name == "openai":
        return {"kind": kind, "bound": bound, "served": model, "match": model == bound, "why": "the requested model"}
    return {"kind": kind, "bound": bound, "served": info.get("model_file") or model, "match": False,
            "why": "a preset bound to a cloud endpoint, run on a local runtime"}


def finish(args, preset, label, info, backend_name, model, run_info):
    """After the probe: record the preset (with its binding check) in `run_info`; returns the run's label."""
    record = preset["record"]
    record["binding"] = binding(preset["binds_to"], backend_name, info, model)
    b = record["binding"]
    if b["match"] is False:
        print(f"warning: preset {record['id']}@{record['version']} is bound to {b['bound']}, but this run uses "
              f"{b['served']} ({b['why']}); its records say so (preset.binding.match false)", file=sys.stderr)
    run_info["preset"] = record
    return label if args.label is not None else f"{label}+{record['id']}@{record['version']}"


def check_resume(ap, out, label, sha):
    """--resume: refuse `out` if it holds records of `label` made with other preset bytes than `sha` (the SHA-256 of
    this run's preset file, or None for a run without --preset, whose records must carry no preset either).

    run.py calls it on every --resume, with or without a preset: records are skipped by label, so a flag-only resume
    under a preset run's --label would otherwise finish the preset's decisions with the command line's own knobs."""
    if not os.path.exists(out):
        return
    with open(out, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict) or "item_id" not in r or r.get("model") != label:
                continue
            other = r["preset"].get("sha256") if isinstance(r.get("preset"), dict) else None
            if other != sha:
                made = f"preset sha256 {other[:12]}" if isinstance(other, str) else "no preset"
                this = f"this preset file's sha256 is {sha[:12]}" if isinstance(sha, str) else "this run has no --preset"
                fix = ("restore the preset file those records were made with" if isinstance(sha, str) and
                       isinstance(other, str) else "resume with the same --preset (or none) as those records")
                ap.error(f"--resume: {os.path.basename(out)} already holds records of {label} made with {made}, but "
                         f"{this}; resuming would mix two harnesses under one label. Fix: write to a new --out file, "
                         f"or {fix}")
