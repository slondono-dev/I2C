"""9Router adapter. Expected to expose an OpenAI-compatible API; gated by NINEROUTER_ENABLED."""

from __future__ import annotations

from app.ai.providers.openai_compatible import OpenAICompatibleProvider
from app.ai.types import ProviderUnavailable


class NineRouterProvider(OpenAICompatibleProvider):
    name = "ninerouter"
    display_name = "9Router"
    cost_score = 0.95
    quality_score = 0.8
    latency_score = 0.6
    is_free = True

    def __init__(self, enabled: bool, **kwargs):
        super().__init__(**kwargs)
        self.enabled = enabled

    @property
    def configured(self) -> bool:
        return self.enabled and super().configured

    async def _chat(self, request, model, with_image):  # type: ignore[override]
        if not self.enabled:
            raise ProviderUnavailable("9Router disabled (NINEROUTER_ENABLED=false)")
        return await super()._chat(request, model, with_image)
