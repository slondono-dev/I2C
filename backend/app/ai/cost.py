"""Usage/cost recording and aggregation (ai_usage table)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai import AIUsage


def record_usage(
    db: Session,
    *,
    user_id: str | None,
    task: str,
    provider: str,
    model: str | None,
    input_units: int,
    output_units: int,
    estimated_cost: float,
    latency_ms: int,
    success: bool,
    fallback: bool,
    error: str | None = None,
) -> None:
    db.add(
        AIUsage(
            user_id=user_id,
            task=task,
            provider=provider,
            model=model,
            input_units=input_units,
            output_units=output_units,
            estimated_cost=estimated_cost,
            latency_ms=latency_ms,
            success=success,
            fallback=fallback,
            error=(error or None) and error[:500],
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    db.commit()


def usage_summary(
    db: Session, since_hours: int = 24, free_providers: set[str] | None = None
) -> dict:
    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=since_hours)
    rows = db.execute(select(AIUsage).where(AIUsage.created_at >= since)).scalars().all()
    requests = len(rows)
    cost = sum(r.estimated_cost for r in rows)
    free = sum(
        1
        for r in rows
        if (free_providers and r.provider in free_providers) or r.estimated_cost == 0
    )
    fallbacks = sum(1 for r in rows if r.fallback)
    errors = sum(1 for r in rows if not r.success)
    by_task: dict[str, int] = {}
    by_provider: dict[str, int] = {}
    for r in rows:
        by_task[r.task] = by_task.get(r.task, 0) + 1
        by_provider[r.provider] = by_provider.get(r.provider, 0) + 1
    return {
        "requests": requests,
        "cost": round(cost, 4),
        "free_ratio": round(free / requests, 3) if requests else 1.0,
        "fallbacks": fallbacks,
        "errors": errors,
        "by_task": by_task,
        "by_provider": by_provider,
    }


def avg_cost_per_product(db: Session) -> float:
    total = db.execute(select(func.coalesce(func.sum(AIUsage.estimated_cost), 0.0))).scalar_one()
    products = db.execute(select(func.count(func.distinct(AIUsage.user_id)))).scalar_one()
    return float(total) / products if products else 0.0
