import asyncio

import pytest

from app.ai.orchestrator import AIOrchestrator
from app.ai.providers.base import AIProvider
from app.ai.providers.mock import MockAIProvider
from app.ai.router import ProviderOverride
from app.ai.types import (
    AIRawResponse,
    AITask,
    Capability,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnauthorized,
)
from app.tests.conftest import make_image


class FlakyProvider(AIProvider):
    capabilities = {Capability.TEXT, Capability.VISION}
    supports_json = True

    def __init__(self, name, errors: list[Exception | None], quality=0.9):
        self.name = name
        self.display_name = name
        self.errors = list(errors)
        self.quality_score = quality
        self.calls = 0

    async def _go(self, request):
        self.calls += 1
        err = self.errors.pop(0) if self.errors else None
        if err:
            raise err
        if request.task == AITask.PRODUCT_NAME:
            return AIRawResponse(text="Camiseta Essential Ivory", model=f"{self.name}-m")
        return AIRawResponse(
            text='{"category":"camiseta","color":"ivory","confidence":0.9}', model=f"{self.name}-m"
        )

    text = _go
    vision = _go


def routing(*names):
    return {t: list(names) for t in AITask}


def test_fallback_a_fails_b_fails_c_works():
    a = FlakyProvider("a", [ProviderTimeout("t"), ProviderTimeout("t")])
    b = FlakyProvider("b", [ProviderRateLimited("r"), ProviderRateLimited("r")])
    c = FlakyProvider("c", [])
    orch = AIOrchestrator([a, b, c], routing=routing("a", "b", "c"))
    res = asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {"category": "camiseta"}}))
    assert res.success and res.provider == "c" and res.fallbacks == 2
    assert res.data["name"] == "Camiseta Essential Ivory"
    assert a.calls == 2 and b.calls == 2  # one retry each on transient errors


def test_no_retry_on_non_retryable_error():
    a = FlakyProvider("a", [ProviderUnauthorized("401")])
    b = FlakyProvider("b", [])
    orch = AIOrchestrator([a, b], routing=routing("a", "b"))
    res = asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}))
    assert res.success and res.provider == "b"
    assert a.calls == 1
    assert orch.health.get("a").status.value == "down"


def test_all_fail_returns_unsuccessful_result_not_exception():
    a = FlakyProvider("a", [ProviderTimeout("t")] * 5)
    orch = AIOrchestrator([a], routing=routing("a"))
    res = asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}))
    assert res.success is False and res.error


def test_circuit_breaker_opens_after_consecutive_failures():
    a = FlakyProvider("a", [ProviderTimeout("t")] * 10, quality=0.9)
    b = FlakyProvider("b", [], quality=0.1)  # a keeps ranking first while merely degraded
    orch = AIOrchestrator([a, b], routing=routing("a", "b"))
    for _ in range(3):
        asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}))
    assert not orch.health.get("a").is_available()
    calls_before = a.calls
    res = asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}))
    assert res.provider == "b" and res.fallbacks == 0
    assert a.calls == calls_before  # DOWN providers receive no traffic


def test_invalid_output_falls_through_to_next_provider():
    class Garbage(FlakyProvider):
        async def _go(self, request):
            self.calls += 1
            return AIRawResponse(text="lorem ipsum no json here", model="g")

        text = _go
        vision = _go

    g = Garbage("g", [])
    ok = FlakyProvider("ok", [])
    orch = AIOrchestrator([g, ok], routing=routing("g", "ok"))
    res = asyncio.run(orch.run(AITask.PRODUCT_RECOGNITION, {"image": make_image()}))
    assert res.success and res.provider == "ok" and res.fallbacks == 1
    assert res.data["category"] == "camiseta"


def test_admin_overrides_disable_and_reprioritize():
    a = FlakyProvider("a", [])
    b = FlakyProvider("b", [])
    orch = AIOrchestrator([a, b], routing=routing("a", "b"))
    orch.set_overrides({"a": ProviderOverride(enabled=False)})
    res = asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}))
    assert res.provider == "b"
    orch.set_overrides({"a": ProviderOverride(priority=50), "b": ProviderOverride(priority=10)})
    res = asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}))
    assert res.provider == "b"


def test_mocks_blocked_when_not_allowed():
    orch = AIOrchestrator([MockAIProvider()], allow_mocks=False, routing=routing("mock"))
    res = asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}))
    assert res.success is False and res.error == "no provider available"


def test_feature_flag_disables_task():
    orch = AIOrchestrator(
        [MockAIProvider()], routing=routing("mock"), feature_flags={"ai_descriptions": False}
    )
    res = asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}))
    assert res.success is False and res.error == "feature disabled"


def test_usage_sink_records_each_attempt():
    records: list[dict] = []
    a = FlakyProvider("a", [ProviderTimeout("t")] * 2)
    b = FlakyProvider("b", [])
    orch = AIOrchestrator([a, b], routing=routing("a", "b"), usage_sink=records.append)
    asyncio.run(orch.run(AITask.PRODUCT_NAME, {"attributes": {}}, user_id="u1"))
    assert [r["provider"] for r in records] == ["a", "b"]
    assert records[0]["success"] is False and records[1]["success"] is True
    assert records[1]["fallback"] is True and records[1]["user_id"] == "u1"


@pytest.mark.parametrize(
    "text", ['```json\n{"name": "x"}\n```', 'Here: {"name": "x"} ok', '{"name":"x"}']
)
def test_extract_json_tolerates_prose_and_fences(text):
    from app.ai.tasks.base import extract_json

    assert extract_json(text) == {"name": "x"}
