"""Unit tests for Console server, API routes, and HTML rendering (spec §9, §17)."""

import json
import threading
import urllib.request
import pytest
from vitals.console import create_console_server, render_console_html
from vitals.health import Health
from vitals.store import VerdictStore
from vitals.verdict.scope import ScopeState
from vitals.verdict.types import (
    Cause,
    Exemplar,
    Subject,
    Verdict,
    VerdictState,
)


def _make_sample_verdict() -> Verdict:
    return Verdict(
        verdict_id="c0123456789abcde",
        ts_unix=1700000000.0,
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        version="v2",
        baseline_version="v1",
        state=VerdictState.CHANGED,
        subject=Subject.RELEASE,
        cause=Cause.RELEASE,
        flag_cost=False,
        flag_behavior=True,
        runaway=False,
        behavior_sigma=4.2,
        cost_sigma=0.3,
        cost_usd_per_req=0.002,
        baseline_cost_usd_per_req=0.002,
        velocity_ratio=1.0,
        samples=100,
        baseline_samples=30,
        onset_ts_unix=1700000000.0,
        seconds_after_deploy=90.0,
        inconclusive_reason=None,
        caveats=("output_length_-15%",),
        falsifier="falsifier check",
        warming_progress=None,
        exemplars=(
            Exemplar(
                kind="worst",
                trace_id="4f2a9100000000000000000000000000",
                span_id="91cd070000000000",
                output_excerpt="worst excerpt",
                behavior_sigma=4.2,
            ),
            Exemplar(
                kind="median",
                trace_id="11111100000000000000000000000000",
                span_id="2222220000000000",
                output_excerpt="median excerpt",
                behavior_sigma=0.3,
            ),
        ),
    )


def test_console_html_renderer():
    v = _make_sample_verdict()
    health = Health()

    html = render_console_html(
        latest_verdict=v,
        verdict_feed=[v],
        scopes=[],
        health_snapshot=health.snapshot(),
        start_time=1700000000.0,
    )

    assert "<!DOCTYPE html>" in html
    assert "CHANGED" in html
    assert "ragapp" in html
    assert "worst excerpt" in html
    assert "median excerpt" in html
    assert "spans:" in html


def test_console_server_http_routes(tmp_path):
    db_path = tmp_path / "console_test.db"
    store = VerdictStore(str(db_path))
    health = Health()

    v = _make_sample_verdict()
    store.insert(v)

    scope_key = ("ragapp", "openai", "gpt-4o")
    scope = ScopeState("ragapp", "openai", "gpt-4o")
    scopes = {scope_key: scope}

    port = 18787
    server = create_console_server("127.0.0.1", port, store, scopes, health)
    assert server is not None

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        # GET /
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8")
            assert "Vitals Console" in body
            assert "CHANGED" in body

        # GET /api/verdicts
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/verdicts") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "verdicts" in data
            assert len(data["verdicts"]) == 1
            assert data["verdicts"][0]["verdict_id"] == v.verdict_id

        # GET /api/verdicts/{id}
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/verdicts/{v.verdict_id}") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["verdict_id"] == v.verdict_id

        # GET /api/scopes
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/scopes") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "scopes" in data
            assert len(data["scopes"]) == 1

        # GET /api/health
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "spans_received" in data
            assert "version" in data

    finally:
        server.shutdown()
        server.server_close()
        store.close()
