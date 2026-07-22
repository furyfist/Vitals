"""Unit tests: baseline warming, drift scoring, CUSUM onset — never-over-report."""

from __future__ import annotations

from vitals.config.settings import QualityConfig
from vitals.model import GenAISpan
from vitals.quality.engine import QualityEngine

HEALTHY = "OpenTelemetry is an open source observability framework for traces metrics logs"
POISONED = "banana banana purple sky jump running quickly nonsense token soup random"


def _cfg(window=5):
    return QualityConfig(baseline_window=window, cusum_k=0.5, cusum_h=3.0)


def _span(text, sv="v1", tid="t", sid="s"):
    return GenAISpan(
        trace_id=tid, span_id=sid, service_name="rag", service_version=sv,
        gen_ai_system="groq", model="llama-3.3-70b-versatile",
        input_text="what is otel?", output_text=text,
        input_tokens=10, output_tokens=20, start_unix_nano=0, end_unix_nano=1,
    )


def test_warming_emits_no_score():
    eng = QualityEngine(_cfg(window=5))
    for i in range(4):
        rec = eng.score(_span(HEALTHY + f" {i}"))
        assert rec.state == "warming"
        assert rec.score is None
        assert rec.drift is None


def test_scores_after_baseline_ready():
    eng = QualityEngine(_cfg(window=5))
    for i in range(5):
        eng.score(_span(HEALTHY + f" variant {i}"))
    rec = eng.score(_span(HEALTHY + " another healthy sentence"))
    assert rec.state == "scored"
    assert rec.drift is not None
    assert rec.score is not None
    assert 0.0 <= rec.score <= 1.0


def test_healthy_traffic_never_false_alarms():
    eng = QualityEngine(_cfg(window=5))
    onsets = 0
    for i in range(40):
        rec = eng.score(_span(HEALTHY + f" clean run token {i % 7}"))
        if rec.drift_onset:
            onsets += 1
    # zero-false-positive budget on a clean run (spike S4)
    assert onsets == 0


def test_poisoned_deploy_raises_drift_and_onset():
    eng = QualityEngine(_cfg(window=5))
    # warm + calibrate on healthy v1
    for i in range(12):
        eng.score(_span(HEALTHY + f" token {i % 5}", sv="v1"))
    # deploy poisoned v2 — scored against v1's healthy baseline
    saw_onset = False
    high_drift = False
    for i in range(20):
        rec = eng.score(_span(POISONED + f" {i}", sv="v2"))
        if rec.drift and rec.drift > 0.1:
            high_drift = True
        if rec.drift_onset:
            saw_onset = True
    assert high_drift, "poisoned output should drift from healthy baseline"
    assert saw_onset, "CUSUM should flag drift onset on sustained poisoning"


def test_version_dimension_preserved():
    eng = QualityEngine(_cfg(window=3))
    for i in range(4):
        eng.score(_span(HEALTHY + f" {i}", sv="v1"))
    eng.score(_span(HEALTHY + " x", sv="v2"))
    versions = {s.dims["service.version"] for s in eng.quality_samples()}
    assert "v2" in versions
