# V2 Pressure Test — Adversarial Review

Written to break the V2 definition, not defend it. Findings are ordered by how
much damage they do. The resulting spec is [docs/v2-prd.md](v2-prd.md).

Five findings are severe enough to change the design:

- **C1** — the release framing is structurally blind to vendor-side model drift
- **C2** — cold start needs *two* deploys, so time-to-value is weeks, not 90 minutes
- **C3** — the 5-minute promise and the 5% canary story are arithmetically incompatible
- **C4** — the state name `QUALITY_REGRESSION` contradicts the project's own honesty doc
- **C5** — "worst-first" exemplar traces are a selection-bias trap that will lose trust

---

## 1. Core thesis

**Claim under test:** *"Every AI change is a deploy with no test suite. Vitals
grades the deploy in production."*

### What's wrong with it

**C1 — The deploy framing has a hole big enough to drive the category through.**
The trigger is a new `service.version`. But the two most-cited AI regressions in
the field have no deploy at all:

- the **$47K/11-day runaway loop** — no version change, no deploy, cost only
- **provider-side model drift** — the vendor changes the model behind a fixed
  string, or the user's traffic mix shifts. `service.version` is constant.
  Vitals, as defined, is structurally incapable of seeing this.

The second one is the more damaging omission, because *"the model changed under
me and nobody told me"* is a fear every AI team has and no OTel-native tool
addresses. The V2 definition accidentally scoped it out.

**The premise is also slightly insulting and slightly false.** Teams *do* have
test suites — offline eval suites, which they ran, and which passed. Telling a
buyer they have no tests makes them defensive. The true and sharper statement is:

> **Your evals passed. Production regressed anyway. You found out from a user or
> from the invoice.**

That is a statement the buyer has personally lived, it implicitly positions
against the eval vendors without naming them, and it does not require a deploy.

**Would a customer understand it immediately?** "Grades the deploy" — yes, but
they'd hear *CI for prompts*, which is offline eval, which is the crowded
category. The framing accidentally points at the wrong shelf.

### Framings compared

| Framing | Strength | Fatal flaw |
|---|---|---|
| "Grades the deploy" (current) | concrete, demo-able | blind to no-deploy regressions; sounds like CI/offline eval |
| "Cost + quality SLO for AI" | familiar SRE shape | SLOs need a ground-truth objective; you don't have one for quality. Overclaims. |
| "Rollback decision support" | decision-shaped | too narrow — only useful in the minutes after a deploy, idle 99% of the time |
| **"Vitals tells you when your AI's behavior changes — and what changed it"** | covers deploys *and* vendor drift *and* traffic shift; "behavior changed" is defensible where "quality dropped" is not | vaguer, so messaging must lead with the release case as the hero |

### Recommendation

**Keep the release comparison as the hero *use case*. Reject it as the *trigger*.**

The trigger becomes: *a statistically significant change in behavior or cost
against a baseline.* Version is then the best-attributable **cause**, not the
precondition. Vendor drift becomes a first-class detection with
`cause: unattributed` instead of being invisible.

Headline: **"Your evals passed. Production changed anyway."**
Subhead: *Vitals watches 100% of your AI traffic and tells you when behavior or
cost moves — which release did it, or that nothing you shipped did.*

That last clause — **"nothing you shipped did"** — is a genuinely novel product
promise and nobody in the OTel-native stack can make it.

---

## 2. Product workflow

Walking the journey from deploy to verdict. Six friction points, in order.

**C2 — Cold start is broken. Time-to-value is two deploys, not 90 minutes.**
The design baselines against *"the last version that held a PASS."* On install
there is no such version. So: deploy 1 establishes the baseline, deploy 2
produces the first verdict. For a team shipping weekly, **first value is 7–14
days after install.** The V2 doc claims 90 minutes. That is the single largest
adoption risk in the product and it was not acknowledged.

*Fix:* on install, immediately begin a **time-over-time** comparison (this hour
vs the rolling baseline of the same service). Value on day one, zero deploys
required. This is the same mechanism that fixes C1 — one change, two problems
solved. It should probably be the *default* mode, with release comparison as a
specialization.

