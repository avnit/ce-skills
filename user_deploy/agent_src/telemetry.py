import os
import re
import json
import logging
import functools
import inspect
import google.auth
from google.auth.transport.grpc import AuthMetadataPlugin
from google.auth.transport.requests import Request
import grpc

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# Auto-instrumentation imports
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.langchain import LangchainInstrumentor

logger = logging.getLogger("agent_telemetry")
_initialized = False

class CredentialRedactingSpanProcessor(SpanProcessor):
    """SpanProcessor to scrub secret keys and runtime credentials from span attributes."""
    _REDACT_KEYS = frozenset({"_runtime_credentials", "api_key", "token", "authorization", "password"})

    def on_end(self, span) -> None:
        attrs = getattr(span, "attributes", None)
        if not attrs:
            return
        for key, val in attrs.items():
            if not isinstance(val, str):
                continue
            # Look for matching sensitive keys
            if any(k in key.lower() or k in val.lower() for k in self._REDACT_KEYS):
                attrs[key] = "[REDACTED]"

def set_opentelemetry(service_name: str) -> None:
    """Wheres up direct OpenTelemetry OTLP export channel using local Application Default Credentials."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    os.environ["OTEL_SERVICE_NAME"] = service_name

    # Resolve Application Default Credentials (ADC)
    gcp_creds, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    # Define standard service resource
    service_resource = Resource.create({
        SERVICE_NAME: service_name,
        "gcp.project_id": project_id,
    })

    # Build composite SSL channel credentials with GCP OAuth Token Provider
    auth_plugin = AuthMetadataPlugin(credentials=gcp_creds, request=Request())
    grpc_channel_creds = grpc.composite_channel_credentials(
        grpc.ssl_channel_credentials(),
        grpc.metadata_call_credentials(auth_plugin),
    )

    try:
        # Initialize Trace Stack
        tracer_provider = TracerProvider(resource=service_resource)
        
        # 1. Register Credential Scrubbing Processor
        tracer_provider.add_span_processor(CredentialRedactingSpanProcessor())
        
        # 2. Register gRPC Direct OTLP Exporter to Cloud Trace
        trace_exporter = OTLPSpanExporter(
            credentials=grpc_channel_creds,
            endpoint="telemetry.googleapis.com:443",
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        logger.info("OpenTelemetry Trace exporter initialized successfully.")
    except Exception as exc:
        logger.warning("Trace export setup failed: %s. Telemetry will operate in-memory.", exc)
        trace.set_tracer_provider(TracerProvider(resource=service_resource))

    # Wheres up common library instrumentations
    for instrumentor, name in (
        (HTTPXClientInstrumentor, "httpx"),
        (LangchainInstrumentor, "langchain"),
    ):
        try:
            instrumentor().instrument()
            logger.info("Auto-instrumented client library: %s", name)
        except Exception as exc:
            logger.warning("Skipped instrumentation for %s: %s", name, exc)

def do_trace(fn=None, *, span_name=None):
    """Decorator to instrument custom sync and async agent execution paths with OTel Spans."""
    def decorator(f):
        @functools.wraps(f)
        async def _async_wrap(*args, **kwargs):
            tracer = trace.get_tracer(f.__module__)
            active_span_name = span_name or f"{f.__name__}"
            with tracer.start_as_current_span(active_span_name) as current_span:
                current_span.set_attribute("code.function", f.__name__)
                current_span.set_attribute("code.module", f.__module__)
                try:
                    return_value = await f(*args, **kwargs)
                    current_span.set_status(trace.Status(trace.StatusCode.OK))
                    if return_value is not None:
                        current_span.set_attribute("query.response", str(return_value)[:1000])
                    return return_value
                except Exception as exc:
                    current_span.record_exception(exc)
                    current_span.set_status(trace.Status(trace.StatusCode.ERROR))
                    raise

        @functools.wraps(f)
        def _sync_wrap(*args, **kwargs):
            tracer = trace.get_tracer(f.__module__)
            active_span_name = span_name or f"{f.__name__}"
            with tracer.start_as_current_span(active_span_name) as current_span:
                current_span.set_attribute("code.function", f.__name__)
                current_span.set_attribute("code.module", f.__module__)
                try:
                    return_value = f(*args, **kwargs)
                    current_span.set_status(trace.Status(trace.StatusCode.OK))
                    if return_value is not None:
                        current_span.set_attribute("query.response", str(return_value)[:1000])
                    return return_value
                except Exception as exc:
                    current_span.record_exception(exc)
                    current_span.set_status(trace.Status(trace.StatusCode.ERROR))
                    raise

        if inspect.iscoroutinefunction(f):
            return _async_wrap
        return _sync_wrap

    if fn is None:
        return decorator
    return decorator(fn)
