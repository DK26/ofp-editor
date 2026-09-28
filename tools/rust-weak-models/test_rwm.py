"""Unit tests for the harness (standard library `unittest`; no cargo, no model).

Run from this folder: python -m unittest test_rwm -v

Sections: code extraction and static scan; listing generator; prompt budget; test-output
parsing and feedback; resume; and the packaging checks added when the harness moved into
the repository (scaffold guard, git-ignored outputs, the live driver's model config, the
relocated analysis scripts, hidden characters and local paths, and the rule that no
enclosing Cargo workspace may adopt this one). The guard tests (scan bypasses, the model
endpoint, pinned prompts and tool configs, key and denylist hygiene, the server command)
live in `test_rwm_guards.py` and are imported at the end, so this module runs them too.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runner
from rwm import cargo, hygiene, listing, padding, prompt, scan, tasks
from rwm.tasks import ROOT, trap_category
from test_rwm_guards import _load_script, _tmpdir

# ── Code extraction and static scan ───────────────────────────────────────────


class ExtractCode(unittest.TestCase):
    def test_prefers_rust_fence(self):
        reply = "text\n```text\nnot this\n```\n```rust\nfn solve() {}\n```"
        self.assertEqual(scan.extract_code(reply), "fn solve() {}\n")

    def test_falls_back_to_first_fence(self):
        self.assertEqual(scan.extract_code("```\nfn solve() {}\n```"), "fn solve() {}\n")

    def test_no_fence_is_format_failure(self):
        self.assertIsNone(scan.extract_code("I would build the mission first."))

    def test_think_block_is_ignored(self):
        reply = "<think>```rust\nfn wrong() {}\n```</think>```rust\nfn solve() {}\n```"
        self.assertEqual(scan.extract_code(reply), "fn solve() {}\n")


class StaticScan(unittest.TestCase):
    OK = "use mb::Mission;\npub fn solve(input: &I) -> R { todo!() }\n"

    def test_accepts_plain_solution(self):
        self.assertIsNone(scan.static_scan(self.OK))

    def test_rejects_sandbox_escapes(self):
        for bad in ["std::process::exit(0);", "std::fs::read(\"x\");", "unsafe { }", "include!(\"x.rs\");",
                    "extern \"C\" { }", "#[path = \"x.rs\"] mod x;", "std::env::var(\"K\");", "mod other;"]:
            with self.subTest(bad=bad):
                self.assertIsNotNone(scan.static_scan(self.OK + bad))

    def test_strings_and_comments_do_not_trigger(self):
        code = self.OK + '// std::process is mentioned here\nconst S: &str = "unsafe std::fs";\nconst C: char = \'"\';\n'
        self.assertIsNone(scan.static_scan(code))

    def test_requires_entry_point(self):
        self.assertEqual(scan.static_scan("fn main() {}"), "no `fn solve` entry point")

    def test_escape_hatch_counts(self):
        h = scan.escape_hatches("let a = x.unwrap(); let b = y.expect(\"m\"); let c = z.unwrap_or(0); let d = i as u32;")
        self.assertEqual((h["unwrap"], h["expect"], h["unwrap_or_literal"], h["id_cast"]), (1, 1, 1, 1))


class TrapCategory(unittest.TestCase):
    def test_slugs_map_to_design_categories(self):
        self.assertEqual(trap_category("trap_seq_cycle_is_last"), "SEQ-CYCLE")
        self.assertEqual(trap_category("trap_ref_vehicle_wrong_side"), "REF-VEHICLE")
        self.assertEqual(trap_category("trap_err_handling_first_problem_wins"), "ERR-HANDLING")
        self.assertIsNone(trap_category("nominal_units"))


# ── Listing generator ─────────────────────────────────────────────────────────

SAMPLE_LIB = '''//! Crate docs.
mod inner;
pub use mb_spec::{Side};
use std::fmt;

/// A public struct.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct Thing {
    /// Visible.
    pub a: u32,
    hidden: u32,
}

struct Private;

impl Thing {
    /// Makes one.
    pub fn new(mut a: u32) -> Thing {
        // implementation detail
        Thing { a, hidden: 0 }
    }
    fn secret(&self) {}
    /// Bounded.
    pub fn go<S>(self) -> Self
    where
        S: Copy,
    {
        self
    }
}

impl fmt::Display for Thing {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{}", '}') }
}

#[diagnostic::on_unimplemented(message = "secret text")]
pub trait Marker {}

#[cfg(test)]
mod tests {
    pub fn t() {}
}
'''

SAMPLE_INNER = '''/// From a module.
pub fn helper(x: &str) -> usize { x.len() }
pub(crate) fn internal() {}
'''


class Listing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        (d / "lib.rs").write_text(SAMPLE_LIB, encoding="utf-8")
        (d / "inner.rs").write_text(SAMPLE_INNER, encoding="utf-8")
        self.text = listing.generate(d)

    def tearDown(self):
        self.tmp.cleanup()

    def test_public_items_and_docs_kept(self):
        for s in ["//! Crate docs.", "/// A public struct.", "pub a: u32,", "pub fn new(a: u32) -> Thing;",
                  "impl Display for Thing {}", "pub trait Marker {}", "pub fn helper(x: &str) -> usize;",
                  "pub use mb_spec::{Side};", "#[derive(Debug, Clone)]"]:
            with self.subTest(s=s):
                self.assertIn(s, self.text)

    def test_private_items_bodies_and_attributes_dropped(self):
        for s in ["hidden: u32", "struct Private", "fn secret", "implementation detail", "secret text",
                  "internal", "mod tests", "#[allow", "Thing { a, hidden: 0 }", "use std::fmt"]:
            with self.subTest(s=s):
                self.assertNotIn(s, self.text)
        self.assertIn("/* private fields */", self.text)

    def test_where_clause_rendered_without_trailing_comma(self):
        self.assertIn("    where\n        S: Copy;", self.text)

    def test_real_crates_render_and_fit_cap(self):
        for v in ("plain", "guided"):
            text = prompt.api_listing(v)
            self.assertIn("pub struct Mission", text)
            self.assertLess(listing.estimate_tokens(text), 7000, v)
            self.assertNotIn("mb_core", text)
            self.assertNotIn("guided", text.lower().replace("guidance", ""))


# ── Prompt budget ─────────────────────────────────────────────────────────────


class Budget(unittest.TestCase):
    def test_padding_is_deterministic_and_bounded(self):
        a = padding.padding_text(800, listing.estimate_tokens)
        b = padding.padding_text(800, listing.estimate_tokens)
        self.assertEqual(a, b)
        self.assertLessEqual(listing.estimate_tokens(a), 802)
        self.assertGreater(listing.estimate_tokens(a), 700)
        self.assertEqual(padding.padding_text(0, listing.estimate_tokens), "")

    def test_equal_budget_balances_variants(self):
        sp = prompt.build_system_prompts("equal")
        ratio = sp.tokens["guided"] / sp.tokens["plain"]
        self.assertAlmostEqual(ratio, 1.0, delta=0.02)
        self.assertGreater(sp.pad_tokens["plain"], 0)
        self.assertEqual(sp.pad_tokens["guided"], 0)

    def test_natural_budget_keeps_listing_gap(self):
        sp = prompt.build_system_prompts("natural")
        self.assertEqual(sp.pad_tokens, {"plain": 0, "guided": 0})
        self.assertGreater(sp.tokens["guided"], sp.tokens["plain"])

    def test_user_prompt_is_identical_across_variants(self):
        from rwm import tasks
        t = [x for x in tasks.discover(quiet=True) if x.id == "T07"][0]
        text = prompt.user_prompt(t)
        self.assertIn("pub fn solve(input: &mb_spec::t07::Input)", text)
        self.assertNotIn("validate", text.lower())

    def test_fit_context_drops_oldest_attempt_first(self):
        msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
        for i in range(3):
            msgs += [{"role": "assistant", "content": "x" * 400}, {"role": "user", "content": f"fb{i} " + "y" * 400}]
        out = prompt.fit_context(msgs, ctx_tokens=300, reserve=0, count=lambda s: len(s) // 4)
        self.assertEqual(out[2]["content"], prompt.CONTEXT_OMITTED)
        self.assertTrue(out[-1]["content"].startswith("fb2"), "latest feedback is kept")


# ── Test-output parsing and feedback ──────────────────────────────────────────

LIBTEST = """running 3 tests
test nominal_a ... ok
test trap_bounds_x ... FAILED
test edge_y ... ok

