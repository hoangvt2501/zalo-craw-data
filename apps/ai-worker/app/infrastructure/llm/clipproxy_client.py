from __future__ import annotations

import json
import re
import time

import httpx


def _chat_completions_url(base_url: str) -> str:
    clean = base_url.rstrip("/")
    if clean.endswith("/chat/completions"):
        return clean
    if clean.endswith("/v1"):
        return f"{clean}/chat/completions"
    return f"{clean}/v1/chat/completions"


def clean_model_json(raw: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", raw or "", flags=re.I)
    text = re.sub(r"```json\s*", "", text, flags=re.I)
    text = text.replace("```", "")
    return text.strip()


class ClipProxyClient:
    def __init__(self, base_url: str, api_key: str, retry_max: int = 3, retry_delay_ms: int = 10000):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.retry_max = retry_max
        self.retry_delay_ms = retry_delay_ms
        self.chat_url = _chat_completions_url(base_url)

    def chat_text(self, *, model: str, messages: list[dict], temperature: float = 0) -> str:
        last_error = None
        for attempt in range(1, self.retry_max + 2):
            started = time.perf_counter()
            try:
                response = httpx.post(
                    self.chat_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "model": model,
                        "stream": False,
                        "temperature": temperature,
                        "messages": messages,
                    },
                    timeout=90,
                )
                latency_ms = int((time.perf_counter() - started) * 1000)

                if response.status_code == 429 or response.status_code >= 500:
                    last_error = RuntimeError(f"LLM API {response.status_code} latency={latency_ms}ms")
                    if attempt <= self.retry_max:
                        time.sleep((self.retry_delay_ms * attempt) / 1000)
                        continue
                    raise last_error

                if response.status_code < 200 or response.status_code >= 300:
                    raise RuntimeError(f"LLM API {response.status_code}: {response.text[:300]}")

                body = response.json()
                return body.get("choices", [{}])[0].get("message", {}).get("content", "")
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt <= self.retry_max:
                    time.sleep((self.retry_delay_ms * attempt) / 1000)
                    continue
                raise RuntimeError(f"LLM request failed: {exc}") from exc

        raise RuntimeError(f"LLM request failed: {last_error}")

    def chat_json(self, *, model: str, messages: list[dict], temperature: float = 0) -> dict:
        raw = self.chat_text(model=model, messages=messages, temperature=temperature)
        return json.loads(clean_model_json(raw))
