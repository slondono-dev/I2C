from __future__ import annotations

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.orm import Session


def unique_slug(
    db: Session, model, base: str, column: str = "slug", exclude_id: str | None = None
) -> str:
    base_slug = slugify(base)[:120] or "item"
    slug = base_slug
    n = 2
    col = getattr(model, column)
    while True:
        stmt = select(model.id).where(col == slug)
        if exclude_id:
            stmt = stmt.where(model.id != exclude_id)
        if db.execute(stmt).first() is None:
            return slug
        slug = f"{base_slug}-{n}"
        n += 1
