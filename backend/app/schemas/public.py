from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from app.models.catalog import CatalogTheme


class PublicBrand(BaseModel):
    name: str
    slug: str
    logo: str | None
    whatsapp: str | None
    primary_color: str
    secondary_color: str
    font: str


class PublicProduct(BaseModel):
    id: str
    sku: str | None
    name: str
    description: str | None
    price: Decimal | None
    currency: str
    available: bool
    stock: int | None
    category: str | None
    color: str | None
    sizes: list[str]
    image: str | None
    images: dict[str, str]
    video: str | None = None
    whatsapp_url: str | None


class PublicCatalog(BaseModel):
    name: str
    slug: str
    description: str | None
    theme: CatalogTheme
    brand: PublicBrand
    products: list[PublicProduct]
    public_url: str
    qr_url: str
