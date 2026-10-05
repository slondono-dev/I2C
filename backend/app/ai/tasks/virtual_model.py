"""VIRTUAL_MODEL: garment image + model reference/style → image of the product being worn.

Premium feature. Providers implement Capability.IMAGE_GENERATION. Disabled by default
(VIRTUAL_MODEL_ENABLED=false) and never required to publish a catalog.
"""

from __future__ import annotations

from typing import Any

from app.ai.tasks.base import TaskHandler
from app.ai.types import AIRawResponse, AIRequest, AITask, Capability, InvalidProviderOutput


class VirtualModelTask(TaskHandler):
    task = AITask.VIRTUAL_MODEL
    capability = Capability.IMAGE_GENERATION

    def build_request(self, payload: dict[str, Any]) -> AIRequest:
        style = payload.get("style") or "studio"
        model = payload.get("model") or {}
        prompt = model.get("prompt_template") or (
            f"Fashion {style} photo of a {model.get('gender', 'female')} model "
            f"({model.get('age_range', '25-35')}) wearing the garment from the reference image. "
            "Keep the garment's exact shape, color, pattern, seams, pockets and buttons. "
            "Neutral background, soft lighting."
        )
        if "{" in prompt:
            fields = {k: v or "" for k, v in model.items() if isinstance(v, str)}
            fields["style"] = style
            try:
                prompt = prompt.format(**fields)
            except (KeyError, IndexError, ValueError):
                pass  # keep template verbatim if it has unknown placeholders
        return AIRequest(
            task=self.task,
            capability=self.capability,
            prompt=prompt,
            image=payload["image"],
            image_mime=payload.get("image_mime", "image/png"),
            params={"style": style, "model": model},
            max_tokens=0,
        )

    def parse(self, raw: AIRawResponse, payload: dict[str, Any]) -> dict[str, Any]:
        if not raw.image:
            raise InvalidProviderOutput("no image returned")
        return {"image": raw.image, "image_mime": raw.image_mime or "image/png"}
