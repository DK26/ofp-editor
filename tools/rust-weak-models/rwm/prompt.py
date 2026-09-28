"""Prompt assembly with an equal budget for both variants.

Message layout (design.json `prompting.structure`):

  system: role text, domain rules, API listing of crate `mb` (variant-specific,
          generated), appendix (export format; neutral padding in the shorter
          variant), `mb_spec` catalog and `Refusal`.  This is a byte-stable prefix
          per variant, so llama-server's prompt cache reuses it across tasks.
  user:   the task's `mb_spec` module, the task text, the entry signature, the
          visible tests.  Identical for both variants.

Budget: with `budget="equal"` the shorter variant's appendix is padded with neutral
example exports until both system prompts have the same token count (exact counts
from the server's tokenizer when available, otherwise the local estimate).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import listing, padding
from .tasks import ROOT, VARIANTS, Task

PROMPTS = ROOT / "prompts"
SPEC_SRC = ROOT / "crates" / "mb-spec" / "src"
CONTEXT_OMITTED = "[earlier attempt omitted]"
FIX_INSTRUCTION = "Fix the file. Return the complete corrected file in one ```rust block."
NO_CODE_FEEDBACK = "No Rust code block was found; return the complete file in one ```rust block."

Counter = Callable[[str], int]


@dataclass
class SystemPrompts:
    text: dict[str, str]  # variant -> system prompt
    tokens: dict[str, int]  # variant -> token count (same counter for both)
    listing_tokens: dict[str, int]
    pad_tokens: dict[str, int]
    counter: str  # "server" or "estimate"

    def sha256(self, variant: str) -> str:
        return hashlib.sha256(self.text[variant].encode("utf-8")).hexdigest()


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8").strip()


def api_listing(variant: str) -> str:
    return listing.generate(ROOT / "crates" / f"mb-{variant}" / "src")


def _spec_shared() -> str:
    return (
        "// crate mb_spec: `catalog` and `refusal` items are re-exported at the crate root\n"
        "// (mb_spec::Side, mb_spec::Point, mb_spec::UnitIn, mb_spec::Refusal, ...).\n\n"
        + _read(SPEC_SRC / "catalog.rs")
        + "\n\n"
        + _read(SPEC_SRC / "refusal.rs")
    )


def _system(listing_text: str, pad: str) -> str:
    appendix = _read(PROMPTS / "appendix.md")
    if pad:
        appendix += "\n\n" + pad
    return (
        _read(PROMPTS / "system.md")
        + "\n\n## Domain rules\n\n"
        + _read(PROMPTS / "rules.md")
        + "\n\n## API of crate `mb`\n\n```rust\n"
        + listing_text.strip()
        + "\n```\n\n## Appendix: export format\n\n"
        + appendix
        + "\n\n## Crate `mb_spec` (shared definitions)\n\n```rust\n"
        + _spec_shared()
        + "\n```\n"
    )


def build_system_prompts(budget: str = "equal", counter: Counter | None = None) -> SystemPrompts:
    count = counter or listing.estimate_tokens
    listings = {v: api_listing(v) for v in VARIANTS}
    base = {v: _system(listings[v], "") for v in VARIANTS}
    base_tok = {v: count(base[v]) for v in VARIANTS}
    pads = {v: "" for v in VARIANTS}
    if budget == "equal":
        target = max(base_tok.values())
        for v in VARIANTS:
            gap = target - base_tok[v]
            if gap > 0:
                # Pad, then re-measure the whole prompt (joins can shift counts by a few tokens).
                pads[v] = padding.padding_text(gap, count)
    elif budget != "natural":
        raise ValueError(f"unknown budget mode {budget!r}")
    text = {v: _system(listings[v], pads[v]) for v in VARIANTS}
    return SystemPrompts(
        text=text,
        tokens={v: count(text[v]) for v in VARIANTS},
        listing_tokens={v: count(listings[v]) for v in VARIANTS},
        pad_tokens={v: count(pads[v]) if pads[v] else 0 for v in VARIANTS},
        counter="server" if counter else "estimate",
    )


def user_prompt(task: Task) -> str:
    """Task-specific part; identical for both variants."""
    mod = task.module
    return (
        f"## Task input: module `mb_spec::{mod}`\n\n```rust\n{task.spec_source().strip()}\n```\n\n"
        f"## Task\n\n{task.text('task.md').strip()}\n\n"
        "Write `src/solution.rs` with exactly this entry point:\n\n"
        f"```rust\npub fn solve(input: &mb_spec::{mod}::Input) -> Result<mb::Exported, mb_spec::Refusal>\n```\n\n"
        "The test harness calls it through `task::run(&input)`, which returns the export "
        "text, or the `Refusal` your `solve` returned.\n\n"
        f"## Visible tests\n\n```rust\n{task.text('visible.rs').strip()}\n```\n"
    )


def feedback_message(body: str) -> str:
    return f"{body.strip()}\n\n{FIX_INSTRUCTION}"


def fit_context(messages: list[dict], ctx_tokens: int, reserve: int, count: Counter) -> list[dict]:
    """Replaces the oldest failed attempt (assistant + feedback pair after the first
    user message) with a marker until the conversation fits `ctx_tokens - reserve`."""
    msgs = [dict(m) for m in messages]
    budget = ctx_tokens - reserve

    def total() -> int:
        return sum(count(m["content"]) + 4 for m in msgs)

    i = 2  # messages[0] system, [1] first user message
    while total() > budget and i + 1 < len(msgs) - 1:
        if msgs[i]["content"] != CONTEXT_OMITTED:
            msgs[i]["content"] = CONTEXT_OMITTED
            msgs[i + 1]["content"] = CONTEXT_OMITTED
        i += 2
    return msgs
