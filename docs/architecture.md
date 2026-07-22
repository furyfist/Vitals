# Vitals architecture

```
 [demo AI app (RAG, Groq)] ──OTLP──▶ [user's OTel Collector]
                                          │ fan-out (2 exporters)
                              ┌───────────┴───────────┐
                              ▼                        ▼
                        [SigNoz ingest]        [vitals service]
                        traces/metrics/logs      │ 1. cost engine  (span attrs → $ velocity)
                              ▲                  │ 2. quality engine (spanIQ scoring + CUSUM)
                              │                  ▼
                              └──OTLP metrics + trace_id-linked eval logs ── (out-of-band)
```

## Pipeline

1. **Ingest** (`vitals/ingest/`) — an OTLP/gRPC receiver is the fan-out target for the
   user's collector (D1). Each span is normalized by the gen_ai semconv mapper
   (`mapper.py`) into a `GenAISpan`; non-gen_ai or malformed spans are counted and
   skipped, never crashing the scorer.
2. **Cost** (`vitals/cost/`) — span-attribute arithmetic (D7): tokens × a bundled,
   user-overridable price table → `vitals.cost.velocity` (USD/min over a sliding window)
   and `vitals.cost.total`.
3. **Quality** (`vitals/quality/`) — deterministic, reference-free scoring (D2, D6):
   ResponseDrift (PSI vs a frozen healthy baseline) + calibrated CUSUM onset. The
   baseline key excludes `service.version`, so a new release is scored against the
   established-good reference — that's what makes a poisoned deploy detectable.
   Consistency/stability (embedding-based) are optional.
4. **Emit** (`vitals/emit/`) — out-of-band OTLP (D3, D4): metrics via observable gauges +
   trace_id-linked eval log records, sent **directly to SigNoz ingest**, not through the
   monitored collector. If the user's pipeline misbehaves, Vitals survives.

## Key decisions (see PROJECT_PLAN §3 and DECISIONS.md)

- **Observe, don't proxy.** Vitals is never in the request path. Scores lag traces by
  seconds; nothing user-facing waits on Vitals.
- **Determinism = 100% coverage.** $0/trace and ~ms latency is the structural moat over
  judge-based tools that can only sample.
- **No span re-emission.** Metrics carry dashboards/alerts; eval logs give per-trace
  drill-down via SigNoz's native logs↔traces correlation. Re-emitting enriched spans
  would duplicate the user's traces.
- **Python.** spanIQ is Python; Vitals wraps it in-process.

## Failure handling

| Failure | Behavior |
|---|---|
| vitals down | User's pipeline unaffected (fan-out exporter drops; SigNoz path untouched). |
| SigNoz ingest unreachable | Metrics buffer in the SDK's bounded queue; errors logged honestly. |
| Malformed / non-gen_ai span | Counted (`vitals.health.spans_skipped`), skipped, never crashes. |
| Baseline cold-start | Signal reports `warming` (no score) until the window fills. |

## State

In-memory rolling baselines and cost windows for V1. Persistent baselines across
restarts (spanIQ SQLite, D8) are a V2 item — see [STATUS.md](../STATUS.md).
