"""Verdict data models, enums, and canonical sentence renderer (spec §3, §7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class VerdictState(str, Enum):
    WARMING = "warming"
    STEADY = "steady"
    CHANGED = "changed"
    INCONCLUSIVE = "inconclusive"


class Subject(str, Enum):
    TIME = "time"  # this window vs frozen reference
    RELEASE = "release"  # version B vs last STEADY version A


class Cause(str, Enum):
    RELEASE = "release"
    UNATTRIBUTED = "unattributed"
    NONE = "none"


class InconclusiveReason(str, Enum):
    LOW_SAMPLE = "low_sample"
    INPUT_SHIFT = "input_shift"
    WARMING = "warming"


@dataclass(frozen=True, slots=True)
class Exemplar:
    kind: str  # "worst" | "median"
    trace_id: str
    span_id: str
    output_excerpt: str  # <= 240 chars, whitespace-collapsed
    behavior_sigma: float


def format_sigma(z: float | None, with_flat: bool = False) -> str:
    if z is None:
        return "N/A"
    sign = "+" if z >= 0 else ""
    val_str = f"{sign}{z:.1f}σ"
    if with_flat and abs(z) < 1.0:
        return f"flat {val_str}"
    return val_str


@dataclass(frozen=True, slots=True)
class Verdict:
    verdict_id: str  # uuid4 hex, 16 chars
    ts_unix: float
    # scope
    service_name: str
    gen_ai_system: str
    model: str
    version: str  # the version under evaluation
    baseline_version: str | None
    # judgment
    state: VerdictState
    subject: Subject
    cause: Cause
    flag_cost: bool
    flag_behavior: bool
    runaway: bool  # cost velocity ratio breach
    # evidence (sigma units — D4)
    behavior_sigma: float | None
    cost_sigma: float | None
    cost_usd_per_req: float | None
    baseline_cost_usd_per_req: float | None
    velocity_ratio: float | None
    samples: int
    baseline_samples: int
    # onset & attribution
    onset_ts_unix: float | None
    seconds_after_deploy: float | None
    # honesty surface
    inconclusive_reason: InconclusiveReason | None
    caveats: tuple[str, ...]  # e.g. ("output_length_-31%",)
    falsifier: str  # "would flip to STEADY if ..."
    warming_progress: tuple[int, int] | None  # (have, need)
    exemplars: tuple[Exemplar, ...]
    input_sigma: float | None = None

    @property
    def sentence(self) -> str:
        """Render the canonical one-liner (§7)."""
        if self.state == VerdictState.WARMING:
            have, need = self.warming_progress if self.warming_progress else (0, 30)
            rem = max(0, need - have)
            est_m = int(round(rem * 2 / 60)) if rem > 0 else 0
            return (
                f"WARMING · {self.service_name} {self.version} · "
                f"collecting reference {have}/{need} · est. {est_m}m"
            )

        if self.state == VerdictState.STEADY:
            b_str = format_sigma(self.behavior_sigma)
            c_str = format_sigma(self.cost_sigma)
            return (
                f"STEADY · {self.service_name} {self.version} · "
                f"behavior {b_str} · cost {c_str} · n={self.samples}"
            )

        if self.state == VerdictState.INCONCLUSIVE:
            reason = self.inconclusive_reason.value if self.inconclusive_reason else "unknown"
            if self.inconclusive_reason == InconclusiveReason.INPUT_SHIFT:
                b_str = format_sigma(self.behavior_sigma)
                i_str = format_sigma(self.input_sigma)
                return (
                    f"INCONCLUSIVE · {reason} · behavior {b_str} but input {i_str} — "
                    f"your traffic changed, not your model · n={self.samples}"
                )
            elif self.inconclusive_reason == InconclusiveReason.LOW_SAMPLE:
                return (
                    f"INCONCLUSIVE · {reason} · sample count {self.samples} below minimum · "
                    f"n={self.samples}"
                )
            else:
                return f"INCONCLUSIVE · {reason} · n={self.samples}"

        if self.state == VerdictState.CHANGED:
            flags_list = []
            if self.flag_behavior:
                flags_list.append("behavior")
            if self.flag_cost:
                flags_list.append("cost")
            flags_str = " + ".join(flags_list) if flags_list else "change"

            parts = [f"CHANGED · {flags_str}"]

            if self.subject == Subject.RELEASE and self.baseline_version:
                parts.append(f"{self.version} vs {self.baseline_version}")

            if self.runaway and self.velocity_ratio is not None:
                parts.append(f"runaway: {int(round(self.velocity_ratio))}× baseline burn rate")
                if self.behavior_sigma is not None:
                    parts.append(f"behavior {format_sigma(self.behavior_sigma, with_flat=True)}")
            else:
                if self.flag_behavior and self.behavior_sigma is not None:
                    parts.append(f"{format_sigma(self.behavior_sigma)} (normal ±1σ)")
                elif self.behavior_sigma is not None:
                    parts.append(f"behavior {format_sigma(self.behavior_sigma, with_flat=True)}")

                if self.flag_cost and self.cost_sigma is not None:
                    parts.append(f"cost {format_sigma(self.cost_sigma)}")
                elif self.cost_sigma is not None:
                    parts.append(f"cost {format_sigma(self.cost_sigma, with_flat=True)}")

            if self.cause == Cause.RELEASE and self.onset_ts_unix is not None:
                dt_str = datetime.fromtimestamp(self.onset_ts_unix, tz=timezone.utc).strftime(
                    "%H:%M:%S"
                )
                sec_str = (
                    f"{int(round(self.seconds_after_deploy))}s"
                    if self.seconds_after_deploy is not None
                    else "0s"
                )
                parts.append(f"onset {dt_str}, {sec_str} after {self.version} deployed")
            elif self.cause == Cause.UNATTRIBUTED:
                parts.append("cause unattributed — no release in the last 5m")

            parts.append(f"n={self.samples}")
            return " · ".join(parts)

        return f"{self.state.value.upper()} · {self.service_name} {self.version} · n={self.samples}"
