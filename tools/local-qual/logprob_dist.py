#!/usr/bin/env python3
"""Reading letter probabilities out of llama-server responses (tools/local-qual; ``run.py --pick-mode logprob``).

What it owns
------------
* ``candidates``: the listed next tokens of a /completion response in any of the five shapes llama-server builds
  return, each entry checked (finite probabilities in [0, 1], a short list of byte values, no token id twice) and
  sorted; malformed entries are counted, never trusted.
* ``token_letter``: which menu letter a next token spells, if any (leading word-boundary markers allowed, nothing but
  the closing quote after the letter), and ``letter_distribution``: the mass per letter summed over its token variants,
  renormalised over the menu, with the bound on what the unlisted letters could hold.
* ``listed_count`` and ``truncation_error``: a list shorter than n_probs comes from a truncated candidate set, not the
  next-token distribution, and is refused.
* Distributions over option keys: ``rotations``, ``average_by_key`` (averaging per key is what cancels a position
  bias), ``apply_temperature``, ``argmax_key`` and ``entropy``.

How it fits
-----------
logprob_pick.LogprobPicker calls these for every option order it sends; cascade.py and scaffold_run.py reuse the
temperature and the key averaging. Everything here is a pure function of a response, so the parser-safety tests can
feed it hostile input directly. Split out of logprob_pick.py to keep each file readable in one pass; logprob_pick.py
re-exports every name. Standard library only.
"""
import math


# Characters a tokenizer puts in front of a word: a space in detokenised text, and the raw word-boundary markers of
# SentencePiece (U+2581) and GPT-2 byte-level BPE (U+0120), in case a server returns raw pieces. Not a tab: a raw tab
# inside a JSON string is invalid (json.loads rejects control characters), so run.py could not parse that answer.
LEADING = " ▁Ġ"


# What may follow a letter inside its token before the closing quote: spaces only (run.py strips them), for the same
# reason.
TRAILING = " "


# The listed probabilities of one position may sum to at most 1 (they are a top-N subset of a distribution);
# anything above 1 + this tolerance is a broken response, not rounding.
MASS_TOLERANCE = 1e-3


# A token's "bytes" list longer than this is not a token; ignore it rather than decode it. Parser-safety cap with
# headroom: the longest ordinary token is 128 bytes in the Qwen3 and Qwen3.5 vocabularies (over a hundred tokens
# exceed 64) and 48 bytes in Gemma 4's (read from the GGUF vocabularies, 2026-09-28).
MAX_TOKEN_BYTES = 256


class LogprobError(ValueError):
    """A llama-server response that carries no usable token probabilities (the decision is recorded as an error)."""


def _number(v):
    """v as a float when it is a real JSON number (not a bool), else None."""
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _entry(e):
    """(token text, probability, token id or None) from one listed token, or None when the entry is unusable.

    Permissive on shape (logprob or prob; token or tok_str), strict on values: a probability must be finite and in
    [0, 1] (a logprob <= 0; -inf or the lowest float means probability 0), and a ``bytes`` field must be a list of at
    most MAX_TOKEN_BYTES byte values. Anything else is counted as a bad entry by the caller and ignored. When
    ``bytes`` is present and not empty it is the token's text: llama-server cuts ``token`` at the last whole UTF-8
    character, so "A" plus the first bytes of "…" arrives as the text "A" while its bytes decode to "A\\ufffd", which
    is not a letter.
    """
    if not isinstance(e, dict):
        return None
    text = e.get("token", e.get("tok_str"))
    raw = e.get("bytes")
    if raw is not None:
        # A bytes field that is not a short list of byte values is malformed, and so is the whole entry.
        if not (isinstance(raw, list) and len(raw) <= MAX_TOKEN_BYTES
                and all(isinstance(b, int) and not isinstance(b, bool) and 0 <= b <= 255 for b in raw)):
            return None
        if raw:
            text = bytes(raw).decode("utf-8", "replace")
    if not isinstance(text, str):
        return None
    if "logprob" in e:
        lp = _number(e["logprob"])
        if lp is None or math.isnan(lp) or lp > 1e-6 or lp == math.inf:
            return None
        p = 0.0 if lp == -math.inf else min(1.0, math.exp(lp))
    elif "prob" in e:
        p = _number(e["prob"])
        if p is None or not math.isfinite(p) or p < 0.0 or p > 1.0 + 1e-6:
            return None
        p = min(1.0, p)
    else:
        return None
    tid = e.get("id")
    return text, p, (tid if isinstance(tid, int) and not isinstance(tid, bool) else None)


