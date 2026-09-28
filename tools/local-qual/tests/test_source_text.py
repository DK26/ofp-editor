#!/usr/bin/env python3
"""The tool's own source text holds no invisible or direction-changing characters (tools/local-qual).

h01 scans every Python and PowerShell file of the tool and of this test folder. A bidi override, an isolate, a
zero-width character or a Unicode tag character in source code changes what a reviewer sees without changing what
the interpreter runs ("Trojan Source", CVE-2021-42574): a string literal can look shorter than it is, or a line can
display its parts out of order. The repository is public and the tool handles an API key, so its source must read
the same on screen as it runs. Tests that need such characters (hostile server text, for example) write them as
escapes (``"\\u202e"``), which read as what they are.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import os
import re
import unittest

import support
from support import check

# The characters no source line may hold, as a character class. C0 controls other than tab and line feed, DEL and
# NEL (U+0085): invisible on screen, and a carriage return that does not end a line makes a terminal overwrite the
# text before it. U+061C, U+200E and U+200F: the Arabic letter mark and the left-to-right and right-to-left marks.
# U+202A-U+202E and U+2066-U+2069: the bidi embeddings, overrides and isolates CVE-2021-42574 names. U+200B-U+200D,
# U+2060-U+2064 and U+FEFF: zero-width characters and invisible operators. U+2028 and U+2029: line and paragraph
# separators, which some editors break a line at and Python does not. U+E0000-U+E007F: the tag characters, which
# render as nothing. A byte order mark at the very start of a file is allowed: Windows PowerShell 5.1 reads a UTF-8
# script correctly only with one, and there it marks the encoding rather than hiding text.
HIDDEN = re.compile("[\x00-\x08\x0b-\x1f\x7f\x85\u061c\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069"
                    "\u2028\u2029\ufeff\U000e0000-\U000e007f]")
# The source files scanned: code, where a hidden character can change what a reviewer believes the program does.
SOURCE_SUFFIXES = (".py", ".ps1")


def _source_files():
    """Every Python and PowerShell file under the tool folder (``support.TOOL``, which includes cloud/) and this
    test folder, each once, in a stable order."""
    found = set()
    for top in (support.TOOL, support.TESTS_DIR):
        for folder, dirs, files in os.walk(top):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            found.update(os.path.normcase(os.path.abspath(os.path.join(folder, name)))
                         for name in files if name.endswith(SOURCE_SUFFIXES))
    return sorted(found)


def _where(path):
    """`path` relative to the tool folder for a short report, or whole when it cannot be (on Windows, a tool copy
    named by LOCALQUAL_TOOL can sit on another drive than this test folder, and relpath refuses that)."""
    try:
        return os.path.relpath(path, support.TOOL)
    except ValueError:
        return path


def h01_sources_hold_no_invisible_or_bidi_characters():
    """No Python or PowerShell file of the tool or its tests holds a bidi control, a zero-width character, a tag
    character or a stray control character (a leading byte order mark excepted).

    Why: such a character makes the code on screen differ from the code that runs; a test's hostile string written
    with raw bidi characters, for example, displays reordered in an editor and on the review page. Escapes keep
    every character visible.

    How: each file is read as UTF-8 (a file that is not UTF-8 fails the case too) and split at line feeds only, not
    with ``str.splitlines``, which would also split at a vertical tab, a form feed, NEL or U+2028 and so never report
    them. The carriage return of a CRLF line end is dropped; every other character is searched with HIDDEN, and a
    hit is reported as file, line, column and code point.
    """
    files = _source_files()
    check(len(files) >= 20, f"only {len(files)} source files found under {support.TOOL}")
    hits = []
    for path in files:
        try:
            # newline="" keeps every carriage return as it is on disk (text mode would turn a lone one into a line
            # feed and hide it).
            with open(path, encoding="utf-8", newline="") as f:
                text = f.read()
        except UnicodeDecodeError as exc:
            hits.append(f"{_where(path)}: not UTF-8 ({exc.reason} at byte {exc.start})")
            continue
        if text.startswith("\ufeff"):
            text = text[1:]
        for n, line in enumerate(text.split("\n"), 1):
            for m in HIDDEN.finditer(line[:-1] if line.endswith("\r") else line):
                hits.append(f"{_where(path)}:{n}:{m.start() + 1} U+{ord(m.group()):04X}")
    check(not hits, "hidden characters in source: " + "; ".join(hits[:20]))
    return f"{len(files)} Python and PowerShell files hold no bidi, zero-width, tag or stray control character"


# ── unittest wiring ──────────────────────────────────────────────────────────

class SourceTextTests(support.CaseTestCase):
    """Source-text hygiene of the tool (see the module docs)."""

    cases = (h01_sources_hold_no_invisible_or_bidi_characters,)


if __name__ == "__main__":
    unittest.main()