failures:

---- trap_bounds_x stdout ----

thread 'trap_bounds_x' panicked at tasks\\T02\\plain\\src\\solution.rs:12:5:
called `Option::unwrap()` on a `None` value

failures:
    trap_bounds_x

test result: FAILED. 2 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out
"""


class Parsing(unittest.TestCase):
    def test_libtest_results_and_sections(self):
        results, output = cargo.parse_test_output(LIBTEST)
        self.assertEqual(results, {"nominal_a": "ok", "trap_bounds_x": "FAILED", "edge_y": "ok"})
        self.assertIn("Option::unwrap()", output["trap_bounds_x"])

    def test_solution_panic_detected_by_location(self):
        _, output = cargo.parse_test_output(LIBTEST)
        self.assertTrue(cargo.solution_panicked(output["trap_bounds_x"]))
        self.assertFalse(cargo.solution_panicked("thread 't' panicked at tasks/T02/hidden.rs:3:1:\nassertion failed"))

    def test_diagnostics_are_blinded(self):
        from rwm.tasks import ROOT
        crate = ROOT / "tasks" / "T01" / "guided"
        text = "help: implemented for `mb_guided::Ready`\n  --> crates\\mb-guided\\src\\trigger.rs:1:1\n  --> crates/mb-plain/src/lib.rs:2:2"
        out = cargo._normalise_paths(text, crate)
        self.assertNotIn("guided", out)
        self.assertNotIn("plain", out)
        self.assertIn("mb::Ready", out)
        self.assertIn("mb/src/trigger.rs", out)

    def test_catch_levels(self):
        base = {"compile_ok": True, "visible_pass": True, "hidden_pass": True}
        self.assertEqual(runner.catch_level(dict(base, compile_ok=False)), "static")
        self.assertEqual(runner.catch_level(dict(base, visible_pass=False, hidden_pass=False)), "loop")
        self.assertEqual(runner.catch_level(dict(base, hidden_pass=False)), "silent")
        self.assertEqual(runner.catch_level(base), "missed")

    def test_seed_depends_on_task_sample_round_only(self):
        a = runner.seed_for("T01", 2, 1, 7)
        self.assertEqual(a, runner.seed_for("T01", 2, 1, 7))
        self.assertNotEqual(a, runner.seed_for("T01", 2, 2, 7))


class Resume(unittest.TestCase):
    """`run --resume` appends to an interrupted results file only when the run config is
    identical, and skips exactly the finished, non-infra episodes (a torn last line from
    a killed process is ignored rather than crashing the resume)."""

    HEADER = {"kind": "run", "run_id": "aaa", "mode": "live", "model": "m", "tasks": ["T01", "T02"],
              "variants": ["plain", "guided"], "samples": 1, "rounds": 3, "seed": 7,
              "sampler": {"temperature": 0.6}, "ctx": 24576, "budget": "equal", "system_sha256": {"plain": "x"}}

    def _write(self, lines):
        p = _tmpdir(self) / "r.jsonl"
        p.write_text("".join((json.dumps(x) if isinstance(x, dict) else x) + "\n" for x in lines), encoding="utf-8")
        return p

    def test_missing_file_resumes_nothing(self):
        done, prior, mismatch = runner.resume_state(_tmpdir(self) / "none.jsonl", dict(self.HEADER))
        self.assertEqual((done, prior, mismatch), (set(), [], None))

    def test_finished_episodes_skipped_infra_rerun_torn_line_ignored(self):
        p = self._write([self.HEADER,
                         {"kind": "episode", "task": "T01", "variant": "plain", "sample": 0, "infra_error": False},
                         {"kind": "episode", "task": "T02", "variant": "guided", "sample": 0, "infra_error": True},
                         '{"kind": "episode", "task": "T02", "vari'])
        done, prior, mismatch = runner.resume_state(p, dict(self.HEADER, run_id="bbb"))
        self.assertIsNone(mismatch)
        self.assertEqual(done, {("T01", "plain", 0)})
        self.assertEqual(prior, ["aaa"])

    def test_config_mismatch_is_refused(self):
        p = self._write([self.HEADER])
        for key, val in (("sampler", {"temperature": 0.7}), ("model", "other"), ("system_sha256", {"plain": "y"})):
            done, _prior, mismatch = runner.resume_state(p, dict(self.HEADER, **{key: val}))
            self.assertIn(key, mismatch or "")
            self.assertEqual(done, set())


# ── Packaging: fresh checkout, outputs, relocated scripts ─────────────────────


def _task_root(case: unittest.TestCase) -> Path:
    """A throwaway harness root (removed after the test) with one complete task folder (T01)
    and nothing generated: the state of a fresh clone before `python runner.py scaffold`."""
    root = _tmpdir(case)
    d = root / "tasks" / "T01"
    d.mkdir(parents=True)
    (d / "task.json").write_text(json.dumps({"id": "T01", "spec_module": "t01", "scored": True}), encoding="utf-8")
    for name in ("task.md", "visible.rs", "hidden.rs", "ref_plain.rs", "ref_guided.rs"):
        (d / name).write_text("", encoding="utf-8")
    return root


class ScaffoldGuard(unittest.TestCase):
    """The per-task test crates and Cargo.lock are generated and git-ignored, so a fresh
    clone has neither. Commands that compile must stop with the command that fixes it
    instead of failing inside Python file writes or cargo's manifest loader."""

    def test_missing_crates_and_lock_are_listed(self):
        """Both generated crate manifests of a task and the lock file are reported when absent."""
        root = _task_root(self)
        found = tasks.discover(root, quiet=True)
        self.assertEqual(tasks.scaffold_missing(found, root),
                         ["tasks/T01/plain/Cargo.toml", "tasks/T01/guided/Cargo.toml", "Cargo.lock"])

    def test_nothing_missing_once_scaffold_output_exists(self):
        """After scaffold wrote every manifest and the lock, nothing is reported."""
        root = _task_root(self)
        for v in ("plain", "guided"):
            (root / "tasks" / "T01" / v).mkdir()
            (root / "tasks" / "T01" / v / "Cargo.toml").write_text("", encoding="utf-8")
        (root / "Cargo.lock").write_text("", encoding="utf-8")
        self.assertEqual(tasks.scaffold_missing(tasks.discover(root, quiet=True), root), [])

    def test_hint_names_the_command_and_an_example(self):
        """The hint is None when nothing is missing; otherwise it counts, shows one path and
        names `python runner.py scaffold`."""
        self.assertIsNone(runner.scaffold_hint([]))
        hint = runner.scaffold_hint(["tasks/T01/plain/Cargo.toml", "Cargo.lock"])
        self.assertIn("python runner.py scaffold", hint)
        self.assertIn("2 generated file(s)", hint)
        self.assertIn("tasks/T01/plain/Cargo.toml", hint)

    def test_compiling_commands_stop_before_cargo(self):
        """verify, mutants, conformance and non-dry runs exit 2 with the hint, and cargo is
        never invoked; the dry run keeps its own missing-crate report."""
        for argv in (["verify"], ["mutants"], ["conformance"], ["run", "--mock", "ref"]):
            with self.subTest(argv=argv), \
                    mock.patch.object(tasks, "scaffold_missing", return_value=["Cargo.lock"]), \
                    mock.patch.object(cargo, "build", side_effect=AssertionError("cargo must not run")), \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(runner.main(argv), 2)
                self.assertIn("python runner.py scaffold", err.getvalue())


