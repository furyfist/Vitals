# Vitals — AI & Agent Observability Research (July 2026)

Research to validate, prioritize, and refine Vitals against the SigNoz ecosystem.
Every number below is attributed. Sources are graded:

- **[A]** peer-reviewed / arXiv paper with published methodology
- **[B]** vendor or practitioner post with a specific, checkable deployment behind it
- **[C]** vendor marketing or aggregator claim — directionally useful, not verified

Treat [C] numbers as hypotheses to re-measure, not as evidence.

---

## 1. Executive Summary

**The core finding: SigNoz has excellent GenAI *ingest* coverage and, as of 2026, a
strong agentic *consumption* layer (MCP + Noz). It has almost nothing in between —
no derived signals. Vitals sits exactly in that gap.**

Five takeaways:

1. **Coverage is not the gap; derivation is.** SigNoz's LLM observability docs list
   50+ GenAI integrations (OpenAI, Anthropic, Gemini, Groq, LangChain, LlamaIndex,
   AutoGen, CrewAI, DSPy, Pydantic AI, Claude Agent SDK, Bedrock, n8n Cloud,
   Firecrawl) and a Traceloop/OpenLLMetry path. But the stated value is
   "latency, errors, and usage trends" — raw span attributes rendered as
   dashboards. Cost is a *query you write*; quality is *not a signal at all*.
   Notably, the general integrations list page has no AI category at all — GenAI
   lives in a separate docs tree, which is itself a discoverability signal.

2. **Cost failures are real, large, and slow to detect.** The best-documented
   public incident: four LangChain agents with no step cap recursed for **11 days
   and produced a $47,000 invoice**, with dashboards green the entire time [B].
   The detection heuristic practitioners converge on — **a session costing >50×
   the median is a runaway loop** [B] — is a *velocity* statistic, not a
   cumulative one. This is precisely `vitals.cost.velocity`. Vitals' core cost
   thesis is validated by the single most-cited agent cost postmortem in the
   field.

3. **Quality failures are silent by construction.** The MAST study coded **150
   multi-agent execution traces across 5 domains** and found failures split
   41.8% specification/design, 36.9% inter-agent misalignment, 21.3% verification
   [A]; **79% of failures trace to bad specs or broken coordination**, not model
   errors [A]. Best open-source multi-agent correctness measured **as low as 25%**
   [A]. None of these produce an error span. A traces/metrics/logs backend
   structurally cannot see them.

4. **Evaluation economics are the wedge.** LLM-as-judge runs **$0.01–0.10 per
   assessment** [C] and forces sampling; at 1M evals/month the spread between a
   small and a large judge is **$101 vs $7,896** [C]. Practitioners state the
   acceptable production overhead budget explicitly: **76–162 ms is fine, a
   multi-second GPT-4 call per output is not** [C]. Vitals' deterministic,
   reference-free scoring at ~ms and $0/trace is the only approach that runs on
   **100% of traffic** — which is the only way to compute a *distribution* and
   therefore the only way to detect drift at all. Sampling breaks PSI.

5. **The strongest validated signal from the field is the joint condition.**
   Drift-detection practice converges on: *alert on input drift **AND** an eval
   drop; drift without eval impact is a false alarm* [C]. Vitals already computes
   both halves in one process. Shipping the conjunction as a first-class alert is
   probably the single highest-leverage thing in this document.

**Differentiation in one line:** SigNoz stores AI traces and lets an agent read
them. Vitals turns those traces into two alertable signals — *cost velocity* and
*quality drift dimensioned by release* — that nothing in the OTel-native stack
emits today.

**Biggest risk to the thesis:** SigNoz's Noz teammate can already "create
dashboards and alerts" and investigate agentically. If Noz starts deriving cost
and quality signals natively, Vitals' surface shrinks to the statistical core.
The defensible moat is the *math + the semantic convention*, not the dashboards.

---

## 2. Real Pain Points with Empirical Evidence

### 2.1 AI Agents (LangChain/LangGraph, AutoGen, Claude SDK, Temporal)

| Finding | Number | Source |
|---|---|---|
| Uncapped agent recursion, undetected | 11 days, $47,000 | [B] postmortem |
| Runaway-loop detection heuristic | session cost > 50× median | [B] |
| Multi-agent failures from spec/coordination, not model | 79% | [A] MAST |
| MAST taxonomy | 14 modes / 3 categories: 41.8% spec, 36.9% misalignment, 21.3% verification | [A] |
| ChatDev-class MAS correctness | as low as 25% | [A] |
| Traces analyzed to derive the taxonomy | 150 across 5 domains | [A] |

