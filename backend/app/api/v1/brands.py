from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models import BrandModel, User
from app.schemas.brand import BrandCreate, BrandModelIn, BrandModelOut, BrandOut, BrandUpdate
from app.services import brands as svc
from app.services.images.validation import InvalidImage, validate_image
from app.services.storage import get_storage

router = APIRouter(prefix="/brands", tags=["brands"])


def _get_or_404(db: Session, user: User, brand_id: str):
    brand = svc.get_brand(db, user.id, brand_id)
    if brand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "brand not found")
    return brand


@router.get("", response_model=list[BrandOut])
def list_brands(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.list_brands(db, user.id)


@router.post("", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
def create_brand(
    data: BrandCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return svc.create_brand(db, user.id, data)


@router.get("/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_or_404(db, user, brand_id)


@router.patch("/{brand_id}", response_model=BrandOut)
def update_brand(
    brand_id: str,
    data: BrandUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.update_brand(db, _get_or_404(db, user, brand_id), data)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(
    brand_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    svc.delete_brand(db, _get_or_404(db, user, brand_id))


@router.post("/{brand_id}/logo", response_model=BrandOut)
async def upload_logo(
    brand_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    brand = _get_or_404(db, user, brand_id)
    try:
        image = validate_image(await file.read(), max_side=512)
    except InvalidImage as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    key = f"brands/{brand.id}/logo.{image.extension}"
    brand.logo = get_storage().save(key, image.data, image.content_type)
    db.commit()
    db.refresh(brand)
    return brand


@router.get("/{brand_id}/models", response_model=list[BrandModelOut])
def list_models(
    brand_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    brand = _get_or_404(db, user, brand_id)
    return list(db.execute(select(BrandModel).where(BrandModel.brand_id == brand.id)).scalars())


@router.post(
    "/{brand_id}/models", response_model=BrandModelOut, status_code=status.HTTP_201_CREATED
)
def create_model(
    brand_id: str,
    data: BrandModelIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    brand = _get_or_404(db, user, brand_id)
    m = BrandModel(brand_id=brand.id, **data.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{brand_id}/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    brand_id: str,
    model_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    brand = _get_or_404(db, user, brand_id)
    m = db.get(BrandModel, model_id)
    if m is None or m.brand_id != brand.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "model not found")
    db.delete(m)
    db.commit()
