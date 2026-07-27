# Vitals Hackathon Demo — Architecture File (Shot-by-Shot Animation Brief)

Source of truth for timing: `vitals_fixed.srt` (27 cues, 00:00:00,190 → 00:00:51,670).
Design system: pasted `hackathon-demo-design.md` brief (landscape continuation of the
Harness/Context Window/MCP reel series). Canvas 1920×1080, 16:9, YouTube.

This file covers **only the narrated span of the SRT (0.19s → 51.67s)**. Cue 27 ends on
"Now let's see Vitals detect a real AI regression live," which is a hard cut into
un-timed live-demo screen capture — see **Confirmed Decisions** below.

---

## Section 1 — The Hook (00:00:00,190 – 00:00:03,810)

**SRT cues 1–2:** "LLM applications usually don't fail because of latency or errors."

**Framing:** Full Face Cam.

**On screen:** Direct address, full-frame face cam. No diagram yet — this is a personal,
narrative opener, per the design brief's Full Face use case.

**Build:** Nothing animates behind the subject except the caption card. Hold on the
face; let the line land.

**Caption:** "LLM applications usually don't fail because of **latency** or **errors**."
(strike-through styling on "latency" / "errors" as the sentence resolves, foreshadowing
the reveal in Section 2 — uses the `#DC2626` error/strike token.)

**SFX:** soft riser (starts under "usually don't fail," builds through the cut to Section 2).

**Transition out:** hard cut on the sentence boundary ("...errors.") into Full Diagram —
timed to the riser's peak.

---

## Section 2 — The Real Failure Mode (00:00:03,810 – 00:00:09,239)

**SRT cues 2(cont.)–5:** "They fail because the answers slowly change, quality drops, or
cost suddenly shoots up while the infrastructure still looks healthy."

**Framing:** Full Diagram / Screen. Face cam disappears entirely.

**On screen:** A generic APM-style dashboard mockup — latency and error-rate panels,
all green, all flat. This is intentionally the "everything looks fine" visual the whole
project's thesis argues against (mirrors the blog post's own framing, "The Dashboard Was
Green. The Answer Was Wrong.").

**Build (progressive, staggered — not sequential node-by-node):**
1. Green latency/error panels fade in first (flat, steady) — calm, unremarkable.
2. As "answers slowly change" lands, a faint quality-score line appears *underneath* the
   green panels, drifting downward — low-contrast, easy to miss, on purpose.
3. As "cost suddenly shoots up" lands, a second faint line spikes upward in the same
   underlayer.
4. The green panels stay green and untouched throughout — the point is that nothing in
   the visible dashboard reacts.

**Kinetic type (on open canvas, not boxed):** "quality drops" and "cost shoots up" land
as short type bursts near their respective drifting lines, `#DC2626` accent.

**Caption:** "They fail because the answers **slowly change** — while infrastructure still looks healthy."

**SFX:** riser resolves into a soft pulse under "quality drops," a second soft pulse
under "cost suddenly shoots up."

**Transition out:** the two hidden lines and the caption wipe away; the dashboard mockup
scales down and away as we cut to Section 3.

---

## Section 3 — The Reveal: Vitals (00:00:09,239 – 00:00:11,954)

**SRT cue 6 (partial):** "That's why we built Vitals. Vitals is an"

**Framing:** Split / Corner — deliberate use #1. Face cam ~480×270, top-left, soft
scale-in entrance. This is the "product reveal next to the person who's telling you
about it" moment the design brief calls out as the legitimate use case for Split.

**On screen:** Next to the face cam, the **Vitals** wordmark builds in the open canvas
(Space Grotesk, bold) — not a placeholder logo, literally the project name as typography,
since Vitals has no separate brand mark to source from the repo.

**Build:** Wordmark soft-scale-in, centered in the open right-hand canvas, away from the
face cam per the text-over-background rule.

**Caption:** "That's why we built **Vitals**."

**SFX:** UI tick as the wordmark lands.

