"""Shared domain model: the normalized gen_ai span that flows through the pipeline.

ingest/ produces GenAISpan from raw OTLP; cost/ and quality/ consume it. Keeping
this in one place is the contract between the modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GenAISpan:
    """A single LLM call, normalized from OTel GenAI semantic-convention attributes."""

    trace_id: str
    span_id: str
    service_name: str
    service_version: str
    gen_ai_system: str  # "openai", "anthropic", "groq", ...
    model: str  # gen_ai.request.model
    input_text: str  # prompt / user content
    output_text: str  # completion
    input_tokens: int
    output_tokens: int
    start_unix_nano: int
    end_unix_nano: int
    attributes: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def dims(self) -> dict[str, str]:
        """Standard dimension set stamped on every emitted signal for this span."""
        return {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "gen_ai.system": self.gen_ai_system,
            "gen_ai.request.model": self.model,
        }
