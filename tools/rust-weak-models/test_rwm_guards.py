"""Guard tests for the harness: the pre-compile scan, the model endpoint, the pinned prompts,
the pinned tool configs, the hygiene check and the live driver's server command.

These guard the experiment's integrity and the machine that runs it (standard library
`unittest`; no cargo, no model). `test_rwm.py` imports every class here, so
`python -m unittest test_rwm` stays the one command that runs all harness tests; this file
also runs on its own (`python -m unittest test_rwm_guards`). It also holds the helpers both
files share (`_tmpdir`, `_load_script`).

Test strings that would trip the hygiene scan (key-like tokens, local paths) are assembled
from pieces, so this file passes its own scan.
"""
from __future__ import annotations

import hashlib
import http.server
import importlib.util
import json
import os
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from rwm import hygiene, llm, prompt, scan, tasks
from rwm.tasks import ROOT

# ── Shared helpers ────────────────────────────────────────────────────────────


def _tmpdir(case: unittest.TestCase) -> Path:
    """A fresh temporary folder that is removed when the test ends (`addCleanup`), so a test
    run leaves nothing behind in the system temp folder."""
    td = tempfile.TemporaryDirectory()
    case.addCleanup(td.cleanup)
    return Path(td.name)


def _load_script(rel: str):
    """Imports a script that is not part of the `rwm` package (`live/`, `analysis/`,
    `power_sim.py`) from its path, so its functions can be tested without running its
    command line. Loading only defines names; every script keeps its work in `main()`."""
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(f"rwm_script_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Pre-compile scan: path bypasses and the allow-list ───────────────────────


class ScanBypasses(unittest.TestCase):
    """The scan runs before model-written code is compiled and its tests executed. Forms that
    reach a forbidden module without spelling `std::<module>` directly must be rejected too:
    grouped imports, crate-root aliases, glob imports, raw identifiers and paths built from
    macro variables. Only listed standard-library modules may be named. The pilot's 768 saved
    solutions contain none of these forms, so their verdicts do not change (checked when the
    scan changed; doc 64, review pass)."""

    OK = "pub fn solve(input: &I) -> R { todo!() }\n"

    def test_rejects_path_bypasses(self):
        """Each bypass form found in review is rejected."""
        bad = {
            "grouped import": "use std::{process::Command, fs};\n",
            "nested group": "use std::{io::{self, Read}, net::TcpStream};\n",
            "crate alias": 'use std as s;\nfn a() { let _ = s::fs::read("x"); }\n',
            "public alias with leading colons": "pub use ::core as c;\n",
            "self alias in a group": "use std::{self as q};\n",
            "glob import of the crate root": "use std::*;\n",
            "raw identifier segment": 'fn a() { let _ = std::r#fs::read("x"); }\n',
            "raw identifier root": 'fn a() { let _ = r#std::fs::read("x"); }\n',
            "macro variable after std": 'macro_rules! m { ($a:ident) => { std::$a::read("x") } }\n',
            "macro variable as root": 'macro_rules! m { ($r:ident) => { $r::fs::read("x") } }\n',
            "module not on the list": 'fn a() { let _ = std::path::Path::new("x").exists(); }\n',
            "threads": "fn a() { std::thread::spawn(|| {}); }\n",
        }
        for label, code in bad.items():
            with self.subTest(label=label):
                self.assertIsNotNone(scan.static_scan(self.OK + code), code)

    def test_accepts_allowed_std_forms(self):
        """Data-only modules pass, grouped or not, including the forms the pilot's models wrote."""
        good = [
            "use std::collections::HashMap;\n",
            "use std::{collections::HashMap, fmt};\n",
            "use std::collections::{BTreeMap, HashSet};\n",
            "use std::{collections::{HashMap, HashSet}, fmt::Write};\n",
            "use core::cmp::Ordering;\n",
            "fn a() -> f64 { std::f64::consts::PI }\n",
            "fn a(x: &mut u32, y: &mut u32) { std::mem::swap(x, y); }\n",
            'fn a() -> String { std::format!("{}", 1) }\n',
            "use std::convert::TryFrom;\nuse std::error::Error;\nuse std::result::Result as R2;\n",
            "use std::fmt::{self, Write};\n",
        ]
        for code in good:
            with self.subTest(code=code):
                self.assertIsNone(scan.static_scan(self.OK + code))

    def test_raw_byte_strings_are_blanked(self):
        """A byte raw string's content is data, like any string literal's."""
        code = self.OK + 'const B: &[u8] = br#"std::fs::read and use std as s"#;\n'
        self.assertIsNone(scan.static_scan(code))

    def test_every_reference_solution_passes(self):
        """No reference solution (34 tasks, both variants) is rejected by the stricter scan."""
        for t in tasks.discover(quiet=True):
            for v in ("plain", "guided"):
                with self.subTest(task=t.id, variant=v):
                    self.assertIsNone(scan.static_scan(t.reference(v)))


# ── Model endpoint: loopback by default, no key fallback, no redirects ────────


class _Target(http.server.BaseHTTPRequestHandler):
    """Records every request it receives; answers with an empty chat completion."""

    seen: list = []

    def _answer(self):
        type(self).seen.append((self.command, dict(self.headers)))
        body = json.dumps({"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = _answer

    def log_message(self, *args):  # keep the test output clean
        pass


class EndpointGuard(unittest.TestCase):
    """The runner sends prompts and, when set, a bearer token to `--base-url`. Only loopback
    endpoints are allowed by default; a remote one needs `--allow-remote-endpoint` and https;
    only `RWM_API_KEY` is read (a general `OPENAI_API_KEY` must not leak to a local test
    server); and redirects are never followed, because urllib re-sends added headers,
    the Authorization header included, to the redirect target."""

    def test_loopback_endpoints_are_accepted(self):
        """IPv4 loopback, `localhost` and IPv6 loopback need no flag."""
        for url in ("http://127.0.0.1:8080/v1", "http://localhost:8080/v1", "http://[::1]:8080/v1",
                    "http://127.0.0.2:9/v1"):
            with self.subTest(url=url):
                llm.OpenAIClient(url, "m")

    def test_remote_endpoint_needs_the_flag_and_https(self):
        """A remote host is refused without the flag (the message names it and the guarded
        route), refused over http even with it, and accepted over https with it."""
        with self.assertRaises(ValueError) as cm:
            llm.OpenAIClient("https://api.example.com/v1", "m")
        self.assertIn("--allow-remote-endpoint", str(cm.exception))
        self.assertIn("tools/local-qual", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            llm.OpenAIClient("http://api.example.com/v1", "m", allow_remote=True)
        self.assertIn("https", str(cm.exception))
        llm.OpenAIClient("https://api.example.com/v1", "m", allow_remote=True)

    def test_malformed_urls_are_refused(self):
        """Other schemes and URLs without a host are refused."""
        for url in ("ftp://127.0.0.1/v1", "127.0.0.1:8080/v1", "http:///v1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                llm.OpenAIClient(url, "m")

    def test_only_rwm_api_key_is_read(self):
        """OPENAI_API_KEY is ignored; RWM_API_KEY is used."""
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "general-key"}):
            os.environ.pop("RWM_API_KEY", None)
            self.assertIsNone(llm.OpenAIClient("http://127.0.0.1:1/v1", "m").api_key)
            os.environ["RWM_API_KEY"] = "harness-key"
            self.assertEqual(llm.OpenAIClient("http://127.0.0.1:1/v1", "m").api_key, "harness-key")

    def _serve(self, handler) -> http.server.HTTPServer:
        srv = http.server.HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        return srv

    def test_redirect_is_not_followed(self):
        """A 302 from the endpoint becomes an infrastructure error, and the redirect target
        receives nothing, so the bearer token never reaches it.

        Two local servers: the endpoint answers every POST with a 302 to the recorder."""
        _Target.seen = []
        target = self._serve(_Target)
        location = f"http://127.0.0.1:{target.server_port}/stolen"

        class Redirector(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header("Location", location)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        endpoint = self._serve(Redirector)
        client = llm.OpenAIClient(f"http://127.0.0.1:{endpoint.server_port}/v1", "m", api_key="token-for-test")
        reply = client.chat([{"role": "user", "content": "x"}], llm.Sampler(), seed=1)
        self.assertIsNotNone(reply.error)
        self.assertIn("302", reply.error)
        self.assertEqual(_Target.seen, [])

    def test_no_redirect_handler_declines(self):
        """The handler itself returns no follow-up request for any redirect code."""
        req = urllib.request.Request("http://127.0.0.1:1/v1/chat/completions", data=b"{}", method="POST")
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                self.assertIsNone(llm._NoRedirect().redirect_request(req, None, code, "moved", {},
                                                                     "http://127.0.0.1:2/x"))

    def test_runner_refuses_a_remote_endpoint_before_any_call(self):
        """`runner.py run` exits 2 and names the flag; no request is made."""
        import contextlib
        import io

        import runner

        with mock.patch.object(tasks, "scaffold_missing", return_value=[]), \
                mock.patch.object(llm.OpenAIClient, "_post", side_effect=AssertionError("no request")), \
                contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            rc = runner.main(["run", "--base-url", "https://api.example.com/v1", "--model", "m", "--tasks", "pilot"])
        self.assertEqual(rc, 2)
        self.assertIn("--allow-remote-endpoint", out.getvalue() + err.getvalue())


# ── Pinned prompts and tool configs ───────────────────────────────────────────


class PromptPins(unittest.TestCase):
    """What a model sees must not change silently. `cargo fmt`, `cargo clippy --fix` or any
    edit of a stimulus crate, prompt file or task file changes the listings or prompts; these
    pins are the pilot's values (run headers of 2026-09-28; the local token estimate, equal
    budget), so such a change fails here and has to be recorded as an experiment change."""

    MESSAGE = ("experiment change: {what} no longer matches the pilot's; record it under Deviations in the README "
               "(and in design.json before freezing), re-run verify, conformance, mutants and listing, then update "
               "the pin")
    LISTING = {"plain": "8517087a5bd7af787df7b9a2a7885c4d72962ead229edf50a0eeaa7b39a5fa08",
               "guided": "d1e284bbdb3406d5c2282c1a1fa71de4557cb27175466a8082bc170b764042ff"}
    SYSTEM = {"plain": "c7ddb4e945ec468bb7e535010d3f695d1dd963f4eeba5028a3305b7b4c476500",
              "guided": "a4d9a1ed46e6c57a780f7363f1ff5445054420b5b04a345216e07e89b25bdb06"}
    # SHA-256 of the lines "<task id> <SHA-256 of its user prompt>" for all 34 tasks, sorted by id.
    USER_PROMPTS = "33c6696067538df2a8ab803804875c306d92b650cb9d7b280c95530209669154"

    def test_listings_match_the_pilot(self):
        """Both API listings are byte-identical to the pilot's."""
        for v, pin in self.LISTING.items():
            with self.subTest(variant=v):
                self.assertEqual(_sha(prompt.api_listing(v)), pin, self.MESSAGE.format(what=f"the {v} listing"))

    def test_system_prompts_match_the_pilot(self):
        """Both balanced system prompts are byte-identical to the pilot's."""
        sp = prompt.build_system_prompts("equal")
        for v, pin in self.SYSTEM.items():
            with self.subTest(variant=v):
                self.assertEqual(sp.sha256(v), pin, self.MESSAGE.format(what=f"the {v} system prompt"))

    def test_user_prompts_match_the_pilot(self):
        """All 34 user prompts are byte-identical to the pilot's."""
        found = sorted(tasks.discover(quiet=True), key=lambda t: t.id)
        self.assertEqual(len(found), 34)
        lines = "".join(f"{t.id} {_sha(prompt.user_prompt(t))}\n" for t in found)
        self.assertEqual(_sha(lines), self.USER_PROMPTS, self.MESSAGE.format(what="a user prompt"))


class ToolConfigs(unittest.TestCase):
    """clippy and rustfmt read the nearest `clippy.toml` / `rustfmt.toml` above a crate and
    never merge files, so this folder pins its own: rustfmt with every rule off (formatting
    would rewrite the stimuli) and an empty clippy.toml (so a repository-root table cannot
    reach the experiment)."""

    def test_rustfmt_is_disabled_here(self):
        """rustfmt.toml exists and turns all formatting off."""
        text = (ROOT / "rustfmt.toml").read_text(encoding="utf-8")
        self.assertIn("disable_all_formatting = true", text.splitlines())

    def test_clippy_config_is_pinned_and_empty(self):
        """clippy.toml exists and sets no key (comments only) until a lint arm needs one."""
        lines = (ROOT / "clippy.toml").read_text(encoding="utf-8").splitlines()
        self.assertEqual([ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")], [])


# ── Hygiene: keys, bare CR, private-name denylist, enclosing tool configs ─────


class HygieneGuards(unittest.TestCase):
    """The hygiene check claims to catch what a public folder must not hold. It reports
    key-like tokens, a CR without LF, terms from an optional local denylist, and any
    `clippy.toml` or `rustfmt.toml` above the folder that this folder does not shadow."""

    def test_key_like_strings_are_reported(self):
        """Common API-key and private-key shapes are reported."""
        samples = ["s" + "k-" + "Ab3d" * 6, "h" + "f_" + "Q1w2E3r4" * 4, "gh" + "p_" + "Z9y8" * 9,
                   "AK" + "IA" + "ABCDEFGHIJKLMNOP", "-----BEGIN " + "RSA PRIVATE KEY-----",
                   "Authorization: Bear" + "er " + "abcdEFGH1234ijklMNOP5678"]
        for text in samples:
            with self.subTest(text=text[:6]):
                self.assertTrue(any("key-like" in p for p in hygiene.text_problems("x " + text + "\n")))

    def test_ordinary_hex_and_code_pass(self):
        """SHA-256 pins, format strings and the word bearer in prose are not keys."""
        text = 'sha256 "' + "0f" * 32 + '" f"Bearer {self.api_key}" a bearer token\n'
        self.assertEqual(hygiene.text_problems(text), [])

    def test_bare_carriage_return_is_reported(self):
        """A CR not followed by LF is reported with its line; CRLF is fine."""
        problems = hygiene.text_problems("a\r\nb\rc\n")
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("line 2", problems[0])

    def test_denylist_terms_are_reported_without_echoing_them(self):
        """A term from the local denylist is reported by entry number, case-insensitively."""
        problems = hygiene.text_problems("mentions Zyxwvu here\n", deny=["alpha", "zyxwvu"])
        self.assertEqual(problems, ["line 1: denylisted term (entry 2)"])

    def test_denylist_is_read_from_the_named_file(self):
        """RWM_HYGIENE_DENYLIST names a file outside the repository: one term per line,
        blank lines and # comments ignored; without the variable the list is empty."""
        path = _tmpdir(self) / "deny.txt"
        path.write_text("# local only\nalpha\n\nZyxwvu\n", encoding="utf-8")
        self.assertEqual(hygiene.load_denylist({"RWM_HYGIENE_DENYLIST": str(path)}), ["alpha", "zyxwvu"])
        self.assertEqual(hygiene.load_denylist({}), [])

    def _tree(self) -> tuple[Path, Path]:
        top = _tmpdir(self)
        (top / ".git").mkdir()
        harness = top / "tools" / "rw"
        harness.mkdir(parents=True)
        (top / "clippy.toml").write_text("disallowed-methods = []\n", encoding="utf-8")
        (top / "tools" / ".rustfmt.toml").write_text("max_width = 80\n", encoding="utf-8")
        return top, harness

    def test_enclosing_tool_configs_are_reported_unless_shadowed(self):
        """Without its own files the harness would inherit both configs, so both are
        reported; once it pins clippy.toml and rustfmt.toml they are shadowed."""
        top, harness = self._tree()
        problems = hygiene.enclosing_config_problems(harness, top)
        self.assertEqual(len(problems), 2, problems)
        self.assertTrue(any("clippy.toml" in p for p in problems) and any("rustfmt.toml" in p for p in problems))
        (harness / "clippy.toml").write_text("", encoding="utf-8")
        (harness / "rustfmt.toml").write_text("disable_all_formatting = true\n", encoding="utf-8")
        self.assertEqual(hygiene.enclosing_config_problems(harness, top), [])


# ── Live driver: server command ───────────────────────────────────────────────


class ServerCommand(unittest.TestCase):
    """The driver starts llama-server through PowerShell. Paths, the tag and the server name
    come from an arms file and the command line, so none of them may be pasted into the
    `-Command` text, where a quote would end the string and the rest would run as code."""

    def test_values_travel_in_the_environment_not_the_command(self):
        """Every caller-supplied value is absent from the command text and present in the
        environment the command reads."""
        drive = _load_script("live/drive_pilot.py")
        gguf = Path("models") / "it's; Remove-Item x" / "m.gguf"
        cmd, env = drive.start_server_command("t'1", gguf, 24576, "llama'server", Path("logs") / "o'k")
        text = cmd[-1]
        for value in ("it's", "t'1", "llama'server", "o'k", "Remove-Item x"):
            with self.subTest(value=value):
                self.assertNotIn(value, text)
        self.assertEqual(env["RWM_START_GGUF"], str(gguf))
        self.assertEqual(env["RWM_START_NAME"], "rwm-t'1")
        self.assertEqual(env["RWM_START_SERVER"], "llama'server")
        self.assertIn("-Ctx 24576", text)

    def test_manual_default_context_is_the_pilots(self):
        """start-server.ps1 run by hand defaults to the pilot's context, 24,576 tokens."""
        text = (ROOT / "live" / "start-server.ps1").read_text(encoding="utf-8")
        self.assertIn("[int]$Ctx = 24576", text)


if __name__ == "__main__":
    unittest.main()
