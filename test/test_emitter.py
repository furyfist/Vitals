"""Unit tests for Emitter verdict telemetry and SigNoz alert rules (spec §17)."""

import json
from pathlib import Path
import pytest
from opentelemetry._logs import SeverityNumber
from vitals.cost.engine import CostEngine
from vitals.cost.prices import PriceTable
from vitals.emit.emitter import Emitter
from vitals.health import Health
from vitals.verdict.types import (
    Cause,
    Exemplar,
    InconclusiveReason,
    Subject,
    Verdict,
    VerdictState,
)


def _make_verdict(state: VerdictState = VerdictState.STEADY) -> Verdict:
    return Verdict(
        verdict_id="abcdef1234567890",
        ts_unix=1700000000.0,
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        version="v1",
        baseline_version=None,
        state=state,
        subject=Subject.TIME,
        cause=Cause.NONE,
        flag_cost=False,
        flag_behavior=(state == VerdictState.CHANGED),
        runaway=False,
        behavior_sigma=4.2 if state == VerdictState.CHANGED else 0.2,
        cost_sigma=0.1,
        cost_usd_per_req=0.001,
        baseline_cost_usd_per_req=0.001,
        velocity_ratio=1.0,
        samples=100,
        baseline_samples=30,
        onset_ts_unix=1700000000.0 if state == VerdictState.CHANGED else None,
        seconds_after_deploy=90.0 if state == VerdictState.CHANGED else None,
        inconclusive_reason=None,
        caveats=("output_length_-10%",),
        falsifier="falsifier string",
        warming_progress=None,
        exemplars=(
            Exemplar(
                kind="worst",
                trace_id="4f2a9100000000000000000000000000",
                span_id="91cd070000000000",
                output_excerpt="worst response excerpt",
                behavior_sigma=4.2,
            ),
            Exemplar(
                kind="median",
                trace_id="11111100000000000000000000000000",
                span_id="2222220000000000",
                output_excerpt="median response excerpt",
                behavior_sigma=0.2,
            ),
        ),
    )


def test_emitter_verdict_provider_and_log_record():
    verdicts_list = [_make_verdict(VerdictState.CHANGED)]
    cost = CostEngine(PriceTable.from_yaml("vitals/cost/prices.yaml"))
    health = Health()

    emitter = Emitter(
        endpoint="http://localhost:4317",
        export_interval_ms=5000,
        cost_provider=cost.sample,
        quality_provider=lambda: [],
        health_provider=health.snapshot,
        verdict_provider=lambda: verdicts_list,
    )

    try:
        # Emit a CHANGED verdict log record
        v_changed = verdicts_list[0]
        emitter.emit_verdict_log(v_changed)

        # Emit a STEADY verdict log record
        v_steady = _make_verdict(VerdictState.STEADY)
        emitter.emit_verdict_log(v_steady)

    finally:
        emitter.shutdown()


def test_verdict_changed_alert_rule_format():
    alert_path = Path("assets/alerts/verdict-changed.json")
    assert alert_path.is_file(), "assets/alerts/verdict-changed.json must exist"

    data = json.loads(alert_path.read_text())
    assert data["alert"] == "Vitals: verdict changed"
    assert data["condition"]["op"] == ">="
    assert data["condition"]["target"] == 2  # CHANGED (2) or INCONCLUSIVE (3)
    # v5 rule query schema (condition.compositeQuery.queries[].spec) — verified against a
    # live SigNoz v0.133.0 instance via /api/v2/rules; the older builder.queryData shape
    # is rejected outright ("must have at least one query").
    assert (
        data["condition"]["compositeQuery"]["queries"][0]["spec"]["aggregations"][0]["metricName"]
        == "vitals.verdict.state"
    )

    # Verify retired V1 rules are deleted
    assert not Path("assets/alerts/cost-velocity.json").exists()
    assert not Path("assets/alerts/quality-drift-onset.json").exists()
    assert not Path("assets/alerts/version-regression.json").exists()
