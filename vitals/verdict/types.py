"""Verdict data models, enums, and canonical sentence renderer (spec §3, §7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


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

    def to_dict(self) -> dict[str, Any]:
        """Serialize Verdict to a JSON-compatible dictionary."""
        return {
            "verdict_id": self.verdict_id,
            "ts_unix": self.ts_unix,
            "service_name": self.service_name,
            "gen_ai_system": self.gen_ai_system,
            "model": self.model,
            "version": self.version,
            "baseline_version": self.baseline_version,
            "state": self.state.value,
            "subject": self.subject.value,
            "cause": self.cause.value,
            "flag_cost": self.flag_cost,
            "flag_behavior": self.flag_behavior,
            "runaway": self.runaway,
            "behavior_sigma": self.behavior_sigma,
            "cost_sigma": self.cost_sigma,
            "cost_usd_per_req": self.cost_usd_per_req,
            "baseline_cost_usd_per_req": self.baseline_cost_usd_per_req,
            "velocity_ratio": self.velocity_ratio,
            "samples": self.samples,
            "baseline_samples": self.baseline_samples,
            "onset_ts_unix": self.onset_ts_unix,
            "seconds_after_deploy": self.seconds_after_deploy,
            "inconclusive_reason": (
                self.inconclusive_reason.value if self.inconclusive_reason else None
            ),
            "caveats": list(self.caveats),
            "falsifier": self.falsifier,
            "warming_progress": list(self.warming_progress) if self.warming_progress else None,
            "exemplars": [
                {
                    "kind": ex.kind,
                    "trace_id": ex.trace_id,
                    "span_id": ex.span_id,
                    "output_excerpt": ex.output_excerpt,
                    "behavior_sigma": ex.behavior_sigma,
                }
                for ex in self.exemplars
            ],
            "input_sigma": self.input_sigma,
            "sentence": self.sentence,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Verdict:
        """Deserialize Verdict from a dictionary."""
        exemplars = tuple(
            Exemplar(
                kind=ex["kind"],
                trace_id=ex["trace_id"],
                span_id=ex["span_id"],
                output_excerpt=ex["output_excerpt"],
                behavior_sigma=float(ex["behavior_sigma"]),
            )
            for ex in d.get("exemplars", [])
        )
        inc_reason = (
            InconclusiveReason(d["inconclusive_reason"])
            if d.get("inconclusive_reason")
            else None
        )
        wp = tuple(d["warming_progress"]) if d.get("warming_progress") is not None else None
        return cls(
            verdict_id=d["verdict_id"],
            ts_unix=float(d["ts_unix"]),
            service_name=d["service_name"],
            gen_ai_system=d["gen_ai_system"],
            model=d["model"],
            version=d["version"],
            baseline_version=d.get("baseline_version"),
            state=VerdictState(d["state"]),
            subject=Subject(d["subject"]),
            cause=Cause(d["cause"]),
            flag_cost=bool(d["flag_cost"]),
            flag_behavior=bool(d["flag_behavior"]),
            runaway=bool(d["runaway"]),
            behavior_sigma=(
                float(d["behavior_sigma"]) if d.get("behavior_sigma") is not None else None
            ),
            cost_sigma=float(d["cost_sigma"]) if d.get("cost_sigma") is not None else None,
            cost_usd_per_req=(
                float(d["cost_usd_per_req"]) if d.get("cost_usd_per_req") is not None else None
            ),
            baseline_cost_usd_per_req=(
                float(d["baseline_cost_usd_per_req"])
                if d.get("baseline_cost_usd_per_req") is not None
                else None
            ),
            velocity_ratio=(
                float(d["velocity_ratio"]) if d.get("velocity_ratio") is not None else None
            ),
            samples=int(d["samples"]),
            baseline_samples=int(d["baseline_samples"]),
            onset_ts_unix=(
                float(d["onset_ts_unix"]) if d.get("onset_ts_unix") is not None else None
            ),
            seconds_after_deploy=(
                float(d["seconds_after_deploy"])
                if d.get("seconds_after_deploy") is not None
                else None
            ),
            inconclusive_reason=inc_reason,
            caveats=tuple(d.get("caveats", ())),
            falsifier=d.get("falsifier", ""),
            warming_progress=wp,
            exemplars=exemplars,
            input_sigma=float(d["input_sigma"]) if d.get("input_sigma") is not None else None,
        )

