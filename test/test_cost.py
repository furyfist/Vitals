"""Unit tests: cost math — exhaustive per §9."""

from __future__ import annotations

from vitals.cost.engine import CostEngine
from vitals.cost.prices import PriceTable
from vitals.model import GenAISpan


def _span(model="llama-3.3-70b-versatile", tin=1000, tout=500, sv="v1"):
    return GenAISpan(
        trace_id="t", span_id="s", service_name="rag", service_version=sv,
        gen_ai_system="groq", model=model, input_text="q", output_text="a",
        input_tokens=tin, output_tokens=tout, start_unix_nano=0, end_unix_nano=1,
    )


def _table():
    return PriceTable.from_yaml("vitals/cost/prices.yaml")


def test_price_lookup_known_model():
    t = _table()
    # 1000 in * 0.59/1e6 + 500 out * 0.79/1e6
    expected = 1000 * 0.59 / 1e6 + 500 * 0.79 / 1e6
    assert abs(t.cost_usd("llama-3.3-70b-versatile", 1000, 500) - expected) < 1e-12


def test_price_lookup_is_case_insensitive():
    t = _table()
    assert t.cost_usd("GPT-4O", 1000, 0) == t.cost_usd("gpt-4o", 1000, 0)


def test_unknown_model_falls_back_to_default():
    t = _table()
    # default: 0.50 in / 1.50 out per 1M
    assert abs(t.cost_usd("some-unknown-model", 1_000_000, 1_000_000) - (0.50 + 1.50)) < 1e-9


def test_total_accumulates():
    eng = CostEngine(_table(), window_s=60)
    for _ in range(3):
        eng.record(_span(), now=0.0)
    samples = eng.sample(now=0.0)
    assert len(samples) == 1
    per_call = _table().cost_usd("llama-3.3-70b-versatile", 1000, 500)
    assert abs(samples[0].total_usd - 3 * per_call) < 1e-12


def test_velocity_extrapolates_to_per_minute():
    eng = CostEngine(_table(), window_s=60)
    # one call worth $X within the window -> velocity ~ X * (60/60) = X per minute
    eng.record(_span(), now=10.0)
    s = eng.sample(now=10.0)[0]
    per_call = _table().cost_usd("llama-3.3-70b-versatile", 1000, 500)
    assert abs(s.velocity_usd_per_min - per_call) < 1e-12


def test_velocity_window_eviction():
    eng = CostEngine(_table(), window_s=60)
    eng.record(_span(), now=0.0)
    # 120s later the sample has aged out of the 60s window
    s = eng.sample(now=120.0)[0]
    assert s.velocity_usd_per_min == 0.0
    # but total is retained
    assert s.total_usd > 0.0


def test_dimensions_split_by_version():
    eng = CostEngine(_table(), window_s=60)
    eng.record(_span(sv="v1"), now=0.0)
    eng.record(_span(sv="v2"), now=0.0)
    samples = eng.sample(now=0.0)
    versions = {s.dims["service.version"] for s in samples}
    assert versions == {"v1", "v2"}
