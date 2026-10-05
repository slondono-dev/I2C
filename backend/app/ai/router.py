"""Task → provider routing with weighted scoring.

score = cost×0.40 + quality×0.30 + availability×0.20 + latency×0.10
Priority order: COST, QUALITY, AVAILABILITY, SPEED. DB config (enabled/priority) overrides.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.health import HealthRegistry
from app.ai.providers.base import AIProvider
from app.ai.types import AITask, Capability

# Default candidate list per task, in preferred order (used as tiebreaker).
DEFAULT_ROUTING: dict[AITask, list[str]] = {
    AITask.PRODUCT_RECOGNITION: [
        "ninerouter",
        "openrouter",
        "openai_compatible",
        "anthropic",
        "local",
        "mock",
    ],
    AITask.PRODUCT_NAME: [
        "ninerouter",
        "openrouter",
        "openai_compatible",
        "anthropic",
        "local",
        "mock",
    ],
    AITask.PRODUCT_DESCRIPTION: [
        "ninerouter",
        "openrouter",
        "openai_compatible",
        "anthropic",
        "local",
        "mock",
    ],
    AITask.BACKGROUND_REMOVAL: ["local", "mock"],
    AITask.PRODUCT_ENHANCEMENT: [],
    AITask.VIRTUAL_MODEL: ["mock"],  # real adapters added here when available
    AITask.PRODUCT_VIDEO: ["mock"],
}

WEIGHTS = {"cost": 0.40, "quality": 0.30, "availability": 0.20, "latency": 0.10}


@dataclass
class ProviderOverride:
    enabled: bool = True
    priority: int = 100  # lower = earlier


class TaskRouter:
    def __init__(
        self,
        providers: dict[str, AIProvider],
        health: HealthRegistry,
        routing: dict[AITask, list[str]] | None = None,
        allow_mocks: bool = True,
    ):
        self.providers = providers
        self.health = health
        self.routing = routing or DEFAULT_ROUTING
        self.allow_mocks = allow_mocks
        self.overrides: dict[str, ProviderOverride] = {}

    def set_overrides(self, overrides: dict[str, ProviderOverride]) -> None:
        self.overrides = overrides

    def score(self, provider: AIProvider) -> float:
        h = self.health.get(provider.name)
        return (
            provider.cost_score * WEIGHTS["cost"]
            + provider.quality_score * WEIGHTS["quality"]
            + h.availability_score() * WEIGHTS["availability"]
            + provider.latency_score * WEIGHTS["latency"]
        )

    def candidates(self, task: AITask, capability: Capability) -> list[AIProvider]:
        names = self.routing.get(task, [])
        selected: list[tuple[int, float, int, AIProvider]] = []
        for idx, name in enumerate(names):
            p = self.providers.get(name)
            if p is None or not p.supports(capability):
                continue
            if p.is_mock and not self.allow_mocks:
                continue
            if not p.configured:
                continue
            ov = self.overrides.get(name, ProviderOverride())
            if not ov.enabled:
                continue
            if not self.health.get(name).is_available():
                continue
            selected.append((ov.priority, -self.score(p), idx, p))
        selected.sort(key=lambda t: (t[0], t[1], t[2]))
        return [t[3] for t in selected]

    def routing_table(self) -> dict[str, list[str]]:
        return {t.value: list(v) for t, v in self.routing.items()}