The structural problem is stated cleanly in the practitioner literature: *a bad
decision at step two only surfaces as a user-visible failure ten spans later*
[C]. Backward causal tracing (AgentTrace) and intervention-replay (DoVer) are
active research responses [A] — meaning root-cause attribution across agent
steps is an **open problem**, not a solved product feature. Vitals should not
promise attribution it cannot deliver; V1's honest "onset, not cause" framing is
correct and should stay.

**Implication for Vitals:** the failure mass is in *coordination*, which is
visible as span-graph shape (fan-out, depth, repeat-tool-call velocity), not as
response text. Vitals scores *responses*. There is a whole second signal family —
trajectory shape — that Vitals currently does not touch.

### 2.2 Self-Hosted Inference (vLLM, Ollama, LiteLLM)

| Finding | Number | Source |
|---|---|---|
| p95 TTFT @ 100 concurrent, TensorRT-LLM vs vLLM | 1,280 ms vs 1,450 ms | [C] |
| Llama-3.1-8B avg TTFT (vLLM 0.21.0) | 162.67 ms (min 93.92 / max 232.43) | [C] |
| Idle VRAM, 70B FP8 on 80 GB | vLLM 71 GB, TensorRT-LLM 74 GB | [C] |
| Peak throughput H100 FP8 | >10,000 output tok/s | [C] |
| KV-cache reduction effect on TTFT | −50% to −62% | [A] arXiv |
| Break-even utilization, 7B | ~50% GPU utilization | [C] |
| Break-even utilization, 13B | ~10% GPU utilization | [C] |
| GPU at 10% load | 10× cost inflation per token | [C] |
| Real client: self-host vs API | $10,400/mo vs $1,870/mo → **5.6× worse** | [C] |
| Self-host break-even volume | ~11B tokens/month | [C] |
| Quantization + batching + spec-decode | up to 16× effective cost reduction | [C] |

**The critical insight for Vitals:** on self-hosted inference, *token price is
not the cost function*. Cost is `GPU-hours / tokens-served`, and it is dominated
by **utilization**, which is bursty (high in business hours, near-zero
overnight). A price-table-per-1K-tokens model — which is what Vitals V1 has —
computes a **fictional** number for vLLM/Ollama users. The variance is not small:
a 10% utilization window makes the true unit cost 10× the nominal one.

This is a concrete, falsifiable gap in Vitals' cost engine and it affects a
large, growing segment.

### 2.3 Workflows (n8n)

n8n added native OTel in v2.22, emitting `workflow.execute` and `node.execute`
spans; SigNoz has a published n8n guide and an `n8n Cloud` integration. The
gap the n8n community names directly: *"AI cost is invisible — users have no idea
which workflows are burning through their OpenAI/Anthropic budget until the bill
arrives"* [B], and community members have built standalone tools for
**per-workflow cost + silent-failure alerts** [B] — i.e. the demand is proven by
people building it themselves.

Second n8n-specific failure mode: **silent stoppage** — a scheduled workflow
stops running with no error and no alert [B]. This is a *dead-man* problem, and
it generalizes to agents: absence-of-spans is a signal, and neither SigNoz nor
Vitals emits it today.

### 2.4 SRE / Self-Healing Agentic Setups (SigNoz MCP + Noz)

The Alien Intelligence deployment is the best empirical data point in the SigNoz
ecosystem [B]:

- Architecture: SigNoz alert → webhook → channel server → long-running Claude
  agent; Claude Opus orchestrator (read-only) + Sonnet/Haiku investigation
  sub-agents with fresh context per alert; SigNoz MCP for traces/logs/metrics;
  read-only k8s RBAC, GitLab, Slack; SQLite operational memory; PM2 restart 4am.
- **First month: 0 false positives, 1 false negative.**
- **~10 minutes saved per transient alert triage.**
- Cost driver for the migration: a **$2,000+/month Datadog quote**.
- 8+ alert types covered (error rate, pod crashes, ArgoCD sync, PVC, latency, DB
  errors, Falco, Trivy).
- **Two stated limitations that matter enormously to Vitals:**
  - **Context-window degradation observed around 50–60% capacity.**
  - **"Dashboards rarely opened after initial setup — now primarily used for
    compliance/ISO screenshots."**

