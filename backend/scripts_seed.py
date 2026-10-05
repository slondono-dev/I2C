"""Seed demo data: `python scripts_seed.py` (run inside backend/ with the venv active).

Creates demo user (demo@i2c.local / demo1234, admin), brand, published catalog and products
with generated placeholder images, so the app can be evaluated immediately.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO

from PIL import Image, ImageDraw
from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import Brand, Catalog, CatalogStatus, Product, ProductStatus, User
from app.schemas.brand import BrandCreate
from app.services.brands import create_brand
from app.services.images.validation import validate_image
from app.services.products import attach_original

DEMO = [
    ("Camiseta Essential Ivory", "camiseta", "ivory", (245, 240, 225), 79900, 12, "CAM-001"),
    ("Camiseta Essential Negra", "camiseta", "negro", (30, 30, 30), 79900, 8, "CAM-002"),
    ("Hoodie Street Gris", "hoodie", "gris", (120, 120, 125), 159900, 5, "HOO-001"),
    ("Jean Slim Azul", "pantalón", "azul", (40, 70, 140), 189900, 3, "JEA-001"),
    ("Vestido Midi Verde", "vestido", "verde", (60, 130, 80), 219900, 4, "VES-001"),
    ("Gorra Classic Beige", "accesorio", "beige", (210, 190, 160), 59900, 20, "GOR-001"),
]


def placeholder(color: tuple[int, int, int], label: str) -> bytes:
    img = Image.new("RGB", (900, 1200), color)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((200, 300, 700, 900), radius=60, fill=tuple(max(0, c - 25) for c in color))
    d.text((60, 60), label, fill=(255, 255, 255) if sum(color) < 380 else (20, 20, 20))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def main() -> None:
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == "demo@i2c.local")).scalar_one_or_none()
        if user is None:
            user = User(
                name="Demo",
                email="demo@i2c.local",
                password_hash=hash_password("demo1234"),
                is_admin=True,
            )
            db.add(user)
            db.commit()
        brand = db.execute(select(Brand).where(Brand.user_id == user.id)).scalars().first()
        if brand is None:
            brand = create_brand(
                db,
                user.id,
                BrandCreate(
                    name="Demo Studio", whatsapp="+573001234567", catalog_style="editorial"
                ),
            )
        catalog = db.execute(select(Catalog).where(Catalog.brand_id == brand.id)).scalars().first()
        assert catalog is not None
        if not catalog.products:
            for name, category, color, rgb, price, stock, sku in DEMO:
                product = Product(
                    catalog_id=catalog.id,
                    name=name,
                    category=category,
                    color=color,
                    price=Decimal(price),
                    stock=stock,
                    sku=sku,
                    status=ProductStatus.PUBLISHED,
                    description=f"{name} de corte regular, ideal para el día a día. Prenda "
                    "versátil, cómoda y fácil de combinar con cualquier look.",
                    size="S, M, L",
                )
                db.add(product)
                db.commit()
                db.refresh(product)
                attach_original(db, product, validate_image(placeholder(rgb, name)))
            catalog.status = CatalogStatus.PUBLISHED
            db.commit()
        print(f"Demo ready: login demo@i2c.local / demo1234 — catalog slug: {catalog.slug}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
