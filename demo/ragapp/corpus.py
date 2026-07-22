"""Tiny in-memory knowledge base for the demo RAG app. Keyword retrieval, no vector DB."""

from __future__ import annotations

DOCS = [
    "OpenTelemetry is an open source observability framework for traces, metrics, and logs.",
    "SigNoz is an open source APM built on OpenTelemetry and ClickHouse.",
    "The OTLP protocol exports telemetry over gRPC on port 4317 and HTTP on port 4318.",
    "GenAI semantic conventions define span attributes like gen_ai.system and gen_ai.request.model.",
    "Token usage is reported via gen_ai.usage.input_tokens and gen_ai.usage.output_tokens.",
    "A runaway agent loop can burn thousands of dollars while dashboards stay green.",
    "Quality drift is deviation from an established healthy baseline, not absolute correctness.",
    "CUSUM detects the onset of a sustained shift in a monitored metric series.",
]


def retrieve(query: str, k: int = 3) -> list[str]:
    """Return the k docs sharing the most words with the query (deterministic)."""
    q_words = {w.lower().strip("?.,") for w in query.split()}
    scored = sorted(
        DOCS,
        key=lambda d: len(q_words & {w.lower().strip("?.,") for w in d.split()}),
        reverse=True,
    )
    return scored[:k]
