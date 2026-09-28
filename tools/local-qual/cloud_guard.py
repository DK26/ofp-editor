#!/usr/bin/env python3
"""What a paid request may carry, and how it travels (tools/local-qual).

What it owns
------------
The checks that run before the ``openai`` backend (cloud_backend.py) sends
anything: the base URL (https, or plain http only to this machine), the key
(stripped, printable, long enough to redact, free of the two characters JSON
escapes, never inside the URL or the extra body), ``--extra-body`` (no field
run.py owns, no billing the budget cap cannot price, no provider thinking
switch next to ``--reasoning``, no credential), the
``--schema-strip`` whitelist and the strict-mode schema copy; the transport
rules: redirects are never followed (the key would go with them), a loopback
server is reached without a proxy, and a response body is read up to a size
cap; and the provider-name match that checks who served a response.

How it fits
-----------
cloud_backend.py calls these in ``OpenAICompatBackend.__init__`` and uses the
opener and the capped reader for every request; cloud_run.py uses the
parameter lists for its flags and ``normalise_schema`` for the canary's
schema-conformance check. Every refusal is a ValueError whose message never
contains the key; cloud_run.py turns it into a command-line error (exit 2)
before any request leaves the machine. Standard library only.
"""
import ipaddress
import json
import re
import urllib.parse
import urllib.request

from backends import SAMPLER_KEYS

# Top-level body fields --extra-body may not set. run.py owns them, and overriding them would break the
# budget (max_tokens, n), the paired design (messages, seed, temperature, sampler) or the schema rungs
# (response_format); `reasoning` has its own flag so the effort is always explicit and recorded. The second
# line is billing the cap cannot see or price: OpenRouter's fallback `models` list (another model, another
# price), web search options billed per search, predicted outputs, and fields that add prompt text or lift the
# output cap under another name (https://openrouter.ai/docs/api-reference/overview, read 2026-09-27). The third
# line bills tokens at a rate the price flags do not name: a service tier (OpenAI's priority tier costs more per
# token than its list price) and audio or image output (`modalities`, `audio`: billed per audio token or per
# image). On an endpoint that reports no cost the ledger would count those calls at the flags' lower rate, and the
# cost-anomaly check, which compares with that same computed figure, could not see it.
FORBIDDEN_EXTRA = frozenset(("model", "messages", "stream", "stream_options", "max_tokens", "max_completion_tokens",
                             "n", "best_of", "response_format", "temperature", "seed", "reasoning", "tools",
                             "tool_choice", "functions", "function_call") + SAMPLER_KEYS
                            + ("models", "route", "web_search_options", "prediction", "max_output_tokens", "prompt",
                               "input")
                            + ("service_tier", "modalities", "audio"))
# Provider-specific thinking switches. --reasoning already sets the effort, so they may appear in --extra-body
# only with --reasoning omit (the documented way to pass a provider's own field).
REASONING_EXTRA = ("reasoning_effort", "thinking", "enable_thinking", "chat_template_kwargs", "include_reasoning")
# Schema keywords --schema-strip may drop: validation-only limits and annotations. Dropping anything else
# (enum, type, properties, required, ...) would quietly turn the strict arm into a looser one.
STRIPPABLE_KEYWORDS = ("maxLength", "minLength", "pattern", "format", "maxItems", "minItems", "uniqueItems",
                       "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minProperties",
                       "maxProperties", "title", "description", "default", "examples", "$schema", "$id", "$comment")
# A field name that looks like a credential. --extra-body is copied into every record, so a secret there would be
# written to disk; the only key the tool handles is the one from --api-key-env, which it redacts.
_SECRET_NAME = re.compile(r"(^|[_-])(api[_-]?key|apikey|key|token|access[_-]?token|secret|password|passwd|"
                          r"authorization|auth|bearer|credentials?)($|[_-])", re.I)
