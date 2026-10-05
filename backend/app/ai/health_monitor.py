"""Periodic provider health checks (runs as an asyncio task inside the API process)."""

from __future__ import annotations

import asyncio
import time

from app.ai.orchestrator import AIOrchestrator
from app.ai.types import ProviderStatus
from app.core.logging import get_logger

log = get_logger("ai.health")


async def check_all(orch: AIOrchestrator) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for name, provider in orch.providers.items():
        health = orch.health.get(name)
        if not provider.configured:
            results[name] = False
            continue
        start = time.perf_counter()
        try:
            ok = await asyncio.wait_for(provider.health_check(), timeout=15)
        except Exception as exc:  # network errors, timeouts
            ok = False
            health.last_error = f"health_check: {exc.__class__.__name__}"
        latency = int((time.perf_counter() - start) * 1000)
        results[name] = ok
        if ok and health.status == ProviderStatus.DOWN and not health.open_until:
            health.status = ProviderStatus.HEALTHY
        elif not ok and health.status == ProviderStatus.HEALTHY:
            health.status = ProviderStatus.DEGRADED
        log.info(
            "ai.health_check", provider=name, ok=ok, latency_ms=latency, status=health.status.value
        )
    return results


async def run_forever(orch: AIOrchestrator, interval_seconds: float = 300.0) -> None:
    while True:
        try:
            await check_all(orch)
        except Exception as exc:  # never die
            log.error("ai.health_loop_error", error=str(exc))
        await asyncio.sleep(interval_seconds)
