"""Unit tests: gen_ai semconv mapper — semconv + Traceloop shapes, skip discipline."""

from __future__ import annotations

from vitals.ingest.mapper import MapStats, map_span

RESOURCE = {"service.name": "ragapp", "service.version": "v1"}


def test_maps_semconv_shape():
    attrs = {
        "gen_ai.system": "groq",
        "gen_ai.request.model": "llama-3.3-70b-versatile",
        "gen_ai.usage.input_tokens": 120,
        "gen_ai.usage.output_tokens": 45,
        "gen_ai.content.prompt": "what is otel?",
        "gen_ai.content.completion": "OpenTelemetry is an observability framework.",
    }
    s = map_span(attrs, RESOURCE, "trace1", "span1")
    assert s is not None
    assert s.gen_ai_system == "groq"
    assert s.model == "llama-3.3-70b-versatile"
    assert s.input_tokens == 120 and s.output_tokens == 45
    assert s.service_version == "v1"
    assert "OpenTelemetry" in s.output_text


def test_maps_traceloop_indexed_shape():
    attrs = {
        "gen_ai.system": "openai",
        "gen_ai.response.model": "gpt-4o-mini",
        "gen_ai.usage.prompt_tokens": 10,
        "gen_ai.usage.completion_tokens": 20,
        "gen_ai.prompt.0.content": "hello",
        "gen_ai.completion.0.content": "hi there",
    }
    s = map_span(attrs, RESOURCE, "t", "s")
    assert s is not None
    assert s.model == "gpt-4o-mini"
    assert s.input_text == "hello"
    assert s.output_text == "hi there"
    assert s.input_tokens == 10 and s.output_tokens == 20


def test_non_genai_span_skipped():
    stats = MapStats()
    s = map_span({"http.method": "GET"}, RESOURCE, "t", "s", stats=stats)
    assert s is None
    assert stats.received == 1 and stats.skipped == 1 and stats.mapped == 0


def test_genai_without_output_skipped():
    stats = MapStats()
    attrs = {"gen_ai.system": "groq", "gen_ai.request.model": "x"}
    s = map_span(attrs, RESOURCE, "t", "s", stats=stats)
    assert s is None
    assert stats.skipped == 1


def test_missing_tokens_default_zero():
    attrs = {
        "gen_ai.system": "groq",
        "gen_ai.request.model": "x",
        "gen_ai.content.completion": "answer",
    }
    s = map_span(attrs, RESOURCE, "t", "s")
    assert s is not None
    assert s.input_tokens == 0 and s.output_tokens == 0


def test_stats_count_mapped():
    stats = MapStats()
    attrs = {
        "gen_ai.system": "groq",
        "gen_ai.request.model": "x",
        "gen_ai.content.completion": "answer",
    }
    map_span(attrs, RESOURCE, "t", "s", stats=stats)
    assert stats.received == 1 and stats.mapped == 1 and stats.skipped == 0
