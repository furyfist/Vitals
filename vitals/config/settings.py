"""vitals.yaml load + validate, with environment-variable override.

Precedence: explicit env var > vitals.yaml value > built-in default. The API keys
and endpoints stay in the environment (.env) — the yaml carries only tuning.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ReceiverConfig:
    grpc_port: int = 4327
    http_port: int = 4328
    host: str = "0.0.0.0"


@dataclass
class EmitConfig:
    # Out-of-band (D4): direct to SigNoz ingest, not through the monitored collector.
    endpoint: str = "http://localhost:4317"
    export_interval_ms: int = 5000
    queue_max: int = 10000  # bounded in-memory buffer if ingest unreachable


@dataclass
class CostConfig:
    price_table: str = "vitals/cost/prices.yaml"
    velocity_window_s: int = 60  # sliding window for USD/min rate


@dataclass
class QualityConfig:
    enabled: bool = True
    baseline_window: int = 30  # outputs collected before scoring begins (warming)
    drift_threshold: float = 0.10  # PSI pass/fail
    # CUSUM onset params (calibrated in spike S4). k = slack, h = decision threshold.
    cusum_k: float = 0.5
    cusum_h: float = 5.0
    db_path: str = "vitals.db"
    # Composite score weights (must sum to 1.0); validated below.
    weight_drift: float = 0.6
    weight_consistency: float = 0.2
    weight_stability: float = 0.2


@dataclass
class VerdictConfig:
    enabled: bool = True
    evaluate_interval_s: int = 10  # tick period
    window_s: int = 300  # current-window lookback
    window_max: int = 500  # per-version rolling record cap
    min_samples: int = 30  # G1 floor
    sigma_threshold: float = 3.0  # CHANGED entry
    consecutive_ticks: int = 2  # hysteresis (bypassed by runaway)
    min_hold_s: int = 120  # CHANGED -> STEADY dwell
    heartbeat_s: int = 60  # re-emit unchanged verdict
    runaway_ratio: float = 20.0  # velocity multiple -> immediate CHANGED
    attribution_window_s: int = 300  # deploy->onset window for RELEASE cause
    length_caveat_pct: float = 0.25  # G3 caveat trigger
    calibration_samples: int = 30  # per-signal calibration window
    exemplars_worst: int = 2
    exemplars_median: int = 1


@dataclass
class ConsoleConfig:
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8787


@dataclass
class StoreConfig:
    path: str = "vitals.db"
    retain_verdicts: int = 1000


@dataclass
class VitalsConfig:
    receiver: ReceiverConfig = field(default_factory=ReceiverConfig)
    emit: EmitConfig = field(default_factory=EmitConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    verdict: VerdictConfig = field(default_factory=VerdictConfig)
    console: ConsoleConfig = field(default_factory=ConsoleConfig)
    store: StoreConfig = field(default_factory=StoreConfig)

    def validate(self) -> None:
        q = self.quality
        total = q.weight_drift + q.weight_consistency + q.weight_stability
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"quality weights must sum to 1.0, got {total}")
        if q.baseline_window < 1:
            raise ValueError("quality.baseline_window must be >= 1")
        if self.emit.queue_max < 1:
            raise ValueError("emit.queue_max must be >= 1")

        v = self.verdict
        if v.sigma_threshold <= 0:
            raise ValueError("verdict.sigma_threshold must be > 0")
        if v.consecutive_ticks < 1:
            raise ValueError("verdict.consecutive_ticks must be >= 1")
        if v.min_samples < 5:
            raise ValueError("verdict.min_samples must be >= 5")
        if v.runaway_ratio <= 1:
            raise ValueError("verdict.runaway_ratio must be > 1")
        if v.evaluate_interval_s < 1:
            raise ValueError("verdict.evaluate_interval_s must be >= 1")
        if not (0 < v.length_caveat_pct < 1):
            raise ValueError("verdict.length_caveat_pct must be between 0 and 1")
        if v.exemplars_median < 1:
            raise ValueError("verdict.exemplars_median must be >= 1")


def _apply_env_overrides(cfg: VitalsConfig) -> None:
    if v := os.getenv("VITALS_OTLP_GRPC_PORT"):
        cfg.receiver.grpc_port = int(v)
    if v := os.getenv("VITALS_OTLP_HTTP_PORT"):
        cfg.receiver.http_port = int(v)
    if v := os.getenv("SIGNOZ_OTLP_ENDPOINT"):
        cfg.emit.endpoint = v
    if v := os.getenv("VITALS_CONSOLE_PORT"):
        cfg.console.port = int(v)
    if v := os.getenv("VITALS_CONSOLE_HOST"):
        cfg.console.host = v
    if v := os.getenv("VITALS_CONSOLE_ENABLED"):
        cfg.console.enabled = v.lower() == "true"
    if v := os.getenv("VITALS_STORE_PATH"):
        cfg.store.path = v
    if v := os.getenv("VITALS_VERDICT_ENABLED"):
        cfg.verdict.enabled = v.lower() == "true"


def load_config(path: str | os.PathLike | None = "vitals.yaml") -> VitalsConfig:
    """Load config from yaml (if present), apply env overrides, validate."""
    cfg = VitalsConfig()

    if path and Path(path).is_file():
        raw = yaml.safe_load(Path(path).read_text()) or {}
        for section, dc in (
            ("receiver", cfg.receiver),
            ("emit", cfg.emit),
            ("cost", cfg.cost),
            ("quality", cfg.quality),
            ("verdict", cfg.verdict),
            ("console", cfg.console),
            ("store", cfg.store),
        ):
            for key, value in (raw.get(section) or {}).items():
                if hasattr(dc, key):
                    setattr(dc, key, value)

    _apply_env_overrides(cfg)
    cfg.validate()
    return cfg