class Outputs(unittest.TestCase):
    """Everything the harness and its scripts write lands in a git-ignored place, so a run
    never dirties the repository and raw model output is never committed by accident."""

    def test_gitignore_covers_generated_and_run_output(self):
        """.gitignore names build output, run output, the generated crates, the lock file and
        the local model config."""
        lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for entry in ("/target/", "/results/", "/Cargo.lock", "/tasks/*/plain/", "/tasks/*/guided/",
                      "/pilot/*/plain/", "/pilot/*/guided/", "/live/arms.local.json",
                      "/diag-probe/*.rlib", "/diag-probe/*.rmeta", "/diag-probe/*.pdb"):
            with self.subTest(entry=entry):
                self.assertIn(entry, lines)

    def test_scripts_write_under_results(self):
        """The runner, the power simulation and the live driver default to `results/`."""
        self.assertEqual(runner.RESULTS, ROOT / "results")
        self.assertEqual(_load_script("power_sim.py").OUTPUT.parent, ROOT / "results")
        self.assertEqual(_load_script("live/drive_pilot.py").DEFAULT_OUT, ROOT / "results" / "pilot-live")


class LiveArms(unittest.TestCase):
    """The live driver takes model file locations from a config file and a models folder
    the user names; no machine's paths live in code (they did in the scratch version)."""

    def setUp(self):
        self.drive = _load_script("live/drive_pilot.py")
        self.dir = _tmpdir(self)

    def _config(self, gguf: str, **extra) -> Path:
        arm = {"tag": "m1", "label": "model-one", "gguf": gguf, "size": 10, "sha256": "0" * 64,
               "top_p": "0.8", "top_k": "20", "min_p": "0", "resume": False}
        arm.update(extra)
        path = self.dir / "arms.json"
        path.write_text(json.dumps({"ctx": 24576, "arms": [arm]}), encoding="utf-8")
        return path

    def test_relative_weights_resolve_against_models_dir(self):
        """A relative `gguf` is joined to the models folder."""
        models = self.dir / "models"
        arms = self.drive.load_arms(self._config("org/repo/m.gguf"), models)
        self.assertEqual(arms[0]["gguf_path"], models / "org" / "repo" / "m.gguf")

    def test_absolute_weights_are_kept(self):
        """An absolute `gguf` (allowed in a local, git-ignored arms.local.json) is used as is."""
        target = (self.dir / "elsewhere" / "m.gguf").resolve()
        arms = self.drive.load_arms(self._config(str(target)), None)
        self.assertEqual(arms[0]["gguf_path"], target)

    def test_relative_weights_without_models_dir_name_the_fix(self):
        """Without a models folder the error names both ways to give one."""
        with self.assertRaises(ValueError) as cm:
            self.drive.load_arms(self._config("org/repo/m.gguf"), None)
        self.assertIn("--models-dir", str(cm.exception))
        self.assertIn("RWM_MODELS_DIR", str(cm.exception))

    def test_missing_field_is_named(self):
        """An arm without a required field is refused with the field's name."""
        path = self._config("m.gguf")
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["arms"][0]["sha256"]
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError) as cm:
            self.drive.load_arms(path, self.dir)
        self.assertIn("sha256", str(cm.exception))

    def test_committed_config_is_the_pilot(self):
        """live/arms.json holds the pilot's three arms: the model labels recorded in the run
        headers, relative weight paths, and a size and SHA-256 pin for every file."""
        arms = self.drive.load_arms(ROOT / "live" / "arms.json", self.dir)
        self.assertEqual([a["label"] for a in arms],
                         ["qwen3.5-4b-q4km", "gemma-4-e4b-it-qat-ud-q4kxl", "granite-4.1-3b-q4km"])
        for a in arms:
            with self.subTest(arm=a["tag"]):
                self.assertFalse(Path(a["gguf"]).is_absolute())
                self.assertGreater(a["size"], 0)
                self.assertRegex(a["sha256"], r"^[0-9a-f]{64}$")


