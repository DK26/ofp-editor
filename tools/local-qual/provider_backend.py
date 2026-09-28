#!/usr/bin/env python3
"""The Groq and Cloudflare Workers AI client: the openai backend with each provider's request shape (tools/local-qual).

What it owns
------------
``ProviderBackend``, an ``OpenAICompatBackend`` (cloud_backend.py) that changes only what the providers need:

* **Key.** Checked against the provider's shape before anything else (providers.key_refusal): an OpenRouter key never
  goes to Groq, and Cloudflare's Global API Key (cfk_) is never used at all.
* **Body.** OpenRouter's ``reasoning`` object is replaced by the field the model takes (``reasoning_effort``, and on
  Groq's Qwen3.8 ``reasoning_format: parsed``; providers.reasoning_wire); a seed of 0 goes to Cloudflare as 1, since
  its models take 1 to 9,999,999,999. Groq's max_completion_tokens and strict-mode schema copy are set by the flags
  (providers.apply_provider_flags), so the base class builds them.
* **Gate hooks.** ``chat`` hands the request to the gate (provider_gate.py) first; ``_post`` hands every HTTP
  exchange to the gate afterwards (usage, headers); the 429 classifier and the response stop are the gate's.
* **Redaction.** On top of the base class's (the key verbatim, every provider's key shape): the Cloudflare account id
  in any letter case, and Groq's organisation ids (``org_...``), which its 429 messages name.
* ``get``: one GET under the API root, for ``--key-status`` (provider_status.py).

How it fits
-----------
cloud_run.make_backend builds it instead of the base class when ``--provider groq|cloudflare`` is set; the paid and
free OpenRouter paths never see it. Records keep ``backend: "openai"`` and gain ``provider`` from the run's fields.
Standard library only.
"""
import re

import providers
from cloud_backend import OpenAICompatBackend
from cloud_guard import get_capped

# Groq's organisation ids ("org_" and letters and digits), as its 429 messages carry them: they identify the owner's
# organisation, so they are scrubbed like a key.
_ORG_ID = re.compile(r"org_[A-Za-z0-9]{6,}")
# The body fields that carry a provider's reasoning setting (recorded as reasoning_sent).
REASONING_FIELDS = ("reasoning_effort", "reasoning_format")


class ProviderBackend(OpenAICompatBackend):
    """``OpenAICompatBackend`` for Groq and Cloudflare (see the module docs). ``provider`` is the settings dict of
    providers.apply_provider_flags: provider, model, account_id, reasoning_wire (and api_root for ``get``)."""

    def __init__(self, base_url, timeout, api_key, provider=None, **kwargs):
        settings = dict(provider or {})
        if settings.get("provider") not in providers.ACTIVE:
            raise ValueError(f"ProviderBackend needs a provider ({', '.join(providers.ACTIVE)})")
        self.provider = settings
        account = settings.get("account_id")
        # Set before the base class runs, so no string it could return escapes this redaction.
        self._account_re = re.compile(re.escape(account), re.I) if account else None
        if api_key:
            why = providers.key_refusal(settings["provider"], api_key)
            if why:
                raise ValueError(why)
        super().__init__(base_url, timeout, api_key, **kwargs)

    # ── Secrets ──────────────────────────────────────────────────────────────

    def redact(self, text):
        """The base class's redaction, then the account id (any letter case) and Groq's organisation ids."""
        text = super().redact(text)
        if not isinstance(text, str):
            return text
        if self._account_re is not None:
            text = self._account_re.sub("[ACCOUNT]", text)
        return _ORG_ID.sub("org_[REDACTED]", text) if "org_" in text else text

    # ── Request ──────────────────────────────────────────────────────────────

    def payload(self, model, messages, schema, temperature, seed, num_predict, num_ctx, sampler, schema_name):
        """The base body with the provider's reasoning fields in place of OpenRouter's object, and Cloudflare's seed
        range (0 goes as 1)."""
        body = super().payload(model, messages, schema, temperature, seed, num_predict, num_ctx, sampler, schema_name)
        body.pop("reasoning", None)
        body.update(self.provider.get("reasoning_wire") or {})
        if self.provider["provider"] == "cloudflare" and body.get("seed") == 0:
            body["seed"] = 1
        return body

    def _post(self, body):
        """One HTTP attempt (the base class's), then the gate reads the reply's usage and headers."""
        status, headers, raw, exc = super()._post(body)
        if self.gate is not None and hasattr(self.gate, "after_attempt"):
            self.gate.after_attempt(status, headers, raw)
        return status, headers, raw, exc

    def _classify_429(self, headers, data, now, retry_after=None):
        if self.gate is not None and hasattr(self.gate, "classify_429"):
            return self.gate.classify_429(headers, data, now, retry_after)
        return super()._classify_429(headers, data, now, retry_after)

    def _response_stop(self, data, answered):
        if self.gate is not None and hasattr(self.gate, "response_stop"):
            return self.gate.response_stop(data, answered)
        return super()._response_stop(data, answered)

    def chat(self, body, budget=None, call_id=None):
        """The base class's call, with the request handed to the gate first; the record names the reasoning fields
        actually sent (or "omit")."""
        if self.gate is not None and hasattr(self.gate, "begin_call"):
            self.gate.begin_call(body, call_id)
        res = super().chat(body, budget=budget, call_id=call_id)
        wire = {k: body[k] for k in REASONING_FIELDS if k in body}
        res["extra"]["reasoning_sent"] = wire or "omit"
        res["think_sent"] = bool(wire)
        return res

    def get(self, url):
        """One GET under the API root with the key (never raises): (status, headers, body text, exception), from
        cloud_guard.get_capped; redirects are never followed. ValueError for a URL outside the root."""
        root = self.provider.get("api_root") or ""
        if not root or not url.startswith(root + "/"):
            raise ValueError("ProviderBackend.get reads only under the provider's API root")
        return get_capped(self._opener, url, self._headers, min(self.timeout, 30.0))
