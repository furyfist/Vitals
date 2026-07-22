# Vitals — Implementation Plan (V1)

> **Status: FROZEN v1.0 — implementation source of truth.**
> This document is self-contained: a fresh engineering session with zero prior context can start coding from it. Every hard tradeoff is decided here, with the losing alternative named once and not revisited.
>
> Product: **Vitals** — the missing vital signs for AI systems: **cost** and **quality**, as first-class, alertable SigNoz signals.
> Event: Agents of SigNoz Hackathon (WeMakeDevs × SigNoz), July 20–26 2026, **Track 1: AI & Agent Observability**. Team: 4 engineers.
> Core asset: **spanIQ** (existing, pre-hackathon: deterministic LLM evaluation engine — semantic similarity, consistency, stability, drift; CUSUM alerting; PELT changepoint attribution; OTLP gRPC+HTTP receiver with GenAI-semconv mapping; 244 passing tests; Apache 2.0). spanIQ core is a **dependency, not a construction site** — it is not modified except for bugfixes. All hackathon work is the Vitals layer.

---

## 0. Context — why this project exists

**The thesis.** Observability has three signals for machines: traces, metrics, logs. AI systems need two more that no OTel-native platform provides today: **what it costs right now** and **whether the answers are any good**. SigNoz currently shows latency, tokens, errors — and is blind to both runaway spend-rate and silent quality failure. Vitals adds both as native SigNoz signals on one pipeline.

