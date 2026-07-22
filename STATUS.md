# Vitals — Build Status (V1)

Snapshot of what the pipeline does today and what's deferred to V2. Source of truth for
scope is [PROJECT_PLAN.md](PROJECT_PLAN.md); deviations are in [DECISIONS.md](DECISIONS.md).

**Bottom line:** the whole pipeline is wired end-to-end and green (19 tests, ruff clean).
Cost and quality signals flow from a real OTLP receiver through scoring to out-of-band
OTLP emission. API keys are **not required to build or run** — the Groq key goes in
`.env` when ready; without it the demo app serves deterministic canned answers so the
pipeline still flows.

---

## Done

### Pipeline (the Vitals layer — all new, in-event work)
- **Ingest** (`vitals/ingest/`) — OTLP/gRPC receiver as the collector fan-out target
  (D1); gen_ai semconv mapper handling both OTel semconv and Traceloop/OpenLLMetry
  attribute shapes (spike S3 covered); malformed/non-gen_ai spans counted and skipped,
  never crash the scorer.
- **Cost** (`vitals/cost/`) — bundled, user-overridable YAML price table; USD/min sliding
  velocity + cumulative burn + token counters (D7). Exhaustive unit tests.
- **Quality** (`vitals/quality/`) — reference-free ResponseDrift (PSI vs a frozen healthy
  baseline) + calibrated CUSUM onset (D6). Baseline key excludes `service.version` so a
  poisoned v2 is scored against v1's healthy reference. `warming` state emits no score
  (never-over-report). Zero-false-positive test on clean traffic (spike S4 discipline).
- **Emit** (`vitals/emit/`) — out-of-band OTLP metrics (observable gauges) + trace_id
  linked eval logs, straight to SigNoz ingest, not through the monitored collector (D3/D4).
- **Health** (`vitals/health.py`) — vitals self-health metrics from day one (§9).
- **Entrypoint** (`vitals/main.py`) — `vitals run` wires the full pipeline with graceful
  shutdown; cost-only mode when quality is disabled.
- **Config** (`vitals/config/`) — `vitals.yaml` load/validate with env-override precedence.
- **Contract** (`vitals/contract.py`) — frozen metric names + eval-log schema (D3).

### Signals, dashboards, alerts
- Three SigNoz dashboards: Overview, Release Compare, Drift (`assets/dashboards/`).
- Three alert rules: cost-velocity breach, quality-drift onset, per-version regression
  (`assets/alerts/`).

### Demo
- `demo/compose.yaml`: ragapp + collector (fan-out) + vitals, alongside existing SigNoz.
- Groq RAG app with versioned prompts (v1 good / v2 poisoned), gen_ai-instrumented.
- Scenarios: `runaway_loop.py` (cost hook), `deploy_v2.sh` (quality payoff), `reset.sh`.
- `demo/README.md` run-of-show (two beats, one pipeline).

### Docs & CI
- `docs/conventions.md` — the `gen_ai.evaluation.*` proposal (first-class deliverable).
- `docs/honesty.md` — drift-not-truth framing. `docs/architecture.md` — pipeline + failure handling.
- CI: ruff + pytest + vendored spanIQ import check.

### Tests (19 passing)
- Cost math (7), semconv mapper (6), quality warming/drift/onset/no-false-positive (5),
  end-to-end OTLP receiver → cost + quality integration (1).

---

## Left for V2 (and why)

### Wiring stubs to finish once keys/live SigNoz are in the loop
- **Groq API key** — drop into `demo/.env`; `llm.py` already calls Groq and falls back to
  canned answers. No code change needed.
- **Live dashboard/alert round-trip** — the JSON is authored to SigNoz's schema but has
  not been import-verified against a running SigNoz UI; validate and adjust field shapes
  on first import.
- **`traceloop-sdk` auto-instrumentation** — the app currently emits gen_ai spans via
  manual instrumentation (S3 fallback, deterministic). Swap to Traceloop auto-instr for
  the primary path when running against real Groq.

### Depth (from PROJECT_PLAN §2 V2)
- **Persistent baselines across restarts** — currently in-memory; wire spanIQ's SQLite
  BaselineStore (D8) so baselines survive a vitals restart.
- **Embedding metrics online** — consistency/stability are imported but return `None` in
  the single-shot online path (`_measure_optional`); they need a per-prompt sample buffer
  to be meaningful. Descope-ladder item #3.
- **Embedding-distribution drift (PSI/KS)** — spanIQ's `statistical/` has the primitives;
  not yet wired into the online scorer. Descope-ladder item #4.
- **Per-chunk RAG grounding** (query↔chunks, answer↔chunks).
- **Per-tenant/user impact dimensions** — "which customers are affected".
- **PELT changepoint attribution** — which pipeline component drifted (V1 gives onset only).

### Reach (V3)
- Upstream the `gen_ai.evaluation.*` convention to the OTel GenAI SIG.
- Enforcement webhooks (budget circuit-breakers via a gateway) — Vitals stays observe-only.
- Behavioral-security signals (anomalous tool-call velocity); multi-backend support.
- PyPI publish of vitals (+ spanIQ).

### Known limits (documented honestly)
- spanIQ write ceiling ~500 spans/s (far above demo load).
- Quality scoring runs synchronously in the receiver thread pool; fine at demo rates, but
  a dedicated async scoring queue is the scale path.
- CUSUM params (`cusum_k`, `cusum_h`, `baseline_window`) ship with S4 defaults; re-calibrate
  against real traffic before trusting onset latency claims.

---

## How to run

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows
pip install -e . && pip install rich sentence-transformers   # full quality path
pytest -q                                            # 19 tests
vitals run                                           # start the sidecar
```

Demo stack: see [demo/README.md](demo/README.md).
