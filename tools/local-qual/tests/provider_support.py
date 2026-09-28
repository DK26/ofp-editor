#!/usr/bin/env python3
"""Shared fixtures of the Groq and Cloudflare Workers AI tests (test_provider_*.py; ``run.py --provider``).

What it owns
------------
* The dummy secrets, random per process and never real: ``GROQ_KEY`` (``gsk_`` and 52 letters and digits, the shape
  secret scanners use for Groq keys), ``CF_TOKEN`` and ``CF_USER_TOKEN`` (Cloudflare's ``cfat_`` account-token and
  ``cfut_`` user-token prefixes), ``ACCOUNT_ID`` (a Cloudflare account id: 32 lower-case hexadecimal characters, not a
  credential but an identifier of the owner's account) and ``ORG_ID`` (the ``org_...`` id Groq's 429 messages name).
  All of them join cloud_support's ``SWEEP``, so the final sweep of every module fails when one reached a file the
  module wrote or a console transcript.
* The argument builders (``groq_args``, ``cf_args``) and runners (``run_groq``, ``run_cf``) that put the dummies in
  the child's environment only, as cloud/run-cloud.ps1 does.
* The mock states (``groq_state``, ``cf_state``) and the provider-shaped error bodies (``groq_429``, ``cf_error``).

Each provider test module star-imports this module (which star-imports cloud_support) and starts its own mock with
``cloud_support.start``; the helpers read ``cloud_support.URL`` when they run, after that start.

Nothing here contacts a real endpoint: every URL is the in-process mock on 127.0.0.1.
"""
import os
import secrets
import string

import cloud_support
from cloud_support import *  # noqa: F401,F403 - re-exported to the provider test modules
from cloud_support import SWEEP, STATE, out, read_text, rows, run_py

_ALNUM = string.ascii_letters + string.digits


def _alnum(n):
    """`n` random letters and digits."""
    return "".join(secrets.choice(_ALNUM) for _ in range(n))


GROQ_KEY = "gsk_" + _alnum(52)
CF_TOKEN = "cfat_" + _alnum(48)
CF_USER_TOKEN = "cfut_" + _alnum(48)
ACCOUNT_ID = secrets.token_hex(16)
ORG_ID = "org_" + _alnum(26)
SWEEP.extend([GROQ_KEY, CF_TOKEN, CF_USER_TOKEN, ACCOUNT_ID, ORG_ID])
PROVIDER_SECRETS = (GROQ_KEY, CF_TOKEN, CF_USER_TOKEN, ACCOUNT_ID, ORG_ID)

# The variables the children read (the launcher's names are GROQ_API_KEY, CLOUDFLARE_API_TOKEN and
# CLOUDFLARE_ACCOUNT_ID; the tests use their own, so a developer's real variables can never be picked up).
GROQ_ENV = "PROVQUAL_GROQ_KEY"
CF_ENV = "PROVQUAL_CF_TOKEN"
ACCT_ENV = "PROVQUAL_CF_ACCOUNT"
GROQ_MODEL = "openai/gpt-oss-20b"
CF_MODEL = "@cf/google/gemma-4-26b-a4b-it"

__all__ = list(cloud_support.__all__) + [
    "GROQ_KEY", "CF_TOKEN", "CF_USER_TOKEN", "ACCOUNT_ID", "ORG_ID", "PROVIDER_SECRETS", "GROQ_ENV", "CF_ENV",
    "ACCT_ENV", "GROQ_MODEL", "CF_MODEL", "cf_root", "groq_args", "cf_args", "run_groq", "run_cf", "groq_state",
    "cf_state", "groq_429", "cf_error", "provider_clean", "quota_rows", "chat_requests"]


def cf_root():
    """The mock's Cloudflare API root (the tool appends /accounts/<id>/ai/v1 and the other paths)."""
    return cloud_support.root_url() + "/client/v4"