**C3 — The 5-minute verdict and the 5% canary are incompatible arithmetic.**
The journey shows `n=1,240` spans within 5 minutes at 5% canary traffic. That
implies ~5,000 requests/minute of total production LLM traffic. Almost no team
in the target segment has that. A realistic mid-size team at 5% canary produces
**tens of spans in five minutes** — permanently `INCONCLUSIVE`. The product
would appear broken to exactly the careful teams it's designed for.

*Fix:* stop promising a wall-clock number. Promise **"a verdict at n spans,
and a live countdown to it."** Show `warming: 340/1000 spans, est. 22 min`.
The user's cognitive load drops because the system is explicit about what it's
waiting for, instead of being mysteriously silent. Wall-clock latency becomes a
*reported* property, not a *promised* one.

**C3b — Sequential windowing is the wrong model for canaries.** A canary means
v2.3 and v2.2 run **concurrently**, on the same traffic mix, at the same hour.
That's a natural A/B and is strictly more sound than comparing a window now to a
window an hour ago — it controls for traffic-mix and time-of-day confounds for
free. The V2 doc described sequential windows and left this on the table.

**C4 — Cost deltas have no unit and no scale.** "Cost delta % per-session
normalized" — *session* is not a defined concept in V1. Per request? Per trace?
Per user turn? An ambiguous denominator makes the headline number
un-interpretable, and the headline number is the product.

Worse: **+34% is not self-evidently bad.** Without knowing that normal
release-to-release variance is ±8%, the user cannot judge. Every delta must ship
with its variance context: *"+34% (normal range ±8%)"*.

**C5 — Six verdict states is three too many.** `COST_REGRESSION`,
`QUALITY_REGRESSION`, and `REGRESSED` are three names encoding two independent
booleans. Collapse to one state plus two flags. Fewer names to learn, and the
joint case stops needing its own vocabulary.

**C6 — The last mile is undefined.** The alert fires and the user is in Slack.
Do they get the verdict *text*, or a link? If it's a link to the Report Card,
the dashboard problem is reintroduced through the back door — the research says
those dashboards go unopened. **The alert payload must contain the entire
verdict.** The dashboard is for the retrospective, never for the decision.

### Cognitive-load reductions

1. One sentence, always the same shape:
   *"v2.3 costs 34% more per request than v2.2 (normal ±8%); behavior unchanged. n=1,240. 3 traces."*
2. Deltas expressed **relative to normal variance** (sigma), not raw percentage.
3. Progress instead of silence: `warming 340/1000` beats an unexplained absence.
4. Every verdict carries a **"what would change this"** line — the falsifier.
5. Verdict lives in the notification; the dashboard is an archive, not a step.

---

## 3. Is `Verdict` the right primary object?

### Alternatives

| Object | Argument for | Why it fails |
|---|---|---|
| **Report Card** | friendly, familiar | passive and retrospective. A report card is something you *receive after it's too late*. It also implies a grade on an absolute scale — which the honesty doc explicitly says Vitals cannot produce. |
| **Incident** | plugs into existing on-call muscle | most outcomes are "nothing changed." You cannot open an incident for a non-event, so the object only exists on the bad path — meaning the product has no artifact 95% of the time, and no way to build trust through repeated correct silence. |
| **Comparison** | it is literally what gets computed; generalizes to time-over-time | it's an *analysis*, not a *decision*. Users don't want a comparison, they want to know what to do about it. Too passive to be the headline noun. |
| **Change** | matches the corrected thesis; exists only when something moved | same problem as Incident — no artifact on the happy path. |
| **Verdict** ✅ | decision-shaped, exists on every path (including PASS), and forces the product to commit | the name overclaims judicial authority, and as scoped it was tied to versions. |

### Recommendation

**Keep `Verdict` as the primary object, but change its subject.**

A Verdict is currently *about a version*. It should be **about a comparison
window** — with the compared thing declared:

- `release` — v2.3 vs v2.2 (hero case)
- `time` — this hour vs baseline (catches vendor drift, works day one)
- `cohort` — canary vs control, concurrent (best statistics, canary-native)

