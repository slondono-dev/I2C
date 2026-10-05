"""Builds the public catalog payload (no auth) including WhatsApp links."""

from __future__ import annotations

from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Catalog, CatalogStatus, Product, ProductStatus, StockMode


def format_price(price, currency: str) -> str:
    if price is None:
        return ""
    amount = (
        f"{int(price):,}".replace(",", ".")
        if currency in ("COP", "CLP", "ARS")
        else f"{price:,.2f}"
    )
    return f"${amount}"


def whatsapp_url(phone: str | None, product: Product) -> str | None:
    if not phone:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not digits:
        return None
    lines = ["Hola.", "", "Estoy interesado en:", "", product.name]
    if product.price is not None:
        lines += ["", "Precio:", format_price(product.price, product.currency)]
    if product.sku:
        lines += ["", "Referencia:", product.sku]
    return f"https://wa.me/{digits}?text={quote(chr(10).join(lines))}"


def get_public_catalog(db: Session, slug: str) -> Catalog | None:
    return db.execute(
        select(Catalog).where(Catalog.slug == slug, Catalog.status == CatalogStatus.PUBLISHED)
    ).scalar_one_or_none()


def serialize_product(product: Product, phone: str | None) -> dict:
    available = not (
        product.stock_mode == StockMode.OUT_OF_STOCK
        or (product.stock_mode == StockMode.TRACKED and (product.stock or 0) <= 0)
    )
    sizes = [v.size for v in product.variants if v.size]
    if not sizes and product.size:
        sizes = [s.strip() for s in product.size.replace("/", ",").split(",") if s.strip()]
    images = {a.type.value: a.url for a in product.assets if a.type.value != "video"}
    thumb = next((a for a in product.assets if a.type.value == "thumbnail"), None)
    display_type = next(
        (t for t in (product.primary_asset_type.value, "clean", "original") if t in images), None
    )
    image_small = (
        thumb.url
        if thumb is not None and (thumb.metadata_ or {}).get("from") == display_type
        else product.display_image
    )
    video = next((a.url for a in product.assets if a.type.value == "video"), None)
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "available": available,
        "stock": product.stock if product.stock_mode == StockMode.TRACKED else None,
        "category": product.category,
        "color": product.color,
        "sizes": sizes,
        "image": product.display_image,
        "image_small": image_small,
        "images": images,
        "video": video,
        "whatsapp_url": whatsapp_url(phone, product),
    }


def serialize_catalog(db: Session, catalog: Catalog) -> dict:
    s = get_settings()
    products = (
        db.execute(
            select(Product)
            .where(Product.catalog_id == catalog.id, Product.status == ProductStatus.PUBLISHED)
            .order_by(Product.created_at.desc())
        )
        .scalars()
        .all()
    )
    brand = catalog.brand
    public_url = f"{s.public_base_url.rstrip('/')}/c/{catalog.slug}"
    return {
        "name": catalog.name,
        "slug": catalog.slug,
        "description": catalog.description,
        "theme": catalog.theme,
        "brand": {
            "name": brand.name,
            "slug": brand.slug,
            "logo": brand.logo,
            "whatsapp": brand.whatsapp,
            "primary_color": brand.primary_color,
            "secondary_color": brand.secondary_color,
            "font": brand.font,
        },
        "products": [serialize_product(p, brand.whatsapp) for p in products],
        "public_url": public_url,
        "qr_url": f"{s.api_base_url.rstrip('/')}/api/v1/public/catalogs/{catalog.slug}/qr.png",
    }


def make_qr_png(url: str) -> bytes:
    from io import BytesIO

    import qrcode

    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
