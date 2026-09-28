#!/usr/bin/env python3
"""Multi-call scaffold arms for the local-qual runner: eliminate, pairwise, subq and prefill (``run.py --scaffold``).

What it owns
------------
``ScaffoldRunner.decide`` runs one Pick decision of a procedure arm: several requests to the server, aggregated by code
into one chosen option key. The texts, schemas and decision rules come from scaffolds.py; this module sends the
requests, keeps a per-call ledger (phase, endpoint, prompt and output tokens, latency, server timings) and turns the
decision into a run.py record (``interpret``). The arms (doc 59 ids):

* **eliminate (S5):** one letter-probability read of the plain menu (the logprob mode's /apply-template + /completion,
  logprob_pick.py), keep the top k real options plus X (X is never masked), then one ordinary sampled Pick over the kept
  options in a fresh seeded order. 1 scoring pass + 1 chat call.
* **pairwise (S6):** the same scoring pass picks the top m options; every pair of them is asked as a two-option menu
  plus X, in both orders; code counts wins (scaffolds.aggregate_pairwise). 1 scoring pass + m(m-1) chat calls (6 at m=3).
* **subq (S7-like):** one call answers yes / no / unclear for every option clause (the menu is not shown); code applies
  the rule table (scaffolds.aggregate_subq) and asks one final Pick over the tied options only when the table cannot
  decide. 1-2 chat calls.
* **prefill (S4):** the plain chat prompt rendered by /apply-template, the code-built skeleton (the diff lines) placed
  at the start of the assistant turn (visible answer, or the empty think block of a Qwen3-style template), and one raw
  POST /completion that continues it under a grammar of the menu letters. 1 render + 1 completion.

Why a raw /completion for prefill
---------------------------------
llama-server can continue an assistant message on /v1/chat/completions too (``--prefill-assistant``, on by default;
at b11146 a trailing assistant message sets continue_final_message and turns add_generation_prompt off), but the
request's response_format becomes a grammar over the *generated* text, which must then be a whole JSON object: it would
demand a fresh "{" after a prefill that already opened one. /apply-template returns the exact prompt the chat path would
render, "which can then be modified as desired ... before sending to /completion" (llama-server README), so this arm
appends the skeleton to that prompt and supplies its own continuation grammar (scaffolds.continuation_grammar). The
rendering is the logprob mode's (same chat body, same thinking switch, BOS handling as documented in logprob_pick.py).
/completion takes the same sampling fields as the chat path (temperature, seed and the sampler pins), so a prefill
decision samples like the plain arm of the same (item, sample).

Answer-blindness
----------------
Every request is built from ``scaffolds.blind(item)``; the full item is never passed below ``decide``'s first line.
The scoring pass uses ``_BlindScorer``, a LogprobPicker whose prompt builder takes the view. The answer enters only in
run.py, which computes the record's scoring fields (correct key and letter) from the full item after the decision.
"""
import time

import logprob_pick
import scaffolds as sc
from backends import _post_with_retries
from prompts import NUM_PREDICT, extract_json, permute_options, strip_think


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _ns(ms):
    return int(round(ms * 1e6)) if isinstance(ms, (int, float)) and not isinstance(ms, bool) else None


def call_entry(phase, endpoint, res, latency_ms):
    """One per-call ledger entry from a backend.chat result (Ollama or llama-server shape).

    prompt_ms / predicted_ms come from llama-server's timings when present, else from Ollama's nanosecond durations;
    cache_n (prompt tokens served from the prefix cache) exists on llama-server only."""
    extra = res.get("extra") or {}
    timings = extra.get("timings") or {}
    prompt_ms = _num(timings.get("prompt_ms"))
    predicted_ms = _num(timings.get("predicted_ms"))
    if prompt_ms is None and _num(res.get("prompt_eval_duration")) is not None:
        prompt_ms = res["prompt_eval_duration"] / 1e6
    if predicted_ms is None and _num(res.get("eval_duration")) is not None:
        predicted_ms = res["eval_duration"] / 1e6
    return {"phase": phase, "endpoint": endpoint, "latency_ms": latency_ms,
            "prompt_tokens": res.get("prompt_eval_count"), "completion_tokens": res.get("eval_count"),
            "prompt_ms": prompt_ms, "predicted_ms": predicted_ms, "cache_n": timings.get("cache_n"),
            "done_reason": res.get("done_reason"), "thinking_chars": res.get("thinking_chars"),
            "error": res.get("error")}


