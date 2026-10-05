from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import get_orchestrator
from app.ai.cost import usage_summary
from app.ai.factory import load_overrides_from_db
from app.ai.health_monitor import check_all
from app.ai.metrics import product_metrics
from app.api.deps import get_admin_user
from app.core.config import get_settings
from app.core.db import get_db
from app.models import ProviderConfig, User
from app.schemas.ai import ProviderConfigUpdate, ProviderStatusOut, TaskRoutingOut, UsageSummaryOut

router = APIRouter(prefix="/admin/ai", tags=["admin"])


@router.get("/providers", response_model=list[ProviderStatusOut])
def providers(_: User = Depends(get_admin_user)):
    return get_orchestrator().provider_status()


@router.patch("/providers/{name}", response_model=list[ProviderStatusOut])
def update_provider(
    name: str,
    data: ProviderConfigUpdate,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    orch = get_orchestrator()
    if name not in orch.providers:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "provider not found")
    row = db.execute(select(ProviderConfig).where(ProviderConfig.name == name)).scalar_one_or_none()
    if row is None:
        row = ProviderConfig(name=name)
        db.add(row)
    if data.enabled is not None:
        row.enabled = data.enabled
    if data.priority is not None:
        row.priority = data.priority
    db.commit()
    load_overrides_from_db(orch)
    return orch.provider_status()


@router.get("/routing", response_model=list[TaskRoutingOut])
def routing(_: User = Depends(get_admin_user)):
    return get_orchestrator().task_routing()


@router.get("/usage", response_model=UsageSummaryOut)
def usage(hours: int = 24, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    orch = get_orchestrator()
    data = usage_summary(db, hours, orch.free_provider_names())
    active = sum(1 for p in orch.provider_status() if p["status"] not in ("disabled", "down"))
    return {**data, "active_providers": active}


@router.get("/features")
def features(_: User = Depends(get_admin_user)):
    return get_settings().feature_flags()


@router.post("/health-check")
async def run_health_check(_: User = Depends(get_admin_user)):
    return await check_all(get_orchestrator())


@router.get("/metrics")
def metrics(hours: int = 24 * 7, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return product_metrics(db, hours)


class ExperimentIn(BaseModel):
    task: str
    providers: list[str] = Field(min_length=1, max_length=6)
    payload: dict = Field(default_factory=dict)
    product_id: str | None = None


@router.post("/experiments")
async def run_experiment(
    data: ExperimentIn, _: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Run the same input through several providers and compare outputs (not for production use)."""
    from app.ai.types import AITask
    from app.models import AssetType, Product
    from app.services.storage import get_storage

    try:
        task = AITask(data.task)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown task") from exc
    payload = dict(data.payload)
    if data.product_id:
        product = db.get(Product, data.product_id)
        if product is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "product not found")
        for t in (AssetType.CLEAN, AssetType.ORIGINAL):
            asset = next((a for a in product.assets if a.type == t), None)
            if asset:
                payload["image"] = get_storage().read(asset.storage_key)
                payload["image_mime"] = (
                    "image/png" if asset.storage_key.endswith(".png") else "image/jpeg"
                )
                break
    orch = get_orchestrator()
    results = []
    for name in data.providers:
        res = await orch.run_with_provider(task, payload, name)
        out = res.to_dict()
        if isinstance(out["data"].get("image"), bytes):
            out["data"] = {**out["data"], "image": f"<{len(out['data']['image'])} bytes>"}
        if isinstance(out["data"].get("video"), bytes):
            out["data"] = {**out["data"], "video": f"<{len(out['data']['video'])} bytes>"}
        results.append(out)
    return {"task": task.value, "results": results}
