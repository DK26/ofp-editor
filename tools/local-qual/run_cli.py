#!/usr/bin/env python3
"""Command line of run.py (tools/local-qual): its flags, and the refusals that need more than argparse.

What it owns
------------
* ``build_parser``: every flag of run.py; the openai backend's flags (and free mode's) come from
  cloud_run.add_cloud_args. ``--preset`` is only declared here: run_preset.py loads the preset and turns it into the
  other flags before the checks below read them. ``--key-status`` is declared here too; key_status.py runs it (and
  nothing else) straight after parsing.
* The checks that run before anything is sent, each refusing an impossible combination with argparse's exit 2:
  ``resolve_variant`` (--condition, --variant, --schema-mode, --why and --repair into one recorded variant),
  ``resolve_scaffold`` (--scaffold and its options), ``load_suite_file`` (a suite kept outside suites/) and
  ``select_split`` (the tune or held-out half of a staged pool).

How it fits
-----------
run.main builds the parser here, parses the command line, and calls the checks before it creates a backend, so a
refused run never touches the network. Split out of run.py to keep each file readable in one pass; run.py re-exports
the check functions. Standard library only.
"""
import argparse
import hashlib
import json
import os

import cloud_run
import logprob_pick
import scaffolds
from prompts import OPEN_VARIANTS, REPAIRABLE, SCHEMA_MODE_VARIANT, SUITE_SHAPE, SUITES, VARIANTS
from run_records import slug


def resolve_variant(ap, args, shape):
    """(condition, base variant, recorded variant) from --condition, --variant, --schema-mode, --why and --repair."""
    condition, base = args.condition, args.variant or "plain"
    if condition == "open":
        if shape != "pick":
            ap.error("--condition open applies to the Pick suites only (pick, pick-hard)")
        if args.variant not in (None, "open"):
            ap.error("--condition open means --variant open; pass one or the other")
        condition, base = "none", "open"
    if args.schema_mode is not None:
        mapped = SCHEMA_MODE_VARIANT[args.schema_mode]
        if args.variant is not None and args.variant != mapped:
            ap.error(f"--schema-mode {args.schema_mode} is variant {mapped}, not {args.variant}")
        if base not in ("plain", mapped):
            ap.error(f"--schema-mode {args.schema_mode} cannot be combined with variant {base}")
        base = mapped
    if args.why:
        if shape != "pick":
            ap.error("--why applies to the Pick suites only (pick, pick-hard)")
        if base != "plain":
            ap.error("--why cannot be combined with another variant")
        base = "why"
    if base not in VARIANTS[shape]:
        ap.error(f"variant {base!r} does not apply to {args.suite} (allowed: {', '.join(VARIANTS[shape])})")
    if base in OPEN_VARIANTS and condition == "cards":
        # The Pick reference cards name most answers' options (43 of the 60 items), so an open arm with its card
        # would be a menu by the back door and its open-versus-menu pairs would understate the menu's uplift.
        ap.error(f"--variant {base} cannot take the reference card (--condition cards): the cards name the options, "
                 f"so the arm would no longer be free of the menu")
    variant = base
    if args.repair:
        if base not in REPAIRABLE.get(shape, ()):
            ap.error(f"--repair applies to pick plain|noschema and fill plain|noschema|schematext, not "
                     f"{args.suite} {base}")
        variant = "repair" if base == "plain" else base + "-repair"
    return condition, base, variant


