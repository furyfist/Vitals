"""Groq generation with a canned fallback. Keys go in the env; logic is wired now."""

from __future__ import annotations

import os

from prompts import canned_answer, system_prompt

MODEL = os.getenv("RAG_MODEL", "llama-3.3-70b-versatile")


def _estimate_tokens(text: str) -> int:
    # ~1.3 tokens/word, good enough for the demo cost math.
    return max(1, int(len(text.split()) * 1.3))


def generate(query: str, context: list[str], version: str) -> dict:
    """Return {answer, model, system, input_tokens, output_tokens}.

    Calls Groq when GROQ_API_KEY is present; otherwise returns a deterministic canned
    answer so the pipeline flows without a key."""
    sys_prompt = system_prompt(version)
    ctx = "\n".join(context)
    user_msg = f"Context:\n{ctx}\n\nQuestion: {query}"

    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq

            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2 if version == "v1" else 0.9,
            )
            answer = resp.choices[0].message.content
            usage = resp.usage
            return {
                "answer": answer,
                "model": MODEL,
                "system": "groq",
                "input_tokens": getattr(usage, "prompt_tokens", _estimate_tokens(user_msg)),
                "output_tokens": getattr(usage, "completion_tokens", _estimate_tokens(answer)),
            }
        except Exception as e:  # noqa: BLE001 — fall back to canned on any API error
            answer = f"[groq error, canned fallback] {canned_answer(version, context)}"
            return {
                "answer": answer, "model": MODEL, "system": "groq",
                "input_tokens": _estimate_tokens(user_msg),
                "output_tokens": _estimate_tokens(answer),
            }

    answer = canned_answer(version, context)
    return {
        "answer": answer,
        "model": MODEL,
        "system": "groq",
        "input_tokens": _estimate_tokens(user_msg),
        "output_tokens": _estimate_tokens(answer),
    }
