# Vitals V2 — Engineering Specification

Implementation-ready. Every decision is locked; there are no TBDs. Product
rationale lives in [v2-prd.md](v2-prd.md) and [v2-critique.md](v2-critique.md) —
this document does not re-argue it.

**Grounding:** V1 exists and works (19 tests green). V2 is additive. The OTLP
receiver, mapper, cost engine, price table, emitter, and health module are
**kept as-is** except where an explicit change is listed in §14.

---

## 1. Locked decisions (read this section, then implement)

| # | Decision | Why (one line) |
|---|---|---|
| D1 | **Verdicts are computed on a timer, not per span.** A single evaluator thread ticks every 10s over aggregate scope state. | Keeps the receiver hot path free, gives natural windowing, and makes verdict emission rate independent of traffic rate. |
| D2 | **Two comparison subjects ship: `time` and `release`. `cohort` is deferred.** | `time` fixes cold start and vendor drift; `release` is the hero. `cohort` needs concurrent traffic splitting in the demo app for zero extra narrative. |
| D3 | **Cost is normalized per *request*, not per session.** | One `gen_ai` span == one request. Sessions do not exist in the data model; inventing them adds a join with no demo payoff. |
| D4 | **All deltas are reported in sigma against observed baseline variance.** Raw PSI never reaches a human or an agent. | PRD requirement; "PSI 0.04" is uninterpretable and an agent will invent a meaning for it. |
| D5 | **Vitals ships its own single-screen console** (stdlib HTTP, no framework, no build step) at `:8787`. | The demo needs a controllable visual, and SigNoz dashboard JSON has never been import-verified. SigNoz stays the archive and drill-down target. |
| D6 | **`vitals replay <fixture.jsonl>` is a first-class command.** | Deterministic reproduction for tests *and* a demo that survives Docker, network, or Groq failure. Highest-ROI item in the plan. |
| D7 | **Verdict history persists to SQLite; baselines stay in memory.** | Receipts are a trust feature and cost ~50 lines. Baseline persistence is invisible on stage and is V2.1. |
| D8 | **Truncation/length shift is a *caveat*, not a gate.** | A poisoned prompt legitimately changes output length; gating on it would turn the hero demo beat into `INCONCLUSIVE`. Disclose, don't suppress. |
| D9 | **Input-distribution co-movement *is* a gate** → `INCONCLUSIVE(input_shift)`. | Traffic-mix shift is the most likely false positive in the product (critique T1). This is the one guard that must block. |
| D10 | **Runaway cost bypasses hysteresis; everything else requires 2 consecutive ticks.** | Runaways must page in ~20s; behavior changes must not flap. |
| D11 | **Use plain `sqlite3`; do not reuse spanIQ's `BaselineStore`.** | spanIQ is vendored-unmodified; coupling our schema to theirs creates an upgrade hazard for a table with three columns. |
| D12 | **No new heavy dependencies.** stdlib `http.server`, stdlib `sqlite3`, existing `grpc`/`opentelemetry`/`pyyaml`. | Install friction is an adoption metric, and a hackathon is a bad place to debug a framework. |

---

## 2. Product workflow (final)

```
span arrives ──▶ normalize ──▶ [cost.record] [quality.score] [scope.observe]
                                                                    │
                            every 10s: EvaluatorThread ─────────────┘
                                       │
                        build ComparisonWindow (time | release)
                                       │
                        normalize deltas to sigma
                                       │
                        guards ──▶ state machine ──▶ Verdict?
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
              SQLite store      OTLP metric+log      Console feed
                                  (→ SigNoz)          (:8787)
```

A verdict is **emitted** when: state changes, sigma moves ≥ 1.0 within `CHANGED`,
or on a 60s heartbeat. Otherwise the tick is silent.

---

## 3. Data models

All in `vitals/verdict/types.py`. Dataclasses, `slots=True`, frozen where safe.

```python
class VerdictState(str, Enum):
    WARMING      = "warming"
    STEADY       = "steady"
    CHANGED      = "changed"
    INCONCLUSIVE = "inconclusive"

class Subject(str, Enum):
    TIME    = "time"      # this window vs frozen reference
    RELEASE = "release"   # version B vs last STEADY version A

class Cause(str, Enum):
    RELEASE      = "release"
    UNATTRIBUTED = "unattributed"
    NONE         = "none"

class InconclusiveReason(str, Enum):
    LOW_SAMPLE  = "low_sample"
    INPUT_SHIFT = "input_shift"
    WARMING     = "warming"

@dataclass(frozen=True, slots=True)
class Exemplar:
    kind: str          # "worst" | "median"
    trace_id: str
    span_id: str
    output_excerpt: str    # <= 240 chars, whitespace-collapsed
    behavior_sigma: float

@dataclass(frozen=True, slots=True)
class Verdict:
    verdict_id: str            # uuid4 hex, 16 chars
    ts_unix: float
    # scope
    service_name: str
    gen_ai_system: str
    model: str
    version: str               # the version under evaluation
    baseline_version: str | None
    # judgment
    state: VerdictState
    subject: Subject
    cause: Cause
    flag_cost: bool
    flag_behavior: bool
    runaway: bool              # cost velocity ratio breach
    # evidence (sigma units — D4)
    behavior_sigma: float | None
    cost_sigma: float | None
    cost_usd_per_req: float | None
    baseline_cost_usd_per_req: float | None
    velocity_ratio: float | None
    samples: int
    baseline_samples: int
    # onset & attribution
    onset_ts_unix: float | None
    seconds_after_deploy: float | None
    # honesty surface
    inconclusive_reason: InconclusiveReason | None
    caveats: tuple[str, ...]           # e.g. ("output_length_-31%",)
    falsifier: str                     # "would flip to STEADY if ..."
    warming_progress: tuple[int, int] | None   # (have, need)
    exemplars: tuple[Exemplar, ...]
    sentence: str                      # the canonical one-liner (§7)
```