# Parser-safety cap on a response body: a completion here is a few KiB, so anything larger is not one (and
# reading an unbounded body from an untrusted server could exhaust memory).
MAX_BODY_BYTES = 8 * 1024 * 1024
# Shortest key the tool accepts: every record line is scrubbed of the key by plain substring replacement, so a
# tiny key such as "x" or "sk" would also rewrite field names and corrupt the records.
MIN_KEY_CHARS = 8
# The printable ASCII characters json.dumps does not write as themselves (a quote and a backslash). The key scrub
# replaces the key's exact text in every JSON line, so a key must not contain them (check_key).
JSON_ESCAPED = ('"', "\\")
# Parameters run.py may leave out per endpoint (--drop-params), for models that reject them.
DROPPABLE_PARAMS = ("temperature", "seed") + SAMPLER_KEYS


def provider_matches(expected, served):
    """Does the provider named in a response match the pinned one?

    Compares lower-case alphanumerics of the pin's provider part ("deepinfra/bf16" -> "deepinfra") with the
    served name ("DeepInfra"), allowing a longer display name ("Nebius AI Studio" for "nebius"). The preflight
    shows the exact served name, which can also be passed as the pin.
    """
    def norm(s):
        return re.sub(r"[^a-z0-9]", "", str(s or "").lower())
    base, got = norm(str(expected).split("/", 1)[0]), norm(served)
    full = norm(expected)
    return bool(base) and bool(got) and (got in (base, full) or got.startswith(base))


def is_loopback(host):
    """localhost, 127.0.0.0/8 or ::1."""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def check_base_url(url):
    """Validate an OpenAI-compatible base URL (for example https://openrouter.ai/api/v1) and return it without a trailing slash.

    The bearer key travels in a header on every call, so the URL must not carry credentials or a query string,
    and plain http is accepted only for a server on this machine (a local vLLM or llama-server, or the test mock).
    """
    raw = (url or "").strip()
    p = urllib.parse.urlsplit(raw)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("--base-url must be an http(s) URL such as https://openrouter.ai/api/v1")
    if p.username or p.password:
        raise ValueError("--base-url must not carry credentials; the key comes from --api-key-env")
    if p.query or p.fragment:
        raise ValueError("--base-url must not carry a query string or a fragment")
    if p.scheme == "http" and not is_loopback(p.hostname):
        raise ValueError("plain http is allowed only for a loopback server: the bearer key would travel unencrypted")
    return raw.rstrip("/")


def check_key(key):
    """Return the key stripped of surrounding whitespace, or raise ValueError (the message never holds the key).

    A key read from a file or with PowerShell's ``Get-Content -Raw`` often ends in a newline; sent as is, Python's
    http.client refuses the header with a ValueError whose message *contains the header value*, so the key would
    land in a traceback. Inner whitespace, control or non-ASCII characters mean the variable holds something else;
    a quote or a backslash (``JSON_ESCAPED``) would defeat the scrub of the JSON lines the tool writes.
    """
    k = (key or "").strip()
    if not k:
        return k
    if any(ord(c) < 33 or ord(c) > 126 for c in k):
        raise ValueError("the API key contains spaces, control or non-ASCII characters; check the environment variable")
    if any(c in JSON_ESCAPED for c in k):
        # Records and ledgers are JSON lines, scrubbed of the key by exact-text replacement just before each write;
        # JSON writes these two characters escaped, so a key holding one, echoed inside a nested object, would reach
        # the file in a form the scrub cannot find. No real API key contains them.
        raise ValueError("the API key contains a double quote or backslash, which JSON escapes, so it could not be "
                         "scrubbed from records; check the environment variable")
    if len(k) < MIN_KEY_CHARS:
        raise ValueError(f"the API key is shorter than {MIN_KEY_CHARS} characters, too short to redact safely from "
                         f"records")
    return k


