from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Brand, Catalog, CatalogStatus, Product
from app.schemas.catalog import CatalogCreate, CatalogUpdate
from app.services.slugs import unique_slug


def public_url(slug: str) -> str:
    return f"{get_settings().public_base_url.rstrip('/')}/c/{slug}"


def list_catalogs(db: Session, user_id: str, brand_id: str | None = None) -> list[Catalog]:
    stmt = select(Catalog).join(Brand).where(Brand.user_id == user_id)
    if brand_id:
        stmt = stmt.where(Catalog.brand_id == brand_id)
    return list(db.execute(stmt.order_by(Catalog.created_at)).scalars())


def get_catalog(db: Session, user_id: str, catalog_id: str) -> Catalog | None:
    return db.execute(
        select(Catalog).join(Brand).where(Catalog.id == catalog_id, Brand.user_id == user_id)
    ).scalar_one_or_none()


def product_count(db: Session, catalog_id: str) -> int:
    return db.execute(
        select(func.count(Product.id)).where(Product.catalog_id == catalog_id)
    ).scalar_one()


def create_catalog(db: Session, brand: Brand, data: CatalogCreate) -> Catalog:
    catalog = Catalog(
        brand_id=brand.id,
        name=data.name,
        slug=unique_slug(db, Catalog, data.slug or f"{brand.slug}-{data.name}"),
        description=data.description,
        theme=data.theme,
    )
    db.add(catalog)
    db.commit()
    db.refresh(catalog)
    return catalog


def update_catalog(db: Session, catalog: Catalog, data: CatalogUpdate) -> Catalog:
    changes = data.model_dump(exclude_unset=True)
    if changes.get("status") == CatalogStatus.PUBLISHED and catalog.published_at is None:
        catalog.published_at = datetime.now(UTC).replace(tzinfo=None)
    for k, v in changes.items():
        setattr(catalog, k, v)
    db.commit()
    db.refresh(catalog)
    return catalog


def publish_catalog(db: Session, catalog: Catalog) -> Catalog:
    catalog.status = CatalogStatus.PUBLISHED
    catalog.published_at = catalog.published_at or datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(catalog)
    return catalog


def delete_catalog(db: Session, catalog: Catalog) -> None:
    db.delete(catalog)
    db.commit()
