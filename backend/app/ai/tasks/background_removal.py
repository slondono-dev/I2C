from __future__ import annotations

from typing import Any

from app.ai.tasks.base import TaskHandler
from app.ai.types import AIRawResponse, AIRequest, AITask, Capability, InvalidProviderOutput


class BackgroundRemovalTask(TaskHandler):
    task = AITask.BACKGROUND_REMOVAL
    capability = Capability.IMAGE_EDIT

    def build_request(self, payload: dict[str, Any]) -> AIRequest:
        return AIRequest(
            task=self.task,
            capability=self.capability,
            image=payload["image"],
            image_mime=payload.get("image_mime", "image/jpeg"),
        )

    def parse(self, raw: AIRawResponse, payload: dict[str, Any]) -> dict[str, Any]:
        if not raw.image:
            raise InvalidProviderOutput("no image returned")
        return {"image": raw.image, "image_mime": raw.image_mime or "image/png"}
