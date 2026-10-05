"""AIOrchestrator: the only entry point the application uses to run AI tasks.

    result = await ai.run(task=AITask.PRODUCT_RECOGNITION, payload={"image": b"..."})

It picks candidate providers through TaskRouter, retries transient errors once,
falls back to the next provider on failure, records usage and health, and never
raises for provider failures: callers receive AIResult(success=False) instead.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

from app.ai.health import HealthRegistry
from app.ai.providers.base import AIProvider
from app.ai.router import ProviderOverride, TaskRouter
from app.ai.tasks import TASK_HANDLERS, TaskHandler
from app.ai.types import AIResult, AITask, InvalidProviderOutput, ProviderError
from app.core.logging import get_logger

log = get_logger("ai.orchestrator")

UsageSink = Callable[[dict[str, Any]], None]


class AIOrchestrator:
    def __init__(
        self,
        providers: list[AIProvider],
        allow_mocks: bool = True,
        routing: dict[AITask, list[str]] | None = None,
        usage_sink: UsageSink | None = None,
        feature_flags: dict[str, bool] | None = None,
        max_retries: int = 1,
    ):
        self.providers: dict[str, AIProvider] = {p.name: p for p in providers}
        self.health = HealthRegistry()
        self.router = TaskRouter(self.providers, self.health, routing, allow_mocks)
        self.handlers: dict[AITask, TaskHandler] = dict(TASK_HANDLERS)
        self.usage_sink = usage_sink
        self.feature_flags = feature_flags or {}
        self.max_retries = max_retries

    # ---------- configuration ----------
    def set_overrides(self, overrides: dict[str, ProviderOverride]) -> None:
        self.router.set_overrides(overrides)

    def task_enabled(self, task: AITask) -> bool:
        flag_by_task = {
            AITask.PRODUCT_RECOGNITION: "ai_recognition",
            AITask.PRODUCT_NAME: "ai_descriptions",
            AITask.PRODUCT_DESCRIPTION: "ai_descriptions",
            AITask.BACKGROUND_REMOVAL: "background_removal",
            AITask.VIRTUAL_MODEL: "virtual_model",
            AITask.PRODUCT_VIDEO: "video_generation",
        }
        flag = flag_by_task.get(task)
        return self.feature_flags.get(flag, True) if flag else True

    # ---------- execution ----------
    async def run(
        self, task: AITask | str, payload: dict[str, Any], user_id: str | None = None
    ) -> AIResult:
        task = AITask(task)
        started = time.perf_counter()
        if not self.task_enabled(task):
            return AIResult(False, task.value, None, None, 0.0, {}, error="feature disabled")
        handler = self.handlers.get(task)
        if handler is None:
            return AIResult(False, task.value, None, None, 0.0, {}, error="unknown task")

        request = handler.build_request(payload)
        candidates = self.router.candidates(task, handler.capability)
        if not candidates:
            log.warning("ai.no_provider", task=task.value)
            return AIResult(False, task.value, None, None, 0.0, {}, error="no provider available")

        fallbacks = 0
        last_error: str | None = None
        for provider in candidates:
            attempt_started = time.perf_counter()
            health = self.health.get(provider.name)
            try:
                raw = await self._call_with_retry(provider, request)
                data = handler.parse(raw, payload)
            except InvalidProviderOutput as exc:
                latency = int((time.perf_counter() - attempt_started) * 1000)
                health.record_failure(exc)
                last_error = str(exc)
                self._record(
                    user_id,
                    task,
                    provider,
                    None,
                    0,
                    0,
                    0.0,
                    latency,
                    False,
                    fallbacks > 0,
                    last_error,
                )
                log.warning(
                    "ai.invalid_output", task=task.value, provider=provider.name, error=last_error
                )
                fallbacks += 1
                continue
            except (TimeoutError, ProviderError, NotImplementedError) as exc:
                latency = int((time.perf_counter() - attempt_started) * 1000)
                health.record_failure(exc)
                last_error = str(exc) or exc.__class__.__name__
                self._record(
                    user_id,
                    task,
                    provider,
                    None,
                    0,
                    0,
                    0.0,
                    latency,
                    False,
                    fallbacks > 0,
                    last_error,
                )
                log.warning(
                    "ai.provider_failed", task=task.value, provider=provider.name, error=last_error
                )
                fallbacks += 1
                continue
            except Exception as exc:  # defensive: unexpected provider bug must not break the app
                latency = int((time.perf_counter() - attempt_started) * 1000)
                health.record_failure(exc)
                last_error = f"unexpected: {exc.__class__.__name__}"
                self._record(
                    user_id,
                    task,
                    provider,
                    None,
                    0,
                    0,
                    0.0,
                    latency,
                    False,
                    fallbacks > 0,
                    last_error,
                )
                log.error(
                    "ai.provider_crashed", task=task.value, provider=provider.name, error=str(exc)
                )
                fallbacks += 1
                continue

            latency = int((time.perf_counter() - attempt_started) * 1000)
            health.record_success(latency)
            self._record(
                user_id,
                task,
                provider,
                raw.model,
                raw.input_units,
                raw.output_units,
                raw.estimated_cost,
                latency,
                True,
                fallbacks > 0,
                None,
            )
            log.info(
                "ai.request",
                task=task.value,
                provider=provider.name,
                model=raw.model,
                latency_ms=latency,
                fallback=fallbacks > 0,
                cost=raw.estimated_cost,
                status="ok",
                prompt_version=request.prompt_version,
            )
            return AIResult(
                success=True,
                task=task.value,
                provider=provider.name,
                model=raw.model,
                cost=raw.estimated_cost,
                data=data,
                fallbacks=fallbacks,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

        return AIResult(
            False,
            task.value,
            None,
            None,
            0.0,
            {},
            fallbacks=fallbacks,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error=last_error or "all providers failed",
        )

    async def _call_with_retry(self, provider: AIProvider, request):
        attempt = 0
        while True:
            try:
                return await provider.execute(request)
            except ProviderError as exc:
                if not exc.retryable or attempt >= self.max_retries:
                    raise
                attempt += 1
                await asyncio.sleep(0.2 * attempt)

    def _record(
        self, user_id, task, provider, model, in_u, out_u, cost, latency, ok, fallback, error
    ):
        if self.usage_sink is None:
            return
        try:
            self.usage_sink(
                {
                    "user_id": user_id,
                    "task": task.value,
                    "provider": provider.name,
                    "model": model,
                    "input_units": in_u,
                    "output_units": out_u,
                    "estimated_cost": cost,
                    "latency_ms": latency,
                    "success": ok,
                    "fallback": fallback,
                    "error": error,
                }
            )
        except Exception as exc:  # never let metrics break requests
            log.error("ai.usage_sink_failed", error=str(exc))

    # ---------- introspection ----------
    def provider_status(self) -> list[dict[str, Any]]:
        out = []
        for name, p in self.providers.items():
            h = self.health.get(name)
            ov = self.router.overrides.get(name, ProviderOverride())
            status = h.status.value
            if not ov.enabled:
                status = "disabled"
            elif not p.configured:
                status = "disabled"
            out.append(
                {
                    "name": name,
                    "display_name": p.display_name,
                    "capabilities": sorted(c.value for c in p.capabilities),
                    "status": status,
                    "enabled": ov.enabled,
                    "priority": ov.priority,
                    "configured": p.configured,
                    "success_rate": round(h.success_rate, 3),
                    "avg_latency_ms": round(h.avg_latency_ms, 1),
                    "last_success": h.last_success,
                    "last_error": h.last_error,
                    "consecutive_failures": h.consecutive_failures,
                    "cost_score": p.cost_score,
                    "quality_score": p.quality_score,
                }
            )
        return out

    def task_routing(self) -> list[dict[str, Any]]:
        out = []
        for task, names in self.router.routing.items():
            handler = self.handlers.get(task)
            active = None
            if handler is not None:
                c = self.router.candidates(task, handler.capability)
                active = c[0].name if c else None
            out.append({"task": task.value, "providers": names, "active": active})
        return out

    def free_provider_names(self) -> set[str]:
        return {n for n, p in self.providers.items() if p.is_free}