def resolve_scaffold(ap, args, shape, condition, base_variant):
    """The --scaffold arm to run (None for 'none' or no flag), after refusing every combination it cannot honour.

    A scaffold arm is compared with the plain request of the same (item, sample), so it takes no other harness
    variant; the multi-call arms keep their own cost ledger, so the paid backend (whose budget reserves one call per
    record) is refused; the arms that read letter probabilities or send a raw /completion need llama-server."""
    arm = args.scaffold
    if arm in (None, "none"):
        for flag, value in (("--scaffold-keep", args.scaffold_keep), ("--prefill-channel", args.prefill_channel)):
            if value is not None:
                ap.error(f"{flag} applies to a --scaffold arm only")
        return None
    if arm in scaffolds.PICK_ARMS and shape != "pick":
        ap.error(f"--scaffold {arm} applies to the Pick suites only (pick, pick-hard, or a Pick --suite-file)")
    if arm in scaffolds.FILL_ARMS and shape != "fill":
        ap.error(f"--scaffold {arm} applies to the Fill suites only (fill, or a Fill --suite-file)")
    if base_variant != "plain" or args.why or args.repair:
        ap.error("--scaffold cannot be combined with --variant, --condition open, --schema-mode none|text, --why or "
                 "--repair: each scaffold arm is paired with the plain request (use --scaffold why for a bounded why)")
    if args.pick_mode != "generate":
        ap.error("--scaffold cannot be combined with --pick-mode logprob (eliminate and pairwise read the letter "
                 "probabilities themselves)")
    if args.backend == "openai":
        ap.error("--scaffold is local-only (ollama, llamacpp): the paid backend's budget reserves one call per record, "
                 "and the multi-call arms are not costed under it")
    if arm in scaffolds.LLAMACPP_ONLY and args.backend != "llamacpp":
        ap.error(f"--scaffold {arm} needs --backend llamacpp (it reads letter probabilities or sends a raw /completion)")
    if arm == "rule" and condition != "cards":
        ap.error("--scaffold rule reads the reference card: pass --condition cards (the selected sentence replaces the "
                 "whole card)")
    if args.scaffold_keep is not None and arm not in scaffolds.LOGPROB_ARMS:
        ap.error("--scaffold-keep applies to --scaffold eliminate or pairwise only")
    if args.scaffold_keep is not None and not 2 <= args.scaffold_keep <= 3:
        ap.error("--scaffold-keep must be 2 or 3 (doc 59: re-ask the top two or three; never mask X)")
    if args.prefill_channel is not None and arm != "prefill":
        ap.error("--prefill-channel applies to --scaffold prefill only")
    if arm == "prefill" and args.think_mode != "false":
        ap.error("--scaffold prefill renders the thinking-off template; it cannot run with --think-mode omit")
    return arm


def load_suite_file(ap, args):
    """(suite dict, sha256 prefix) of --suite-file, checked; sets args.suite to the file's own suite name.

    A suite file outside suites/ (the staged pools) must name itself ("suite") and its step shape ("shape"), because
    records and score.py group by that name and pick the scorer by that shape. A copy of a built-in suite may omit the
    shape: its name gives it, as for suites/<name>.json."""
    try:
        with open(args.suite_file, "rb") as f:
            raw = f.read()
        suite = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError) as e:
        ap.error(f"--suite-file {args.suite_file!r} is not readable JSON: {e}")
    if not isinstance(suite, dict) or not isinstance(suite.get("items"), list):
        ap.error("--suite-file must hold a JSON object with an 'items' list")
    name = suite.get("suite")
    if not isinstance(name, str) or not name or slug(name) != name:
        ap.error("--suite-file must name itself with a 'suite' field of letters, digits, '.', '_' or '-'")
    shape = suite.get("shape", SUITE_SHAPE.get(name))
    suite["shape"] = shape
    if shape not in set(SUITE_SHAPE.values()):
        ap.error(f"--suite-file must declare a 'shape' ({', '.join(sorted(set(SUITE_SHAPE.values())))})")
    if args.suite is not None and args.suite != name:
        ap.error(f"--suite {args.suite} does not match the suite file's own name {name!r}; pass one or the other")
    if not all(isinstance(it, dict) and isinstance(it.get("id"), str) for it in suite["items"]):
        ap.error("--suite-file: every item must be an object with a string 'id'")
    args.suite = name
    return suite, hashlib.sha256(raw).hexdigest()[:16]


def select_split(ap, args, items):
    """The items of --split, refusing a mixed-split suite without it and the held-out half without --confirm-heldout.

    The staged pools carry "split": "tune" or "heldout" per item; tuning reads only the tune half, and the held-out
    half runs once, deliberately, for the pre-registered confirmation (doc 55 §4.1)."""
    has_split = any("split" in it for it in items)
    if args.confirm_heldout and args.split != "heldout":
        ap.error("--confirm-heldout goes with --split heldout only")
    if args.split is None:
        if has_split:
            ap.error(f"suite {args.suite} mixes splits; pass --split tune (or --split heldout --confirm-heldout for "
                     f"the pre-registered confirmation run)")
        return items
    if not has_split:
        ap.error("--split applies to suites whose items carry a 'split' field")
    if args.split == "heldout" and not args.confirm_heldout:
        ap.error("--split heldout runs the held-out half; add --confirm-heldout to confirm this is the pre-registered "
                 "confirmation run")
    return [it for it in items if it.get("split") == args.split]


