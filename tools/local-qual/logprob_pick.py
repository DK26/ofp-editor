#!/usr/bin/env python3
"""Logprob Pick for llama-server (tools/local-qual): read the letter distribution instead of sampling one letter.

What it owns
------------
``run.py --pick-mode logprob`` (Pick suites, ``--backend llamacpp`` only). The generate mode lets the model write
``{"choice": "<letter>"}`` under a grammar and keeps the one letter it sampled. This mode asks llama-server instead
for the probability of every candidate next token at the single position where the letter goes, and turns that into
a probability per menu option:

1. **Render** the chat prompt with the model's own template through ``POST /apply-template``. The body carries the
   generate mode's own ``messages``, ``response_format``, ``chat_template_kwargs: {"enable_thinking": false}`` and
   ``model`` (built by the backend's ``payload``), because llama-server renders /apply-template and
   /v1/chat/completions through the same parser (``oaicompat_chat_params_parse``): a chat handler that reads the
   schema, or router mode choosing the model by name, sees the same request, so the prompt is the one the generate
   mode gets. The template's leading BOS is already removed when the tokenizer adds one (common/chat.cpp strips it,
   "to avoid double BOS"), and /completion adds it back. Then append the answer prefix ``{"choice": "`` so that the
   next token is the letter. llama-server documents this use: the endpoint returns the formatted prompt "which can
   then be modified as desired (for example, to insert 'Sure!' at the beginning of the model's response) before
   sending to /completion".
2. **One forward pass.** ``POST /completion`` with ``n_predict: 1``, ``n_probs: N`` (default 32, at least 20) and
   ``temperature: 0``. For the one generated token the server returns the top N tokens of the next-token
   distribution before any sampler, a softmax over every logit it holds (llama.cpp ``tools/server/server-context.cpp``,
   ``populate_token_probs``, the non-post-sampling branch; ``server-common.cpp``, ``get_token_probabilities``), in
   ``completion_probabilities[0].top_logprobs`` as ``{id, token, bytes, logprob}`` (``top_probs`` with ``prob`` when
   a client asks for ``post_sampling_probs``; ``server-task.cpp``, ``probs_vector_to_json``, which writes a
   probability of 0 as the lowest float, not -inf, and cuts ``token`` at the last whole UTF-8 character while
   ``bytes`` keeps every byte; https://github.com/ggml-org/llama.cpp/tree/master/tools/server, read 2026-09-28).
   It normally holds the whole vocabulary; with backend sampling (``-bs``, experimental, off by default) it holds
   only the sampler's candidates, possibly the one greedy token, and the list comes back shorter than N: the
   preflight and every decision refuse such a list (``listed`` < N), since a single token would read as certainty.
   Older builds (``probs`` with ``tok_str``/``prob``) and the OpenAI-style endpoints (``choices[0].logprobs``) use
   other shapes; ``candidates`` reads all of them.
3. **Map tokens to letters** (``token_letter``). One letter can arrive as several different tokens: "A", " A", 'A"',
   'A"}', a raw SentencePiece "▁A", or the same text under two ids (a piece and a byte-fallback token). Each is a
   separate next-token event that means the same letter, so their probabilities add up. A token that would continue
   into a longer string ("AB", "Al", "A1", or "A" plus the first bytes of a multi-byte character, read from
   ``bytes``) means something else and is ignored, and so is a tab next to the letter (a raw tab makes the JSON
   string invalid, so run.py's parser would reject it). Lower case and spaces count, because run.py's parser strips
   and upper-cases the choice too. The grammar of the generate mode would not allow those two; their mass is
   normally tiny and ``variants`` records it per letter.
4. **Renormalise** over the valid letters of this menu, the escape X included: p(L) = mass(L) / valid mass. A valid
   letter outside the top N gets 0; its true probability is at most the smallest listed one (``floor``), and all the
   missing letters together hold at most ``missing_mass_max`` = min(unlisted mass, missing letters x floor).
   ``valid_mass`` says how much of the model's probability the menu letters held at all (cascade.py can refuse to
   trust a confidence renormalised from a small share, ``--min-valid-mass``).
5. **Permute** (``--permute N``): steps 1-4 run for N cyclic rotations of the sample's option order (the escape stays
   last as X, doc 21 §3.2) and the probabilities are averaged *per option key*. With N equal to the number of real
   options every option visits every position once, which cancels exactly a bias that adds the same probability to
   a letter whatever option sits there, and dampens other position effects. Rotations keep each option's
   neighbours, so a neighbour effect is not cancelled, and the escape's own position is never varied.
6. **Calibrate** (``--calibration FILE``): temperature scaling p_T(k) ∝ p(k)^(1/T) with a T fitted offline by
   ``cascade.py calibrate``. It changes the confidence, never the argmax.
7. **Boundary check** (once per run, ``boundary_check``): the letter is read at the token boundary the prefix ends
   on, which is only the model's own boundary if its tokenizer splits there. ``POST /tokenize`` (no forward pass)
   tokenises the rendered prompt, the prompt plus the prefix, and the prompt plus the prefix plus each letter and
   '"}'; a letter whose tokens do not extend the prefix's tokens (a vocabulary with one token for ' "A') is listed
   under ``noncanonical`` in the records' ``logprob_boundary`` and warned about. Byte-level BPE vocabularies with a
   regex pre-tokenizer (Qwen, Llama 3, GPT-2 style) always split punctuation from letters there; vocabularies that
   merge across it (Gemma 4 pre-tokenizes whole lines) have to be checked per model, which this does.

Why
---
A sampled letter says nothing about how sure the model was. The distribution gives a confidence for the price of one
forward pass and one generated token, which is what a cascade needs to decide whether to accept a small model's
answer or escalate (``cascade.py`` replays that offline), and the argmax removes sampling noise from the decision.

How it fits
-----------
run.py refuses the flags outside their scope (``resolve``), builds one ``LogprobPicker`` per run, calls ``decide``
once per (item, sample) and fills the record with ``interpret``, which sets the same Pick fields as the generate mode
(``chosen_letter``, ``chosen_key``, ``correct`` and the order-0 permutation), so score.py and uplift.py score the
records unchanged. The record's variant is ``logprob`` (``logprob-perm<N>`` with ``--permute N``), so these records
group apart from sampled ones. The response parsing and the distribution maths (the pure functions this module
re-exports) live in logprob_dist.py. Standard library only.
"""
import hashlib
import json
import math
import os
import time

