from __future__ import annotations

import enum

from sqlalchemy import JSON, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import IdMixin, TimestampMixin


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class StockMode(str, enum.Enum):
    TRACKED = "tracked"
    UNLIMITED = "unlimited"
    OUT_OF_STOCK = "out_of_stock"


class AssetType(str, enum.Enum):
    ORIGINAL = "original"
    CLEAN = "clean"
    MODEL = "model"
    LIFESTYLE = "lifestyle"
    VIDEO = "video"
    THUMBNAIL = "thumbnail"


class Product(Base, IdMixin, TimestampMixin):
    __tablename__ = "products"

    catalog_id: Mapped[str] = mapped_column(ForeignKey("catalogs.id"), index=True, nullable=False)
    sku: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="COP")
    stock: Mapped[int | None] = mapped_column(Integer)
    stock_mode: Mapped[StockMode] = mapped_column(
        Enum(StockMode, native_enum=False, length=20), default=StockMode.TRACKED
    )
    category: Mapped[str | None] = mapped_column(String(80))
    subcategory: Mapped[str | None] = mapped_column(String(80))
    color: Mapped[str | None] = mapped_column(String(60))
    gender: Mapped[str | None] = mapped_column(String(30))
    size: Mapped[str | None] = mapped_column(String(60))
    material: Mapped[str | None] = mapped_column(String(80))
    fit: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, native_enum=False, length=20), default=ProductStatus.DRAFT
    )
    primary_asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, native_enum=False, length=20), default=AssetType.CLEAN
    )
    ai_metadata: Mapped[dict | None] = mapped_column(JSON)

    catalog = relationship("Catalog", back_populates="products")
    assets = relationship(
        "ProductAsset", back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )
    variants = relationship(
        "ProductVariant", back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )
    jobs = relationship("AIJob", back_populates="product", cascade="all, delete-orphan")

    def asset_url(self, asset_type: AssetType) -> str | None:
        for a in self.assets:
            if a.type == asset_type:
                return a.url
        return None

    @property
    def display_image(self) -> str | None:
        """Image shown in catalog: preferred type, falling back to clean, then original."""
        for t in (self.primary_asset_type, AssetType.CLEAN, AssetType.ORIGINAL):
            url = self.asset_url(t)
            if url:
                return url
        return None


class ProductAsset(Base, IdMixin, TimestampMixin):
    __tablename__ = "product_assets"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    type: Mapped[AssetType] = mapped_column(Enum(AssetType, native_enum=False, length=20))
    source: Mapped[str] = mapped_column(String(40), default="upload")  # upload | ai | derived
    provider: Mapped[str | None] = mapped_column(String(60))
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(600), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON)
    is_primary: Mapped[bool] = mapped_column(default=False)

    product = relationship("Product", back_populates="assets")


class ProductVariant(Base, IdMixin, TimestampMixin):
    __tablename__ = "product_variants"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    size: Mapped[str | None] = mapped_column(String(30))
    color: Mapped[str | None] = mapped_column(String(60))
    stock: Mapped[int | None] = mapped_column(Integer)
    sku: Mapped[str | None] = mapped_column(String(64))

    product = relationship("Product", back_populates="variants")