One object, one state machine, three subjects. This is a small conceptual change
that resolves C1, C2, and C3b simultaneously — which is a strong signal it's the
right cut.

**And rename the states.** `QUALITY_REGRESSION` directly contradicts
`docs/honesty.md`, which states Vitals measures *deviation from baseline, not
correctness*. Shipping a state literally named "quality regression" re-introduces
the overclaim the project already decided not to make — and it's the claim a
skeptical judge or a skeptical buyer will attack first.

| Old | New |
|---|---|
| `PASS` | `STEADY` |
| `COST_REGRESSION` / `QUALITY_REGRESSION` / `REGRESSED` | `CHANGED` + flags `cost` / `behavior` |
| `WARMING` | `WARMING` (now with progress) |
| `INCONCLUSIVE` | `INCONCLUSIVE` (with a reason code) |

Four states. `CHANGED` is defensible in front of anyone; `QUALITY_REGRESSION` is
not.

---

## 4. Trust — every way this loses it

### False positives

| # | Scenario | Severity |
|---|---|---|
| T1 | **Traffic-mix shift.** Monday-morning enterprise questions vs weekend consumer questions. Output distribution moves because *input* moved. Vitals reports a behavior change; nothing changed. **This is the most likely false positive in the product** and output-only PSI cannot distinguish it. | Critical |
| T2 | **Truncation config change.** Operator follows OTel guidance and caps content at 500 chars. Every embedding shifts. | High |
| T3 | **Length-driven drift.** A prompt change that makes answers politely longer moves PSI without changing substance. | High |
| T4 | **Retry/timeout storms** inflating cost velocity with no behavior change. | Medium |
| T5 | **Low-volume noise** — a 40-span window producing a confident-looking delta. | High |

*Mitigations:* score the **input** distribution alongside the output and suppress
when both moved together (T1); guard on completion-length distribution and label
`suspected_truncation` (T2, T3); hard sample-size floor before any non-`WARMING`
state (T5).

### False negatives

| # | Scenario |
|---|---|
| T6 | **Subtle factual degradation** with unchanged style, length, and embedding profile. PSI is blind to this. It is the failure people most fear and the one Vitals is *least* able to catch. |
| T7 | **Baseline poisoning** — a bad release that runs long enough silently becomes the reference. The "baseline against last STEADY" rule mitigates this only if a verdict was correctly issued at the time. |
| T8 | **Deploy during `WARMING`** (e.g. after a restart) — the blind window falls exactly when coverage matters most. |
| T9 | **Uniform degradation** — everything got slightly worse together, so the *relative* comparison shows nothing. |

*Mitigation for T6 and T9 is not technical — it is disclosure.* Ship a
**"Known Blind Spots"** page and link it from the product. Naming your own
failure modes is the single most trust-building thing a measurement product can
do, and it costs one afternoon.

### Presentation failures

**C5/T10 — "Worst-first" exemplars are a selection-bias trap.** Showing the
worst 3–5 traces out of 1,200 means the user reads the tail and concludes the
system is broken — when a heavy tail may be perfectly normal. Then they check
manually, find most outputs fine, and conclude *Vitals* is broken. Trust lost in
one interaction.

*Fix:* always show **one median exemplar next to the worst ones**, labeled. The
contrast is what makes the evidence honest.

**T11 — PSI is unitless.** "Behavior delta 0.04" is meaningless to a human and
worse to an agent, which will confidently invent an interpretation. Always
express change in **sigmas against observed baseline variance**, never in raw
statistic units.

**T12 — Agent amplification.** An agent reading a wrong verdict doesn't just
believe it; it acts, then reports its action confidently in Slack. Machine
consumption raises the cost of every false positive. The `INCONCLUSIVE` state
must be *machine-legible* and the `skills.md` must explicitly instruct the agent
to refuse to recommend rollback on `INCONCLUSIVE`.

**T13 — Uncalibrated CUSUM.** Onset-latency defaults are synthetic. Any published
latency number is currently unbacked.

### Trust mechanisms to build in

1. **Shadow week.** New installs compute verdicts but don't alert for 7 days.
   The user sees what *would* have fired and calibrates against reality before
   Vitals earns the right to page them.
