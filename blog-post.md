# The Dashboard Was Green. The Answer Was Wrong.
### Building Vitals: a cost and quality layer for SigNoz that scores every AI response instead of sampling one

Six days into the hackathon, I was staring at a terminal-styled console on my own laptop, watching a verdict card that I'd built flip states in real time. It said `CHANGED`. Good, that's what a poisoned prompt deploy is supposed to trigger. Then I looked one line down, at the `cause` field, and it said `unattributed`.

It should have said `RELEASE`.

The detector was right. The reasoning behind it was wrong. And for about twenty minutes I genuinely didn't know if I'd found a real bug or if I was about to convince myself of a bug that wasn't there, which is its own special kind of hackathon panic.

I'll get back to that. First, the actual reason any of this exists.

### The problem I kept running into

A dashboard full of green latency and error-rate panels tells you almost nothing about whether an LLM feature is working. A wrong answer is still a `200 OK`. There's no exception, no non-2xx status, nothing that trips an alert. The model just answers confidently and incorrectly, and every graph in your APM stays flat and green while it happens.

This isn't hypothetical. In April 2026, Anthropic confirmed that a wave of Claude Code quality complaints came from a product-layer prompt and reasoning change: no model version bump, no announcement, and no internal way to catch it without measuring outputs directly. Their own engineers found out from user complaints. If the company that built the model can't see this happening internally, an app team building on top of it has even less visibility.

Cost fails the same way, just faster and more expensively. The most-cited postmortem in this space is four LangChain agents with no step cap that recursed for eleven days and produced a $47,000 bill, with every dashboard green the entire time. Nobody notices a "slightly busier" hour. They notice the invoice.

Both failures share a shape: the signal that would have caught them exists, but it isn't wired into anything that pages a human.

### Why the obvious fix doesn't scale

The obvious fix is an LLM-as-judge: have another model grade every response. It works, but it costs real money and takes real seconds per call, so nobody runs it on every request. Teams sample it, offline, in a separate tool that's disconnected from whatever actually pages someone. The quality data exists. It just never reaches the alerting system.

I wanted something that could run on **100% of traffic**, cost nothing per request, and live in the same place as p99 latency instead of a side tool nobody opens until after the invoice arrives. That's only possible if the scoring is deterministic, no model call, just math, which also happens to be the one thing spanIQ, a deterministic eval engine I already had lying around from before the hackathon, was built to do.

### What I built

Vitals is a sidecar that sits next to an existing OTel Collector. It doesn't proxy anything and it isn't in the request path. The collector just fans a second, unmodified copy of the same `gen_ai` span stream out to Vitals, the same way it already fans traffic to SigNoz. If Vitals falls over, nothing user-facing notices.

Inside, two engines run on every span: a cost engine (tokens times a price table, tracked as USD/min velocity, not just cumulative spend, because the failure mode that matters is the *rate*), and a quality engine that scores drift against a rolling healthy baseline using PSI, no reference answer required. Every few seconds, an evaluator compares each service/model/version scope's current window against its baseline and emits one of four verdicts: `WARMING` (not enough data yet, so no score at all; I decided early on that a false alarm on clean traffic is worse than a slow one), `STEADY`, `CHANGED`, or `INCONCLUSIVE`. Both signals get written back into SigNoz over their own out-of-band OTLP connection, as metrics for dashboards and trace-linked log records for drill-down.

I want to be specific about what this measures, because it would be easy to oversell it: it detects *change*, not *truth*. It answers "did quality shift, when, and with which release," not "is this answer correct." No reference-free metric run on live production traffic can answer the second question, and every incident I cited above, Anthropic's included, was a *change* story, not a correctness story. Claiming more than that is exactly how a project like this falls apart the moment someone who knows the space starts asking questions.

To make all of this demoable without a live model or Docker, I built a deterministic replay engine: pre-recorded OTLP spans in JSONL, fed through the real receiver, real scoring, real evaluator, at any speed you want, `vitals replay demo/fixtures/02_release_regression.jsonl --speed 10.0`. Console pops up at `localhost:8787`, same code path as production, zero API keys.

**[Image 1: architecture diagram — collector fanning out to SigNoz and Vitals]**

Which brings me back to the console and the wrong label.

### The bug that made me actually understand my own system

The regression fixture is built to simulate a poisoned prompt shipping as `v2`. At normal speed it worked exactly as designed: behavior drift crosses threshold, the evaluator attributes the change to the recent release, `cause: RELEASE`. But I was running it at 10x speed to make the demo watchable, and at that speed the `cause` came back `unattributed` instead.

