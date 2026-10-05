from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AssetType,
    Brand,
    Catalog,
    Product,
    ProductAsset,
    ProductStatus,
    ProductVariant,
    StockMode,
)
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.images.validation import ValidatedImage, make_thumbnail
from app.services.storage import get_storage


class ProductError(Exception):
    pass


def list_products(
    db: Session,
    user_id: str,
    catalog_id: str | None = None,
    status: ProductStatus | None = None,
    category: str | None = None,
    low_stock: int | None = None,
) -> list[Product]:
    stmt = select(Product).join(Catalog).join(Brand).where(Brand.user_id == user_id)
    if catalog_id:
        stmt = stmt.where(Product.catalog_id == catalog_id)
    if status:
        stmt = stmt.where(Product.status == status)
    if category:
        stmt = stmt.where(Product.category == category)
    if low_stock is not None:
        stmt = stmt.where(Product.stock_mode == StockMode.TRACKED, Product.stock <= low_stock)
    return list(db.execute(stmt.order_by(Product.created_at.desc())).scalars())


def get_product(db: Session, user_id: str, product_id: str) -> Product | None:
    return db.execute(
        select(Product)
        .join(Catalog)
        .join(Brand)
        .where(Product.id == product_id, Brand.user_id == user_id)
    ).scalar_one_or_none()


def create_product(db: Session, catalog: Catalog, data: ProductCreate) -> Product:
    payload = data.model_dump(exclude={"catalog_id"})
    product = Product(catalog_id=catalog.id, **payload)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, data: ProductUpdate) -> Product:
    changes = data.model_dump(exclude_unset=True)
    variants = changes.pop("variants", None)
    if changes.get("status") == ProductStatus.PUBLISHED:
        _ensure_publishable(product, changes)
    for k, v in changes.items():
        setattr(product, k, v)
    if variants is not None:
        product.variants.clear()
        for v in variants:
            product.variants.append(ProductVariant(**v))
    db.commit()
    db.refresh(product)
    return product


def _ensure_publishable(product: Product, changes: dict) -> None:
    name = changes.get("name", product.name)
    price = changes.get("price", product.price)
    if not name or not name.strip():
        raise ProductError("name is required to publish")
    if price is None:
        raise ProductError("price is required to publish")
    if not product.assets:
        raise ProductError("an image is required to publish")


def publish_products(db: Session, products: list[Product]) -> tuple[list[Product], list[dict]]:
    published, errors = [], []
    for p in products:
        try:
            _ensure_publishable(p, {})
        except ProductError as exc:
            errors.append({"id": p.id, "error": str(exc)})
            continue
        p.status = ProductStatus.PUBLISHED
        published.append(p)
    db.commit()
    return published, errors


def delete_product(db: Session, product: Product) -> None:
    storage = get_storage()
    for a in product.assets:
        try:
            storage.delete(a.storage_key)
        except Exception:
            pass
    db.delete(product)
    db.commit()


def add_asset(
    db: Session,
    product: Product,
    asset_type: AssetType,
    data: bytes,
    extension: str,
    content_type: str,
    source: str = "upload",
    provider: str | None = None,
    metadata: dict | None = None,
    replace: bool = True,
) -> ProductAsset:
    storage = get_storage()
    if replace:
        for existing in [a for a in product.assets if a.type == asset_type]:
            try:
                storage.delete(existing.storage_key)
            except Exception:
                pass
            db.delete(existing)
            product.assets.remove(existing)
    key = f"products/{product.id}/{asset_type.value}.{extension}"
    url = storage.save(key, data, content_type)
    asset = ProductAsset(
        product_id=product.id,
        type=asset_type,
        source=source,
        provider=provider,
        storage_key=key,
        url=url,
        metadata_=metadata,
        is_primary=asset_type == product.primary_asset_type,
    )
    db.add(asset)
    product.assets.append(asset)
    db.commit()
    db.refresh(product)
    return asset


def attach_original(db: Session, product: Product, image: ValidatedImage) -> ProductAsset:
    """Store original (never destroyed) plus a thumbnail derived from it."""
    asset = add_asset(
        db,
        product,
        AssetType.ORIGINAL,
        image.data,
        image.extension,
        image.content_type,
        metadata={"width": image.width, "height": image.height},
    )
    thumb = make_thumbnail(image.data)
    add_asset(db, product, AssetType.THUMBNAIL, thumb, "jpg", "image/jpeg", source="derived")
    return asset


def apply_price(value: Decimal | float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))
