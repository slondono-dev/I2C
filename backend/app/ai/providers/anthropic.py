"""Anthropic (Claude) provider used mainly during development; replaceable by any other."""

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
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnauthorized,
    ProviderUnavailable,
)

# Rough blended cost for small models (USD per 1k tokens), used for cost tracking only.
_COST_PER_1K = {"input": 0.001, "output": 0.005}


class AnthropicProvider(AIProvider):
    name = "anthropic"
    display_name = "Anthropic"
    capabilities = {Capability.TEXT, Capability.VISION}
    cost_score = 0.4
    quality_score = 0.95
    latency_score = 0.6
    is_free = False
    supports_json = False

    def __init__(self, api_key: str, model: str, timeout: float = 45.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    async def _call(self, request: AIRequest, with_image: bool) -> AIRawResponse:
        if not self.configured:
            raise ProviderUnavailable("anthropic not configured")
        content: list[dict] = []
        if with_image and request.image is not None:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": request.image_mime,
                        "data": base64.b64encode(request.image).decode(),
                    },
                }
            )
        prompt = request.prompt
        if request.json_output:
            prompt += "\nResponde únicamente con JSON válido, sin texto adicional."
        content.append({"type": "text", "text": prompt})
        body: dict = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": "user", "content": content}],
        }
        if request.system:
            body["system"] = request.system
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages", json=body, headers=headers
                )
        except httpx.TimeoutException as exc:
            raise ProviderTimeout("anthropic timeout") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailable("anthropic network error") from exc
        if resp.status_code in (401, 403):
            raise ProviderUnauthorized("anthropic unauthorized", resp.status_code)
        if resp.status_code == 429:
            raise ProviderRateLimited("anthropic rate limited", 429)
        if resp.status_code >= 500 or resp.status_code == 529:
            raise ProviderUnavailable("anthropic unavailable", resp.status_code)
        if resp.status_code >= 400:
            raise ProviderError(f"anthropic error {resp.status_code}", resp.status_code)
        payload = resp.json()
        text = "".join(
            b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text"
        )
        usage = payload.get("usage") or {}
        in_tok, out_tok = int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)
        cost = in_tok / 1000 * _COST_PER_1K["input"] + out_tok / 1000 * _COST_PER_1K["output"]
        return AIRawResponse(
            text=text,
            model=payload.get("model") or self.model,
            input_units=in_tok,
            output_units=out_tok,
            estimated_cost=round(cost, 6),
            meta={"latency_ms": int((time.perf_counter() - start) * 1000)},
        )

    async def text(self, request: AIRequest) -> AIRawResponse:
        return await self._call(request, with_image=False)

    async def vision(self, request: AIRequest) -> AIRawResponse:
        return await self._call(request, with_image=True)
