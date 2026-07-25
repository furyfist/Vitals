# Vitals Demo & Replay Guide

Every scenario in Vitals is 100% reproducible — either live through Docker Compose or instantly via deterministic `vitals replay` fixtures without external network calls or Groq API keys.

---

## Quickstart A — Instant Replay Scenarios (No Docker needed)

Vitals includes a deterministic replay engine (`vitals replay <fixture>`) that replays pre-recorded OTLP spans through the full scoring and verdict engine. `replay` stands up its own receiver, evaluator, and console in one process — **do not** run `vitals run` first; a second process binding the same ports (4327, 8787) will fail to start.

Run each scenario with `--config vitals.demo.yaml`, a lower-threshold config sized for these 45-55 span fixtures (`vitals.yaml`'s production thresholds need ~90 spans/version to ever clear warming — see the comment at the top of `vitals.demo.yaml`).

```bash
# Scenario 1: Steady Baseline (Verdict: STEADY)
python -m vitals.main replay demo/fixtures/01_steady_baseline.jsonl --speed 10.0 --config vitals.demo.yaml

# Scenario 2: Release Regression (Verdict: CHANGED)
python -m vitals.main replay demo/fixtures/02_release_regression.jsonl --speed 10.0 --config vitals.demo.yaml

# Scenario 3: Runaway Cost Loop (Verdict: CHANGED · Runaway: TRUE)
python -m vitals.main replay demo/fixtures/03_runaway_loop.jsonl --speed 10.0 --config vitals.demo.yaml

# Scenario 4: User Traffic Shift (Verdict: INCONCLUSIVE · Guard: INPUT_SHIFT)
python -m vitals.main replay demo/fixtures/04_input_shift.jsonl --speed 10.0 --config vitals.demo.yaml
```

Open the **Vitals Console** in your browser once a replay is running: [http://localhost:8787](http://localhost:8787). Watch the **Hero Verdict Card** update live with state colors, sigma meter bars, falsifier statements, and evidence exemplars!

> **Note on Scenario 2's cause label:** at accelerated replay speed the evaluator's real-time tick and the fixture's compressed virtual timestamps diverge, so the release-attribution window can miss and `cause` shows `unattributed` instead of `RELEASE` — the verdict still correctly reaches `CHANGED`. Attribution resolves correctly at `--speed 1.0` (real time, ~11 min) or in the live Quickstart B path below, which sends traffic in real time.

---

## Quickstart B — Live RAG Application with Docker & SigNoz

### Prerequisites
- Docker Desktop running.
- (Optional) `GROQ_API_KEY` in `demo/.env`.

### 1. Deploy SigNoz via Foundry

```bash
cd deploy/signoz
foundryctl cast -f casting.yaml -p ./pours
```

This brings up SigNoz (UI on `localhost:8080`, OTLP ingest on `localhost:4317`) and
the MCP server (`localhost:8000`). See [deploy/signoz/README.md](../deploy/signoz/README.md).

> **Before sending any traffic**, open [http://localhost:8080](http://localhost:8080)
> and complete the signup wizard. The ingester only receives its real OTLP pipeline
> config from the control plane *after* an org/admin account exists — until then it
> looks like it's running, but every span and metric sent to it is silently dropped.

### 2. Launch the App Stack

```bash
cd ../..                                            # back to repo root
cp demo/.env.example demo/.env
docker compose -f demo/compose.yaml up --build -d
```

Services started:
| Service | Address | Role |
|---|---|---|
| `ragapp` | `:8002` | RAG service emitting `gen_ai` semantic spans (`:8000` is SigNoz's MCP server) |
| `collector` | `:4317`\* | OTel Collector fanning out to SigNoz and Vitals (\*host 4319, see `demo/collector/config.yaml`) |
| `vitals` | `:8787` | Vitals sidecar with Console and SigNoz OTLP emitter |

### 3. Import SigNoz Assets

Import all three dashboards in SigNoz UI (`Dashboards -> New dashboard -> Import JSON`):
- `assets/dashboards/overview.json`
- `assets/dashboards/drift.json`
- `assets/dashboards/release-compare.json`

Alerts require at least one notification channel to exist first (`Alerts -> Notification
Channels -> New` — any type, e.g. a webhook; it doesn't need to be a real reachable
endpoint for the demo). Then import the alert rule (`Alerts -> New Alert Rule -> Import
JSON`, selecting your channel when prompted):
- `assets/alerts/verdict-changed.json`

### 4. Run Live Traffic Scenarios

```bash
# Steady traffic (Topic A)
python demo/scenarios/steady_traffic.py --rate 2 --count 50

# Deploy poisoned prompt (v2) and observe CHANGED verdict
bash demo/scenarios/deploy_v2.sh
python demo/scenarios/steady_traffic.py --rate 2 --count 50

# Runaway loop simulation
python demo/scenarios/runaway_loop.py --rate 20 --duration 60

# Input shift simulation (Topic B queries)
python demo/scenarios/traffic_shift.py --rate 2 --count 50
```

### 5. Reset Environment

```bash
bash demo/scenarios/reset.sh
```

---

## Understanding the Vitals Console (`:8787`)

- **Zone 1 (Hero Verdict Card)**: Shows current state (`WARMING`, `STEADY`, `CHANGED`, `INCONCLUSIVE`), behavior/cost sigmas (`+4.2σ`), falsifier line, and **worst + median evidence exemplars**.
- **Zone 2 (Verdict Feed)**: Historical feed of up to 50 stored verdicts with expandable JSON details.
- **Zone 3 (Health Strip)**: Live counters for spans received/scored/skipped, scopes, verdicts emitted, errors, and uptime.
