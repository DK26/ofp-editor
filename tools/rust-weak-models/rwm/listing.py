"""Public-API listing generator for a small Rust crate (the "API docs" the model sees).

rustdoc JSON needs a nightly toolchain, so this module derives the listing from the
source instead, with one generator for both variants (a fairness control):

* keeps `//!` crate docs, `///` item docs, `#[derive]` / `#[must_use]` attributes;
* keeps `pub` free functions, structs (public fields only), enums, traits, consts,
  type aliases and `pub use mb_spec::...` re-exports;
* keeps inherent `impl` blocks with their `pub fn` signatures (bodies elided) and
  one-line trait impls (`impl Display for X {}`) so the model sees what is
  implemented; drops impls of the internal `Sealed` trait;
* flattens private `mod x;` files into the crate root (the crates re-export
  everything at the root);
* drops private items, `pub(crate)` items, plain `//` comments, other attributes
  (including `#[diagnostic::on_unimplemented]`, which rustdoc does not show either:
  its text reaches the model only through compiler errors, which is the mechanism
  under test) and `#[cfg(test)]` modules.

The lexer understands comments (nested block comments too), string, raw string,
byte and char literals and lifetimes, which is all these crates use.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Lexer ─────────────────────────────────────────────────────────────────────


@dataclass
class Tok:
    kind: str  # doc_outer, doc_inner, ident, punct, lit, lifetime
    text: str
    start: int
    end: int


def lex(src: str) -> list[Tok]:
    toks: list[Tok] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if src.startswith("///", i) and not src.startswith("////", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            toks.append(Tok("doc_outer", src[i:j], i, j))
            i = j
            continue
        if src.startswith("//!", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            toks.append(Tok("doc_inner", src[i:j], i, j))
            i = j
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
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
            i = j
            continue
        m = re.match(r'b?r(#*)"', src[i:])
        if m and (i == 0 or not (src[i - 1].isalnum() or src[i - 1] == "_")):
            hashes = m.group(1)
            close = '"' + hashes
            j = src.find(close, i + m.end())
            j = n if j < 0 else j + len(close)
            toks.append(Tok("lit", src[i:j], i, j))
            i = j
            continue
        if c == '"' or (c == "b" and src.startswith('b"', i)):
            j = i + (2 if c == "b" else 1)
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            j += 1
            toks.append(Tok("lit", src[i:j], i, j))
            i = j
            continue
        if c == "'":
            # char literal ('a', '\n', '\u{1}') or lifetime ('a, 'static)
            if i + 1 < n and src[i + 1] == "\\":
                j = src.find("'", i + 2)
                j = n if j < 0 else j + 1
                toks.append(Tok("lit", src[i:j], i, j))
                i = j
                continue
            if i + 2 < n and src[i + 2] == "'":
                toks.append(Tok("lit", src[i : i + 3], i, i + 3))
                i += 3
                continue
            m = re.match(r"'[A-Za-z_][A-Za-z0-9_]*", src[i:])
            if m:
                toks.append(Tok("lifetime", m.group(0), i, i + m.end()))
                i += m.end()
                continue
        if c.isalpha() or c == "_":
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", src[i:])
            toks.append(Tok("ident", m.group(0), i, i + m.end()))
            i += m.end()
            continue
        if c.isdigit():
            m = re.match(r"[0-9][0-9_]*(\.[0-9][0-9_]*)?([eE][+-]?[0-9]+)?[A-Za-z0-9_]*", src[i:])
            toks.append(Tok("lit", m.group(0), i, i + m.end()))
            i += m.end()
            continue
        if src.startswith("::", i) or src.startswith("->", i) or src.startswith("=>", i):
            toks.append(Tok("punct", src[i : i + 2], i, i + 2))
            i += 2
            continue
        toks.append(Tok("punct", c, i, i + 1))
        i += 1
    return toks


# ── Item parser ───────────────────────────────────────────────────────────────


@dataclass
class Item:
    docs: list[str]
    attrs: list[str]  # raw attribute text, e.g. "#[derive(Debug)]"
    head_start: int  # source offset of the first non-attribute token
    body: tuple[int, int] | None  # token indices of `{` and matching `}` (inclusive)
    end_tok: int  # index of the last token of the item
    head_end: int  # source offset where the body `{` (or the `;`) starts
    words: list[str] = field(default_factory=list)  # leading keywords/idents


def _match(toks: list[Tok], i: int, open_: str, close: str) -> int:
    depth = 0
    while i < len(toks):
        t = toks[i]
        if t.kind == "punct" and t.text == open_:
            depth += 1
        elif t.kind == "punct" and t.text == close:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(toks) - 1


def parse_items(src: str, toks: list[Tok], lo: int, hi: int) -> list[Item]:
    """Items between token indices lo..hi (exclusive)."""
    items: list[Item] = []
    i = lo
    while i < hi:
        docs: list[str] = []
        attrs: list[str] = []
        while i < hi:
            t = toks[i]
            if t.kind == "doc_outer":
                docs.append(t.text)
                i += 1
            elif t.kind == "doc_inner":
                i += 1  # handled separately for the crate root
            elif t.kind == "punct" and t.text == "#":
                j = i + 1
                if j < hi and toks[j].text == "!":
                    j += 1
                k = _match(toks, j, "[", "]")
                attrs.append(" ".join(src[toks[i].start : toks[k].end].split()))
                i = k + 1
            else:
                break
        if i >= hi:
            break
        start = i
        words = []
        j = i
        while j < hi and toks[j].kind in ("ident",) and len(words) < 6:
            words.append(toks[j].text)
            j += 1
        # `pub(crate)` → words = ["pub"], next token "(" — detect below.
        is_value_item = any(w in ("const", "static", "use", "type") for w in words[:3])
        paren = 0
        body = None
        k = i
        while k < hi:
            t = toks[k]
            if t.kind == "punct" and t.text in "([":
                paren += 1
            elif t.kind == "punct" and t.text in ")]":
                paren -= 1
            elif t.kind == "punct" and t.text == ";" and paren == 0:
                break
            elif t.kind == "punct" and t.text == "{" and paren == 0 and not is_value_item:
                close = _match(toks, k, "{", "}")
                body = (k, close)
                k = close
                break
            elif t.kind == "punct" and t.text == "{" and is_value_item:
                k = _match(toks, k, "{", "}")
            k += 1
        head_end = toks[body[0]].start if body else toks[min(k, hi - 1)].start
        items.append(Item(docs, attrs, toks[start].start, body, k, head_end, words))
        i = k + 1
    return items


# ── Rendering ─────────────────────────────────────────────────────────────────

KEEP_ATTR = re.compile(r"^#\[(derive\(|must_use)")


def _is_pub(src: str, item: Item) -> bool:
    head = src[item.head_start : item.head_end].lstrip()
    return head.startswith("pub ") or head.startswith("pub\n")


def _clean_head(src: str, item: Item) -> str:
    head = src[item.head_start : item.head_end]
    head = re.sub(r"//[^\n]*", "", head)  # strip line comments inside signatures
    # Continuation lines keep their indentation relative to the item's own column.
    line_start = src.rfind("\n", 0, item.head_start) + 1
    base = item.head_start - line_start
    lines = []
    for n, ln in enumerate(head.strip().splitlines()):
        ln = ln.rstrip()
        if n and ln[:base].strip() == "":
            ln = ln[base:]
        if ln.strip():
            lines.append(ln)
    text = "\n".join(lines)
    # rustdoc shows parameter patterns without `mut`.
    text = re.sub(r"(?<=[(,\s])mut (?=\w)", "", text)
    return text.rstrip().rstrip(",")


def _indent(text: str, pad: str) -> str:
    return "\n".join(pad + ln if ln else ln for ln in text.splitlines())


def _dedent_block(lines: list[str]) -> list[str]:
    stripped = [ln.strip() for ln in lines]
    return stripped


def _attrs(item: Item) -> list[str]:
    return [a for a in item.attrs if KEEP_ATTR.match(a)]


def _render_fields(src: str, toks: list[Tok], body: tuple[int, int], tuple_struct: bool) -> tuple[list[str], int]:
    """Public fields of a struct body as lines; returns (lines, private_count)."""
    lo, hi = body
    out: list[str] = []
    private = 0
    # split on depth-0 commas
    depth = 0
    seg_start = lo + 1
    segs: list[tuple[int, int]] = []
    for idx in range(lo + 1, hi):
        t = toks[idx]
        if t.kind == "punct" and t.text in "([{<":
            depth += 1
        elif t.kind == "punct" and t.text in ")]}>":
            depth -= 1
        elif t.kind == "punct" and t.text == "," and depth == 0:
            segs.append((seg_start, idx))
            seg_start = idx + 1
    if seg_start < hi:
        segs.append((seg_start, hi))
    for a, b in segs:
        docs = [toks[x].text.strip() for x in range(a, b) if toks[x].kind == "doc_outer"]
        code = [toks[x] for x in range(a, b) if toks[x].kind not in ("doc_outer", "doc_inner")]
        if not code:
            continue
        text = src[code[0].start : code[-1].end]
        text = " ".join(text.split())
        if text.startswith("pub ") and not text.startswith("pub("):
            out.extend(docs)
            out.append(text + ",")
        else:
            private += 1
    return out, private


def render_items(src: str, toks: list[Tok], items: list[Item], pad: str, crate_dir: Path, in_impl: bool = False) -> list[str]:
    out: list[str] = []
    deferred_mods: list[Path] = []
    for it in items:
        words = it.words
        head = _clean_head(src, it)
        first = words[0] if words else ""
        # ── modules: flatten `mod x;` files, drop inline private/test modules ──
        if first == "mod" or (first == "pub" and len(words) > 1 and words[1] == "mod"):
            if any("cfg(test)" in a for a in it.attrs):
                continue
            name = words[-1] if it.body is None else words[1 if first == "mod" else 2]
            if it.body is None:
                path = crate_dir / f"{name}.rs"
                if path.exists():
                    deferred_mods.append(path)  # flattened after the file's own items
            continue
        if first == "impl" or (first == "unsafe" and len(words) > 1 and words[1] == "impl"):
            if re.search(r"\bSealed\b", head):
                continue
            is_trait_impl = re.search(r"\bfor\b", head) is not None
            if is_trait_impl or it.body is None:
                one = " ".join(head.split())
                one = re.sub(r"\b(std::)?(fmt|error)::", "", one)  # rustdoc-style short trait paths
                out.append(pad + one + " {}")
                out.append("")
                continue
            lo, hi = it.body
            inner = parse_items(src, toks, lo + 1, hi)
            inner_lines = render_items(src, toks, inner, pad + "    ", crate_dir, in_impl=True)
            if inner_lines:
                out.append(pad + " ".join(head.split()) + " {")
                out.extend(inner_lines)
                out.append(pad + "}")
                out.append("")
            continue
        if not _is_pub(src, it) or head.startswith("pub(") or head.startswith("pub (crate)"):
            continue
        kind = next((w for w in words if w in ("fn", "struct", "enum", "trait", "const", "static", "type", "use")), "")
        if kind == "use":
            if "mb_spec" not in head:
                continue
            out.extend(pad + d.strip() for d in it.docs)
            out.append(pad + " ".join(head.split()) + ";")
            continue
        for d in it.docs:
            out.append(pad + d.strip())
        for a in _attrs(it):
            out.append(pad + a)
        if kind == "fn":
            out.append(_indent(head, pad) + ";")
        elif kind == "struct":
            if it.body is None:
                # tuple or unit struct
                m = re.match(r"(.*?)\((.*)\)\s*$", " ".join(head.split()), re.S)
                if m:
                    fields = [f.strip() for f in m.group(2).split(",") if f.strip()]
                    shown = [f for f in fields if f.startswith("pub ") and not f.startswith("pub(")]
                    inner = ", ".join(shown) if len(shown) == len(fields) else "/* private fields */"
                    out.append(pad + f"{m.group(1)}({inner});")
                else:
                    out.append(pad + " ".join(head.split()) + ";")
            else:
                fields, private = _render_fields(src, toks, it.body, False)
                out.append(pad + " ".join(head.split()) + " {")
                out.extend(pad + "    " + f for f in fields)
                if private:
                    out.append(pad + "    /* private fields */")
                out.append(pad + "}")
        elif kind == "enum":
            lo, hi = it.body if it.body else (0, 0)
            body_src = src[toks[lo].start : toks[hi].end] if it.body else "{}"
            body_src = re.sub(r"(?m)^\s*//(?![/!])[^\n]*\n", "", body_src)
            lines = [ln.strip() for ln in body_src.strip()[1:-1].splitlines() if ln.strip()]
            out.append(pad + " ".join(head.split()) + " {")
            out.extend(pad + "    " + ln for ln in lines)
            out.append(pad + "}")
        elif kind == "trait":
            if it.body is None:
                out.append(pad + " ".join(head.split()) + ";")
                continue
            lo, hi = it.body
            inner = parse_items(src, toks, lo + 1, hi)
            inner_lines = []
            for x in inner:
                inner_lines.extend(pad + "    " + d.strip() for d in x.docs)
                inner_lines.append(_indent(_clean_head(src, x), pad + "    ") + ";")
            if inner_lines:
                out.append(pad + " ".join(head.split()) + " {")
                out.extend(inner_lines)
                out.append(pad + "}")
            else:
                out.append(pad + " ".join(head.split()) + " {}")
        else:  # const, static, type
            out.append(pad + " ".join(src[it.head_start : toks[it.end_tok].end].split()))
        if not in_impl:
            out.append("")
    for path in deferred_mods:
        out.extend(render_file(path, crate_dir, pad))
    return out


def _tidy(lines: list[str]) -> list[str]:
    """Drops blank lines between consecutive one-line trait impls."""
    out: list[str] = []
    for ln in lines:
        if out and out[-1] == "" and len(out) >= 2 and out[-2].endswith(" {}") and out[-2].lstrip().startswith("impl"):
            if ln.lstrip().startswith("impl") and ln.endswith(" {}"):
                out.pop()
        out.append(ln)
    return out


def crate_docs(src: str, toks: list[Tok]) -> list[str]:
    return [t.text.strip() for t in toks if t.kind == "doc_inner"]


def render_file(path: Path, crate_dir: Path, pad: str = "") -> list[str]:
    src = path.read_text(encoding="utf-8")
    toks = lex(src)
    items = parse_items(src, toks, 0, len(toks))
    return render_items(src, toks, items, pad, crate_dir)


def generate(crate_src_dir: Path, crate_name: str = "mb") -> str:
    """Listing for the crate whose `src/` directory is given."""
    lib = crate_src_dir / "lib.rs"
    src = lib.read_text(encoding="utf-8")
    toks = lex(src)
    lines = [f"// Public API of crate `{crate_name}` (generated listing: signatures and docs, bodies elided).", ""]
    docs = crate_docs(src, toks)
    if docs:
        lines.extend(docs)
        lines.append("")
    lines.extend(render_file(lib, crate_src_dir))
    text = "\n".join(_tidy(lines))
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


def estimate_tokens(text: str) -> int:
    """Rough BPE-like token estimate (no tokenizer on the host): identifier runs of up
    to 6 characters, each punctuation mark and each newline count as one token."""
    count = 0
    for m in re.finditer(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]|\n", text):
        s = m.group(0)
        count += (len(s) + 5) // 6 if s[0].isalnum() or s[0] == "_" else 1
    return count
