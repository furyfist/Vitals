"""Generate deterministic golden JSONL replay fixtures (spec §10, §18)."""

from __future__ import annotations

import os
from pathlib import Path
from vitals.model import GenAISpan
from vitals.replay.fixtures import write_fixture


def make_span(
    i: int,
    version: str = "v1",
    input_text: str = "what is opentelemetry?",
    output_text: str = "OpenTelemetry is an open source observability framework.",
    input_tokens: int = 15,
    output_tokens: int = 30,
    rel_ts: float = 0.0,
) -> tuple[GenAISpan, float]:
    span = GenAISpan(
        trace_id=f"tr_{i:06d}000000000000000000000",
        span_id=f"sp_{i:06d}0000000",
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        service_version=version,
        input_text=input_text,
        output_text=output_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        start_unix_nano=1000000000 + int(rel_ts * 1e9),
        end_unix_nano=2000000000 + int(rel_ts * 1e9),
    )
    return span, rel_ts


def generate_all_fixtures(out_dir: str = "demo/fixtures") -> None:
    path_dir = Path(out_dir)
    path_dir.mkdir(parents=True, exist_ok=True)

    # 1. Steady Baseline (01_steady_baseline.jsonl)
    spans_01 = []
    ts = 0.0
    for i in range(45):
        spans_01.append(
            make_span(
                i,
                version="v1",
                input_text=f"what is opentelemetry topic query {i % 5}?",
                output_text=f"OpenTelemetry is an open source observability framework variant {i % 5}.",
                rel_ts=ts,
            )
        )
        ts += 2.0
    write_fixture(path_dir / "01_steady_baseline.jsonl", spans_01)

    # 2. Release Regression (02_release_regression.jsonl)
    spans_02 = []
    ts = 0.0
    # 30 reference v1 spans
    for i in range(30):
        spans_02.append(
            make_span(
                i,
                version="v1",
                input_text=f"what is opentelemetry topic query {i % 5}?",
                output_text=f"OpenTelemetry is an open source observability framework variant {i % 5}.",
                rel_ts=ts,
            )
        )
        ts += 2.0
    # 15 degraded v2 spans (poisoned prompt / hallucinated output)
    for i in range(30, 45):
        spans_02.append(
            make_span(
                i,
                version="v2",
                input_text=f"what is opentelemetry topic query {i % 5}?",
                output_text=f"Garbage hallucinated text response with zero semantic similarity {i}.",
                rel_ts=ts,
            )
        )
        ts += 2.0
    write_fixture(path_dir / "02_release_regression.jsonl", spans_02)

    # 3. Runaway Loop (03_runaway_loop.jsonl)
    spans_03 = []
    ts = 0.0
    # 30 reference v1 spans
    for i in range(30):
        spans_03.append(
            make_span(
                i,
                version="v1",
                input_text=f"query {i % 5}",
                output_text=f"standard response {i % 5}",
                input_tokens=20,
                output_tokens=30,
                rel_ts=ts,
            )
        )
        ts += 2.0
    # 15 runaway loop spans (high token burn & high rate)
    for i in range(30, 45):
        spans_03.append(
            make_span(
                i,
                version="v1",
                input_text=f"runaway agent loop iteration {i}",
                output_text="A" * 5000,
                input_tokens=15000,
                output_tokens=25000,
                rel_ts=ts,
            )
        )
        ts += 0.2
    write_fixture(path_dir / "03_runaway_loop.jsonl", spans_03)

    # 4. Input Shift (04_input_shift.jsonl)
    spans_04 = []
    ts = 0.0
    # 30 reference spans on Topic A
    for i in range(30):
        spans_04.append(
            make_span(
                i,
                version="v1",
                input_text=f"what is opentelemetry topic query {i % 5}?",
                output_text=f"OpenTelemetry is an open source observability framework variant {i % 5}.",
                rel_ts=ts,
            )
        )
        ts += 2.0
    # 15 shifted Topic B database queries + modified outputs (causes input drift + behavior drift)
    for i in range(30, 45):
        spans_04.append(
            make_span(
                i,
                version="v1",
                input_text=f"explain write ahead logging index locking deadlock {i}",
                output_text=f"Write ahead logging and relational database B-Trees MVCC isolation {i}.",
                rel_ts=ts,
            )
        )
        ts += 2.0
    write_fixture(path_dir / "04_input_shift.jsonl", spans_04)

    print(f"Successfully generated 4 golden replay fixtures in {out_dir}")


if __name__ == "__main__":
    generate_all_fixtures()