`Verdict` is the only object crossing module boundaries. Store, emitter, console,
and API all serialize this one type.

---

## 4. Detection pipeline

### 4.1 Scope key

`ScopeKey = (service_name, gen_ai_system, model)` — **version excluded**, matching
V1's existing `_baseline_key`. Version is a dimension of comparison, never of the
reference.

### 4.2 `CalibratedSignal` — the reusable primitive

`vitals/verdict/signal.py`. Wraps every measured quantity so §D4 is structural,
not a convention someone can forget.

```python
class CalibratedSignal:
    def __init__(self, calib_n: int, sigma_floor: float = 1e-6): ...
    def observe_calibration(self, x: float) -> None   # during calibration
    def calibrated(self) -> bool
    def z(self, x: float) -> float                    # (x - mu) / sigma
    mu: float; sigma: float; n: int
```

Four signals per scope, all calibrated from the same post-warming window:

| Signal | Measures | Used for |
|---|---|---|
| `behavior` | output PSI vs frozen reference | `behavior_sigma` |
| `input` | input-text PSI vs frozen reference | G2 gate (D9) |
| `cost` | USD per request | `cost_sigma` |
| `length` | output character count | caveat (D8) |

**Input PSI reuses the exact same `ResponseDriftMetric` machinery**, called with
`actual_output=span.input_text` against a frozen reference of input texts. No new
statistics; one extra reference list. This is deliberate — same distributional
lens on both sides makes the co-movement comparison meaningful.

### 4.3 `ScopeState`

`vitals/verdict/scope.py`. One per `ScopeKey`, own `threading.Lock`.

```
reference_outputs: list[str]        # frozen at N=30 (existing Baseline behaviour)
reference_inputs:  list[str]        # frozen at N=30  (NEW)
signals: dict[str, CalibratedSignal]
windows: dict[version, RollingWindow]   # deque, maxlen=window_max (500)
version_timeline: list[(version, first_seen_ts)]
current_state: VerdictState
last_verdict: Verdict | None
state_since_ts: float
consecutive_condition_ticks: int
```

`RollingWindow` holds per-span records: `(ts, behavior_psi, input_psi, usd,
out_len, trace_id, span_id, output_excerpt)`. `maxlen=500` bounds memory at
roughly 500 × 300 B ≈ 150 KB per version per scope. Acceptable.

### 4.4 Lifecycle phases

```
COLLECTING_REFERENCE  (n < 30)              → WARMING, progress (n, 30)
CALIBRATING           (next 30 samples)     → WARMING, progress (n, 30)
LIVE                  (all signals ready)   → STEADY | CHANGED | INCONCLUSIVE
```

Both phases report `WARMING` with visible progress — the critique's C3 fix.
Never emit a non-warming verdict during either.

### 4.5 Evaluation tick (every `evaluate_interval_s`, default 10)

For each scope, for each version with ≥1 span in the last `window_s` (default 300):

1. **Select subject.** If this version is not the reference version *and* the
   scope has a prior `STEADY` version → `RELEASE` (baseline = last STEADY
   version). Otherwise → `TIME` (baseline = frozen reference).
2. **Aggregate** the current window: `n`, `mean_behavior_psi`, `mean_input_psi`,
   `mean_usd_per_req`, `mean_out_len`, `velocity_usd_per_min`.
3. **Normalize** each to sigma via `CalibratedSignal.z(...)`.
4. **Runaway check:** `velocity_ratio = current_velocity / max(baseline_velocity, eps)`.
   If `≥ runaway_ratio` (default 20.0) → set `runaway=True`, `flag_cost=True`,
   skip hysteresis (D10).
5. **Guards** (§5), in order. First trip wins.
6. **State machine** (§6).
7. **Build verdict** if emission is warranted (§2).

### 4.6 Attribution

`vitals/verdict/attribution.py`. On transition into `CHANGED`:

- Find the most recent entry in `version_timeline` whose `first_seen_ts` falls
  within `attribution_window_s` (default 300) **before** `onset_ts`.
- Found → `cause=RELEASE`, `baseline_version` = previous version,
  `seconds_after_deploy = onset_ts - first_seen_ts`.
