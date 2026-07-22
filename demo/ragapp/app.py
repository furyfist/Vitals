"""Demo RAG app: retrieve -> generate -> emit a gen_ai span. FastAPI on :8000.

    GET  /health           liveness
    POST /ask  {"query"}   answer a question, emit one gen_ai chat span
    GET  /ask?query=...    convenience for scenario scripts / curl
"""

from __future__ import annotations

import os

from corpus import retrieve
from fastapi import FastAPI
from llm import generate
from pydantic import BaseModel
from telemetry import init_tracer, record_gen_ai_span

app = FastAPI(title="vitals demo ragapp")
_tracer = init_tracer()
_version = os.getenv("PROMPT_VERSION", os.getenv("SERVICE_VERSION", "v1"))


class AskRequest(BaseModel):
    query: str


def _answer(query: str) -> dict:
    context = retrieve(query)
    result = generate(query, context, _version)
    record_gen_ai_span(
        _tracer,
        model=result["model"],
        system=result["system"],
        prompt=query,
        completion=result["answer"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
    )
    return {
        "query": query,
        "version": _version,
        "answer": result["answer"],
        "context": context,
        "tokens": {
            "input": result["input_tokens"],
            "output": result["output_tokens"],
        },
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": _version}


@app.post("/ask")
def ask_post(req: AskRequest) -> dict:
    return _answer(req.query)


@app.get("/ask")
def ask_get(query: str = "what is opentelemetry?") -> dict:
    return _answer(query)
