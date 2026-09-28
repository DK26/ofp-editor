#!/usr/bin/env python3
"""The numeric building blocks of cascade.py (tools/local-qual): safe numbers, flag parsing, signal quality and the
temperature fit.

What it owns
------------
* Reading numbers from untrusted records and flags: ``real`` and ``probability`` (finite JSON numbers only, never a
  bool, NaN or infinity), ``parse_assignments``, ``parse_price``, ``parse_cost`` and ``parse_thresholds`` (the
  ARM=VALUE and threshold flags, each refused with a message naming the flag).
* Signal quality of a stage's confidence against its own correctness: ``auroc`` (ties count half), ``ece`` (equal-
  width bins over [0, 1]) and ``brier``, gathered by ``signal_quality``.
* The temperature fit ``cascade.py calibrate`` writes and ``run.py --calibration`` reads: ``fit_rows``, ``nll``
  (log-sum-exp for stability), ``fit_temperature`` (golden-section search over beta = 1/T, where the NLL is convex)
  and ``calibration_report`` (NLL, ECE and Brier before and after scaling).
* ``fold_of`` (the cross-fit fold of an item, from a hash of its id) and the small helpers ``mean`` and ``rnd``.

How it fits
-----------
Pure functions only; cascade.py's simulator and commands call them. Split out of cascade.py to keep each file readable
in one pass; cascade.py imports every name it uses from here. Standard library only.
"""
import hashlib
import math
import statistics
from collections import defaultdict

from logprob_pick import T_MAX, T_MIN, apply_temperature
from uplift import spec


ECE_BINS = 10


# A correct option with probability 0 (outside the listed tokens) would make the log-likelihood infinite; the fit
# counts it at this floor instead. It is constant in T, so it does not move the optimum.
P_FLOOR = 1e-6


# Threshold comparisons tolerate float noise from the grid (0.1 * 7 is 0.7000000000000001).
EPS = 1e-9


MAX_THRESHOLDS = 1001


GOLDEN_ITERATIONS = 200


def real(v):
    """v as a float when it is a finite JSON number (not a bool), else None."""
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def probability(v):
    p = real(v)
    return p if p is not None and 0.0 <= p <= 1.0 + 1e-9 else None


def mean(xs):
    xs = list(xs)
    return statistics.fmean(xs) if xs else None


def rnd(v, nd=6):
    return None if v is None else round(v, nd)


def fold_of(item_id):
    """0 or 1, from a hash of the item id (stable across runs and machines)."""
    return int(hashlib.sha256(str(item_id).encode("utf-8")).hexdigest()[:8], 16) % 2


def parse_assignments(values, what, parse):
    """{arm: parsed value} from ARM=VALUE strings.

    Split at the first '=': an arm (model|suite|condition|variant) never contains one, while a value (a file path)
    may.
    """
    out = {}
    for text in values or []:
        arm, sep, value = text.partition("=")
        if not sep or not arm:
            raise ValueError(f"{what} must be ARM=VALUE, got {text!r}")
        out[spec(arm)] = parse(value)
    return out


def parse_price(value):
    parts = value.split(",")
    nums = [real(_float(p)) for p in parts]
    if len(parts) != 2 or any(n is None or n < 0 for n in nums):
        raise ValueError(f"--price needs IN,OUT in USD per million tokens (two numbers >= 0), got {value!r}")
    return tuple(nums)


def parse_cost(value):
    n = real(_float(value))
    if n is None or n < 0:
        raise ValueError(f"--cost needs a number of USD per call >= 0, got {value!r}")
    return n


def _float(text):
    try:
        return float(text)
    except ValueError:
        return None


def parse_thresholds(text):
    """'start:stop:step' (inclusive) or a comma list; every value finite and in [0, 1]."""
    if ":" in text:
        parts = [_float(p) for p in text.split(":")]
        if len(parts) != 3 or any(p is None or not math.isfinite(p) for p in parts) or parts[2] <= 0:
            raise ValueError(f"--thresholds start:stop:step needs three numbers and a step > 0, got {text!r}")
        start, stop, step = parts
        count = int(math.floor((stop - start) / step + EPS)) + 1
        if count > MAX_THRESHOLDS:
            raise ValueError(f"--thresholds would give {count} values; at most {MAX_THRESHOLDS}")
        values = [round(start + i * step, 10) for i in range(max(0, count))]
    else:
        values = [_float(p) for p in text.split(",") if p.strip()]
        if len(values) > MAX_THRESHOLDS:
            raise ValueError(f"at most {MAX_THRESHOLDS} thresholds")
    if not values or any(v is None or not math.isfinite(v) or not 0.0 <= v <= 1.0 for v in values):
        raise ValueError(f"--thresholds must be numbers in [0, 1], got {text!r}")
    return sorted(set(values))


