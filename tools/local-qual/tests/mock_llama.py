#!/usr/bin/env python3
"""Mock llama-server for testing the local-qual logprob Pick mode without a model (standard library only).

What it serves
--------------
* ``GET /health`` (200), ``GET /props`` (build, model file, context, sampler defaults), ``GET /v1/models``.
* ``POST /apply-template``: a ChatML-style rendering of the messages ("<|im_start|>role\\ncontent<|im_end|>") plus the
  generation prompt, with an empty think block when ``chat_template_kwargs.enable_thinking`` is false, like the
  Qwen3.5 template. ``reject_kwargs`` answers 400 naming the field instead (an old build).
* ``POST /completion``: parses the lettered menu out of the prompt ("A) label: desc" ... "X) label"), asks
  ``dist_fn(menu, prompt)`` for the next-token list [(token, prob), ...] and returns its top ``n_probs`` in the
  shape ``shape`` names (``menu`` maps each letter to its line text, "label: desc" or the escape label): ``native``
  (completion_probabilities[0].top_logprobs with id/token/bytes/logprob), ``native-post`` (top_probs/prob),
  ``native-old`` (probs with tok_str/prob), ``openai`` (choices[0].logprobs.content[0].top_logprobs) or
  ``openai-legacy`` (choices[0].logprobs.top_logprobs[0] as a {token: logprob} dict). Like a real server, whose
  softmax covers the whole vocabulary, the list always has ``n_probs`` entries: ``pad`` (on by default) fills it up
  with non-letter tokens of probability 0, sent as logprob -3.4028235e38 (llama-server's ``logarithm(0)``, the
  lowest float, because JSON has no -inf). ``truncate`` = k lists only the top k (a server that samples on the
  backend, ``-bs``, and reports its candidate set; ``truncate_ping`` false spares the preflight). ``raw_response`` (a dict) replaces the whole body (adversarial
  tests); ``no_probs`` leaves the probabilities out (a server that ignores n_probs); ``fail_completion`` answers that
  many menu prompts with a 500 first, ``fail_nth`` the n-th menu prompt only (the one-token preflight is never
  failed). A token's ``bytes`` are its UTF-8 bytes, or ``token_bytes[token]`` when the test sets them (a token that
  ends inside a multi-byte character, whose ``token`` text llama-server cuts at the last whole character).
* ``POST /tokenize``: a toy tokenizer for the answer-prefix boundary check: greedy longest match over ``PIECES``
  plus ``extra_pieces`` (single characters otherwise), ids from a hash of the piece, ``{"tokens": [{"id", "piece"}]}``
  with ``with_pieces`` or bare ids without. ``no_tokenize`` answers 404 (a build without the endpoint).
  ``template_reply`` / ``tokenize_reply`` (any JSON value) replace the reply of /apply-template or /tokenize.
* ``POST /v1/chat/completions``: ``{"choice": chat_fn(body)}`` for a generate-mode run (the large model of a cascade).

Every request (path, parsed body) is appended to ``state.requests``.
"""
import hashlib
import json
import math
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MENU_LINE = re.compile(r"^([A-GX])\) (.*)$")
# llama-server's logarithm(0): the lowest finite float32, because nlohmann::json writes -inf as null.
LOWEST = -3.4028234663852886e38
# The toy tokenizer's multi-character pieces: the template's special tokens and the JSON pieces a byte-level BPE
# vocabulary splits the answer into ('{"', 'choice', '":', ' "', letter, '"}'). A test adds a piece such as ' "A' to
# model a vocabulary that merges the opening quote with the letter.
PIECES = ("<|im_start|>", "<|im_end|>", "<think>", "</think>", '{"', "choice", '":', ' "', '"}', "\n\n")


def menu_of(prompt):
    """{letter: line text after "L) "} of the lettered menu inside a rendered prompt ("label: desc", or the escape label)."""
    menu = {}
    for line in prompt.split("\n"):
        m = MENU_LINE.match(line)
        if m:
            menu[m.group(1)] = m.group(2)
    return menu


def default_dist(menu, prompt):
    return [("Hello", 0.6), (" there", 0.3), ("!", 0.1)]


class LState:
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = []
        self.shape = "native"
        self.dist_fn = default_dist
        self.reject_kwargs = False
        self.no_probs = False
        self.fail_completion = 0
        self.fail_nth = None
        self.menu_completions = 0
        self.raw_response = None
        self.chat_fn = lambda body: "A"
        self.pad = True
        self.truncate = None
        self.truncate_ping = True
        self.token_bytes = {}
        self.extra_pieces = ()
        self.no_tokenize = False
        self.template_reply = None
        self.tokenize_reply = None

    def reset(self):
        self.__init__()

    def paths(self, suffix):
        with self.lock:
            return [r for r in self.requests if r["path"] == suffix]


STATE = LState()


def render(messages, kwargs):
    out = "".join(f"<|im_start|>{m.get('role')}\n{m.get('content')}<|im_end|>\n" for m in messages)
    out += "<|im_start|>assistant\n"
    if isinstance(kwargs, dict) and kwargs.get("enable_thinking") is False:
        out += "<think>\n\n</think>\n\n"
    return out


def tokenize(text, extra=()):
    """Greedy longest-match tokenisation over PIECES + extra, one character otherwise; [(id, piece)]."""
    pieces = sorted(set(PIECES) | set(extra), key=len, reverse=True)
    out, i = [], 0
    while i < len(text):
        piece = next((p for p in pieces if text.startswith(p, i)), text[i])
        out.append((int(hashlib.sha256(piece.encode("utf-8")).hexdigest()[:6], 16), piece))
        i += len(piece)
    return out


