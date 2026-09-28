"""Stand-in for run.py in the key-script tests: reports what the child process received, never the value itself.

Writes one JSON object to PROBE_OUT (a path; the child shares the console, so its stdout cannot be captured by the
PowerShell caller): the SHA-256 of the key variable's value and its length (the test compares the hash with the
dummy key's), whether the value appears in the command line, and the arguments. PROBE_MARKER (a path) is touched
so a test can tell whether the child ran at all; PROBE_EXIT sets the exit code.
"""
import hashlib
import json
import os
import sys

name = os.environ.get("PROBE_ENV_NAME", "OPENROUTER_API_KEY")
value = os.environ.get(name, "")
report = json.dumps({"sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(), "len": len(value),
                     "in_argv": bool(value) and any(value in a for a in sys.argv), "argv": sys.argv[1:]})
if os.environ.get("PROBE_OUT"):
    with open(os.environ["PROBE_OUT"], "w", encoding="utf-8") as f:
        f.write(report)
marker = os.environ.get("PROBE_MARKER")
if marker:
    with open(marker, "w", encoding="utf-8") as f:
        f.write("ran")
sys.exit(int(os.environ.get("PROBE_EXIT", "0")))