That last line is the most important sentence in this entire research pass. In an
agent-native SRE setup, **the consumer of Vitals' output is an LLM agent, not a
human looking at a chart.** And that consumer degrades past ~50% context. A
dashboard-first product loses; a *dense, low-token, machine-readable signal*
wins.

### 2.5 E2E Debugging Across Long-Running Sessions

Temporal-backed agents can sleep for hours or days and resume with full state;
event history is the audit trail, with OTel spans per Activity. The structural
mismatch is stated well in that literature: *"a trace can explain what happened;
a durable journal must decide what may be replayed"* [C]. Practically: a
multi-day agent session has **no single trace** — trace context does not survive
the sleep, so the session is N disconnected traces sharing a business-level ID.

Vitals' baselines are keyed on service/model/version. For long-running sessions
the meaningful unit is the **session**, and neither SigNoz's trace view nor
Vitals' current windows aggregate on it.

### 2.6 Telemetry Cost — the counter-pressure

The OTel GenAI WG recommends prompts/completions be captured as **span events,
not span attributes**, because backends struggle with large payloads; guidance
is to **cap content at 500–1000 characters** [C]. Attributes are always indexed
and always exported; events can be dropped at the Collector.

This cuts directly against Vitals: **if operators follow best practice and cap
content at 500–1000 chars, Vitals scores truncated text.** PSI over embeddings of
truncated completions is a different distribution than PSI over full ones —
stable only if truncation is *consistent*. If someone changes the cap, Vitals
fires a drift alert on a config change. This needs an explicit guard.

---

## 3. SigNoz Ecosystem Gaps & Opportunities

### What works well

- **Ingest breadth.** 50+ GenAI integrations; Traceloop/OpenLLMetry supported
  directly; SigNoz publishes guides for LangChain/LangGraph, LlamaIndex, LiteLLM,
  Vercel AI SDK, Pydantic AI. Vitals' dual-shape mapper (OTel semconv +
  Traceloop) is the right bet — both shapes are genuinely in the wild.
- **Storage.** ClickHouse columnar with ZSTD/Delta/LowCardinality is the right
  substrate for high-volume LLM spans — a real advantage over row-store APMs
  that "are not designed to store or query this kind of data efficiently" [C].
- **The agentic layer is ahead of the market.** MCP server + Noz + Agent Skills
  (`skills.md` in a repo) + Claude Code / Cursor / Codex / Gemini integration.
  Alerts→webhook→agent is a proven pattern with real numbers behind it.
- **Templates.** 80+ dashboard templates; a Langflow dashboard built on
  `gen_ai.*` from Traceloop, breaking down input/output/total tokens by
  `gen_ai.request.model`.

### What is genuinely missing for production AI

1. **No cost *rate*.** Token-count dashboards exist; token counts grouped by
   model are a *usage* chart. Nothing computes USD/min, nothing has a price
   table, nothing pages on burn rate. The $47K/11-day failure mode is not
   catchable with a token-count time series.
2. **No quality signal of any kind.** There is no `gen_ai.evaluation.*`.
   Verification failures are 21.3% of MAST-coded agent failures [A] and are
   entirely invisible to the current stack.
3. **No version-aware baseline.** SigNoz has deployment history; nothing joins
   "this release" to "this quality/cost distribution." "Did my prompt change make
   it worse?" is unanswerable today.
4. **No self-hosted inference cost model.** No vLLM/Ollama integration in the
   integrations list; no GPU-hours-per-token attribution. Given the 10×
   utilization sensitivity, this is a large hole.
5. **No absence-detection.** Silent stoppage (n8n, cron agents) needs dead-man
   alerting; not present.
6. **Semconv is pre-stable and moving.** As of v1.42.0 (12 June 2026) all
   `gen_ai.*` attributes/spans moved out of the core semconv repo into a
   dedicated GenAI conventions repo, still Development status [C]. Agent/framework
   spans are experimental but reported stable in practice through Q1 2026 [C].
   **Attribute churn is an operational risk for Vitals' mapper and a reason to
   version the mapper explicitly.**

### Where Vitals complements rather than competes

- Vitals emits *metrics and logs*, not a UI. It rides SigNoz's storage, query,
  alerting, and — critically — **Noz/MCP**. A `vitals.cost.velocity` gauge and a
  trace-linked eval log are things Noz can already read and reason over with zero
  Vitals-side integration work.