def candidates(resp, n_probs):
    """The listed next tokens of a llama-server response, whatever its shape.

    Returns (entries, shape, sampled token text or None, bad entries, entries beyond n_probs), where entries are
    (token text, probability) sorted by probability, highest first, and cut at n_probs (a server that sends more
    than asked is not trusted to have sorted them). The server listed len(entries) + bad + beyond tokens in all.
    Raises LogprobError when there are no probabilities at all.
    Shapes read: ``native`` (completion_probabilities[0].top_logprobs), ``native-post`` (top_probs),
    ``native-old`` (probs with tok_str/prob, builds before 2025), ``openai`` (choices[0].logprobs.content[0]
    .top_logprobs) and ``openai-legacy`` (choices[0].logprobs.top_logprobs[0] as {token: logprob}).
    """
    if not isinstance(resp, dict):
        raise LogprobError("the response is not a JSON object")
    raw = shape = sampled = None
    cp = resp.get("completion_probabilities")
    choices = resp.get("choices")
    if isinstance(cp, list) and cp and isinstance(cp[0], dict):
        first = cp[0]
        sampled = first.get("token", first.get("content"))
        for key, name in (("top_logprobs", "native"), ("top_probs", "native-post"), ("probs", "native-old")):
            if isinstance(first.get(key), list):
                raw, shape = first[key], name
                break
    elif isinstance(choices, list) and choices and isinstance(choices[0], dict):
        lp = choices[0].get("logprobs")
        content = lp.get("content") if isinstance(lp, dict) else None
        legacy = lp.get("top_logprobs") if isinstance(lp, dict) else None
        if isinstance(content, list) and content and isinstance(content[0], dict) \
                and isinstance(content[0].get("top_logprobs"), list):
            raw, shape, sampled = content[0]["top_logprobs"], "openai", content[0].get("token")
        elif isinstance(legacy, list) and legacy and isinstance(legacy[0], dict):
            raw = [{"token": t, "logprob": v} for t, v in legacy[0].items()]
            shape = "openai-legacy"
            tokens = lp.get("tokens")
            sampled = tokens[0] if isinstance(tokens, list) and tokens else None
    if raw is None:
        raise LogprobError("no token probabilities in the response (does this llama-server build honour n_probs?)")
    out, seen, bad = [], set(), 0
    for e in raw:
        parsed = _entry(e)
        if parsed is None:
            bad += 1
            continue
        text, p, tid = parsed
        if tid is not None:
            # The same token id twice is a malformed list; counting it twice would inflate its letter.
            if tid in seen:
                bad += 1
                continue
            seen.add(tid)
        out.append((text, p))
    out.sort(key=lambda tp: -tp[1])  # stable: equal probabilities keep the server's order
    return out[:n_probs], shape, (sampled if isinstance(sampled, str) else None), bad, max(0, len(out) - n_probs)


def token_letter(text, valid_letters, opens_string=True):
    """The menu letter a next token means, or None.

    `opens_string` says the prompt already ends with the quote that opens the choice string (ANSWER_PREFIX does);
    otherwise the token must bring that quote itself ('"A', ' "A'). After the letter only the closing quote (and
    whatever follows it, such as '"}') or nothing may come: "A" alone may still be followed by the closing quote in
    the next token, while "AB" or "A1" would make a longer string, which is not a menu letter.
    """
    t = text.lstrip(LEADING)
    if not opens_string:
        if not t.startswith('"'):
            return None
        t = t[1:].lstrip(LEADING)
    if not t or not t[0].isascii() or not t[0].isalpha():
        return None
    letter = t[0].upper()
    if letter not in valid_letters:
        return None
    rest = t[1:].lstrip(TRAILING)
    return letter if (not rest or rest.startswith('"')) else None


