"""Compile a task crate and run its test binaries, returning structured results.

Build: `cargo test -p <pkg> --no-run --offline --locked --message-format json`.
The JSON stream gives, per diagnostic, its level, error code and the human-rendered
text (fed back to the model), and, per test target, the path of the compiled test
executable. Tests then run by invoking those executables directly (not through
cargo), so a timeout kills exactly the process that hangs.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from .tasks import ROOT

FEEDBACK_LIMIT = 6000  # characters, cut on a diagnostic/test boundary (design.json)


@dataclass
class Diag:
    level: str  # error | warning
    code: str | None
    rendered: str
    in_solution: bool


@dataclass
class Build:
    ok: bool
    diags: list[Diag] = field(default_factory=list)
    exes: dict[str, str] = field(default_factory=dict)  # test target name -> path
    ms: int = 0
    timed_out: bool = False
    tail: str = ""  # stderr tail for infrastructure errors

    @property
    def codes(self) -> list[str]:
        return [d.code or d.level for d in self.diags if d.level == "error"]


@dataclass
class TestRun:
    results: dict[str, str] = field(default_factory=dict)  # name -> ok | FAILED | ignored | timeout
    output: dict[str, str] = field(default_factory=dict)  # name -> captured failure text
    ms: int = 0
    timed_out: bool = False
    exit_code: int | None = None

    @property
    def passed(self) -> list[str]:
        return [n for n, r in self.results.items() if r == "ok"]

    @property
    def failed(self) -> list[str]:
        return [n for n, r in self.results.items() if r != "ok" and r != "ignored"]

    @property
    def all_pass(self) -> bool:
        return bool(self.results) and not self.failed and not self.timed_out


def _env() -> dict:
    env = dict(os.environ)
    env["CARGO_TERM_COLOR"] = "never"
    env["RUST_BACKTRACE"] = "0"
    env.setdefault("CARGO_TARGET_DIR", str(ROOT / "target"))
    return env


def _kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def _run(cmd: list[str], cwd: Path, timeout: float, extra_env: dict | None = None) -> tuple[int | None, str, str, bool, int]:
    t0 = time.monotonic()
    env = _env()
    env.update(extra_env or {})
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        out, err = proc.communicate(timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        out, err = proc.communicate()
        timed_out = True
    ms = int((time.monotonic() - t0) * 1000)
    return proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), timed_out, ms


def _is_package(package_id: str, package: str) -> bool:
    """Matches cargo package ids old (`name 0.1.0 (path+...)`) and new
    (`path+file:///.../dir#name@0.1.0` or `.../name#0.1.0`) formats."""
    return (
        f"#{package}@" in package_id
        or package_id.startswith(f"{package} ")
        or re.search(rf"/{re.escape(package)}#[0-9]", package_id) is not None
    )


def build(package: str, timeout: float = 300.0) -> Build:
    cmd = ["cargo", "test", "-p", package, "--no-run", "--offline", "--locked", "--message-format", "json", "--color", "never"]
    code, out, err, timed_out, ms = _run(cmd, ROOT, timeout)
    b = Build(ok=False, ms=ms, timed_out=timed_out, tail=err[-3000:])
    finished_ok = False
    for line in out.splitlines():
        if not line.startswith("{"):
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        reason = msg.get("reason")
        if reason == "compiler-message":
            if not _is_package(msg.get("package_id", ""), package):
                continue  # diagnostics of dependencies are never the model's
            m = msg.get("message", {})
            level = m.get("level", "")
            if level not in ("error", "warning"):
                continue
            rendered = m.get("rendered") or m.get("message", "")
            if re.match(r"^(error|warning): .*(generated \d+ warning|aborting due to|could not compile)", rendered):
                continue
            spans = m.get("spans") or []
            in_solution = any(str(s.get("file_name", "")).replace("\\", "/").endswith("src/solution.rs") for s in spans)
            code_obj = m.get("code") or {}
            if any(d.rendered == rendered for d in b.diags):
                continue  # the same message from a second compilation of the same file
            b.diags.append(Diag(level, code_obj.get("code"), rendered, in_solution))
        elif reason == "compiler-artifact":
            target = msg.get("target", {})
            if msg.get("profile", {}).get("test") and "test" in target.get("kind", []) and msg.get("executable"):
                b.exes[target.get("name", "")] = msg["executable"]
        elif reason == "build-finished":
            finished_ok = bool(msg.get("success"))
    b.ok = finished_ok and code == 0 and not timed_out
    return b


_TEST_LINE = re.compile(r"^test (\S+) \.\.\. (ok|FAILED|ignored)")
_SECTION = re.compile(r"^---- (\S+) stdout ----$")


def parse_test_output(out: str) -> tuple[dict[str, str], dict[str, str]]:
    """Parses libtest's human output: per-test status lines (`test NAME ... ok`) and
    the captured output of failed tests (`---- NAME stdout ----` sections)."""
    results: dict[str, str] = {}
    output: dict[str, str] = {}
    lines = out.splitlines()
    for ln in lines:
        m = _TEST_LINE.match(ln)
        if m:
            results[m.group(1)] = m.group(2)
    current, buf = None, []
    for ln in lines:
        m = _SECTION.match(ln)
        if m:
            if current:
                output[current] = "\n".join(buf).strip()
            current, buf = m.group(1), []
        elif current and (ln.startswith("failures:") or ln.startswith("test result:")):
            output[current] = "\n".join(buf).strip()
            current, buf = None, []
        elif current:
            buf.append(ln)
    if current:
        output[current] = "\n".join(buf).strip()
    return results, output


def run_tests(exe: str, timeout: float = 20.0, extra_env: dict | None = None) -> TestRun:
    """Runs one libtest binary single-threaded with a wall-clock limit."""
    code, out, err, timed_out, ms = _run([exe, "--test-threads=1", "--color", "never"], ROOT, timeout, extra_env)
    tr = TestRun(ms=ms, timed_out=timed_out, exit_code=code)
    tr.results, tr.output = parse_test_output(out)
    if timed_out:
        # A test that started but never reported is the one that hung.
        started = re.findall(r"^test (\S+) \.\.\. ?$", out, flags=re.M)
        for name in started:
            tr.results.setdefault(name, "timeout")
        if not tr.results:
            tr.results["<binary>"] = "timeout"
    elif code not in (0, 101) and not tr.results:
        tr.results["<binary>"] = "crashed"
        tr.output["<binary>"] = (out + err)[-2000:]
    return tr


def list_tests(exe: str, timeout: float = 20.0) -> list[str]:
    """Names of the tests in a libtest binary (`--list`)."""
    code, out, _err, _t, _ms = _run([exe, "--list", "--format", "terse"], ROOT, timeout)
    return [ln.split(":")[0] for ln in out.splitlines() if ln.endswith(": test")]


def solution_panicked(output: str) -> bool:
    """True if the failure is a panic raised inside the solution (not a test assert)."""
    m = re.search(r"panicked at ([^\n:]+)", output)
    return bool(m) and m.group(1).replace("\\", "/").endswith("src/solution.rs")


# Both variants are presented to the model as crate `mb`; rendered diagnostics must not
# reveal which variant it is (blinding) nor the hidden core crate's name.
_CRATE_ALIASES = [
    (re.compile(r"crates[\\/]+mb-(plain|guided)[\\/]+src[\\/]+"), "mb/src/"),
    (re.compile(r"crates[\\/]+mb-spec[\\/]+src[\\/]+"), "mb_spec/src/"),
    (re.compile(r"\bmb_(plain|guided)::"), "mb::"),
    (re.compile(r"\bmb-(plain|guided)\b"), "mb"),
    (re.compile(r"\bmb_core::"), "mb::"),
]


def _normalise_paths(text: str, crate_dir: Path) -> str:
    for base in (str(crate_dir) + os.sep, str(crate_dir).replace("\\", "/") + "/"):
        text = text.replace(base, "")
    rel = crate_dir.relative_to(ROOT).as_posix()
    text = text.replace(rel.replace("/", "\\") + "\\", "").replace(rel + "/", "")
    for root in (str(ROOT) + os.sep, str(ROOT).replace("\\", "/") + "/"):
        text = text.replace(root, "")
    for pattern, repl in _CRATE_ALIASES:
        text = pattern.sub(repl, text)
    return text.replace("src\\solution.rs", "src/solution.rs")


def _cut(blocks: list[str], limit: int) -> str:
    out, used = [], 0
    for b in blocks:
        if used + len(b) > limit:
            out.append(f"[{len(blocks) - len(out)} more message(s) omitted]")
            break
        out.append(b)
        used += len(b) + 1
    return "\n".join(out)


def compile_feedback(b: Build, crate_dir: Path, limit: int = FEEDBACK_LIMIT) -> str:
    """Rendered diagnostics, errors first, then warnings, cut on a message boundary."""
    errors = [d.rendered.rstrip() for d in b.diags if d.level == "error"]
    warnings = [d.rendered.rstrip() for d in b.diags if d.level == "warning"]
    blocks = [_normalise_paths(x, crate_dir) for x in errors + warnings]
    if not blocks:
        blocks = ["The build failed without compiler diagnostics:\n" + _normalise_paths(b.tail[-1500:], crate_dir)]
    return _cut(blocks, limit)


def test_feedback(tr: TestRun, crate_dir: Path, limit: int = FEEDBACK_LIMIT) -> str:
    """Visible-test failures: names and captured panic output (assert left/right)."""
    blocks = []
    for name in tr.failed:
        detail = tr.output.get(name, "").strip() or tr.results.get(name, "failed")
        blocks.append(f"test {name} failed:\n{_normalise_paths(detail, crate_dir)}")
    if tr.timed_out:
        blocks.append("The visible tests did not finish within the time limit.")
    passed = ", ".join(tr.passed) or "none"
    return _cut(blocks, limit - 200) + f"\n(passed: {passed})"
