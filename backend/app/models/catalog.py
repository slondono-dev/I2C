from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import IdMixin, TimestampMixin


class CatalogStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CatalogTheme(str, enum.Enum):
    MINIMAL = "minimal"
    EDITORIAL = "editorial"
    STREET = "street"
    PREMIUM = "premium"
    COLORFUL = "colorful"


class Catalog(Base, IdMixin, TimestampMixin):
    __tablename__ = "catalogs"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CatalogStatus] = mapped_column(
        Enum(CatalogStatus, native_enum=False, length=20), default=CatalogStatus.DRAFT
    )
    theme: Mapped[CatalogTheme] = mapped_column(
        Enum(CatalogTheme, native_enum=False, length=20), default=CatalogTheme.MINIMAL
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    brand = relationship("Brand", back_populates="catalogs")
    products = relationship("Product", back_populates="catalog", cascade="all, delete-orphan")