def shaped(entries, shape, n_probs, truncate=None):
    """The /completion body for the top n_probs of `entries` in the requested shape."""
    top = sorted(entries, key=lambda tp: -tp[1])[:n_probs]
    if STATE.pad and len(top) < n_probs:
        # A real vocabulary always has n_probs tokens to list; the rest of this mock's vocabulary has probability 0.
        top += [(f"~pad{i}", 0.0) for i in range(n_probs - len(top))]
    if truncate is not None:
        top = top[:truncate]
    best = top[0][0] if top else ""

    def lp(p):
        return math.log(p) if p > 0 else LOWEST

    def raw(t):
        return list(STATE.token_bytes.get(t, t.encode("utf-8")))

    def text(t):
        # llama-server cuts the token text at the last whole UTF-8 character (validate_utf8); bytes keep it all.
        return bytes(raw(t)).decode("utf-8", "ignore") if t in STATE.token_bytes else t

    if shape == "native":
        probs = [{"id": 1000 + i, "token": text(t), "bytes": raw(t), "logprob": lp(p)} for i, (t, p) in enumerate(top)]
        cp = [{"id": 1000, "token": text(best), "bytes": raw(best), "logprob": probs[0]["logprob"],
               "top_logprobs": probs}]
        body = {"content": best, "completion_probabilities": cp}
    elif shape == "native-post":
        probs = [{"id": 1000 + i, "token": text(t), "bytes": raw(t), "prob": p} for i, (t, p) in enumerate(top)]
        body = {"content": best, "completion_probabilities": [{"id": 1000, "token": best, "prob": top[0][1],
                                                               "top_probs": probs}]}
    elif shape == "native-old":
        body = {"content": best, "completion_probabilities": [{"content": best,
                                                               "probs": [{"tok_str": t, "prob": p} for t, p in top]}]}
    elif shape == "openai":
        body = {"choices": [{"text": best, "index": 0, "finish_reason": "length", "logprobs": {"content": [
            {"id": 1000, "token": best, "logprob": lp(top[0][1]), "bytes": raw(best),
             "top_logprobs": [{"id": 1000 + i, "token": text(t), "logprob": lp(p), "bytes": raw(t)}
                              for i, (t, p) in enumerate(top)]}]}}]}
    elif shape == "openai-legacy":
        body = {"choices": [{"text": best, "index": 0, "logprobs": {
            "tokens": [best], "token_logprobs": [lp(top[0][1])], "top_logprobs": [{t: lp(p) for t, p in top}]}}]}
    else:
        raise ValueError(shape)
    return body


class Handler(BaseHTTPRequestHandler):
    server_version = "MockLlama/1.0"

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
        if self.path == "/apply-template":
            if STATE.reject_kwargs and "chat_template_kwargs" in body:
                return self._send(400, {"error": {"code": 400, "message": "unknown field chat_template_kwargs"}})
            if STATE.template_reply is not None:
                return self._send(200, STATE.template_reply)
            return self._send(200, {"prompt": render(body.get("messages") or [], body.get("chat_template_kwargs"))})
        if self.path == "/tokenize":
            if STATE.no_tokenize:
                return self._send(404, {"error": {"code": 404, "message": "not found"}})
            if STATE.tokenize_reply is not None:
                return self._send(200, STATE.tokenize_reply)
            toks = tokenize(str(body.get("content") or ""), STATE.extra_pieces)
            if body.get("with_pieces"):
                return self._send(200, {"tokens": [{"id": i, "piece": p} for i, p in toks]})
            return self._send(200, {"tokens": [i for i, _ in toks]})
        if self.path == "/completion":
            with STATE.lock:
                # Only menu prompts fail, so the run's one-token preflight ("ping") still passes.
                menu_prompt = "Options:" in str(body.get("prompt"))
                if menu_prompt:
                    STATE.menu_completions += 1
                fail = menu_prompt and (STATE.fail_completion > 0 or STATE.fail_nth == STATE.menu_completions)
                if fail and STATE.fail_completion > 0:
                    STATE.fail_completion -= 1
            if fail:
                return self._send(500, {"error": {"code": 500, "message": "mock failure"}})
            if STATE.raw_response is not None:
                return self._send(200, STATE.raw_response)
            prompt = body.get("prompt") or ""
            entries = STATE.dist_fn(menu_of(prompt), prompt)
            out = {"content": "", "tokens_predicted": 1, "tokens_evaluated": max(1, len(prompt) // 4),
                   "timings": {"cache_n": 0, "prompt_n": max(1, len(prompt) // 4), "prompt_ms": 12.5,
                               "predicted_n": 1, "predicted_ms": 2.5}}
            if not STATE.no_probs:
                out.update(shaped(entries, STATE.shape, int(body.get("n_probs") or 0) or len(entries),
                                  STATE.truncate if (menu_prompt or STATE.truncate_ping) else None))
            return self._send(200, out)
        if self.path == "/v1/chat/completions":
            content = json.dumps({"choice": STATE.chat_fn(body)})
            return self._send(200, {"choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                                                 "finish_reason": "stop"}],
                                    "usage": {"prompt_tokens": 200, "completion_tokens": 7, "total_tokens": 207},
                                    "timings": {"prompt_n": 200, "prompt_ms": 400.0, "predicted_n": 7,
                                                "predicted_ms": 100.0}})
        return self._send(404, {"error": {"code": 404, "message": "not found"}})


def start(port=0):
    """Start on 127.0.0.1 in a daemon thread; returns (server, base URL)."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"
