"""Vitals self-health counters — emitted from day one (§9). vitals watches vitals."""

from __future__ import annotations

import threading


class Health:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.spans_scored = 0
        self.emit_errors = 0
        self.baseline_ready = 0  # 0 = warming, 1 = at least one baseline ready
        # receiver-owned counters are read via the injected stats object
        self._recv_stats = None

    def bind_receiver_stats(self, stats) -> None:
        self._recv_stats = stats

    def inc_scored(self) -> None:
        with self._lock:
            self.spans_scored += 1

    def inc_emit_error(self) -> None:
        with self._lock:
            self.emit_errors += 1

    def set_baseline_ready(self, ready: bool) -> None:
        with self._lock:
            self.baseline_ready = 1 if ready else 0

    def snapshot(self) -> dict[str, float]:
        recv = getattr(self._recv_stats, "received", 0)
        skipped = getattr(self._recv_stats, "skipped", 0)
        with self._lock:
            return {
                "spans_received": float(recv),
                "spans_scored": float(self.spans_scored),
                "spans_skipped": float(skipped),
                "emit_errors": float(self.emit_errors),
                "baseline_state": float(self.baseline_ready),
            }