def build_parser():
    """run.py's argument parser (see the module docs); each flag documents itself in its help text."""
    ap = argparse.ArgumentParser(description="Run a local-qual suite against a model (Ollama, llama-server, or an "
                                             "OpenAI-compatible endpoint under a hard budget).")
    ap.add_argument("--backend", default="ollama", choices=("ollama", "llamacpp", "openai"),
                    help="'ollama' (default): native /api/chat; 'llamacpp': llama-server's /v1/chat/completions; "
                         "'openai': any OpenAI-compatible <base-url>/chat/completions (paid endpoints need --max-usd)")
    ap.add_argument("--model", default=None,
                    help="ollama: the model name (required), e.g. qwen3.5:4b-q4_K_M or hf.co/<user>/<repo>:<quant>; "
                         "llamacpp: a label for records and file names (default: the served GGUF's file name "
                         "without .gguf), also sent as the request's model for router mode; openai: the model id "
                         "sent to the endpoint (required), e.g. google/gemma-4-26b-a4b-it")
    ap.add_argument("--label", default=None,
                    help="the model label in records and file names (default: --model; for openai, --model plus "
                         "'@<endpoint tag>' when one endpoint is pinned, so precision rungs score separately)")
    ap.add_argument("--suite", default=None, choices=SUITES,
                    help="the suite under suites/ (required unless --suite-file names one)")
    ap.add_argument("--suite-file", default=None,
                    help="a suite JSON outside suites/ (the staged pools); it must carry 'suite' (its name in records) "
                         "and 'shape'; score it with score.py --suite-file")
    ap.add_argument("--split", default=None, choices=("tune", "heldout"),
                    help="run only the items of this split (required for a suite whose items carry 'split')")
    ap.add_argument("--confirm-heldout", action="store_true",
                    help="with --split heldout: this is the pre-registered confirmation run")
    ap.add_argument("--preset", default=None,
                    help="a harness preset file (D048, doc 55 section 3; drafts in presets/drafts/): its knobs for "
                         "the suite's step kind become the flags that send them (sampler, thinking switch, schema "
                         "mode, card policy, Pick scoring mode, the bounded why, output cap, context); a knob run.py "
                         "cannot honour, or a flag that contradicts one, is refused (run_preset.py). Records carry the "
                         "preset's id, version and SHA-256; the label gains '+<id>@<version>' unless --label is given")
    ap.add_argument("--condition", default="none", choices=("none", "cards", "open"),
                    help="'cards' appends the item's reference card when it has one; 'open' (Pick only) is short "
                         "for --condition none --variant open")
    ap.add_argument("--variant", default=None, choices=sorted({v for vs in VARIANTS.values() for v in vs} - {"why"}),
                    help="harness-uplift rung (default plain): pick open|labels|noschema, fill noschema|schematext, "
                         "text bare")
    ap.add_argument("--schema-mode", default=None, choices=tuple(SCHEMA_MODE_VARIANT),
                    help="Pick and Fill: 'strict' (default, the response schema is enforced), 'none' (no schema: "
                         "variant noschema), 'text' (Fill: schema text in the prompt only: variant schematext)")
    ap.add_argument("--repair", action="store_true",
                    help="pick plain|noschema and fill: one repair call when a code check fails (variant "
                         "'repair' or '<variant>-repair'; the record holds both answers and the summed cost)")
    ap.add_argument("--k", type=int, default=3, help="samples per item (default 3)")
    ap.add_argument("--offset", type=int, default=0,
                    help="skip the first N items (after --items, before --limit); with --limit, runs a chunk")
    ap.add_argument("--limit", type=int, default=None, help="only the first N items (after --items and --offset)")
    ap.add_argument("--items", default=None, help="comma-separated item ids to run")
    # --output is the same option under a second name: `powershell -File` (cloud/run-cloud.ps1) takes "--out" for an
    # abbreviation of its own -OutVariable/-OutBuffer and stops before the launcher starts, while "--output" matches
    # no PowerShell parameter and passes through.
    ap.add_argument("--out", "--output", default=None,
                    help="JSONL output (default results/<label>__<suite>__<condition>[__<variant>].jsonl); --output "
                         "is the same option, for launchers such as cloud/run-cloud.ps1 that cannot pass --out")
    ap.add_argument("--base-url", default=None,
                    help="server URL (default: --host for ollama, http://127.0.0.1:8080 for llamacpp); openai: "
                         "required, the API base such as https://openrouter.ai/api/v1")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
                    help="ollama only, kept for older command lines: the Ollama server (default OLLAMA_HOST)")
    ap.add_argument("--api-key", default=None,
                    help="llamacpp only: bearer key if llama-server runs with --api-key (default LLAMA_API_KEY); "
                         "never accepted for openai, which reads its key from --api-key-env")
    ap.add_argument("--quant", default=None,
                    help="quantisation label for the records when the server cannot report it")
    ap.add_argument("--why", action="store_true", help="pick only: ask for a short 'why' before the choice")
    ap.add_argument("--scaffold", default=None, choices=scaffolds.ARMS,
                    help="reasoning scaffold arm (doc 59; default none = the plain request): pick why|diff|rule "
                         "(one call), eliminate|pairwise|prefill (llamacpp, several calls), subq (one or two calls); "
                         "fill quote-first. Records get variant scaffold-<arm> and a per-call ledger")
    ap.add_argument("--scaffold-keep", type=int, default=None,
                    help="eliminate: options kept after the scoring pass; pairwise: candidates in the round robin "
                         "(2-3, default 3)")
    ap.add_argument("--prefill-channel", default=None, choices=("content", "think"),
                    help="prefill: put the skeleton at the start of the visible answer (content, default) or in the "
                         "empty think block of a Qwen3-style template (think)")
    ap.add_argument("--pick-mode", default="generate", choices=("generate", "logprob"),
                    help="Pick suites: 'generate' (default) samples the reply under the schema; 'logprob' (llamacpp "
                         "only) reads every menu letter's next-token probability from llama-server's /completion "
                         "and records the distribution (variant 'logprob'; see logprob_pick.py)")
    ap.add_argument("--permute", type=int, default=None,
                    help=f"logprob: average over N cyclic rotations of the option order (1-{logprob_pick.MAX_PERMUTE}, "
                         f"default 1; N = the number of options cancels a pure position bias)")
    ap.add_argument("--n-probs", type=int, default=None,
                    help=f"logprob: top tokens requested per position (default {logprob_pick.DEFAULT_N_PROBS}, "
                         f"{logprob_pick.MIN_N_PROBS}-{logprob_pick.MAX_N_PROBS})")
    ap.add_argument("--calibration", default=None,
                    help="logprob: temperature-scaling file from 'cascade.py calibrate' (changes the confidence, "
                         "never the chosen option)")
    ap.add_argument("--temperature", type=float, default=None, help="override the per-suite temperature")
    # Sampler pins. Unset means the server's or the build's default; set them to compare two runtimes
    # or two builds with the same sampler (doc 44 §1.6).
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--top-p", type=float, default=None)
    ap.add_argument("--min-p", type=float, default=None)
    ap.add_argument("--presence-penalty", type=float, default=None)
    ap.add_argument("--repeat-penalty", type=float, default=None)
    ap.add_argument("--num-ctx", type=int, default=8192,
                    help="ollama: context per request; llamacpp: fixed by the server's -c, only checked")
    ap.add_argument("--num-predict", type=int, default=None, help="override the per-suite output token cap")
    ap.add_argument("--keep-alive", default="10m", help="ollama only")
    ap.add_argument("--think-mode", default="false", choices=("false", "omit"),
                    help="'false' (default) switches thinking off (ollama think=false; llamacpp "
                         "chat_template_kwargs.enable_thinking=false); 'omit' leaves the field out")
    ap.add_argument("--timeout", type=float, default=600.0, help="per-request timeout in seconds")
    ap.add_argument("--wait", type=float, default=180.0,
                    help="llamacpp only: seconds to wait for /health while the server loads the model")
    ap.add_argument("--warmup", action="store_true",
                    help="send the first selected call once, unrecorded, before the run (use on the first job "
                         "after a model load, so load and first-use costs stay out of the latency figures); "
                         "not with openai, where every call is paid and recorded")
    ap.add_argument("--resume", action="store_true", help="skip calls already recorded without error in --out")
    ap.add_argument("--dry-run", action="store_true", help="print the first request payload and exit")
    ap.add_argument("--key-status", action="store_true",
                    help="read the key's own record once (GET <base>/key; --base-url defaults to "
                         "https://openrouter.ai/api/v1 for an OpenRouter key) and print its non-secret fields: credit "
                         "limit, usage, free tier, management key, today's free-model requests and their UTC reset, "
                         "the per-key rate limit, and whether --free-only would accept the key; needs --api-key-env; "
                         "sends no model request, uses no quota, writes nothing and skips every other flag "
                         "(key_status.py)")
    cloud_run.add_cloud_args(ap)
    return ap