class AnalysisPaths(unittest.TestCase):
    """The analysis scripts moved out of the results folder. They must read the per-round
    feedback and code that `runner.py run --save-dir <results dir>/code` saved next to the
    results file they are given, not next to the script."""

    RID = "r1"

    def setUp(self):
        self.dir = _tmpdir(self)
        base = {"run_id": self.RID, "task": "T01", "variant": "plain", "sample": 0, "gen": {}}
        rows = [{"kind": "run", "model": "m", "run_id": self.RID, "rounds": 1},
                dict(base, kind="round", round=0, compile_ok=False, failure_mode="compile"),
                dict(base, kind="round", round=1, compile_ok=True, failure_mode="none"),
                {"kind": "episode", "task": "T01", "variant": "plain", "sample": 0}]
        self.results = self.dir / "m.jsonl"
        self.results.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        code = self.dir / "code" / self.RID
        code.mkdir(parents=True)
        (code / "T01_plain_s0_R0.feedback.txt").write_text(
            "error[E0618]: expected function, found `Refusal`\n", encoding="utf-8")
        (code / "T01_plain_s0_R0.rs").write_text("Err(Refusal::OutOfMap(label))\n", encoding="utf-8")

    def _run(self, script: str) -> dict:
        out = self.dir / f"{Path(script).stem}.json"
        module = _load_script(script)
        with mock.patch.object(sys, "argv", [script, str(out), str(self.results)]), \
                contextlib.redirect_stdout(io.StringIO()):
            module.main()
        return json.loads(out.read_text(encoding="utf-8"))

    def test_transition_rates_reads_feedback_next_to_results(self):
        """The R0 hint-less E0618 disappears at R1 and R1 compiles: 1/1 for both counters."""
        report = self._run("analysis/transition_rates.py")["m"]
        self.assertEqual(report["plain/E0618-Refusal"], "1/1")
        self.assertEqual(report["plain/any-compile-fail"], "1/1")

    def test_fix_rates_reads_feedback_next_to_results(self):
        """The per-block counter finds the same block."""
        self.assertEqual(self._run("analysis/fix_rates.py")["m"], {"plain/E0618-Refusal": "1/1"})

    def test_refusal_payload_reads_code_next_to_results(self):
        """The payload scan finds the unit-variant call in the saved code."""
        plain = self._run("analysis/refusal_payload.py")["m"]["plain"]
        self.assertEqual((plain["episodes_payload"], plain["rounds_only_refusal_e0618"]), (1, 1))


