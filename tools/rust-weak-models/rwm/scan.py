"""Code extraction from model replies, the pre-compile static scan, and escape-hatch counts.

The static scan is a sandbox layer, not a correctness check: it rejects source that
could reach outside the crate (processes, files, network, environment, foreign code,
`include!`) or re-route the entry point. A rejected file counts as a `bypass`
failure and the reason is fed back. The test crate's `lib.rs` additionally carries
`#![forbid(unsafe_code)]`.
"""
from __future__ import annotations

import re

_FENCE_RUST = re.compile(r"```[ \t]*(?:rust|rs)[^\n]*\n(.*?)```", re.S | re.I)
_FENCE_ANY = re.compile(r"```[^\n]*\n(.*?)```", re.S)
_THINK = re.compile(r"<think>.*?</think>", re.S | re.I)


def extract_code(reply: str) -> str | None:
    """First ```rust block, else the first fenced block; None if there is none."""
    text = _THINK.sub("", reply or "")
    m = _FENCE_RUST.search(text) or _FENCE_ANY.search(text)
    if not m:
        return None
    code = m.group(1).strip("\n")
    return code + "\n" if code.strip() else None


# (pattern, reason) pairs; patterns run on source with comments and strings removed.
_FORBIDDEN = [
    (r"\bstd\s*::\s*process\b", "uses std::process"),
    (r"\bstd\s*::\s*fs\b", "uses std::fs"),
    (r"\bstd\s*::\s*net\b", "uses std::net"),
    (r"\bstd\s*::\s*env\b", "uses std::env"),
    (r"\bstd\s*::\s*io\s*::\s*stdin\b", "reads stdin"),
    (r"\binclude(_str|_bytes)?\s*!", "uses include!"),
    (r"\b(option_)?env\s*!", "uses env!"),
    (r"\bextern\b", "declares extern items"),
    (r"#\s*\[\s*path\b", "uses #[path]"),
    (r"\bunsafe\b", "uses unsafe"),
    (r"#\s*!\s*\[\s*no_(std|core|implicit_prelude)", "changes the crate prelude"),
    (r"\bmod\s+\w+\s*;", "declares an out-of-file module"),
    (r"\bglobal_asm\s*!|\basm\s*!", "uses inline assembly"),
    (r"#\s*\[\s*(export_name|no_mangle|link)\b", "uses linkage attributes"),
]


def strip_comments_and_strings(src: str) -> str:
    """Blanks out comments and string/char literal contents (keeps line structure)."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            i = j
            continue
        if src.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif src.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            out.append(" ")
            i = j
            continue
        m = re.match(r'r(#*)"', src[i:])
        if m and (i == 0 or not (src[i - 1].isalnum() or src[i - 1] == "_")):
            close = '"' + m.group(1)
            j = src.find(close, i + m.end())
            j = n if j < 0 else j + len(close)
            out.append('""')
            i = j
            continue
        if c == "'":
            # char literal ('"', '\n', '\u{1}'); a lifetime ('a) does not match
            m = re.match(r"'(\\[^']{1,10}|[^\\'])'", src[i:])
            if m:
                out.append("' '")
                i += m.end()
                continue
        if c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            out.append('""')
            i = j + 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def static_scan(code: str) -> str | None:
    """Reason for rejection, or None if the file may be compiled."""
    bare = strip_comments_and_strings(code)
    for pattern, reason in _FORBIDDEN:
        if re.search(pattern, bare):
            return reason
    for m in re.finditer(r"macro_rules\s*!\s*\w+\s*\{", bare):
        body = bare[m.end(): m.end() + 2000]
        if re.search(r"\bsolve\b", body):
            return "defines a macro that produces the entry point"
    if not re.search(r"\bfn\s+solve\b", bare):
        return "no `fn solve` entry point"
    return None


_HATCHES = {
    "unwrap": r"\.unwrap\(\)",
    "expect": r"\.expect\(",
    "panic": r"\bpanic!\s*\(",
    "unreachable": r"\bunreachable!\s*\(",
    "todo": r"\b(todo|unimplemented)!\s*\(",
    "unwrap_or_default": r"\.unwrap_or_default\(\)",
    "unwrap_or_literal": r"\.unwrap_or\(\s*-?[0-9]",
    "id_cast": r"\bas\s+(u32|usize|u64|i32|i64)\b",
    "clone": r"\.clone\(\)",
    "index": r"\w\[[^\]\[]+\]",
}


def escape_hatches(code: str) -> dict[str, int]:
    """Counts of patterns that sidestep forced handling (static, exploratory metric)."""
    bare = strip_comments_and_strings(code)
    return {k: len(re.findall(p, bare)) for k, p in _HATCHES.items()}
