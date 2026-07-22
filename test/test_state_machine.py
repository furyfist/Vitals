"""Unit tests for Verdict state machine (spec §17)."""

from vitals.config.settings import VerdictConfig
from vitals.model import GenAISpan
from vitals.quality.types import EvalLogRecord
from vitals.verdict.evaluator import evaluate_scope_version
from vitals.verdict.scope import ScopeState
from vitals.verdict.types import InconclusiveReason, VerdictState


def _make_span(i: int, version: str = "v1") -> GenAISpan:
    return GenAISpan(
        trace_id=f"tr_{i:04d}",
        span_id=f"sp_{i:04d}",
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        service_version=version,
        input_text=f"input query {i}",
        output_text=f"output response {i}",
        input_tokens=10,
        output_tokens=20,
        start_unix_nano=1000000000,
        end_unix_nano=2000000000,
    )


def test_state_machine_hysteresis_2_ticks():
    cfg = VerdictConfig(
        min_samples=5, calibration_samples=5, consecutive_ticks=2, min_hold_s=120
    )
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)

    # Calibrate scope (5 reference + 5 calibration)
    for i in range(10):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored" if i >= 5 else "warming",
            drift=0.01,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    assert scope.is_live()

    # Initial tick: STEADY
    v0 = evaluate_scope_version(scope, "v1", cfg, now=1100.0)
    assert v0.state == VerdictState.STEADY

    # Add high behavior drift spans (10 spans)
    for i in range(10, 20):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.50,  # high behavior drift
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1100.0 + i)

    # Tick 1: Condition True on 1st tick -> remain STEADY (consecutive_ticks=1 < 2)
    v1 = evaluate_scope_version(scope, "v1", cfg, now=1110.0)
    assert v1.state == VerdictState.STEADY

    # Tick 2: Condition True on 2nd tick -> transition to CHANGED
    v2 = evaluate_scope_version(scope, "v1", cfg, now=1120.0)
    assert v2.state == VerdictState.CHANGED
    assert v2.flag_behavior is True


def test_state_machine_runaway_bypass_hysteresis():
    cfg = VerdictConfig(
        min_samples=5, calibration_samples=5, consecutive_ticks=2, runaway_ratio=5.0
    )
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)

    # Calibrate scope
    for i in range(10):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored" if i >= 5 else "warming",
            drift=0.01,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    # Spike USD cost massively (runaway velocity)
    for i in range(10, 50):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.01,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.50, now=1100.0 + i)

    # Tick 1: Runaway bypasses hysteresis immediately
    v1 = evaluate_scope_version(scope, "v1", cfg, now=1110.0)
    assert v1.state == VerdictState.CHANGED
    assert v1.runaway is True
    assert v1.flag_cost is True


def test_state_machine_min_hold_dwell():
    cfg = VerdictConfig(
        min_samples=5,
        calibration_samples=5,
        consecutive_ticks=1,
        min_hold_s=120,
        window_s=60,
    )
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)

    # Calibrate scope
    for i in range(10):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored" if i >= 5 else "warming",
            drift=0.01,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    # Trigger CHANGED at t=1050
    for i in range(10, 20):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.50,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1050.0 + i)

    v_changed = evaluate_scope_version(scope, "v1", cfg, now=1060.0)
    assert v_changed.state == VerdictState.CHANGED

    # Now condition clears (clean spans at t=1140, lookback window=60s clears old t=1060 high-drift spans)
    for i in range(20, 30):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.01,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1140.0 + i)

    # At t=1150 (90s dwell since onset t=1060, < 120s min_hold_s) -> must remain CHANGED due to dwell hold
    v_held = evaluate_scope_version(scope, "v1", cfg, now=1150.0)
    assert v_held.state == VerdictState.CHANGED

    # At t=1200 (140s dwell since onset t=1060, > 120s min_hold_s) -> transitions back to STEADY
    v_steady = evaluate_scope_version(scope, "v1", cfg, now=1200.0)
    assert v_steady.state == VerdictState.STEADY


def test_state_machine_inconclusive_non_latching():
    cfg = VerdictConfig(
        min_samples=5,
        calibration_samples=5,
        consecutive_ticks=1,
        sigma_threshold=3.0,
        window_s=60,
    )
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)

    # Calibrate scope
    for i in range(10):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored" if i >= 5 else "warming",
            drift=0.01,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    # Cause input shift G2 (co-movement) at t=1050
    for i in range(10, 20):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.50,
            input_drift=0.50,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1050.0 + i)

    v_inc = evaluate_scope_version(scope, "v1", cfg, now=1060.0)
    assert v_inc.state == VerdictState.INCONCLUSIVE
    assert v_inc.inconclusive_reason == InconclusiveReason.INPUT_SHIFT

    # Next clean tick at t=1200 (> window_s=60s so old input shift spans fall out)
    for i in range(20, 30):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.01,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=1200.0 + i)

    v_clean = evaluate_scope_version(scope, "v1", cfg, now=1210.0)
    # INCONCLUSIVE did not latch; cleanly returned to STEADY
    assert v_clean.state == VerdictState.STEADY
