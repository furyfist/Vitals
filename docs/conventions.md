# `gen_ai.evaluation.*` — Semantic Conventions for LLM Evaluation Results (proposal)

> **Status:** Draft proposal, written as if for the OpenTelemetry GenAI SIG. The OTel
> GenAI semantic conventions today cover requests, responses, and token usage — but
> **not evaluation results**; embedding eval results into telemetry is still in early
> discussion. This document is Vitals' working reference implementation and the standard
> slot it fills.

## Motivation

AI systems need two signals no OTel-native platform emits today: **what a response cost**
and **whether its quality changed**. Cost is derivable from existing `gen_ai.usage.*`
attributes plus a price table. Quality has no convention at all. This proposal defines a
minimal, backend-agnostic set of metric and log attributes for **online, deterministic
evaluation results** so any tool can emit them and any backend can alert on them.

## Design principles

1. **Deviation, not truth.** Online scores measure change from an established healthy
   baseline, not absolute correctness. Names and units reflect this (see
   [honesty.md](honesty.md)).
2. **Dimensioned by release.** Every signal carries `service.name` and `service.version`
   so quality/cost can be compared per deploy.
3. **Correlatable.** Per-response results are emitted as log records carrying `trace_id`
   and `span_id`, so a backend can join an eval result to the trace that produced it.
4. **Cheap enough for 100% coverage.** Deterministic scoring ($0/trace, ~ms) is what
   makes emitting on every response viable; the convention assumes inline, not sampled.

## Metrics

| Metric | Instrument | Unit | Meaning |
|---|---|---|---|
| `gen_ai.evaluation.drift` | Gauge | `1` (PSI) | Distributional drift of the response vs the healthy baseline. Lower is better. |
| `gen_ai.evaluation.consistency` | Gauge | `1` | Self-consistency across sampled responses (optional, embedding-based). |
| `gen_ai.evaluation.stability` | Gauge | `1` | Output stability (optional, embedding-based). |
| `gen_ai.evaluation.score` | Gauge | `1` | Composite quality in `[0,1]`; higher is better. |
| `gen_ai.evaluation.drift_onset` | Gauge | `1` | `1` at/after the detected onset of sustained drift, else `0`. |
| `vitals.cost.velocity` | Gauge | `usd/min` | Token spend-rate over a sliding window. |
| `vitals.cost.total` | Counter | `usd` | Cumulative token spend. |
| `vitals.tokens.input` / `vitals.tokens.output` | Counter | `{token}` | Token counters. |

### Recommended dimensions (attributes) on every metric point

- `service.name`, `service.version`
- `gen_ai.system` (e.g. `openai`, `anthropic`, `groq`)
- `gen_ai.request.model`

## Log records (per evaluated response)

One log record per scored response, so results correlate to the originating trace.

| Attribute | Type | Meaning |
|---|---|---|
| `trace_id`, `span_id` | string | Link to the scored LLM span. |
| `gen_ai.evaluation.state` | string | `warming` (baseline not yet established, no score) or `scored`. |
| `gen_ai.evaluation.drift` | double | PSI drift (present when `scored`). |
| `gen_ai.evaluation.consistency` | double | Optional. |
| `gen_ai.evaluation.stability` | double | Optional. |
| `gen_ai.evaluation.score` | double | Composite `[0,1]`. |
| `gen_ai.evaluation.drift_onset` | int | `0` or `1`. |
| `gen_ai.evaluation.reason` | string | Human-readable, e.g. `PSI 0.03 < 0.10`. |

### The `warming` state (required for honesty)

Before a baseline is established, evaluators MUST emit `state=warming` and MUST NOT emit
a score. A backend must never render or alert on a score during warming — a false
quality page destroys trust permanently.

## Reference implementation

Vitals (`vitals/contract.py`, `vitals/emit/`) emits exactly these names. See
[architecture.md](architecture.md) for the pipeline and [honesty.md](honesty.md) for the
semantics contract.
