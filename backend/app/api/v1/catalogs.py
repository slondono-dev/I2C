from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models import Catalog, User
from app.schemas.catalog import CatalogCreate, CatalogOut, CatalogUpdate
from app.services import brands as brand_svc
from app.services import catalogs as svc
from app.services.catalog.public import make_qr_png

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


def _out(db: Session, c: Catalog) -> CatalogOut:
    out = CatalogOut.model_validate(c)
    out.product_count = svc.product_count(db, c.id)
    out.public_url = svc.public_url(c.slug)
    return out


def _get_or_404(db: Session, user: User, catalog_id: str) -> Catalog:
    c = svc.get_catalog(db, user.id, catalog_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "catalog not found")
    return c


@router.get("", response_model=list[CatalogOut])
def list_catalogs(
    brand_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [_out(db, c) for c in svc.list_catalogs(db, user.id, brand_id)]


@router.post("", response_model=CatalogOut, status_code=status.HTTP_201_CREATED)
def create_catalog(
    data: CatalogCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    brand = brand_svc.get_brand(db, user.id, data.brand_id)
    if brand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "brand not found")
    return _out(db, svc.create_catalog(db, brand, data))


@router.get("/{catalog_id}", response_model=CatalogOut)
def get_catalog(
    catalog_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _out(db, _get_or_404(db, user, catalog_id))


@router.patch("/{catalog_id}", response_model=CatalogOut)
def update_catalog(
    catalog_id: str,
    data: CatalogUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _out(db, svc.update_catalog(db, _get_or_404(db, user, catalog_id), data))


@router.post("/{catalog_id}/publish", response_model=CatalogOut)
def publish_catalog(
    catalog_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _out(db, svc.publish_catalog(db, _get_or_404(db, user, catalog_id)))


@router.get("/{catalog_id}/qr.png")
def catalog_qr(
    catalog_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    c = _get_or_404(db, user, catalog_id)
    return Response(make_qr_png(svc.public_url(c.slug)), media_type="image/png")


@router.delete("/{catalog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog(
    catalog_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    svc.delete_catalog(db, _get_or_404(db, user, catalog_id))