from backends import _post_with_retries
from prompts import ESCAPE_LETTER, PICK_LETTERS, build_pick_order, permute_options
# Response parsing and the distribution maths live in logprob_dist.py; re-exported because cascade.py, scaffold_run.py
# and the tests read them from this module.
from logprob_dist import (LEADING, MASS_TOLERANCE, MAX_TOKEN_BYTES, TRAILING, LogprobError,  # noqa: F401
                          _entry, _number, apply_temperature, argmax_key, average_by_key, candidates, entropy,
                          letter_distribution, listed_count, rotations, token_letter, truncation_error)

# The JSON the Pick reply line asks for, up to and including the quote that opens the letter's string. Ending inside
# the string makes the letter the very next token; a prefix ending before the quote would leave the letter to the
# token after a lone quote, which one forward pass cannot see.
ANSWER_PREFIX = '{"choice": "'
DEFAULT_N_PROBS = 32
# At least 20: a 7-option menu plus X is 8 letters, each of which may arrive as 2-3 token variants, next to a few
# non-letter tokens ("\n", "{"). OpenAI's API caps top_logprobs at 20; llama-server's /completion takes more.
MIN_N_PROBS = 20
# Upper bound: beyond a few hundred the list is noise and the record grows for nothing.
MAX_N_PROBS = 200
# A menu has at most 7 real options (doc 21 §3.2), so at most 7 distinct rotations exist.
MAX_PERMUTE = len(PICK_LETTERS)
# Accepted range of a calibration temperature. Temperatures outside it mean a broken fit (T -> 0 turns every
# distribution into a one-hot, T -> infinity into uniform); cascade.py's fit searches the same range.
T_MIN, T_MAX = 0.05, 20.0
# The letters and the text the boundary check appends to the prefix: every letter a menu can have, then the closing
# quote and brace the reply line asks for.
BOUNDARY_LETTERS = PICK_LETTERS + ESCAPE_LETTER
BOUNDARY_TAIL = '"}'


