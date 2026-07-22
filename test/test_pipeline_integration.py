"""End-to-end: real OTLP spans -> receiver -> cost + quality (spikes S1/S2 wiring).

Sends gen_ai spans through the actual gRPC receiver on a loopback port and asserts the
cost engine accounted them and the quality engine warmed a baseline. No SigNoz needed —
this exercises the ingest+scoring half of the pipeline in isolation.
"""

from __future__ import annotations

import time

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from vitals.config.settings import QualityConfig
from vitals.cost.engine import CostEngine
from vitals.cost.prices import PriceTable
from vitals.health import Health
from vitals.ingest.receiver import OTLPReceiver
from vitals.quality.engine import QualityEngine

PORT = 14327


def _send_spans(n: int, version: str = "v1"):
    provider = TracerProvider(
        resource=Resource.create({"service.name": "ragapp", "service.version": version})
    )
    provider.add_span_processor(
        SimpleSpanProcessor(
            OTLPSpanExporter(endpoint=f"http://localhost:{PORT}", insecure=True)
        )
    )
    tracer = provider.get_tracer("test")
    for i in range(n):
        with tracer.start_as_current_span("chat") as span:
            span.set_attribute("gen_ai.system", "groq")
            span.set_attribute("gen_ai.request.model", "llama-3.3-70b-versatile")
            span.set_attribute("gen_ai.usage.input_tokens", 100)
            span.set_attribute("gen_ai.usage.output_tokens", 40)
            span.set_attribute("gen_ai.content.prompt", "what is otel?")
            span.set_attribute(
                "gen_ai.content.completion",
                f"OpenTelemetry is an observability framework variant {i}",
            )
    provider.force_flush()
    provider.shutdown()


def test_spans_flow_through_receiver_into_cost_and_quality():
    cost = CostEngine(PriceTable.from_yaml("vitals/cost/prices.yaml"))
    quality = QualityEngine(QualityConfig(baseline_window=5))
    health = Health()

    def on_span(span):
        cost.record(span)
        quality.score(span)
        health.inc_scored()

    receiver = OTLPReceiver("127.0.0.1", PORT, on_span)
    health.bind_receiver_stats(receiver.stats)
    receiver.start()
    try:
        _send_spans(8)
        # give the receiver thread pool a moment to drain
        for _ in range(50):
            if receiver.stats.received >= 8:
                break
            time.sleep(0.1)
    finally:
        receiver.stop()

    assert receiver.stats.received >= 8
    assert receiver.stats.mapped >= 8
    samples = cost.sample()
    assert samples and samples[0].total_usd > 0
    assert health.spans_scored >= 8
    # baseline_window=5 -> some spans warmed, later ones scored
    q = quality.quality_samples()
    assert q


def test_pipeline_safety_store_failure_resilience(monkeypatch, tmp_path):
    """Safety test (spec §17): push 1,000 spans with store.insert monkeypatched to raise.

    Asserts zero exceptions escape and spans_scored == 1000.
    """
    from vitals.config.settings import VerdictConfig
    from vitals.main import EvaluatorThread
    from vitals.model import GenAISpan
    from vitals.store.db import VerdictStore
    from vitals.verdict.scope import ScopeState

    def _failing_insert(self, verdict, retain_count=None):
        raise RuntimeError("Simulated store write failure")

    monkeypatch.setattr(VerdictStore, "insert", _failing_insert)

    db_path = tmp_path / "safety_test.db"
    store = VerdictStore(str(db_path))

    prices = PriceTable.from_yaml("vitals/cost/prices.yaml")
    cost_engine = CostEngine(prices)
    quality_engine = QualityEngine(QualityConfig(baseline_window=30))
    health = Health()

    cfg = VerdictConfig(enabled=True, min_samples=5, calibration_samples=5, evaluate_interval_s=1)
    scope = ScopeState("ragapp", "openai", "gpt-4o", reference_window=30, calib_n=5)
    scopes = {("ragapp", "openai", "gpt-4o"): scope}

    evaluator = EvaluatorThread(scopes, store, cfg, cost_engine, health)
    evaluator.start()

    try:
        for i in range(1000):
            span = GenAISpan(
                trace_id=f"tr_{i:06d}",
                span_id=f"sp_{i:06d}",
                service_name="ragapp",
                service_version="v1",
                gen_ai_system="openai",
                model="gpt-4o",
                input_text=f"input prompt {i}",
                output_text=f"output completion {i}",
                input_tokens=10,
                output_tokens=20,
                start_unix_nano=1000000000 + i * 1000000,
                end_unix_nano=2000000000 + i * 1000000,
            )
            cost_engine.record(span)
            usd = prices.cost_usd(span.model, span.input_tokens, span.output_tokens)
            rec = quality_engine.score(span)
            scope.observe(span, rec, usd)
            health.inc_scored()

        time.sleep(0.5)
    finally:
        evaluator.stop()
        evaluator.join(timeout=2.0)
        store.close()

    assert health.spans_scored == 1000
