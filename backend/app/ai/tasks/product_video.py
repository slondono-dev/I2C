"""PRODUCT_VIDEO: model/product image → short 5-10 s clip. Optional, VIDEO_ENABLED=false."""

from __future__ import annotations

from typing import Any

from app.ai.tasks.base import TaskHandler
from app.ai.types import AIRawResponse, AIRequest, AITask, Capability, InvalidProviderOutput


class ProductVideoTask(TaskHandler):
    task = AITask.PRODUCT_VIDEO
    capability = Capability.VIDEO

    def build_request(self, payload: dict[str, Any]) -> AIRequest:
        return AIRequest(
            task=self.task,
            capability=self.capability,
            prompt="Slow runway-style motion, subtle camera push-in, keep garment unchanged.",
            image=payload["image"],
            image_mime=payload.get("image_mime", "image/png"),
            params={"duration_seconds": int(payload.get("duration_seconds", 6))},
            max_tokens=0,
        )

    def parse(self, raw: AIRawResponse, payload: dict[str, Any]) -> dict[str, Any]:
        if not raw.image:
            raise InvalidProviderOutput("no video returned")
        return {"video": raw.image, "video_mime": raw.image_mime or "video/mp4"}
