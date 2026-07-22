# Vitals V2 — Product Requirements Document

Status: ready for engineering handoff. No implementation detail by design.
Supersedes [docs/v2-product-definition.md](v2-product-definition.md).
Rationale for every change is in [docs/v2-critique.md](v2-critique.md).

---

## 1. Product vision

**Every team running AI in production is flying on instruments that cannot see
the thing that breaks.** Latency, error rate, and throughput all report perfect
health while the model quietly gets worse or quietly gets expensive. The bill
arrives in thirty days; the user complaint arrives sooner.

Vitals is the instrument that reads the two dimensions no OTel-native platform
reports: **what your AI costs right now, and whether it is behaving the way it
was.** It lives inside the observability platform teams already run, adds nothing
to the request path, and speaks to humans and to AI agents equally well.

Long term, `gen_ai.evaluation.*` becomes a standard OpenTelemetry convention and
Vitals is its reference implementation.

---

## 2. Target users

**Primary — the AI platform engineer.** Owns an LLM-backed product feature or
agent. Ships prompt and model changes weekly. Already runs SigNoz and an OTel
collector. Has offline evals that pass. Has no idea what happens after deploy.
*Buys because:* they have been burned by a silent regression and cannot prove
what caused it.

**Secondary — the SRE running an agentic on-call loop.** SigNoz MCP wired into a
Claude or Cursor agent. Dashboards are effectively unused; the agent is the
consumer. Context budget degrades past ~50–60%.
*Buys because:* their agent has no AI-specific signal to reason over.

**Tertiary — the automation/workflow owner** (n8n and similar). Dozens of
workflows with LLM nodes, no per-workflow cost attribution, and silent failures.
*Buys because:* they are currently building this themselves.

**Explicitly not the user:** the ML researcher wanting offline eval, dataset
curation, or prompt experimentation. That is Braintrust/Langfuse/Phoenix
territory and Vitals does not enter it.

---

## 3. User problem

Four true statements the user would recognize instantly:

1. **Their evals passed and production regressed anyway.** Offline suites do not
   see production traffic distribution.
2. **Nothing turns red.** A wrong answer is a successful HTTP request. Error
   rate, latency, and throughput are all normal during a total quality collapse.
3. **Cost is discovered, not monitored.** Runaway loops are found on the invoice.
   One documented case: four uncapped agents, 11 days, $47,000, dashboards green
   throughout.
4. **They cannot answer "was it us?"** When behavior changes, they cannot tell
   whether their release did it, the provider changed the model underneath them,
   or the traffic just shifted.

Point 4 is the emotional core and the one nobody serves.

---

## 4. Product thesis

> **Your evals passed. Production changed anyway.**
>
> Vitals watches 100% of your AI traffic and tells you when behavior or cost
> moves — which release caused it, or that nothing you shipped did.

Three commitments follow from this and constrain every decision below:

- **Change, not correctness.** Vitals never claims an answer is wrong. It claims
  the population moved, by how much, and when. This is defensible; "quality
  score" is not.
- **100% of traffic, or the math doesn't work.** Distributional detection is
  impossible on a sample. This is why scoring must be deterministic and free —
  it is a mathematical requirement, not a cost optimization.
- **Silence is a feature.** A system that says "I don't know" is trusted. A
  system that always produces a number is not.

---

## 5. Core workflow

**One object: the Verdict.** It is *about a comparison*, and the comparison has
one of three subjects:

| Subject | Compares | Serves |
|---|---|---|
| `release` | v2.3 vs the last `STEADY` version | the hero case — "did my deploy do this?" |
| `time` | this window vs the rolling baseline | works on install with zero deploys; catches provider-side drift |
| `cohort` | canary vs control, concurrently | best statistics — controls for traffic mix and time of day |

**Four states.** `WARMING` → `STEADY` | `CHANGED` | `INCONCLUSIVE`.
`CHANGED` carries independent flags for `cost` and `behavior`.
`INCONCLUSIVE` always carries a reason code.

There is deliberately no state named for quality or regression — Vitals detects
change and reports attribution, and the vocabulary must not exceed the evidence.

**The loop:**

