"""Task discovery and scaffolding of the per-(task, variant) test crates.

A task folder (`tasks/Tnn/` or `pilot/Pnn/`) holds hand-written sources:

    task.json      id, title, tier, spec_module, traps, refusals, friction, scored
    task.md        task text shown to the model (identical for both variants)
    visible.rs     visible tests (shown in the prompt, used in the feedback loop)
    hidden.rs      hidden tests (never shown); names start with nominal_, trap_<cat>_,
                   refusal_ or edge_
    ref_plain.rs   reference solution against the PLAIN API
    ref_guided.rs  reference solution against the GUIDED API
    mutants.json   optional trap mutants: find/replace edits of the references

`scaffold()` generates, for each variant, a crate `<task>/<variant>/` whose library
is named `task`: `src/lib.rs` (fixed; includes `src/solution.rs`), `tests/visible.rs`
and `tests/hidden.rs` (each an `include!` of the shared test file) and a Cargo.toml
that renames the variant crate to `mb`, so both variants look identical from the
solution's side. The model writes only `src/solution.rs`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = ("plain", "guided")

# Trap categories (design.json trap_taxonomy) and their test-name slugs.
TRAP_SLUGS = {
    "seq_cycle": "SEQ-CYCLE",
    "seq_hold": "SEQ-HOLD",
    "seq_mount": "SEQ-MOUNT",
    "seq_export": "SEQ-EXPORT",
    "id_mix": "ID-MIX",
    "unit_measure": "UNIT-MEASURE",
    "ref_sync": "REF-SYNC",
    "ref_vehicle": "REF-VEHICLE",
    "empty_group": "EMPTY-GROUP",
    "act_rule": "ACT-RULE",
    "timer_order": "TIMER-ORDER",
    "bounds": "BOUNDS",
    "err_handling": "ERR-HANDLING",
}
TRAP_CLASS = {
    "SEQ-CYCLE": "S", "SEQ-HOLD": "S", "SEQ-MOUNT": "S", "SEQ-EXPORT": "S", "ID-MIX": "S",
    "UNIT-MEASURE": "S/F", "REF-SYNC": "F", "REF-VEHICLE": "F", "EMPTY-GROUP": "F", "ACT-RULE": "S/F",
    "TIMER-ORDER": "R", "BOUNDS": "R", "ERR-HANDLING": "R",
}


def trap_category(test_name: str) -> str | None:
    """`trap_seq_cycle_after_loop` -> `SEQ-CYCLE`; None for non-trap tests."""
    if not test_name.startswith("trap_"):
        return None
    rest = test_name[len("trap_"):]
    for slug in sorted(TRAP_SLUGS, key=len, reverse=True):
        if rest.startswith(slug):
            return TRAP_SLUGS[slug]
    return "UNKNOWN"


@dataclass
class Task:
    id: str
    dir: Path
    meta: dict = field(default_factory=dict)

    @property
    def module(self) -> str:
        return self.meta["spec_module"]

    @property
    def scored(self) -> bool:
        return bool(self.meta.get("scored", False))

    def crate_dir(self, variant: str) -> Path:
        return self.dir / variant

    def package(self, variant: str) -> str:
        return f"{self.id.lower()}-{variant}"

    def reference(self, variant: str) -> str:
        return (self.dir / f"ref_{variant}.rs").read_text(encoding="utf-8")

    def text(self, name: str) -> str:
        return (self.dir / name).read_text(encoding="utf-8")

    def spec_source(self) -> str:
        return (ROOT / "crates" / "mb-spec" / "src" / f"{self.module}.rs").read_text(encoding="utf-8")

    def mutants(self, variant: str) -> list[dict]:
        """Trap mutants for this variant: the reference solution with the find/replace
        edits of `mutants.json` applied. Each mutant makes one realistic mistake; the
        PLAIN and GUIDED versions make the same mistake in each API's own terms.

        Returns dicts with name, category, note and code."""
        spec = self.dir / "mutants.json"
        if not spec.is_file():
            return []
        out = []
        for m in json.loads(spec.read_text(encoding="utf-8")):
            edits = m.get(variant)
            if not edits:
                continue
            code = self.reference(variant)
            for find, repl in edits:
                if find not in code:
                    raise SystemExit(f"{self.id} mutant {m['name']} ({variant}): pattern not found: {find!r}")
                code = code.replace(find, repl, 1)
            out.append({"name": m["name"], "category": m["category"], "note": m.get("note", ""), "code": code})
        return out


REQUIRED_FILES = ("task.json", "task.md", "visible.rs", "hidden.rs", "ref_plain.rs", "ref_guided.rs")


def discover(root: Path = ROOT, quiet: bool = False) -> list[Task]:
    """Complete task folders (every required file present), pilots first."""
    tasks = []
    for base in ("pilot", "tasks"):
        for d in sorted((root / base).glob("*")):
            if not (d / "task.json").is_file():
                continue
            missing = [f for f in REQUIRED_FILES if not (d / f).is_file()]
            if missing:
                if not quiet:
                    print(f"note: {d.name} skipped (missing {', '.join(missing)})", file=sys.stderr)
                continue
            meta = json.loads((d / "task.json").read_text(encoding="utf-8"))
            tasks.append(Task(meta["id"], d, meta))
    return tasks


def select(tasks: list[Task], spec: str) -> list[Task]:
    """`all`, `pilot`, `scored`, or a comma list of ids (`T01,T02`)."""
    if spec == "all":
        return tasks
    if spec == "pilot":
        return [t for t in tasks if not t.scored]
    if spec == "scored":
        return [t for t in tasks if t.scored]
    wanted = [s.strip().upper() for s in spec.split(",") if s.strip()]
    by_id = {t.id: t for t in tasks}
    missing = [w for w in wanted if w not in by_id]
    if missing:
        raise SystemExit(f"unknown task id(s): {', '.join(missing)}")
    return [by_id[w] for w in wanted]


# ── Scaffold ──────────────────────────────────────────────────────────────────

CARGO_TOML = """# Generated by `python runner.py scaffold`; do not edit.
[package]
name = "{package}"
version.workspace = true
edition.workspace = true
rust-version.workspace = true
license.workspace = true
publish.workspace = true

