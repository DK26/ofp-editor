#!/usr/bin/env python3
"""The answer-blind scaffold algorithms that need no menu (tools/local-qual; ``run.py --scaffold``, doc 59).

What it owns
------------
* Words and stems (``stem``, ``content_stems``, ``_norm_token``, ``_norm_text``): a deliberately light normalisation
  so lexical overlap counts are less brittle.
* The diff arm's (S1) comparison of two option descriptions: ``nearest_pairs`` (each option's most similar
  neighbour, independent of the menu order) and ``diff_phrases`` (the wording one has and the other lacks), with the
  algorithm described step by step below.
* The rule arm's (S2) choice of the decisive card sentence (``select_rule_sentence``, by IDF-weighted overlap with the
  request) and its card block (``rule_card_text``).
* The eliminate (S5) and pairwise (S6) rankings from letter probabilities: ``rank_real``, ``keep_top`` (X is never
  masked), ``pair_schedule`` (both orders of every pair) and ``aggregate_pairwise``.

How it fits
-----------
Everything here reads option texts, the request or the card of the answer-blind view, never an answer. scaffolds.py
renders the texts (every rendering goes through its ``menu``, which the leakage tests watch) and re-exports every name
here; scaffold_run.py runs the multi-call arms with the rankings. Split out of scaffolds.py to keep each file readable
in one pass. No function does I/O, so the same inputs always give the same result (doc 59 T-L9). Standard library only.
"""
import math
import re
from difflib import SequenceMatcher


# Function words dropped before lexical overlap is counted. Quantifiers and negations (only, every, none, not) are
# dropped too: they occur in most rule sentences and most requests, so they would add overlap without topic.
STOPWORDS = frozenset("""
a an the and or but nor of to in on at by for with from into onto as is are was were be been being it its this that
these those there here which who whom whose what when where why how if then than so such do does did done can could
should would will shall may might must has have had not no none only every each any all some both either neither
one own same other others own their them they he she his her we our you your i me my also just very more most less
""".split())


_TOKEN_RE = re.compile(r"[a-z0-9#]+")


def stem(word):
    """A light suffix stripper (ies -> y, then -s, -ing, -ed), so 'triggers' meets 'trigger' and 'destroyed' meets
    'destroy'. Deliberately crude: it only has to make overlap counts less brittle, never to be linguistically right."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    for suffix in ("ing", "ed"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def content_stems(text):
    """The set of stemmed content words of `text` (lower case, stopwords dropped).

    One-letter tokens are dropped unless they are digits: the possessive in "group's" splits into "group" and "s",
    and a lone "s" would count as overlap between any two texts with a possessive."""
    return {stem(t) for t in _TOKEN_RE.findall((text or "").lower())
            if t not in STOPWORDS and (len(t) > 1 or t.isdigit())}


def _norm_token(token):
    """A whitespace token as it is compared: lower case, surrounding punctuation removed ("dismount;" -> "dismount")."""
    return token.strip(" \t;,.:()\"'").lower()


def _norm_text(text):
    """Text as it is compared for identity: lower case, words only, single spaces."""
    return " ".join(re.findall(r"[a-z0-9#']+", (text or "").lower()))


# ── diff (S1): how the closest options differ ────────────────────────────────
# Algorithm (answer-blind; permutation-invariant up to the letters):
# 1. Each real option's description is split into whitespace tokens; tokens are compared after _norm_token.
# 2. Similarity of two options = difflib.SequenceMatcher ratio of their token lists, always computed with the option
#    whose key sorts first as the first argument (ratio is not exactly symmetric; fixing the argument order by key makes
#    the result independent of the menu order).
# 3. Each option's nearest neighbour is the other option with the highest similarity; ties go to the smaller key.
# 4. The unordered pairs {option, nearest neighbour} are collected; each pair is rendered once, in menu order of its
#    earlier-lettered member. Every real option appears in at least one line (as itself or as a neighbour), so every
#    option gets the same treatment (doc 59 T-L4).
# 5. For a pair, SequenceMatcher's opcodes give the token runs present in one description and not the other. A run of
#    one token is widened by the token before it (unless that token ends a clause), so "#2" reads "End #2". At most
#    MAX_PHRASES runs per side are shown; the rest are summarised as "and more", never silently dropped.
# The escape (X) has no description and is never diffed. Only option texts are read: the request is not used, so no
# overlap with the request can steer which lines appear.
DIFF_HEADING = "How the closest options differ (worked out by the editor from the option texts):"


MAX_PHRASES = 4


def _similarity(a, b):
    """SequenceMatcher ratio of two options' normalised description tokens, argument order fixed by key."""
    first, second = (a, b) if a["key"] <= b["key"] else (b, a)
    ta = [_norm_token(t) for t in first["desc"].split()]
    tb = [_norm_token(t) for t in second["desc"].split()]
    return SequenceMatcher(None, ta, tb, autojunk=False).ratio()


