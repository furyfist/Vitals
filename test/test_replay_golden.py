"""Golden replay integration test suite verifying exact verdicts across 4 scenarios (spec §10, §17)."""

from pathlib import Path
import pytest
from vitals.config.settings import QualityConfig, VerdictConfig
from vitals.cost.engine import CostEngine
from vitals.cost.prices import PriceTable
from vitals.quality.engine import QualityEngine
from vitals.replay.runner import run_replay
from vitals.store.db import VerdictStore
from vitals.verdict.evaluator import evaluate_scope_version
from vitals.verdict.scope import ScopeState
from vitals.verdict.types import Cause, InconclusiveReason, VerdictState

FIXTURES_DIR = Path("demo/fixtures")


def _run_scenario_evaluation(
    fixture_filename: str, tmp_path
) -> tuple[VerdictState, Cause | None, InconclusiveReason | None, bool]:
    db_path = tmp_path / f"store_{fixture_filename}.db"
    store = VerdictStore(str(db_path))

    prices = PriceTable.from_yaml("vitals/cost/prices.yaml")
    cost_engine = CostEngine(prices, window_s=300)
    quality_engine = QualityEngine(QualityConfig(baseline_window=30))

    cfg = VerdictConfig(
        enabled=True,
        min_samples=5,
        calibration_samples=5,
        window_max=500,
        evaluate_interval_s=1,
        window_s=300,
    )

    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=30, calib_n=5)
    virtual_clock = [0.0]

    def on_span(span, now_ts):
        cost_engine.record(span, now=now_ts)
        usd = prices.cost_usd(span.model, span.input_tokens, span.output_tokens)
        rec = quality_engine.score(span)
        scope.observe(span, rec, usd, now=now_ts)
        virtual_clock[0] = now_ts

    fix_file = FIXTURES_DIR / fixture_filename
    run_replay(fix_file, speed=0.0, on_span_cb=on_span)

    now = virtual_clock[0]
    versions = list(scope.windows.keys())
    target_ver = versions[-1] if versions else "v1"

    verdict1 = evaluate_scope_version(scope, target_ver, cfg, now, cost_engine)
    if verdict1:
        scope.last_verdict = verdict1
        store.insert(verdict1)

    verdict2 = evaluate_scope_version(scope, target_ver, cfg, now + 10.0, cost_engine)
    final_v = verdict2 or verdict1

    assert final_v is not None, f"Expected verdict for scenario {fixture_filename}"
    store.insert(final_v)
    store.close()

    return final_v.state, final_v.cause, final_v.inconclusive_reason, final_v.runaway


def test_golden_01_steady_baseline(tmp_path):
    state, cause, inc_reason, runaway = _run_scenario_evaluation(
        "01_steady_baseline.jsonl", tmp_path
    )
    assert state == VerdictState.STEADY


def test_golden_02_release_regression(tmp_path):
    state, cause, inc_reason, runaway = _run_scenario_evaluation(
        "02_release_regression.jsonl", tmp_path
    )
    assert state == VerdictState.CHANGED
    assert cause == Cause.RELEASE


def test_golden_03_runaway_loop(tmp_path):
    state, cause, inc_reason, runaway = _run_scenario_evaluation(
        "03_runaway_loop.jsonl", tmp_path
    )
    assert state == VerdictState.CHANGED
    assert runaway is True


def test_golden_04_input_shift(tmp_path):
    state, cause, inc_reason, runaway = _run_scenario_evaluation(
        "04_input_shift.jsonl", tmp_path
    )
    assert state == VerdictState.INCONCLUSIVE
    assert inc_reason == InconclusiveReason.INPUT_SHIFT