[lib]
name = "task"
path = "src/lib.rs"
# The solution is compiled once, for the integration tests only (no lib unit-test
# target, no doctests): halves build time and avoids duplicate diagnostics.
test = false
doctest = false

[dependencies]
mb = {{ package = "mb-{variant}", path = "../../../crates/mb-{variant}" }}
mb-spec = {{ path = "../../../crates/mb-spec" }}

[dev-dependencies]
mb-oracle = {{ path = "../../../crates/mb-oracle" }}

[[test]]
name = "visible"
path = "tests/visible.rs"

[[test]]
name = "hidden"
path = "tests/hidden.rs"
"""

LIB_RS = """//! Generated by `python runner.py scaffold`; do not edit. The model writes only
//! `src/solution.rs`; this file fixes the entry point and forbids `unsafe`.
#![forbid(unsafe_code)]

pub mod solution;

/// The entry point must have exactly this signature.
const _ENTRY: fn(&mb_spec::{module}::Input) -> Result<mb::Exported, mb_spec::Refusal> = solution::solve;

/// Runs the solution and returns the export text (what the tests inspect).
pub fn run(input: &mb_spec::{module}::Input) -> Result<String, mb_spec::Refusal> {{
    let out = solution::solve(input).map(|exported| exported.text().to_owned());
    conformance_dump(&out);
    out
}}

/// Harness hook for `runner.py conformance`: when `RWM_DUMP_DIR` is set, appends each
/// result to a file named after the running test (libtest names each test thread), so
/// the PLAIN and GUIDED reference outputs can be compared byte for byte. Inactive in
/// model runs (the variable is never set there).
fn conformance_dump(out: &Result<String, mb_spec::Refusal>) {{
    use std::io::Write as _;
    let Ok(dir) = std::env::var("RWM_DUMP_DIR") else {{ return }};
    let name = std::thread::current().name().unwrap_or("main").replace("::", "_");
    let text = match out {{
        Ok(t) => t.clone(),
        Err(r) => format!("REFUSAL {{r:?}}\n"),
    }};
    let path = std::path::Path::new(&dir).join(format!("{{name}}.txt"));
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(path) {{
        let _ = write!(f, "{{text}}----\n");
    }}
}}
"""

TEST_RS = """// Generated by `python runner.py scaffold`; do not edit.
include!("../../{name}.rs");
"""


def _write_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def scaffold(tasks: list[Task], root: Path = ROOT) -> list[str]:
    """Writes every task crate, installs the reference solutions and rewrites the
    workspace member list. Returns the member paths."""
    members = []
    spec_lib = (root / "crates" / "mb-spec" / "src" / "lib.rs").read_text(encoding="utf-8")
    for t in tasks:
        if not re.search(rf"\bpub mod {t.module};", spec_lib):
            raise SystemExit(f"{t.id}: mb-spec/src/lib.rs does not declare `pub mod {t.module};`")
        for v in VARIANTS:
            c = t.crate_dir(v)
            _write_if_changed(c / "Cargo.toml", CARGO_TOML.format(package=t.package(v), variant=v))
            _write_if_changed(c / "src" / "lib.rs", LIB_RS.format(module=t.module))
            _write_if_changed(c / "tests" / "visible.rs", TEST_RS.format(name="visible"))
            _write_if_changed(c / "tests" / "hidden.rs", TEST_RS.format(name="hidden"))
            _write_if_changed(c / "src" / "solution.rs", t.reference(v))
            members.append(c.relative_to(root).as_posix())
    ws = root / "Cargo.toml"
    text = ws.read_text(encoding="utf-8")
    block = "".join(f'    "{m}",\n' for m in members)
    new = re.sub(
        r"(    # BEGIN scaffold members\n).*?(    # END scaffold members)",
        lambda m: m.group(1) + block + m.group(2),
        text,
        flags=re.S,
    )
    _write_if_changed(ws, new)
    # No external dependencies: generating the lock file never touches the network.
    subprocess.run(["cargo", "generate-lockfile", "--offline"], cwd=root, check=True, capture_output=True)
    return members


def scaffold_missing(tasks: list[Task], root: Path = ROOT) -> list[str]:
    """Files that `scaffold()` generates and that are absent, as paths relative to `root`:
    each task crate's Cargo.toml (both variants), then Cargo.lock.

    Why: the generated crates and the lock file are git-ignored, so a fresh clone has
    none of them. Without this check `verify` fails writing `src/solution.rs` into a
    folder that does not exist, and cargo fails loading the workspace member list; both
    errors hide the one command that fixes them. Every task is checked, not only the
    selected ones, because the workspace manifest names all of them as members."""
    missing = [f"{t.crate_dir(v).relative_to(root).as_posix()}/Cargo.toml"
               for t in tasks for v in VARIANTS if not (t.crate_dir(v) / "Cargo.toml").is_file()]
    if not (root / "Cargo.lock").is_file():
        missing.append("Cargo.lock")
    return missing


def install_solution(task: Task, variant: str, code: str) -> Path:
    path = task.crate_dir(variant) / "src" / "solution.rs"
    path.write_text(code, encoding="utf-8", newline="\n")
    return path


def restore_reference(task: Task, variant: str) -> None:
    install_solution(task, variant, task.reference(variant))
