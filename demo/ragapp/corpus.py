"""Tiny in-memory knowledge base for the demo RAG app. Keyword retrieval, no vector DB."""

from __future__ import annotations

DOCS_TOPIC_A = [
    "OpenTelemetry is an open source observability framework for traces, metrics, and logs.",
    "SigNoz is an open source APM built on OpenTelemetry and ClickHouse.",
    "The OTLP protocol exports telemetry over gRPC on port 4317 and HTTP on port 4318.",
    "GenAI semantic conventions define span attributes like gen_ai.system and gen_ai.request.model.",
    "Token usage is reported via gen_ai.usage.input_tokens and gen_ai.usage.output_tokens.",
    "A runaway agent loop can burn thousands of dollars while dashboards stay green.",
    "Quality drift is deviation from an established healthy baseline, not absolute correctness.",
    "CUSUM detects the onset of a sustained shift in a monitored metric series.",
]

DOCS_TOPIC_B = [
    "Write-Ahead Logging (WAL) ensures durability and atomic index updates in relational engines.",
    "B-Tree indices optimize range queries, whereas Hash indices target exact equality lookups.",
    "Multiversion Concurrency Control (MVCC) allows concurrent readers and writers without global locks.",
    "Query planners use cost estimates to choose between nested loop joins and hash joins.",
    "Database checkpoints flush dirty buffer pool pages to disk for recovery speed.",
    "Foreign keys enforce referential integrity across relational schema tables.",
    "Deadlock detection algorithms build wait-for graphs to break cyclic transaction dependencies.",
    "Read committed isolation prevents dirty reads by acquiring short-term shared locks.",
]

DOCS = DOCS_TOPIC_A + DOCS_TOPIC_B


def retrieve(query: str, k: int = 3, topic: str | None = None) -> list[str]:
    """Return the k docs sharing the most words with the query (deterministic)."""
    docs_to_search = DOCS
    if topic == "A":
        docs_to_search = DOCS_TOPIC_A
    elif topic == "B":
        docs_to_search = DOCS_TOPIC_B

    q_words = {w.lower().strip("?.,") for w in query.split()}
    scored = sorted(
        docs_to_search,
        key=lambda d: len(q_words & {w.lower().strip("?.,") for w in d.split()}),
        reverse=True,
    )
    return scored[:k]