- Not found → `cause=UNATTRIBUTED`, `seconds_after_deploy=None`.

`UNATTRIBUTED` is a first-class success, not a failure — it is the vendor-drift
and runaway case, and the sentence says so plainly.

---

## 5. Guards

Evaluated in this order; the first that trips sets the state and stops.

| # | Guard | Condition | Result |
|---|---|---|---|
| G0 | Warming | any signal not calibrated | `WARMING`, `progress=(have, need)` |
| G1 | Low sample | `n < min_samples` (default 30) | `INCONCLUSIVE(low_sample)` |
| G2 | **Input co-movement** | `behavior_z ≥ sigma_threshold` **AND** `input_z ≥ sigma_threshold` | `INCONCLUSIVE(input_shift)` |
| G3 | Length shift | `abs(pct_change(mean_out_len)) ≥ 0.25` | **caveat only** — appended to `caveats`, does not change state (D8) |

`sigma_threshold` default **3.0**. Justification: with a calibrated Gaussian-ish
signal, 3σ is a ~0.3% per-tick false-positive rate; combined with the 2-tick
hysteresis (D10) that is effectively zero over a 7-day steady run, which is the
PRD's non-negotiable metric.

**G2 is the only guard that can mask a real regression.** That is an accepted,
documented trade: a simultaneous input+output shift is far more often a traffic
change than a model change, and the falsifier line tells the user exactly what
was suppressed and why.

---

## 6. State machine

States: `WARMING`, `STEADY`, `CHANGED`, `INCONCLUSIVE`.

```
                 ┌──────────────────────────────────────────┐
   (start) ──▶ WARMING ──(all signals calibrated)──▶ STEADY  │
                 ▲                                     │     │
                 │                              condition    │
              (never — warming is                held 2 ticks│
               terminal per scope,                     ▼     │
               reference is frozen)               CHANGED ───┤
                                                       │     │
                                    condition clear    │     │
                                    AND held ≥120s ────┘     │
                                                             │
        any state ──(guard G1/G2 trips)──▶ INCONCLUSIVE ─────┘
                     (returns to prior evaluation next tick)
```

Rules, locked:

- **Entry to `CHANGED`** requires `condition = (behavior_z ≥ 3.0) OR (cost_z ≥ 3.0)`
  true on **2 consecutive ticks** (≈20s), **unless** `runaway` — which enters
  immediately (D10).
- **Exit from `CHANGED` to `STEADY`** requires condition false **and**
  `now - state_since_ts ≥ min_hold_s` (default 120). Prevents flapping and keeps
  the demo card stable while the presenter talks.
- **`INCONCLUSIVE` is not sticky.** It is recomputed every tick; the next clean
  tick returns to normal evaluation. It never latches, because latching
  uncertainty is worse than reporting it.
- **`WARMING` is terminal per scope** — once calibrated, a scope never returns to
  warming, because the reference is frozen for the process lifetime.
- **`flag_cost` / `flag_behavior`** are independent booleans on `CHANGED`. There
  is no combined state name (critique C5).

---

## 7. The sentence

One canonical renderer, `Verdict.sentence`, built in `types.py`. Every surface —
console, log body, alert, agent — uses this exact string. One implementation, one
format, no drift between surfaces.

**Grammar:**

```
{STATE} · {flags} · {subject-clause} · {evidence} · {attribution} · n={n}
```

**Locked examples:**

```
STEADY · ragapp v1 · behavior +0.3σ · cost +0.1σ · n=412

CHANGED · behavior · v2 vs v1 · +4.2σ (normal ±1σ) · cost flat +0.3σ ·
  onset 14:32:07, 90s after v2 deployed · n=1240

CHANGED · cost · runaway: 51× baseline burn rate · behavior flat +0.4σ ·
  cause unattributed — no release in the last 5m · n=88

INCONCLUSIVE · input_shift · behavior +3.8σ but input +4.1σ —
  your traffic changed, not your model · n=205

WARMING · ragapp v1 · collecting reference 340/1000 · est. 22m
```

Rules: sigma always signed and to 1 decimal; `flat` used when `abs(z) < 1.0`;
never print PSI; never use the words *quality*, *regression*, *good*, or *bad*.

**Falsifier line** (separate field, always populated):

| State | Falsifier |
|---|---|
| `CHANGED` behavior | `"would flip to STEADY if input drift ≥3σ (currently 0.4σ)"` |
| `CHANGED` cost | `"would flip to STEADY if velocity returns within 3σ for 120s"` |
| `INCONCLUSIVE` | `"would resolve if input drift drops below 3σ"` |
| `STEADY` | `"would flip to CHANGED at behavior ≥3σ (currently 0.3σ)"` |

---

## 8. Contracts

### 8.1 New metrics (append to `vitals/contract.py`; existing names unchanged)

