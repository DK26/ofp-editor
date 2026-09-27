#!/usr/bin/env python3
"""HTTP clients for the local-qual runner (tools/local-qual).

What it owns
------------
The two runtimes run.py can talk to, behind one small interface:

* ``OllamaBackend``: Ollama's native ``POST /api/chat`` (``stream: false``). The
  JSON schema goes in ``format``; ``think: false`` switches off hybrid thinking.
  This is the path doc 44 measured, and its request body is unchanged.
* ``LlamaServerBackend``: llama.cpp's ``llama-server``, through its
  OpenAI-compatible ``POST /v1/chat/completions``. The JSON schema goes in
  ``response_format`` (``{"type": "json_schema", "json_schema": {name, schema,
  strict}}``), which llama-server turns into a grammar that constrains
  decoding, the same mechanism as Ollama's ``format``. Thinking is switched
  off with ``chat_template_kwargs: {"enable_thinking": false}``, a variable the
  model's own Jinja chat template reads (not every template reads it; the
  probe records whether this one does).

How it fits
-----------
run.py builds the prompt, the schema and the seed for one call; a backend turns
them into its wire format (``payload``), sends it (``chat``) and returns a
backend-neutral result whose field names are the ones score.py already reads
(Ollama's names: ``prompt_eval_count``, ``eval_count``, ``eval_duration`` in
nanoseconds, ``done_reason``). So score.py scores both backends unchanged.
``probe`` reads what the server says about itself once per run (runtime
version, model file, quantisation, effective context size), because servers
may silently differ from what was asked (doc 13 §3).

Standard library only, like the rest of the tool.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

# Quantisation tag inside a GGUF file name, for example "UD-Q4_K_XL" in
# "Qwen3.5-4B-UD-Q4_K_XL.gguf", "Q4_K_M", "IQ4_XS", "q4_0" or "BF16". The tag must
# sit between separators so model names such as "Qwen3.5" or "E4B" never match.
_QUANT_RE = re.compile(r"(?:^|[-_.])((?:UD-)?I?Q\d(?:_[A-Z0-9]+)*|BF16|F16|F32)(?=$|[-_.])", re.I)
# Sampler overrides run.py may send; None means "leave the server or build default".
SAMPLER_KEYS = ("top_k", "top_p", "min_p", "presence_penalty", "repeat_penalty")


def quant_from_filename(name):
    """Return the quantisation tag found in a GGUF file name (upper case), or None."""
    stem = os.path.basename(name or "")
    if stem.lower().endswith(".gguf"):
        stem = stem[:-5]
    found = _QUANT_RE.findall(stem)
    return found[-1].upper() if found else None


def normalize_host(host, default_port="11434"):
    """Turn a host setting into a URL a client can connect to.

    OLLAMA_HOST is often set for the *server* as a bind address such as
    "0.0.0.0:11434". A client cannot connect to a wildcard address (Windows
    fails with WinError 10049), so, like the Ollama CLI, map 0.0.0.0 and :: to
    loopback, and add the scheme and the default port when missing.
    """
    h = (host or "").strip() or f"http://localhost:{default_port}"
    if "://" not in h:
        h = "http://" + h
    scheme, rest = h.split("://", 1)
    hostport, _, path = rest.partition("/")
    if hostport.startswith("["):  # IPv6 literal, e.g. [::]:11434
        addr, _, port = hostport[1:].partition("]")
        port = port.lstrip(":")
    elif hostport.count(":") == 1:
        addr, port = hostport.split(":")
    else:
        addr, port = hostport, ""
    if addr in ("0.0.0.0", "::", ""):
        addr = "127.0.0.1"
    elif ":" in addr:
        addr = f"[{addr}]"
    return f"{scheme}://{addr}:{port or default_port}" + (f"/{path}" if path else "")


class _Http:
    """Tiny JSON-over-HTTP helper shared by both backends."""

    def __init__(self, base_url, timeout, headers=None):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json", **(headers or {})}

    def request(self, method, path, body=None, timeout=None):
        """Send one request and return the decoded JSON (raises urllib errors)."""
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, headers=self.headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
            raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def try_request(self, method, path, body=None, timeout=30):
        """Like request, but returns None on any failure (used by the optional probes)."""
        try:
            return self.request(method, path, body, timeout)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, ValueError):
            return None


def _post_with_retries(http, path, body, drop_field, match_words, on_drop):
    """POST with two retries on connection errors and one retry without `drop_field`.

    Returns (response dict or None, error str or None, body actually sent). A
    server whose error message names the field (any of `match_words`), such as
    an older Ollama rejecting ``think`` or a llama-server build rejecting
    ``chat_template_kwargs``, gets the call again without it; `on_drop` then
    stops sending it for the rest of the run. The record's ``think_sent`` shows
    that this happened.
    """
    for attempt in range(3):
        try:
            return http.request("POST", path, body), None, body
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            named = any(w in detail.lower() for w in match_words)
            if drop_field in body and e.code in (400, 422, 500) and named:
                body = {k: v for k, v in body.items() if k != drop_field}
                on_drop()
                continue
            return None, f"HTTP {e.code}: {detail}", body
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if attempt < 2:
                time.sleep(2.0)
                continue
            return None, f"{type(e).__name__}: {e}", body
    return None, "retries exhausted", body


# ── Ollama ───────────────────────────────────────────────────────────────────

class OllamaBackend:
    """Ollama's native /api/chat (stream=false), as measured in doc 44."""

    name = "ollama"

    def __init__(self, base_url, timeout, think_mode, keep_alive):
        self.http = _Http(base_url, timeout)
        self.keep_alive = keep_alive
        # think_mode "false" sends think=false; "omit" never sends the field.
        self.send_think = think_mode == "false"

    def probe(self, model):
        """Runtime version (GET /api/version) and the build's quantisation (POST /api/show)."""
        version = (self.http.try_request("GET", "/api/version") or {}).get("version")
        show = self.http.try_request("POST", "/api/show", {"model": model}) or {}
        return {"runtime_version": version, "model_file": None,
                "quant": (show.get("details") or {}).get("quantization_level"), "model": model}

    def payload(self, model, messages, schema, temperature, seed, num_predict, num_ctx, sampler, schema_name):
        """The /api/chat body. Identical to doc 44's when no sampler override is given."""
        options = {"temperature": temperature, "num_ctx": num_ctx, "seed": seed, "num_predict": num_predict}
        options.update({k: v for k, v in sampler.items() if v is not None})
        body = {"model": model, "messages": messages, "stream": False, "keep_alive": self.keep_alive,
                "options": options}
        if schema is not None:
            body["format"] = schema  # grammar-constrained decoding against the item's schema
        if self.send_think:
            body["think"] = False
        return body

    def chat(self, body):
        """Send one call; return a backend-neutral result dict (see module docs)."""

        def stop_think():
            self.send_think = False

        resp, error, sent = _post_with_retries(self.http, "/api/chat", body, "think", ("think",), stop_think)
        r = resp or {}
        msg = r.get("message") or {}
        return {
            "error": error, "think_sent": "think" in sent,
            "content": msg.get("content", "") if resp else "",
            "thinking_chars": len(msg.get("thinking") or ""),
            "prompt_eval_count": r.get("prompt_eval_count"), "eval_count": r.get("eval_count"),
            "eval_duration": r.get("eval_duration"), "prompt_eval_duration": r.get("prompt_eval_duration"),
            "load_duration": r.get("load_duration"), "total_duration": r.get("total_duration"),
            "done_reason": r.get("done_reason"), "extra": {},
        }


