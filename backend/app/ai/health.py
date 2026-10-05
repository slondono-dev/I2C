"""In-memory provider health with a simple circuit breaker."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.ai.types import ProviderQuotaExceeded, ProviderStatus, ProviderUnauthorized

FAILURE_THRESHOLD = 3
OPEN_SECONDS = 120.0
QUOTA_COOLDOWN_SECONDS = 3600.0


@dataclass
class ProviderHealth:
    name: str
    status: ProviderStatus = ProviderStatus.HEALTHY
    consecutive_failures: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: int = 0
    last_success: datetime | None = None
    last_error: str | None = None
    open_until: float = 0.0
    recent: list[bool] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if not self.recent:
            return 1.0
        return sum(self.recent) / len(self.recent)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.successes if self.successes else 0.0

    def availability_score(self) -> float:
        if not self.is_available():
            return 0.0
        return 0.5 + 0.5 * self.success_rate

    def is_available(self) -> bool:
        if self.status == ProviderStatus.DISABLED:
            return False
        if self.open_until and time.monotonic() < self.open_until:
            return False
        if self.open_until and time.monotonic() >= self.open_until:
            # half-open: allow a trial request
            self.open_until = 0.0
            self.status = ProviderStatus.DEGRADED
        return True

    def record_success(self, latency_ms: int) -> None:
        self.successes += 1
        self.consecutive_failures = 0
        self.total_latency_ms += latency_ms
        self.last_success = datetime.now(UTC)
        self.status = ProviderStatus.HEALTHY
        self.open_until = 0.0
        self._push(True)

    def record_failure(self, exc: Exception) -> None:
        self.failures += 1
        self.consecutive_failures += 1
        self.last_error = f"{exc.__class__.__name__}: {exc}"[:300]
        self._push(False)
        if isinstance(exc, ProviderQuotaExceeded):
            self.status = ProviderStatus.QUOTA_EXCEEDED
            self.open_until = time.monotonic() + QUOTA_COOLDOWN_SECONDS
        elif isinstance(exc, ProviderUnauthorized):
            self.status = ProviderStatus.DOWN
            self.open_until = time.monotonic() + QUOTA_COOLDOWN_SECONDS
        elif self.consecutive_failures >= FAILURE_THRESHOLD:
            self.status = ProviderStatus.DOWN
            self.open_until = time.monotonic() + OPEN_SECONDS
        else:
            self.status = ProviderStatus.DEGRADED

    def _push(self, ok: bool) -> None:
        self.recent.append(ok)
        if len(self.recent) > 50:
            self.recent.pop(0)


class HealthRegistry:
    def __init__(self) -> None:
        self._items: dict[str, ProviderHealth] = {}

    def get(self, name: str) -> ProviderHealth:
        if name not in self._items:
            self._items[name] = ProviderHealth(name=name)
        return self._items[name]

    def all(self) -> dict[str, ProviderHealth]:
        return dict(self._items)

    def reset(self) -> None:
        self._items.clear()