- The out-of-band emission path (D3/D4 — straight to SigNoz ingest, not through
  the monitored collector) is architecturally correct: Vitals' own failure cannot
  corrupt the customer's telemetry pipeline.
- The `gen_ai.evaluation.*` convention proposal is the highest-leverage
  non-code asset in the project. If it lands upstream, Vitals defines the schema
  the ecosystem uses.

---

## 4. High-Value Real-World Scenarios

### P1 — "Ana", AI platform engineer at a Series-B SaaS (LangGraph + Claude SDK)

Ships prompt changes weekly behind a canary at 5–10% traffic and monitors 24–48h
before ramping [C]. Her question: **"v2.3 went out 40 minutes ago — is cost per
session up and is quality down, versus v2.2, right now?"**
Today: she compares token-count charts by eye and has no quality axis at all.
With Vitals: the Release Compare dashboard answers it directly, because the
baseline key deliberately excludes `service.version`.
Win: canary decisions in minutes rather than the 24–48h soak; regressions caught
at 5% blast radius instead of 100%.

### P2 — "Diego", SRE running an agentic on-call loop (SigNoz MCP + Claude)

His measured baseline: 0 FP / 1 FN in month one, ~10 min saved per transient
alert, dashboards effectively unopened [B]. His question when paged:
**"Is this a cost anomaly, a quality regression, or infra?"** — asked *by an
agent*, in tokens, under a context budget that degrades past 50–60%.
With Vitals: a `vitals.*` gauge plus a trace-linked eval log answers the
cost-vs-quality fork in a handful of tokens instead of a screenshot.
Win: the classification step of triage becomes a metric lookup.

### P3 — "Priya", ops lead on 200 n8n workflows with LLM nodes

Her question: **"Which workflow burned the budget last night, and did anything
stop running?"** Community evidence says people build this by hand today [B].
With Vitals: cost velocity dimensioned by workflow/node + dead-man on
`node.execute` absence.
Win: attribution before the invoice; the runaway-retry-loop-on-a-heavy-node
failure mode [C] becomes a page, not a surprise.

### P4 — "Marcus", ML infra on self-hosted vLLM

His question: **"What did that request actually cost me?"** — which given the 10×
utilization sensitivity [C] is not answerable from token counts.
With Vitals (proposed): a GPU-amortized price mode.
Win: real unit economics, and a defensible answer to "should we still self-host"
— the case where a team paid **5.6×** for the privilege [C] is exactly the
mistake this signal prevents.

---

## 5. Actionable Recommendations

### Tier 1 — highest evidence-to-effort ratio

**R1. Ship the joint drift alert (drift AND eval-drop) as the flagship rule.**
Field practice is explicit that unilateral drift alerts are noise: *"drift
without eval impact is a false alarm"* [C]. Vitals is unusual in having both
halves in one process. This is a one-rule change with the best supporting
evidence in this document.
*Effort: S. Risk: low.*

**R2. Make Vitals agent-legible, not dashboard-legible.**
The Alien Intelligence report says dashboards go unopened and the agent degrades
past 50–60% context [B]. Ship (a) a `skills.md` for SigNoz Agent Skills that
teaches an agent how to interpret `vitals.*`, and (b) a token-budgeted
`vitals explain --since 1h` summary. Optimize the eval-log schema for tokens
consumed, not pixels.
*Effort: S–M. This is the strategic bet — it aligns Vitals with where SigNoz is
actually going.*

**R3. Ship velocity ratio-to-median, not just absolute USD/min.**
The empirically-used heuristic is **>50× median session cost** [B]. Absolute
thresholds require every operator to guess a number; a ratio ships with a working
default. Emit `vitals.cost.session_ratio` and alert at 50×.
*Effort: S. Directly encodes the $47K failure mode.*

**R4. Guard against truncation-induced false drift.**
Given the 500–1000 char capping guidance [C]: record observed completion-length
distribution in the baseline; if mean length shifts >X% while embedding drift
fires, label the alert `suspected_truncation_change` instead of quality drift.
*Effort: S. Prevents the most likely embarrassing false positive.*

### Tier 2 — closes a named ecosystem gap

**R5. Dead-man / absence detection.** Alert on expected-but-missing `gen_ai` or
`node.execute` spans per workflow/service. Named explicitly as an unmet need in
the n8n community [B]; nothing in SigNoz or Vitals covers it. *Effort: M.*

