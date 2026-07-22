"""`vitals run` — single entrypoint wiring the full pipeline.

    collector fan-out ─▶ OTLPReceiver ─▶ on_span ─┬─▶ CostEngine
                                                   ├─▶ QualityEngine ─▶ eval log
                                                   └─▶ ScopeState ──▶ EvaluatorThread ─▶ VerdictStore ──▶ ConsoleServer (:8787)
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
from vitals.console import create_console_server
from vitals.cost.engine import CostEngine
from vitals.cost.prices import PriceTable
from vitals.emit.emitter import Emitter
from vitals.health import Health
from vitals.ingest.receiver import OTLPReceiver
from vitals.model import GenAISpan
from vitals.replay import read_fixture, run_replay, write_fixture
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
        emitter: Emitter | None = None,
        verdict_snapshot: dict | None = None,
    ) -> None:
        super().__init__(name="EvaluatorThread", daemon=True)
        self._scopes = scopes
        self._store = store
        self._cfg = cfg
        self._cost_engine = cost_engine
        self._health = health
        self._emitter = emitter
        self._verdict_snapshot = verdict_snapshot if verdict_snapshot is not None else {}
        self._stop_event = threading.Event()
        self._last_emitted_ts: dict[tuple[tuple, str], float] = {}

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                now = time.time()
                self._tick(now)
            except Exception:  # noqa: BLE001
                log.exception("evaluator: unhandled error during tick")
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
                        self._verdict_snapshot[key] = verdict
                        self._store.insert(verdict)
                        self._health.inc_verdicts_emitted()

                        if self._emitter is not None:
                            try:
                                self._emitter.emit_verdict_log(verdict)
                            except Exception:  # noqa: BLE001
                                log.exception("evaluator: error emitting verdict log")
                                self._health.inc_emit_error()

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
    verdict_snapshot: dict[tuple, Verdict] = {}

    emitter = Emitter(
        endpoint=cfg.emit.endpoint,
        export_interval_ms=cfg.emit.export_interval_ms,
        cost_provider=cost_engine.sample,
        quality_provider=(
            quality_engine.quality_samples if quality_engine else (lambda: [])
        ),
        health_provider=health.snapshot,
        verdict_provider=lambda: list(verdict_snapshot.values()),
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
        evaluator = EvaluatorThread(
            scopes, store, cfg.verdict, cost_engine, health, emitter, verdict_snapshot
        )

    console_server = None
    if cfg.console.enabled:
        console_server = create_console_server(
            cfg.console.host, cfg.console.port, store, scopes, health
        )

    receiver = OTLPReceiver(cfg.receiver.host, cfg.receiver.grpc_port, on_span)
    health.bind_receiver_stats(receiver.stats)
    return cfg, receiver, emitter, health, store, evaluator, console_server, on_span


def run(config_path: str | None = "vitals.yaml") -> None:
    cfg, receiver, emitter, _, store, evaluator, console_server, _ = build_pipeline(config_path)
    receiver.start()
    if evaluator is not None:
        evaluator.start()

    if console_server is not None:
        console_thread = threading.Thread(target=console_server.serve_forever, daemon=True)
        console_thread.start()

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
        if console_server is not None:
            console_server.shutdown()
            console_server.server_close()
        emitter.shutdown()
        store.close()


def record_cmd(out_path: str, config_path: str | None = "vitals.yaml") -> None:
    """Record mapped GenAISpans to JSONL fixture file (spec §D6, §18)."""
    cfg = load_config(config_path)
    spans_recorded: list[tuple[GenAISpan, float]] = []
    start_ts = time.time()
    lock = threading.Lock()

    def on_span(span: GenAISpan) -> None:
        with lock:
            rel_ts = time.time() - start_ts
            spans_recorded.append((span, rel_ts))
            log.info("recorded span #%d from %s", len(spans_recorded), span.service_name)

    receiver = OTLPReceiver(cfg.receiver.host, cfg.receiver.grpc_port, on_span)
    receiver.start()
    log.info("vitals record running on :%d — recording to %s", cfg.receiver.grpc_port, out_path)

    stop = threading.Event()

    def _shutdown(*_):
        stop.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    try:
        stop.wait()
    finally:
        receiver.stop()
        with lock:
            write_fixture(out_path, spans_recorded)
            log.info("Saved %d spans to %s", len(spans_recorded), out_path)


def replay_cmd(
    fixture_path: str, speed: float = 1.0, config_path: str | None = "vitals.yaml"
) -> None:
    """Replay mapped GenAISpans from JSONL fixture file (spec §D6, §18)."""
    cfg, _, emitter, _, store, evaluator, console_server, on_span_cb = build_pipeline(config_path)
    if evaluator is not None:
        evaluator.start()

    if console_server is not None:
        console_thread = threading.Thread(target=console_server.serve_forever, daemon=True)
        console_thread.start()

    try:
        n = run_replay(fixture_path, speed=speed, on_span_cb=lambda span, _: on_span_cb(span))
        log.info("Replay completed: %d spans processed", n)
        # Give evaluator time for final tick if needed
        time.sleep(1.0)
    finally:
        if evaluator is not None:
            evaluator.stop()
            evaluator.join(timeout=2.0)
        if console_server is not None:
            console_server.shutdown()
            console_server.server_close()
        emitter.shutdown()
        store.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vitals", description="Vitals AI signal sidecar")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="start the sidecar")
    run_p.add_argument("--config", default="vitals.yaml", help="path to vitals.yaml")

    rec_p = sub.add_parser("record", help="record spans to JSONL fixture")
    rec_p.add_argument("--out", required=True, help="output JSONL path")
    rec_p.add_argument("--config", default="vitals.yaml", help="path to vitals.yaml")

    rep_p = sub.add_parser("replay", help="replay spans from JSONL fixture")
    rep_p.add_argument("fixture", help="path to JSONL fixture file")
    rep_p.add_argument("--speed", type=float, default=1.0, help="replay speed factor")
    rep_p.add_argument("--config", default="vitals.yaml", help="path to vitals.yaml")

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

    if args.command == "record":
        record_cmd(args.out, args.config)
        return 0

    if args.command == "replay":
        replay_cmd(args.fixture, args.speed, args.config)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
