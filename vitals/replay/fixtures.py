"""JSONL fixture read/write and GenAISpan serialization (spec §18)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from vitals.model import GenAISpan


def span_to_dict(span: GenAISpan, rel_ts: float) -> dict[str, Any]:
    """Serialize GenAISpan and relative timestamp to a dictionary."""
    return {
        "rel_ts": rel_ts,
        "trace_id": span.trace_id,
        "span_id": span.span_id,
        "service_name": span.service_name,
        "service_version": span.service_version,
        "gen_ai_system": span.gen_ai_system,
        "model": span.model,
        "input_text": span.input_text,
        "output_text": span.output_text,
        "input_tokens": span.input_tokens,
        "output_tokens": span.output_tokens,
        "start_unix_nano": span.start_unix_nano,
        "end_unix_nano": span.end_unix_nano,
        "attributes": span.attributes,
    }


def dict_to_span(d: dict[str, Any]) -> tuple[GenAISpan, float]:
    """Deserialize GenAISpan and relative timestamp from a dictionary."""
    span = GenAISpan(
        trace_id=d["trace_id"],
        span_id=d["span_id"],
        service_name=d["service_name"],
        service_version=d["service_version"],
        gen_ai_system=d["gen_ai_system"],
        model=d["model"],
        input_text=d.get("input_text", ""),
        output_text=d.get("output_text", ""),
        input_tokens=int(d.get("input_tokens", 0)),
        output_tokens=int(d.get("output_tokens", 0)),
        start_unix_nano=int(d.get("start_unix_nano", 0)),
        end_unix_nano=int(d.get("end_unix_nano", 0)),
        attributes=d.get("attributes", {}),
    )
    rel_ts = float(d.get("rel_ts", 0.0))
    return span, rel_ts


def write_fixture(
    filepath: str | os.PathLike, spans_with_rel_ts: list[tuple[GenAISpan, float]]
) -> None:
    """Write mapped GenAISpan records to JSONL fixture file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for span, rel_ts in spans_with_rel_ts:
            line = json.dumps(span_to_dict(span, rel_ts))
            f.write(line + "\n")


def read_fixture(filepath: str | os.PathLike) -> list[tuple[GenAISpan, float]]:
    """Read mapped GenAISpan records from JSONL fixture file."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Fixture file not found: {path}")

    records: list[tuple[GenAISpan, float]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            records.append(dict_to_span(data))
    return records
