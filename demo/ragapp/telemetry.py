"""OTel setup for the demo app. Emits gen_ai semconv spans to the collector.

Uses manual instrumentation (spike S3 fallback) so the demo is deterministic and works
with or without a Groq key. Traceloop/OpenLLMetry auto-instrumentation can be layered on
top when a real Groq client is used; the attribute shapes match either way.
"""

from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_SERVICE = os.getenv("OTEL_SERVICE_NAME", "ragapp")
_VERSION = os.getenv("SERVICE_VERSION", "v1")
_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")


def init_tracer() -> trace.Tracer:
    resource = Resource.create(
        {"service.name": _SERVICE, "service.version": _VERSION}
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=_ENDPOINT, insecure=True))
    )
    trace.set_tracer_provider(provider)
    return trace.get_tracer("ragapp")


def record_gen_ai_span(
    tracer: trace.Tracer,
    *,
    model: str,
    system: str,
    prompt: str,
    completion: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Emit one gen_ai chat span with semconv attributes the vitals mapper reads."""
    with tracer.start_as_current_span("chat") as span:
        span.set_attribute("gen_ai.system", system)
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
        span.set_attribute("gen_ai.content.prompt", prompt)
        span.set_attribute("gen_ai.content.completion", completion)
