"""Builds the application-wide AIOrchestrator from settings."""

from __future__ import annotations

from functools import lru_cache

from app.ai.orchestrator import AIOrchestrator
from app.ai.providers import (
    AIProvider,
    AnthropicProvider,
    LocalProvider,
    MockAIProvider,
    NineRouterProvider,
    OpenAICompatibleProvider,
    OpenRouterProvider,
)
from app.core.config import Settings, get_settings


def build_providers(s: Settings) -> list[AIProvider]:
    timeout = s.ai_request_timeout_seconds
    providers: list[AIProvider] = [
        NineRouterProvider(
            enabled=s.ninerouter_enabled,
            base_url=s.ninerouter_base_url,
            api_key=s.ninerouter_api_key,
            text_model=s.ninerouter_text_model,
            vision_model=s.ninerouter_vision_model,
            timeout=timeout,
        ),
        OpenRouterProvider(
            base_url=s.openrouter_base_url,
            api_key=s.openrouter_api_key,
            text_model=s.openrouter_text_model,
            vision_model=s.openrouter_vision_model,
            timeout=timeout,
        ),
        OpenAICompatibleProvider(
            base_url=s.openai_compatible_base_url,
            api_key=s.openai_compatible_api_key,
            text_model=s.openai_compatible_text_model,
            vision_model=s.openai_compatible_vision_model,
            timeout=timeout,
        ),
        AnthropicProvider(api_key=s.anthropic_api_key, model=s.anthropic_model, timeout=timeout),
        LocalProvider(),
    ]
    if s.mocks_allowed:
        providers.append(MockAIProvider())
    return providers


def _db_usage_sink(record: dict) -> None:
    from app.ai.cost import record_usage
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        record_usage(db, **record)
    finally:
        db.close()


@lru_cache
def get_orchestrator() -> AIOrchestrator:
    s = get_settings()
    orch = AIOrchestrator(
        providers=build_providers(s),
        allow_mocks=s.mocks_allowed,
        usage_sink=_db_usage_sink,
        feature_flags=lambda: get_settings().feature_flags(),
    )
    return orch


def load_overrides_from_db(orch: AIOrchestrator) -> None:
    """Apply /admin/ai provider configuration stored in the database."""
    from sqlalchemy import select

    from app.ai.router import ProviderOverride
    from app.core.db import SessionLocal
    from app.models.ai import ProviderConfig

    db = SessionLocal()
    try:
        rows = db.execute(select(ProviderConfig)).scalars().all()
        orch.set_overrides(
            {r.name: ProviderOverride(enabled=r.enabled, priority=r.priority) for r in rows}
        )
    finally:
        db.close()