| Metric | Type | Unit | Notes |
|---|---|---|---|
| `vitals.verdict.state` | observable gauge | `1` | `0`=warming `1`=steady `2`=changed `3`=inconclusive |
| `vitals.verdict.behavior_sigma` | observable gauge | `1` | signed |
| `vitals.verdict.cost_sigma` | observable gauge | `1` | signed |
| `vitals.verdict.velocity_ratio` | observable gauge | `1` | current / baseline burn rate |
| `vitals.verdict.samples` | observable gauge | `1` | window n |
| `vitals.health.scopes` | observable gauge | `1` | live scope count |
| `vitals.health.verdicts_emitted` | observable counter | `1` | — |

Attributes on every verdict metric: `service.name`, `service.version`,
`gen_ai.system`, `gen_ai.request.model`, `vitals.subject`, `vitals.cause`,
`vitals.flag_cost`, `vitals.flag_behavior`, `vitals.runaway`, `vitals.verdict_id`.

Cardinality check: scopes × versions × 4 enum-ish attrs. For the demo, 1 scope ×
2 versions = 2 series per metric. In production, bounded by deploy frequency.
`verdict_id` is high-cardinality — **it is emitted on the log only, not on the
metric.** (Locked correction to the list above: drop `vitals.verdict_id` from
metric attributes.)

### 8.2 Verdict log record

Emitted once per verdict, severity `WARN` when `CHANGED`, else `INFO`.

- `body` = `Verdict.sentence`
- `trace_id` / `span_id` = the **worst exemplar's** ids, so SigNoz's native
  log→trace correlation jumps straight to the evidence.
- attributes: every scalar `Verdict` field, flattened with the `vitals.` prefix,
  plus `vitals.falsifier`, `vitals.caveats` (comma-joined),
  `vitals.exemplars` (JSON string, ≤2 KB).

### 8.3 HTTP API (console, `:8787`)

| Method | Path | Returns |
|---|---|---|
| `GET` | `/` | the console HTML (§9) |
| `GET` | `/api/verdicts?limit=50` | `{"verdicts": [Verdict, ...]}` newest first |
| `GET` | `/api/verdicts/{verdict_id}` | full `Verdict` incl. exemplars |
| `GET` | `/api/scopes` | live scope states + warming progress |
| `GET` | `/api/health` | health snapshot + uptime + version |

JSON is `Verdict` serialized field-for-field, enums as their string values,
`None` preserved as `null`. Read-only; no auth; binds `127.0.0.1` by default.

### 8.4 SigNoz alert

One alert rule, `assets/alerts/verdict-changed.json`: threshold on
`vitals.verdict.state >= 2` for 1 minute.

Message template (the entire verdict, no link required — critique C6):

```
{{service.name}} {{service.version}} — VERDICT CHANGED
behavior {{vitals.behavior_sigma}}σ · cost {{vitals.cost_sigma}}σ
cause: {{vitals.cause}} · subject: {{vitals.subject}} · n={{vitals.samples}}
runaway: {{vitals.runaway}}
Full record: vitals verdict log, trace-linked.
```

V1's `cost-velocity` and `quality-drift-onset` rules are **retired** — their
signals are now inputs to the verdict (PRD F3). Delete the JSON files; keep
`version-regression.json` deleted too. One rule ships.

---

## 9. UI — the Vitals Console

**One screen. No navigation. No routing. No build step.** Server-rendered HTML
from Python f-strings, one inline `<style>`, a 2-second `fetch` poll that
replaces innerHTML. Dark terminal aesthetic — monospace, near-black background,
one accent color per state.

State colors: `WARMING` grey `#6b7280` · `STEADY` green `#22c55e` ·
`CHANGED` amber `#f59e0b` · `INCONCLUSIVE` blue `#3b82f6`.

**`CHANGED` is amber, not red.** Vitals reports change, not failure — the color
must not make a claim the words refuse to make.

### Screen hierarchy (top to bottom, single column, max-width 900px)

**Zone 1 — Verdict Card** (the hero; this is the Release Report Card):

```
┌─────────────────────────────────────────────────────────┐
│ ● CHANGED                                  ragapp · v2  │
│ behavior · release · v2 vs v1                           │
│                                                         │
│   behavior   +4.2σ  ████████████░░░░░░  normal ±1σ      │
│   cost       +0.3σ  █░░░░░░░░░░░░░░░░░  flat            │
│                                                         │
│ onset 14:32:07 — 90s after v2 deployed                  │
│ n=1240 · baseline v1 (n=30)                             │
│                                                         │
│ ⚠ caveats: output length −31%                           │
│ ? would flip to STEADY if input drift ≥3σ (now 0.4σ)    │
│                                                         │
│ evidence                                                │
│  [worst ] 4f2a91… +6.1σ  "Sure! Here's a fun fact…"     │
│  [median] 91cd07… +0.2σ  "OpenTelemetry is a CNCF…"     │
└─────────────────────────────────────────────────────────┘
```

**Exemplars always show one median beside the worst ones** (critique C5). The
median row is not optional and not collapsible.