My first instinct was that the drift math was broken. It wasn't: the verdict itself was correct, `CHANGED`, right on schedule. The problem was time. Attribution works by checking whether a version's deploy timestamp falls inside a fixed real-world window (five minutes) before the current evaluator tick. That window is written in wall-clock seconds. A replay running at 10x speed compresses eleven real minutes of fixture timestamps into about one real minute, so by the time the evaluator's own tick (which runs on actual wall-clock time, not replay-accelerated time) catches up, the deploy has already scrolled outside the attribution window. The detection was fine. The attribution's clock and the replay's clock were running at two different speeds, and nothing in the code ever reconciled them.

That distinction, virtual time versus real time, turned out to be a running theme, not a one-off. A few days earlier I'd found a related bug where `--speed 0` (as fast as physically possible, no sleep at all) fed every span the same frozen virtual timestamp, because the replay runner only propagated a real elapsed offset when speed was greater than zero. I fixed that one directly: `virtual_now = start_real_ts + rel_ts`, no conditional, every span gets its own point in virtual time regardless of speed.

**[Image 2: Vitals console mid-CHANGED verdict during a replay run]**

The accelerated-attribution miss was different. I could have hacked around it: inflated the attribution window, or special-cased replay mode to lie about elapsed time. Both would have made the demo look cleaner and would have been exactly the kind of quiet self-deception the whole project exists to catch in *other* systems. So I didn't. I documented it in the demo guide instead: at `--speed 10.0` the cause can show `unattributed` even though the verdict is correct, and it resolves correctly at `--speed 1.0` or against live traffic, where the evaluator's clock and the traffic's clock actually agree. Writing that sentence stung a little. It also felt like the only honest thing to do, given that "never emit a score you can't stand behind" was already the rule for every other verdict in the system.

### Then I pointed it at a real SigNoz instance, and time wasn't the problem anymore

The replay path is deterministic and self-contained on purpose, but a hackathon judge is going to want to see real dashboards and a real alert fire, so I stood up an actual SigNoz deployment and imported the three dashboards and the alert rule I'd written.

Two of the four assets failed on first import. The alert rule was authored against an older rule-query schema; the live instance was running SigNoz's newer `v5` format, and the old shape wasn't just deprecated, it was rejected outright with "must have at least one query." I rewrote the composite query structure and swapped the `{{handlebars}}` templating in the alert description for SigNoz's actual `$var` syntax, then re-verified by importing all three dashboards and the alert rule again, for real, against real data.

**[Image 3: SigNoz Query Builder result for vitals.cost.velocity, grouped by service.name and model, from a live import]**

Separately, the demo app and SigNoz's own MCP server were both defaulting to port 8000, so the RAG app silently lost the fight and the compose stack came up broken until I moved it to 8002 and fixed two scenario scripts that were still POSTing `{"prompt": ...}` to an endpoint that only accepted `{"query": ...}`. And once the MCP server was actually running, Docker reported it `unhealthy`, which turned out to be a packaging bug in the platform's generated healthcheck (it `exec`s `wget` inside a container image that doesn't ship `wget`), not a real outage. `curl` against the actual endpoint returned a clean `200` the whole time. Three different systems, three different ways of quietly lying about their own state, which, in hindsight, is a fairly on-brand set of bugs for a project about not trusting a system's surface-level status.

### What actually shipped

By the end, cost and quality signals flowed from a real OTLP receiver through scoring to out-of-band OTLP emission, verified against live traffic and a live SigNoz instance rather than authored and hoped-for. From an alert or a dashboard panel, an engineer, or Claude, via SigNoz's own MCP server, can pull the trace-linked exemplars behind a `CHANGED` verdict and go straight to the response that tripped it.

**[Image 4: the verdict-changed alert firing in a live SigNoz instance]**

### What I'd tell someone building something similar

Time is the hardest part of any system that claims to detect *when* something changed, not just *that* it changed, and it gets harder, not easier, the more you accelerate or simulate it for a demo. If your system's entire value proposition is "we tell you the truth about drift," the discipline has to extend to your own debugging: document the caveat instead of quietly patching around it, because the caveat is more convincing than a demo that never shows you a single rough edge. And check the raw protocol before you trust a status label: `docker ps` said `unhealthy`, `curl` said otherwise, and the label was the one that was wrong.

Code's on GitHub if you want to see how any of it actually works: [github.com/furyfist/Vitals](https://github.com/furyfist/Vitals). Apache 2.0.
