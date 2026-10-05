from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class BrandCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    whatsapp: str | None = Field(default=None, max_length=32)
    primary_color: str = "#111111"
    secondary_color: str = "#f5f5f4"
    font: str = "inter"
    catalog_style: str = "minimal"


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    whatsapp: str | None = None
    logo: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    font: str | None = None
    catalog_style: str | None = None


class BrandOut(ORMModel):
    id: str
    name: str
    slug: str
    logo: str | None
    whatsapp: str | None
    primary_color: str
    secondary_color: str
    font: str
    catalog_style: str
    created_at: datetime