def listed_count(entries, bad, beyond):
    """How many tokens the server listed for the position (kept, malformed and beyond n_probs)."""
    return len(entries) + bad + beyond


def truncation_error(listed, n_probs):
    """None when the server listed n_probs tokens, else why the list cannot be read as a distribution.

    A full vocabulary always has n_probs (at most MAX_N_PROBS) tokens to list; fewer means the server computed the
    probabilities over a candidate set (backend sampling, -bs), which can be the one greedy token at temperature 0.
    """
    if listed >= n_probs:
        return None
    return (f"the server listed {listed} of {n_probs} tokens: its probabilities cover a truncated candidate set "
            f"(backend sampling, -bs?), not the next-token distribution")


def letter_distribution(entries, valid_letters, opens_string=True):
    """Per-letter mass, the token variants behind it, and the renormalised distribution over `valid_letters`.

    Raises LogprobError when the listed probabilities add up to more than 1 (a broken response). ``dist`` is None
    when no valid letter was listed at all (the decision then has no answer; it is not a server error).
    """
    total = sum(p for _, p in entries)
    if total > 1.0 + MASS_TOLERANCE:
        raise LogprobError(f"the listed probabilities sum to {total:.4f}, more than 1")
    mass = {letter: 0.0 for letter in valid_letters}
    variants = {}
    for text, p in entries:
        letter = token_letter(text, valid_letters, opens_string)
        if letter is None:
            continue
        # Different tokens that spell the same letter are different next-token events: add them.
        mass[letter] += p
        variants.setdefault(letter, []).append(text)
    valid = sum(mass.values())
    dist = {letter: mass[letter] / valid for letter in valid_letters} if valid > 0 else None
    missing = [letter for letter in valid_letters if letter not in variants]
    floor = entries[-1][1] if entries else None
    # Each missing letter's tokens were not listed, so each holds at most the floor, and all of them together at most
    # what the list left unlisted: the error bound of treating them as 0.
    bound = min(max(0.0, 1.0 - total), len(missing) * floor) if floor is not None else None
    return {"letter_mass": mass, "variants": variants, "valid_mass": valid, "total_mass": total,
            "missing": missing, "floor": floor, "missing_mass_max": bound, "dist": dist}


def rotations(opts, n):
    """The first min(n, len(opts)) cyclic rotations of `opts`; rotation 0 is `opts` itself."""
    return [opts[j:] + opts[:j] for j in range(min(n, len(opts)))]


def average_by_key(orders):
    """Mean probability per option key over the orders that produced a distribution.

    Averaging per key (not per letter) is what makes the rotations cancel a position bias: a key's probability is
    read from whichever letter it had in each order.
    """
    used = [o for o in orders if o.get("dist") is not None]
    if not used:
        return None
    keys = list(used[0]["letter_to_key"].values())
    total = {k: 0.0 for k in keys}
    for o in used:
        for letter, key in o["letter_to_key"].items():
            total[key] = total.get(key, 0.0) + o["dist"].get(letter, 0.0)
    return {k: v / len(used) for k, v in total.items()}


def apply_temperature(p_by_key, temperature):
    """Temperature scaling: p_T(k) ∝ p(k)^(1/T), computed in log space; keys with probability 0 stay 0."""
    logs = {k: math.log(p) / temperature for k, p in p_by_key.items() if p > 0}
    if not logs:
        return dict(p_by_key)
    top = max(logs.values())
    w = {k: math.exp(v - top) for k, v in logs.items()}
    z = sum(w.values())
    return {k: (w[k] / z if k in w else 0.0) for k in p_by_key}


def argmax_key(p_by_key, letter_to_key):
    """(best key, tie flag). Ties go to the key with the earliest letter in order 0, so the choice is reproducible."""
    best = max(p_by_key.values())
    ranked = [k for k in letter_to_key.values() if abs(p_by_key.get(k, 0.0) - best) <= 1e-12]
    return ranked[0], len(ranked) > 1


def entropy(p):
    """Shannon entropy in nats."""
    return -sum(v * math.log(v) for v in p.values() if v > 0)
