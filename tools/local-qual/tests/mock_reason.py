#!/usr/bin/env python3
"""Mock llama-server (and a minimal Ollama) for testing the local-qual scaffold arms without a model.

Standard library only; runs in-process on 127.0.0.1. Derived from the logprob tests' mock (same /apply-template
rendering and /completion probability shapes), extended for the scaffold arms.

What it serves
--------------
* ``GET /health``, ``GET /props``, ``GET /v1/models`` (llama-server probe), ``GET /api/version`` and
  ``POST /api/show`` (Ollama probe).
* ``POST /apply-template``: ChatML rendering of the messages plus the generation prompt. ``template_style`` "qwen"
  (default) adds the empty think block "<think>\\n\\n</think>\\n\\n" when ``chat_template_kwargs.enable_thinking`` is
  false, like the Qwen3 / Qwen3.5 templates; "plain" never renders a think block (a template without a think channel,
  as Granite 4.1's). ``reject_kwargs`` answers 400 naming the field.
* ``POST /completion``: with ``n_probs`` > 0 and ``n_predict`` 1 it is a letter-probability read: ``dist_fn(menu,
  prompt)`` gives [(token, prob), ...], returned in llama-server's native top_logprobs shape, padded to n_probs with
  probability-0 tokens (a real vocabulary always has n_probs tokens). With a ``grammar`` it is the prefill arm's
  continuation: ``complete_fn(prompt, body)`` returns the letter; the reply's content is the letter plus '"}'.
  ``fail_completion`` answers that many completion requests with a 500 first; ``no_probs`` leaves probabilities out.
* ``POST /v1/chat/completions`` and ``POST /api/chat``: the reply content is ``chat_fn(body)`` (a string), with usage
  and timings; the finish reason is ``finish_fn(body)`` ("stop" by default; "length" stands for a reply cut at its
  cap). ``fail_chat_nth`` answers the n-th chat request with a 500.

Every request (path, parsed body) is appended to ``STATE.requests``.
"""
import json
import math
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MENU_LINE = re.compile(r"^([A-GX])\) (.*)$")
LOWEST = -3.4028234663852886e38  # llama-server's logarithm(0): the lowest float32 (JSON has no -inf)


def menu_of(prompt):
    """{letter: line text after "L) "} of the lettered menu inside a prompt (the menu lines only, not the diff lines)."""
    out = {}
    for line in prompt.split("\n"):
        m = MENU_LINE.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def user_text(body):
    msgs = body.get("messages") or []
    return next((m.get("content") for m in reversed(msgs) if m.get("role") == "user"), "") or ""


def default_chat(body):
    """A mock model: the first menu letter for a Pick, "unclear" for every subq statement."""
    user = user_text(body)
    ids = re.findall(r"^(s\d+): ", user, flags=re.M)
    if ids:
        return json.dumps({sid: "unclear" for sid in ids})
    return json.dumps({"choice": "A"})


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = []
        self.template_style = "qwen"
        self.reject_kwargs = False
        self.dist_fn = lambda menu, prompt: [("A", 0.6), ("B", 0.3), ("X", 0.1)]
        self.complete_fn = lambda prompt, body: "A"
        self.chat_fn = default_chat
        self.finish_fn = lambda body: "stop"
        self.fail_completion = 0
        self.fail_chat_nth = None
        self.chat_count = 0
        self.no_probs = False

    def reset(self):
        self.__init__()

    def paths(self, path):
        with self.lock:
            return [r for r in self.requests if r["path"] == path]


STATE = State()


def render(messages, kwargs):
    out = "".join(f"<|im_start|>{m.get('role')}\n{m.get('content')}<|im_end|>\n" for m in messages)
    out += "<|im_start|>assistant\n"
    if STATE.template_style == "qwen" and isinstance(kwargs, dict) and kwargs.get("enable_thinking") is False:
        out += "<think>\n\n</think>\n\n"
    return out


def probs_body(entries, n_probs):
    top = sorted(entries, key=lambda tp: -tp[1])[:n_probs]
    top += [(f"~pad{i}", 0.0) for i in range(n_probs - len(top))]
    lp = [math.log(p) if p > 0 else LOWEST for _, p in top]
    probs = [{"id": 1000 + i, "token": t, "bytes": list(t.encode("utf-8")), "logprob": v}
             for i, ((t, _), v) in enumerate(zip(top, lp))]
    return {"content": top[0][0], "completion_probabilities": [
        {"id": 1000, "token": top[0][0], "bytes": list(top[0][0].encode("utf-8")), "logprob": lp[0],
         "top_logprobs": probs}]}


