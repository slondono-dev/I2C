from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models import User
from app.schemas.brand import BrandCreate, BrandOut, BrandUpdate
from app.services import brands as svc

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
