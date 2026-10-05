from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.public import PublicCatalog
from app.services.catalog import public as svc

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/catalogs/{slug}", response_model=PublicCatalog)
def public_catalog(slug: str, db: Session = Depends(get_db)):
    catalog = svc.get_public_catalog(db, slug)
    if catalog is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "catalog not found")
    return svc.serialize_catalog(db, catalog)


@router.get("/catalogs/{slug}/qr.png")
def public_catalog_qr(slug: str, db: Session = Depends(get_db)):
    catalog = svc.get_public_catalog(db, slug)
    if catalog is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "catalog not found")
    payload = svc.serialize_catalog(db, catalog)
    return Response(
        svc.make_qr_png(payload["public_url"]),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