class _BlindScorer(logprob_pick.LogprobPicker):
    """The logprob mode's one-pass letter read, over the answer-blind view.

    LogprobPicker.messages builds the prompt with prompts.build_pick_order, which also computes the correct letter from
    the item's answer. This subclass builds the identical prompt with scaffolds.pick_user from the view, so the scoring
    pass has no path to the answer; ``orders`` still uses the sample's seeded order (permute_options reads only the id
    and the options)."""

    def messages(self, item, condition, opts):
        user, schema, letter_to_key = sc.pick_user(item, condition, opts)
        return ([{"role": "system", "content": self.system}, {"role": "user", "content": user}], schema,
                {"letter_to_key": letter_to_key, "options_order": [o["key"] for o in opts]})


class ScaffoldRunner:
    """Runs one procedure arm per ``decide`` call; see the module docs for each arm's calls."""

    def __init__(self, backend, system, arm, temperature, num_ctx, sampler, num_predict=None, keep=3,
                 channel="content", n_probs=logprob_pick.DEFAULT_N_PROBS):
        if arm not in sc.PROCEDURE_ARMS:
            raise ValueError(f"{arm!r} is not a procedure arm")
        self.backend = backend
        self.system = system
        self.arm = arm
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.sampler = sampler
        self.num_predict = num_predict  # --num-predict: overrides every generated call's cap when set
        self.keep = keep
        self.channel = channel
        # The scorer is also the prefill arm's renderer (_render sends the same /apply-template body).
        self.scorer = _BlindScorer(backend, system, n_probs=n_probs) if arm in sc.LOGPROB_ARMS + ("prefill",) else None

    @property
    def endpoint(self):
        return "/api/chat" if self.backend.name == "ollama" else "/v1/chat/completions"

    def variant(self):
        """The record variant: scaffold-<arm>, plus a suffix for a non-default knob (so arms never pool)."""
        v = "scaffold-" + self.arm
        if self.arm in sc.LOGPROB_ARMS and self.keep != 3:
            v += f"-k{self.keep}"
        if self.arm == "prefill" and self.channel != "content":
            v += "-" + self.channel
        return v

    # Checks before the run ────────────────────────────────────────────────────

    def preflight(self, item, condition, model):
        """None when the server can run this arm, else a message (run.py stops with exit 3 before any record).

        eliminate / pairwise: the logprob mode's n_probs check. prefill: the first item renders through
        /apply-template, and with the think channel the rendered prompt ends with the empty think block."""
        if self.arm in sc.LOGPROB_ARMS:
            return self.scorer.preflight(model)
        if self.arm == "prefill":
            view = sc.blind(item)
            messages, schema, _ = self.scorer.messages(view, condition, permute_options(view, 0))
            prompt, err, _ = self.scorer._render(messages, schema, model)
            if err:
                return err
            _, why_not = sc.prefill_prompt(prompt, "", self.channel)
            return why_not
        return None

    def boundary_check(self, item, condition, model):
        """The logprob mode's token-boundary check (recorded per run), for the arms that read letter probabilities."""
        if self.arm not in sc.LOGPROB_ARMS:
            return None
        return self.scorer.boundary_check(sc.blind(item), condition, model)

    def dry_run(self, item, condition, sample, seed, model):
        """The first request(s) of one decision, without the network; later phases depend on replies and are named."""
        view = sc.blind(item)
        opts = permute_options(view, sample)
        if self.arm in sc.LOGPROB_ARMS:
            out = self.scorer.dry_run(view, condition, sample, seed, model)
            later = ("then one sampled Pick over the top " + str(self.keep) + " options plus X in a fresh seeded order"
                     if self.arm == "eliminate" else
                     f"then every pair of the top {self.keep} options, both orders, as two-option Picks plus X")
            return out + [(later, {})]
        if self.arm == "subq":
            user, schema, _, _ = sc.subq_user(view, condition, opts)
            return [(f"POST {self.endpoint} (subq)", self._payload(user, schema, seed, model, self._cap("subq", schema),
                                                                   "subq")),
                    ("then, only when the rule table ties, one sampled Pick over the tied options plus X", {})]
        messages, schema, extra = self.scorer.messages(view, condition, opts)
        letters = list(extra["letter_to_key"])
        prompt, _ = sc.prefill_prompt("<prompt rendered by /apply-template>" +
                                      (sc.EMPTY_THINK if self.channel == "think" else ""),
                                      sc.prefill_skeleton(view, opts), self.channel)
        return [("POST /apply-template", self.scorer.template_body(messages, schema, model)),
                ("POST /completion", self._completion_body(prompt, letters, seed, model))]

    # Requests ─────────────────────────────────────────────────────────────────

    def _cap(self, phase, schema=None):
        if self.num_predict is not None:
            return self.num_predict
        if phase == "subq":
            return sc.subq_cap(len(schema["properties"]))
        if phase == "prefill":
            return sc.PREFILL_CAP
        return NUM_PREDICT["pick"]

    def _payload(self, user, schema, seed, model, cap, schema_name="pick"):
        # The subq call answers statements, not a menu, so it has its own system prompt; every Pick call keeps the
        # plain request's.
        system = sc.SUBQ_SYSTEM if schema_name == "subq" else self.system
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        return self.backend.payload(model, messages, schema, self.temperature, seed, cap, self.num_ctx, self.sampler,
                                    schema_name=schema_name)

    def _chat(self, phase, user, schema, seed, model, schema_name="pick"):
        """One chat call; returns (ledger entry, parsed JSON object or None)."""
        cap = self._cap(phase, schema)
        payload = self._payload(user, schema, seed, model, cap, schema_name)
        t0 = time.perf_counter()
        res = self.backend.chat(payload)
        entry = call_entry(phase, self.endpoint, res, round((time.perf_counter() - t0) * 1000.0, 1))
        # The output cap this call ran under: the record's num_predict is the plain Pick cap, while the subq call has
        # its own (scaffolds.subq_cap), so a "length" finish can only be judged against the call's own cap.
        entry["cap"] = cap
        entry["think_sent"] = res.get("think_sent")
        entry["raw"] = res.get("content")
        text, _ = strip_think(res.get("content") or "")
        parsed, mode = extract_json(text) if not res.get("error") else (None, "no_response")
        entry["parse_mode"] = mode
        return entry, parsed

    def _pick(self, phase, view, condition, opts, seed, model):
        """A plain lettered Pick over `opts` plus X; returns (ledger entry, chosen key or None)."""
        user, schema, letter_to_key = sc.pick_user(view, condition, opts)
        entry, parsed = self._chat(phase, user, schema, seed, model)
        choice = parsed.get("choice") if isinstance(parsed, dict) else None
        letter = choice.strip().upper() if isinstance(choice, str) else None
        key = letter_to_key.get(letter) if letter else None
        entry.update(options_order=[o["key"] for o in opts], letter=letter, key=key)
        return entry, key

    def _completion_body(self, prompt, letters, seed, model):
        body = {"prompt": prompt, "n_predict": self._cap("prefill"), "temperature": self.temperature, "seed": seed,
                "grammar": sc.continuation_grammar(letters), "cache_prompt": True}
        body.update({k: v for k, v in (self.sampler or {}).items() if v is not None})
        if model:
            body["model"] = model  # router mode picks the model by name; a single-model server ignores it
        return body

    def _score(self, view, condition, sample, seed, model):
        """The eliminate / pairwise scoring pass: (ledger entry, p_by_key or None, error or None)."""
        res, _ = self.scorer.decide(view, condition, sample, seed, model)
        pick = res.get("pick") or {}
        detail = pick.get("detail") or {}
        entry = {"phase": "score", "endpoint": "/apply-template + /completion", "latency_ms": res["latency_ms"],
                 "prompt_tokens": res["prompt_eval_count"], "completion_tokens": res["eval_count"],
                 "prompt_ms": (res["prompt_eval_duration"] or 0) / 1e6 if res["prompt_eval_duration"] else None,
                 "predicted_ms": (res["eval_duration"] or 0) / 1e6 if res["eval_duration"] else None,
                 "cache_n": (detail.get("orders") or [{}])[0].get("cache_n") if detail.get("orders") else None,
                 "completion_calls": detail.get("completion_calls"), "done_reason": "logprob", "cap": 1,
                 "thinking_chars": 0, "think_sent": res.get("think_sent"), "error": res.get("error"),
                 "p_by_key": pick.get("p_by_key"), "valid_mass": pick.get("valid_mass_min"),
                 "confidence": pick.get("confidence")}
        return entry, pick.get("p_by_key"), res.get("error")

    # One decision ─────────────────────────────────────────────────────────────

    def decide(self, item, condition, sample, seed, model):
        """One decision; returns a backend.chat-shaped result plus latency_ms, chosen_key and scaffold (the ledger)."""
        view = sc.blind(item)  # from here on only the answer-blind view is used
        del item
        t0 = time.perf_counter()
        opts = permute_options(view, sample)  # the plain request's seeded order for this (item, sample)
        order_keys = [o["key"] for o in opts]
        escape = view["escape"]["key"]
        by_key = {o["key"]: o for o in opts}
        calls, info, chosen, error = [], {}, None, None

        def failed(entry):
            return entry.get("error")

        if self.arm in sc.LOGPROB_ARMS:
            entry, p, error = self._score(view, condition, sample, seed, model)
            calls.append(entry)
            if not error:
                if p is None:
                    info["fallback"] = "no_valid_letter"  # no menu letter among the listed tokens: nothing to rank
                    ranked = order_keys[: self.keep]
                else:
                    ranked = sc.keep_top(p, order_keys, self.keep)
                info["kept"] = ranked
                if self.arm == "eliminate":
                    final_opts = sc.seeded_order(view, ranked, "elim", sample)
                    entry, chosen = self._pick("final", view, condition, final_opts, seed, model)
                    calls.append(entry)
                    error = failed(entry)
                    info["decided_by"] = "final_pick"
                else:
                    votes = []
                    for a, b in sc.pair_schedule(ranked):
                        entry, key = self._pick("pair", view, condition, [by_key[a], by_key[b]], seed, model)
                        calls.append(entry)
                        if failed(entry):
                            error = failed(entry)
                            break
                        votes.append(key)
                    if not error:
                        chosen, agg = sc.aggregate_pairwise(ranked, votes, escape, p)
                        info.update(pairwise=agg, decided_by="code:" + agg["rule"])
        elif self.arm == "subq":
            user, schema, statements, owners = sc.subq_user(view, condition, opts)
            entry, parsed = self._chat("subq", user, schema, seed, model, schema_name="subq")
            calls.append(entry)
            error = failed(entry)
            info["statements"] = [{"id": sid, "text": text, "options": owners[sid],
                                   "answer": parsed.get(sid) if isinstance(parsed, dict) else None}
                                  for sid, text in statements]
            if not error:
                (kind, value), agg = sc.aggregate_subq(parsed, statements, owners, order_keys)
                info["subq"] = agg
                if kind == "key":
                    chosen, info["decided_by"] = value, "code:unique_top"
                elif kind == "escape":
                    chosen, info["decided_by"] = escape, "code:no_survivor"
                elif kind == "final":
                    final_opts = sc.seeded_order(view, value, "subq", sample)
                    entry, chosen = self._pick("final", view, condition, final_opts, seed, model)
                    calls.append(entry)
                    error = failed(entry)
                    info["decided_by"] = "final_pick"
                else:
                    info["decided_by"] = "none:" + agg["rule"]
        else:  # prefill
            messages, schema, extra = self.scorer.messages(view, condition, opts)
            letters = list(extra["letter_to_key"])
            t1 = time.perf_counter()
            prompt, err, kwargs_sent = self.scorer._render(messages, schema, model)
            calls.append({"phase": "render", "endpoint": "/apply-template",
                          "latency_ms": round((time.perf_counter() - t1) * 1000.0, 1), "prompt_tokens": None,
                          "completion_tokens": None, "think_sent": kwargs_sent, "error": err})
            skeleton = sc.prefill_skeleton(view, opts)
            info.update(channel=self.channel, skeleton=skeleton, skeleton_sha=sc.text_sha(skeleton))
            error = err
            if not error:
                full, why_not = sc.prefill_prompt(prompt, skeleton, self.channel)
                error = why_not
            if not error:
                body = self._completion_body(full, letters, seed, model)
                t1 = time.perf_counter()
                resp, err, _ = _post_with_retries(self.backend.http, "/completion", body, "", (), lambda: None)
                meta = resp if isinstance(resp, dict) else {}
                timings = meta.get("timings") if isinstance(meta.get("timings"), dict) else {}
                content = meta.get("content") if isinstance(meta.get("content"), str) else ""
                parsed, mode = extract_json(sc.ANSWER_PREFIX + content) if not err else (None, "no_response")
                choice = parsed.get("choice") if isinstance(parsed, dict) else None
                letter = choice.strip().upper() if isinstance(choice, str) else None
                chosen = extra["letter_to_key"].get(letter) if letter else None
                calls.append({"phase": "answer", "endpoint": "/completion",
                              "latency_ms": round((time.perf_counter() - t1) * 1000.0, 1),
                              "prompt_tokens": _num(meta.get("tokens_evaluated")),
                              "completion_tokens": _num(meta.get("tokens_predicted")),
                              "prompt_ms": _num(timings.get("prompt_ms")), "predicted_ms": _num(timings.get("predicted_ms")),
                              "cache_n": timings.get("cache_n"), "done_reason": meta.get("stop_type"),
                              "cap": body["n_predict"],
                              "thinking_chars": 0, "think_sent": kwargs_sent, "error": err, "raw": content,
                              "parse_mode": mode, "letter": letter, "key": chosen,
                              "prompt_tail": full[-160:]})
                error = err
                info["decided_by"] = "model"

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        sums = {f: sum(c.get(f) or 0 for c in calls) for f in ("prompt_tokens", "completion_tokens")}
        prompt_ms = sum(c.get("prompt_ms") or 0 for c in calls)
        predicted_ms = sum(c.get("predicted_ms") or 0 for c in calls)
        last = calls[-1] if calls else {}
        # model_calls counts forward passes: a render (/apply-template) has none, a scoring pass has one per order.
        model_calls = sum(0 if c["phase"] == "render" else (c.get("completion_calls") or 1) for c in calls)
        # Calls that stopped at their output cap ("length" on the chat endpoints, "limit" on /completion). The record's
        # done_reason is only the last call's, so a truncated pair call inside a decision is visible only here (PR1).
        truncated = sum(1 for c in calls if c.get("done_reason") in ("length", "limit"))
        scaffold = {"arm": self.arm, "version": sc.SCAFFOLD_VERSION, "n_calls": len(calls),
                    "model_calls": model_calls, "truncated_calls": truncated, "calls": calls}
        scaffold.update(info)
        if self.arm in sc.LOGPROB_ARMS:
            scaffold["keep"] = self.keep
        return {
            "error": error, "think_sent": all(c.get("think_sent") is not False for c in calls),
            "content": last.get("raw") or "", "thinking_chars": sum(c.get("thinking_chars") or 0 for c in calls),
            "prompt_eval_count": sums["prompt_tokens"], "eval_count": sums["completion_tokens"],
            "eval_duration": _ns(predicted_ms), "prompt_eval_duration": _ns(prompt_ms), "load_duration": None,
            "total_duration": _ns(prompt_ms + predicted_ms), "done_reason": last.get("done_reason"), "extra": {},
            "latency_ms": latency_ms, "chosen_key": chosen if not error else None, "scaffold": scaffold,
        }


def interpret(rec, res, extra):
    """Fill a run.py record from a procedure-arm decision, with the plain arm's Pick fields.

    `extra` is the plain request's scoring fields for this (item, sample) (the full seeded menu, the correct key and
    letter), computed by run.py from the full item. ``chosen_letter`` is the chosen key's letter in *that* menu, so
    position statistics in score.py read the same lettering as the plain arm; the letters of the follow-up menus are in
    the ledger (scaffold.calls)."""
    rec.update(extra)
    key = res.get("chosen_key") if not res.get("error") else None
    letter = next((letter for letter, k in extra["letter_to_key"].items() if k == key), None) if key else None
    rec["parse_ok"] = key is not None
    rec["parse_mode"] = "scaffold" if key else ("no_response" if res.get("error") else "no_decision")
    rec["parsed"] = {"choice": letter} if letter else None
    rec["chosen_letter"] = letter
    rec["chosen_key"] = key
    rec["valid_choice"] = key is not None
    rec["correct"] = key is not None and key == extra.get("correct_key")
    rec["scaffold"] = res.get("scaffold")
    rec["n_calls"] = (res.get("scaffold") or {}).get("model_calls")