2. **Every verdict states its falsifier** — "this would flip to STEADY if input
   distribution is the cause; input drift was 0.3σ."
3. **Verdict receipts.** Every past verdict is retrievable with its inputs. Users
   can audit. Auditability *is* trust.
4. **A "this was wrong" button.** Costs almost nothing, signals humility, and
   generates the only labelled data the product will ever get.
5. **Never say "quality."** Say "behavior changed." Underclaim on the noun and
   overclaim on nothing.
6. **Publish blind spots** (T6, T9) in the product, not just the docs.

---

## 5. Demo — 4:30, story-first

The current two-beat demo opens with architecture. It should open with a
**customer being failed**. Judges must feel the problem before seeing any tool.

**Scene 1 — The failure (0:00–0:30).** *No slides.* A support chatbot on screen.
Type a real customer question. It answers confidently — and wrongly. Beat.
Presenter: *"That's your product, in production, right now. Here's what your
monitoring says about it."* Cut to SigNoz: latency flat, error rate zero,
throughput normal. **Every chart is green.**
> *"Everything is green. The product is broken. That's the entire problem."*

Why: 30 seconds, no jargon, no architecture, and the judges now own the problem.

**Scene 2 — Why it's invisible (0:30–1:15).** One slide, three lines: HTTP 200.
Latency normal. Zero errors. *"A wrong answer is a successful HTTP request. Every
tool in this room measures whether the machine worked. None of them measure
whether the answer was any good — or what it cost you to be wrong."* Name the
$47K/11-day runaway in one sentence.

Why: establishes that this is a category gap, not a configuration mistake.

**Scene 3 — What we did (1:15–1:45).** One diagram, on screen for 20 seconds.
*"One line in your collector config. We get a copy of your AI spans. We never
touch your request path — if we go down, nothing happens to you."*

Why: judges' first objection is "does this slow down my app." Kill it early, then
never mention architecture again.

**Scene 4 — Cost (1:45–2:30).** Trigger the runaway loop. Show the invoice: still
$3. *"Your bill won't tell you for 30 days."* Then Vitals fires on **rate**:
`CHANGED · cost · 51× median session · unattributed`.
> *"The bill is still three dollars. You already know."*

Why: an unmistakable, quantitative win, and it demonstrates *velocity vs
cumulative* without a word of statistics.

**Scene 5 — The silent regression (2:30–3:30).** Ship the poisoned prompt.
SigNoz dashboards on the left — still green, still flat. Vitals on the right:
`CHANGED · behavior · v2 vs v1 · 4.2σ · onset 90s after deploy · cost flat`.
Click one exemplar and **read the bad answer out loud**, next to the median
answer from v1.
> *"Nothing on the left will ever turn red. This is the failure that reaches your
> customers."*

Why: split-screen green-vs-red is the single most persuasive image available, and
reading the answer aloud makes it visceral rather than statistical.

**Scene 6 — The close (3:30–4:15).** Switch to a terminal running Claude with the
SigNoz MCP server. Type: *"Should we roll back v2?"* The agent reads the verdict
and answers with the version, the delta, and trace links.
> *"No dashboard. No query. The person on call is increasingly not a person —
> and this is the signal it needs."*

Why: this beat is the one no competitor can copy on stage, and it lands the
strategic bet in ten seconds.

**Scene 7 — Honesty (4:15–4:30).** One slide: *"We don't tell you the answer is
wrong. We tell you it changed, when, and what shipped. Here's what we can't
see — [blind spots]."*

Why: judges try to break demos. Pre-empting the attack converts your biggest
weakness into your most credible moment. Never skip this to save 15 seconds.

**Cut from the demo:** the architecture deep-dive, the three dashboards, the
price-table config, anything about PSI or CUSUM by name. If a judge asks, answer;
never volunteer.

---

## 6. Competition — by workflow, not features

The honest cut is **push vs pull** and **where you already are**.

