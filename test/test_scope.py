"""Unit tests for ScopeState and RollingWindow (spec §17, §19)."""

from vitals.model import GenAISpan
from vitals.quality.types import EvalLogRecord
from vitals.verdict.scope import ScopeState


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


def test_scope_reference_freeze_and_calibration():
    scope = ScopeState(
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        reference_window=30,
        calib_n=30,
    )

    assert not scope.is_reference_ready()
    assert not scope.is_calibrated()
    assert not scope.is_live()

    # Feed 30 reference spans
    for i in range(30):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="warming",
            drift=None,
            input_drift=None,
            output_len=len(span.output_text),
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    assert scope.is_reference_ready()
    assert len(scope.reference_outputs) == 30
    assert len(scope.reference_inputs) == 30
    assert not scope.is_calibrated()
    assert not scope.is_live()

    # Feed 30 calibration spans (total 60 spans)
    for i in range(30, 60):
        span = _make_span(i)
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.05,
            input_drift=0.02,
            output_len=len(span.output_text),
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    # Now at 60 spans, scope reaches LIVE and all 4 signals are calibrated
    assert scope.is_calibrated()
    assert scope.is_live()
    for sig_name, sig in scope.signals.items():
        assert sig.calibrated(), f"Signal {sig_name} not calibrated"


def test_scope_rolling_window_cap_and_version_timeline():
    scope = ScopeState(
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        reference_window=10,
        calib_n=10,
        window_max=15,
    )

    # Feed reference spans
    for i in range(10):
        span = _make_span(i, version="v1")
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="warming",
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=100.0 + i)

    # Feed 20 v1 post-reference spans
    for i in range(10, 30):
        span = _make_span(i, version="v1")
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.01,
            input_drift=0.01,
            output_len=20,
        )
        scope.observe(span, rec, usd=0.001, now=100.0 + i)

    # Check rolling window maxlen cap (15)
    assert len(scope.windows["v1"]) == 15

    # Feed v2 span
    v2_span = _make_span(31, version="v2")
    v2_rec = EvalLogRecord(
        trace_id=v2_span.trace_id,
        span_id=v2_span.span_id,
        dims=v2_span.dims(),
        state="scored",
        drift=0.5,
        input_drift=0.01,
        output_len=25,
    )
    scope.observe(v2_span, v2_rec, usd=0.002, now=200.0)

    # Check version timeline contains both v1 and v2 with first seen timestamps
    timeline = scope.version_timeline
    assert len(timeline) == 2
    assert timeline[0] == ("v1", 100.0)
    assert timeline[1] == ("v2", 200.0)
