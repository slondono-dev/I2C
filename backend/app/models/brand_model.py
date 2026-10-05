from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import IdMixin, TimestampMixin


class BrandModel(Base, IdMixin, TimestampMixin):
    """Reusable virtual model definition for a brand (used by VIRTUAL_MODEL)."""

    __tablename__ = "brand_models"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(30))
    age_range: Mapped[str | None] = mapped_column(String(30))
    style: Mapped[str | None] = mapped_column(String(60))
    reference_images: Mapped[list | None] = mapped_column(JSON)
    prompt_template: Mapped[str | None] = mapped_column(Text)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON)

    brand = relationship("Brand", back_populates="models")

    def as_options(self) -> dict:
        return {
            "gender": self.gender,
            "age_range": self.age_range,
            "style": self.style,
            "reference_images": self.reference_images or [],
            "prompt_template": self.prompt_template,
            "name": self.name,
        }