1. **Watch** — score every `gen_ai` span for cost and output behavior against a
   frozen baseline. Always on, from install, no deploy required.
2. **Detect** — a change crosses the joint threshold: cost *and/or* behavior
   moved beyond normal observed variance.
3. **Attribute** — if a version boundary coincides with onset, the cause is that
   release. If not, the cause is `unattributed` — and saying so is a feature.
4. **Guard** — before emitting, check sample size, warming status, and whether
   the *input* distribution moved too. Fail to `INCONCLUSIVE` with a reason.
5. **Deliver** — the complete verdict goes into the notification payload. No
   click required to make the decision.

**Every verdict, in one sentence, always the same shape:**

> `CHANGED · behavior · v2.3 vs v2.2 · 4.2σ · onset 90s after deploy · cost flat · n=1,240 · 3 traces`

**Every delta is expressed against observed variance (σ), never as a raw
statistic.** "PSI 0.04" is meaningless to a human and dangerous to an agent.

---

## 6. MVP feature set

Six features. Each maps to a thesis commitment; nothing else ships.

**F1 — Always-on change detection.**
Continuous cost and behavior scoring against a rolling baseline from the moment
Vitals starts. Delivers value on install with zero deploys. *This is the feature
that makes the product work on day one and the reason vendor-side drift is
visible at all.*

**F2 — Release attribution.**
When a new `service.version` appears, open a comparison against the last
`STEADY` version and attribute onset to it if timing coincides. When it doesn't,
report `unattributed`. *Turns "something changed" into "you changed it" — the
hero use case.*

**F3 — The Verdict engine.**
One state machine over four states, combining cost and behavior into a single
joint judgment, with deltas normalized to observed variance. Absorbs V1's two
separate alert rules as inputs. *Two alerts a user must tune become one verdict
they must trust.*

**F4 — Trust guards → `INCONCLUSIVE`.**
Sample-size floor; `WARMING` with visible progress (`340/1000 spans`); input-
distribution co-movement check to suppress traffic-mix false positives. Every
`INCONCLUSIVE` names its reason. *The credibility feature — this is what buys the
right to be believed.*

**F5 — Self-contained delivery.**
The full verdict lands in the notification payload as an OTLP metric plus a
structured log with exemplar trace links. Never a bare link to a dashboard.
*A verdict that requires a click has already lost to the green dashboard.*

**F6 — Agent-legible output.**
A `skills.md` for SigNoz Agent Skills teaching an agent to read `vitals.*`,
including an explicit instruction to refuse rollback recommendations on
`INCONCLUSIVE`. Verdict records are token-budgeted (~200 tokens).
*The consumer is increasingly a machine with a degrading context window; and this
is the feature that makes Vitals worth adopting rather than reimplementing.*

**Evidence presentation rule (applies to F5):** exemplar traces always include
**one median example alongside the worst ones, labeled.** Worst-only evidence is
selection bias and will be caught.

---

## 7. Non-goals

| Not doing | Why |
|---|---|
| **Claiming an answer is wrong** | Vitals detects change, not correctness. Every state name, metric name, and doc must respect this. It is the project's central honesty commitment. |
| **Root-cause attribution beyond release boundaries** | Agent RCA is an open research problem. One confidently-wrong root cause destroys more trust than ten `INCONCLUSIVE`s. |
| **Offline evals, datasets, prompt management** | Someone else's category. Entering it makes Vitals the worst product in a crowded market instead of the only one in an empty market. |
| **LLM-as-judge scoring** | $0.01–0.10/assessment forces sampling; sampling makes distributional detection arithmetically impossible. |
| **Sitting in the request path** | Out-of-band is a positioning asset (vs proxy-based tools) and removes an entire class of reliability and compliance objections. |
| **Enforcement / budget circuit breakers** | Observe-only. The moment Vitals can kill traffic it needs a different reliability, security, and support story. |
| **Self-hosted GPU cost model (vLLM/Ollama)** | Different cost function, different buyer, forks the cost engine. The strongest V2.1 differentiator — and still wrong for V2. |
| **Trajectory / agent-behavior signals** | Span-graph data model, not response data. This is V3 and cannot share the verdict object without redefining it. |
| **Session-scoped aggregation, dead-man alerting, per-tenant dims** | Real gaps; no verdict story yet, or already generic SigNoz capabilities. |
| **Multi-backend support** | Being *the* SigNoz-native AI layer beats being a mediocre cross-platform one. |
| **Selling cost-only mode as a product** | Cost-only Vitals is approximately OpenLIT. The differentiation is entirely in the derived layer. Cost-only is a degraded fallback, not an offering. |

