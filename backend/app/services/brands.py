from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Brand, Catalog, CatalogTheme
from app.schemas.brand import BrandCreate, BrandUpdate
from app.services.slugs import unique_slug


def list_brands(db: Session, user_id: str) -> list[Brand]:
    return list(db.execute(select(Brand).where(Brand.user_id == user_id)).scalars())


def get_brand(db: Session, user_id: str, brand_id: str) -> Brand | None:
    return db.execute(
        select(Brand).where(Brand.id == brand_id, Brand.user_id == user_id)
    ).scalar_one_or_none()


def create_brand(db: Session, user_id: str, data: BrandCreate) -> Brand:
    brand = Brand(
        user_id=user_id,
        name=data.name,
        slug=unique_slug(db, Brand, data.slug or data.name),
        whatsapp=data.whatsapp,
        primary_color=data.primary_color,
        secondary_color=data.secondary_color,
        font=data.font,
        catalog_style=data.catalog_style,
    )
    db.add(brand)
    db.flush()
    # Every brand gets a default catalog so the user can start adding products at once.
    catalog = Catalog(
        brand_id=brand.id,
        name=data.name,
        slug=unique_slug(db, Catalog, brand.slug),
        theme=CatalogTheme(data.catalog_style)
        if data.catalog_style in CatalogTheme._value2member_map_
        else CatalogTheme.MINIMAL,
    )
    db.add(catalog)
    db.commit()
    db.refresh(brand)
    return brand


def update_brand(db: Session, brand: Brand, data: BrandUpdate) -> Brand:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(brand, k, v)
    db.commit()
    db.refresh(brand)
    return brand


def delete_brand(db: Session, brand: Brand) -> None:
    db.delete(brand)
    db.commit()
