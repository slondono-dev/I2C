"""Local provider: runs on the server with no network.

- Background removal via `rembg` when installed (open source, U2Net/BiRefNet models).
- Heuristic product recognition (dominant color) so recognition never fully fails.
- Template-based naming/description as a last-resort text fallback.
"""

from __future__ import annotations

import asyncio
import json
from io import BytesIO

from PIL import Image

from app.ai.providers.base import AIProvider
from app.ai.types import AIRawResponse, AIRequest, AITask, Capability, ProviderUnavailable
from app.core.config import get_settings

try:  # optional heavy dependency
    from rembg import remove as _rembg_remove  # type: ignore

    REMBG_AVAILABLE = True
except Exception:  # pragma: no cover - depends on environment
    _rembg_remove = None
    REMBG_AVAILABLE = False


_COLOR_NAMES: list[tuple[str, tuple[int, int, int]]] = [
    ("negro", (20, 20, 20)),
    ("blanco", (245, 245, 245)),
    ("ivory", (255, 250, 235)),
    ("gris", (128, 128, 128)),
    ("rojo", (200, 30, 40)),
    ("vino", (110, 20, 40)),
    ("rosa", (240, 150, 180)),
    ("naranja", (240, 130, 40)),
    ("amarillo", (240, 220, 60)),
    ("verde", (50, 140, 70)),
    ("verde oliva", (110, 120, 60)),
    ("azul", (40, 80, 180)),
    ("azul marino", (25, 35, 80)),
    ("celeste", (140, 190, 235)),
    ("morado", (120, 60, 160)),
    ("beige", (215, 195, 160)),
    ("café", (110, 70, 40)),
]


def dominant_color_name(data: bytes) -> tuple[str, float]:
    img = Image.open(BytesIO(data)).convert("RGBA")
    img.thumbnail((64, 64))
    w, h = img.size
    # Sample the centre region, where the product usually is.
    box = (w // 4, h // 4, max(w // 4 + 1, 3 * w // 4), max(h // 4 + 1, 3 * h // 4))
    region = img.crop(box)
    pixels = [p for p in list(region.getdata()) if p[3] > 10]  # type: ignore[call-overload]
    if not pixels:
        return "desconocido", 0.0
    r = sum(p[0] for p in pixels) / len(pixels)
    g = sum(p[1] for p in pixels) / len(pixels)
    b = sum(p[2] for p in pixels) / len(pixels)
    best, best_d = "desconocido", float("inf")
    for name, (cr, cg, cb) in _COLOR_NAMES:
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_d:
            best, best_d = name, d
    confidence = max(0.2, 1 - (best_d**0.5) / 255)
    return best, round(confidence * 0.5, 2)  # heuristic → low confidence


class LocalProvider(AIProvider):
    name = "local"
    display_name = "Local"
    capabilities = {Capability.IMAGE_EDIT, Capability.VISION, Capability.TEXT}
    cost_score = 1.0
    quality_score = 0.35
    latency_score = 0.7
    supports_json = True

    async def image_edit(self, request: AIRequest) -> AIRawResponse:
        if request.task != AITask.BACKGROUND_REMOVAL:
            raise NotImplementedError
        if not REMBG_AVAILABLE or request.image is None:
            raise ProviderUnavailable("rembg not installed")
        if not get_settings().local_rembg_enabled:
            raise ProviderUnavailable("local rembg disabled")
        loop = asyncio.get_running_loop()
        out = await loop.run_in_executor(None, _rembg_remove, request.image)
        return AIRawResponse(image=bytes(out), image_mime="image/png", model="rembg-u2net")

    async def vision(self, request: AIRequest) -> AIRawResponse:
        if request.image is None:
            raise ProviderUnavailable("no image")
        color, conf = dominant_color_name(request.image)
        data = {"category": None, "color": color, "confidence": conf, "source": "heuristic"}
        return AIRawResponse(text=json.dumps(data), model="local-heuristic")

    async def text(self, request: AIRequest) -> AIRawResponse:
        attrs = request.params.get("attributes", {})
        category = (attrs.get("category") or "Producto").strip().capitalize()
        color = (attrs.get("color") or "").strip().capitalize()
        if request.task == AITask.PRODUCT_NAME:
            name = " ".join(x for x in [category, color] if x)
            return AIRawResponse(text=name, model="local-template")
        parts = [category]
        if color:
            parts.append(f"en tono {color.lower()}")
        if attrs.get("fit"):
            parts.append(f"de corte {attrs['fit']}")
        if attrs.get("material"):
            parts.append(f"en {attrs['material']}")
        text = " ".join(parts) + ". Pieza versátil, cómoda y fácil de combinar."
        return AIRawResponse(text=text, model="local-template")
