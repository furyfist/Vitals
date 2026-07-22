"""ScopeState and RollingWindow (spec §4.3, §4.4).

ScopeKey = (service_name, gen_ai_system, model) — version excluded.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from vitals.model import GenAISpan
from vitals.quality.types import EvalLogRecord
from vitals.verdict.signal import CalibratedSignal
from vitals.verdict.types import Verdict, VerdictState


@dataclass(frozen=True, slots=True)
class SpanRecord:
    ts: float
    behavior_psi: float
    input_psi: float
    usd: float
    out_len: int
    trace_id: str
    span_id: str
    output_excerpt: str  # <= 240 chars, whitespace-collapsed


class ScopeState:
    """State and signal tracker for one ScopeKey (service_name, gen_ai_system, model)."""

    def __init__(
        self,
        service_name: str,
        gen_ai_system: str,
        model: str,
        reference_window: int = 30,
        calib_n: int = 30,
        window_max: int = 500,
        sigma_floor: float = 1e-6,
    ) -> None:
        self.service_name = service_name
        self.gen_ai_system = gen_ai_system
        self.model = model
        self.key = (service_name, gen_ai_system, model)

        self._lock = threading.Lock()
        self.reference_window = reference_window
        self.calib_n = calib_n
        self.window_max = window_max

        self.reference_outputs: list[str] = []
        self.reference_inputs: list[str] = []
        self.signals: dict[str, CalibratedSignal] = {
            "behavior": CalibratedSignal(calib_n, sigma_floor),
            "input": CalibratedSignal(calib_n, sigma_floor),
            "cost": CalibratedSignal(calib_n, sigma_floor),
            "length": CalibratedSignal(calib_n, sigma_floor),
        }
        self.windows: dict[str, deque[SpanRecord]] = defaultdict(
            lambda: deque(maxlen=self.window_max)
        )
        self.version_timeline: list[tuple[str, float]] = []  # (version, first_seen_ts)
        self.current_state: VerdictState = VerdictState.WARMING
        self.last_verdict: Verdict | None = None
        self.state_since_ts: float = 0.0
        self.consecutive_condition_ticks: int = 0
        self.total_spans_seen: int = 0

    def observe(
        self, span: GenAISpan, record: EvalLogRecord, usd: float, now: float | None = None
    ) -> None:
        """Observe one mapped GenAISpan and its quality/cost records."""
        now = time.time() if now is None else now
        version = span.service_version

        with self._lock:
            self.total_spans_seen += 1
            # Record version timeline if first seen
            if not any(v == version for v, _ in self.version_timeline):
                self.version_timeline.append((version, now))

            # Phase 1: Reference collection (first reference_window spans)
            if len(self.reference_outputs) < self.reference_window:
                self.reference_outputs.append(span.output_text)
                self.reference_inputs.append(span.input_text or " ")
                return

            # Phase 2: Post-reference spans
            behavior_psi = record.drift if record.drift is not None else 0.0
            input_psi = record.input_drift if record.input_drift is not None else 0.0
            out_len = record.output_len

            # Calibrate signals
            self.signals["behavior"].observe_calibration(behavior_psi)
            self.signals["input"].observe_calibration(input_psi)
            self.signals["cost"].observe_calibration(usd)
            self.signals["length"].observe_calibration(float(out_len))

            # Whitespace collapse excerpt
            raw_excerpt = (span.output_text or "")[:240]
            excerpt = " ".join(raw_excerpt.split())

            rec = SpanRecord(
                ts=now,
                behavior_psi=behavior_psi,
                input_psi=input_psi,
                usd=usd,
                out_len=out_len,
                trace_id=span.trace_id,
                span_id=span.span_id,
                output_excerpt=excerpt,
            )
            self.windows[version].append(rec)

    def is_reference_ready(self) -> bool:
        with self._lock:
            return len(self.reference_outputs) >= self.reference_window

    def is_calibrated(self) -> bool:
        with self._lock:
            return all(sig.calibrated() for sig in self.signals.values())

    def is_live(self) -> bool:
        with self._lock:
            return (
                len(self.reference_outputs) >= self.reference_window
                and all(sig.calibrated() for sig in self.signals.values())
            )

    def warming_progress(self) -> tuple[tuple[int, int], str]:
        """Returns ((have, need), phase_name) for progress reporting."""
        with self._lock:
            ref_have = len(self.reference_outputs)
            if ref_have < self.reference_window:
                return (ref_have, self.reference_window), "collecting_reference"
            calib_have = self.signals["behavior"].n
            if calib_have < self.calib_n:
                return (calib_have, self.calib_n), "calibrating"
            return (self.calib_n, self.calib_n), "live"
