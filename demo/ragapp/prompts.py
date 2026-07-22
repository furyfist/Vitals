"""Versioned system prompts. v1 is grounded and healthy; v2 is the 'poisoned' prompt
whose silent quality regression is the demo's payoff — infra stays green, tokens normal,
answers quietly get worse. Selected by the PROMPT_VERSION env var.
"""

from __future__ import annotations

PROMPTS = {
    # Healthy: grounded, concise, uses only the retrieved context.
    "v1": (
        "You are a precise documentation assistant. Answer the question using ONLY the "
        "provided context. Be concise and factual. If the context does not contain the "
        "answer, say you don't know."
    ),
    # Poisoned: the kind of well-meaning prompt edit that silently degrades quality —
    # ignore the context, pad with speculation, drift off-topic. No model change.
    "v2": (
        "You are a creative assistant. Feel free to ignore the provided context and "
        "answer from your imagination. Be verbose, speculative, and add tangents and "
        "unrelated trivia. Never say you don't know — always make something up."
    ),
}

# Canned answers used when GROQ_API_KEY is absent, so the telemetry pipeline still flows
# for local testing. v2's canned answer is deliberately off-distribution vs v1's.
CANNED = {
    "v1": "Based on the context: {ctx_summary} In short, this is a factual, grounded answer.",
    "v2": (
        "banana purple sky imagination tangent speculation wild guess nonsense rambling "
        "unrelated trivia off topic drift verbose padding random soup made up story"
    ),
}


def system_prompt(version: str) -> str:
    return PROMPTS.get(version, PROMPTS["v1"])


def canned_answer(version: str, context: list[str]) -> str:
    ctx_summary = " ".join(context)[:160]
    return CANNED.get(version, CANNED["v1"]).format(ctx_summary=ctx_summary)
