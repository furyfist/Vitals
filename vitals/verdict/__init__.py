"""Verdict package — evaluation models, signals, scope state, attribution, and evaluator."""

from vitals.verdict.attribution import attribute_change
from vitals.verdict.evaluator import evaluate_scope_version, select_exemplars
from vitals.verdict.scope import ScopeState, SpanRecord
from vitals.verdict.signal import CalibratedSignal
from vitals.verdict.types import (
    Cause,
    Exemplar,
    InconclusiveReason,
    Subject,
    Verdict,
    VerdictState,
)

__all__ = [
    "VerdictState",
    "Subject",
    "Cause",
    "InconclusiveReason",
    "Exemplar",
    "Verdict",
    "CalibratedSignal",
    "ScopeState",
    "SpanRecord",
    "attribute_change",
    "evaluate_scope_version",
    "select_exemplars",
]
