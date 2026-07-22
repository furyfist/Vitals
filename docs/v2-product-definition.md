# Vitals V2 — Product Definition

Written PM-first. Scope decisions here override the raw backlog in
[docs/research/ai-agent-observability.md](research/ai-agent-observability.md).

---

## 0. The product thesis

**Every AI change is a deploy with no test suite. Vitals grades the deploy in
production, on cost and quality jointly, within minutes.**

V1 emits *signals*. Signals require a human to go look, correlate two charts, and
form an opinion. The research is blunt about how that ends: in the one documented
agent-native SRE deployment, **"dashboards rarely opened after initial setup —
now primarily used for compliance/ISO screenshots."**

**V2 emits a *verdict*.** That is the entire product jump. One object, one state,
one place it lands, readable by a human in three seconds or by an agent in ~200
tokens.

Everything in V2 exists to make one sentence true and trustworthy:

> *"v2.3 is a cost regression: +34% USD/session, quality flat. Here are 5 traces."*

If a proposed feature does not make that sentence more available, more accurate,
or more trusted, it is not in V2.

---

## 1. Why this thesis and not another

Three candidate products were on the table. Only one is coherent at this size.

| Candidate | Why not |
|---|---|
| **"Cost observability for AI"** | Real pain ($47K/11 days), but it is a feature, not a product — and it is the feature most likely to be absorbed by SigNoz's query builder plus a price table. Defensible for about two quarters. |
| **"LLM evaluation platform"** | Crowded (Langfuse, Braintrust, Traceloop, Confident). Buyers there want offline eval suites and dataset management — a different product with a different data model. Vitals would be the worst option in a category it doesn't belong to. |
| **"The release verdict for AI systems"** ✅ | Uses the one asset nobody else in the OTel-native stack has: version-aware baselines computed on 100% of traffic, out of band, deterministically. Answers the question teams actually ask on deploy day. Absorbs cost *and* quality into a single object instead of shipping two disconnected capabilities. |

The strategic reason it wins: **it is the only framing where cost and quality
must live in the same product.** Ship them separately and you have two mediocre
features. Ship them as one verdict and you have the answer to "should I roll
back," which neither an eval vendor nor an APM can produce.

It also matches the strongest empirical finding in the research: alert on the
**joint** condition. Drift without cost/eval impact is a false alarm. The verdict
*is* the joint condition, productized.

---

## 2. The core object: the Verdict

One noun. Everything else in the product is a way of producing, storing,
delivering, or trusting it.

```
Verdict {
  service, version, baseline_version
  state:        WARMING | PASS | COST_REGRESSION | QUALITY_REGRESSION
                | REGRESSED | INCONCLUSIVE
  cost_delta_pct        # vs baseline version, per-session normalized
  quality_delta         # drift score delta vs baseline version
  window                # opened_at, closed_at, n_spans
  confidence            # sample-size + guard status
  exemplar_trace_ids[]  # 3-5 traces, worst-first
  reason                # one sentence, written for a human AND an agent
}
```

**`INCONCLUSIVE` is the most important state in the product.** Every eval vendor
always returns a number. Vitals is the one that says "I don't know yet, and
here's why" — sample too small, content truncation changed, semconv mapping
degraded, baseline still warming. This is the credibility feature. A verdict
system that is occasionally wrong is worthless; a verdict system that is
sometimes silent is trusted.

---

## 3. Core workflow

Five steps. No step requires a human to open a chart.

1. **Detect** — a new `service.version` appears in the span stream.
2. **Window** — Vitals auto-opens a comparison window against the last version
   that held a `PASS` verdict (not merely the previous version — never baseline
   against a known-bad release).
3. **Grade** — cost and quality are scored on 100% of traffic in that window,
   against the frozen baseline. Guards run in parallel.
4. **Verdict** — at the earlier of *n* spans or *t* minutes, emit the verdict as
   a metric, an eval log, and (if not `PASS`) an alert.
5. **Deliver** — the alert routes to Slack for a human, or to a webhook →
   agent loop; either consumer can pull the full verdict and its exemplar traces
   through SigNoz.

**Time budget: verdict within 5 minutes of a deploy, or `INCONCLUSIVE`.**
That number is the product. Canary practice today is a 24–48h soak; if Vitals
turns that into minutes at 5% traffic, the value proposition is self-evident and
needs no chart to explain.

---

## 4. User journey

**Persona: Ana, AI platform engineer, ships prompt changes weekly behind a 5–10%
canary.** Today she ramps on vibes after a 24–48h soak, because she has a token
chart and no quality axis at all.

