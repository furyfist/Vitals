# Vitals Technical Analysis: System Boundaries & Blind Spots

This document provides a rigorous architectural analysis of Vitals' detection boundaries, statistical trade-offs, false positive/negative failure modes, and future roadmap.

---

## 1. Mathematical & Statistical Boundaries

### 1.1 Sample Size Constraints (`n < min_samples`)
- **Boundary**: Statistical normalization (z-score calculation via Welford's algorithm) requires sufficient sample density to estimate variance accurately.
- **Trade-off**: When sample count `n < min_samples` (default 5), Vitals emits `INCONCLUSIVE (low_sample)`.
- **Impact**: Short bursts of < 5 requests cannot trigger a `CHANGED` verdict, preventing false alerts on low-traffic endpoints.

### 1.2 Reference Baseline & Cold Start Window
- **Boundary**: Vitals requires a baseline reference window (default 30 spans) to establish the healthy comparison distribution.
- **Trade-off**: During initial pipeline startup, the verdict state remains `WARMING`.
- **Impact**: An anomaly occurring during the first 30 spans of a brand new service will not be flagged until warming completes.

### 1.3 Gradual Drift vs. Sudden Release Spikes
- **Boundary**: Rolling deques (`maxlen=500`) maintain moving windows. Gradual drift occurring over days/weeks will slowly shift the baseline mean (`mu`).
- **Trade-off**: Vitals is optimized for **release regressions** (step-function drops at deploy time) and **runaway cost spikes** (sudden rate increases), not multi-month semantic drift.

---

## 2. Guard Design & False Positive Suppression

### 2.1 Guard G2: Input Co-movement (`INCONCLUSIVE(input_shift)`)
- **Problem**: When user query topics shift (e.g., users switch from asking basic product questions to complex debugging queries), response semantic distance increases naturally. A naive drift detector would falsely flag model regression.
- **Mechanism**: Guard G2 measures `input_drift` alongside `behavior_drift`. If `behavior_z >= 3.0` **AND** `input_z >= 3.0`, Vitals emits `INCONCLUSIVE (input_shift)`.
- **Outcome**: Suppresses false positive rollbacks when user traffic changes rather than model behavior.

### 2.2 Guard G3: Length Shift Caveat
- **Problem**: Model prompt changes often cause longer or shorter responses. Shortened responses reduce semantic drift space, potentially masking drift.
- **Mechanism**: Guard G3 measures `output_len` percentage change relative to baseline. If `abs(pct_change) >= 20%`, Vitals attaches caveat `output_length_X%` to the verdict while retaining detection accuracy.

---

## 3. Telemetry & Out-of-Band Pipeline Boundaries

### 3.1 Ingest Hot Path Isolation
- **Boundary**: Scoring and verdict evaluation execute entirely out-of-band on fan-out gRPC span copies.
- **Guarantee**: No failure, lock contention, or SQLite exception in Vitals can ever block user API requests or interrupt the primary SigNoz telemetry path.

### 3.2 Missing Telemetry Attributes
- **Boundary**: If a client span fails to record `gen_ai.content.completion` or token counts, `QualityEngine` gracefully skips quality scoring while `CostEngine` records zero cost.
- **Health Counter**: Increments `spans_skipped` in self-health metrics.

---

## 4. Failure Mode Matrix

| Scenario | Expected State | Cause / Reason | Explanation |
|---|---|---|---|
| New Version Release with Prompt Regression | `CHANGED` | `RELEASE` | Behavior z-score ≥ 3.0σ within 300s of deployment |
| Runaway Agent Loop (Rate ≥ 5x) | `CHANGED` | `UNATTRIBUTED` | Cost spend-rate multiplier ≥ 5.0x (bypasses 2-tick hysteresis) |
| User Traffic Topic Shift | `INCONCLUSIVE` | `INPUT_SHIFT` | Input drift ≥ 3.0σ and behavior drift ≥ 3.0σ (Guard G2) |
| Insufficient Traffic (n < 5) | `INCONCLUSIVE` | `LOW_SAMPLE` | Sample count below statistical threshold (Guard G1) |
| Output Length Shift (-25%) | `STEADY` / `CHANGED` | Caveat Attached | Output length caveat appended without corrupting z-score (Guard G3) |

---

## 5. Future Roadmap

1. **Multi-Tenant Token Isolation**: Extending `ScopeKey` to include `tenant.id` for granular B2B SaaS per-customer anomaly detection.
2. **Vector Embedding Shift Metrics**: Complementing response drift (PSI) with lightweight vector centroid distance metrics.
3. **Adaptive Sigma Floor**: Dynamic adjustment of `sigma_floor` based on baseline variance coefficient of variation.
