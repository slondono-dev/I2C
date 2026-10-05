from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.models.product import AssetType, ProductStatus, StockMode
from app.schemas.common import ORMModel


class ProductAssetOut(ORMModel):
    id: str
    type: AssetType
    source: str
    provider: str | None
    url: str
    is_primary: bool
    created_at: datetime


class ProductVariantIn(BaseModel):
    size: str | None = None
    color: str | None = None
    stock: int | None = None
    sku: str | None = None


class ProductVariantOut(ORMModel):
    id: str
    size: str | None
    color: str | None
    stock: int | None
    sku: str | None


class ProductCreate(BaseModel):
    catalog_id: str
    name: str = Field(default="", max_length=160)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str = "COP"
    stock: int | None = Field(default=None, ge=0)
    stock_mode: StockMode = StockMode.TRACKED
    sku: str | None = None
    category: str | None = None
    subcategory: str | None = None
    color: str | None = None
    gender: str | None = None
    size: str | None = None
    material: str | None = None
    fit: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    stock: int | None = Field(default=None, ge=0)
    stock_mode: StockMode | None = None
    sku: str | None = None
    category: str | None = None
    subcategory: str | None = None
    color: str | None = None
    gender: str | None = None
    size: str | None = None
    material: str | None = None
    fit: str | None = None
    status: ProductStatus | None = None
    primary_asset_type: AssetType | None = None
    variants: list[ProductVariantIn] | None = None


class ProductOut(ORMModel):
    id: str
    catalog_id: str
    sku: str | None
    name: str
    description: str | None
    price: Decimal | None
    currency: str
    stock: int | None
    stock_mode: StockMode
    category: str | None
    subcategory: str | None
    color: str | None
    gender: str | None
    size: str | None
    material: str | None
    fit: str | None
    status: ProductStatus
    primary_asset_type: AssetType
    ai_metadata: dict | None
    display_image: str | None
    assets: list[ProductAssetOut]
    variants: list[ProductVariantOut]
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BulkPublish(BaseModel):
    product_ids: list[str] = Field(min_length=1)


class BulkReprocess(BaseModel):
    product_ids: list[str] = Field(min_length=1, max_length=100)
    task: Literal["analyze", "clean", "full"] = "full"
    overwrite: bool = False


class BulkUpdateItem(BaseModel):
    id: str
    name: str | None = None
    price: Decimal | None = None
    stock: int | None = None
    sku: str | None = None


class BulkUpdate(BaseModel):
    items: list[BulkUpdateItem] = Field(min_length=1)