# ── Flags ────────────────────────────────────────────────────────────────────

def load_calibration(path):
    """Read and check a temperature-scaling file; returns {temperature, model, sha, file} or raises ValueError.

    The file is the JSON ``cascade.py calibrate`` writes: ``{"method": "temperature", "temperature": T, "model": ...}``.
    T must be a real number in [T_MIN, T_MAX]; ``model``, when present, must name the run's model label (checked by
    run.py once the label is known), because a temperature fitted on one model means nothing for another.
    """
    try:
        with open(path, "rb") as f:
            raw = f.read()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"calibration file {path!r} is not readable JSON: {e}") from None
    if not isinstance(data, dict):
        raise ValueError("calibration file must hold a JSON object")
    if data.get("method", "temperature") != "temperature":
        raise ValueError(f"calibration method {data.get('method')!r} is not supported (only 'temperature')")
    t = data.get("temperature")
    if not isinstance(t, (int, float)) or isinstance(t, bool) or not math.isfinite(t) or not T_MIN <= t <= T_MAX:
        raise ValueError(f"calibration temperature must be a number in [{T_MIN}, {T_MAX}], got {t!r}")
    model = data.get("model")
    if model is not None and not isinstance(model, str):
        raise ValueError("calibration 'model' must be a string when present")
    return {"temperature": float(t), "model": model, "sha": hashlib.sha256(raw).hexdigest()[:16],
            "file": os.path.basename(path)}


def resolve(ap, args, shape, variant):
    """Check the logprob flags against the run; returns (record variant, picker settings or None).

    Everything that cannot apply is refused before any request (argparse exit 2): the mode needs llama-server's
    /completion, a lettered Pick menu and no second call, and it sends no sampler, so the sampling flags would be
    silently ignored.
    """
    if args.pick_mode != "logprob":
        for flag, value in (("--permute", args.permute), ("--n-probs", args.n_probs),
                            ("--calibration", args.calibration)):
            if value is not None:
                ap.error(f"{flag} applies to --pick-mode logprob only")
        return variant, None
    if args.backend != "llamacpp":
        ap.error("--pick-mode logprob needs --backend llamacpp (it reads token probabilities from llama-server's "
                 "/completion with n_probs)")
    if shape != "pick":
        ap.error("--pick-mode logprob applies to the Pick suites only (pick, pick-hard)")
    if variant != "plain":
        ap.error(f"--pick-mode logprob reads the plain lettered menu; it cannot be combined with variant {variant!r} "
                 f"(--variant, --why, --repair, --schema-mode none|text)")
    ignored = [flag for flag, value in (("--temperature", args.temperature), ("--num-predict", args.num_predict),
                                        ("--top-k", args.top_k), ("--top-p", args.top_p), ("--min-p", args.min_p),
                                        ("--presence-penalty", args.presence_penalty),
                                        ("--repeat-penalty", args.repeat_penalty)) if value is not None]
    if ignored:
        ap.error(f"{', '.join(ignored)} do(es) not apply to --pick-mode logprob: the distribution is read before any "
                 f"sampler, and exactly one token is generated at temperature 0")
    permute = 1 if args.permute is None else args.permute
    if not 1 <= permute <= MAX_PERMUTE:
        ap.error(f"--permute must be 1-{MAX_PERMUTE} (a menu has at most {MAX_PERMUTE} real options)")
    n_probs = DEFAULT_N_PROBS if args.n_probs is None else args.n_probs
    if not MIN_N_PROBS <= n_probs <= MAX_N_PROBS:
        ap.error(f"--n-probs must be {MIN_N_PROBS}-{MAX_N_PROBS}")
    calibration = None
    if args.calibration is not None:
        try:
            calibration = load_calibration(args.calibration)
        except ValueError as e:
            ap.error(str(e))
    return ("logprob" if permute == 1 else f"logprob-perm{permute}"), {
        "permute": permute, "n_probs": n_probs, "calibration": calibration}