# ── llama.cpp llama-server ───────────────────────────────────────────────────

class LlamaServerBackend:
    """llama-server's OpenAI-compatible /v1/chat/completions (stream=false).

    The context size is a *server* setting (``-c``), not a per-request option,
    so ``probe`` reads the effective value from ``GET /props`` and run.py
    records that, not the requested one.
    """

    name = "llamacpp"

    def __init__(self, base_url, timeout, think_mode, api_key=None):
        # llama-server checks "Authorization: Bearer <key>" when started with --api-key.
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.http = _Http(base_url, timeout, headers)
        self.send_think = think_mode == "false"

    def wait_ready(self, max_wait_s=180.0):
        """Poll GET /health until the model is loaded (200) or `max_wait_s` passes.

        llama-server answers 503 while it is still loading weights; a runner
        started right after the server would otherwise fail its first calls.
        """
        deadline = time.monotonic() + max_wait_s
        last = None
        while time.monotonic() < deadline:
            try:
                self.http.request("GET", "/health", timeout=5)
                return True, None
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}"
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                last = f"{type(e).__name__}: {e}"
            time.sleep(1.0)
        return False, last

    def _template_probe(self):
        """Does the chat template react to enable_thinking?

        Renders one tiny conversation through POST /apply-template with
        enable_thinking false and true. Different prompts mean the template
        reads the variable, so sending it has an effect. Returns (bool or None,
        tail of the thinking-off prompt) for the record; None means the probe
        could not run.
        """
        msgs = [{"role": "user", "content": "ping"}]
        off = self.http.try_request("POST", "/apply-template",
                                    {"messages": msgs, "chat_template_kwargs": {"enable_thinking": False}})
        on = self.http.try_request("POST", "/apply-template",
                                   {"messages": msgs, "chat_template_kwargs": {"enable_thinking": True}})
        if not off or not on or "prompt" not in off or "prompt" not in on:
            return None, None
        return off["prompt"] != on["prompt"], off["prompt"][-80:]

    def probe(self, model):
        """What the server reports about itself: build, model file, quant, context, sampler defaults."""
        props = self.http.try_request("GET", "/props") or {}
        models = self.http.try_request("GET", "/v1/models") or {}
        gen = props.get("default_generation_settings") or {}
        params = gen.get("params") or {}
        # Keep only the file name: the local path would leak a user name into results.
        model_file = os.path.basename(props.get("model_path") or "") or None
        served = [m.get("id") for m in (models.get("data") or []) if isinstance(m, dict)]
        changes, tail = self._template_probe()
        return {
            "runtime_version": props.get("build_info"),
            "model_file": model_file,
            "quant": quant_from_filename(model_file),
            "model": model or (os.path.splitext(model_file)[0] if model_file else (served[0] if served else None)),
            "served_model_ids": served,
            "n_ctx": gen.get("n_ctx"),
            "total_slots": props.get("total_slots"),
            "server_sampler_defaults": {k: params.get(k) for k in ("temperature",) + SAMPLER_KEYS},
            "thinking_kwarg_changes_prompt": changes,
            "template_tail_thinking_off": tail,
        }

    def payload(self, model, messages, schema, temperature, seed, num_predict, num_ctx, sampler, schema_name):
        """The /v1/chat/completions body.

        ``num_ctx`` is accepted for interface parity but not sent: llama-server
        fixes the context at start-up (``-c``). ``max_tokens`` is the output cap.
        """
        body = {"messages": messages, "stream": False, "temperature": temperature, "seed": seed,
                "max_tokens": num_predict}
        if model:
            # In router mode llama-server picks the model by this name; a single-model server ignores it.
            body["model"] = model
        body.update({k: v for k, v in sampler.items() if v is not None})
        if schema is not None:
            body["response_format"] = {"type": "json_schema",
                                       "json_schema": {"name": schema_name, "schema": schema, "strict": True}}
        if self.send_think:
            body["chat_template_kwargs"] = {"enable_thinking": False}
        return body

    def chat(self, body):
        """Send one call; return a backend-neutral result dict (see module docs)."""

        def stop_kwargs():
            self.send_think = False

        resp, error, sent = _post_with_retries(self.http, "/v1/chat/completions", body, "chat_template_kwargs",
                                               ("chat_template_kwargs", "enable_thinking"), stop_kwargs)
        r = resp or {}
        choice = (r.get("choices") or [{}])[0] or {}
        msg = choice.get("message") or {}
        content = msg.get("content") or ""
        # Thinking can come back parsed (reasoning_content, llama-server's default
        # --reasoning-format) or raw inside <think> tags; count both, so a
        # template that ignores enable_thinking shows up in thinking_chars.
        in_content = sum(len(t) for t in re.findall(r"<think>(.*?)</think>", content, re.S))
        usage = r.get("usage") or {}
        timings = r.get("timings") or {}
        prompt_ms, predicted_ms = timings.get("prompt_ms"), timings.get("predicted_ms")

        def ns(ms):
            return int(round(ms * 1e6)) if isinstance(ms, (int, float)) else None

        return {
            "error": error, "think_sent": "chat_template_kwargs" in sent,
            "content": content,
            "thinking_chars": len(msg.get("reasoning_content") or "") + in_content,
            # usage counts the whole prompt; timings.prompt_n counts only the part not reused from the
            # prompt cache, so usage is the figure comparable with Ollama's prompt_eval_count.
            "prompt_eval_count": usage.get("prompt_tokens"), "eval_count": usage.get("completion_tokens"),
            "eval_duration": ns(predicted_ms), "prompt_eval_duration": ns(prompt_ms),
            "load_duration": None,
            "total_duration": ns((prompt_ms or 0) + (predicted_ms or 0)) if timings else None,
            "done_reason": choice.get("finish_reason"),
            "extra": {
                "usage": usage or None,
                "timings": {k: timings.get(k) for k in ("cache_n", "prompt_n", "prompt_ms", "predicted_n",
                                                         "predicted_ms", "predicted_per_second")} if timings else None,
                "system_fingerprint": r.get("system_fingerprint"),
            },
        }