class TimeSplit(unittest.TestCase):
    """analysis/time_split.py (the generation vs build vs test split in doc 64's revision)
    takes its results files on the command line instead of a scratch-folder constant."""

    def test_split_from_named_files(self):
        """Four synthetic rounds (two per arm), each 4.5 s generation and 0.5 s build, no
        tests; only PLAIN's repair round compiles."""
        d = _tmpdir(self)
        timings = {"prompt_ms": 3000, "predicted_ms": 1500, "prompt_n": 100,
                   "predicted_per_second": 20.0, "prompt_per_second": 500.0}
        rounds = [{"kind": "round", "run_id": "r", "ts": f"2026-09-28T10:00:{10 * n + i:02d}+00:00", "task": "T01",
                   "variant": v, "sample": 0, "round": i, "build_ms": 500, "test_ms": 0,
                   "format_ok": True, "compile_ok": v == "plain" and i == 1, "visible_pass": False,
                   "gen": {"gen_ms": 4500, "prompt_tokens": 1000, "completion_tokens": 300, "timings": timings}}
                  for n, v in enumerate(("plain", "guided")) for i in range(2)]
        episodes = [{"kind": "episode", "run_id": "r", "ts": f"2026-09-28T10:00:{10 * n + 5:02d}+00:00", "variant": v,
                     "per_R": {"R0": {"compile_ok": False}, "R1": {"compile_ok": v == "plain"}},
                     "final": {"hidden_pass": False, "compile_ok": v == "plain", "accepted_but_wrong": False},
                     "tokens": {"total": 2600}, "wall_ms": {"generation": 9000, "cargo": 1000}}
                    for n, v in enumerate(("plain", "guided"))]
        path = d / "m.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rounds + episodes), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _load_script("analysis/time_split.py").main([str(path)])
        text = buf.getvalue()
        self.assertIn("compiled 1/4", text)
        self.assertIn("compiled 1/2", text)
        self.assertIn("gen 90.000%  build 10.000%  tests 0.000%", text)


