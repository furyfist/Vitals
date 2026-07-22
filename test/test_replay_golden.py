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
from vitals.verdict.types import Cause, InconclusiveReason, Verdict, VerdictState

FIXTURES_DIR = Path("demo/fixtures")


def _run_scenario_with_state_sequence(
    fixture_filename: str, tmp_path
) -> tuple[list[VerdictState], Verdict]:
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
    observed_states: list[VerdictState] = []
    last_state = None
    last_verdict = None

    def on_span(span, now_ts):
        nonlocal last_state, last_verdict
        cost_engine.record(span, now=now_ts)
        usd = prices.cost_usd(span.model, span.input_tokens, span.output_tokens)
        rec = quality_engine.score(span)
        scope.observe(span, rec, usd, now=now_ts)

        versions = list(scope.windows.keys())
        target_ver = versions[-1] if versions else span.service_version
        v = evaluate_scope_version(scope, target_ver, cfg, now_ts, cost_engine)
        if v:
            last_verdict = v
            if v.state != last_state:
                observed_states.append(v.state)
                last_state = v.state

    fix_file = FIXTURES_DIR / fixture_filename
    run_replay(fix_file, speed=0.0, on_span_cb=on_span)

    assert last_verdict is not None, f"Expected verdict for scenario {fixture_filename}"
    store.insert(last_verdict)
    store.close()

    return observed_states, last_verdict


def test_golden_01_steady_baseline(tmp_path):
    states, final_v = _run_scenario_with_state_sequence("01_steady_baseline.jsonl", tmp_path)
    assert states == [VerdictState.WARMING, VerdictState.STEADY]
    assert VerdictState.CHANGED not in states
    assert final_v.state == VerdictState.STEADY


def test_golden_02_release_regression(tmp_path):
    states, final_v = _run_scenario_with_state_sequence("02_release_regression.jsonl", tmp_path)
    assert VerdictState.WARMING in states
    assert VerdictState.STEADY in states
    assert VerdictState.CHANGED in states
    assert final_v.state == VerdictState.CHANGED
    assert final_v.cause == Cause.RELEASE
    assert final_v.seconds_after_deploy is not None
    assert 0.0 <= final_v.seconds_after_deploy <= 300.0


def test_golden_03_runaway_loop(tmp_path):
    states, final_v = _run_scenario_with_state_sequence("03_runaway_loop.jsonl", tmp_path)
    assert VerdictState.WARMING in states
    assert VerdictState.STEADY in states
    assert VerdictState.CHANGED in states
    assert final_v.state == VerdictState.CHANGED
    assert final_v.runaway is True


def test_golden_04_input_shift(tmp_path):
    states, final_v = _run_scenario_with_state_sequence("04_input_shift.jsonl", tmp_path)
    assert VerdictState.CHANGED not in states
    assert final_v.state == VerdictState.INCONCLUSIVE
    assert final_v.inconclusive_reason == InconclusiveReason.INPUT_SHIFT
