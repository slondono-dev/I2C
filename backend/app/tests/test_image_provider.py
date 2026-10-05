import asyncio
import base64
import json

import httpx
import pytest

from app.ai.orchestrator import AIOrchestrator
from app.ai.providers.openai_image import OpenAICompatibleImageProvider
from app.ai.types import AIRequest, AITask, Capability, ProviderRateLimited
from app.tests.conftest import make_image


def _provider(handler):
    return OpenAICompatibleImageProvider(
        base_url="https://gw.example/v1",
        api_key="k",
        model="img-1",
        transport=httpx.MockTransport(handler),
    )


def test_edit_returns_b64_image_and_tracks_cost():
    seen = {}

    def handler(request: httpx.Request):
        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(
            200, json={"data": [{"b64_json": base64.b64encode(make_image()).decode()}]}
        )

    p = _provider(handler)
    p.cost_per_image = 0.02
    orch = AIOrchestrator([p], routing={AITask.VIRTUAL_MODEL: ["openai_image"]})
    res = asyncio.run(orch.run(AITask.VIRTUAL_MODEL, {"image": make_image(), "style": "studio"}))
    assert res.success and res.provider == "openai_image" and res.cost == 0.02
    assert seen["path"].endswith("/images/edits") and seen["auth"] == "Bearer k"
    assert res.data["image"][:3] == b"\xff\xd8\xff"


def test_rate_limit_maps_to_retryable_error():
    p = _provider(lambda r: httpx.Response(429, text="slow down"))
    req = AIRequest(
        task=AITask.VIRTUAL_MODEL, capability=Capability.IMAGE_GENERATION, image=make_image()
    )
    with pytest.raises(ProviderRateLimited):
        asyncio.run(p.image(req))


def test_unconfigured_provider_is_skipped_in_routing():
    p = OpenAICompatibleImageProvider(base_url="", api_key="", model="")
    orch = AIOrchestrator([p], routing={AITask.VIRTUAL_MODEL: ["openai_image"]})
    res = asyncio.run(orch.run(AITask.VIRTUAL_MODEL, {"image": make_image()}))
    assert res.success is False and res.error == "no provider available"


def test_generation_without_image_uses_generations_endpoint():
    def handler(request: httpx.Request):
        body = json.loads(request.content)
        assert request.url.path.endswith("/images/generations") and body["model"] == "img-1"
        return httpx.Response(
            200, json={"data": [{"b64_json": base64.b64encode(make_image()).decode()}]}
        )

    p = _provider(handler)
    raw = asyncio.run(
        p.image(
            AIRequest(task=AITask.VIRTUAL_MODEL, capability=Capability.IMAGE_GENERATION, prompt="x")
        )
    )
    assert raw.image and raw.model == "img-1"
