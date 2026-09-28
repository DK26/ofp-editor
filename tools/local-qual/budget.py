#!/usr/bin/env python3
"""Hard spending cap for paid endpoints (tools/local-qual).

What it owns
------------
The money side of a cloud run: the worst-case cost of one attempt, the running
total, and the refusal to send an attempt that could push the total past the
cap. run.py creates one ``Budget`` per run of the ``openai`` backend;
``OpenAICompatBackend.chat`` (cloud_backend.py) asks it before every attempt and
reports what each attempt cost afterwards.

How the cap holds
-----------------
* **Reserve before sending.** An attempt's worst case is
  ``(prompt estimate x price_in + output cap x price_out) / 1e6``. The prompt
  estimate is deliberately pessimistic: every UTF-8 byte of every message (and
  of the schema, which a provider may inject into the prompt, and of any body
  field that is not a known routing or sampling parameter, which a provider
  might turn into prompt text) counts as ``tokens_per_byte`` tokens (default
  1.0; a byte-level tokenizer never makes more tokens than bytes), plus a few
  tokens of chat template per message, all times a 1.3 margin. The output cap
  is the request's ``max_tokens`` (plus ``reasoning.max_tokens`` when one is
  sent), which the endpoint enforces. The attempt is sent only when
  ``spent + reservation <= cap``. Prices and the cap must be > 0, except in
  free-only mode (``--free-only``, OpenRouter ``:free`` models), where the cap
  and every price are exactly 0: every reservation is then 0 and any attempt
  that costs anything is over its worst case. Outside free mode a zero price
  would make every worst case 0 and, on an endpoint that reports no cost, let
  spending run unseen.
* **Write ahead.** The reservation is written to the ledger (a JSONL file)
  *before* the request leaves, and the call's record carries the settled cost
  afterwards. A reservation without a settled record (the process died in
  between) keeps counting at its full worst case, so a crash can only
  over-count.
* **Settle after.** An answered attempt costs the higher of what the provider
  reported (``usage.cost``, plus the upstream cost only on a request that ran
  on the user's own provider key: ``usage.is_byok`` true) and what its usage
  costs at the price flags (so a provider reporting 0, or a cost in another
  unit, can never make the ledger under-count), else whichever of the two is
  known, else its whole reservation. Attempts that failed before a model ran (400,
  401, 402, 403, 404, 413, 422, 429) cost nothing; every other failed attempt
  costs its reservation (see cloud_backend.py for the rules and their source).
* **Persist.** The ledger is the run's output JSONL by default, so ``--resume``
  (and any later run that appends to the same file) keeps counting from what
  that file already spent; ``--ledger PATH`` shares one cap across many output
  files (one process at a time).

Ledger rows: ``{"budget_event": "reserve", "call_id", "attempt",
"reserved_usd", "ts"}`` before a send; the call record (or, in a separate
ledger, a ``{"budget_event": "settle", "call_id", "cost_usd", ...}`` row)
after it; ``{"budget_event": "stop", ...}`` when a run stops on the budget.
score.py and run.py's --resume skip ``budget_event`` rows.

Standard library only.
"""
import datetime as _dt
import json
import math
import os

from backends import SAMPLER_KEYS
from cloud_backend import usage_fields

# Pessimism factor on the prompt estimate, as the cloud plan asks (text length x 1.3).
PROMPT_MARGIN = 1.3
# Chat-template tokens charged per message on top of its bytes (role markers, separators).
TOKENS_PER_MESSAGE = 8
# Body fields that are never prompt text (routing, caps, sampling); every other top-level field's bytes count
# toward the prompt estimate, in case the provider injects it (messages and response_format are counted apart).
NON_PROMPT_FIELDS = frozenset(("model", "messages", "response_format", "stream", "max_tokens",
                               "max_completion_tokens", "temperature", "seed", "reasoning", "provider")
                              + SAMPLER_KEYS)
# Floor on --est-tokens-per-byte: real tokenizers make about 0.2-0.3 tokens per byte of English, so a smaller
# figure is a typo that would shrink every reservation below the real prompt.
MIN_TOKENS_PER_BYTE = 0.1


