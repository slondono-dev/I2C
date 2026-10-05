from __future__ import annotations

from app.ai.providers.openai_compatible import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    name = "openrouter"
    display_name = "OpenRouter"
    cost_score = 0.9  # free-tier models by default
    quality_score = 0.75
    latency_score = 0.5
    is_free = True

    def __init__(self, **kwargs):
        kwargs.setdefault(
            "extra_headers",
            {"HTTP-Referer": "https://i2c.local", "X-Title": "I2C"},
        )
        super().__init__(**kwargs)

    @property
    def configured(self) -> bool:
        return bool(self.api_key) and super().configured
