// OpenTelemetry initialization for browser (web UI)
// Follows: https://opentelemetry.io/docs/languages/js/getting-started/browser/

import { WebTracerProvider } from "@opentelemetry/sdk-trace-web";
import {
  BatchSpanProcessor,
  ConsoleSpanExporter,
} from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { DocumentLoadInstrumentation } from "@opentelemetry/instrumentation-document-load";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";
import { XMLHttpRequestInstrumentation } from "@opentelemetry/instrumentation-xml-http-request";
// Keep import commented to show where to get semantic attributes if needed
// import { SemanticResourceAttributes } from "@opentelemetry/semantic-conventions";
import { ZoneContextManager } from "@opentelemetry/context-zone";

// Disable in unit tests unless explicitly enabled
interface ViteEnv {
  MODE: string;
  VITE_OTEL_ENABLED?: string;
  VITE_OTEL_TRACE_URL?: string;
  VITE_OTEL_CONSOLE_EXPORTER?: string;
  VITE_OTEL_TRACE_HEADERS?: string;
}
const env = import.meta.env as unknown as ViteEnv;
const isTestMode = env.MODE === "test";
const isEnabled = (env.VITE_OTEL_ENABLED ?? "true") !== "false";
if (!isTestMode && isEnabled) {
  // const serviceName = (import.meta.env.VITE_OTEL_SERVICE_NAME as string) || "rag-studio-ui";
  // const serviceVersion = (import.meta.env.VITE_OTEL_SERVICE_VERSION as string) || "1.0.0";

  // Export to an OTLP/HTTP endpoint (Collector, APM Gateway, etc.)
  // Example: VITE_OTEL_TRACE_URL="http://localhost:4318/v1/traces"
  // Point to local dev sink served by ui/express (or your collector)
  const url = env.VITE_OTEL_TRACE_URL ?? "/v1/traces";
  const headersEnv = env.VITE_OTEL_TRACE_HEADERS ?? "";
  const headers: Record<string, string> = {};
  if (headersEnv) {
    headersEnv.split(",").forEach((kv) => {
      const [k, v] = kv.split("=");
      if (k && v) headers[k.trim()] = v.trim();
    });
  }

  const exporter = new OTLPTraceExporter({ url, headers });

  // Build span processors per SDK v2 (no addSpanProcessor method)
  const spanProcessors: Array<
    import("@opentelemetry/sdk-trace-base").SpanProcessor
  > = [new BatchSpanProcessor(exporter)];
  if (env.VITE_OTEL_CONSOLE_EXPORTER === "true") {
    spanProcessors.push(new BatchSpanProcessor(new ConsoleSpanExporter()));
  }

  // Construct provider with spanProcessors
  const provider = new WebTracerProvider({ spanProcessors });

  provider.register({ contextManager: new ZoneContextManager() });

  // Auto-instrument browser events/fetch/xhr/document load
  registerInstrumentations({
    instrumentations: [
      new DocumentLoadInstrumentation(),
      new FetchInstrumentation({
        // Propagate trace headers to all same-origin and cross-origin requests by default.
        propagateTraceHeaderCorsUrls: [/.*/],
        clearTimingResources: true,
      }),
      new XMLHttpRequestInstrumentation({
        propagateTraceHeaderCorsUrls: [/.*/],
        clearTimingResources: true,
      }),
    ],
  });
}