# ── Client ───────────────────────────────────────────────────────────────────

def _ns(ms):
    return int(round(ms * 1e6)) if isinstance(ms, (int, float)) and not isinstance(ms, bool) else None


def _count(v):
    """v as an int when it is a finite JSON number >= 0, else None.

    json.loads accepts NaN and Infinity, int() of either raises, and json.dumps would write NaN into a record that
    strict JSON readers reject, so a server's token count or cache count passes through here.
    """
    n = _number(v)
    return int(n) if n is not None and math.isfinite(n) and n >= 0 else None


class LogprobPicker:
    """One logprob Pick decision per call of ``decide``: render, one /completion per rotation, map, average."""

    def __init__(self, backend, system, n_probs=DEFAULT_N_PROBS, permute=1, calibration=None):
        self.backend = backend  # a backends.LlamaServerBackend: its HTTP client, bearer key and thinking switch
        self.system = system
        self.n_probs = n_probs
        self.permute = permute
        self.calibration = calibration

    # Request bodies ─────────────────────────────────────────────────────────

    # The fields of the generate mode's chat body that reach the template renderer: the messages, the schema (a chat
    # handler may read it), the thinking switch and the model name (router mode picks the model, and so the template,
    # by it). Sampling fields (temperature, seed, max_tokens, sampler pins) do not affect the prompt and are left out.
    TEMPLATE_FIELDS = ("messages", "response_format", "chat_template_kwargs", "model")

    def template_body(self, messages, schema, model):
        """POST /apply-template: the generate mode's own chat body (backend.payload), cut to TEMPLATE_FIELDS.

        Building it with the same function as the chat call keeps the two in step: enable_thinking goes out exactly
        when the chat path sends it (also after a template rejected it), and the schema is wrapped the same way.
        """
        chat = self.backend.payload(model, messages, schema, 0.0, None, 1, None, {}, schema_name="pick")
        return {k: chat[k] for k in self.TEMPLATE_FIELDS if k in chat}

    def completion_body(self, prompt, seed, model):
        """POST /completion: one token at temperature 0, with the top n_probs of the raw distribution."""
        body = {"prompt": prompt + ANSWER_PREFIX, "n_predict": 1, "n_probs": self.n_probs, "temperature": 0.0,
                "seed": seed, "cache_prompt": True}
        if model:
            body["model"] = model  # router mode picks the model by name; a single-model server ignores it
        return body

    def messages(self, item, condition, opts):
        """(chat messages, Pick schema, extra record fields) of one option order, as the generate mode builds them."""
        user, schema, extra = build_pick_order(item, condition, opts)
        return [{"role": "system", "content": self.system}, {"role": "user", "content": user}], schema, extra

    def orders(self, item, sample):
        """The option orders of one decision: the seeded order of (item, sample) first, then its rotations."""
        return rotations(permute_options(item, sample), self.permute)

    def dry_run(self, item, condition, sample, seed, model):
        """The two request bodies of the first order, without the network (the rendered prompt is a placeholder)."""
        messages, schema, _ = self.messages(item, condition, self.orders(item, sample)[0])
        return [("POST /apply-template", self.template_body(messages, schema, model)),
                ("POST /completion", self.completion_body("<prompt rendered by /apply-template>", seed, model))]

    # Calls ──────────────────────────────────────────────────────────────────

    def _post(self, path, body):
        """POST with backends.py's retries on connection errors; no field is ever dropped from a /completion."""
        return _post_with_retries(self.backend.http, path, body, "", (), lambda: None)

    def preflight(self, model):
        """None when the server returns token probabilities for n_probs, else a message (run.py stops, exit 3).

        One tiny completion before the run, so a build that ignores n_probs fails once, not once per item.
        """
        body = {"prompt": "ping", "n_predict": 1, "n_probs": self.n_probs, "temperature": 0.0}
        if model:
            body["model"] = model
        resp, err, _ = self._post("/completion", body)
        if err:
            return f"POST /completion failed: {err}"
        try:
            entries, _, _, bad, beyond = candidates(resp, self.n_probs)
        except LogprobError as e:
            return str(e)
        if not entries:
            return "the server listed no token probabilities for n_probs"
        return truncation_error(listed_count(entries, bad, beyond), self.n_probs)

    def _tokenize(self, text, model):
        """[(id, piece)] of `text` through POST /tokenize, or raises LogprobError.

        add_special false (the BOS does not move the boundary), parse_special true as /completion tokenises the
        prompt, with_pieces for the record. A piece that is not valid UTF-8 comes back as a list of bytes; a build
        that ignores with_pieces returns bare ids, which are enough for the comparison.
        """
        body = {"content": text, "add_special": False, "parse_special": True, "with_pieces": True}
        if model:
            body["model"] = model
        resp, err, _ = self._post("/tokenize", body)
        if err:
            raise LogprobError(f"POST /tokenize: {err}")
        toks = resp.get("tokens") if isinstance(resp, dict) else None
        if not isinstance(toks, list) or not toks:
            raise LogprobError("POST /tokenize returned no tokens")
        out = []
        for t in toks:
            tid, piece = (t.get("id"), t.get("piece")) if isinstance(t, dict) else (t, None)
            if not isinstance(tid, int) or isinstance(tid, bool):
                raise LogprobError("POST /tokenize returned a token without an integer id")
            if isinstance(piece, list):
                piece = bytes(b for b in piece if isinstance(b, int) and 0 <= b <= 255).decode("utf-8", "replace")
            out.append((tid, piece if isinstance(piece, str) else None))
        return out

    def boundary_check(self, item, condition, model):
        """Does the answer prefix end on the model's own token boundary? A dict for the run's records, never raises.

        Renders the first order of `item` like a decision, then tokenises the prompt, the prompt plus the prefix,
        and the prompt plus the prefix plus each letter and '"}'. ``junction_ok``: the prompt's tokens are a prefix
        of the prompt-plus-prefix tokens (the prefix does not merge into the template's last token). A letter is
        ``noncanonical`` when its full tokens do not start with the prompt-plus-prefix tokens: the tokenizer would
        have merged across the end of the prefix (one token for ' "A'), so the model reads 'A' after a split it never
        saw. ``letter_pieces`` is the token that holds each letter. ``checked`` is false, with the reason, when the
        server cannot tokenise (a build without /tokenize): the run goes on and the records say so.
        """
        messages, schema, _ = self.messages(item, condition, self.orders(item, 0)[0])
        prompt, err, _ = self._render(messages, schema, model)
        if err:
            return {"checked": False, "reason": err}
        try:
            head = self._tokenize(prompt, model)
            base = self._tokenize(prompt + ANSWER_PREFIX, model)
            noncanonical, pieces = [], {}
            for letter in BOUNDARY_LETTERS:
                full = self._tokenize(prompt + ANSWER_PREFIX + letter + BOUNDARY_TAIL, model)
                ids, base_ids = [t for t, _ in full], [t for t, _ in base]
                # The first token where the two tokenisations part: the letter's own token when the boundary holds.
                split = next((i for i, (a, b) in enumerate(zip(ids, base_ids)) if a != b), min(len(ids), len(base)))
                if ids[:len(base_ids)] != base_ids:
                    noncanonical.append(letter)
                pieces[letter] = full[split][1] if split < len(full) else None
        except LogprobError as e:
            return {"checked": False, "reason": str(e)}
        return {"checked": True, "junction_ok": [t for t, _ in base[:len(head)]] == [t for t, _ in head],
                "noncanonical": noncanonical, "prefix_tail": [p for _, p in base[-2:]], "letter_pieces": pieces}

    def _render(self, messages, schema, model):
        """(prompt or None, error or None, whether chat_template_kwargs went out)."""

        def stop_kwargs():
            self.backend.send_think = False  # the chat path stops sending it too, as after a rejected chat call

        resp, err, sent = _post_with_retries(self.backend.http, "/apply-template",
                                             self.template_body(messages, schema, model), "chat_template_kwargs",
                                             ("chat_template_kwargs", "enable_thinking"), stop_kwargs)
        kwargs_sent = "chat_template_kwargs" in sent
        if err:
            return None, f"POST /apply-template: {err}", kwargs_sent
        # A reply that is not a JSON object (a list, a string) has no prompt; .get on it would raise.
        prompt = resp.get("prompt") if isinstance(resp, dict) else None
        if not isinstance(prompt, str) or not prompt:
            return None, "POST /apply-template returned no prompt", kwargs_sent
        return prompt, None, kwargs_sent

    def decide(self, item, condition, sample, seed, model):
        """One decision. Returns (result, extra): result has backend.chat's fields plus ``latency_ms`` and ``pick``;
        extra is the order-0 menu (letter_to_key, options_order, correct letter...), as build_pick returns it."""
        t0 = time.perf_counter()
        orders, error, think_sent, extra0 = [], None, True, None
        # completion_calls counts every /completion sent, the one that failed included (cascade.py costs them all).
        sums = {"prompt": 0, "predicted": 0, "prompt_ms": 0.0, "predicted_ms": 0.0}
        calls = 0
        for j, opts in enumerate(self.orders(item, sample)):
            messages, schema, extra = self.messages(item, condition, opts)
            extra0 = extra0 or extra
            prompt, err, kwargs_sent = self._render(messages, schema, model)
            think_sent = think_sent and kwargs_sent
            if err:
                error = f"order {j}: {err}"
                break
            body = self.completion_body(prompt, seed, model)
            calls += 1
            resp, err, _ = self._post("/completion", body)
            if err:
                error = f"order {j}: POST /completion: {err}"
                break
            # The server evaluated the prompt even when its answer turns out unusable below: count its tokens.
            meta = resp if isinstance(resp, dict) else {}
            timings = meta.get("timings") if isinstance(meta.get("timings"), dict) else {}
            for field, key in (("tokens_evaluated", "prompt"), ("tokens_predicted", "predicted")):
                sums[key] += _count(meta.get(field)) or 0
            for field in ("prompt_ms", "predicted_ms"):
                v = _number(timings.get(field))
                sums[field] += v if v is not None and math.isfinite(v) and v >= 0 else 0.0
            letters = list(extra["letter_to_key"])  # the menu's letters, then X
            try:
                entries, shape, sampled, bad, beyond = candidates(resp, self.n_probs)
                listed = listed_count(entries, bad, beyond)
                why = truncation_error(listed, self.n_probs)
                if why:
                    raise LogprobError(why)
                # llama-server records a token's probabilities only once its text is whole UTF-8 (process_token
                # skips add_token while the text ends inside a character), so a first token that stops mid-character
                # can make the server generate a second one and list *that* position. One generated token is the
                # letter position; more means the list may belong to another position.
                n_gen = _count(meta.get("tokens_predicted"))
                if n_gen is not None and n_gen > 1:
                    raise LogprobError(f"the server generated {n_gen} tokens, not 1 (the first ended inside a UTF-8 "
                                       f"character?): the listed probabilities may be another position's")
                dist = letter_distribution(entries, letters)
            except LogprobError as e:
                error = f"order {j}: {e}"
                break
            orders.append({
                "options_order": extra["options_order"], "letter_to_key": extra["letter_to_key"],
                "prompt_sha": hashlib.sha256(body["prompt"].encode("utf-8")).hexdigest()[:16],
                "prompt_tail": body["prompt"][-120:], "shape": shape, "sampled_token": sampled,
                "listed": listed, "n_returned": len(entries), "bad_entries": bad, "extra_entries": beyond,
                "total_mass": dist["total_mass"], "valid_mass": dist["valid_mass"], "floor": dist["floor"],
                "missing": dist["missing"], "missing_mass_max": dist["missing_mass_max"],
                "variants": dist["variants"], "letter_mass": dist["letter_mass"],
                "dist": dist["dist"], "top": [[t, round(p, 8)] for t, p in entries],
                "cache_n": _count(timings.get("cache_n")),
            })
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        pick = {"detail": {"prefix": ANSWER_PREFIX, "n_probs": self.n_probs, "endpoint": "/completion",
                           "permute_requested": self.permute, "orders": orders, "completion_calls": calls,
                           "orders_used": sum(1 for o in orders if o["dist"] is not None)}}
        if error is None:
            self._summarise(pick, orders, extra0)
        result = {
            "error": error, "think_sent": think_sent,
            "content": (orders[0]["sampled_token"] or "") if orders else "", "thinking_chars": 0,
            "prompt_eval_count": sums["prompt"], "eval_count": sums["predicted"],
            "eval_duration": _ns(sums["predicted_ms"]), "prompt_eval_duration": _ns(sums["prompt_ms"]),
            "load_duration": None, "total_duration": _ns(sums["prompt_ms"] + sums["predicted_ms"]),
            "done_reason": "logprob", "extra": {}, "latency_ms": latency_ms, "pick": pick,
        }
        return result, extra0

    def _summarise(self, pick, orders, extra0):
        """Average the orders per key, pick the argmax, and add the confidence fields (calibrated when asked)."""
        p = average_by_key(orders)
        if p is None:
            return  # no order listed any valid letter: no answer (parse_mode no_valid_letter)
        best, tie = argmax_key(p, extra0["letter_to_key"])
        pick["letter"] = next(letter for letter, key in extra0["letter_to_key"].items() if key == best)
        pick["detail"]["tie"] = tie
        ranked = sorted(p.values(), reverse=True)
        pick.update(p_by_key=p, confidence_raw=ranked[0], p_margin=ranked[0] - (ranked[1] if len(ranked) > 1 else 0.0),
                    p_entropy=entropy(p), confidence=ranked[0],
                    valid_mass_min=min(o["valid_mass"] for o in orders if o["dist"] is not None))
        if self.calibration is not None:
            cal = apply_temperature(p, self.calibration["temperature"])
            pick["p_by_key_cal"] = cal
            pick["confidence"] = max(cal.values())
            pick["detail"]["calibration"] = {k: self.calibration[k] for k in ("temperature", "sha", "file", "model")}