def nearest_pairs(opts):
    """The unordered nearest-neighbour pairs of `opts`, as (key, key) tuples sorted by key (step 3-4 above)."""
    pairs = []
    for o in opts:
        # Sorted by key first: max() returns the first of several equal maxima, so ties go to the smallest key.
        others = sorted((p for p in opts if p["key"] != o["key"]), key=lambda p: p["key"])
        if not others:
            continue
        best = max(others, key=lambda p: _similarity(o, p))
        pair = tuple(sorted((o["key"], best["key"])))
        if pair not in pairs:
            pairs.append(pair)
    return pairs


def _phrase(raw, i1, i2):
    """The display phrase for tokens raw[i1:i2], widened by one token of context for a one-token run (step 5)."""
    if i2 - i1 == 1 and i1 > 0 and not raw[i1 - 1].endswith((";", ",")):
        i1 -= 1
    return " ".join(raw[i1:i2]).strip(" ;,")


def diff_phrases(a, b):
    """(phrases only in a's description, phrases only in b's), from SequenceMatcher opcodes (step 5).

    Computed with the smaller key first and mapped back, so the result for {a, b} does not depend on the order the
    caller passes them in."""
    swap = a["key"] > b["key"]
    first, second = (b, a) if swap else (a, b)
    ra, rb = first["desc"].split(), second["desc"].split()
    na, nb = [_norm_token(t) for t in ra], [_norm_token(t) for t in rb]
    only_a, only_b = [], []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, na, nb, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if i2 > i1 and any(na[i1:i2]):
            only_a.append(_phrase(ra, i1, i2))
        if j2 > j1 and any(nb[j1:j2]):
            only_b.append(_phrase(rb, j1, j2))
    only_a = [p for p in only_a if p]
    only_b = [p for p in only_b if p]
    return (only_b, only_a) if swap else (only_a, only_b)


def _quote_list(phrases):
    if not phrases:
        return "no wording the other lacks"
    shown = ", ".join(f'"{p}"' for p in phrases[:MAX_PHRASES])
    return shown + (f" and {len(phrases) - MAX_PHRASES} more" if len(phrases) > MAX_PHRASES else "")


