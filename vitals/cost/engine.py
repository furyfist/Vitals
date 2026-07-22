"""Cost engine: span-attribute arithmetic -> USD spend-rate + cumulative burn (D7).

Per dimension key (service/version/system/model) it keeps:
  - a cumulative total (USD) -> vitals.cost.total
  - a sliding window of (timestamp, usd) samples -> vitals.cost.velocity (USD/min)

Velocity is what catches a runaway loop in minutes: dollars-per-minute over the last
`window_s` seconds, extrapolated to a per-minute rate.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from vitals.cost.prices import PriceTable
from vitals.model import GenAISpan


@dataclass
class CostSample:
    """A per-dimension cost snapshot the emitter turns into metric points."""

    dims: dict[str, str]
    velocity_usd_per_min: float
    total_usd: float
    input_tokens: int
    output_tokens: int


def _dim_key(dims: dict[str, str]) -> tuple:
    return tuple(sorted(dims.items()))


class CostEngine:
    def __init__(self, price_table: PriceTable, window_s: int = 60):
        self._prices = price_table
        self._window_s = window_s
        self._lock = threading.Lock()
        self._totals: dict[tuple, float] = defaultdict(float)
        self._tokens_in: dict[tuple, int] = defaultdict(int)
        self._tokens_out: dict[tuple, int] = defaultdict(int)
        self._dims: dict[tuple, dict[str, str]] = {}
        # key -> deque[(monotonic_ts, usd)]
        self._windows: dict[tuple, deque] = defaultdict(deque)

    def record(self, span: GenAISpan, now: float | None = None) -> None:
        """Account one span's cost. `now` injectable for deterministic tests."""
        now = time.monotonic() if now is None else now
        usd = self._prices.cost_usd(span.model, span.input_tokens, span.output_tokens)
        dims = span.dims()
        key = _dim_key(dims)
        with self._lock:
            self._dims[key] = dims
            self._totals[key] += usd
            self._tokens_in[key] += span.input_tokens
            self._tokens_out[key] += span.output_tokens
            self._windows[key].append((now, usd))
            self._evict(key, now)

    def _evict(self, key: tuple, now: float) -> None:
        window = self._windows[key]
        cutoff = now - self._window_s
        while window and window[0][0] < cutoff:
            window.popleft()

    def _velocity(self, key: tuple, now: float) -> float:
        """USD/min over the sliding window."""
        self._evict(key, now)
        window = self._windows[key]
        if not window:
            return 0.0
        usd_in_window = sum(usd for _, usd in window)
        return usd_in_window * (60.0 / self._window_s)

    def sample(self, now: float | None = None) -> list[CostSample]:
        """Current cost state per dimension. Called on the emit interval."""
        now = time.monotonic() if now is None else now
        out: list[CostSample] = []
        with self._lock:
            for key, dims in self._dims.items():
                out.append(
                    CostSample(
                        dims=dims,
                        velocity_usd_per_min=self._velocity(key, now),
                        total_usd=self._totals[key],
                        input_tokens=self._tokens_in[key],
                        output_tokens=self._tokens_out[key],
                    )
                )
        return out

    def velocity_for(self, dims: dict[str, str], now: float | None = None) -> float:
        """USD/min velocity for specific dimensions."""
        now = time.monotonic() if now is None else now
        key = _dim_key(dims)
        with self._lock:
            return self._velocity(key, now)
