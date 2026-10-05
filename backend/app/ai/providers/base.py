from __future__ import annotations

from abc import ABC

from app.ai.types import AIRawResponse, AIRequest, Capability


class AIProvider(ABC):
    """Common provider contract. Subclasses implement only the capabilities they support."""

    name: str = "base"
    display_name: str = "Base"
    capabilities: set[Capability] = set()
    # Static scores in [0, 1]; 1 is best (free, high quality, fast).
    cost_score: float = 1.0
    quality_score: float = 0.5
    latency_score: float = 0.5
    is_free: bool = True
    is_mock: bool = False
    supports_json: bool = False

    @property
    def configured(self) -> bool:
        return True

    def supports(self, capability: Capability) -> bool:
        return capability in self.capabilities

    async def execute(self, request: AIRequest) -> AIRawResponse:
        if request.capability == Capability.TEXT:
            return await self.text(request)
        if request.capability == Capability.VISION:
            return await self.vision(request)
        if request.capability == Capability.IMAGE_EDIT:
            return await self.image_edit(request)
        if request.capability == Capability.IMAGE_GENERATION:
            return await self.image(request)
        if request.capability == Capability.VIDEO:
            return await self.video(request)
        raise NotImplementedError(request.capability)

    async def text(self, request: AIRequest) -> AIRawResponse:
        raise NotImplementedError

    async def vision(self, request: AIRequest) -> AIRawResponse:
        raise NotImplementedError

    async def image_edit(self, request: AIRequest) -> AIRawResponse:
        raise NotImplementedError

    async def image(self, request: AIRequest) -> AIRawResponse:
        raise NotImplementedError

    async def video(self, request: AIRequest) -> AIRawResponse:
        raise NotImplementedError

    async def health_check(self) -> bool:
        return self.configured

    def describe(self) -> dict:
        return {
            "provider": self.name,
            "display_name": self.display_name,
            "capabilities": sorted(c.value for c in self.capabilities),
            "supports_json": self.supports_json,
            "is_free": self.is_free,
            "is_mock": self.is_mock,
            "configured": self.configured,
        }