**R6. Self-hosted GPU cost mode.** Extend the price table with a
`gpu_hourly_rate` + utilization-derived cost model for vLLM/Ollama/LiteLLM, so
cost = amortized GPU-hours/token rather than a fictional per-1K price. Pair with
TTFT/ITL percentiles from vLLM's own metrics endpoint. Justified by the 10×
utilization sensitivity and the 5.6× real-world misjudgment [C]. *Effort: M–L.
Also the clearest "no one else does this" differentiator.*

**R7. Session-scoped aggregation.** Add a configurable session-key attribute so
cost and quality aggregate over a multi-day Temporal/durable agent session that
spans N disconnected traces. *Effort: M.*

**R8. Trajectory-shape signals.** 79% of multi-agent failures are spec/
coordination [A] and are invisible in response text. Cheap span-graph statistics
— tool-call repeat rate, fan-out, step depth vs baseline — catch loops before
cost does. *Effort: M. Expands Vitals from "response quality" to "agent
behavior", which is where the failure mass actually is.*

### Tier 3 — durable moat

**R9. Upstream `gen_ai.evaluation.*` to the OTel GenAI SIG.** The conventions
moved to a dedicated repo with its own cadence as of v1.42.0 [C] — the window
for new proposals is unusually open right now. *Effort: L, long horizon, highest
strategic payoff.*

**R10. Version the semconv mapper explicitly.** GenAI conventions are pre-stable
and just moved repos. Ship `mapper_version` in Vitals' self-health metrics so
attribute churn shows up as a drop in mapped-span rate rather than as silent
quality degradation. *Effort: S.*

### Barriers and mitigations

| Barrier | Evidence | Mitigation |
|---|---|---|
| Instrumentation effort | teams already run Traceloop/OTel | collector fan-out only — zero app changes. Keep this as the headline. |
| Scoring overhead | acceptable budget is 76–162 ms [C] | deterministic scoring is ~ms; publish a measured p99 per span, don't claim it |
| Throughput ceiling | spanIQ ~500 spans/s (STATUS.md) | async scoring queue; degrade to cost-only mode under load and *say so* via a health metric |
| Content truncation | 500–1000 char cap guidance [C] | R4 |
| Semconv churn | pre-stable, repo moved June 2026 [C] | R10 |
| CUSUM calibration | STATUS.md: S4 defaults, uncalibrated on real traffic | ship a `vitals calibrate` mode; do **not** publish onset-latency claims until measured |
| Noz absorbs the category | Noz already creates dashboards/alerts | moat is the statistics + convention, not the UI (R2, R9) |

---

## 6. Prioritized V2 Backlog

| # | Item | Why (evidence) | Effort |
|---|---|---|---|
| 1 | Joint drift+eval-drop alert rule | "drift without eval impact is a false alarm" [C] | S |
| 2 | `skills.md` + token-budgeted `vitals explain` | dashboards unopened; agent degrades >50% ctx [B] | S–M |
| 3 | `vitals.cost.session_ratio`, alert at 50× median | the operative runaway heuristic [B] | S |
| 4 | Truncation guard on drift | 500–1000 char capping guidance [C] | S |
| 5 | `mapper_version` + mapped-span-rate health metric | semconv pre-stable, moved repos June 2026 [C] | S |
| 6 | Persistent baselines (spanIQ SQLite BaselineStore, D8) | in-memory baselines lose state on restart | S–M |
| 7 | Live SigNoz dashboard/alert import round-trip | never verified against a running UI (STATUS.md) | S |
| 8 | Dead-man / absence alerting | named unmet need in n8n community [B] | M |
| 9 | Async scoring queue + load-shed to cost-only | ~500 spans/s ceiling | M |
| 10 | Session-scoped aggregation (Temporal/durable agents) | multi-day sessions ≠ one trace [C] | M |
| 11 | Trajectory-shape signals (loop/fan-out/depth) | 79% of failures are coordination, not text [A] | M |
| 12 | Self-hosted GPU cost mode + vLLM TTFT/ITL panels | 10× utilization sensitivity; 5.6× real misjudgment [C] | M–L |
| 13 | CUSUM recalibration harness on real traffic | S4 defaults unvalidated (STATUS.md) | M |
| 14 | Embedding-distribution drift (PSI/KS) wired online | spanIQ primitives exist, not connected | M |
| 15 | Per-tenant/user impact dimensions | "which customers are affected" | M |
| 16 | Upstream `gen_ai.evaluation.*` to OTel GenAI SIG | window open post-repo-split [C] | L |

