"""Out-of-band OTLP emitter (D3, D4): metrics + trace_id-linked eval logs, sent
DIRECTLY to SigNoz ingest — never through the monitored collector, so vitals survives
a misbehaving user pipeline.

Metrics use observable gauges wired to provider callbacks: on each export interval the
SDK pulls the current cost/quality/health state. Eval logs are emitted per scored
response and correlate to the original trace via trace_id/span_id.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from opentelemetry._logs import SeverityNumber
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk._logs import Logger, LoggerProvider
from opentelemetry.sdk._logs._internal import LogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from vitals import contract
from vitals.cost.engine import CostSample
from vitals.quality.types import EvalLogRecord, QualityMetricSample

log = logging.getLogger(__name__)

CostProvider = Callable[[], list[CostSample]]
QualityProvider = Callable[[], list[QualityMetricSample]]
HealthProvider = Callable[[], dict[str, float]]


def _obs(value: float | None, dims: dict[str, str]) -> Observation | None:
    if value is None:
        return None
    return Observation(float(value), attributes=dims)


class Emitter:
    def __init__(
        self,
        endpoint: str,
        export_interval_ms: int,
        cost_provider: CostProvider,
        quality_provider: QualityProvider,
        health_provider: HealthProvider,
        insecure: bool = True,
    ):
        self._resource = Resource.create({"service.name": contract.SCOPE_NAME})
        self._cost_provider = cost_provider
        self._quality_provider = quality_provider
        self._health_provider = health_provider

        # --- metrics: direct OTLP gRPC to SigNoz ingest ---
        metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=insecure)
        reader = PeriodicExportingMetricReader(
            metric_exporter, export_interval_millis=export_interval_ms
        )
        self._meter_provider = MeterProvider(
            resource=self._resource, metric_readers=[reader]
        )
        meter = self._meter_provider.get_meter(contract.SCOPE_NAME)
        self._register_gauges(meter)

        # --- logs: eval records, separate OTLP log pipeline ---
        log_exporter = OTLPLogExporter(endpoint=endpoint, insecure=insecure)
        self._logger_provider = LoggerProvider(resource=self._resource)
        self._logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(log_exporter)
        )
        self._logger: Logger = self._logger_provider.get_logger(contract.SCOPE_NAME)

    # ------------------------------------------------------------------ gauges
    def _register_gauges(self, meter) -> None:
        def cost_velocity(_: CallbackOptions):
            return [
                o
                for s in self._cost_provider()
                if (o := _obs(s.velocity_usd_per_min, s.dims))
            ]

        def cost_total(_: CallbackOptions):
            return [o for s in self._cost_provider() if (o := _obs(s.total_usd, s.dims))]

        def tokens_in(_: CallbackOptions):
            return [
                Observation(float(s.input_tokens), attributes=s.dims)
                for s in self._cost_provider()
            ]

        def tokens_out(_: CallbackOptions):
            return [
                Observation(float(s.output_tokens), attributes=s.dims)
                for s in self._cost_provider()
            ]

        meter.create_observable_gauge(
            contract.METRIC_COST_VELOCITY, callbacks=[cost_velocity], unit="usd/min"
        )
        meter.create_observable_counter(
            contract.METRIC_COST_TOTAL, callbacks=[cost_total], unit="usd"
        )
        meter.create_observable_counter(
            contract.METRIC_TOKENS_INPUT, callbacks=[tokens_in], unit="{token}"
        )
        meter.create_observable_counter(
            contract.METRIC_TOKENS_OUTPUT, callbacks=[tokens_out], unit="{token}"
        )

        def q_field(getter):
            def cb(_: CallbackOptions):
                return [
                    o for s in self._quality_provider() if (o := _obs(getter(s), s.dims))
                ]

            return cb

        meter.create_observable_gauge(
            contract.METRIC_QUALITY_DRIFT, callbacks=[q_field(lambda s: s.drift)]
        )
        meter.create_observable_gauge(
            contract.METRIC_QUALITY_CONSISTENCY,
            callbacks=[q_field(lambda s: s.consistency)],
        )
        meter.create_observable_gauge(
            contract.METRIC_QUALITY_STABILITY, callbacks=[q_field(lambda s: s.stability)]
        )
        meter.create_observable_gauge(
            contract.METRIC_QUALITY_SCORE, callbacks=[q_field(lambda s: s.score)]
        )
        meter.create_observable_gauge(
            contract.METRIC_DRIFT_ONSET,
            callbacks=[q_field(lambda s: float(s.drift_onset))],
        )

        def health(_: CallbackOptions):
            return [
                Observation(v, attributes={"metric": k})
                for k, v in self._health_provider().items()
            ]

        meter.create_observable_gauge(
            "vitals.health", callbacks=[health], unit="1"
        )

    # -------------------------------------------------------------------- logs
    def emit_eval_log(self, rec: EvalLogRecord) -> None:
        attrs: dict[str, object] = dict(rec.dims)
        attrs.update(
            {
                contract.LOG_ATTR_TRACE_ID: rec.trace_id,
                contract.LOG_ATTR_SPAN_ID: rec.span_id,
                contract.LOG_ATTR_STATE: rec.state,
                contract.LOG_ATTR_DRIFT_ONSET: rec.drift_onset,
                contract.LOG_ATTR_REASON: rec.reason,
            }
        )
        for key, val in (
            (contract.LOG_ATTR_DRIFT, rec.drift),
            (contract.LOG_ATTR_CONSISTENCY, rec.consistency),
            (contract.LOG_ATTR_STABILITY, rec.stability),
            (contract.LOG_ATTR_SCORE, rec.score),
        ):
            if val is not None:
                attrs[key] = val

        try:
            trace_id_int = int(rec.trace_id, 16) if rec.trace_id else 0
            span_id_int = int(rec.span_id, 16) if rec.span_id else 0
        except ValueError:
            trace_id_int = span_id_int = 0

        record = LogRecord(
            timestamp=time.time_ns(),
            trace_id=trace_id_int,
            span_id=span_id_int,
            severity_number=SeverityNumber.INFO,
            severity_text="INFO",
            body=f"vitals eval {rec.state}: {rec.reason}",
            attributes=attrs,
        )
        self._logger.emit(record)

    def shutdown(self) -> None:
        try:
            self._meter_provider.shutdown()
            self._logger_provider.shutdown()
        except Exception:
            log.exception("vitals emitter shutdown error")
