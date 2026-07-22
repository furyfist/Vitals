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
class VitalsConfig:
    receiver: ReceiverConfig = field(default_factory=ReceiverConfig)
    emit: EmitConfig = field(default_factory=EmitConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)

    def validate(self) -> None:
        q = self.quality
        total = q.weight_drift + q.weight_consistency + q.weight_stability
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"quality weights must sum to 1.0, got {total}")
        if q.baseline_window < 1:
            raise ValueError("quality.baseline_window must be >= 1")
        if self.emit.queue_max < 1:
            raise ValueError("emit.queue_max must be >= 1")


def _apply_env_overrides(cfg: VitalsConfig) -> None:
    if v := os.getenv("VITALS_OTLP_GRPC_PORT"):
        cfg.receiver.grpc_port = int(v)
    if v := os.getenv("VITALS_OTLP_HTTP_PORT"):
        cfg.receiver.http_port = int(v)
    if v := os.getenv("SIGNOZ_OTLP_ENDPOINT"):
        cfg.emit.endpoint = v


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
        ):
            for key, value in (raw.get(section) or {}).items():
                if hasattr(dc, key):
                    setattr(dc, key, value)

    _apply_env_overrides(cfg)
    cfg.validate()
    return cfg
