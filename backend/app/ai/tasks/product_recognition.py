from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

from app.ai.prompts.registry import get_prompt
from app.ai.tasks.base import TaskHandler, extract_json
from app.ai.types import AIRawResponse, AIRequest, AITask, Capability, InvalidProviderOutput

_NULLS = {"", "null", "none", "n/a", "desconocido", "unknown"}


class ProductRecognitionResult(BaseModel):
    category: str | None = None
    subcategory: str | None = None
    color: str | None = None
    gender: str | None = None
    sleeve: str | None = None
    neck: str | None = None
    fit: str | None = None
    pattern: str | None = None
    material: str | None = None
    confidence: float | None = None

    @field_validator(
        "category",
        "subcategory",
        "color",
        "gender",
        "sleeve",
        "neck",
        "fit",
        "pattern",
        "material",
        mode="before",
    )
    @classmethod
    def _norm(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip().lower()
        return None if s in _NULLS else s[:80]

    @field_validator("confidence", mode="before")
    @classmethod
    def _conf(cls, v: object) -> float | None:
        if v is None:
            return None
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, f))


class ProductRecognitionTask(TaskHandler):
    task = AITask.PRODUCT_RECOGNITION
    capability = Capability.VISION

    def build_request(self, payload: dict[str, Any]) -> AIRequest:
        prompt = get_prompt("product_recognition")
        return AIRequest(
            task=self.task,
            capability=self.capability,
            system=prompt.system,
            prompt=prompt.render(),
            image=payload["image"],
            image_mime=payload.get("image_mime", "image/jpeg"),
            json_output=True,
            max_tokens=400,
            prompt_version=prompt.version,
        )

    def parse(self, raw: AIRawResponse, payload: dict[str, Any]) -> dict[str, Any]:
        if not raw.text:
            raise InvalidProviderOutput("empty response")
        data = extract_json(raw.text)
        try:
            result = ProductRecognitionResult.model_validate(data)
        except ValidationError as exc:
            raise InvalidProviderOutput(f"schema mismatch: {exc.error_count()} errors") from exc
        out = result.model_dump()
        if not any(out[k] for k in ("category", "color")):
            raise InvalidProviderOutput("no usable attributes")
        return out