**Zone 2 — Verdict Feed**: reverse-chronological, one line each, `time · state ·
sentence`. Clicking expands the stored verdict inline (receipts, PRD trust
mechanism #3). Cap at 50.

**Zone 3 — Health strip**: `spans received / scored / skipped · scopes · verdicts
emitted · emit errors · uptime`. Small, grey, bottom. Proves Vitals is alive when
the verdict is `STEADY` — the "silence is working, not broken" affordance.

---

## 10. Folder structure

```
vitals/
  contract.py            # MODIFIED: + verdict metric/log names, state enum values
  model.py               # unchanged
  main.py                # MODIFIED: wire evaluator + console; add `replay` command
  health.py              # MODIFIED: + scopes, verdicts_emitted
  config/settings.py     # MODIFIED: + VerdictConfig, ConsoleConfig, StoreConfig
  ingest/                # unchanged
  cost/                  # MODIFIED: engine exposes baseline velocity accessor
  quality/
    engine.py            # MODIFIED: returns input_psi + out_len on the record
    baseline.py          # MODIFIED: + reference_inputs alongside reference outputs
    types.py             # MODIFIED: EvalLogRecord + input_drift, output_len
  verdict/               # NEW
    __init__.py
    types.py             # Verdict, Exemplar, enums, sentence renderer
    signal.py            # CalibratedSignal
    scope.py             # ScopeState, RollingWindow
    attribution.py       # version timeline -> Cause
    evaluator.py         # tick loop, guards, state machine
  store/                 # NEW
    __init__.py
    db.py                # sqlite3: verdicts table, insert/list/get
  console/               # NEW
    __init__.py
    server.py            # ThreadingHTTPServer, routes
    render.py            # HTML/CSS as f-strings
  replay/                # NEW
    __init__.py
    fixtures.py          # JSONL read/write, GenAISpan (de)serialization
    runner.py            # clock-injected replay driver
  agent/                 # NEW
    skills.md            # SigNoz Agent Skill

assets/
  alerts/verdict-changed.json      # NEW (replaces the three V1 rules)
  dashboards/release-compare.json  # KEPT, retargeted at vitals.verdict.*
  dashboards/{overview,drift}.json # KEPT as-is

demo/
  scenarios/
    steady_traffic.py    # NEW — background driver, beat A
    runaway_loop.py      # KEPT
    deploy_v2.sh         # KEPT
    traffic_shift.py     # NEW — beat D (the honesty beat)
    reset.sh             # KEPT
  ragapp/corpus.py       # MODIFIED: + off-topic corpus for traffic_shift

test/
  test_cost.py test_mapper.py test_quality.py test_pipeline_integration.py  # KEPT
  test_signal.py         # NEW
  test_scope.py          # NEW
  test_state_machine.py  # NEW
  test_attribution.py    # NEW
  test_guards.py         # NEW
  test_store.py          # NEW
  test_replay_golden.py  # NEW — the four golden scenarios
  fixtures/
    steady.jsonl  runaway.jsonl  deploy_v2.jsonl  traffic_shift.jsonl
```

---

## 11. Configuration

`vitals.yaml`, additive. Existing sections unchanged.

```yaml
receiver:
  grpc_port: 4327
  host: 0.0.0.0

emit:
  endpoint: http://localhost:4317
  export_interval_ms: 5000
  queue_max: 10000

cost:
  price_table: vitals/cost/prices.yaml
  velocity_window_s: 60

quality:
  enabled: true
  baseline_window: 30
  drift_threshold: 0.10
  cusum_k: 0.5
  cusum_h: 5.0
  weight_drift: 0.6
  weight_consistency: 0.2
  weight_stability: 0.2

verdict:                      # NEW
  enabled: true
  evaluate_interval_s: 10     # tick period
  window_s: 300               # current-window lookback
  window_max: 500             # per-version rolling record cap
  min_samples: 30             # G1 floor
  sigma_threshold: 3.0        # CHANGED entry
  consecutive_ticks: 2        # hysteresis (bypassed by runaway)
  min_hold_s: 120             # CHANGED -> STEADY dwell
  heartbeat_s: 60             # re-emit unchanged verdict
  runaway_ratio: 20.0         # velocity multiple -> immediate CHANGED
  attribution_window_s: 300   # deploy->onset window for RELEASE cause
  length_caveat_pct: 0.25     # G3 caveat trigger
  calibration_samples: 30     # per-signal calibration window
  exemplars_worst: 2
  exemplars_median: 1

console:                      # NEW
  enabled: true
  host: 127.0.0.1
  port: 8787

store:                        # NEW
  path: vitals.db
  retain_verdicts: 1000
```

Env overrides follow V1's precedence (env > yaml > default). New vars:
`VITALS_CONSOLE_PORT`, `VITALS_CONSOLE_ENABLED`, `VITALS_STORE_PATH`,
`VITALS_VERDICT_ENABLED`.

**Validation** (extend `VitalsConfig.validate`): `sigma_threshold > 0`;
`consecutive_ticks >= 1`; `min_samples >= 5`; `runaway_ratio > 1`;
`evaluate_interval_s >= 1`; `0 < length_caveat_pct < 1`;
`exemplars_median >= 1` (the median exemplar is not optional — §9).

---

## 12. Storage

Single SQLite file, `WAL` mode, one connection guarded by a lock (write volume is
one row per verdict — contention is not a concern).

```sql
CREATE TABLE IF NOT EXISTS verdicts (
  verdict_id      TEXT PRIMARY KEY,
  ts_unix         REAL NOT NULL,
  service_name    TEXT NOT NULL,
  version         TEXT NOT NULL,
  state           TEXT NOT NULL,
  subject         TEXT NOT NULL,
  cause           TEXT NOT NULL,
  behavior_sigma  REAL,
  cost_sigma      REAL,
  samples         INTEGER NOT NULL,
  sentence        TEXT NOT NULL,
  payload_json    TEXT NOT NULL    -- full Verdict, source of truth for the API
);
CREATE INDEX IF NOT EXISTS idx_verdicts_ts ON verdicts(ts_unix DESC);
```

Columns are duplicated out of `payload_json` only to keep the feed query cheap;
`payload_json` is authoritative. Retention: after each insert, delete rows beyond
`retain_verdicts` by `ts_unix`. Store failures are logged and swallowed — a
storage outage must never suppress a verdict from the metric or log path.

---

## 13. Event lifecycle (end to end)

| Stage | Thread | Action | On failure |
|---|---|---|---|
| 1. OTLP export received | gRPC pool (4) | `_TraceService.Export` | log, return OK — never fail the exporter |
| 2. Map to `GenAISpan` | gRPC pool | `map_span` | count `spans_skipped`, drop |
| 3. Cost record | gRPC pool | `CostEngine.record` | log, continue |
| 4. Quality score | gRPC pool | `QualityEngine.score` → `EvalLogRecord` (+`input_drift`, `output_len`) | log, `emit_errors++`, continue |
| 5. Scope observe | gRPC pool | `ScopeState.observe(span, record)` — appends to rolling window, feeds calibration, records version first-seen | log, continue |
| 6. Eval log emit | gRPC pool | `Emitter.emit_eval_log` (unchanged from V1) | `emit_errors++` |
| 7. **Tick** | `EvaluatorThread` (1, daemon) | for each scope × version: aggregate → guards → state machine → `Verdict?` | log; a failing scope must not stop other scopes — wrap per-scope in try/except |
| 8. Persist | EvaluatorThread | `store.insert(verdict)` | log, swallow |
| 9. Metric update | EvaluatorThread | write into the emitter's verdict snapshot dict (gauges pull on the 5s export) | n/a |
| 10. Verdict log emit | EvaluatorThread | `Emitter.emit_verdict_log(verdict)` | `emit_errors++` |
| 11. Console read | HTTP thread | reads store + live scope snapshot | 500 with JSON error body |

Shutdown order: receiver stop → evaluator join (2s) → console shutdown →
emitter shutdown → store close.

---

## 14. Changes to existing V1 code

Exhaustive; nothing else is touched.

1. **`quality/baseline.py`** — add `reference_inputs: list[str]` collected in
   parallel with `outputs`, frozen at the same window size. Add
   `add_warming_input(text)`.
2. **`quality/engine.py`** — measure input PSI (same `ResponseDriftMetric`,
   `actual_output=span.input_text`, `baseline_outputs=reference_inputs`); return
   it plus `len(span.output_text)` on `EvalLogRecord`. **Do not change** the
   existing drift/CUSUM path or the composite score — V1 tests must stay green.
3. **`quality/types.py`** — `EvalLogRecord += input_drift: float | None`,
   `output_len: int`.
4. **`cost/engine.py`** — add `velocity_for(dims) -> float` so the evaluator can
   read current burn rate per dimension without re-deriving it.
5. **`contract.py`** — append §8.1 names. Nothing removed (V1 dashboards keep
   working).
6. **`health.py`** — add `scopes` and `verdicts_emitted` counters.
7. **`config/settings.py`** — `VerdictConfig`, `ConsoleConfig`, `StoreConfig` +
   validation + env overrides.
8. **`main.py`** — build store, scopes, evaluator, console in `build_pipeline`;
   add `vitals replay` subcommand; extend shutdown.
9. **`emit/emitter.py`** — `verdict_provider` callback + verdict gauges +
   `emit_verdict_log`.
10. **`assets/alerts/`** — delete three rules, add `verdict-changed.json`.

---

## 15. Error handling

| Class | Policy |
|---|---|
| Malformed span | Count `spans_skipped`, drop silently. Never raise to the exporter. |
| Scoring exception | Log at `ERROR` with span id, `emit_errors++`, span contributes cost only. |
| Evaluator exception, one scope | Catch per scope, log, continue to the next. A poisoned scope must never stop the tick. |
| Evaluator exception, tick-level | Catch, log, sleep the interval, continue. The thread never dies. |
| Store write failure | Log `WARN`, swallow. Verdict still reaches metric + log + console-live. |
| OTLP emit failure | Existing V1 behavior (bounded queue, `emit_errors++`). Unchanged. |
| Console request error | HTTP 500, `{"error": "..."}`. Console failure never affects the pipeline. |
| Port already bound (8787) | Log `WARN`, disable the console, **keep running**. The console is a view, not the product. |
| Division by zero in sigma | `CalibratedSignal` enforces `sigma >= 1e-6` (V1's existing `_SIGMA_FLOOR` pattern). |
| Zero baseline velocity | `velocity_ratio = None`, runaway check skipped. |

**Invariant:** no code path in `verdict/`, `store/`, or `console/` may raise into
the ingest hot path. Enforced by a test that pushes 1,000 spans while the store
path is monkeypatched to raise.

---

## 16. Logging

Standard library `logging`, V1's existing format. Levels are locked:

| Level | Used for |
|---|---|
| `DEBUG` | per-tick aggregates (n, sigmas, guard outcomes) — the debugging surface |
| `INFO` | lifecycle (start/stop), scope calibration complete, every verdict emitted (as `Verdict.sentence`) |
| `WARNING` | guard trips that mask a signal (`INCONCLUSIVE`), store failures, console disabled |
| `ERROR` | scoring/evaluator exceptions, emit failures |

Loggers are named `vitals.verdict`, `vitals.store`, `vitals.console`,
`vitals.replay`. **Every emitted verdict is logged at `INFO` as its sentence** —
which means the terminal running `vitals run` is itself a usable demo surface if
the console fails.

---

## 17. Testing strategy

Target: **existing 19 green + ~35 new**. `pytest -q`, ruff clean, no network.

**Unit**
- `test_signal.py` — calibration math, sigma floor, z-score correctness, not-ready guard.
- `test_scope.py` — reference freeze at N, rolling window cap, version first-seen recording.
- `test_guards.py` — G0/G1/G2 trip conditions; G3 produces a caveat and **does not** change state (the D8 regression test).
- `test_attribution.py` — deploy inside window → `RELEASE`; outside → `UNATTRIBUTED`; no timeline → `UNATTRIBUTED`.
- `test_state_machine.py` — hysteresis (1 tick insufficient, 2 sufficient); `min_hold_s` dwell; runaway bypass; `INCONCLUSIVE` non-latching.
- `test_store.py` — insert/list/get round-trip, retention pruning, failure swallowing.

**Golden replay** — `test_replay_golden.py`, the highest-value suite. Each fixture
is a JSONL span sequence with relative timestamps, replayed against an injected
clock; the test asserts the **verdict state sequence**, not exact sigma values.

| Fixture | Asserted sequence | Guards |
|---|---|---|
| `steady.jsonl` (600 spans, 20 min) | `WARMING → STEADY`, and **never** `CHANGED` | the zero-false-positive test — PRD's non-negotiable metric |
| `deploy_v2.jsonl` | `WARMING → STEADY → CHANGED(behavior, cause=release)` | `seconds_after_deploy` within [0, 300] |
| `runaway.jsonl` | `WARMING → STEADY → CHANGED(cost, runaway=True, cause=unattributed)` | enters within 2 ticks of the spike |
| `traffic_shift.jsonl` | `WARMING → STEADY → INCONCLUSIVE(input_shift)` | never `CHANGED` — the G2 proof |

**Contract test** — `Verdict.sentence` snapshot for each of the five §7 examples.
Locks the format so console, log, and alert can never diverge.

**Safety test** — 1,000 spans with `store.insert` monkeypatched to raise;
assert zero exceptions escape and `spans_scored == 1000`.

**Not tested** (deliberate): live SigNoz round-trip, live Groq, console HTML
rendering. All three are demo-day checks on a real stack, not CI.

---

## 18. Demo scenarios and sample data

### Corpus

`demo/ragapp/corpus.py` gains a second topic set. Both are hand-written, fixed,
and committed — no generation at runtime.

- `OTEL_DOCS` — 12 passages on OpenTelemetry/observability. The baseline domain.
- `COOKING_DOCS` — 12 passages on recipes. Used **only** by `traffic_shift.py` to
  move the input distribution while the model stays identical.

`llm.py`'s canned-answer path (already present) keys off `(query, version)` so
every scenario is deterministic with no API key. **The demo must run with
`GROQ_API_KEY` unset.** That is a hard requirement, not a fallback.

### Scenarios

| Script | Beat | What it does | Expected verdict |
|---|---|---|---|
| `steady_traffic.py` | A | 2 req/s of OTEL queries against v1, indefinitely. Started first, left running throughout. | `WARMING` → `STEADY` |
| `runaway_loop.py` | B | Same query re-fired ~40×/s for 30s | `CHANGED · cost · runaway · unattributed` |
| `deploy_v2.sh` | C | Restarts ragapp with `PROMPT_VERSION=v2` (poisoned prompt) | `CHANGED · behavior · release · v2 vs v1` |
| `traffic_shift.py` | D | Switches queries to `COOKING_DOCS` against unchanged v1 | `INCONCLUSIVE · input_shift` |

Beat D is the honesty beat and is **held in reserve** — run it only if a judge
asks about false positives. It is the strongest possible answer to that question,
and it is scripted rather than improvised.

### Fixture capture

`vitals record --out fixture.jsonl` writes every mapped `GenAISpan` to JSONL
while a scenario runs. Capture all four fixtures once, commit them, and the demo
becomes replayable with `vitals replay demo/fixtures/deploy_v2.jsonl --speed 10`
— no Docker, no collector, no network. **Do this on day 1 of demo prep, not
demo morning.**

---

## 19. Milestones

Five milestones. Each ends with something visible in the demo; none depends on a
later one. Sizes assume one engineer.

### M0 — Foundations (0.5 day)
**Deliverables:** `verdict/types.py` (models, enums, sentence renderer);
`verdict/signal.py`; config sections + validation; `contract.py` additions;
`store/db.py`.
**Depends on:** nothing.
**Acceptance:** `test_signal.py`, `test_store.py`, and the sentence snapshot test
pass. `load_config()` accepts the §11 yaml and rejects each invalid value. V1's
19 tests still green.

### M1 — Detection substrate (1 day)
**Deliverables:** `verdict/scope.py`; input-PSI and `output_len` plumbed through
`quality/baseline.py`, `engine.py`, `types.py`; `CostEngine.velocity_for`.
**Depends on:** M0.
**Acceptance:** `test_scope.py` passes; a scope reaches `LIVE` after exactly 60
spans (30 reference + 30 calibration); all four signals report `calibrated()`;
V1 quality tests unchanged and still green.

### M2 — The product (1 day)
**Deliverables:** `verdict/attribution.py`; `verdict/evaluator.py` (tick loop,
guards G0–G3, state machine, exemplar selection); wired into `main.py` as a
daemon thread.
**Depends on:** M1.
**Acceptance:** `test_guards.py`, `test_attribution.py`, `test_state_machine.py`
pass. `vitals run` against live traffic logs `STEADY` at `INFO` within 2 minutes.
Exemplar selection always returns ≥1 median.
**This is the milestone where the product exists.** If the schedule slips,
everything after this is presentation.

### M3 — Delivery (0.5 day)
**Deliverables:** emitter verdict gauges + `emit_verdict_log`; store wiring;
`assets/alerts/verdict-changed.json`; delete the three V1 alert rules;
retarget `release-compare.json` at `vitals.verdict.*`.
**Depends on:** M2.
**Acceptance:** `vitals.verdict.state` visible in SigNoz with correct attributes;
one verdict log per verdict, trace-linked to the worst exemplar; alert fires on a
forced `CHANGED`.

### M4 — Console + replay (1 day)
**Deliverables:** `console/server.py` + `render.py` (§9 layout, all three zones);
`replay/fixtures.py` + `runner.py`; `vitals record` and `vitals replay`
subcommands.
**Depends on:** M2 (M3 is not a prerequisite — the console reads the store and
live scope state directly).
**Acceptance:** `:8787` renders the hero card with worst **and** median
exemplars; feed rows expand; health strip updates. `vitals replay` reproduces a
fixture's verdict sequence identically at `--speed 10`.

### M5 — Narrative (1 day)
**Deliverables:** `steady_traffic.py`, `traffic_shift.py`, `corpus.py` second
topic set; four captured fixtures committed; `test_replay_golden.py`;
`agent/skills.md`; `demo/README.md` run-of-show; `docs/blind-spots.md`.
**Depends on:** M4.
**Acceptance:** all four golden replays pass in CI. A cold `docker compose up` +
three scripts produces the three demo beats. `skills.md` instructs an agent to
refuse rollback advice on `INCONCLUSIVE` (PRD F6).

**Critical path:** M0 → M1 → M2 → M4 → M5. M3 can be done in parallel with M4 or
dropped to a stretch if SigNoz import fights back — the console and the `INFO`
log carry the demo without it.

**If you have only 3 days:** M0, M1, M2, M4 (console), and a reduced M5 with two
fixtures (`steady`, `deploy_v2`). Ship M3 after the demo.

---

## 20. Definition of done

1. `pytest -q` green (19 existing + ~35 new), `ruff` clean.
2. `vitals run` with `GROQ_API_KEY` unset produces `STEADY` on steady traffic
   within 2 minutes and **never** produces `CHANGED` on `steady.jsonl`.
3. `deploy_v2.sh` produces `CHANGED · behavior · release · v2 vs v1` with
   `seconds_after_deploy` populated, within 60s of the deploy.
4. `runaway_loop.py` produces `CHANGED · cost · runaway` within 30s.
5. `traffic_shift.py` produces `INCONCLUSIVE · input_shift` and never `CHANGED`.
6. Console at `:8787` shows the hero card with a median exemplar beside the worst.
7. `vitals replay demo/fixtures/deploy_v2.jsonl` reproduces beat C with no
   collector, no Docker, and no network.
8. `docs/blind-spots.md` exists and is linked from the console footer.

**Still prohibited (carried from the PRD):** no published drift-onset-latency
number anywhere — README, console, alert, or pitch — until CUSUM is calibrated
against real traffic. The demo says *"onset 90s after deploy"* as an observed
fact about that run, never as a product claim.
