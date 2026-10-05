from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import IdMixin, TimestampMixin


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIJob(Base, IdMixin, TimestampMixin):
    __tablename__ = "ai_jobs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), index=True)
    task: Mapped[str] = mapped_column(String(60), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=20), default=JobStatus.PENDING, index=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    product = relationship("Product", back_populates="jobs")


class AIUsage(Base, IdMixin):
    __tablename__ = "ai_usage"

    user_id: Mapped[str | None] = mapped_column(String(32), index=True)
    task: Mapped[str] = mapped_column(String(60), index=True)
    provider: Mapped[str] = mapped_column(String(60), index=True)
    model: Mapped[str | None] = mapped_column(String(120))
    input_units: Mapped[int] = mapped_column(Integer, default=0)
    output_units: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class ProviderConfig(Base, IdMixin, TimestampMixin):
    """Runtime provider configuration editable from /admin/ai (no code change needed)."""

    __tablename__ = "ai_provider_configs"

    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    settings: Mapped[dict | None] = mapped_column(JSON)
