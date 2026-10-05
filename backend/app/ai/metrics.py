"""Product-level metrics: photo→product time, cost per product, fallback/error rates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AIJob, AIUsage, JobStatus, Product


def _since(hours: int) -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours)


def product_metrics(db: Session, hours: int = 24 * 7) -> dict:
    since = _since(hours)
    # photo → product (first completed pipeline job per product)
    jobs = db.execute(
        select(AIJob, Product.created_at)
        .join(Product, Product.id == AIJob.product_id)
        .where(
            AIJob.status == JobStatus.COMPLETED,
            AIJob.task.in_(["full", "analyze"]),
            AIJob.created_at >= since,
        )
    ).all()
    durations = [
        (job.completed_at - created).total_seconds() for job, created in jobs if job.completed_at
    ]
    # product → catalog (published)
    pub = db.execute(
        select(Product.created_at, Product.published_at).where(
            Product.published_at.is_not(None), Product.created_at >= since
        )
    ).all()
    to_catalog = [(p - c).total_seconds() for c, p in pub if p is not None]

    usage = db.execute(select(AIUsage).where(AIUsage.created_at >= since)).scalars().all()
    products_with_ai = {u.product_id for u in usage if u.product_id}
    total_cost = sum(u.estimated_cost for u in usage)
    users = {u.user_id for u in usage if u.user_id}
    n = len(usage)
    published_count = db.execute(
        select(func.count(Product.id)).where(Product.published_at >= since)
    ).scalar_one()

    def avg(xs: list[float]) -> float | None:
        return round(sum(xs) / len(xs), 1) if xs else None

    return {
        "window_hours": hours,
        "photo_to_product_seconds_avg": avg(durations),
        "product_to_catalog_seconds_avg": avg(to_catalog),
        "products_processed": len(products_with_ai),
        "products_published": published_count,
        "ai_cost_per_product": round(total_cost / len(products_with_ai), 5)
        if products_with_ai
        else 0.0,
        "ai_cost_per_user": round(total_cost / len(users), 5) if users else 0.0,
        "free_provider_ratio": round(sum(1 for u in usage if u.estimated_cost == 0) / n, 3)
        if n
        else 1.0,
        "fallback_rate": round(sum(1 for u in usage if u.fallback) / n, 3) if n else 0.0,
        "ai_error_rate": round(sum(1 for u in usage if not u.success) / n, 3) if n else 0.0,
    }