**Transition out:** quick swipe wipe (per design brief's mode-transition motion grammar)
into Full Diagram as the sentence continues into the architecture explanation.

---

## Section 4 — What Vitals Actually Is: The Pipeline (00:00:11,954 – 00:00:23,114)

**SRT cues 7–12:** "AI monitoring layer built on top of SigNoz. It watches 13 production
metrics across behaviour, quality, and cost, then combines them into simple verdicts like
WARMING, STEADY, and CHANGED to detect AI regressions automatically."

**Framing:** Full Diagram / Screen.

**On screen — the real pipeline, left to right, matching the actual data flow in
`docs/architecture.md` / the README's mermaid diagram:**

```
[Your AI Application] --OTLP--> [OTel Collector] --fan-out--> [SigNoz Ingest]
                                        │
                                        └--fan-out--> [Vitals Sidecar]
                                                          ├─ Cost Engine
                                                          └─ Quality Engine (spanIQ)
                                                                   │
                                                             [Verdict Evaluator]
```

**Build (grouped/staggered — see pacing flag below):**
1. (0:11.95–0:14.67, "AI monitoring layer built on top of SigNoz") — `OTel Collector`
   and `SigNoz Ingest` nodes are already faintly present (carried over from Section 2's
   dashboard motif, now formalized as labeled boxes); the `Vitals Sidecar` box builds in
   beside/below `SigNoz Ingest`, connected by the fan-out arrow, with a small "sits
   alongside, not in the request path" label-tag.
2. (0:14.67–0:19.80, "13 production metrics across behaviour, quality, and cost") —
   inside the Vitals Sidecar box, **three grouped category chips** appear together
   (soft scale-in, staggered by ~150ms each, not one-by-one node reveals): **Behavior**,
   **Quality**, **Cost**. A small "13" badge ticks up once across all three collectively
   rather than 13 individual metric names appearing on screen (see pacing flag).
3. (0:19.80–0:23.11, "combines them into simple verdicts like WARMING, STEADY, and
   CHANGED") — the three chips converge into a single `Verdict Evaluator` node; three
   verdict-state pills build in beside it in sequence: `WARMING` (gray), `STEADY`
   (`#16A34A` green), `CHANGED` (`#DC2626` red) — one active pill highlighted at a time
   per the motion grammar, the other two dimmed.

**Caption cards (2 max lines each, cut at phrase boundaries):**
- "An AI monitoring layer built on top of **SigNoz**."
- "13 production metrics across **behaviour, quality, and cost**."
- "Combined into simple verdicts: **WARMING · STEADY · CHANGED**."

**SFX:** digital click on the Vitals Sidecar box landing; three soft UI ticks for the
category chips; digital bloom on the verdict pills resolving.

**⚠ Pacing flag:** ~11.2s of narration covers three distinct architectural ideas (layer
placement, 13 metrics across 3 categories, verdict combination). Rendering 13 individual
metric-name nodes in that window would be illegible. Recommended fix (already reflected
above): show 3 grouped category chips with a single "13" badge, not 13 discrete boxes.
See **Confirmed Decisions** for the exact-count question this sidesteps.

---

## Section 5 — How Detection Actually Works (00:00:23,114 – 00:00:36,400)

**SRT cues 13–19:** "Instead of checking every request on its own, Vitals continuously
compares the current behaviour with a healthy baseline. When enough metrics move
together, beyond the normal range, it marks the system as changed and sends that
information to SigNoz through dashboards and alerts."

**Framing:** Full Diagram / Screen (continues from Section 4 — no mode cut, but a
distinct visual beat with its own build; see design note below).

**On screen:** Zoom from the pipeline-level view into the `Verdict Evaluator` node's
internal logic.

**Build (progressive):**
1. (0:23.11–0:26.73, "Instead of checking every request on its own, Vitals continuously
   compares...") — a rolling baseline distribution (soft histogram/band shape, frozen
   healthy reference) appears on the left; a "current window" distribution appears on
   the right, both labeled plainly (not literal PSI/CUSUM math on screen — see
   `docs/architecture.md`'s ResponseDrift/CUSUM mechanism, simplified to a visual
   baseline-vs-current comparison for a general technical audience).
2. (0:26.73–0:30.93, "current behaviour with a healthy baseline. When enough metrics
   move together, beyond the normal range...") — the current-window shape drifts and
   separates from the baseline band; a sigma readout ticks up (e.g. `+4.2σ`, matching
   the real `behavior_sigma` / `cost_sigma` values shown in the actual Vitals console).
3. (0:30.93–0:34.67, "it marks the system as changed") — the `CHANGED` pill (dimmed
   since Section 4) snaps to full brightness/red, others dim fully. Digital bloom.
4. (0:34.67–0:36.40, "and sends that information to SigNoz through dashboards and
   alerts") — an arrow animates from the `Verdict Evaluator` back out to `SigNoz Ingest`
   (echoing the real out-of-band OTLP emission path — metrics + trace-linked eval/verdict
   logs, sent directly to SigNoz ingest, not through the monitored collector), branching
   into two labeled endpoints: `Dashboards` and `Alerts`.

**Caption cards:**
- "Continuously compares current behaviour with a **healthy baseline**."
- "Enough metrics move together → marked **CHANGED**."
- "Sent back to SigNoz as **dashboards and alerts**."

**SFX:** soft pulse as the distributions separate; digital bloom on the CHANGED pill;
whoosh on the arrow animating out to SigNoz.

**Transition out:** hard cut to Full Face Cam on the sentence boundary at 36.40s.

---

## Section 6 — Transition: Why This Matters (00:00:36,400 – 00:00:41,010)

**SRT cues 20–21 (partial):** "This helps engineers catch problems much earlier."

**Framing:** Full Face Cam.

**On screen:** Back to the subject, full frame — a breather beat between the dense
technical Sections 4–5 and the fast proof-point montage in Section 7, per the design
brief's "transitions between technical sections" use case for Full Face.

**Build:** No diagram. Caption only.

**Caption:** "This helps engineers catch problems **much earlier**."

**SFX:** soft fade (clears the SFX bed from Section 5 before the montage's faster cuts
start).

---

## Section 7 — Proof Points Montage (00:00:41,010 – 00:00:47,060)

**SRT cues 21(cont.)–24(partial):** "We tested it on 4 real failure scenarios, built 3
dashboards, and added verdict-based alerts, and connected it to Claude through MCP, so
engineers"

**Framing:** Full Diagram / Screen, fast-cut pacing (the design brief's explicit
exception for narration that calls for urgency/list-pacing).

**On screen — real artifacts, not generic placeholders:**

*4 failure scenarios* (0:41.01–0:42.74, ~1.7s) — four small scenario cards appear
**together as a grouped reveal**, not sequentially (see pacing flag): `Steady Baseline`,
`Release Regression`, `Runaway Cost Loop`, `Input Shift` — matching the four real replay
fixtures (`01_steady_baseline.jsonl` … `04_input_shift.jsonl`) and their real verdicts
(`STEADY`, `CHANGED`, `CHANGED · runaway`, `INCONCLUSIVE`).

*3 dashboards* (0:42.74–0:44.76, ~2.0s) — three dashboard thumbnails build in together:
`Overview`, `Drift`, `Release Compare` — the real SigNoz dashboard titles from
`assets/dashboards/`.

*Verdict-based alert* (0:44.76–~0:45.4s) — a small bell/alert icon with the label
`verdict-changed` (the real alert rule name from `assets/alerts/verdict-changed.json`).

*Claude MCP connection* (0:45.4–0:47.06) — an arrow animates from the SigNoz dashboards
cluster to a small Claude mark, labeled `MCP` — representing SigNoz's own MCP server
(`signoz-mcp`, port 8000) that Claude Code connects to.

**Caption cards:**
- "4 real failure scenarios · 3 dashboards · verdict-based alerts."
- "Connected to **Claude** through **MCP**."

**SFX:** four quick UI ticks (scenario cards), digital click ×3 (dashboard thumbnails),
soft pulse (alert bell), whoosh (MCP arrow to Claude mark).

**⚠ Pacing flag:** this is the densest beat in the video — 9 distinct real artifacts (4
scenarios + 3 dashboards + 1 alert + 1 MCP connection) inside ~6 seconds. Sequential
one-by-one reveals would be illegible at this speed; the grouped/staggered reveals above
(scenarios as one cluster, dashboards as one cluster) are the recommended simplification
rather than compressing the animation further to fit literal sequential timing.

---

## Section 8 — Natural-Language Investigation (00:00:47,060 – 00:00:50,518)

**SRT cues 24(cont.)–26(partial):** "so engineers can investigate incidents using
natural language. Now let's see Vitals"

**Framing:** Split / Corner — deliberate use #2. Face cam returns top-left, soft
scale-in. This is the design brief's other legitimate Split case: "narration is pointing
at something on screen in real time."

**On screen:** Beside the face cam, a minimal chat/terminal-style panel shows a natural-
language query being typed against the SigNoz MCP connection from Section 7 — e.g. a
question referencing real Vitals fields (`behavior_sigma`, `service.version`). **Exact
example query text is not sourced from the repo and needs sign-off — see Confirmed
Decisions.**

**Build:** Panel soft-scale-in beside the face cam; query text types on (kinetic
typography rule: stays in the open canvas area, never over the face).

**Caption:** "Engineers investigate incidents using **natural language**."

**SFX:** UI tick per typed-text beat (light, low-mix).

---

## Section 9 — Closing Line / Cut to Live Demo (00:00:50,518 – 00:00:51,670)

**SRT cue 26(cont.)–27:** "Now let's see Vitals detect a real AI regression live."

**Framing:** Full Face Cam.

**On screen:** Split panel wipes away; back to full-frame direct address for the handoff
line — a clean, energetic beat that sets up the live demo cut.

**Caption:** "Let's see Vitals detect a real regression — **live**."

**SFX:** whoosh out, into whatever the live-demo footage brings.

**Transition out:** hard cut to un-timed live-demo screen capture (outside this SRT's
scope — see Confirmed Decisions).

---

## Framing-Mode Tally (self-check against the design brief's "actually cut" requirement)

| Section | Timespan | Mode |
|---|---|---|
| 1 | 0:00.19–0:03.81 | Full Face |
| 2 | 0:03.81–0:09.24 | Full Diagram |
| 3 | 0:09.24–0:11.95 | Split (deliberate #1) |
| 4–5 | 0:11.95–0:36.40 | Full Diagram (continuous technical explanation, internal builds only) |
| 6 | 0:36.40–0:41.01 | Full Face |
| 7 | 0:41.01–0:47.06 | Full Diagram (fast-cut) |
| 8 | 0:47.06–0:50.52 | Split (deliberate #2) |
| 9 | 0:50.52–0:51.67 | Full Face |

8 distinct segments, 7 mode transitions, 3 Full Face / 3 Full Diagram / 2 Split — Split
is used exactly twice, each time matching the brief's stated exception cases (product
reveal, on-screen pointing), not as a default resting state.

---

## Confirmed Decisions

Items resolved by best judgment below — flagging for your sign-off before this gets
built, per your instructions not to guess on specific factual claims.

1. **"13 production metrics" — narration says 13; `vitals/contract.py` defines 14
   distinct metric names** (4 cost: `vitals.cost.velocity`, `.total`,
   `vitals.tokens.input`, `.output` · 5 quality: `gen_ai.evaluation.drift`,
   `.consistency`, `.stability`, `.score`, `.drift_onset` · 5 verdict:
   `vitals.verdict.state`, `.behavior_sigma`, `.cost_sigma`, `.velocity_ratio`,
   `.samples`) — 13 if `vitals.verdict.samples` is excluded as bookkeeping rather than a
   signal. **Sidestepped in Section 4** by showing 3 grouped category chips with a single
   "13" badge instead of enumerating individual metrics, so the diagram doesn't visibly
   contradict either count — but please confirm which number is actually correct before
   this ships, since a judge could grep the repo.
2. **Verdict states shown — narration only names WARMING, STEADY, CHANGED; the real
   system has a 4th state, `INCONCLUSIVE`** (`vitals/verdict/types.py`). Resolved as: show
   only the 3 named states in Section 4 (matches audio, and "verdicts **like** WARMING,
   STEADY, and CHANGED" reads as a non-exhaustive list), then surface the real
   `INCONCLUSIVE` verdict honestly in Section 7's scenario montage (Scenario 4 / Input
   Shift's real result). Confirm this reads as consistent rather than contradictory to
   you.
3. **Section 8's natural-language MCP query text is invented**, not sourced from the repo
   (no example query is documented anywhere in the codebase or blog post). Drafted as
   something referencing real fields (`behavior_sigma`, `service.version`) rather than
   generic filler, but you should supply the actual query you plan to run in the live
   demo, or approve a specific placeholder line, before this gets animated.
4. **This file stops at SRT cue 27 (51.67s).** "Now let's see Vitals detect a real AI
   regression live" is a hard cut into what's presumably screen-recorded live-demo
   footage (replay console or live SigNoz dashboards) with no SRT timing of its own.
   Assumed this file's job ends at the handoff line and the live segment is either
   unscripted/raw footage or will get its own SRT + brief later — confirm that's correct
   rather than me inventing timed beats for a segment that doesn't exist in the source
   file yet.
5. **Section 5's baseline/drift visual is simplified** to a plain "baseline distribution
   vs current window" shape rather than literally depicting PSI (Population Stability
   Index) or CUSUM math on screen, since the real mechanism (`docs/architecture.md`) is
   statistical detail that would need its own explainer beat to render accurately in the
   ~5.6s available. Flagging per your instruction to simplify pacing rather than cram in
   an illegible-but-literal diagram.

---

## Real Component & Terminology Reference

Every named entity used above, and where it lives in the actual codebase — nothing here
is an invented placeholder.

**Pipeline components** (`docs/architecture.md`, README architecture section)
- Your AI Application — demo ships a Groq-backed RAG app, `demo/ragapp/` (FastAPI, Llama
  3.3 70B via Groq), emitting OTel `gen_ai` semantic-convention spans
- OTel Collector — user's existing collector; fans out 2 exporters (SigNoz + Vitals),
  config at `demo/collector/config.yaml`
- SigNoz Ingest — receives traces/metrics/logs from the collector, and separately
  receives Vitals' out-of-band OTLP metrics + eval/verdict logs
- Vitals Sidecar (`vitals/`) — never in the request path; OTLP/gRPC receiver
  (`vitals/ingest/receiver.py`, `mapper.py`) + Cost Engine (`vitals/cost/engine.py`) +
  Quality Engine (`vitals/quality/engine.py`, wraps vendored **spanIQ**) + Verdict
  Evaluator (`vitals/verdict/evaluator.py`) + Emitter (`vitals/emit/emitter.py`)

**Metrics** (`vitals/contract.py`, `docs/conventions.md`)
- Cost: `vitals.cost.velocity` (USD/min), `vitals.cost.total`, `vitals.tokens.input`,
  `vitals.tokens.output`
- Quality: `gen_ai.evaluation.drift` (PSI), `.consistency`, `.stability`, `.score`,
  `.drift_onset` (CUSUM alarm flag)
- Verdict: `vitals.verdict.state`, `.behavior_sigma`, `.cost_sigma`, `.velocity_ratio`,
  `.samples`
- Health (console Zone 3): spans received/scored/skipped, scopes, verdicts emitted,
  errors, uptime

**Verdict states** (`vitals/verdict/types.py`, `VerdictState` enum)
- `WARMING` — baseline window not yet full, never emits a score
- `STEADY` — within normal range
- `CHANGED` — sustained drift beyond threshold, sigma-scored
- `INCONCLUSIVE` — real 4th state, with `InconclusiveReason` of `LOW_SAMPLE`,
  `INPUT_SHIFT`, or `WARMING`

**Demo scenarios** (`demo/fixtures/`, `demo/scenarios/`, README's scenario table)
- Steady baseline — `01_steady_baseline.jsonl` → `STEADY`
- Release regression (poisoned prompt) — `02_release_regression.jsonl` → `CHANGED`
- Runaway cost loop — `03_runaway_loop.jsonl` → `CHANGED · runaway`
- User traffic topic shift — `04_input_shift.jsonl` → `INCONCLUSIVE · input shift`
- Live-traffic equivalents: `steady_traffic.py`, `deploy_v2.sh`, `runaway_loop.py`,
  `traffic_shift.py`, `reset.sh`

**SigNoz assets** (`assets/`)
- Dashboards: `overview.json` ("Vitals — Overview": Cost velocity, Cumulative burn,
  Quality score, Quality drift, Output tokens, Vitals health), `drift.json` ("Vitals —
  Drift": Drift (PSI) timeline, CUSUM drift onset, Consistency, Stability),
  `release-compare.json` ("Vitals — Release Compare": Verdict state by version, Behavior
  sigma by version, Cost sigma by version, Velocity ratio by version)
- Alert: `alerts/verdict-changed.json` — the verdict-changed alert rule

**MCP / Claude integration** (`deploy/signoz/README.md`)
- SigNoz's own MCP server, forged as the `signoz-mcp` container, HTTP transport at
  `http://localhost:8000/mcp`, deployed via Foundry (`casting.yaml`,
  `spec.mcp.spec.enabled: true`)
- Claude Code connects via `claude mcp add --scope user --transport http signoz
  http://localhost:8000/mcp`

**Console** (`vitals/console/`, localhost:8787)
- Zone 1: Hero Verdict Card (state, behavior/cost sigmas, falsifier line, worst + median
  evidence exemplars)
- Zone 2: Verdict Feed (up to 50 stored verdicts)
- Zone 3: Health Strip (live counters)

**Storage / replay**
- `vitals.db` (SQLite) — verdict history
- `vitals replay <fixture> --speed <n> --config vitals.demo.yaml` — deterministic replay
  engine, no Docker/API keys needed
