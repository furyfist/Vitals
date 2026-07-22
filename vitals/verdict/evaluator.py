"""Verdict Evaluator: aggregate windows, run guards G0-G3, manage state machine, select exemplars (spec §4.5, §5, §6)."""

from __future__ import annotations

import logging
import uuid
from statistics import fmean
from typing import TYPE_CHECKING

from vitals.config.settings import VerdictConfig
from vitals.verdict.attribution import attribute_change
from vitals.verdict.scope import ScopeState, SpanRecord
from vitals.verdict.types import (
    Cause,
    Exemplar,
    InconclusiveReason,
    Subject,
    Verdict,
    VerdictState,
)

if TYPE_CHECKING:
    from vitals.cost.engine import CostEngine

logger = logging.getLogger("vitals.verdict")


def select_exemplars(
    recs: list[SpanRecord],
    behavior_z: float,
    worst_count: int = 2,
    median_count: int = 1,
    signal: CalibratedSignal | None = None,
) -> tuple[Exemplar, ...]:
    """Select worst and median exemplars from span records (spec §4.5, §9)."""
    if not recs:
        return ()

    sorted_recs = sorted(recs, key=lambda r: r.behavior_psi, reverse=True)
    exemplars: list[Exemplar] = []

    def _get_sigma(r: SpanRecord) -> float:
        if signal is not None and signal.calibrated():
            return signal.z(r.behavior_psi)
        return behavior_z

    # Worst exemplars
    actual_worst_n = min(worst_count, len(sorted_recs))
    for r in sorted_recs[:actual_worst_n]:
        exemplars.append(
            Exemplar(
                kind="worst",
                trace_id=r.trace_id,
                span_id=r.span_id,
                output_excerpt=r.output_excerpt,
                behavior_sigma=_get_sigma(r),
            )
        )

    # Median exemplar (always included beside worst)
    if median_count >= 1:
        med_idx = len(sorted_recs) // 2
        med_rec = sorted_recs[med_idx]
        exemplars.append(
            Exemplar(
                kind="median",
                trace_id=med_rec.trace_id,
                span_id=med_rec.span_id,
                output_excerpt=med_rec.output_excerpt,
                behavior_sigma=_get_sigma(med_rec),
            )
        )

    return tuple(exemplars)


