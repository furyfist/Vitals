"""Unit tests for Verdict Evaluator and Exemplar Selection (spec §4.5, §9, §17)."""

from vitals.config.settings import VerdictConfig
from vitals.model import GenAISpan
from vitals.quality.types import EvalLogRecord
from vitals.verdict.evaluator import evaluate_scope_version, select_exemplars
from vitals.verdict.scope import ScopeState, SpanRecord
from vitals.verdict.types import VerdictState


def _make_span(i: int, version: str = "v1") -> GenAISpan:
    return GenAISpan(
        trace_id=f"tr_{i:04d}",
        span_id=f"sp_{i:04d}",
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        service_version=version,
        input_text=f"input query {i}",
        output_text=f"output response {i}\n  line2  line3",
        input_tokens=10,
        output_tokens=20,
        start_unix_nano=1000000000,
        end_unix_nano=2000000000,
    )


def test_select_exemplars_includes_worst_and_median():
    recs = [
        SpanRecord(
            ts=100.0 + i,
            behavior_psi=0.1 * i,
            input_psi=0.01,
            usd=0.001,
            out_len=20,
            trace_id=f"tr_{i}",
            span_id=f"sp_{i}",
            output_excerpt=f"excerpt {i}",
        )
        for i in range(5)  # behavior_psi: 0.0, 0.1, 0.2, 0.3, 0.4
    ]

    exemplars = select_exemplars(recs, behavior_z=2.5, worst_count=2, median_count=1)

    assert len(exemplars) == 3  # 2 worst + 1 median
    kinds = [ex.kind for ex in exemplars]
    assert kinds.count("worst") == 2
    assert kinds.count("median") == 1

    # Worst exemplars should have highest behavior_psi (trace_id tr_4 and tr_3)
    worst_traces = [ex.trace_id for ex in exemplars if ex.kind == "worst"]
    assert "tr_4" in worst_traces
    assert "tr_3" in worst_traces

    # Median exemplar should be middle index (tr_2)
    median_ex = [ex for ex in exemplars if ex.kind == "median"][0]
    assert median_ex.trace_id == "tr_2"


def test_evaluator_end_to_end_steady_and_changed():
    cfg = VerdictConfig(
        min_samples=5,
        calibration_samples=5,
        consecutive_ticks=1,
        sigma_threshold=3.0,
    )
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)

    # 1. Calibrate scope (5 ref + 5 calib)
    for i in range(10):
        span = _make_span(i, version="v1")
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored" if i >= 5 else "warming",
            drift=0.01,
            input_drift=0.01,
            output_len=len(span.output_text),
        )
        scope.observe(span, rec, usd=0.001, now=1000.0 + i)

    assert scope.is_live()

    # 2. Evaluate steady state
    v_steady = evaluate_scope_version(scope, "v1", cfg, now=1050.0)
    assert v_steady is not None
    assert v_steady.state == VerdictState.STEADY
    assert len(v_steady.exemplars) >= 2  # contains worst and median
    assert v_steady.sentence.startswith("STEADY · ragapp v1")

    # 3. Deploy v2 (version change) with high behavior drift
    for i in range(10, 20):
        span = _make_span(i, version="v2")
        rec = EvalLogRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            dims=span.dims(),
            state="scored",
            drift=0.50,  # high behavior drift
            input_drift=0.01,
            output_len=len(span.output_text),
        )
        scope.observe(span, rec, usd=0.001, now=1100.0 + i)

    # 4. Evaluate v2 -> CHANGED with release attribution
    v_changed = evaluate_scope_version(scope, "v2", cfg, now=1120.0)
    assert v_changed is not None
    assert v_changed.state == VerdictState.CHANGED
    assert v_changed.flag_behavior is True
    assert v_changed.cause.value == "release"
    assert v_changed.baseline_version == "v1"
    assert v_changed.seconds_after_deploy is not None
    assert "v2 vs v1" in v_changed.sentence
