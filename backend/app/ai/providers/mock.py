"""Deterministic mock provider: lets the whole app run with no external API."""

from __future__ import annotations

import json

from app.ai.providers.base import AIProvider
from app.ai.types import AIRawResponse, AIRequest, AITask, Capability


class MockAIProvider(AIProvider):
    name = "mock"
    display_name = "Mock"
    capabilities = {Capability.TEXT, Capability.VISION, Capability.IMAGE_EDIT}
    cost_score = 1.0
    quality_score = 0.1
    latency_score = 1.0
    is_mock = True
    supports_json = True

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = 0

    async def vision(self, request: AIRequest) -> AIRawResponse:
        self.calls += 1
        if self.fail:
            from app.ai.types import ProviderUnavailable

            raise ProviderUnavailable("mock failure")
        data = {
            "category": "camiseta",
            "subcategory": "camiseta básica",
            "color": "ivory",
            "gender": "mujer",
            "sleeve": "corta",
            "neck": "redondo",
            "fit": "regular",
            "pattern": "liso",
            "material": None,
            "confidence": 0.5,
        }
        return AIRawResponse(text=json.dumps(data), model="mock-vision")

    async def text(self, request: AIRequest) -> AIRawResponse:
        self.calls += 1
        if self.fail:
            from app.ai.types import ProviderUnavailable

            raise ProviderUnavailable("mock failure")
        attrs = request.params.get("attributes", {})
        category = (attrs.get("category") or "Producto").capitalize()
        color = (attrs.get("color") or "").capitalize()
        if request.task == AITask.PRODUCT_NAME:
            return AIRawResponse(text=f"{category} Essential {color}".strip(), model="mock-text")
        return AIRawResponse(
            text=(
                f"{category} {color} de corte {attrs.get('fit') or 'regular'}, "
                "ideal para el día a día. Prenda versátil, cómoda y fácil de combinar."
            ).strip(),
            model="mock-text",
        )

    async def image_edit(self, request: AIRequest) -> AIRawResponse:
        self.calls += 1
        # Return original bytes untouched: a safe no-op for development.
        return AIRawResponse(image=request.image, image_mime=request.image_mime, model="mock-image")