class Hygiene(unittest.TestCase):
    """This folder is public: no hidden characters (they can hide instructions or change
    how code reads) and no absolute local paths or user folders in any committed file.
    Test strings are assembled from code points and pieces, so this file passes its own scan."""

    def test_hidden_characters_are_reported_with_code_point(self):
        """Zero-width, bidi, byte-order-mark, tag, C0 control and soft-hyphen characters are each reported."""
        for cp in (0x200B, 0x202E, 0x2066, 0xFEFF, 0xE0041, 0x0007, 0x00AD, 0x2028):
            with self.subTest(cp=f"U+{cp:04X}"):
                problems = hygiene.text_problems("ok" + chr(cp) + "x\n")
                self.assertTrue(any(f"U+{cp:04X}" in p for p in problems), problems)

    def test_tabs_line_ends_and_ordinary_unicode_pass(self):
        """Tabs, CRLF and visible non-ASCII text (dashes, math signs, accents) are fine."""
        text = "a\tb\r\nc " + "".join(chr(c) for c in (0x2014, 0x2264, 0x00D7, 0x00FC, 0x00A7)) + "\n"
        self.assertEqual(hygiene.text_problems(text), [])

    def test_local_paths_are_reported(self):
        """A drive-letter path and absolute user-home folders are reported."""
        for text in ("see " + "C" + ":" + "\\" + "tools\\x", "at " + "/" + "home" + "/someone/x",
                     "at " + "/" + "Users" + "/someone/x", "under App" + "Data here"):
            with self.subTest(text=text):
                self.assertTrue(hygiene.text_problems(text))

    def test_relative_paths_and_urls_pass(self):
        """Relative paths, loopback URLs and Rust paths are not local paths."""
        text = "crates\\mb-guided\\src\\x.rs http://127.0.0.1:8080/v1 tasks/T01 std::fmt::Display"
        self.assertEqual(hygiene.text_problems(text), [])

    def test_this_folder_is_clean(self):
        """Every file that git would track here passes the scan."""
        problems = hygiene.scan_tree(ROOT)
        self.assertEqual(problems, [], "\n".join(problems))


