# Vitals demo — run-of-show

Two beats, one pipeline. Every number is reproducible: run the scenarios yourself and
watch the Vitals dashboards in SigNoz.

## Prerequisites

- Docker Desktop running.
- **SigNoz already up** on the host (self-hosted compose or Cloud trial), OTLP ingest on
  `localhost:4317`, UI on `localhost:8080`.
- A Groq API key (free at https://console.groq.com). Optional — without it the app serves
  deterministic canned answers so the pipeline still flows.

## Setup

```bash
cp demo/.env.example demo/.env        # add GROQ_API_KEY (optional)
docker compose -f demo/compose.yaml up --build -d
```

This starts three services alongside your existing SigNoz:

| service | role |
|---|---|
| `ragapp` | Groq RAG app on :8000, emits gen_ai spans to the collector |
| `collector` | OTel Collector — **fans out** spans to SigNoz **and** vitals |
| `vitals` | the sidecar: scores spans, emits cost + quality signals out-of-band to SigNoz |

Import the dashboards and alerts (SigNoz UI → Dashboards → Import JSON):
`assets/dashboards/*.json`, `assets/alerts/*.json`.

Warm the quality baseline once (healthy v1 traffic):

```bash
python demo/scenarios/runaway_loop.py --rate 3 --duration 60
```

---

## Beat 1 — the hook: cost

```bash
python demo/scenarios/runaway_loop.py --rate 20 --duration 120
```

On **Vitals — Overview**, `vitals.cost.velocity` (USD/min) spirals upward. The
**cost velocity** alert fires at the threshold — in minutes, not on the invoice.

> *"A 4-agent loop burned \$47,000 over 11 days with dashboards green. \$47K incidents end here."*

## Beat 2 — the payoff: quality

Deploy the poisoned prompt (v2). **No model change. Tokens stay normal. Infra stays green.**

```bash
bash demo/scenarios/deploy_v2.sh
python demo/scenarios/runaway_loop.py --rate 5 --duration 180
```

On **Vitals — Drift**, the drift line bends and a **CUSUM onset marker** appears. On
**Vitals — Release Compare**, v1 and v2 split — v2's quality score drops while v1 holds.
The **quality drift onset** alert pages.

> *"Anthropic shipped this exact failure in April and found out from user complaints.*
> *Cost to detect: \$0.00."*

Close on the convention: *"and we wrote down the standard so everyone can emit this"* —
[docs/conventions.md](../docs/conventions.md).

## Reset

```bash
bash demo/scenarios/reset.sh
```

Redeploys v1 and restarts vitals so baselines re-warm. SigNoz data is left intact.

## Honesty note (say it first)

Vitals measures **deviation from a healthy baseline**, not absolute correctness — the
exact signal behind every silent-regression incident. See [docs/honesty.md](../docs/honesty.md).
