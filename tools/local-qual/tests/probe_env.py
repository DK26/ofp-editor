"""Stand-in for run.py in the key-script tests: reports what the child process received, never the value itself.

Writes one JSON object to PROBE_OUT (a path; the child shares the console, so its stdout cannot be captured by the
PowerShell caller): the SHA-256 of the key variable's value and its length (the test compares the hash with the
dummy key's), whether the value appears in the command line, and the arguments. PROBE_ENV_NAME names the key variable
(default OPENROUTER_API_KEY); PROBE_ENV_EXTRA names more variables (comma-separated, for example the Cloudflare account
id's), each reported the same way under "extra" (a missing one as null); PROBE_ENV_ABSENT names variables whose
presence alone is reported under "present" (the launcher gives the child one provider's key only). PROBE_MARKER (a
path) is touched so a test can tell whether the child ran at all; PROBE_EXIT sets the exit code.
"""
import hashlib
import json
import os
import sys


def digest(value):
    """What the report says of one variable's value: its SHA-256, its length, and whether argv holds it."""
    return {"sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(), "len": len(value),
            "in_argv": bool(value) and any(value in a for a in sys.argv)}


name = os.environ.get("PROBE_ENV_NAME", "OPENROUTER_API_KEY")
value = os.environ.get(name, "")
extra = {n: (digest(os.environ[n]) if n in os.environ else None)
         for n in os.environ.get("PROBE_ENV_EXTRA", "").split(",") if n}
present = {n: n in os.environ for n in os.environ.get("PROBE_ENV_ABSENT", "").split(",") if n}
report = json.dumps(dict(digest(value), argv=sys.argv[1:], extra=extra, present=present))
if os.environ.get("PROBE_OUT"):
    with open(os.environ["PROBE_OUT"], "w", encoding="utf-8") as f:
        f.write(report)
marker = os.environ.get("PROBE_MARKER")
if marker:
    with open(marker, "w", encoding="utf-8") as f:
        f.write("ran")
sys.exit(int(os.environ.get("PROBE_EXIT", "0")))
