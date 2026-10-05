"""Shared AI types. The rest of the app only sees AITask, AIResult and the orchestrator."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class AITask(str, enum.Enum):
    PRODUCT_RECOGNITION = "product_recognition"
    PRODUCT_NAME = "product_name"
    PRODUCT_DESCRIPTION = "product_description"
    BACKGROUND_REMOVAL = "background_removal"
    PRODUCT_ENHANCEMENT = "product_enhancement"
    VIRTUAL_MODEL = "virtual_model"
    PRODUCT_VIDEO = "product_video"


class Capability(str, enum.Enum):
    TEXT = "text"
    VISION = "vision"
    IMAGE_EDIT = "image_edit"
    IMAGE_GENERATION = "image_generation"
    VIDEO = "video"


class ProviderStatus(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    QUOTA_EXCEEDED = "quota_exceeded"
    DISABLED = "disabled"


@dataclass
class AIRequest:
    task: AITask
    capability: Capability
    prompt: str = ""
    system: str = ""
    image: bytes | None = None
    image_mime: str = "image/jpeg"
    json_output: bool = False
    max_tokens: int = 400
    params: dict[str, Any] = field(default_factory=dict)
    prompt_version: str | None = None


@dataclass
class AIRawResponse:
    text: str | None = None
    image: bytes | None = None
    image_mime: str | None = None
    model: str | None = None
    input_units: int = 0
    output_units: int = 0
    estimated_cost: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResult:
    success: bool
    task: str
    provider: str | None
    model: str | None
    cost: float
    data: dict[str, Any]
    fallbacks: int = 0
    latency_ms: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "task": self.task,
            "provider": self.provider,
            "model": self.model,
            "cost": self.cost,
            "data": self.data,
            "fallbacks": self.fallbacks,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


# ---------- Errors ----------
class ProviderError(Exception):
    """Base provider error. `retryable` marks transient failures (timeout, 429, 5xx)."""

    retryable = False

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ProviderUnavailable(ProviderError):
    retryable = True


class ProviderTimeout(ProviderError):
    retryable = True


class ProviderRateLimited(ProviderError):
    retryable = True


class ProviderQuotaExceeded(ProviderError):
    retryable = False


class ProviderUnauthorized(ProviderError):
    retryable = False


class InvalidProviderOutput(ProviderError):
    """Output could not be parsed/validated. Try next provider, don't retry same."""

    retryable = False


class NoProviderAvailable(Exception):
    pass