def evaluate_scope_version(
    scope: ScopeState,
    version: str,
    cfg: VerdictConfig,
    now: float,
    cost_engine: CostEngine | None = None,
) -> Verdict | None:
    """Evaluate one scope x version state and return a Verdict (spec §4.5)."""
    records = list(scope.windows.get(version, []))
    recs = [r for r in records if r.ts >= (now - cfg.window_s)]
    n = len(recs)

    # Guard G0: Warming check
    if not scope.is_live():
        (have, need), phase = scope.warming_progress()
        return Verdict(
            verdict_id=uuid.uuid4().hex[:16],
            ts_unix=now,
            service_name=scope.service_name,
            gen_ai_system=scope.gen_ai_system,
            model=scope.model,
            version=version,
            baseline_version=None,
            state=VerdictState.WARMING,
            subject=Subject.TIME,
            cause=Cause.NONE,
            flag_cost=False,
            flag_behavior=False,
            runaway=False,
            behavior_sigma=None,
            cost_sigma=None,
            cost_usd_per_req=None,
            baseline_cost_usd_per_req=None,
            velocity_ratio=None,
            samples=n,
            baseline_samples=need,
            onset_ts_unix=None,
            seconds_after_deploy=None,
            inconclusive_reason=InconclusiveReason.WARMING,
            caveats=(),
            falsifier="would transition to STEADY when reference and calibration finish",
            warming_progress=(have, need),
            exemplars=(),
        )

    # Aggregation & Normalization
    mean_behavior_psi = fmean([r.behavior_psi for r in recs]) if recs else 0.0
    mean_input_psi = fmean([r.input_psi for r in recs]) if recs else 0.0
    mean_cost_usd = fmean([r.usd for r in recs]) if recs else 0.0
    mean_out_len = fmean([r.out_len for r in recs]) if recs else 0.0

    behavior_z = scope.signals["behavior"].z(mean_behavior_psi)
    input_z = scope.signals["input"].z(mean_input_psi)
    cost_z = scope.signals["cost"].z(mean_cost_usd)

    current_velocity = (
        cost_engine.velocity_for(
            {
                "service.name": scope.service_name,
                "service.version": version,
                "gen_ai.system": scope.gen_ai_system,
                "gen_ai.request.model": scope.model,
            },
            now=now,
        )
        if cost_engine is not None
        else (sum(r.usd for r in recs) * (60.0 / cfg.window_s) if recs else 0.0)
    )

    baseline_cost_usd = scope.signals["cost"].mu
    baseline_velocity = (baseline_cost_usd * scope.calib_n) * (60.0 / cfg.window_s)
    velocity_ratio = (current_velocity / baseline_velocity) if baseline_velocity > 0 else None
    runaway = velocity_ratio is not None and velocity_ratio >= cfg.runaway_ratio

    # Subject selection
    baseline_version: str | None = None
    subject = Subject.TIME
    timeline = scope.version_timeline
    if len(timeline) > 1:
        matching_idx = next((i for i, (v, _) in enumerate(timeline) if v == version), None)
        if matching_idx is not None and matching_idx > 0:
            subject = Subject.RELEASE
            baseline_version = timeline[matching_idx - 1][0]

    # Guard G1: Low sample
    if n < cfg.min_samples:
        return Verdict(
            verdict_id=uuid.uuid4().hex[:16],
            ts_unix=now,
            service_name=scope.service_name,
            gen_ai_system=scope.gen_ai_system,
            model=scope.model,
            version=version,
            baseline_version=baseline_version,
            state=VerdictState.INCONCLUSIVE,
            subject=subject,
            cause=Cause.NONE,
            flag_cost=False,
            flag_behavior=False,
            runaway=False,
            behavior_sigma=behavior_z,
            cost_sigma=cost_z,
            cost_usd_per_req=mean_cost_usd,
            baseline_cost_usd_per_req=baseline_cost_usd,
            velocity_ratio=velocity_ratio,
            samples=n,
            baseline_samples=cfg.min_samples,
            onset_ts_unix=None,
            seconds_after_deploy=None,
            inconclusive_reason=InconclusiveReason.LOW_SAMPLE,
            caveats=(),
            falsifier=f"would resolve if sample size reaches {cfg.min_samples}",
            warming_progress=None,
            exemplars=select_exemplars(
                recs,
                behavior_z,
                cfg.exemplars_worst,
                cfg.exemplars_median,
                signal=scope.signals.get("behavior"),
            ),
            input_sigma=input_z,
        )

    # Guard G2: Input co-movement
    if behavior_z >= cfg.sigma_threshold and input_z >= cfg.sigma_threshold:
        return Verdict(
            verdict_id=uuid.uuid4().hex[:16],
            ts_unix=now,
            service_name=scope.service_name,
            gen_ai_system=scope.gen_ai_system,
            model=scope.model,
            version=version,
            baseline_version=baseline_version,
            state=VerdictState.INCONCLUSIVE,
            subject=subject,
            cause=Cause.NONE,
            flag_cost=False,
            flag_behavior=False,
            runaway=False,
            behavior_sigma=behavior_z,
            cost_sigma=cost_z,
            cost_usd_per_req=mean_cost_usd,
            baseline_cost_usd_per_req=baseline_cost_usd,
            velocity_ratio=velocity_ratio,
            samples=n,
            baseline_samples=cfg.min_samples,
            onset_ts_unix=None,
            seconds_after_deploy=None,
            inconclusive_reason=InconclusiveReason.INPUT_SHIFT,
            caveats=(),
            falsifier="would resolve if input drift drops below 3σ",
            warming_progress=None,
            exemplars=select_exemplars(
                recs,
                behavior_z,
                cfg.exemplars_worst,
                cfg.exemplars_median,
                signal=scope.signals.get("behavior"),
            ),
            input_sigma=input_z,
        )

    # Guard G3: Length shift caveat (D8)
    caveats_list: list[str] = []
    baseline_len = scope.signals["length"].mu
    if baseline_len > 0:
        pct_len_change = (mean_out_len - baseline_len) / baseline_len
        if abs(pct_len_change) >= cfg.length_caveat_pct:
            caveats_list.append(f"output_length_{int(round(pct_len_change * 100)):+d}%")

    # State Machine Evaluation
    cond_behavior = behavior_z >= cfg.sigma_threshold
    cond_cost = (cost_z >= cfg.sigma_threshold) or runaway
    condition = cond_behavior or cond_cost

    if condition:
        if runaway:
            next_state = VerdictState.CHANGED
            scope.consecutive_condition_ticks = cfg.consecutive_ticks
        else:
            scope.consecutive_condition_ticks += 1
            if scope.consecutive_condition_ticks >= cfg.consecutive_ticks:
                next_state = VerdictState.CHANGED
            else:
                next_state = (
                    scope.current_state
                    if scope.current_state != VerdictState.WARMING
                    else VerdictState.STEADY
                )
    else:
        scope.consecutive_condition_ticks = 0
        if scope.current_state == VerdictState.CHANGED:
            if (now - scope.state_since_ts) >= cfg.min_hold_s:
                next_state = VerdictState.STEADY
            else:
                next_state = VerdictState.CHANGED  # dwell hold
        else:
            next_state = VerdictState.STEADY

    if next_state != scope.current_state:
        scope.current_state = next_state
        scope.state_since_ts = now

    # Attribution for CHANGED state
    if next_state == VerdictState.CHANGED:
        cause, attr_baseline_ver, sec_after = attribute_change(
            scope.version_timeline, version, now, cfg.attribution_window_s
        )
        flag_behavior = cond_behavior
        flag_cost = cond_cost
        onset_ts = now
        if attr_baseline_ver:
            baseline_version = attr_baseline_ver
    else:
        cause = Cause.NONE
        flag_behavior = False
        flag_cost = False
        onset_ts = None
        sec_after = None

    # Dynamic falsifier string
    if next_state == VerdictState.CHANGED:
        if flag_behavior:
            falsifier = f"would flip to STEADY if input drift >=3σ (currently {input_z:.1f}σ)"
        else:
            falsifier = "would flip to STEADY if velocity returns within 3σ for 120s"
    else:
        falsifier = f"would flip to CHANGED at behavior >=3σ (currently {behavior_z:.1f}σ)"

    exemplars = select_exemplars(
        recs,
        behavior_z,
        cfg.exemplars_worst,
        cfg.exemplars_median,
        signal=scope.signals.get("behavior"),
    )

    return Verdict(
        verdict_id=uuid.uuid4().hex[:16],
        ts_unix=now,
        service_name=scope.service_name,
        gen_ai_system=scope.gen_ai_system,
        model=scope.model,
        version=version,
        baseline_version=baseline_version,
        state=next_state,
        subject=subject,
        cause=cause,
        flag_cost=flag_cost,
        flag_behavior=flag_behavior,
        runaway=runaway,
        behavior_sigma=behavior_z,
        cost_sigma=cost_z,
        cost_usd_per_req=mean_cost_usd,
        baseline_cost_usd_per_req=baseline_cost_usd,
        velocity_ratio=velocity_ratio,
        samples=n,
        baseline_samples=cfg.min_samples,
        onset_ts_unix=onset_ts,
        seconds_after_deploy=sec_after,
        inconclusive_reason=None,
        caveats=tuple(caveats_list),
        falsifier=falsifier,
        warming_progress=None,
        exemplars=exemplars,
        input_sigma=input_z,
    )
