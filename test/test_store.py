"""Unit tests for SQLite VerdictStore (spec §17)."""

import pytest
from vitals.store.db import VerdictStore
from vitals.verdict.types import (
    Cause,
    Exemplar,
    InconclusiveReason,
    Subject,
    Verdict,
    VerdictState,
)


def _make_verdict(vid: str, ts: float) -> Verdict:
    return Verdict(
        verdict_id=vid,
        ts_unix=ts,
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        version="v1",
        baseline_version=None,
        state=VerdictState.STEADY,
        subject=Subject.TIME,
        cause=Cause.NONE,
        flag_cost=False,
        flag_behavior=False,
        runaway=False,
        behavior_sigma=0.2,
        cost_sigma=0.1,
        cost_usd_per_req=0.001,
        baseline_cost_usd_per_req=0.001,
        velocity_ratio=1.0,
        samples=50,
        baseline_samples=30,
        onset_ts_unix=None,
        seconds_after_deploy=None,
        inconclusive_reason=None,
        caveats=(),
        falsifier="falsifier string",
        warming_progress=None,
        exemplars=(
            Exemplar(
                kind="worst",
                trace_id="tr1",
                span_id="sp1",
                output_excerpt="excerpt",
                behavior_sigma=1.2,
            ),
        ),
    )


def test_store_insert_get_list(tmp_path):
    db_path = tmp_path / "test_verdicts.db"
    store = VerdictStore(path=str(db_path))

    v1 = _make_verdict("v100000000000001", 100.0)
    v2 = _make_verdict("v100000000000002", 200.0)

    store.insert(v1)
    store.insert(v2)

    fetched_v1 = store.get("v100000000000001")
    assert fetched_v1 is not None
    assert fetched_v1.verdict_id == "v100000000000001"
    assert fetched_v1.ts_unix == 100.0
    assert fetched_v1.state == VerdictState.STEADY
    assert len(fetched_v1.exemplars) == 1
    assert fetched_v1.exemplars[0].trace_id == "tr1"

    verdicts = store.list(limit=50)
    assert len(verdicts) == 2
    # newest first
    assert verdicts[0].verdict_id == "v100000000000002"
    assert verdicts[1].verdict_id == "v100000000000001"

    store.close()


def test_store_retention_pruning(tmp_path):
    db_path = tmp_path / "test_retention.db"
    store = VerdictStore(path=str(db_path), retain_verdicts=3)

    for i in range(5):
        v = _make_verdict(f"v10000000000000{i}", 100.0 + i)
        store.insert(v)

    verdicts = store.list(limit=10)
    assert len(verdicts) == 3
    # should keep the 3 newest (timestamps 104.0, 103.0, 102.0)
    retained_ids = [v.verdict_id for v in verdicts]
    assert retained_ids == ["v100000000000004", "v100000000000003", "v100000000000002"]
    assert store.get("v100000000000000") is None

    store.close()


def test_store_error_swallowing(tmp_path, caplog):
    db_path = tmp_path / "test_err.db"
    store = VerdictStore(path=str(db_path))

    # Force connection to fail by closing it prematurely
    store.close()

    v = _make_verdict("v100000000000009", 500.0)
    # Should not raise exception
    store.insert(v)
    res = store.get("v100000000000009")
    assert res is None
    res_list = store.list()
    assert res_list == []