def _now():
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_ledger_rows(path):
    """All JSON objects in a JSONL file (missing file -> []); lines that are not JSON objects are skipped."""
    rows = []
    if not path or not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


class Budget:
    """Running total and cap for one run (see the module docs for the rules)."""

    def __init__(self, cap_usd, price_in, price_out, price_cache_read=None, tokens_per_byte=1.0,
                 extra_prompt_tokens=0, sink=None, rows=(), separate_ledger=False, free_only=False):
        for name, value in (("cap_usd", cap_usd), ("price_in", price_in), ("price_out", price_out),
                            ("tokens_per_byte", tokens_per_byte), ("extra_prompt_tokens", extra_prompt_tokens)):
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite number >= 0, got {value!r}")
        if free_only:
            # Free-only: nothing may be spent, so the cap and every price are exactly 0 (any cost is over the cap).
            if cap_usd != 0 or price_in != 0 or price_out != 0 or price_cache_read not in (None, 0):
                raise ValueError("--free-only spends nothing: the cap and every price must be 0")
        else:
            if cap_usd <= 0:
                raise ValueError("the budget cap must be > 0 USD")
            if price_in == 0 or price_out == 0:
                raise ValueError("a zero price makes every worst case 0; zero prices are accepted only with "
                                 "--free-only (OpenRouter :free models)")
        if tokens_per_byte < MIN_TOKENS_PER_BYTE:
            raise ValueError(f"tokens_per_byte must be >= {MIN_TOKENS_PER_BYTE}, got {tokens_per_byte!r}")
        if price_cache_read is not None and (not math.isfinite(price_cache_read) or price_cache_read < 0):
            raise ValueError("price_cache_read must be a finite number >= 0")
        self.cap_usd = float(cap_usd)
        self.price_in, self.price_out = float(price_in), float(price_out)
        self.price_cache_read = None if price_cache_read is None else float(price_cache_read)
        self.tokens_per_byte = float(tokens_per_byte)
        self.extra_prompt_tokens = float(extra_prompt_tokens)
        self.sink = sink  # callable(row dict) that appends one JSON line and flushes
        self.separate_ledger = separate_ledger
        self.free_only = bool(free_only)
        self.reserved = {}  # (call_id, attempt) -> USD
        self.settled = {}  # call_id -> USD
        for row in rows:
            self._absorb(row)

    def _absorb(self, row):
        """Fold one ledger row into the totals (reserve rows, and anything with call_id + cost_usd).

        A repaired decision's record holds two calls; its ``call_costs`` ({call_id: USD}) settles each one.
        """
        costs = row.get("call_costs")
        if isinstance(costs, dict) and row.get("budget_event") is None:
            for cid, usd in costs.items():
                if isinstance(usd, (int, float)) and math.isfinite(usd):
                    self.settled[cid] = max(0.0, float(usd))
            return
        cid = row.get("call_id")
        if cid is None:
            return
        if row.get("budget_event") == "reserve":
            usd = row.get("reserved_usd")
            if isinstance(usd, (int, float)) and math.isfinite(usd) and usd >= 0:
                self.reserved[(cid, row.get("attempt"))] = float(usd)
        elif isinstance(row.get("cost_usd"), (int, float)) and math.isfinite(row["cost_usd"]):
            # A call settles once, with the total of all its attempts; a record and a settle row for the same
            # call carry the same total, so the last one read simply wins.
            self.settled[cid] = max(0.0, float(row["cost_usd"]))

    def spent(self):
        """Settled costs plus the full reservation of every attempt whose call has not settled."""
        pending = sum(usd for (cid, _), usd in self.reserved.items() if cid not in self.settled)
        return sum(self.settled.values()) + pending

    # ── Estimates ───────────────────────────────────────────────────────────

    def estimate(self, body):
        """Worst case of one attempt of `body`: {prompt_tokens_est, output_cap, usd}.

        Raises ValueError when the body has no output cap, because then no worst case exists.
        """
        msgs = body.get("messages") or []
        nbytes = 0
        for m in msgs:
            content = m.get("content") if isinstance(m, dict) else m
            nbytes += len((content if isinstance(content, str) else json.dumps(content)).encode("utf-8"))
        if body.get("response_format") is not None:
            nbytes += len(json.dumps(body["response_format"], ensure_ascii=False).encode("utf-8"))
        for key, value in body.items():
            if key not in NON_PROMPT_FIELDS:
                nbytes += len(json.dumps({key: value}, ensure_ascii=False).encode("utf-8"))
        prompt_est = math.ceil(PROMPT_MARGIN * (nbytes * self.tokens_per_byte + TOKENS_PER_MESSAGE * len(msgs)
                                                + self.extra_prompt_tokens))
        cap = body.get("max_tokens", body.get("max_completion_tokens"))
        if isinstance(cap, bool) or not isinstance(cap, int) or cap <= 0:
            raise ValueError("the request has no positive max_tokens, so its worst-case cost is unbounded")
        reasoning = body.get("reasoning")
        if isinstance(reasoning, dict) and isinstance(reasoning.get("max_tokens"), int) and reasoning["max_tokens"] > 0:
            cap += reasoning["max_tokens"]  # a separate thinking budget may be billed on top of the text cap
        usd = (prompt_est * self.price_in + cap * self.price_out) / 1e6
        return {"prompt_tokens_est": prompt_est, "output_cap": cap, "usd": usd}

    def reservation_usd(self, body):
        return self.estimate(body)["usd"]

    def cost_from_usage(self, usage):
        """(USD, source) for one answered attempt; (None, None) without usage.

        Source 'provider' (usage.cost, plus the upstream cost on a BYOK request, when that is at least the computed
        figure), 'computed' (tokens x price flags, when the provider reports no cost) or 'computed>provider' (the
        provider reported less than its own token counts cost at the price flags; the higher figure is kept, so the
        ledger never under-counts).

        The upstream cost is added only when ``usage.is_byok`` is true: outside a BYOK request OpenRouter reports the
        same money in ``cost`` and in ``cost_details.upstream_inference_cost``, and adding both booked every call
        twice (doc 54 §4.2: a ledger of 0.327 USD against 0.163 billed, and a false cost-anomaly stop).
        """
        u = usage_fields(usage)
        upstream = (u["upstream_cost"] or 0.0) if u["is_byok"] else 0.0
        provider = None if u["cost"] is None else u["cost"] + upstream
        computed = None
        if u["prompt_tokens"] is not None and u["completion_tokens"] is not None:
            cached = min(u["cached_tokens"] or 0, u["prompt_tokens"])
            cache_price = self.price_in if self.price_cache_read is None else self.price_cache_read
            computed = ((u["prompt_tokens"] - cached) * self.price_in + cached * cache_price
                        + u["completion_tokens"] * self.price_out) / 1e6
        if provider is None:
            return (computed, "computed") if computed is not None else (None, None)
        if computed is None or provider >= computed:
            return provider, "provider"
        return computed, "computed>provider"

    # ── Reserve and settle ───────────────────────────────────────────────────

    def try_reserve(self, call_id, attempt, usd):
        """Reserve `usd` for one attempt if it fits under the cap. Returns (ok, spent before the attempt)."""
        spent = self.spent()
        if spent + usd > self.cap_usd + 1e-12:
            return False, spent
        self.reserved[(call_id, attempt)] = float(usd)
        if self.sink is not None:
            self.sink({"budget_event": "reserve", "call_id": call_id, "attempt": attempt,
                       "reserved_usd": round(float(usd), 12), "ts": _now()})
        return True, spent

    def settle(self, call_id, cost_usd, source):
        """Replace a call's reservations with its actual cost (in memory; in a separate ledger, also on disk)."""
        self.settled[call_id] = max(0.0, float(cost_usd))
        if self.separate_ledger and self.sink is not None:
            self.sink({"budget_event": "settle", "call_id": call_id, "cost_usd": round(float(cost_usd), 12),
                       "cost_source": source, "ts": _now()})

    def stop_row(self, reason, **fields):
        """The row written when a run stops on the budget (not a call record: it has no seed)."""
        row = {"budget_event": "stop", "stop": reason, "spent_usd": round(self.spent(), 12),
               "budget_usd": self.cap_usd, "ts": _now()}
        row.update(fields)
        return row
