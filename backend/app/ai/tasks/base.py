from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from app.ai.types import AIRawResponse, AIRequest, AITask, Capability, InvalidProviderOutput


def extract_json(text: str) -> dict[str, Any]:
    """Tolerant JSON extraction: strips code fences and surrounding prose."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise InvalidProviderOutput("no JSON object in response") from None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise InvalidProviderOutput("invalid JSON in response") from exc
    if not isinstance(data, dict):
        raise InvalidProviderOutput("JSON is not an object")
    return data


class TaskHandler(ABC):
    task: AITask
    capability: Capability

    @abstractmethod
    def build_request(self, payload: dict[str, Any]) -> AIRequest: ...

    @abstractmethod
    def parse(self, raw: AIRawResponse, payload: dict[str, Any]) -> dict[str, Any]: ...
