"""`vitals run` — single entrypoint wiring the full pipeline.

    collector fan-out ─▶ OTLPReceiver ─▶ on_span ─┬─▶ CostEngine
                                                   ├─▶ QualityEngine ─▶ eval log
                                                   └─▶ ScopeState ──▶ EvaluatorThread ─▶ VerdictStore
                          Emitter (out-of-band) ◀── cost/quality/health providers ─────────────▶ SigNoz
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
import time

from vitals import __version__
from vitals.config import load_config
from vitals.cost.engine import CostEngine
from vitals.cost.prices import PriceTable
from vitals.emit.emitter import Emitter
from vitals.health import Health
from vitals.ingest.receiver import OTLPReceiver
from vitals.model import GenAISpan
from vitals.store import VerdictStore
from vitals.verdict.evaluator import evaluate_scope_version
from vitals.verdict.scope import ScopeState
from vitals.verdict.types import VerdictState

log = logging.getLogger(__name__)


class EvaluatorThread(threading.Thread):
    """Evaluator daemon thread ticking on evaluate_interval_s (spec §4.5, §13)."""

    def __init__(
        self,
        scopes: dict[tuple, ScopeState],
        store: VerdictStore,
        cfg,
        cost_engine: CostEngine,
        health: Health,
    ) -> None:
        super().__init__(name="EvaluatorThread", daemon=True)
        self._scopes = scopes
        self._store = store
        self._cfg = cfg
        self._cost_engine = cost_engine
        self._health = health
        self._stop_event = threading.Event()
        self._last_emitted_ts: dict[tuple[tuple, str], float] = {}

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            self._tick(now)
            self._stop_event.wait(float(self._cfg.evaluate_interval_s))

    def _tick(self, now: float) -> None:
        for scope_key, scope in list(self._scopes.items()):
            try:
                versions = list(scope.windows.keys())
                if not versions and scope.version_timeline:
                    versions = [v for v, _ in scope.version_timeline]
                if not versions:
                    versions = ["v1"]

                for ver in versions:
                    verdict = evaluate_scope_version(
                        scope, ver, self._cfg, now, self._cost_engine
                    )
                    if verdict is None:
                        continue

                    key = (scope_key, ver)
                    last_v = scope.last_verdict
                    last_ts = self._last_emitted_ts.get(key, 0.0)

                    should_emit = False
                    if last_v is None:
                        should_emit = True
                    elif verdict.state != last_v.state:
                        should_emit = True
                    elif verdict.state == VerdictState.CHANGED:
                        b_curr = verdict.behavior_sigma or 0.0
                        b_prev = last_v.behavior_sigma or 0.0
                        if abs(b_curr - b_prev) >= 1.0:
                            should_emit = True
                    elif (now - last_ts) >= self._cfg.heartbeat_s:
                        should_emit = True

                    if should_emit:
                        scope.last_verdict = verdict
                        self._last_emitted_ts[key] = now
                        self._store.insert(verdict)
                        self._health.inc_verdicts_emitted()

                        if verdict.state == VerdictState.CHANGED:
                            log.warning("%s", verdict.sentence)
                        else:
                            log.info("%s", verdict.sentence)
            except Exception:  # noqa: BLE001 — a failing scope must never stop the tick
                log.exception("evaluator: error processing scope %s", scope_key)


def build_pipeline(config_path: str | None = "vitals.yaml"):
    cfg = load_config(config_path)
    health = Health()

    price_table = PriceTable.from_yaml(cfg.cost.price_table)
    cost_engine = CostEngine(price_table, window_s=cfg.cost.velocity_window_s)

    quality_engine = None
    if cfg.quality.enabled:
        from vitals.quality.engine import QualityEngine

        quality_engine = QualityEngine(cfg.quality)

    store = VerdictStore(cfg.store.path, cfg.store.retain_verdicts)
    scopes: dict[tuple, ScopeState] = {}
    scopes_lock = threading.Lock()

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
        usd = price_table.cost_usd(span.model, span.input_tokens, span.output_tokens)

        key = (span.service_name, span.gen_ai_system, span.model)
        with scopes_lock:
            scope = scopes.get(key)
            if scope is None:
                scope = ScopeState(
                    service_name=span.service_name,
                    gen_ai_system=span.gen_ai_system,
                    model=span.model,
                    reference_window=cfg.quality.baseline_window,
                    calib_n=cfg.verdict.calibration_samples,
                    window_max=cfg.verdict.window_max,
                )
                scopes[key] = scope
                health.set_scopes(len(scopes))

        if quality_engine is not None:
            try:
                rec = quality_engine.score(span)
                scope.observe(span, rec, usd)
                emitter.emit_eval_log(rec)
                health.inc_scored()
                if rec.state == "scored":
                    health.set_baseline_ready(True)
            except Exception:  # noqa: BLE001 — never crash on one bad span
                log.exception("pipeline: scoring error")
                health.inc_emit_error()

    evaluator = None
    if cfg.verdict.enabled:
        evaluator = EvaluatorThread(scopes, store, cfg.verdict, cost_engine, health)

    receiver = OTLPReceiver(cfg.receiver.host, cfg.receiver.grpc_port, on_span)
    health.bind_receiver_stats(receiver.stats)
    return cfg, receiver, emitter, health, store, evaluator


def run(config_path: str | None = "vitals.yaml") -> None:
    cfg, receiver, emitter, _, store, evaluator = build_pipeline(config_path)
    receiver.start()
    if evaluator is not None:
        evaluator.start()

    log.info(
        "vitals %s running — receiver :%d -> emitting to %s",
        __version__,
        cfg.receiver.grpc_port,
        cfg.emit.endpoint,
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
        if evaluator is not None:
            evaluator.stop()
            evaluator.join(timeout=2.0)
        emitter.shutdown()
        store.close()


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
