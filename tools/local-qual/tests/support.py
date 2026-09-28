#!/usr/bin/env python3
"""Shared plumbing for the tools/local-qual test suite (standard library ``unittest`` only).

What it owns
------------
* Where the tool under test lives: ``TOOL`` is the folder above this one, or the folder named by the
  ``LOCALQUAL_TOOL`` environment variable (the mutation checks point the whole suite at a deliberately broken copy
  that way). Importing this module puts ``TOOL`` first on ``sys.path``, so a test module imports ``run``, ``budget``
  or ``scaffolds`` exactly as the tool's own scripts import each other.
* A fresh work folder per test module (``make_work``), created in the system temp folder so no test output ever
  lands in the repository, and removed afterwards unless ``LOCALQUAL_KEEP_WORK`` is set (keep it to read the records
  a failing test wrote).
* ``CaseTestCase``, the bridge between the suite's case functions and ``unittest`` (below).
* Golden-file helpers (``load_golden``, ``run_digests``) for the regression tests that pin the request bodies,
  records and summaries of earlier tool versions.

Why case functions
------------------
Every check is a plain function named after its group and number (``t04_budget_cap_...``, ``l03_...``,
``c07_...``) that raises ``AssertionError`` through ``check()`` and returns a one-line summary of the numbers it
verified. The README's verification notes cite these names and numbers, so they stay stable. ``CaseTestCase`` turns
each function listed in a subclass's ``cases`` tuple into a ``test_<name>`` method; ``unittest`` then runs them in
name order, reports failures with the function's own message, and shows the first docstring line under ``-v``.
Set ``LOCALQUAL_TEST_DETAIL=1`` to print each passing case's summary as well. A case that cannot run on this
machine (the Windows-only key-script checks elsewhere) returns a string starting with "skipped", which becomes a
``unittest`` skip rather than a silent pass.

Run the whole suite from the repository root::

    python -m unittest discover -s tools/local-qual/tests

Standard library only; nothing here touches the network.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.abspath(os.environ.get("LOCALQUAL_TOOL") or os.path.dirname(TESTS_DIR))
GOLDEN_DIR = os.path.join(TESTS_DIR, "golden")

# The tool's modules import each other by bare name (they are scripts, not a package), so the tests do the same.
if TOOL not in sys.path:
    sys.path.insert(0, TOOL)
if TESTS_DIR not in sys.path:
    sys.path.insert(1, TESTS_DIR)
# Keep the tool folder free of bytecode caches written by the in-process imports below (git ignores them anyway).
sys.dont_write_bytecode = True


def check(cond, what):
    """Raise AssertionError(what) unless `cond` holds: the one assertion every case function uses."""
    if not cond:
        raise AssertionError(what)


def make_work(tag):
    """A new, empty work folder for one test module, outside the repository (``LOCALQUAL_TEST_WORK`` overrides)."""
    root = os.environ.get("LOCALQUAL_TEST_WORK")
    if root:
        path = os.path.join(os.path.abspath(root), tag)
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        return path
    return tempfile.mkdtemp(prefix=f"localqual-{tag}-")


def remove_work(path):
    """Delete a work folder made by make_work, unless LOCALQUAL_KEEP_WORK asks to keep it for inspection."""
    if path and not os.environ.get("LOCALQUAL_KEEP_WORK") and not os.environ.get("LOCALQUAL_TEST_WORK"):
        shutil.rmtree(path, ignore_errors=True)


def read_text(path):
    """A UTF-8 text file's content, with the file closed at once (a bare open().read() leaves that to the collector,
    which unittest reports as a ResourceWarning and which can keep a Windows file locked)."""
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_json(path):
    """A UTF-8 JSON file's content (see read_text)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_text(path, text):
    """Write `text` to `path` (UTF-8, newlines as given), closing the file at once."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def child_env(**extra):
    """The environment for a child process of the tool: UTF-8 console, no bytecode, and no stray bearer key.

    LLAMA_API_KEY is removed because run.py reads it as llama-server's default key; a value left in the developer's
    shell would otherwise change the Authorization header of every local request the tests compare.
    """
    env = dict(os.environ)
    env.pop("LLAMA_API_KEY", None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(extra)
    return env


# ── Case functions as unittest tests ────────────────────────────────────────

def _case_method(fn):
    """A unittest method that runs one case function and turns a "skipped ..." result into a skip."""
    def method(self):
        detail = fn()
        if isinstance(detail, str) and detail.startswith("skipped"):
            self.skipTest(detail)
        if detail and os.environ.get("LOCALQUAL_TEST_DETAIL"):
            print(f"\n    {fn.__name__}: {detail}", file=sys.stderr)
    method.__name__ = "test_" + fn.__name__
    method.__doc__ = fn.__doc__
    return method


class CaseTestCase(unittest.TestCase):
    """Base class: each function in a subclass's ``cases`` tuple becomes a ``test_<function name>`` method.

    Subclasses reset their mock server's state in ``setUp`` (every case starts from a clean mock, as the original
    runner did) and list their cases in the order they should run; ``unittest`` sorts the generated methods by
    name, and the case names carry their number, so that order is kept.
    """

    cases = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for fn in cls.__dict__.get("cases", ()):
            setattr(cls, "test_" + fn.__name__, _case_method(fn))


# ── Golden files ────────────────────────────────────────────────────────────

def load_golden(name):
    """One JSON file from tests/golden/ (see make_goldens.py for how each was produced)."""
    with open(os.path.join(GOLDEN_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def sha256_lines(lines):
    """SHA-256 of the given text lines joined with newlines (UTF-8), as the goldens store it."""
    h = hashlib.sha256()
    for line in lines:
        h.update(line.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def run_digests(grid, tagged_lines):
    """Per-run digests of a dump: [{"argv", "n", "sha256"}] from ``(run index, line)`` pairs and the run grid.

    Grouping by run lets a failing comparison name the command line whose output changed, instead of reporting one
    difference somewhere in two thousand request bodies.
    """
    per_run = [[] for _ in grid]
    for n, line in tagged_lines:
        per_run[n].append(line)
    return [{"argv": argv, "n": len(lines), "sha256": sha256_lines(lines)} for argv, lines in zip(grid, per_run)]


def compare_digests(label, want, got):
    """None when two digest lists agree, else a message naming the first command line whose output differs."""
    if len(want) != len(got):
        return f"{label}: {len(got)} runs, the golden has {len(want)}"
    for w, g in zip(want, got):
        if w != g:
            return (f"{label}: run {' '.join(g['argv'])!r} differs from the golden ({g['n']} lines, sha256 "
                    f"{g['sha256'][:16]}; golden {w['n']} lines, {w['sha256'][:16]}; golden argv "
                    f"{' '.join(w['argv'])!r})")
    return None