class Handler(BaseHTTPRequestHandler):
    server_version = "MockReason/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send(self, status, body):
        raw = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_GET(self):
        with STATE.lock:
            STATE.requests.append({"path": self.path, "body": None})
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        if self.path == "/props":
            return self._send(200, {"build_info": "mock-b1", "model_path": "/models/Mock-4B-Q4_K_M.gguf",
                                    "total_slots": 1, "default_generation_settings": {
                                        "n_ctx": 8192, "params": {"temperature": 0.8, "top_k": 40, "top_p": 0.95,
                                                                  "min_p": 0.05}}})
        if self.path == "/v1/models":
            return self._send(200, {"data": [{"id": "Mock-4B-Q4_K_M.gguf"}]})
        if self.path == "/api/version":
            return self._send(200, {"version": "mock-0.1"})
        return self._send(404, {"error": {"code": 404, "message": "not found"}})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError:
            body = None
        with STATE.lock:
            STATE.requests.append({"path": self.path, "body": body})
        if not isinstance(body, dict):
            return self._send(400, {"error": {"code": 400, "message": "bad json"}})
        if self.path == "/api/show":
            return self._send(200, {"details": {"quantization_level": "Q4_K_M"}})
        if self.path == "/apply-template":
            if STATE.reject_kwargs and "chat_template_kwargs" in body:
                return self._send(400, {"error": {"code": 400, "message": "unknown field chat_template_kwargs"}})
            return self._send(200, {"prompt": render(body.get("messages") or [], body.get("chat_template_kwargs"))})
        if self.path == "/completion":
            with STATE.lock:
                fail = STATE.fail_completion > 0 and "ping" != body.get("prompt")
                if fail:
                    STATE.fail_completion -= 1
            if fail:
                return self._send(500, {"error": {"code": 500, "message": "mock failure"}})
            prompt = body.get("prompt") or ""
            timings = {"cache_n": 0, "prompt_n": max(1, len(prompt) // 4), "prompt_ms": 12.5, "predicted_n": 1,
                       "predicted_ms": 2.5}
            if body.get("grammar"):
                letter = STATE.complete_fn(prompt, body)
                return self._send(200, {"content": letter + '"}', "tokens_predicted": 2,
                                        "tokens_evaluated": max(1, len(prompt) // 4), "stop_type": "eos",
                                        "timings": dict(timings, predicted_n=2, predicted_ms=5.0)})
            out = {"content": "", "tokens_predicted": 1, "tokens_evaluated": max(1, len(prompt) // 4),
                   "timings": timings}
            if not STATE.no_probs:
                out.update(probs_body(STATE.dist_fn(menu_of(prompt), prompt), int(body.get("n_probs") or 1)))
            return self._send(200, out)
        if self.path in ("/v1/chat/completions", "/api/chat"):
            with STATE.lock:
                STATE.chat_count += 1
                fail = STATE.fail_chat_nth == STATE.chat_count
            if fail:
                return self._send(500, {"error": {"code": 500, "message": "mock chat failure"}})
            content = STATE.chat_fn(body)
            finish = STATE.finish_fn(body)
            n_prompt = max(1, len(user_text(body)) // 4)
            n_out = max(1, len(content) // 4)
            if self.path == "/api/chat":
                return self._send(200, {"message": {"role": "assistant", "content": content}, "done": True,
                                        "done_reason": finish, "prompt_eval_count": n_prompt, "eval_count": n_out,
                                        "prompt_eval_duration": 40_000_000, "eval_duration": 20_000_000,
                                        "total_duration": 60_000_000, "load_duration": 1})
            return self._send(200, {"choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                                                 "finish_reason": finish}],
                                    "usage": {"prompt_tokens": n_prompt, "completion_tokens": n_out,
                                              "total_tokens": n_prompt + n_out},
                                    "timings": {"cache_n": 0, "prompt_n": n_prompt, "prompt_ms": 40.0,
                                                "predicted_n": n_out, "predicted_ms": 20.0}})
        return self._send(404, {"error": {"code": 404, "message": "not found"}})


def start(port=0):
    """Start on 127.0.0.1 in a daemon thread; returns (server, base URL)."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"
