"""Code extraction from model replies, the pre-compile static scan, and escape-hatch counts.

The static scan is a best-effort guard, not a sandbox and not a correctness check: it
rejects source that could reach outside the crate (processes, files, network, environment,
foreign code, `include!`) or re-route the entry point. A rejected file counts as a `bypass`
failure and the reason is fed back. The test crate's `lib.rs` additionally carries
`#![forbid(unsafe_code)]`. Because the scan reads text, not a parsed crate, the runner talks
only to endpoints the operator trusts (loopback by default, see `rwm.llm`).

How standard-library paths are checked (added after review, doc 64): every path rooted at
`std`, `core` or `alloc` must name a module on `_ALLOWED_STD` as its first segment, and that
holds inside grouped imports (`use std::{collections::HashMap, fmt}`) too. Crate-root
aliases (`use std as s`, `std::{self as q}`), glob imports of the root (`use std::*`) and
paths built from macro variables (`std::$m`, `$root::fs`) are rejected, and raw identifiers
(`std::r#fs`) are read as plain identifiers first. The pilot's 768 saved solutions get the
same verdicts under this version as under the one that ran.
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

# First path segments allowed after `std::`, `core::` or `alloc::`: data, formatting and
# arithmetic modules only. Everything that can touch the machine (fs, io, env, process,
# net, os, path, thread, time, ffi, ptr, alloc, arch, panic, ...) is left out on purpose;
# a new module a task legitimately needs is added here with a test.
_ALLOWED_STD = frozenset("""
    any array ascii borrow boxed cell char clone cmp collections convert default error
    f32 f64 fmt hash hint i8 i16 i32 i64 i128 isize iter marker mem num ops option
    prelude primitive rc result slice str string sync u8 u16 u32 u64 u128 usize vec
""".split())
_STD_ROOT = re.compile(r"(?<![\w$])(?:::\s*)?(std|core|alloc)\s*::\s*")
_ROOT_ALIAS = re.compile(r"\buse\s+(?:::\s*)?(?:std|core|alloc)\s+as\b")
_MACRO_PATH = re.compile(r"\$\w+\s*::|::\s*\$")
_RAW_IDENT = re.compile(r"(?<![\w#])r#(?=[A-Za-z_])")


def _group_items(text: str, open_at: int) -> list[str] | None:
    """Top-level items of the `{ ... }` group whose `{` is at `open_at`, split on commas
    outside nested braces; None when the group is not closed (the compiler rejects it)."""
    depth, start, items = 0, open_at + 1, []
    for i, ch in enumerate(text[open_at:], open_at):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                items.append(text[start:i])
                return [x.strip() for x in items if x.strip()]
        elif ch == "," and depth == 1:
            items.append(text[start:i])
            start = i + 1
    return None


def _first_segment_problem(root: str, item: str) -> str | None:
    """Why the path `root::item...` is not allowed, or None. `item` starts right after the
    root's `::` (a module name, `*`, `self`, `$var` or a nested group)."""
    m = re.match(r"(\*|\$|self\b|[A-Za-z_]\w*)", item)
    if not m:
        return f"uses an unrecognised {root} path"
    seg = m.group(1)
    if seg == "*":
        return f"imports everything from {root}"
    if seg == "$":
        return "builds a path from a macro variable"
    if seg == "self":
        return f"aliases or re-imports the {root} crate root"
    if re.match(r"\s*!", item[m.end():]):
        return None  # a macro called by path (`std::format!`); banned macros are caught above
    if seg not in _ALLOWED_STD:
        return f"uses {root}::{seg}, which is not on the allowed module list"
    return None


def _std_path_problem(bare: str) -> str | None:
    """The first disallowed standard-library path in comment- and string-free source."""
    if _ROOT_ALIAS.search(bare):
        return "aliases the standard-library crate root"
    if _MACRO_PATH.search(bare):
        return "builds a path from a macro variable"
    for m in _STD_ROOT.finditer(bare):
        root, rest_at = m.group(1), m.end()
        if bare.startswith("{", rest_at):
            items = _group_items(bare, rest_at)
            for item in items or []:
                problem = _first_segment_problem(root, item)
                if problem:
                    return problem
            continue
        problem = _first_segment_problem(root, bare[rest_at:rest_at + 80])
        if problem:
            return problem
    return None


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
        m = re.match(r'b?r(#*)"', src[i:])
        # A raw string (`r"…"`, `r#"…"#`) or raw byte string (`br#"…"#`) starts a token:
        # the character before it must not continue an identifier.
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
    # Raw identifiers (`r#fs`) name the same item as the plain identifier, so read them as
    # plain ones before any pattern runs.
    bare = _RAW_IDENT.sub("", strip_comments_and_strings(code))
    for pattern, reason in _FORBIDDEN:
        if re.search(pattern, bare):
            return reason
    for m in re.finditer(r"macro_rules\s*!\s*\w+\s*\{", bare):
        body = bare[m.end(): m.end() + 2000]
        if re.search(r"\bsolve\b", body):
            return "defines a macro that produces the entry point"
    problem = _std_path_problem(bare)
    if problem:
        return problem
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