| Stage | What happens | Time |
|---|---|---|
| **Install** | Adds a second exporter to her existing collector config. No app changes, no SDK. | 10 min |
| **Warm** | Vitals ingests current traffic, establishes a baseline on the live version, emits `WARMING`. She sees Vitals is alive via self-health metrics. | ~1 hr |
| **First value** | v2.3 canary goes to 5%. Within 5 min: `COST_REGRESSION — +34% USD/session vs v2.2, quality flat (Δ 0.01), n=1,240, 5 traces`. | day 1 |
| **Decide** | She opens two of the five exemplar traces, sees a retry loop on the summarizer node, holds the ramp. Blast radius: 5%, not 100%. | 5 min |
| **Trust** | Over two weeks she sees `PASS` on eight releases and `INCONCLUSIVE` twice on low-traffic evenings. Vitals never cried wolf. She starts gating the ramp on the verdict. | 2 wks |
| **Delegate** | Her team wires the verdict alert into their SigNoz-MCP agent loop. The agent reads the verdict, correlates the deploy, and posts a rollback recommendation to Slack. | month 2 |

The last row is the strategic endgame: **Vitals becomes the AI-specific sense
organ of an agentic SRE loop that SigNoz already ships the nervous system for.**

---

## 5. Primary demo scenario

One scenario. Two beats. Under four minutes. The existing demo assets (`ragapp`
with v1-good / v2-poisoned prompts, `runaway_loop.py`, `deploy_v2.sh`) already
support it — V2 changes the *ending*, not the setup.

**Beat 1 — the cost regression (60s).** Run `runaway_loop.py`. A retry loop
starts. Cumulative cost is still trivially small — an invoice-based or
total-spend-based system sees nothing. Vitals fires on **rate**: session cost
crosses 50× median. Verdict lands. *Line: "the bill is still $3. You already
know."*

**Beat 2 — the silent quality regression (120s).** Run `deploy_v2.sh`. The
poisoned prompt ships. **Every span is HTTP 200. Latency is flat. Error rate is
zero. SigNoz's own dashboards are green — show them, side by side.** Then the
Vitals verdict: `QUALITY_REGRESSION — v2 vs v1, drift onset 90s after deploy,
cost flat`. Click through to an exemplar trace and read the bad answer aloud.

**The close (30s).** Ask Claude, via SigNoz MCP: *"Should we roll back v2?"* The
agent reads the verdict record and answers with the version, the delta, and the
trace links — no dashboard opened, no query written.

That close is the whole product in one interaction, and it is the beat that
differentiates Vitals from every eval tool and every APM simultaneously.

---

## 6. V2 feature set

Seven features. Each maps to a clause of the thesis.

| # | Feature | Thesis clause it serves |
|---|---|---|
| **F1** | **Release detection + auto-windowing.** New `service.version` opens a comparison window against the last `PASS` version. | *"grades the deploy"* — without this the user still has to go look, which is V1. |
| **F2** | **The Verdict engine.** One state machine combining cost delta and quality delta into a single state. Includes the joint-condition rule and the 50×-median session-cost trigger as a cost input. | *"on cost and quality jointly"* — this is the product. |
| **F3** | **Verdict delivery, three surfaces.** `vitals.release.verdict` metric (state as a numeric enum, deltas as attributes), a structured eval log with trace exemplars, and one alert rule. | *"within minutes"* — a verdict nobody receives isn't one. |
| **F4** | **Agent-legible output.** A `skills.md` for SigNoz Agent Skills teaching an agent to read `vitals.*`, plus `vitals explain --release <v>` returning a ~200-token summary. | The verdict's primary consumer is an agent with a context budget that degrades past 50–60%. Dashboards go unopened. |
| **F5** | **Trust guards → `INCONCLUSIVE`.** Sample-size floor, completion-length/truncation guard, `mapper_version` + mapped-span-rate health, warming state. | *"trustworthy"* — this is what buys the right to be believed on beat 2. |
| **F6** | **Persistent baselines** (spanIQ SQLite `BaselineStore`). | A verdict that evaporates on restart is not a verdict. Pure enablement of F1/F2. |
| **F7** | **One dashboard: the Release Report Card.** Verdict timeline, cost delta, quality delta, exemplar traces — per version. Replaces V1's three dashboards as the primary surface; the others become drill-downs. | *"in three seconds"* — and it must round-trip against a live SigNoz UI, which V1's dashboard JSON never has. |

**Nothing else ships in V2.**

Note what F2 absorbs: V1's separate cost-velocity and quality-drift alert rules
stop being top-level products and become *inputs*. That is a deliberate
reduction in surface area — two alerts a user must tune become one verdict they
must trust.

---

## 7. Deliberate exclusions

