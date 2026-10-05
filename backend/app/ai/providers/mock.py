"""Deterministic mock provider: lets the whole app run with no external API."""

from __future__ import annotations

import json

from app.ai.providers.base import AIProvider
from app.ai.types import AIRawResponse, AIRequest, AITask, Capability


class MockAIProvider(AIProvider):
    name = "mock"
    display_name = "Mock"
    capabilities = {
        Capability.TEXT,
        Capability.VISION,
        Capability.IMAGE_EDIT,
        Capability.IMAGE_GENERATION,
        Capability.VIDEO,
    }
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

    async def image(self, request: AIRequest) -> AIRawResponse:
        """Virtual model mock: returns the garment on a neutral studio background."""
        self.calls += 1
        from io import BytesIO

        from PIL import Image

        garment = Image.open(BytesIO(request.image or b"")).convert("RGBA")
        canvas = Image.new(
            "RGBA", (max(garment.width, 600), max(garment.height, 800) + 120), (238, 236, 232, 255)
        )
        canvas.alpha_composite(garment, ((canvas.width - garment.width) // 2, 60))
        out = BytesIO()
        canvas.convert("RGB").save(out, format="JPEG", quality=88)
        return AIRawResponse(image=out.getvalue(), image_mime="image/jpeg", model="mock-image-gen")

    async def video(self, request: AIRequest) -> AIRawResponse:
        """Video mock: a short animated GIF (zoom) so the pipeline can be exercised end to end."""
        self.calls += 1
        from io import BytesIO

        from PIL import Image

        base = Image.open(BytesIO(request.image or b"")).convert("RGB")
        base.thumbnail((480, 640))
        frames = []
        for i in range(12):
            z = 1 + i * 0.015
            w, h = int(base.width / z), int(base.height / z)
            box = (
                (base.width - w) // 2,
                (base.height - h) // 2,
                (base.width + w) // 2,
                (base.height + h) // 2,
            )
            frames.append(base.crop(box).resize(base.size))
        out = BytesIO()
        frames[0].save(
            out, format="GIF", save_all=True, append_images=frames[1:], duration=120, loop=0
        )
        return AIRawResponse(image=out.getvalue(), image_mime="image/gif", model="mock-video")