def check_extra_body(extra, key, reasoning):
    """Refuse --extra-body content that would break the budget, the measurement or the key rules (ValueError)."""
    plugins = extra.get("plugins")
    if plugins is not None:
        # Response healing repairs JSON on the server (blurring the schema rungs); the web plugin bills per search.
        raise ValueError("--extra-body may not set plugins: OpenRouter plugins such as response-healing (server-side "
                         "JSON repair would blur the schema rungs) or web (billed per search) change what is measured "
                         "or billed")
    bad = sorted(set(extra) & FORBIDDEN_EXTRA)
    if bad:
        raise ValueError(f"--extra-body may not set {', '.join(bad)}: run.py sets these (use its flags), or they add "
                         f"billing the budget cap cannot price")
    if reasoning is not None:
        clash = sorted(set(extra) & set(REASONING_EXTRA))
        if clash:
            raise ValueError(f"--extra-body sets {', '.join(clash)} while --reasoning already sets the effort; pass "
                             f"--reasoning omit to use a provider's own field")
    text = json.dumps(extra, ensure_ascii=False)
    if key and key in text:
        raise ValueError("--extra-body contains the API key; the key goes only in --api-key-env")

    def walk(node, path):
        if isinstance(node, dict):
            for name, value in node.items():
                if _SECRET_NAME.search(str(name)):
                    raise ValueError(f"--extra-body field {path + str(name)!r} looks like a credential; --extra-body "
                                     f"is copied into every record, so no secret may go there")
                walk(value, f"{path}{name}.")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}{i}.")
    walk(extra, "")


class _RefuseRedirects(urllib.request.HTTPRedirectHandler):
    """Never follow a 3xx. urllib's default handler re-sends a POST 301/302/303 as a GET, and follows every GET
    redirect, *with the Authorization header*, to whatever host (or plain-http URL) the Location names. Returning
    None here makes the opener raise the 3xx as an HTTPError instead, which chat() stops on, unbilled."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def opener(base_url):
    """The URL opener for one endpoint: redirects refused; no proxy for a loopback server (a proxy would see the key
    of a plain-http local server in clear text); for https, the environment's proxy settings still apply (the
    request stays encrypted inside the proxy's CONNECT tunnel)."""
    handlers = [_RefuseRedirects]
    if is_loopback(urllib.parse.urlsplit(base_url).hostname or ""):
        handlers.append(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener(*handlers)


def read_capped(stream):
    """Up to MAX_BODY_BYTES of a response body as text; (text, None) or ("", ValueError) when it is larger."""
    raw = stream.read(MAX_BODY_BYTES + 1)
    if len(raw) > MAX_BODY_BYTES:
        return "", ValueError(f"response body larger than {MAX_BODY_BYTES} bytes")
    return raw.decode("utf-8", "replace"), None


def normalise_schema(schema, strict_objects=True, strip=()):
    """Return (a copy of `schema` for strict structured-output endpoints, sorted list of keywords removed).

    OpenAI-style strict mode wants every object to list all its properties in ``required`` and to set
    ``additionalProperties: false``; some providers also reject keywords such as ``maxLength`` or ``pattern``
    (doc 40 §2.6 for Anthropic). Only the wire copy changes: score.py still validates every answer against the
    suite's original schema, so a stripped keyword is still checked, in code. The walk knows which keys hold
    sub-schemas, so a property that happens to be *named* "pattern" is never stripped.
    """
    removed = set()

    def walk(node):
        if not isinstance(node, dict):
            return node
        out = {}
        for key, value in node.items():
            if key in strip:
                removed.add(key)
                continue
            if key in ("properties", "$defs", "definitions", "patternProperties") and isinstance(value, dict):
                out[key] = {name: walk(sub) for name, sub in value.items()}
            elif key in ("items", "additionalProperties", "not", "contains") and isinstance(value, dict):
                out[key] = walk(value)
            elif key in ("anyOf", "oneOf", "allOf", "prefixItems") and isinstance(value, list):
                out[key] = [walk(sub) for sub in value]
            else:
                out[key] = value  # data (enum, const, required) or a scalar keyword, copied as is
        typ = out.get("type")
        is_object = typ == "object" or (isinstance(typ, list) and "object" in typ) or "properties" in out
        if strict_objects and is_object:
            out["required"] = list(out.get("properties", {}))
            out["additionalProperties"] = False
        return out

    return walk(schema), sorted(removed)
