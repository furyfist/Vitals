"""Shared quality value types produced by the quality engine, consumed by emit."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QualityMetricSample:
    """Per-dimension latest quality state -> observable gauges."""

    dims: dict[str, str]
    drift: float | None
    consistency: float | None
    stability: float | None
    score: float | None  # composite 0..1
    drift_onset: int  # 1 if CUSUM has alarmed for this dimension, else 0
    baseline_ready: bool  # False while warming


@dataclass
class EvalLogRecord:
    """Per-scored-response log record, trace_id-linked for SigNoz drill-down."""

    trace_id: str
    span_id: str
    dims: dict[str, str]
    state: str  # "warming" | "scored"
    drift: float | None = None
    consistency: float | None = None
    stability: float | None = None
    score: float | None = None
    drift_onset: int = 0
    reason: str = ""
    attributes: dict = field(default_factory=dict)