| Tool | Their workflow | Vitals' workflow difference |
|---|---|---|
| **SigNoz** | You already run it. Stores AI spans, Noz reads them. Answers *"what happened?"* | Not a competitor — the substrate. Vitals gives Noz a derived signal worth reading. Risk: Noz derives it natively. |
| **LangSmith** | Separate app, separate login. You go there *when you already suspect a problem*. Trace-inspection and prompt-iteration first. | Vitals is push. It tells you to suspect. Also: LangChain-centric; Vitals is framework-agnostic via OTel. |
| **Langfuse** | Self-hostable, OTel-ish, LLM-as-judge on **sampled** traffic. Excellent for offline eval + dataset workflows. | Sampling makes distributional drift undetectable. Vitals runs on 100% because it's deterministic and free. **Complementary, not displacing** — Langfuse for "is this output good," Vitals for "did the population change." |
| **Arize / Phoenix** | The most direct threat: embedding drift is their home turf and Phoenix is OSS + OTel. | Arize is a *platform you adopt* — new data plane, new UI, new bill. Vitals is a *signal inside the platform you already run.* The wedge is "don't adopt anything," not "detect drift better." Do not claim better statistics than Arize; you won't win that. |
| **Braintrust** | Eval-first, CI-centric, dataset and scorer management. Pre-production. | Different half of the lifecycle. Braintrust says ship; Vitals says what happened after you did. Genuinely complementary. |
| **Helicone** | A **proxy**. One-line integration, great cost analytics. | Being in the request path is a reliability and compliance coupling many teams refuse. Vitals is out-of-band by design. Helicone has no quality signal. |
| **OpenLIT** | The closest neighbor: OTel-native, emits GenAI cost/token metrics to any backend. | **Be honest — cost-only Vitals is roughly OpenLIT.** OpenLIT *instruments and computes*; it does not do version-aware statistical comparison, baselines, or verdicts. The differentiation is entirely in the derived layer. This means **cost-only mode is not a product** — it's a fallback. Don't sell it. |

**Why not just add another dashboard?** Because a dashboard is *pull*. Every
regression in the research went undetected while dashboards were green and
available. The failure mode isn't missing data — it's that nobody looked. Vitals
is push, and increasingly pushes to a machine.

**Why not just add an eval tool?** Because judge-based evals cost $0.01–0.10 per
assessment, which forces sampling, and **sampling makes drift detection
mathematically impossible.** You cannot compute a population shift from 2% of a
population. That's not a feature gap; it's an arithmetic one.

**The uncomfortable truth to internalize:** Vitals does not displace anything. It
is additive. Pricing, packaging, and pitch must all be built for *additive*, or
every sales conversation becomes a rip-and-replace argument you will lose.

---

## 7. Scope

### If you have 3–4 days — cut these five

| Cut | Why it's safe |
|---|---|
| **The Release Report Card dashboard** | The verdict lives in the alert payload. The dashboard is the *archive*, and the research says archives go unopened. Highest effort, lowest demo value. |
| **Persistent baselines** | Painful in production, invisible in a demo. Document the restart behavior honestly and move on. |
| **`vitals explain` CLI** | `skills.md` plus a well-shaped log record gives the agent everything. The CLI is a second surface for the same content. |
| **Truncation + mapper-version guards** | Real, but they defend against *operator config changes* that won't occur in a 4-day window or on stage. Ship the sample-size floor and `WARMING` — those two carry the entire trust story for now. |
| **Three delivery surfaces → one** | Metric + log is enough. Drop the third. |

**Do not cut:** change detection, the verdict state machine, the joint condition,
the sample-size floor, `INCONCLUSIVE`, `skills.md`, and the median-vs-worst
exemplar pairing. Those *are* the product.

### If you have one extra week — one thing

**Ship time-over-time comparison (the `time` subject).**

It is the highest-leverage item in the entire backlog because it fixes three
separate problems with one mechanism:

- **Cold start (C2)** — value on day one, zero deploys required. Kills the
  largest adoption risk in the product.
- **Vendor drift (C1)** — closes the structural blind spot and unlocks the one
  promise no competitor can make: *"nothing you shipped did this."*
- **Demo** — a third beat that needs no deploy and shows the product working on
  a system nobody changed.

Runner-up: concurrent cohort comparison (canary vs control), which fixes the
statistics and the C3 arithmetic. But it only helps teams already running
canaries; time-over-time helps everyone, on install, forever.
