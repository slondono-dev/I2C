from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.catalog import CatalogStatus, CatalogTheme
from app.schemas.common import ORMModel


class CatalogCreate(BaseModel):
    brand_id: str
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = None
    theme: CatalogTheme = CatalogTheme.MINIMAL


class CatalogUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    theme: CatalogTheme | None = None
    status: CatalogStatus | None = None


class CatalogOut(ORMModel):
    id: str
    brand_id: str
    name: str
    slug: str
    description: str | None
    status: CatalogStatus
    theme: CatalogTheme
    created_at: datetime
    published_at: datetime | None
    product_count: int = 0
    public_url: str | None = None