Everything below is *good* and most of it is in the research backlog. It is
excluded because it does not serve the thesis at this size.

| Excluded | Why it's out of V2 |
|---|---|
| **Self-hosted GPU cost mode (vLLM/Ollama)** | Different cost function (GPU-hours ÷ tokens, utilization-dominated), different buyer (ML infra, not app team), and it forks the cost engine. The strongest *differentiator* in the backlog and still wrong for V2: it would consume the release cycle and produce a second product. **V2.1, as a headline.** |
| **Trajectory-shape signals (loop/fan-out/depth)** | Different data model — span graph, not response text. 79% of agent failures live here, so this is the real V3 ("agent behavior vitals"), but it cannot share the verdict object without redefining it mid-flight. |
| **Dead-man / absence alerting** | Trigger semantics are inverted (absence, not deviation), and it is a generic SigNoz capability, not a Vitals one. Recommending an existing SigNoz alert costs nothing and keeps the product honest about its boundaries. |
| **Session-scoped aggregation (Temporal/durable agents)** | Real gap, but there is no verdict story for a multi-day session yet — what does "release verdict" even mean when one session spans four deploys? Needs product thinking, not just code. |
| **Per-tenant / per-user impact dimensions** | Pure cardinality expansion. Valuable once the verdict is trusted; noise before it. |
| **PELT changepoint attribution** | Agent root-cause attribution is an open research problem (AgentTrace, DoVer, FALAT are all 2026 preprints). Shipping cause-attribution invites a claim that cannot be defended, and one confidently-wrong root cause destroys more trust than ten `INCONCLUSIVE`s. **The honest "onset, not cause" framing is a feature — keep it.** |
| **Enforcement / budget circuit breakers** | Observe-only is a positioning decision, not a limitation. The moment Vitals can kill traffic it needs a completely different reliability, security, and support story. |
| **Multi-backend support (Datadog, Grafana)** | Being *the* SigNoz-native AI layer beats being a mediocre cross-platform one. Breadth after depth. |
| **Offline eval suites, datasets, prompt management** | Someone else's category. Entering it makes Vitals the worst product in a crowded market instead of the only product in an empty one. |
| **PyPI publish** | Distribution, not product. Ships when the verdict is trusted, not before. |
| **`gen_ai.evaluation.*` upstreaming** | Not excluded — **de-scoped from the release train.** It runs in parallel on its own clock. It is the long-term moat and must not gate or be gated by V2. |

---

## 8. What "done" means

V2 is complete when a stranger can, unassisted:

1. Add one exporter to a collector config,
2. Deploy a prompt change,
3. Receive a correct verdict within five minutes,
4. Ask their coding agent "should I roll back?" and get a grounded answer.

Success metrics to instrument from day one:

| Metric | Target | Why |
|---|---|---|
| Time to first verdict after install | < 90 min | Adoption cliff. |
| Deploy → verdict latency | p50 < 5 min | The core promise. |
| False-positive rate on clean traffic | 0 over 7 days | Beat-2 credibility. Non-negotiable. |
| Share of verdicts `INCONCLUSIVE` | 5–15% | Below 5% = guards aren't working. Above 15% = product feels useless. |
| Verdicts read by an agent vs a human | rising | Confirms or kills the F4 bet. |

**Known measurement debt to clear before publishing any claim:** CUSUM parameters
still ship with synthetic-spike defaults and have never been calibrated against
real traffic. Do not publish a drift-onset-latency number until that calibration
exists. The p50-5-min target above is a *design* target and must be labeled as
such until measured.

---

## 9. Positioning

**One line:** *Vitals tells you whether your last AI release was safe — cost and
quality — before your users or your invoice do.*

**Against SigNoz:** not a competitor, a signal source. SigNoz stores AI traces
and lets Noz read them; Vitals gives Noz something worth reading.

**Against Langfuse / Braintrust / Traceloop:** they answer *"is this output
good?"* on sampled traffic, offline, with an LLM judge. Vitals answers *"did this
release change?"* on 100% of traffic, online, deterministically, at $0/trace.
Different question, complementary tool, no head-to-head.

**Against Datadog LLM Observability:** OTel-native, self-hostable, no per-host
pricing — in a segment where a $2,000+/month quote is a documented reason teams
switch.

**Primary risk:** SigNoz's Noz teammate can already create dashboards and alerts
agentically, and could derive cost/quality itself. The moat is not the UI — it is
the version-aware statistics, the `INCONCLUSIVE` discipline, and the semantic
convention. F4 (agent-legible output) is therefore not a nice-to-have; it is the
feature that makes Vitals *worth adopting rather than reimplementing*.
