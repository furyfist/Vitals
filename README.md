# Vitals

**The missing vital signs for AI systems: cost and quality, as first-class, alertable SigNoz signals.**

Observability has three signals for machines: traces, metrics, logs. AI systems
need two more that no OTel-native platform provides today: **what it costs right
now** and **whether the answers are any good**. Vitals adds both.

Vitals is an OTel-native sidecar. Your existing OTel Collector fans out a copy of
its `gen_ai` spans to Vitals; Vitals scores them — deterministically, out of the
request path, on 100% of traffic — and emits two new signal families back into
SigNoz:

- **Cost vitals** — per-service/model/version token spend-rate (`vitals.cost.velocity`,
  USD/min) and cumulative burn (`vitals.cost.total`), so a runaway agent loop pages
  you in minutes, not on the invoice.
- **Quality vitals** — reference-free deterministic scores on every response
  (`gen_ai.evaluation.*`): drift from a healthy baseline, self-consistency, output
  stability, plus CUSUM drift-onset detection dimensioned by `service.version` for
  per-release quality comparison.

> **Honesty framing:** online quality scores measure *deviation from an established
> good baseline*, not absolute correctness. Vitals answers "did quality change, when,
> and with which release" — the question behind every silent-regression incident — not
> "is this answer true." See [docs/honesty.md](docs/honesty.md).

## Architecture

```
 [demo AI app (RAG, Groq)] ──OTLP──▶ [OTel Collector]
                                        │ fan-out (2 exporters)
                            ┌───────────┴───────────┐
                            ▼                        ▼
                      [SigNoz ingest]          [vitals service]
                                                 cost engine + quality engine
                                                     │
                      [SigNoz ingest] ◀── OTLP metrics + eval logs (out-of-band)
```

Built on **spanIQ** (vendored, unmodified) — a deterministic LLM evaluation engine
that scores at $0/trace and ~ms latency, the only approach that can run inline on
100% of traffic.

## Quick start

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows
pip install -e .
cp .env.example .env                                # add GROQ_API_KEY later
vitals run                                           # starts the sidecar
```

See [demo/README.md](demo/README.md) for the full stack (app + collector + SigNoz +
vitals) and the demo run-of-show.

## Status

See [STATUS.md](STATUS.md) for what's done and what's planned for V2.

Apache 2.0.