**Evidence — quality blindness (the deep pain):**
- April 2026: **Anthropic confirmed Claude Code quality complaints were caused by product-layer prompt/reasoning changes — "no model version change, no notification, no way to detect it without measuring outputs; engineers found out through user complaints"** ([writeup](https://dev.to/delafosse_olivier_f47ff53/silent-degradation-in-llm-systems-detecting-when-your-ai-quietly-gets-worse-4gdm)). If Anthropic can't catch this internally, no app team can.
- "[An AI agent can return 200 OK with a completely wrong answer](https://www.braintrust.dev/articles/llm-observability-guide)"; "[quality degradation happens silently… without triggering a single alert in your existing stack](https://www.kalviumlabs.ai/blog/llm-observability-in-production/)."
- [VB Pulse early-2026: 33% of enterprises that scaled RAG in 2025 now prioritize *rebuilding* their retrieval stack; the drivers — wrong chunks, ungrounded answers, silent accuracy drift — are "exactly what standard monitors never catch"](https://www.braintrust.dev/articles/agent-observability-complete-guide-2026).
- Verified HN complaint: engineer's company [went through three LLM-observability vendors and still couldn't get the basic quality-debugging workflow](https://news.ycombinator.com/item?id=45716518).
- [Prompt updates drive most LLM production incidents](https://deepchecks.com/llm-production-challenges-prompt-update-incidents/); provider model updates shift behavior [with regressions undetected until users complain](https://qawerk.com/blog/llm-regression-testing/).

**Evidence — cost blindness (the visceral pain):**
- [$47,000 burned by a 4-agent loop over 11 days](https://dev.to/waxell/the-47000-agent-loop-why-token-budget-alerts-arent-budget-enforcement-389i); [$2,847 in 4 hours "with all monitoring dashboards green"](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-burn-2026/); [agents burn ~50–100× more tokens than equivalent chat](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/).

**Why nothing solves this today:**
- Eval vendors run **offline, sampled, and paid**: [LangSmith ~$2,514/mo trace overages at 1M events; Langfuse's deterministic online checks only reached basic GA (JSON-schema checks) in May 2026](https://www.morphllm.com/comparisons/langfuse-vs-langsmith); LLM-as-judge is too expensive and too nondeterministic to run on every trace.
- Teams therefore run **two stacks** — an LLM-eval tool *plus* infra APM ([industry-admitted pattern](https://www.braintrust.dev/articles/arize-ai-alternatives-2026)) — and quality never reaches the alerting system that pages anyone.
- **The OTel GenAI semantic conventions do not cover evaluation results** — embedding eval results into telemetry is ["still in early discussion" in the GenAI SIG](https://www.fiddler.ai/blog/opentelemetry-ai-observability-guide). The standard slot is empty; Vitals ships a working reference implementation and a public convention proposal (`gen_ai.evaluation.*`) — high-leverage with an OTel-native sponsor/judge.
- SigNoz's own [LLM observability docs](https://signoz.io/docs/llm-observability/) cover tokens/cost/latency dashboards; evaluation appears only as an "emerging trend."

**Why spanIQ is the unfair advantage:** deterministic scoring at $0/trace and ~ms latency is the only approach that can run **inline on 100% of traffic** (judges economically can't); spanIQ already has the scoring engine, drift statistics (CUSUM/PELT), and an OTLP receiver. The hackathon's hardest problem — a credible, reproducible quality metric — is a solved dependency. Hackathon rules allow existing projects with substantial modification; the entire Vitals layer (fan-out pipeline, emitters, price engine, convention proposal, dashboards, alerts, demo system) is new, dated, in-event work.

---

## 1. Product Definition

**V1 is:** an OTel-native sidecar service (**vitals**) that receives a fan-out copy of gen_ai spans from the user's existing OTel Collector, and emits two new signal families back into SigNoz:
1. **Cost vitals** — per-service/model/version token spend-rate (`vitals.cost.velocity`, USD/min via a bundled price table) and cumulative burn, with alert rules that catch runaway loops in minutes, not invoices.
2. **Quality vitals** — deterministic, reference-free quality scores on every LLM response (drift-from-healthy-baseline, self-consistency, output stability) computed by spanIQ, plus **drift-onset detection** (CUSUM) — dimensioned by `service.name`, `service.version`, and model, enabling per-release quality comparison.

Plus the SigNoz experience: **three dashboards** (Vitals Overview — quality beside cost beside latency; Release Compare — quality/cost split by `service.version`; Drift — score timelines with onset markers) and **alert rules** (token-velocity breach; quality-drift onset; per-version regression).

**V1 is NOT:** a proxy/gateway (we observe, we don't sit in the request path); an enforcement layer (no kill switches — [alerts aren't enforcement](https://dev.to/waxell/the-47000-agent-loop-why-token-budget-alerts-arent-budget-enforcement-389i), and enforcement belongs in a gateway; V3); a ground-truth correctness oracle (see honesty framing below); an eval-authoring UI; a replacement for offline eval suites; per-chunk RAG grounding (V2); per-tenant segmentation (V2); security/injection signals (V3).

**The honesty framing (non-negotiable, baked into all copy and demo):** online quality scores are **deviation-from-established-good-baseline**, not absolute correctness. Vitals answers "did quality *change*, when, and with which release" — the question behind the Anthropic incident — not "is this answer true." Reference-based absolute scoring exists only against the seeded eval set in the demo. Over-claiming correctness is how this product dies in expert review; the drift framing is also what makes reference-free online scoring legitimate.

**User persona:** the small team / solo founder running an AI product on SigNoz with no ML-eval team. Before: prompt tweak ships → dashboards green → users quietly get worse answers or an agent loop quietly burns $80/hr → discovery via complaint or invoice. After: quality and cost-rate are lines on the same dashboard as p99, and both page you.

---

## 2. Version Roadmap

- **V1 (hackathon):** both signal families, as defined above. Internal build order: cost first (proves the whole pipeline end-to-end in days — it's arithmetic), quality second (the deep half). This order is a build sequence, not a priority ranking: quality is the product's identity; cost is the pipeline's proof and the demo's hook.
- **V2 — Depth:** per-chunk RAG grounding scores (query↔chunks, answer↔chunks); per-tenant/user impact dimensions ("which customers are affected"); PELT changepoint *attribution* (which pipeline component drifted); reference-set spot-check scheduling; persistent baselines across restarts.
- **V3 — Reach:** `gen_ai.evaluation.*` convention proposal upstreamed to the OTel GenAI SIG; enforcement webhooks (budget circuit-breakers via gateway integration); behavioral-security signals (anomalous tool-call velocity); multi-backend support.

---

## 3. Architecture (decisions with losing alternatives)

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

**D1 — Ingestion: collector fan-out to vitals' OTLP receiver.** The user's collector adds one exporter; vitals receives the same gen_ai spans SigNoz does (spanIQ V4's OTLP receiver, already GenAI-semconv-aware). *Proxy loses:* not OTel-native, injects latency/failure risk into the request hot path, and duplicates Helicone. *Polling SigNoz's API loses:* laggy, load on SigNoz, and makes SigNoz a dependency of scoring rather than a destination.

**D2 — Scoring is asynchronous, out-of-request-path, on 100% of traffic.** Scores lag traces by seconds; nothing user-facing ever waits on Vitals. Determinism + $0/trace is what makes 100% coverage possible — this is the structural moat over judge-based tools and is stated everywhere.

**D3 — Emission: OTLP metrics + trace_id-linked structured log records. No span re-emission.** Metrics carry the dashboards/alerts; eval log records (one per scored response, containing scores + trace_id) give per-trace drill-down via SigNoz's native logs↔traces correlation. *Re-emitting enriched spans loses:* duplicates the user's traces in SigNoz (pollution, double cost, confusing UX). Metric names implement our public `gen_ai.evaluation.*` / `vitals.cost.*` convention proposal (`docs/conventions.md` — written as if for the OTel GenAI SIG; this document is a first-class deliverable).

**D4 — Emission is out-of-band** (direct to SigNoz ingest, not through the monitored collector). If the user's pipeline is misbehaving, the vitals must survive. (Law borrowed from our Track 2 sibling project; independently correct here.)

**D5 — Language: Python.** spanIQ is Python; the integration wraps it in-process. A second language buys nothing and forfeits the asset. (Contrast deliberately with spanLedger's Go choice — there the asset was greenfield and the ecosystem was Go; here the asset decides.)

**D6 — V1 online quality metrics are reference-free:** ResponseDrift vs a rolling healthy-baseline window, self-consistency, output stability, plus embedding-distribution drift (PSI/KS) — all run without golden answers. *Reference-based similarity as the online metric loses:* production traffic has no references; pretending otherwise is the credibility hole judges would find in minutes. CUSUM provides onset timestamps; PELT attribution deferred to V2 (descope candidate, not core).

**D7 — Cost engine is span-attribute arithmetic inside vitals** (`gen_ai.usage.input_tokens`/`output_tokens` × bundled per-model price table, YAML, user-overridable) → `vitals.cost.velocity` (USD/min, per service/model/version) + `vitals.cost.total`. *Building it as collector processors loses:* splits the product across two codebases for a sum.

**D8 — State: SQLite via spanIQ's existing storage** (baselines, score history). Known write ceiling (~500 spans/s documented in spanIQ) is far above demo load and is documented honestly as a current limit.

**D9 — Demo app instrumentation: OpenLLMetry (Traceloop) auto-instrumentation** for gen_ai semconv spans over a small Groq-powered RAG app (free tier: ~30 RPM / 6K TPM — ample). *Manual instrumentation is the fallback* if the auto-instr attribute shapes disagree with spanIQ's mapper (spike S3).

**Failure handling:** vitals down → user's pipeline completely unaffected (fan-out exporter drops; SigNoz path untouched). SigNoz ingest unreachable → vitals buffers metrics in memory with bounded queue, logs honestly. Malformed/non-gen_ai spans → counted, skipped, never crash the scorer. Baseline cold-start → quality signals report `warming` (no score) until the baseline window fills — **never emit a score that could be a false alarm** (same never-over-report discipline as spanLedger: a false quality page kills trust permanently).

---

## 4. Repository Structure

```
vitals/
├── vitals/                      # the new package (all hackathon work)
│   ├── ingest/                  # OTLP receiver glue → span router        [E1]
│   ├── cost/                    # price table, velocity engine            [E1]
│   ├── quality/                 # spanIQ adapter, baselines, CUSUM glue   [E2]
│   ├── emit/                    # OTLP metric/log emitters (out-of-band)  [E1]
│   ├── config/                  # vitals.yaml load/validate               [E2]
│   └── main.py                  # single entrypoint: `vitals run`
├── spaniq/                      # vendored dependency (unmodified core)
├── assets/dashboards/           # overview.json, release-compare.json, drift.json  [E4]
├── assets/alerts/                                                          [E4]
├── demo/
│   ├── compose.yaml             # app + collector(fan-out) + SigNoz + vitals       [E3]
│   ├── ragapp/                  # Groq RAG app, OpenLLMetry-instrumented,
│   │                            #   versioned prompts (v1 good / v2 poisoned)      [E3]
│   ├── scenarios/               # runaway_loop.py, deploy_v2.sh, reset.sh          [E3]
│   └── README.md                                                                   [E3+E4]
├── docs/conventions.md          # gen_ai.evaluation.* proposal (deliverable)       [E4]
├── docs/architecture.md  docs/honesty.md (the drift-not-truth framing, public)     [E4]
├── test/                        # unit: cost math, baseline/CUSUM behavior, mapper
├── .github/workflows/ci.yaml    # ruff + pytest (spanIQ's 244 tests keep running)
├── PROJECT_PLAN.md  README.md
```

---

## 5. Milestones

**M0 — Spikes + scaffold (Jul 17–19):** S1–S4 below; repo scaffold; compose stack with SigNoz up; contract freeze (metric names, eval-log schema, vitals.yaml — §3/D3); pre-event blog if pursuing (due Jul 19).
**M1 — Cost vital end-to-end (Jul 20–21):** fan-out → vitals → cost velocity metric → SigNoz dashboard panel → alert fires on a scripted runaway loop. **Proves the entire pipeline with the simple signal first.**
**M2 — Quality vital (Jul 21–23):** spanIQ adapter scoring live spans; rolling baseline + warming state; drift + consistency metrics; CUSUM onset; eval logs with trace_id drill-down; Drift dashboard.
**M3 — Release Compare + scenarios (Jul 23–24):** `service.version` dimensions everywhere; Release-Compare dashboard; poisoned-v2 deploy scenario detects within target window (spike S4 defines it); all alerts; `reset.sh`. **Feature freeze Jul 24 EOD.**
**M4 (only if ahead; first cut):** PyPI publish of vitals (+spanIQ), per-tenant dimension preview.
**Jul 25–26:** demo video (cost hook → quality payoff, per demo/README.md run-of-show), blog, README, submission.

**Descope ladder (cut in order):** 1) PyPI publish → 2) per-tenant preview → 3) consistency/stability metrics (keep drift — it carries the demo) → 4) embedding-distribution PSI (keep response drift). **Never cut:** fan-out pipeline, cost velocity + alert, response-drift + CUSUM onset, Release Compare, the honesty framing.

---

## 6. Team

| | Owns | Week-1 focus |
|---|---|---|
| E1 | ingest/, cost/, emit/ | S1, S2; M1 end-to-end |
| E2 | quality/, config/, spanIQ adapter | S4 (detection sensitivity — the make-or-break spike) |
| E3 | demo/: compose, ragapp, scenarios, reset | S3; scenario reliability |
| E4 | dashboards, alerts, conventions.md, honesty.md, README, blog, video | Blog by Jul 19; dashboard round-trip with E1 |

Sync points: Day-1 contract freeze (§3 D3 schemas) · M1 checkpoint (end Jul 21: pipeline proven) · M3 freeze + full rehearsal (Jul 24).

---

## 7. Spikes (before feature work)

| # | Assumption | Test | Fallback |
|---|---|---|---|
| S1 | Collector fan-out → spanIQ's OTLP receiver works with real gen_ai spans at demo load | Wire it, replay recorded spans | Patch receiver mapping (allowed: it's glue, not core); worst case vitals embeds its own light OTLP receiver |
| S2 | OTLP metrics + trace_id-linked logs render/alert correctly in SigNoz | Emit synthetic vitals, build one panel + one alert | Metrics via Prometheus-scrape path; logs remain OTLP |
| S3 | OpenLLMetry's gen_ai attribute shapes match spanIQ's semconv mapper | Instrument ragapp, inspect spans | Manual instrumentation of ragapp (half-day) |
| S4 | **Poisoned-prompt v2 is detectable via reference-free drift within minutes at demo traffic rates** | Calibrate baseline window + CUSUM params against scripted degradation; measure detection latency & false-positive rate over ≥1 h clean run | Tune poison strength honestly (disclosed); widen detection window; last resort: reference-set scoring for the demo path, disclosed as such |

S4 is this project's spanLedger-S1: the only unknown that can force redesign. It runs first and gets the most engineering attention. A clean-run false positive is worse than slow detection (never-over-report).

---

## 8. Demo (run-of-show lives in demo/README.md)

Two beats, one pipeline: **(1) The hook — cost:** scripted agent loop; dollars/min spiral on the Vitals dashboard; alert fires at threshold; *"$47K incidents end here."* **(2) The payoff — quality:** deploy v2 (poisoned prompt); infra green, tokens normal; quality drift line bends, CUSUM onset marker appears, Release Compare splits v1/v2, alert pages; *"Anthropic shipped this exact failure in April and found out from user complaints. Cost to detect: $0.00."* Close on the conventions doc: *"and we wrote down the standard so everyone can emit this."* Every number reproducible by a judge running `demo/scenarios/` themselves.

---

## 9. Engineering Standards

Trunk-based; short-lived branches; PR + owner review across module boundaries; CI green to merge (ruff + pytest; spanIQ's suite stays green — proof the core is untouched). Conventional single-line commits. Unit tests exhaustive on: cost math, baseline/warming/CUSUM behavior, semconv mapper. vitals emits its own health metrics from day one. Definition of done: code + tests + docs + demoable + owner-reviewed.

---

## 10. Risks & Standing Answers

1. **"Your quality score isn't ground truth."** Correct — and we say it first (docs/honesty.md, demo script): Vitals measures *change* against a healthy baseline, which is exactly the signal behind every silent-regression incident cited in §0. Judges tier = escalation, not monitoring; spanIQ's published benchmark (F1 0.879 vs judges at $0, and judges collapsing to 0.667 on summarization) is the evidence base.
2. **S4 sensitivity risk** — the demo hinges on detection-within-minutes; that's why it's the first spike with a false-positive budget of zero on clean runs.
3. **"Isn't this Langfuse?"** — No: they added a sixth tool to your stack, offline and sampled. Vitals makes the APM you already run quality-aware, on 100% of traffic, at $0, and proposes the missing OTel convention. One pane, one pager.
4. **spanIQ throughput ceiling (~500 spans/s)** — documented honestly; far above demo load; V2 roadmap item.
5. **Rules optics** — spanIQ predates the event (allowed, disclosed); the Vitals layer is the submission and is 100% in-event work with dated commits.

---

## 11. For the implementation session (read first)

1. This file is the source of truth; §3 D3 schemas freeze on Day 1 — deviations go to `DECISIONS.md` with one-line rationale.
2. Build order is fixed: M0 spikes → M1 cost end-to-end → M2 quality → M3 release compare. Never start M(n+1) with M(n) red.
3. Repo root: `C:\Users\himan\OneDrive\Desktop\Vitals\` — `git init`, scaffold per §4, first commit = scaffold + this plan. spanIQ comes in from github.com/furyfist/spanIQ (vendor or submodule — vendor preferred for demo reproducibility).
4. Prereqs: Docker Desktop; SigNoz (self-hosted compose for dev; Cloud trial for recording); Groq API key (free); `SIGNOZ_API_KEY` if any query-side features are added later (none in V1 — Vitals only *writes* to SigNoz).
