#!/usr/bin/env python3
"""Mock OpenAI-compatible server for testing the local-qual cloud backend without spending money.

What it serves
--------------
* ``POST <any prefix>/chat/completions``: a canned chat completion. With a strict ``response_format``
  json_schema it returns an object built from the schema (first enum value, short strings); without one it
  returns ``text_answer`` (or whatever ``answer_fn(body)`` returns). ``usage`` carries prompt tokens (UTF-8
  bytes of the messages / 4), completion tokens (+ reasoning tokens), ``cost`` at the mock's own prices,
  cached tokens and reasoning tokens, like OpenRouter's usage accounting. The top-level ``provider`` field
  names the serving provider.
* ``GET <any prefix>/key``: an OpenRouter-style key record ({"data": {...}}): ``state.key`` as set, plus, when
  ``free_daily_limit`` is set, ``free_model_daily_requests {used, limit, remaining}`` counted live from the chat
  requests (every attempt counts) plus ``free_used_offset`` (and ``external_use = (after_n_chats, extra)``: another
  client using the account's quota mid-run); ``key_usage_per_chat`` makes ``usage``/``usage_daily`` rise per chat.
* ``GET <prefix>/models`` and ``GET <prefix>/models/<id>/endpoints``: a small public catalogue in OpenRouter's shape
  (``state.catalogue``, see ``default_catalogue``): a free model, a paid model and the traps a free-only guard must
  refuse (a router-style "-1" price, a request fee, a web-search fee, audio output, priced overrides, no endpoints,
  a priced endpoint, an expired model) and an endpoint without structured outputs or seed.

Free-tier behaviour
-------------------
With ``free_daily_limit`` set, a chat request past the limit gets OpenRouter's daily-cap 429 ("Rate limit exceeded:
free-models-per-day", X-RateLimit-Reset at the next 00:00 UTC in epoch milliseconds). ``served_model`` replaces the
response's ``model`` (model substitution). ``price_in``/``price_out`` 0 make ``usage.cost`` 0, as on a free model.

Scripting
---------
``state.queue`` holds scripted responses consumed first-in first-out by chat calls: dicts with ``status``,
``body`` (a dict, or a string sent raw) and ``headers``, or ``{"drop": True}``, which closes the connection
without any answer (a dropped connection: the request may have been processed). The special body string
``"ECHO_AUTH"`` returns the request's Authorization header inside the error message (to prove the client redacts
it). Other switches:
``reject_schema`` (400 when response_format is present), ``cost_mode`` ("provider": usage.cost; "tokens":
usage without cost; "none": no usage at all), ``cost_details`` (None, the default: no ``cost_details`` and no
``is_byok``; "mirror": OpenRouter's shape on a request paid with OpenRouter credits, ``is_byok`` false and
``cost_details.upstream_inference_cost`` equal to ``cost``, as on every answered call of doc 54's screening round;
a number: a bring-your-own-key request, ``is_byok`` true with that upstream cost in USD), ``cost_multiplier``,
``provider``, ``reasoning_tokens``,
``answer_fn``, ``key_redirect`` (a URL: ``GET /key`` answers 302 to it, to prove the client never follows a
redirect with the key), ``key_queue`` (scripted ``GET /key`` responses, consumed first-in first-out like ``queue``,
with the same ``"ECHO_AUTH"`` body; the key-status failure tests) and ``delay_s`` (seconds each chat call waits,
for the concurrency test). Every request (path, headers, parsed body) is appended to ``state.requests``.

Groq and Cloudflare Workers AI (``run.py --provider``)
------------------------------------------------------
Both speak the same chat completions shape, so the chat route above serves them too (``cost_mode = "tokens"``: usage
without a cost field, as both send). A ``response_format`` in Workers AI's own JSON-mode shape (``json_schema`` holding
the schema itself, not OpenAI's ``{name, strict, schema}``) is answered from that schema too. ``groq_limits`` ({"rpd", "tpm"}) makes every answered chat carry Groq's
``x-ratelimit-*`` headers (requests per day and tokens per minute, remaining counts and Go-style reset durations);
``groq_models`` (a list of model objects) makes ``GET <prefix>/models`` answer Groq's model list instead of the
OpenRouter catalogue. For Cloudflare, ``GET .../tokens/verify`` answers ``cf_verify`` (default: an active token) and
``GET .../ai/models/search?search=<text>`` lists the names in ``cf_models`` that contain the search text, both in
Cloudflare's v4 envelope. ``get_queue`` holds scripted responses for every GET except ``/key`` (first in, first out,
the same ``"ECHO_AUTH"`` body as ``queue``), for the key-status failure tests.

Run standalone (``python mock_server.py --port 8765``) or in-process (``start()``). Standard library only.
"""
import argparse
import copy
import datetime
import json
import math
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Every parameter the default free endpoint supports (OpenRouter's supported_parameters names).
ALL_PARAMS = ["max_tokens", "temperature", "seed", "reasoning", "include_reasoning", "response_format",
              "structured_outputs", "top_p", "top_k", "min_p", "presence_penalty", "repetition_penalty", "stop"]
FREE = {"prompt": "0", "completion": "0"}


def _model(mid, pricing=None, out=("text",), expiration=None, canonical=None):
    return {"id": mid, "canonical_slug": canonical or mid.split(":")[0] + "-20260901", "name": mid,
            "architecture": {"modality": "text->" + "+".join(out), "input_modalities": ["text"],
                             "output_modalities": list(out), "tokenizer": "Other"},
            "pricing": dict(FREE if pricing is None else pricing), "expiration_date": expiration,
            "reasoning": {"mandatory": False, "default_enabled": False, "supported_efforts": ["low", "medium", "high"]}}


def _endpoint(mid, pricing=None, params=None, tag="mockprov/fp8", provider="MockProvider"):
    return {"name": f"{provider} | {mid}", "model_id": mid, "context_length": 32768,
            "pricing": dict(dict(FREE, discount=0) if pricing is None else pricing), "provider_name": provider,
            "tag": tag, "quantization": "fp8", "supported_parameters": list(ALL_PARAMS if params is None else params),
            "status": 0, "uptime_last_1d": 99.5}


def default_catalogue():
    """id -> {"model": /models entry, "endpoints": /endpoints rows} for the free-mode tests."""
    cat = {}

    def add(mid, model=None, endpoints=None):
        cat[mid] = {"model": model or _model(mid), "endpoints": [_endpoint(mid)] if endpoints is None else endpoints}

    add("mock/free-model:free")
    add("mock/model-1", _model("mock/model-1", {"prompt": "0.000001", "completion": "0.000001"}),
        [_endpoint("mock/model-1", {"prompt": "0.000001", "completion": "0.000001"})])
    add("mock/negprice:free", _model("mock/negprice:free", {"prompt": "-1", "completion": "-1"}))
    add("mock/hidden-fee:free", _model("mock/hidden-fee:free", dict(FREE, request="0.001")))
    add("mock/web-fee:free", _model("mock/web-fee:free", dict(FREE, web_search="0.01")))
    add("mock/audio:free", _model("mock/audio:free", out=("text", "audio")))
    add("mock/overrides:free", _model("mock/overrides:free", dict(FREE, overrides=[
        {"min_prompt_tokens": 1000, "prompt": "0.0000001", "completion": "0"}])))
    add("mock/zero-overrides:free", _model("mock/zero-overrides:free", dict(FREE, request="0", image="0", overrides=[
        {"min_prompt_tokens": 1000, "prompt": "0", "completion": "0"}])))
    add("mock/no-endpoints:free", endpoints=[])
    add("mock/paid-endpoint:free", endpoints=[_endpoint("mock/paid-endpoint:free",
                                                        {"prompt": "0.0000002", "completion": "0", "discount": 0})])
    add("mock/expired:free", _model("mock/expired:free", expiration="2020-01-01"))
    add("mock/noschema:free", endpoints=[_endpoint("mock/noschema:free", params=[
        p for p in ALL_PARAMS if p not in ("response_format", "structured_outputs", "seed")])])
    return cat


def next_midnight_ms():
    now = datetime.datetime.now(datetime.timezone.utc)
    day = now.date() + datetime.timedelta(days=1)
    return int(datetime.datetime(day.year, day.month, day.day, tzinfo=datetime.timezone.utc).timestamp() * 1000)


def daily_cap_429():
    """OpenRouter's daily free-quota 429 (body and headers as reported publicly)."""
    return {"status": 429, "body": {"error": {"code": 429, "message": "Rate limit exceeded: free-models-per-day",
                                              "metadata": {"error_type": "rate_limit_exceeded"}}},
            "headers": {"X-RateLimit-Limit": "50", "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(next_midnight_ms())}}


def value_for(schema):
    """A small valid value for the schema subset the suites use."""
    if "enum" in schema:
        return schema["enum"][0]
    typ = schema.get("type")
    if isinstance(typ, list):
        typ = typ[0]
    if typ == "object":
        return {k: value_for(v) for k, v in schema.get("properties", {}).items()}
    if typ == "array":
        return [value_for(schema.get("items", {}))] * max(1, schema.get("minItems", 0))
    if typ in ("integer", "number"):
        return 0
    if typ == "boolean":
        return False
    return "x"


class MockState:
    def __init__(self):
        self.lock = threading.Lock()
        self.queue = []
        self.requests = []
        self.reject_schema = False
        self.cost_mode = "provider"
        self.cost_details = None  # None, "mirror" or a BYOK upstream cost in USD (see the module docs)
        self.price_in = 1.0  # USD per 1M tokens, for usage.cost
        self.price_out = 1.0
        self.cost_multiplier = 1.0
        self.provider = "MockProvider"
        self.reasoning_tokens = 0
        self.cached_tokens = 0
        self.text_answer = "HOLD"
        self.answer_fn = None
        self.key = {"limit": 2.0, "limit_remaining": 1.5, "usage": 0.5}
        self.key_redirect = None
        self.key_queue = []  # scripted GET /key responses ({"status", "body", "headers"}), first in, first out
        self.delay_s = 0.0
        self.catalogue = default_catalogue()
        self.free_daily_limit = None
        self.free_used_offset = 0
        self.external_use = None  # (after_n_chats, extra requests another client used)
        self.key_usage_per_chat = 0.0
        self.served_model = None
        # Groq and Cloudflare (see the module docs); None or empty: the OpenRouter-shaped behaviour above.
        self.groq_limits = None
        self.groq_models = None
        self.get_queue = []
        self.cf_verify = None
        self.cf_models = None

    def reset(self):
        self.__init__()

    def count(self, suffix="/chat/completions"):
        with self.lock:
            return sum(1 for r in self.requests if r["path"].endswith(suffix))

    def free_used(self):
        """The account's free requests used today: every chat attempt, the preset offset, other clients' use."""
        chats = self.count()
        extra = self.external_use[1] if self.external_use and chats >= self.external_use[0] else 0
        return chats + self.free_used_offset + extra

    def key_record(self):
        data = copy.deepcopy(self.key)
        chats = self.count()
        if self.key_usage_per_chat:
            for f in ("usage", "usage_daily"):
                data[f] = (data.get(f) or 0) + self.key_usage_per_chat * chats
        if self.free_daily_limit is not None:
            used = self.free_used()
            data["free_model_daily_requests"] = {"used": used, "limit": self.free_daily_limit,
                                                 "remaining": max(0, self.free_daily_limit - used)}
        return data


STATE = MockState()


class Handler(BaseHTTPRequestHandler):
    server_version = "MockOpenAI/1.0"

    def log_message(self, fmt, *args):  # keep test output quiet
        pass

    def _send(self, status, body, headers=None):
        raw = body if isinstance(body, (bytes, str)) else json.dumps(body)
        raw = raw.encode("utf-8") if isinstance(raw, str) else raw
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for k, v in (headers or {}).items():
            if isinstance(v, str) and v.startswith("RESET_IN:"):
                # A reset relative to the moment of sending, in epoch milliseconds (timing-independent tests).
                v = str(int((time.time() + float(v.split(":", 1)[1])) * 1000))
            self.send_header(k, str(v))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # the client stopped reading (the oversize-body test); nothing to report

    def do_GET(self):
        with STATE.lock:
            STATE.requests.append({"path": self.path, "headers": dict(self.headers), "body": None})
        rel = self.path.split("/api/v1", 1)[1] if "/api/v1" in self.path else self.path
        if rel == "/key" or (rel.endswith("/key") and not rel.startswith("/models")):
            with STATE.lock:
                scripted = STATE.key_queue.pop(0) if STATE.key_queue else None
            if scripted is not None:
                out = scripted.get("body")
                if out == "ECHO_AUTH":
                    out = {"error": {"code": scripted.get("status", 500),
                                     "message": "key lookup failed; you sent " + str(self.headers.get("Authorization"))}}
                return self._send(scripted.get("status", 200), out, scripted.get("headers"))
            if STATE.key_redirect:
                return self._send(302, {"error": {"code": 302, "message": "moved"}}, {"Location": STATE.key_redirect})
            return self._send(200, {"data": STATE.key_record()})
        with STATE.lock:
            scripted = STATE.get_queue.pop(0) if STATE.get_queue else None
        if scripted is not None:
            out = scripted.get("body")
            if out == "ECHO_AUTH":
                out = {"error": {"code": scripted.get("status", 500),
                                 "message": "lookup failed; you sent " + str(self.headers.get("Authorization"))}}
            return self._send(scripted.get("status", 200), out, scripted.get("headers"))
        path = urllib.parse.urlsplit(rel).path
        if path.endswith("/tokens/verify"):
            # Cloudflare's token check (v4 envelope); the default is an active token with no expiry.
            verify = STATE.cf_verify or {"id": "mock-token-id", "status": "active", "expires_on": None,
                                         "not_before": None}
            return self._send(200, {"success": True, "errors": [], "messages": [], "result": verify})
        if path.endswith("/ai/models/search"):
            # Cloudflare's model catalogue: every name in cf_models that contains the search text.
            wanted = (urllib.parse.parse_qs(urllib.parse.urlsplit(rel).query).get("search") or [""])[0]
            found = [{"id": f"mock-{i}", "name": name, "description": "", "task": {"name": "Text Generation"}}
                     for i, name in enumerate(STATE.cf_models or []) if wanted in name]
            return self._send(200, {"success": True, "errors": [], "messages": [], "result": found})
        if rel == "/models" and STATE.groq_models is not None:
            return self._send(200, {"object": "list", "data": copy.deepcopy(STATE.groq_models)})
        if rel == "/models":
            return self._send(200, {"data": [copy.deepcopy(v["model"]) for v in STATE.catalogue.values()]})
        if rel.startswith("/models/") and rel.endswith("/endpoints"):
            mid = rel[len("/models/"):-len("/endpoints")]
            entry = STATE.catalogue.get(mid)
            if entry is None:
                return self._send(404, {"error": {"code": 404, "message": "Model not found"}})
            return self._send(200, {"data": {"id": mid, "name": mid, "architecture": entry["model"]["architecture"],
                                             "endpoints": copy.deepcopy(entry["endpoints"])}})
        return self._send(404, {"error": {"code": 404, "message": "not found"}})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8")
        try:
            body = json.loads(raw)
        except ValueError:
            body = None
        with STATE.lock:
            STATE.requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
            scripted = STATE.queue.pop(0) if STATE.queue else None
        if STATE.delay_s:
            time.sleep(STATE.delay_s)
        if not self.path.endswith("/chat/completions") or not isinstance(body, dict):
            return self._send(404, {"error": {"code": 404, "message": "not found"}})
        if scripted is not None and scripted.get("drop"):
            # No status line at all: the handler returns and the server closes the socket, so the client sees the
            # connection end without an answer (http.client's RemoteDisconnected).
            self.close_connection = True
            return None
        if scripted is not None:
            out = scripted.get("body")
            if out == "ECHO_AUTH":
                out = {"error": {"code": scripted.get("status", 500),
                                 "message": "upstream failed; you sent " + str(self.headers.get("Authorization"))}}
            elif out == "OK":
                out = self.completion(body)
            return self._send(scripted.get("status", 200), out, scripted.get("headers"))
        if STATE.free_daily_limit is not None and STATE.free_used() > STATE.free_daily_limit:
            cap = daily_cap_429()  # the server's own daily cap: the client should never get here
            return self._send(cap["status"], cap["body"], cap["headers"])
        if STATE.reject_schema and "response_format" in body:
            return self._send(400, {"error": {"code": 400, "message": "Provider returned error",
                                              "metadata": {"provider_name": STATE.provider,
                                                           "raw": "response_format json_schema is not supported"}}})
        resp = self.completion(body)
        return self._send(200, resp, self.groq_headers(resp))

    def groq_headers(self, resp):
        """Groq's rate-limit headers for one answered chat (none unless ``groq_limits`` is set): requests per day
        (limit, remaining after this request, reset as a Go duration) and tokens per minute (limit, remaining after
        this reply's tokens, reset), as https://console.groq.com/docs/rate-limits describes them."""
        lim = STATE.groq_limits
        if not lim:
            return {}
        used = (resp.get("usage") or {}).get("total_tokens") or 0
        return {"x-ratelimit-limit-requests": str(lim["rpd"]),
                "x-ratelimit-remaining-requests": str(max(0, lim["rpd"] - STATE.count())),
                "x-ratelimit-reset-requests": "2m59.56s",
                "x-ratelimit-limit-tokens": str(lim["tpm"]),
                "x-ratelimit-remaining-tokens": str(max(0, lim["tpm"] - used)),
                "x-ratelimit-reset-tokens": "7.66s"}

    def completion(self, body):
        """A chat completion for `body` with usage, cost and provider, like OpenRouter's."""
        rf = body.get("response_format")
        if STATE.answer_fn is not None:
            content = STATE.answer_fn(body)
        elif isinstance(rf, dict) and rf.get("type") == "json_schema":
            # OpenAI's wrapper {name, strict, schema}, or Workers AI's JSON mode, where json_schema is the schema.
            js = rf.get("json_schema") or {}
            content = json.dumps(value_for(js["schema"] if isinstance(js.get("schema"), dict) else js))
        else:
            content = STATE.text_answer
        nbytes = sum(len(str(m.get("content") or "").encode("utf-8")) for m in body.get("messages", []))
        prompt = math.ceil(nbytes / 4)
        completion = math.ceil(len(content) / 4) + STATE.reasoning_tokens
        usage = {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion,
                 "prompt_tokens_details": {"cached_tokens": STATE.cached_tokens, "cache_write_tokens": 0},
                 "completion_tokens_details": {"reasoning_tokens": STATE.reasoning_tokens}}
        if STATE.cost_mode == "provider":
            usage["cost"] = (prompt * STATE.price_in + completion * STATE.price_out) / 1e6 * STATE.cost_multiplier
            if STATE.cost_details == "mirror":
                usage["is_byok"] = False
                usage["cost_details"] = {"upstream_inference_cost": usage["cost"]}
            elif isinstance(STATE.cost_details, (int, float)) and not isinstance(STATE.cost_details, bool):
                usage["is_byok"] = True
                usage["cost_details"] = {"upstream_inference_cost": float(STATE.cost_details)}
        resp = {"id": "gen-mock-%d" % len(STATE.requests), "object": "chat.completion", "created": 0,
                "model": STATE.served_model or body.get("model"), "provider": STATE.provider,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                             "finish_reason": "stop", "native_finish_reason": "stop"}]}
        if STATE.cost_mode != "none":
            resp["usage"] = usage
        return resp


def start(port=0):
    """Start the server on 127.0.0.1 in a daemon thread; returns (server, base_url)."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/api/v1"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Mock OpenAI-compatible server (canned answers, usage and cost).")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--reject-schema", action="store_true")
    ap.add_argument("--provider", default="MockProvider")
    a = ap.parse_args()
    STATE.reject_schema, STATE.provider = a.reject_schema, a.provider
    srv, url = start(a.port)
    print(f"mock OpenAI-compatible server at {url} (Ctrl+C to stop)", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()
