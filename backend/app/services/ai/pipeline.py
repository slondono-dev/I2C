"""Product AI pipeline executed as background jobs.

analyze:  recognition → name → description   (updates product attributes, never blocks publishing)
clean:    background removal → CLEAN asset
full:     analyze + clean

Each step degrades gracefully: if a task fails the product keeps whatever it had.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import AITask, get_orchestrator
from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models import AIJob, AssetType, JobStatus, Product, ProductStatus
from app.services.products import add_asset
from app.services.storage import get_storage

log = get_logger("ai.pipeline")

_ATTR_FIELDS = ("category", "subcategory", "color", "gender", "fit", "material")


def create_job(
    db: Session, user_id: str, product_id: str | None, task: str, options: dict | None = None
) -> AIJob:
    job = AIJob(
        user_id=user_id,
        product_id=product_id,
        task=task,
        status=JobStatus.PENDING,
        result={"options": options} if options else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def find_active_job(db: Session, product_id: str, task: str) -> AIJob | None:
    """Idempotency: reuse a pending/running job for the same product+task."""
    return (
        db.execute(
            select(AIJob).where(
                AIJob.product_id == product_id,
                AIJob.task == task,
                AIJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
            )
        )
        .scalars()
        .first()
    )


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _set(db: Session, job: AIJob, **fields: Any) -> None:
    for k, v in fields.items():
        setattr(job, k, v)
    db.commit()


def _original_bytes(product: Product) -> tuple[bytes, str] | None:
    storage = get_storage()
    for a in product.assets:
        if a.type == AssetType.ORIGINAL:
            mime = "image/png" if a.storage_key.endswith(".png") else "image/jpeg"
            if a.storage_key.endswith(".webp"):
                mime = "image/webp"
            return storage.read(a.storage_key), mime
    return None


async def run_analyze(db: Session, job: AIJob, product: Product, overwrite: bool = False) -> dict:
    ai = get_orchestrator()
    summary: dict[str, Any] = {"recognition": None, "name": None, "description": None}
    original = _original_bytes(product)
    if original is None:
        raise RuntimeError("product has no original image")
    image, mime = original

    _set(db, job, progress=10)
    rec = await ai.run(
        AITask.PRODUCT_RECOGNITION, {"image": image, "image_mime": mime}, job.user_id, product.id
    )
    attrs: dict[str, Any] = {}
    if rec.success:
        attrs = rec.data
        for field in _ATTR_FIELDS:
            if attrs.get(field) and (overwrite or not getattr(product, field)):
                setattr(product, field, attrs[field])
        meta = dict(product.ai_metadata or {})
        meta["recognition"] = {
            **{k: v for k, v in attrs.items()},
            "provider": rec.provider,
            "model": rec.model,
            "at": _now().isoformat(),
        }
        product.ai_metadata = meta
        db.commit()
    summary["recognition"] = {"success": rec.success, "provider": rec.provider, "error": rec.error}
    _set(db, job, progress=45)

    attributes = {f: getattr(product, f) for f in _ATTR_FIELDS if getattr(product, f)}
    attributes.update({k: v for k, v in attrs.items() if k in ("sleeve", "neck", "pattern") and v})

    if overwrite or not product.name:
        name = await ai.run(
            AITask.PRODUCT_NAME, {"attributes": attributes}, job.user_id, product.id
        )
        if name.success:
            product.name = name.data["name"]
            db.commit()
        summary["name"] = {"success": name.success, "provider": name.provider, "error": name.error}
    _set(db, job, progress=70)

    if overwrite or not product.description:
        desc = await ai.run(
            AITask.PRODUCT_DESCRIPTION,
            {"attributes": attributes, "name": product.name},
            job.user_id,
            product.id,
        )
        if desc.success:
            product.description = desc.data["description"]
            db.commit()
        elif not product.description and product.name:
            # Fallback rule: name + attributes
            parts = [product.name] + [str(v) for v in attributes.values()]
            product.description = " · ".join(parts)
            db.commit()
        summary["description"] = {
            "success": desc.success,
            "provider": desc.provider,
            "error": desc.error,
        }
    return summary


async def run_clean(db: Session, job: AIJob, product: Product) -> dict:
    ai = get_orchestrator()
    original = _original_bytes(product)
    if original is None:
        raise RuntimeError("product has no original image")
    image, mime = original
    _set(db, job, progress=20)
    res = await ai.run(
        AITask.BACKGROUND_REMOVAL, {"image": image, "image_mime": mime}, job.user_id, product.id
    )
    if res.success:
        out_mime = res.data.get("image_mime", "image/png")
        ext = "png" if out_mime == "image/png" else "jpg"
        add_asset(
            db,
            product,
            AssetType.CLEAN,
            res.data["image"],
            ext,
            out_mime,
            source="ai",
            provider=res.provider,
        )
    return {"success": res.success, "provider": res.provider, "error": res.error}


def _source_for_generation(product: Product) -> tuple[bytes, str] | None:
    """Prefer the clean image (transparent) for generation, else original."""
    storage = get_storage()
    for t in (AssetType.CLEAN, AssetType.ORIGINAL):
        for a in product.assets:
            if a.type == t:
                mime = "image/png" if a.storage_key.endswith(".png") else "image/jpeg"
                return storage.read(a.storage_key), mime
    return None


async def run_model(db: Session, job: AIJob, product: Product, options: dict | None = None) -> dict:
    from app.services.images.fidelity import fidelity_score, needs_review

    ai = get_orchestrator()
    src = _source_for_generation(product)
    if src is None:
        raise RuntimeError("product has no image")
    image, mime = src
    options = options or {}
    _set(db, job, progress=20)
    res = await ai.run(
        AITask.VIRTUAL_MODEL,
        {
            "image": image,
            "image_mime": mime,
            "style": options.get("style"),
            "model": options.get("model"),
        },
        job.user_id,
        product.id,
    )
    out: dict[str, Any] = {"success": res.success, "provider": res.provider, "error": res.error}
    if res.success:
        score = fidelity_score(image, res.data["image"])
        out["fidelity_score"] = score
        out["review_required"] = needs_review(score)
        ext = "png" if res.data["image_mime"] == "image/png" else "jpg"
        add_asset(
            db,
            product,
            AssetType.MODEL,
            res.data["image"],
            ext,
            res.data["image_mime"],
            source="ai",
            provider=res.provider,
            metadata={"fidelity_score": score, "review_required": needs_review(score)},
        )
        meta = dict(product.ai_metadata or {})
        meta["virtual_model"] = {
            "provider": res.provider,
            "fidelity_score": score,
            "review_required": needs_review(score),
            "at": _now().isoformat(),
        }
        product.ai_metadata = meta
        db.commit()
    return out


async def run_video(db: Session, job: AIJob, product: Product) -> dict:
    ai = get_orchestrator()
    storage = get_storage()
    src = None
    for t in (AssetType.MODEL, AssetType.CLEAN, AssetType.ORIGINAL):
        for a in product.assets:
            if a.type == t:
                src = (
                    storage.read(a.storage_key),
                    "image/png" if a.storage_key.endswith(".png") else "image/jpeg",
                )
                break
        if src:
            break
    if src is None:
        raise RuntimeError("product has no image")
    _set(db, job, progress=20)
    res = await ai.run(
        AITask.PRODUCT_VIDEO, {"image": src[0], "image_mime": src[1]}, job.user_id, product.id
    )
    if res.success:
        mime = res.data["video_mime"]
        ext = {"video/mp4": "mp4", "video/webm": "webm", "image/gif": "gif"}.get(mime, "bin")
        add_asset(
            db,
            product,
            AssetType.VIDEO,
            res.data["video"],
            ext,
            mime,
            source="ai",
            provider=res.provider,
        )
    return {"success": res.success, "provider": res.provider, "error": res.error}


async def execute_job(job_id: str, overwrite: bool = False) -> None:
    """Entry point for BackgroundTasks. Opens its own DB session."""
    db = SessionLocal()
    try:
        job = db.get(AIJob, job_id)
        if job is None or job.status not in (JobStatus.PENDING,):
            return
        product = db.get(Product, job.product_id) if job.product_id else None
        if product is None:
            _set(db, job, status=JobStatus.FAILED, error="product not found", completed_at=_now())
            return
        _set(db, job, status=JobStatus.RUNNING, progress=5)
        previous_status = product.status
        if product.status in (ProductStatus.DRAFT,):
            product.status = ProductStatus.PROCESSING
            db.commit()
        result: dict[str, Any] = {}
        try:
            if job.task in ("analyze", "full"):
                result["analyze"] = await run_analyze(db, job, product, overwrite)
            if job.task in ("clean", "full"):
                result["clean"] = await run_clean(db, job, product)
            if job.task == "model":
                result["model"] = await run_model(
                    db, job, product, (job.result or {}).get("options")
                )
            if job.task == "video":
                result["video"] = await run_video(db, job, product)
            if job.task not in ("analyze", "clean", "full", "model", "video"):
                raise RuntimeError(f"unknown job task {job.task}")
            used: list[str] = [
                r["provider"]
                for r in (result.get("analyze") or {}).values()
                if isinstance(r, dict) and r.get("provider")
            ]
            for key in ("clean", "model", "video"):
                if result.get(key, {}).get("provider"):
                    used.append(result[key]["provider"])
            _set(
                db,
                job,
                status=JobStatus.COMPLETED,
                progress=100,
                result=result,
                provider=",".join(dict.fromkeys(used)) or None,
                completed_at=_now(),
            )
        except Exception as exc:  # job must never leave product stuck in PROCESSING
            log.error("job.failed", job_id=job_id, task=job.task, error=str(exc))
            _set(
                db,
                job,
                status=JobStatus.FAILED,
                error=str(exc)[:500],
                result=result,
                completed_at=_now(),
            )
        finally:
            db.refresh(product)
            if product.status == ProductStatus.PROCESSING:
                product.status = (
                    ProductStatus.REVIEW
                    if previous_status == ProductStatus.DRAFT
                    else previous_status
                )
                db.commit()
    finally:
        db.close()


def run_job_sync(job_id: str, overwrite: bool = False) -> None:
    asyncio.run(execute_job(job_id, overwrite))
