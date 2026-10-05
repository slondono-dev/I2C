from __future__ import annotations

import json
from typing import Any

from app.ai.prompts.registry import get_prompt
from app.ai.tasks.base import TaskHandler
from app.ai.types import AIRawResponse, AIRequest, AITask, Capability, InvalidProviderOutput

_ATTR_KEYS = (
    "category",
    "subcategory",
    "color",
    "gender",
    "sleeve",
    "neck",
    "fit",
    "pattern",
    "material",
)


def _attributes(payload: dict[str, Any]) -> dict[str, Any]:
    attrs = payload.get("attributes") or {}
    return {k: v for k, v in attrs.items() if k in _ATTR_KEYS and v}


def _clean_line(text: str) -> str:
    line = text.strip().splitlines()[0] if text.strip() else ""
    return line.strip().strip('"').strip("'").strip("*").strip()


class ProductNameTask(TaskHandler):
    task = AITask.PRODUCT_NAME
    capability = Capability.TEXT

    def build_request(self, payload: dict[str, Any]) -> AIRequest:
        prompt = get_prompt("product_name")
        attrs = _attributes(payload)
        return AIRequest(
            task=self.task,
            capability=self.capability,
            system=prompt.system,
            prompt=prompt.render(attributes=json.dumps(attrs, ensure_ascii=False)),
            params={"attributes": attrs, "temperature": 0.7},
            max_tokens=40,
            prompt_version=prompt.version,
        )

    def parse(self, raw: AIRawResponse, payload: dict[str, Any]) -> dict[str, Any]:
        name = _clean_line(raw.text or "")
        words = name.split()
        if not name or len(words) > 8 or len(name) > 80:
            raise InvalidProviderOutput("name out of bounds")
        return {"name": " ".join(w.capitalize() if w.islower() else w for w in words)}


class ProductDescriptionTask(TaskHandler):
    task = AITask.PRODUCT_DESCRIPTION
    capability = Capability.TEXT
    MIN_WORDS, MAX_WORDS = 10, 60

    def build_request(self, payload: dict[str, Any]) -> AIRequest:
        prompt = get_prompt("product_description")
        attrs = _attributes(payload)
        return AIRequest(
            task=self.task,
            capability=self.capability,
            system=prompt.system,
            prompt=prompt.render(
                name=payload.get("name") or "el producto",
                attributes=json.dumps(attrs, ensure_ascii=False),
            ),
            params={"attributes": attrs, "temperature": 0.7},
            max_tokens=160,
            prompt_version=prompt.version,
        )

    def parse(self, raw: AIRawResponse, payload: dict[str, Any]) -> dict[str, Any]:
        text = " ".join((raw.text or "").strip().strip('"').split())
        words = text.split()
        if len(words) < self.MIN_WORDS:
            raise InvalidProviderOutput("description too short")
        if len(words) > self.MAX_WORDS:
            text = " ".join(words[: self.MAX_WORDS]).rstrip(",;:") + "."
        return {"description": text}
