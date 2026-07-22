"""`vitals run` — single entrypoint wiring the full pipeline.

    collector fan-out ─▶ OTLPReceiver ─▶ on_span ─┬─▶ CostEngine
                                                   └─▶ QualityEngine ─▶ eval log
                          Emitter (out-of-band) ◀── cost/quality/health providers ─▶ SigNoz

Quality scoring runs synchronously inside the receiver's thread pool (out of the user's
request path already — this is the fan-out copy). A misbehaving span is counted and
skipped; nothing here can affect the user's pipeline or SigNoz path.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading

from vitals import __version__
from vitals.config import load_config
from vitals.cost.engine import CostEngine
from vitals.cost.prices import PriceTable
from vitals.emit.emitter import Emitter
from vitals.health import Health
from vitals.ingest.receiver import OTLPReceiver
from vitals.model import GenAISpan

log = logging.getLogger(__name__)


def build_pipeline(config_path: str | None = "vitals.yaml"):
    cfg = load_config(config_path)
    health = Health()

    price_table = PriceTable.from_yaml(cfg.cost.price_table)
    cost_engine = CostEngine(price_table, window_s=cfg.cost.velocity_window_s)

    quality_engine = None
    if cfg.quality.enabled:
        # Imported here so the cost-only path never pays the spanIQ import cost.
        from vitals.quality.engine import QualityEngine

        quality_engine = QualityEngine(cfg.quality)

    emitter = Emitter(
        endpoint=cfg.emit.endpoint,
        export_interval_ms=cfg.emit.export_interval_ms,
        cost_provider=cost_engine.sample,
        quality_provider=(
            quality_engine.quality_samples if quality_engine else (lambda: [])
        ),
        health_provider=health.snapshot,
    )

    def on_span(span: GenAISpan) -> None:
        cost_engine.record(span)
        if quality_engine is not None:
            try:
                rec = quality_engine.score(span)
                emitter.emit_eval_log(rec)
                health.inc_scored()
                if rec.state == "scored":
                    health.set_baseline_ready(True)
            except Exception:  # noqa: BLE001 — never crash on one bad span
                log.exception("pipeline: scoring error")
                health.inc_emit_error()

    receiver = OTLPReceiver(cfg.receiver.host, cfg.receiver.grpc_port, on_span)
    health.bind_receiver_stats(receiver.stats)
    return cfg, receiver, emitter, health


def run(config_path: str | None = "vitals.yaml") -> None:
    cfg, receiver, emitter, _ = build_pipeline(config_path)
    receiver.start()
    log.info(
        "vitals %s running — receiver :%d -> emitting to %s",
        __version__, cfg.receiver.grpc_port, cfg.emit.endpoint,
    )

    stop = threading.Event()

    def _shutdown(*_):
        log.info("vitals: shutting down")
        stop.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    try:
        stop.wait()
    finally:
        receiver.stop()
        emitter.shutdown()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vitals", description="Vitals AI signal sidecar")
    sub = parser.add_subparsers(dest="command")
    run_p = sub.add_parser("run", help="start the sidecar")
    run_p.add_argument("--config", default="vitals.yaml", help="path to vitals.yaml")
    parser.add_argument("--version", action="version", version=f"vitals {__version__}")
    parser.add_argument("--log-level", default="INFO")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if args.command == "run":
        run(args.config)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
