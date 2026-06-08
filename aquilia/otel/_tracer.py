"""
AquiliaTracer — thin wrapper around the OTel TracerProvider.

Falls back to a no-op tracer when OTel is not installed or not configured,
so framework code can unconditionally call ``get_tracer()`` without
guarding on availability.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aquilia._version import __version__

if TYPE_CHECKING:
    pass

logger = logging.getLogger("aquilia.otel")

_TRACER: Any = None
_PROVIDER: Any = None
_CONFIGURED = False


def _noop_tracer() -> Any:
    try:
        from opentelemetry.trace import NoOpTracer

        return NoOpTracer()
    except ImportError:
        return _NoOpTracerFallback()


class _NoOpTracerFallback:
    def start_as_current_span(self, name: str, **_: Any):
        import contextlib

        return contextlib.nullcontext()

    def start_span(self, name: str, **_: Any):
        return _NoOpSpan()


class _NoOpSpan:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def set_attribute(self, *_):
        pass

    def record_exception(self, *_):
        pass

    def set_status(self, *_):
        pass

    def end(self):
        pass


def setup(config: Any) -> None:
    global _TRACER, _PROVIDER, _CONFIGURED

    try:
        from opentelemetry import trace
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.propagators.composite import CompositePropagator
        from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "opentelemetry-sdk not installed. OTel tracing disabled. Install with: pip install aquilia[otel]"
        )
        _TRACER = _noop_tracer()
        _CONFIGURED = True
        return

    service_version = config.service_version or __version__
    resource_attrs = {
        SERVICE_NAME: config.service_name,
        SERVICE_VERSION: service_version,
        **config.resource_attrs,
    }
    resource = Resource.create(resource_attrs)
    provider = TracerProvider(resource=resource)

    if config.otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTel OTLP exporter configured: %s", config.otlp_endpoint)
        except ImportError:
            logger.warning(
                "opentelemetry-exporter-otlp-proto-grpc not installed. "
                "Traces will not be exported. Install with: pip install aquilia[otel]"
            )

    try:
        propagators = []
        for name in config.propagators:
            if name == "tracecontext":
                from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

                propagators.append(TraceContextTextMapPropagator())
            elif name == "baggage":
                from opentelemetry.baggage.propagation import W3CBaggagePropagator

                propagators.append(W3CBaggagePropagator())
        if propagators:
            set_global_textmap(CompositePropagator(propagators))
    except Exception as exc:
        logger.warning("Failed to configure OTel propagators: %s", exc)

    trace.set_tracer_provider(provider)
    _PROVIDER = provider
    _TRACER = provider.get_tracer("aquilia", __version__)
    _CONFIGURED = True
    logger.info("OTel tracing configured for service: %s", config.service_name)


def get_tracer() -> Any:
    global _TRACER
    if _TRACER is None:
        _TRACER = _noop_tracer()
    return _TRACER


def shutdown() -> None:
    global _PROVIDER
    if _PROVIDER is not None:
        try:
            _PROVIDER.shutdown()
        except Exception as exc:
            logger.warning("OTel provider shutdown error: %s", exc)
        _PROVIDER = None