@unittest.skipIf(hygiene.tomllib is None, "reading Cargo manifests needs tomllib (Python 3.11+)")
class EnclosingWorkspace(unittest.TestCase):
    """This is a standalone Cargo workspace inside the repository. Probed with cargo 1.98.1:
    a root workspace whose members glob matches this folder fails loudly ("multiple
    workspace roots"), but one whose members reach a crate inside it adopts that crate
    silently, with the root's lock file, profiles and lints. `exclude` filters globbed
    members; an explicit member path still wins. A root rust-toolchain file or
    .cargo/config would also change how the experiment compiles."""

    def _tree(self, root_manifest: str | None) -> tuple[Path, Path]:
        top = _tmpdir(self)
        (top / ".git").mkdir()
        harness = top / "tools" / "rw"
        (harness / "crates" / "a").mkdir(parents=True)
        (harness / "Cargo.toml").write_text('[workspace]\nmembers = ["crates/*"]\n', encoding="utf-8")
        if root_manifest is not None:
            (top / "Cargo.toml").write_text(root_manifest, encoding="utf-8")
        return top, harness

    def test_root_workspace_without_exclude_is_reported(self):
        """A root workspace that does not exclude the harness gets the fix in the message."""
        top, harness = self._tree('[workspace]\nmembers = ["crates/*"]\n')
        problems = hygiene.enclosing_workspace_problems(harness, top)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn('exclude = ["tools/rw"]', problems[0])

    def test_root_workspace_with_exclude_passes(self):
        """Excluding the harness folder (even under a glob that would reach it) passes."""
        top, harness = self._tree('[workspace]\nmembers = ["tools/*/*"]\nexclude = ["tools/rw"]\n')
        self.assertEqual(hygiene.enclosing_workspace_problems(harness, top), [])

    def test_explicit_member_inside_is_reported_despite_exclude(self):
        """An explicit member path into the harness overrides exclude, so it is reported."""
        top, harness = self._tree('[workspace]\nmembers = ["tools/rw/crates/a"]\nexclude = ["tools/rw"]\n')
        problems = hygiene.enclosing_workspace_problems(harness, top)
        self.assertTrue(any("tools/rw/crates/a" in p for p in problems), problems)

    def test_root_package_without_workspace_passes(self):
        """A root package that declares no workspace cannot adopt anything."""
        top, harness = self._tree('[package]\nname = "x"\nversion = "0.1.0"\n')
        self.assertEqual(hygiene.enclosing_workspace_problems(harness, top), [])

    def test_enclosing_toolchain_and_cargo_config_are_reported(self):
        """A toolchain pin or cargo config between the harness and the repository root is reported."""
        top, harness = self._tree(None)
        (top / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.99"\n', encoding="utf-8")
        (top / ".cargo").mkdir()
        (top / ".cargo" / "config.toml").write_text("[build]\n", encoding="utf-8")
        problems = hygiene.enclosing_config_problems(harness, top)
        self.assertEqual(len(problems), 2, problems)

    def test_this_harness_stands_alone(self):
        """The real manifest is a virtual workspace, and nothing up to the repository root
        adopts it or changes its toolchain or cargo configuration."""
        manifest = hygiene.tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))
        self.assertIn("workspace", manifest)
        self.assertNotIn("package", manifest)
        top = hygiene.repo_root(ROOT)
        if top is None:
            self.skipTest("not inside a git checkout")
        problems = hygiene.enclosing_workspace_problems(ROOT, top) + hygiene.enclosing_config_problems(ROOT, top)
        self.assertEqual(problems, [], "\n".join(problems))


# ── Guard tests (defined in test_rwm_guards.py) ───────────────────────────────

# Imported by name so that `python -m unittest test_rwm` collects them with this module's tests.
from test_rwm_guards import (  # noqa: E402,F401
    EndpointGuard,
    HygieneGuards,
    PromptPins,
    ScanBypasses,
    ServerCommand,
    ToolConfigs,
)

if __name__ == "__main__":
    unittest.main()