# ── rule (S2): the decisive card sentence ────────────────────────────────────
# Algorithm (answer-blind: reads the request, the card and the option labels only):
# 1. Split the card into sentences at ".", "!" or "?" followed by whitespace and a capital letter, digit or quote.
# 2. For each sentence s: score(s) = sum over the stems it shares with the request of idf(w), with
#    idf(w) = ln(1 + N / df(w)), N the number of sentences and df(w) the number of sentences containing w. A word in
#    every sentence of the card ("trigger" on a trigger card) counts least; a word only one sentence has counts most.
# 3. Ties (within 1e-9) go to the sentence that names more distinct option labels (a rule about the menu's options),
#    then to the earlier sentence.
# 4. When no sentence shares a stem with the request (score 0 everywhere), the sentence naming the most option labels
#    is chosen, then the first; the record says so (fallback "no_overlap").
# Known failure, kept on purpose so the experiment measures it: on HM04 the request words "player", "come" and "back"
# select the Respawn point parameter sentence, which describes the lure (doc 59 §4.2 S2's "confident error" risk).
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def card_sentences(card):
    """The card's sentences (step 1), stripped, empty ones dropped."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(card or "") if s.strip()]


def select_rule_sentence(view):
    """(sentence or None, detail) chosen by steps 1-4 above. None when the item has no card."""
    sentences = card_sentences(view.get("card"))
    if not sentences:
        return None, {"fallback": "no_card", "n_sentences": 0}
    request = content_stems(view["request"])
    stems = [content_stems(s) for s in sentences]
    n = len(sentences)
    df = {}
    for st in stems:
        for w in st:
            df[w] = df.get(w, 0) + 1
    labels = [_norm_text(o["label"]) for o in view["options"]]

    def label_hits(s):
        text = " " + _norm_text(s) + " "
        return sum(1 for lab in set(labels) if lab and f" {lab} " in text)

    scored = []
    for i, (s, st) in enumerate(zip(sentences, stems)):
        shared = sorted(st & request)
        score = sum(math.log(1.0 + n / df[w]) for w in shared)
        scored.append((round(score, 9), label_hits(s), -i, i, shared))
    best = max(scored)
    detail = {"n_sentences": n, "index": best[3], "score": best[0], "shared": best[4], "label_hits": best[1],
              "scores": [x[0] for x in scored]}
    if best[0] == 0:
        detail["fallback"] = "no_overlap"
    return sentences[best[3]], detail


def rule_card_text(sentence):
    """The card block of the rule arm: the same "[REFERENCE CARD]" frame as the cards condition, one sentence in it,
    so the only difference from the plain cards request is the card's content."""
    return "" if sentence is None else "\n\n[REFERENCE CARD]\n" + sentence


def rank_real(p_by_key, order_keys):
    """The real option keys ranked by probability, highest first; ties go to the earlier seeded position.

    `order_keys` is the scored menu's real-option order (escape excluded). A key missing from p_by_key counts 0."""
    pos = {k: i for i, k in enumerate(order_keys)}
    return sorted(order_keys, key=lambda k: (-(p_by_key or {}).get(k, 0.0), pos[k]))


def keep_top(p_by_key, order_keys, k):
    """The eliminate arm's kept keys: the top k real options (X is always kept separately: never masked)."""
    return rank_real(p_by_key, order_keys)[: max(1, min(k, len(order_keys)))]


def pair_schedule(cands):
    """Every unordered pair of the candidates, each in both orders: [(a, b), (b, a), ...] in rank order.

    Asking both orders cancels a first-position preference inside each pair (pairwise ranking prompting scores both
    orders for the same reason, doc 59 [66])."""
    out = []
    for i, a in enumerate(cands):
        for b in cands[i + 1:]:
            out += [(a, b), (b, a)]
    return out


def aggregate_pairwise(cands, votes, escape_key, p_by_key):
    """(chosen key, detail) from the pair calls' votes (each a key, the escape key, or None for an invalid reply).

    Rule: the escape wins when more than half of the pair calls chose X (invalid replies count in the denominator);
    otherwise the candidate that won the most calls (a count of won calls over both orders of every pair, not a
    Copeland score of pair majorities), ties to the higher first-pass probability, then to the better first-pass
    rank."""
    wins = {c: 0 for c in cands}
    escape_votes = invalid = 0
    for v in votes:
        if v is None:
            invalid += 1
        elif v == escape_key:
            escape_votes += 1
        elif v in wins:
            wins[v] += 1
        else:
            invalid += 1  # a key outside the pair cannot come back from a two-option menu; counted, never scored
    detail = {"wins": wins, "escape_votes": escape_votes, "invalid": invalid, "calls": len(votes)}
    if votes and escape_votes * 2 > len(votes):
        detail["rule"] = "escape_majority"
        return escape_key, detail
    if invalid == len(votes):
        detail["rule"] = "fallback_first_pass"
        return cands[0] if cands else escape_key, detail
    rank = {c: i for i, c in enumerate(cands)}
    best = max(cands, key=lambda c: (wins[c], (p_by_key or {}).get(c, 0.0), -rank[c]))
    detail["rule"] = "most_wins"
    return best, detail