def groq_args(ledger, model=GROQ_MODEL, reasoning="low"):
    """run.py arguments for a Groq run at the mock with the shared ledger `ledger` (in the work folder)."""
    return ["--provider", "groq", "--backend", "openai", "--model", model, "--base-url", cloud_support.URL,
            "--api-key-env", GROQ_ENV, "--reasoning", reasoning, "--retry-base-s", "0.01", "--retry-cap-s", "0.05",
            "--ledger", out(ledger)]


def cf_args(ledger, model=CF_MODEL, reasoning="none"):
    """run.py arguments for a Cloudflare run at the mock (the account id comes from ACCT_ENV); --provider alone
    selects the openai backend."""
    return ["--provider", "cloudflare", "--model", model, "--base-url", cf_root(), "--api-key-env", CF_ENV,
            "--account-id-env", ACCT_ENV, "--reasoning", reasoning, "--retry-base-s", "0.01", "--retry-cap-s", "0.05",
            "--ledger", out(ledger)]


def run_groq(args, key=None, **kw):
    """run.py with the dummy Groq key (or `key`) in GROQ_ENV only."""
    return run_py("run.py", args, env_extra={GROQ_ENV: GROQ_KEY if key is None else key}, drop_key=True, **kw)


def run_cf(args, key=None, account=None, **kw):
    """run.py with the dummy Cloudflare token (or `key`) and account id (or `account`) in the child's environment."""
    env = {CF_ENV: CF_TOKEN if key is None else key, ACCT_ENV: ACCOUNT_ID if account is None else account}
    return run_py("run.py", args, env_extra=env, drop_key=True, **kw)


def groq_state(rpd=1000, tpm=8000):
    """The mock as Groq on the Free plan: usage without a cost field, the free plan's limit headers."""
    STATE.cost_mode = "tokens"
    STATE.provider = None
    STATE.groq_limits = {"rpd": rpd, "tpm": tpm}


def cf_state(models=(CF_MODEL,)):
    """The mock as Cloudflare Workers AI: usage without a cost field, `models` listed by the model search."""
    STATE.cost_mode = "tokens"
    STATE.provider = None
    STATE.cf_models = list(models)


def groq_429(window, retry_after="0", model=GROQ_MODEL):
    """Groq's 429 for one limit window ("RPM", "RPD", "TPM" or "TPD"), with the organisation id in its message as
    Groq's own messages carry it (third-party quotes of the real text; Groq does not document the body)."""
    what = {"RPM": "requests per minute", "RPD": "requests per day", "TPM": "tokens per minute",
            "TPD": "tokens per day"}[window]
    msg = (f"Rate limit reached for model `{model}` in organization `{ORG_ID}` service tier `on_demand` on {what} "
           f"({window}): Limit 1000, Used 1000, Requested 1. Please try again in 7.5s.")
    return {"status": 429, "headers": {"retry-after": retry_after},
            "body": {"error": {"message": msg, "type": "tokens" if window.startswith("T") else "requests",
                               "code": "rate_limit_exceeded"}}}


def cf_error(status, code, message):
    """Cloudflare's v4 error envelope ({success: false, errors: [{code, message}]})."""
    return {"status": status, "body": {"success": False, "errors": [{"code": code, "message": message}],
                                       "messages": [], "result": None}}


def provider_clean(p, *paths):
    """No provider secret (key, token, account id, organisation id) reaches the console or the given files."""
    text = p.stdout + p.stderr + "".join(read_text(x) for x in paths if os.path.exists(x))
    return not any(s in text for s in PROVIDER_SECRETS)


def quota_rows(path, event="quota"):
    """The provider quota rows (``budget_event`` quota or quota_settle) of a ledger."""
    return [r for r in rows(path) if r.get("budget_event") == event]


def chat_requests():
    """The chat completion requests the mock received (path, headers, body)."""
    return [r for r in STATE.requests if r["path"].endswith("/chat/completions")]
