from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import IdMixin, TimestampMixin


class Brand(Base, IdMixin, TimestampMixin):
    __tablename__ = "brands"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    logo: Mapped[str | None] = mapped_column(String(500))
    whatsapp: Mapped[str | None] = mapped_column(String(32))
    primary_color: Mapped[str] = mapped_column(String(16), default="#111111")
    secondary_color: Mapped[str] = mapped_column(String(16), default="#f5f5f4")
    font: Mapped[str] = mapped_column(String(64), default="inter")
    catalog_style: Mapped[str] = mapped_column(String(32), default="minimal")

    owner = relationship("User", back_populates="brands")
    catalogs = relationship("Catalog", back_populates="brand", cascade="all, delete-orphan")
    models = relationship("BrandModel", back_populates="brand", cascade="all, delete-orphan")
