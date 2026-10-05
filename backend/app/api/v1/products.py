from __future__ import annotations

from decimal import Decimal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.models import Product, ProductStatus, StockMode, User
from app.schemas.ai import JobOut
from app.schemas.product import (
    BulkPublish,
    BulkUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)
from app.services import catalogs as catalog_svc
from app.services import products as svc
from app.services.ai import pipeline
from app.services.images.validation import InvalidImage, validate_image

router = APIRouter(prefix="/products", tags=["products"])


def _get_or_404(db: Session, user: User, product_id: str) -> Product:
    p = svc.get_product(db, user.id, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "product not found")
    return p


def _catalog_or_404(db: Session, user: User, catalog_id: str):
    c = catalog_svc.get_catalog(db, user.id, catalog_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "catalog not found")
    return c


def _start_job(
    db: Session, bg: BackgroundTasks, user: User, product: Product, task: str, overwrite=False
):
    existing = pipeline.find_active_job(db, product.id, task)
    if existing:
        return existing
    job = pipeline.create_job(db, user.id, product.id, task)
    bg.add_task(pipeline.execute_job, job.id, overwrite)
    return job


@router.get("", response_model=list[ProductOut])
def list_products(
    catalog_id: str | None = None,
    status_: ProductStatus | None = None,
    category: str | None = None,
    low_stock: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.list_products(db, user.id, catalog_id, status_, category, low_stock)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    catalog = _catalog_or_404(db, user, data.catalog_id)
    return svc.create_product(db, catalog, data)


@router.post("/upload", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def upload_product(
    bg: BackgroundTasks,
    catalog_id: str = Form(...),
    file: UploadFile = File(...),
    auto_process: bool = Form(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Main entry point of the UX: photo in → product (draft) out, AI runs in background."""
    catalog = _catalog_or_404(db, user, catalog_id)
    raw = await file.read()
    try:
        image = validate_image(raw)
    except InvalidImage as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    product = svc.create_product(db, catalog, ProductCreate(catalog_id=catalog.id))
    svc.attach_original(db, product, image)
    s = get_settings()
    if auto_process:
        wants_analysis = s.ai_recognition_enabled or s.ai_descriptions_enabled
        task = (
            "full"
            if (wants_analysis and s.background_removal_enabled)
            else (
                "analyze" if wants_analysis else ("clean" if s.background_removal_enabled else None)
            )
        )
        if task:
            _start_job(db, bg, user, product, task)
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _get_or_404(db, user, product_id)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    data: ProductUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return svc.update_product(db, _get_or_404(db, user, product_id), data)
    except svc.ProductError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    svc.delete_product(db, _get_or_404(db, user, product_id))


@router.post("/{product_id}/image", response_model=ProductOut)
async def replace_image(
    product_id: str,
    bg: BackgroundTasks,
    file: UploadFile = File(...),
    reprocess: bool = Form(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = _get_or_404(db, user, product_id)
    try:
        image = validate_image(await file.read())
    except InvalidImage as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    svc.attach_original(db, product, image)
    if reprocess:
        _start_job(db, bg, user, product, "full", overwrite=True)
    db.refresh(product)
    return product


@router.post("/{product_id}/analyze", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def analyze_product(
    product_id: str,
    bg: BackgroundTasks,
    overwrite: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = _get_or_404(db, user, product_id)
    return _start_job(db, bg, user, product, "analyze", overwrite)


@router.post(
    "/{product_id}/remove-background", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED
)
def remove_background(
    product_id: str,
    bg: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = _get_or_404(db, user, product_id)
    return _start_job(db, bg, user, product, "clean")


@router.post("/{product_id}/generate-model", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def generate_model(product_id: str, user: User = Depends(get_current_user)):
    if not get_settings().virtual_model_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "virtual model is disabled")
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "virtual model provider not configured")


@router.post("/{product_id}/generate-video", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def generate_video(product_id: str, user: User = Depends(get_current_user)):
    if not get_settings().video_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "video generation is disabled")
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "video provider not configured")


@router.post("/bulk/publish")
def bulk_publish(
    data: BulkPublish, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    products = [p for pid in data.product_ids if (p := svc.get_product(db, user.id, pid))]
    published, errors = svc.publish_products(db, products)
    return {"published": [p.id for p in published], "errors": errors}


@router.post("/bulk/update", response_model=list[ProductOut])
def bulk_update(
    data: BulkUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    out = []
    for item in data.items:
        p = svc.get_product(db, user.id, item.id)
        if p is None:
            continue
        changes = item.model_dump(exclude_unset=True, exclude={"id"})
        if "price" in changes and changes["price"] is not None:
            changes["price"] = Decimal(str(changes["price"]))
        if "stock" in changes and changes["stock"] is not None:
            p.stock_mode = StockMode.TRACKED
        for k, v in changes.items():
            setattr(p, k, v)
        out.append(p)
    db.commit()
    return out
