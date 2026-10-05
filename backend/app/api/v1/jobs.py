import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import SessionLocal, get_db
from app.models import AIJob, JobStatus, User
from app.schemas.ai import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    product_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(AIJob).where(AIJob.user_id == user.id)
    if product_id:
        stmt = stmt.where(AIJob.product_id == product_id)
    return list(db.execute(stmt.order_by(AIJob.created_at.desc()).limit(100)).scalars())


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(AIJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")
    return job


TERMINAL = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}


@router.get("/{job_id}/stream")
async def stream_job(
    job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Server-Sent Events: emits the job state every ~0.5 s until it reaches a terminal status."""
    job = db.get(AIJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")

    async def events():
        last = None
        for _ in range(600):  # hard cap ≈ 5 min
            session = SessionLocal()
            try:
                current = session.get(AIJob, job_id)
                snapshot = (
                    JobOut.model_validate(current).model_dump(mode="json") if current else None
                )
            finally:
                session.close()
            if snapshot != last:
                yield f"event: job\ndata: {json.dumps(snapshot)}\n\n"
                last = snapshot
            if snapshot is None or snapshot["status"] in {s.value for s in TERMINAL}:
                break
            await asyncio.sleep(0.5)
        yield "event: end\ndata: {}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