---

## 8. Demo flow — 4:30

| # | Time | On screen | Presenter | Why |
|---|---|---|---|---|
| 1 | 0:00–0:30 | Support chatbot answers a real question confidently and **wrongly**. Cut to SigNoz: latency flat, errors zero, all green. | *"Everything is green. The product is broken. That's the entire problem."* | Judges own the problem in 30 seconds, with no jargon and no architecture. |
| 2 | 0:30–1:15 | One slide: HTTP 200 · latency normal · zero errors. | *"A wrong answer is a successful HTTP request. Every tool measures whether the machine worked — none measure whether the answer was good, or what being wrong cost you."* Cite $47K/11 days. | Establishes a category gap, not a config mistake. |
| 3 | 1:15–1:45 | One diagram, 20 seconds. | *"One line in your collector config. We never touch your request path."* | Kills the "does this slow my app down" objection early, then architecture is never mentioned again. |
| 4 | 1:45–2:30 | Runaway loop triggered. Invoice shows **$3**. Vitals: `CHANGED · cost · 51× median session · unattributed`. | *"The bill is still three dollars. You already know."* | Quantitative, unmistakable, and teaches velocity-vs-cumulative without statistics. |
| 5 | 2:30–3:30 | Split screen. Left: SigNoz, still green, still flat. Right: `CHANGED · behavior · v2 vs v1 · 4.2σ · onset 90s after deploy · cost flat`. Open one exemplar; **read the bad answer aloud** beside the v1 median answer. | *"Nothing on the left will ever turn red. This is the failure that reaches your customers."* | Green-vs-red split screen is the most persuasive image available; reading it aloud makes it visceral. |
| 6 | 3:30–4:15 | Terminal: Claude + SigNoz MCP. Type *"Should we roll back v2?"* Agent answers with version, delta, trace links. | *"No dashboard. No query. The person on call is increasingly not a person."* | The beat no competitor can copy on stage. |
| 7 | 4:15–4:30 | One slide: what Vitals does **not** claim, and its known blind spots. | *"We don't tell you the answer is wrong. We tell you it changed, when, and what shipped."* | Judges try to break demos. Pre-empting converts the weakest point into the most credible one. Never cut this for time. |

**Not in the demo:** architecture deep-dive, the dashboards, price-table config,
and the words PSI or CUSUM. Answer if asked; never volunteer.

---

## 9. Success criteria

**Ship criteria** — a stranger, unassisted, can:
1. add one exporter to a collector config,
2. see a `STEADY` verdict on unchanged traffic **within one hour, with no
   deploy**,
3. deploy a prompt change and receive a correct attributed verdict,
4. ask their coding agent "should I roll back?" and get a grounded answer.

Step 2 is the acceptance test for the corrected thesis. If first value requires
a deploy, V2 has failed regardless of what else works.

**Metrics**

| Metric | Target | Rationale |
|---|---|---|
| Time to first verdict after install | < 60 min, zero deploys | The cold-start cliff. Non-negotiable. |
| False-positive rate on steady traffic | 0 over 7 days | The demo's beat-5 credibility rests entirely on this. |
| Share of verdicts `INCONCLUSIVE` | 5–15% | <5% means the guards aren't working. >15% means the product feels useless. |
| Attribution correctness on known deploys | 100% on the demo corpus | If it misattributes a release, the hero use case is dead. |
| Verdicts consumed by an agent vs a human | rising over time | Confirms or kills the F6 bet — instrument it from day one. |

**Measurement debt to clear before publishing any claim:** CUSUM parameters ship
with synthetic-spike defaults and have never been calibrated against real
traffic. No drift-onset-latency figure may be published — in the demo, the README,
or a pitch — until that calibration exists. On a product whose entire asset is
trust, an unbacked latency number is the most expensive available mistake.
