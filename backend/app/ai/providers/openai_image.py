"""OpenAI-compatible image provider (`/images/edits`, `/images/generations`).

Works with any gateway exposing the OpenAI images API (9Router, OpenRouter-like proxies,
self-hosted diffusion servers). Used for VIRTUAL_MODEL / PRODUCT_ENHANCEMENT. Disabled unless
OPENAI_IMAGE_BASE_URL and OPENAI_IMAGE_MODEL are set.
"""

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


class OpenAICompatibleImageProvider(AIProvider):
    name = "openai_image"
    display_name = "OpenAI-compatible images"
    capabilities = {Capability.IMAGE_GENERATION}
    cost_score = 0.5
    quality_score = 0.8
    latency_score = 0.3
    is_free = False

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 120.0,
        cost_per_image: float = 0.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.cost_per_image = cost_per_image
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def image(self, request: AIRequest) -> AIRawResponse:
        if not self.configured:
            raise ProviderUnavailable(f"{self.name} not configured")
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
                if request.image is not None:
                    resp = await client.post(
                        f"{self.base_url}/images/edits",
                        data={
                            "model": self.model,
                            "prompt": request.prompt,
                            "n": "1",
                            "size": request.params.get("size", "1024x1024"),
                        },
                        files={"image": ("image.png", request.image, request.image_mime)},
                        headers=self._headers(),
                    )
                else:
                    resp = await client.post(
                        f"{self.base_url}/images/generations",
                        json={
                            "model": self.model,
                            "prompt": request.prompt,
                            "n": 1,
                            "size": request.params.get("size", "1024x1024"),
                            "response_format": "b64_json",
                        },
                        headers={**self._headers(), "Content-Type": "application/json"},
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
            item = payload["data"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.name} malformed response") from exc
        if item.get("b64_json"):
            data = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout, transport=self._transport
                ) as client:
                    img = await client.get(item["url"])
                img.raise_for_status()
                data = img.content
            except httpx.HTTPError as exc:
                raise ProviderUnavailable(f"{self.name} could not download image") from exc
        else:
            raise ProviderError(f"{self.name} no image in response")
        return AIRawResponse(
            image=data,
            image_mime="image/png",
            model=self.model,
            output_units=1,
            estimated_cost=self.cost_per_image,
            meta={"latency_ms": int((time.perf_counter() - start) * 1000)},
        )

    def _raise_for_status(self, resp: httpx.Response) -> None:
        code = resp.status_code
        if code < 400:
            return
        if code in (401, 403):
            raise ProviderUnauthorized(f"{self.name} unauthorized", code)
        if code == 429:
            raise ProviderRateLimited(f"{self.name} rate limited", code)
        if code == 402:
            raise ProviderQuotaExceeded(f"{self.name} payment required", code)
        if code in (408, 502, 503, 504):
            raise ProviderUnavailable(f"{self.name} upstream error {code}", code)
        raise ProviderError(f"{self.name} error {code}", code)
