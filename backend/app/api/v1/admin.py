from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import get_orchestrator
from app.ai.cost import usage_summary
from app.ai.factory import load_overrides_from_db
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
