from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.ai import JobStatus
from app.schemas.common import ORMModel


class JobOut(ORMModel):
    id: str
    product_id: str | None
    task: str
    provider: str | None
    status: JobStatus
    progress: int
    result: dict | None
    error: str | None
    created_at: datetime
    completed_at: datetime | None


class ProviderStatusOut(BaseModel):
    name: str
    display_name: str
    capabilities: list[str]
    status: str
    enabled: bool
    priority: int
    configured: bool
    success_rate: float
    avg_latency_ms: float
    last_success: datetime | None
    last_error: str | None
    consecutive_failures: int
    cost_score: float
    quality_score: float


class ProviderConfigUpdate(BaseModel):
    enabled: bool | None = None
    priority: int | None = None


class TaskRoutingOut(BaseModel):
    task: str
    providers: list[str]
    active: str | None


class UsageSummaryOut(BaseModel):
    requests: int
    cost: float
    free_ratio: float
    fallbacks: int
    errors: int
    active_providers: int
    by_task: dict[str, int]
    by_provider: dict[str, int]
