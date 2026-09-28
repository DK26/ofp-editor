"""Model clients: an OpenAI-compatible chat client (llama-server or a cloud endpoint)
and a mock that replays reference solutions to prove the pipeline end to end.

Only the standard library is used (urllib), so the harness runs on a bare Python.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class Reply:
    content: str
    prompt_tokens: int | None = None
    cached_tokens: int | None = None
    completion_tokens: int | None = None
    gen_ms: int = 0
    finish_reason: str | None = None
    timings: dict = field(default_factory=dict)
    error: str | None = None  # infrastructure error (endpoint unreachable, HTTP 5xx)
    reasoning_chars: int = 0  # length of message.reasoning_content (must stay 0 with thinking off)


@dataclass
class Sampler:
    temperature: float = 0.6
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None
    max_tokens: int = 3072
    llama_extras: bool = True  # send top_k / min_p / cache_prompt (llama-server fields)
    # Sent as `chat_template_kwargs` (llama-server), e.g. {"enable_thinking": false} for
    # thinking off (doc 49 section 1.4); None sends nothing.
    template_kwargs: dict | None = None
    # Neutral penalties sent explicitly so a GGUF's embedded sampler defaults cannot leak in.
    neutral_penalties: bool = True


class OpenAIClient:
    """POST {base_url}/chat/completions, non-streaming.

    llama-server returns `timings` (prompt_n = uncached prompt tokens evaluated,
    cache_n = prompt tokens reused from the cache, predicted_n, prompt_ms,
    predicted_ms); cloud endpoints return `usage` (with
    `prompt_tokens_details.cached_tokens` where supported). Both are recorded.
    """

    def __init__(self, base_url: str, model: str, api_key: str | None = None, timeout: float = 600.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get("RWM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.timeout = timeout

    def _post(self, url: str, body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def chat(self, messages: list[dict], sampler: Sampler, seed: int) -> Reply:
        body: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": sampler.temperature,
            "max_tokens": sampler.max_tokens,
            "seed": seed,
            "stream": False,
        }
        if sampler.top_p is not None:
            body["top_p"] = sampler.top_p
        if sampler.llama_extras:
            body["cache_prompt"] = True
            if sampler.top_k is not None:
                body["top_k"] = sampler.top_k
            if sampler.min_p is not None:
                body["min_p"] = sampler.min_p
            if sampler.neutral_penalties:
                body["repeat_penalty"] = 1.0
        if sampler.neutral_penalties:
            body["presence_penalty"] = 0.0
            body["frequency_penalty"] = 0.0
        if sampler.template_kwargs:
            body["chat_template_kwargs"] = sampler.template_kwargs
        t0 = time.monotonic()
        try:
            data = self._post(f"{self.base_url}/chat/completions", body)
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
            return Reply(content="", gen_ms=int((time.monotonic() - t0) * 1000), error=f"{type(e).__name__}: {e}")
        ms = int((time.monotonic() - t0) * 1000)
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        usage = data.get("usage") or {}
        timings = data.get("timings") or {}
        cached = timings.get("cache_n")
        if cached is None:
            cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
        return Reply(
            content=msg.get("content") or "",
            prompt_tokens=usage.get("prompt_tokens"),
            cached_tokens=cached,
            completion_tokens=usage.get("completion_tokens"),
            gen_ms=ms,
            finish_reason=choice.get("finish_reason"),
            timings=timings,
            reasoning_chars=len(msg.get("reasoning_content") or ""),
        )

    def tokenize_count(self, text: str) -> int | None:
        """Exact token count via llama-server's /tokenize (None if unavailable)."""
        root = self.base_url[: -len("/v1")] if self.base_url.endswith("/v1") else self.base_url
        try:
            data = self._post(f"{root}/tokenize", {"content": text})
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
            return None
        toks = data.get("tokens")
        return len(toks) if isinstance(toks, list) else None


class MockClient:
    """Replays the task's reference solution for the episode's variant.

    Modes (per episode, by round):
      ref            round 0 returns the reference (proves compile/test/record paths)
      fail-first     round 0 returns the reference with a deliberate compile error,
                     round 1 the reference (proves diagnostics feedback and repair)
      no-code-first  round 0 returns prose without a code block (format failure),
                     round 1 the reference
      mutant         round 0 returns the first trap mutant if the task has one (to
                     exercise hidden/trap scoring), later rounds the reference
    """

    def __init__(self, mode: str):
        self.mode = mode
        self.current: dict = {}

    def bind(self, reference: str, mutant: str | None) -> None:
        self.current = {"reference": reference, "mutant": mutant}

    def chat(self, messages: list[dict], sampler: Sampler, seed: int) -> Reply:
        round_no = sum(1 for m in messages if m["role"] == "assistant")
        ref = self.current["reference"]
        content = f"```rust\n{ref}```"
        if round_no == 0:
            if self.mode == "fail-first":
                broken = 'compile_error!("mock: deliberate compile error for the feedback-loop check");\n' + ref
                content = f"```rust\n{broken}```"
            elif self.mode == "no-code-first":
                content = "Here is my plan: build the mission, then export it."
            elif self.mode == "mutant" and self.current.get("mutant"):
                content = f"```rust\n{self.current['mutant']}```"
        prompt_chars = sum(len(m["content"]) for m in messages)
        return Reply(
            content=content,
            prompt_tokens=prompt_chars // 4,
            cached_tokens=0,
            completion_tokens=len(content) // 4,
            gen_ms=0,
            finish_reason="stop",
        )

    def tokenize_count(self, text: str) -> int | None:
        return None
