"""Integration test for EvaluatorThread daemon (spec §4.5, §13, §15)."""

import time
import pytest
from vitals.config.settings import VerdictConfig
from vitals.cost.engine import CostEngine
from vitals.cost.prices import PriceTable
from vitals.health import Health
from vitals.main import EvaluatorThread
from vitals.model import GenAISpan
from vitals.quality.types import EvalLogRecord
from vitals.store.db import VerdictStore
from vitals.verdict.scope import ScopeState
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
        output_text=f"output response {i}",
        input_tokens=10,
        output_tokens=20,
        start_unix_nano=1000000000,
        end_unix_nano=2000000000,
    )


def test_evaluator_daemon_thread_lifecycle(tmp_path):
    db_path = tmp_path / "eval_daemon.db"
    store = VerdictStore(str(db_path))
    health = Health()
    prices = PriceTable.from_yaml("vitals/cost/prices.yaml")
    cost_engine = CostEngine(prices)

    cfg = VerdictConfig(
        enabled=True,
        evaluate_interval_s=1,
        min_samples=5,
        calibration_samples=5,
        heartbeat_s=10,
    )

    scope_key = ("ragapp", "openai", "gpt-4o")
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=5, calib_n=5)
    scopes = {scope_key: scope}

    # Populate 10 spans (5 reference + 5 calibration) to bring scope to LIVE
    now = time.time()
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
        scope.observe(span, rec, usd=0.001, now=now + i)

    evaluator = EvaluatorThread(scopes, store, cfg, cost_engine, health)
    evaluator.start()

    try:
        # Give evaluator daemon thread time to tick
        time.sleep(1.5)

        verdicts = store.list(limit=10)
        assert len(verdicts) >= 1
        latest = verdicts[0]
        assert latest.state == VerdictState.STEADY
        assert health.verdicts_emitted >= 1

    finally:
        evaluator.stop()
        evaluator.join(timeout=2.0)
        store.close()
