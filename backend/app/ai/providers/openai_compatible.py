"""Generic OpenAI-compatible chat provider (works with 9Router, OpenRouter, vLLM, Ollama, ...)."""

from __future__ import annotations

import base64
import time

import httpx

from app.ai.providers.base import AIProvider
from app.ai.types import (
    AIRawResponse,
    AIRequest,
    Capability,
    ProviderError,
    ProviderQuotaExceeded,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnauthorized,
    ProviderUnavailable,
)


class OpenAICompatibleProvider(AIProvider):
    name = "openai_compatible"
    display_name = "OpenAI-compatible"
    capabilities = {Capability.TEXT, Capability.VISION}
    cost_score = 0.6
    quality_score = 0.75
    latency_score = 0.6
    is_free = False
    supports_json = True

    def __init__(
        self,
        base_url: str,
        api_key: str,
        text_model: str,
        vision_model: str = "",
        timeout: float = 45.0,
        extra_headers: dict[str, str] | None = None,
        cost_per_1k_tokens: float = 0.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.text_model = text_model
        self.vision_model = vision_model or text_model
        self.timeout = timeout
        self.extra_headers = extra_headers or {}
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.capabilities = {Capability.TEXT} | (
            {Capability.VISION} if self.vision_model else set()
        )

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.text_model)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _messages(self, request: AIRequest, with_image: bool) -> list[dict]:
        messages: list[dict] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        if with_image and request.image is not None:
            b64 = base64.b64encode(request.image).decode()
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": request.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{request.image_mime};base64,{b64}"},
                        },
                    ],
                }
            )
        else:
            messages.append({"role": "user", "content": request.prompt})
        return messages

    async def _chat(self, request: AIRequest, model: str, with_image: bool) -> AIRawResponse:
        if not self.configured:
            raise ProviderUnavailable(f"{self.name} not configured")
        body: dict = {
            "model": model,
            "messages": self._messages(request, with_image),
            "max_tokens": request.max_tokens,
            "temperature": request.params.get("temperature", 0.3),
        }
        if request.json_output and self.supports_json:
            body["response_format"] = {"type": "json_object"}
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions", json=body, headers=self._headers()
                )
        except httpx.TimeoutException as exc:
            raise ProviderTimeout(f"{self.name} timeout") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(
                f"{self.name} network error: {exc.__class__.__name__}"
            ) from exc
        self._raise_for_status(resp)
        payload = resp.json()
        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.name} malformed response") from exc
        usage = payload.get("usage") or {}
        in_tok = int(usage.get("prompt_tokens") or 0)
        out_tok = int(usage.get("completion_tokens") or 0)
        cost = (in_tok + out_tok) / 1000 * self.cost_per_1k_tokens
        return AIRawResponse(
            text=text if isinstance(text, str) else str(text),
            model=payload.get("model") or model,
            input_units=in_tok,
            output_units=out_tok,
            estimated_cost=cost,
            meta={"latency_ms": int((time.perf_counter() - start) * 1000)},
        )

    def _raise_for_status(self, resp: httpx.Response) -> None:
        code = resp.status_code
        if code < 400:
            return
        snippet = resp.text[:200]
        if code in (401, 403):
            raise ProviderUnauthorized(f"{self.name} unauthorized", code)
        if code == 429:
            if "quota" in snippet.lower() or "billing" in snippet.lower():
                raise ProviderQuotaExceeded(f"{self.name} quota exceeded", code)
            raise ProviderRateLimited(f"{self.name} rate limited", code)
        if code == 402:
            raise ProviderQuotaExceeded(f"{self.name} payment required", code)
        if code in (408, 502, 503, 504):
            raise ProviderUnavailable(f"{self.name} upstream error {code}", code)
        raise ProviderError(f"{self.name} error {code}", code)

    async def text(self, request: AIRequest) -> AIRawResponse:
        return await self._chat(request, self.text_model, with_image=False)

    async def vision(self, request: AIRequest) -> AIRawResponse:
        return await self._chat(request, self.vision_model, with_image=True)

    async def health_check(self) -> bool:
        if not self.configured:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers())
            return resp.status_code < 500
        except httpx.HTTPError:
            return False
