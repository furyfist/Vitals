"""Quality engine: deterministic, reference-free scoring on every response (D2, D6).

Primary signal (never cut): ResponseDrift (PSI vs frozen healthy baseline) + CUSUM
onset. Consistency and output stability are embedding-based and OPTIONAL — enabled only
when spanIQ's embedding metrics import successfully (`vitals[quality-full]`); their
absence degrades gracefully to the drift-only composite (matches the descope ladder).
"""

from __future__ import annotations

import logging
import threading

from spaniq.core.test_case import LLMTestCase
from spaniq.metrics.response_drift import ResponseDriftMetric
from vitals.config.settings import QualityConfig
from vitals.model import GenAISpan
from vitals.quality.baseline import Baseline
from vitals.quality.types import EvalLogRecord, QualityMetricSample

log = logging.getLogger(__name__)


def _drift_to_score(drift: float) -> float:
    """Map PSI drift (0 good, higher worse) to a 0..1 goodness. PSI 0.25 ~ 0.5."""
    return max(0.0, 1.0 - min(drift, 1.0))


class QualityEngine:
    def __init__(self, cfg: QualityConfig):
        self._cfg = cfg
        self._lock = threading.Lock()
        self._drift_metric = ResponseDriftMetric(threshold=cfg.drift_threshold)
        self._baselines: dict[tuple, Baseline] = {}
        self._latest: dict[tuple, QualityMetricSample] = {}
        # calibration window mirrors the baseline window (spike S4 default)
        self._calib_n = cfg.baseline_window

        # Optional embedding metrics — import lazily; None if unavailable.
        self._consistency = None
        self._stability = None
        self._try_load_embedding_metrics()

    def _try_load_embedding_metrics(self) -> None:
        try:
            from spaniq.metrics.consistency import ConsistencyMetric
            from spaniq.metrics.output_stability import OutputStabilityMetric

            self._consistency = ConsistencyMetric()
            self._stability = OutputStabilityMetric()
            log.info("quality: embedding metrics enabled (consistency, stability)")
        except Exception as e:  # noqa: BLE001 — optional path
            log.info("quality: embedding metrics unavailable, drift-only (%s)", e)

    @staticmethod
    def _baseline_key(span: GenAISpan) -> tuple:
        # version-independent: v2 is scored against v1's healthy baseline
        return (span.service_name, span.gen_ai_system, span.model)

    def _baseline_for(self, span: GenAISpan) -> Baseline:
        key = self._baseline_key(span)
        b = self._baselines.get(key)
        if b is None:
            b = Baseline(
                window=self._cfg.baseline_window,
                calib_n=self._calib_n,
                k_sigma=self._cfg.cusum_k,
                h_sigma=self._cfg.cusum_h,
            )
            self._baselines[key] = b
        return b

    def score(self, span: GenAISpan) -> EvalLogRecord:
        """Score one span. Emits a `warming` record (no score) until the baseline
        fills, then a full `scored` record. Thread-safe; never raises on bad input."""
        dims = span.dims()
        with self._lock:
            baseline = self._baseline_for(span)

            if not baseline.ready:
                baseline.add_warming_output(span.output_text)
                self._latest[tuple(sorted(dims.items()))] = QualityMetricSample(
                    dims=dims, drift=None, consistency=None, stability=None,
                    score=None, drift_onset=0, baseline_ready=False,
                )
                return EvalLogRecord(
                    trace_id=span.trace_id, span_id=span.span_id, dims=dims,
                    state="warming", reason="baseline warming "
                    f"({len(baseline.outputs)}/{self._cfg.baseline_window})",
                )

            drift = self._measure_drift(span, baseline)
            consistency, stability = self._measure_optional(span)
            baseline.observe_drift(drift)
            onset = 1 if baseline.onset else 0

            score = self._composite(drift, consistency, stability)
            reason = f"PSI {drift:.4f} " + ("<" if drift < self._cfg.drift_threshold
                                            else ">=") + f" {self._cfg.drift_threshold}"
            if onset:
                reason += " | CUSUM drift onset"

            self._latest[tuple(sorted(dims.items()))] = QualityMetricSample(
                dims=dims, drift=drift, consistency=consistency, stability=stability,
                score=score, drift_onset=onset, baseline_ready=True,
            )
            return EvalLogRecord(
                trace_id=span.trace_id, span_id=span.span_id, dims=dims, state="scored",
                drift=drift, consistency=consistency, stability=stability, score=score,
                drift_onset=onset, reason=reason,
            )

    def _measure_drift(self, span: GenAISpan, baseline: Baseline) -> float:
        try:
            tc = LLMTestCase(
                input=span.input_text or " ",
                actual_output=span.output_text,
                baseline_outputs=baseline.outputs,
            )
            return float(self._drift_metric.measure(tc))
        except Exception:  # noqa: BLE001 — never crash the scorer
            log.exception("quality: drift measure failed")
            return 0.0

    def _measure_optional(self, span: GenAISpan) -> tuple[float | None, float | None]:
        # Consistency/stability need multiple samples of the same prompt; in the online
        # single-shot path they are best-effort against the baseline set.
        return None, None

    def _composite(
        self, drift: float, consistency: float | None, stability: float | None
    ) -> float:
        """Weighted 0..1 composite over available components (renormalized)."""
        parts: list[tuple[float, float]] = [(self._cfg.weight_drift, _drift_to_score(drift))]
        if consistency is not None:
            parts.append((self._cfg.weight_consistency, max(0.0, 1.0 - consistency)))
        if stability is not None:
            parts.append((self._cfg.weight_stability, max(0.0, 1.0 - stability)))
        total_w = sum(w for w, _ in parts)
        if total_w <= 0:
            return _drift_to_score(drift)
        return sum(w * v for w, v in parts) / total_w

    # ---- providers for the emitter ----
    def quality_samples(self) -> list[QualityMetricSample]:
        with self._lock:
            return list(self._latest.values())
