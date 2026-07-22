"""Frozen signal contract (PROJECT_PLAN D3) — the single source of truth for every
metric name, log attribute, and resource dimension Vitals emits.

These names implement the public `gen_ai.evaluation.*` / `vitals.cost.*` convention
proposal (see docs/conventions.md). Deviations go to DECISIONS.md, not silent edits.
"""

from __future__ import annotations

# --- Resource / dimension attributes (present on every emitted signal) ---
SERVICE_NAME = "service.name"
SERVICE_VERSION = "service.version"  # enables per-release quality/cost comparison
GEN_AI_SYSTEM = "gen_ai.system"
GEN_AI_MODEL = "gen_ai.request.model"

# --- Cost metrics (vitals.cost.*) ---
METRIC_COST_VELOCITY = "vitals.cost.velocity"  # USD/min, gauge, per service/model/version
METRIC_COST_TOTAL = "vitals.cost.total"  # USD, cumulative counter
METRIC_TOKENS_INPUT = "vitals.tokens.input"  # counter
METRIC_TOKENS_OUTPUT = "vitals.tokens.output"  # counter

# --- Quality metrics (gen_ai.evaluation.*) — the convention proposal ---
METRIC_QUALITY_DRIFT = "gen_ai.evaluation.drift"  # PSI vs healthy baseline (lower better)
METRIC_QUALITY_CONSISTENCY = "gen_ai.evaluation.consistency"
METRIC_QUALITY_STABILITY = "gen_ai.evaluation.stability"
METRIC_QUALITY_SCORE = "gen_ai.evaluation.score"  # composite 0..1 (higher better)
METRIC_DRIFT_ONSET = "gen_ai.evaluation.drift_onset"  # 1 when CUSUM alarms, else 0

# --- Vitals self-health metrics (emitted from day one, D from §9) ---
METRIC_HEALTH_SPANS_RECEIVED = "vitals.health.spans_received"
METRIC_HEALTH_SPANS_SCORED = "vitals.health.spans_scored"
METRIC_HEALTH_SPANS_SKIPPED = "vitals.health.spans_skipped"  # malformed / non-gen_ai
METRIC_HEALTH_EMIT_ERRORS = "vitals.health.emit_errors"
METRIC_HEALTH_BASELINE_STATE = "vitals.health.baseline_state"  # 0=warming, 1=ready

# --- Eval log record schema (one per scored response, trace_id-linked) ---
# SigNoz native logs<->traces correlation keys off trace_id / span_id.
LOG_ATTR_TRACE_ID = "trace_id"
LOG_ATTR_SPAN_ID = "span_id"
LOG_ATTR_DRIFT = "gen_ai.evaluation.drift"
LOG_ATTR_CONSISTENCY = "gen_ai.evaluation.consistency"
LOG_ATTR_STABILITY = "gen_ai.evaluation.stability"
LOG_ATTR_SCORE = "gen_ai.evaluation.score"
LOG_ATTR_STATE = "gen_ai.evaluation.state"  # "warming" | "scored"
LOG_ATTR_DRIFT_ONSET = "gen_ai.evaluation.drift_onset"
LOG_ATTR_REASON = "gen_ai.evaluation.reason"  # human-readable, e.g. "PSI 0.03 < 0.10"

# --- Baseline lifecycle states ---
STATE_WARMING = "warming"  # baseline window not yet full — never emit a score
STATE_SCORED = "scored"

# The instrumentation scope name stamped on all Vitals-emitted telemetry.
SCOPE_NAME = "vitals"
