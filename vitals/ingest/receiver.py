"""OTLP/gRPC trace receiver: the fan-out target for the user's collector (D1, S1).

Implements the OTLP TraceService. Each exported span is converted to an attribute
dict, mapped to a GenAISpan, and handed to the pipeline callback. Malformed spans are
counted and skipped — the receiver never raises back to the exporter.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent import futures

import grpc
from opentelemetry.proto.collector.trace.v1 import (
    trace_service_pb2,
    trace_service_pb2_grpc,
)
from opentelemetry.proto.common.v1 import common_pb2

from vitals.ingest.mapper import MapStats, map_span
from vitals.model import GenAISpan

log = logging.getLogger(__name__)

SpanCallback = Callable[[GenAISpan], None]


def _anyvalue(v: common_pb2.AnyValue):
    """Unwrap an OTLP AnyValue into a Python scalar/str."""
    which = v.WhichOneof("value")
    if which is None:
        return None
    if which == "string_value":
        return v.string_value
    if which == "int_value":
        return v.int_value
    if which == "double_value":
        return v.double_value
    if which == "bool_value":
        return v.bool_value
    if which == "array_value":
        return [_anyvalue(x) for x in v.array_value.values]
    # kvlist / bytes — stringify for content extraction robustness
    return str(getattr(v, which))


def _attrs(kv_list) -> dict:
    return {kv.key: _anyvalue(kv.value) for kv in kv_list}


class _TraceService(trace_service_pb2_grpc.TraceServiceServicer):
    def __init__(self, on_span: SpanCallback, stats: MapStats):
        self._on_span = on_span
        self._stats = stats

    def Export(self, request, context):  # noqa: N802 (gRPC method name)
        try:
            self._handle(request)
        except Exception:  # defensive: never fail the exporter
            log.exception("vitals receiver: error handling export batch")
        return trace_service_pb2.ExportTraceServiceResponse()

    def _handle(self, request) -> None:
        for rs in request.resource_spans:
            resource_attrs = _attrs(rs.resource.attributes)
            for ss in rs.scope_spans:
                for span in ss.spans:
                    span_attrs = _attrs(span.attributes)
                    gspan = map_span(
                        span_attrs=span_attrs,
                        resource_attrs=resource_attrs,
                        trace_id=span.trace_id.hex(),
                        span_id=span.span_id.hex(),
                        start_unix_nano=span.start_time_unix_nano,
                        end_unix_nano=span.end_time_unix_nano,
                        stats=self._stats,
                    )
                    if gspan is not None:
                        self._on_span(gspan)


class OTLPReceiver:
    """gRPC OTLP trace receiver running on a background thread pool."""

    def __init__(self, host: str, grpc_port: int, on_span: SpanCallback):
        self.host = host
        self.grpc_port = grpc_port
        self.stats = MapStats()
        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        trace_service_pb2_grpc.add_TraceServiceServicer_to_server(
            _TraceService(on_span, self.stats), self._server
        )
        self._server.add_insecure_port(f"{host}:{grpc_port}")

    def start(self) -> None:
        self._server.start()
        log.info("vitals OTLP receiver listening on %s:%d", self.host, self.grpc_port)

    def stop(self, grace: float = 2.0) -> None:
        self._server.stop(grace)

    def wait(self) -> None:
        self._server.wait_for_termination()
