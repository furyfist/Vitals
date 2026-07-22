"""Unit tests for JSONL replay fixtures and replay runner (spec §D6, §18)."""

import pytest
from vitals.model import GenAISpan
from vitals.replay import read_fixture, run_replay, write_fixture


def _make_test_span(i: int) -> GenAISpan:
    return GenAISpan(
        trace_id=f"tr_{i:04d}",
        span_id=f"sp_{i:04d}",
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        service_version="v1",
        input_text=f"prompt {i}",
        output_text=f"completion {i}",
        input_tokens=15,
        output_tokens=30,
        start_unix_nano=1000000000,
        end_unix_nano=2000000000,
    )


def test_fixture_jsonl_roundtrip(tmp_path):
    fix_path = tmp_path / "test_fix.jsonl"
    spans_in = [(_make_test_span(i), float(i * 2)) for i in range(5)]

    write_fixture(str(fix_path), spans_in)
    assert fix_path.is_file()

    spans_out = read_fixture(str(fix_path))
    assert len(spans_out) == 5

    for i in range(5):
        s, r_ts = spans_out[i]
        assert s.trace_id == f"tr_{i:04d}"
        assert s.input_text == f"prompt {i}"
        assert r_ts == float(i * 2)


def test_replay_runner_fast_mode(tmp_path):
    fix_path = tmp_path / "fast_replay.jsonl"
    spans_in = [(_make_test_span(i), float(i * 1.5)) for i in range(10)]
    write_fixture(str(fix_path), spans_in)

    replayed_spans = []

    def on_span(span: GenAISpan, virtual_now: float):
        replayed_spans.append(span)

    n = run_replay(str(fix_path), speed=0.0, on_span_cb=on_span)
    assert n == 10
    assert len(replayed_spans) == 10
    assert replayed_spans[0].trace_id == "tr_0000"
    assert replayed_spans[9].trace_id == "tr_0009"