def interpret(rec, res, extra):
    """Fill a run.py record from a decision: the generate mode's Pick fields plus the distribution.

    ``raw`` (set by run.py) is the one token the server sampled for order 0; ``parsed`` is the argmax letter as the
    object the generate mode would have parsed, so every reader of Pick records works unchanged.
    """
    pick = res.get("pick") or {}
    rec.update(extra or {})
    rec["pick_mode"] = "logprob"
    rec["logprob"] = pick.get("detail")
    letter = pick.get("letter") if not res.get("error") else None
    rec["parse_ok"] = letter is not None
    rec["parse_mode"] = "logprob" if letter else ("no_response" if res.get("error") else "no_valid_letter")
    rec["parsed"] = {"choice": letter} if letter else None
    rec["chosen_letter"] = letter
    rec["chosen_key"] = (extra or {}).get("letter_to_key", {}).get(letter) if letter else None
    rec["valid_choice"] = rec["chosen_key"] is not None
    rec["correct"] = rec["chosen_key"] is not None and rec["chosen_key"] == (extra or {}).get("correct_key")
    for field in ("p_by_key", "p_by_key_cal", "confidence", "confidence_raw", "p_margin", "p_entropy",
                  "valid_mass_min"):
        if field in pick:
            rec[field] = pick[field]
