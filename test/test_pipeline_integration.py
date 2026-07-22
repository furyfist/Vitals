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