**Sequencing:** items 1–7 are all Small and each closes a named gap — that is a
coherent V2.0 release. Items 8–12 are V2.1 and are where the differentiation
compounds. Item 16 runs in parallel on its own clock.

**What to cut / defer:** PELT changepoint attribution — the research literature
treats agent root-cause attribution as an open problem (AgentTrace, DoVer, FALAT
are all 2026 arXiv preprints [A]). Promising onset *and* cause invites a claim
Vitals cannot defend. Keep the honest "onset, not cause" framing.

---

## Sources

- [SigNoz — Integrations list](https://signoz.io/docs/integrations/integrations-list/)
- [SigNoz — LLM Observability docs](https://signoz.io/docs/llm-observability/)
- [SigNoz — Traceloop integration](https://signoz.io/docs/traceloop/)
- [SigNoz — Noz & AI tools overview](https://signoz.io/docs/ai/overview/)
- [SigNoz — Agent-native observability](https://signoz.io/agent-native-observability/)
- [SigNoz — How Alien Intelligence built an AI SRE workflow](https://signoz.io/blog/alien-intelligence-ai-sre-workflow-signoz/)
- [SigNoz — n8n monitoring with OpenTelemetry](https://signoz.io/blog/n8n-monitoring-with-opentelemetry/)
- [SigNoz — Langflow dashboard template](https://signoz.io/docs/dashboards/dashboard-templates/langflow-dashboard/)
- [SigNoz — LLM observability & OpenTelemetry](https://signoz.io/blog/llm-observability-opentelemetry/)
- [Why Do Multi-Agent LLM Systems Fail? (MAST)](https://arxiv.org/html/2503.13657v1)
- [AgentTrace: causal graph tracing for RCA](https://arxiv.org/pdf/2603.14688)
- [DoVer: intervention-driven auto debugging](https://arxiv.org/pdf/2512.06749)
- [FALAT: tracing failures in agent trajectories](https://arxiv.org/pdf/2606.00765)
- [Nautilus Compass: black-box persona drift detection](https://arxiv.org/pdf/2605.09863)
- [The Agent That Spent $47K on Itself — postmortem](https://dev.to/gabrielanhaia/the-agent-that-spent-47k-on-itself-an-autonomous-loop-postmortem-3313)
- [OpenTelemetry — Inside the LLM Call: GenAI observability](https://opentelemetry.io/blog/2026/genai-observability/)
- [OpenTelemetry — Gen AI attribute registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)
- [Traceloop — GenAI semantic conventions](https://www.traceloop.com/docs/openllmetry/contributing/semantic-conventions)
- [OpenLLMetry](https://github.com/traceloop/openllmetry)
- [n8n docs — trace executions with OpenTelemetry](https://docs.n8n.io/deploy/host-n8n/keep-n8n-running/trace-executions-with-opentelemetry)
- [n8n community — per-workflow AI cost + silent failure alerts](https://community.n8n.io/t/built-a-free-tool-to-track-ai-api-cost-per-n8n-workflow-silent-failure-alerts-looking-for-beta-feedback/301296)
- [vLLM — Metrics design](https://docs.vllm.ai/en/stable/design/metrics/)
- [vLLM vs TensorRT-LLM vs SGLang H100 benchmarks](https://www.spheron.network/blog/vllm-vs-tensorrt-llm-vs-sglang-benchmarks/)
- [Benchmarking TTFT, ITL and throughput](https://dev.to/wheynelau/how-to-benchmark-llm-inference-performance-ttft-itl-and-throughput-metrics-416p)
- [Inference unit economics: true cost per million tokens](https://introl.com/blog/inference-unit-economics-true-cost-per-million-tokens-guide)
- [Self-hosted LLM vs API break-even analysis](https://www.braincuber.com/blog/self-hosted-llms-vs-api-based-llms-cost-performance-analysis)
- [Langfuse — LLM-as-a-judge](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)
- [Evidently — 5 methods to detect drift in ML embeddings](https://www.evidentlyai.com/blog/embedding-drift-detection)
- [AWS — detecting drift in production GenAI applications](https://docs.aws.amazon.com/prescriptive-guidance/latest/gen-ai-lifecycle-operational-excellence/prod-monitoring-drift.html)
- [(Why) Is My Prompt Getting Worse?](https://arxiv.org/pdf/2311.11123)
- [Temporal — durable AI agents](https://temporal.io/blog/build-durable-ai-agents-pydantic-ai-and-temporal)
