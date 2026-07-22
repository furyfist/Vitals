"""Unit tests for guards G0-G3 (spec §17, §19)."""

from vitals.config.settings import VerdictConfig
from vitals.model import GenAISpan
from vitals.quality.types import EvalLogRecord
from vitals.verdict.evaluator import evaluate_scope_version
from vitals.verdict.scope import ScopeState
from vitals.verdict.types import InconclusiveReason, VerdictState


def _make_span(i: int, version: str = "v1", out_len: int = 100) -> GenAISpan:
    return GenAISpan(
        trace_id=f"tr_{i:04d}",
        span_id=f"sp_{i:04d}",
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        service_version=version,
        input_text=f"input query {i}",
        output_text="x" * out_len,
        input_tokens=10,
        output_tokens=out_len // 4,
        start_unix_nano=1000000000,
        end_unix_nano=2000000000,
    )


def test_guard_g0_warming():
    cfg = VerdictConfig(min_samples=10, calibration_samples=10)
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=10, calib_n=10)

    verdict = evaluate_scope_version(scope, "v1", cfg, now=1000.0)
    assert verdict is not None
    assert verdict.state == VerdictState.WARMING
    assert verdict.inconclusive_reason == InconclusiveReason.WARMING


def test_guard_g1_low_sample():
    cfg = VerdictConfig(min_samples=30, calibration_samples=5)
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)

    # Populate 5 reference + 5 calibration spans (scope becomes LIVE)
    for i in range(10):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored" if i >= 5 else "warming",
            drift=0.01 if i >= 5 else None,
            input_drift=0.01 if i >= 5 else None,
            output_len=100,
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    assert scope.is_live()

    # Now evaluate version v1, which only has 5 spans in window (< min_samples 30)
    verdict = evaluate_scope_version(scope, "v1", cfg, now=1100.0)
    assert verdict is not None
    assert verdict.state == VerdictState.INCONCLUSIVE
    assert verdict.inconclusive_reason == InconclusiveReason.LOW_SAMPLE


def test_guard_g2_input_shift():
    cfg = VerdictConfig(min_samples=10, calibration_samples=5, sigma_threshold=3.0)
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)

    # Calibrate scope with low noise
    for i in range(10):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored" if i >= 5 else "warming",
            drift=0.01,
            input_drift=0.01,
            output_len=100,
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    assert scope.is_live()

    # Add 15 spans with HIGH behavior drift AND HIGH input drift (co-movement)
    for i in range(10, 25):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.50,  # high behavior drift
            input_drift=0.50,  # high input drift
            output_len=100,
        )
        scope.observe(span, rec, usd=0.001, now=1100.0 + i)

    verdict = evaluate_scope_version(scope, "v1", cfg, now=1200.0)
    assert verdict is not None
    assert verdict.state == VerdictState.INCONCLUSIVE
    assert verdict.inconclusive_reason == InconclusiveReason.INPUT_SHIFT


def test_guard_g3_length_shift_caveat_does_not_change_state():
    cfg = VerdictConfig(min_samples=10, calibration_samples=5, length_caveat_pct=0.25)
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)

    # Calibrate scope with output_len = 100
    for i in range(10):
        span = _make_span(i, out_len=100)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored" if i >= 5 else "warming",
            drift=0.01,
            input_drift=0.01,
            output_len=100,
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    # Add spans with output_len = 50 (50% reduction, abs(pct) >= 0.25)
    for i in range(10, 30):
        span = _make_span(i, out_len=50)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.01,  # normal behavior
            input_drift=0.01,  # normal input
            output_len=50,
        )
        scope.observe(span, rec, usd=0.001, now=1100.0 + i)

    verdict = evaluate_scope_version(scope, "v1", cfg, now=1200.0)
    assert verdict is not None
    # G3 produces caveat ONLY, state remains STEADY (D8 regression test)
    assert verdict.state == VerdictState.STEADY
    assert any("output_length_" in c for c in verdict.caveats)
