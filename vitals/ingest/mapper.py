"""GenAI semantic-convention mapper: raw span attributes -> GenAISpan.

Tolerates both the OTel GenAI semconv shape and the Traceloop/OpenLLMetry shape
(spike S3). Non-gen_ai or malformed spans are counted and skipped — never crash the
scorer (failure-handling law, §3).
"""

from __future__ import annotations

from dataclasses import dataclass

from vitals.model import GenAISpan

# --- attribute keys, in priority order per field ---
_SYSTEM_KEYS = ("gen_ai.system", "llm.system")
_MODEL_KEYS = ("gen_ai.request.model", "gen_ai.response.model", "llm.request.model")
_INPUT_TOKEN_KEYS = (
    "gen_ai.usage.input_tokens",
    "gen_ai.usage.prompt_tokens",
    "llm.usage.prompt_tokens",
)
_OUTPUT_TOKEN_KEYS = (
    "gen_ai.usage.output_tokens",
    "gen_ai.usage.completion_tokens",
    "llm.usage.completion_tokens",
)
# Direct content keys (semconv). Traceloop indexes: gen_ai.prompt.N.content etc.
_PROMPT_KEYS = ("gen_ai.content.prompt", "gen_ai.prompt")
_COMPLETION_KEYS = ("gen_ai.content.completion", "gen_ai.completion")


@dataclass
class MapStats:
    received: int = 0
    mapped: int = 0
    skipped: int = 0


def _first(attrs: dict, keys) -> object | None:
    for k in keys:
        if k in attrs and attrs[k] not in (None, ""):
            return attrs[k]
    return None


def _int(value: object | None) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _indexed_content(attrs: dict, prefix: str) -> str:
    """Traceloop packs messages as gen_ai.<prefix>.<i>.content — join them in order."""
    parts: list[tuple[int, str]] = []
    needle = f"gen_ai.{prefix}."
    for k, v in attrs.items():
        if k.startswith(needle) and k.endswith(".content") and v:
            try:
                idx = int(k[len(needle):].split(".", 1)[0])
            except ValueError:
                idx = 0
            parts.append((idx, str(v)))
    return "\n".join(text for _, text in sorted(parts))


def _content(attrs: dict, direct_keys, indexed_prefix: str) -> str:
    direct = _first(attrs, direct_keys)
    if direct:
        return str(direct)
    return _indexed_content(attrs, indexed_prefix)


def is_gen_ai(attrs: dict) -> bool:
    return _first(attrs, _SYSTEM_KEYS) is not None or _first(attrs, _MODEL_KEYS) is not None


def map_span(
    span_attrs: dict,
    resource_attrs: dict,
    trace_id: str,
    span_id: str,
    start_unix_nano: int = 0,
    end_unix_nano: int = 0,
    stats: MapStats | None = None,
) -> GenAISpan | None:
    """Map one span. Returns None (and bumps stats.skipped) if not a usable gen_ai span."""
    if stats is not None:
        stats.received += 1

    if not is_gen_ai(span_attrs):
        if stats is not None:
            stats.skipped += 1
        return None

    output_text = _content(span_attrs, _COMPLETION_KEYS, "completion")
    # A response with no output text cannot be quality-scored; skip cleanly.
    if not output_text:
        if stats is not None:
            stats.skipped += 1
        return None

    span = GenAISpan(
        trace_id=trace_id,
        span_id=span_id,
        service_name=str(resource_attrs.get("service.name", "unknown")),
        service_version=str(resource_attrs.get("service.version", "unknown")),
        gen_ai_system=str(_first(span_attrs, _SYSTEM_KEYS) or "unknown"),
        model=str(_first(span_attrs, _MODEL_KEYS) or "unknown"),
        input_text=_content(span_attrs, _PROMPT_KEYS, "prompt"),
        output_text=output_text,
        input_tokens=_int(_first(span_attrs, _INPUT_TOKEN_KEYS)),
        output_tokens=_int(_first(span_attrs, _OUTPUT_TOKEN_KEYS)),
        start_unix_nano=start_unix_nano,
        end_unix_nano=end_unix_nano,
        attributes=dict(span_attrs),
    )
    if stats is not None:
        stats.mapped += 1
    return span
