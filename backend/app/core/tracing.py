"""OpenTelemetry 链路追踪初始化（推送到 Jaeger OTLP）。

- 仅当 otel_enabled=True 且端点可解析时才启用，失败降级为无迹（不阻塞业务）。
- 在 main.py 的 lifespan 启动时调用 init_tracing()。
"""

import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


def init_tracing() -> None:
    if not settings.otel_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info("OpenTelemetry tracing 已启用，推送端点：%s", settings.otel_exporter_otlp_endpoint)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenTelemetry 初始化失败（降级为无迹）：%s", exc)