def auroc(pairs):
    """P(confidence of a correct unit > that of a wrong one), ties counting half; None without both classes."""
    pos = [c for c, y in pairs if y >= 0.5]
    neg = [c for c, y in pairs if y < 0.5]
    if not pos or not neg:
        return None
    wins = sum(1.0 if p > q else (0.5 if p == q else 0.0) for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def ece(pairs, bins=ECE_BINS):
    """Expected calibration error with equal-width bins over [0, 1]."""
    if not pairs:
        return None
    groups = defaultdict(list)
    for c, y in pairs:
        groups[min(int(c * bins), bins - 1)].append((c, y))
    return sum(len(g) * abs(mean(c for c, _ in g) - mean(y for _, y in g)) for g in groups.values()) / len(pairs)


def brier(pairs):
    return mean((c - y) ** 2 for c, y in pairs) if pairs else None


def signal_quality(units):
    """AUROC, ECE and Brier of a stage's confidence against its own correctness (a missing confidence counts 0)."""
    pairs = [(u["conf"] if u["conf"] is not None else 0.0, u["correct"]) for u in units]
    return {"auroc": rnd(auroc(pairs)), "ece": rnd(ece(pairs)), "brier": rnd(brier(pairs)),
            "mean_confidence": rnd(mean(c for c, _ in pairs)), "no_confidence": sum(1 for u in units
                                                                                  if u["conf"] is None)}


def fit_rows(dec):
    """(p_by_key, correct key) of every usable logprob decision of an arm."""
    rows = []
    for d in dec.values():
        r = d["rec"]
        p = r.get("p_by_key")
        if r.get("error") or not isinstance(p, dict) or not p:
            continue
        vals = {k: probability(v) for k, v in p.items()}
        if any(v is None for v in vals.values()) or sum(vals.values()) <= 0 or r.get("correct_key") is None:
            continue
        rows.append((vals, r["correct_key"]))
    return rows


def nll(rows, beta):
    """Mean negative log-likelihood of the correct key under p ∝ p^beta (beta = 1/T), log-sum-exp for stability."""
    total = 0.0
    for p, correct in rows:
        logs = [beta * math.log(v) for v in p.values() if v > 0]
        top = max(logs)
        lse = top + math.log(sum(math.exp(x - top) for x in logs))
        pc = p.get(correct, 0.0)
        total += (lse - beta * math.log(pc)) if pc > 0 else -math.log(P_FLOOR)
    return total / len(rows)


def fit_temperature(rows):
    """The T in [T_MIN, T_MAX] that minimises the NLL: golden-section search over beta = 1/T (convex in beta)."""
    lo, hi = 1.0 / T_MAX, 1.0 / T_MIN
    g = (math.sqrt(5) - 1) / 2
    a, b = hi - g * (hi - lo), lo + g * (hi - lo)
    fa, fb = nll(rows, a), nll(rows, b)
    for _ in range(GOLDEN_ITERATIONS):
        if fa <= fb:
            hi, b, fb = b, a, fa
            a = hi - g * (hi - lo)
            fa = nll(rows, a)
        else:
            lo, a, fa = a, b, fb
            b = lo + g * (hi - lo)
            fb = nll(rows, b)
        if hi - lo < 1e-12:
            break
    return 1.0 / ((lo + hi) / 2)


def calibration_report(rows, temperature):
    """NLL, ECE and Brier of the argmax confidence before and after scaling with `temperature`."""
    def pairs(t):
        out = []
        for p, correct in rows:
            q = apply_temperature(p, t) if t != 1.0 else p
            best = max(q, key=q.get)
            out.append((q[best], 1.0 if best == correct else 0.0))
        return out
    before, after = pairs(1.0), pairs(temperature)
    return {"nll_before": rnd(nll(rows, 1.0)), "nll_after": rnd(nll(rows, 1.0 / temperature)),
            "ece_before": rnd(ece(before)), "ece_after": rnd(ece(after)),
            "brier_before": rnd(brier(before)), "brier_after": rnd(brier(after))}
