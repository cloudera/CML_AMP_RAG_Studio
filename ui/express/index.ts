import express, { Request, Response, RequestHandler } from "express";
import cors from "cors";
import { join } from "path";
import { createProxyMiddleware, Options } from "http-proxy-middleware";
import { IncomingMessage, ServerResponse } from "node:http";
import { Socket } from "node:net";
import fs from "node:fs";

const app = express();

const port: number = parseInt(process.env.CDSW_APP_PORT ?? "3000", 10);
const host: string = process.env.NODE_HOST ?? "127.0.0.1";

const allowedOrigins = [
  "http://localhost:5173",
  "http://127.0.0.1:5173",
  "http://localhost:3000",
  "http://127.0.0.1:3000",
];
app.use(
  cors({
    origin: allowedOrigins,
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: [
      "Content-Type",
      "traceparent",
      "tracestate",
      "b3",
      "x-requested-with",
    ],
    maxAge: 86400,
  })
);
// Explicit preflight for OTLP endpoint
app.options("/v1/traces", cors({ origin: allowedOrigins }));
// Explicit per-route CORS headers for OTLP traces
const tracesCorsHandler: RequestHandler = (req, res, next) => {
  const origin = req.headers["origin"] as string | undefined;
  res.header("x-trace-sink", "ui-express");
  if (origin && allowedOrigins.includes(origin)) {
    res.header("Access-Control-Allow-Origin", origin);
    res.header("Vary", "Origin");
    res.header("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.header(
      "Access-Control-Allow-Headers",
      "Content-Type, traceparent, tracestate, b3, x-requested-with"
    );
    res.header("Access-Control-Max-Age", "86400");
    if (req.method === "OPTIONS") {
      res.sendStatus(204);
      return;
    }
  }
  next();
};
app.use("/v1/traces", tracesCorsHandler);
// Accept raw OTLP bodies only for the tracing endpoint; keep other routes unaffected
app.use("/v1/traces", express.raw({ type: "*/*", limit: "10mb" }));

const apiProxy: Options = {
  target: process.env.API_URL ?? "http://localhost:8080",
  changeOrigin: true,
  pathFilter: ["/api/**"],
  secure: false,
  xfwd: true,
  headers: {
    Authorization: `Bearer ${process.env.CDSW_APIV2_KEY}`,
  },
  on: {
    error: (
      err: Error,
      req: IncomingMessage,
      res: ServerResponse<IncomingMessage> | Socket
    ) => {
      console.error("API Proxy Error:", err);
      console.error("API Error Request URL:", req.url);

      if (res instanceof Socket) {
        console.error("Response is a Socket, not a ServerResponse.");
        return res.end("Something went wrong.");
      }

      // Only return 502 for service unavailability errors
      const isServiceUnavailable = [
        "ECONNREFUSED",
        "ENOTFOUND",
        "ETIMEDOUT",
        "ECONNRESET",
        "EHOSTUNREACH",
        "ENETUNREACH",
      ].some((code) => err.stack?.includes(code));

      if (isServiceUnavailable) {
        res.writeHead(502, {
          "Content-Type": "application/json",
        });
        return res.end(
          JSON.stringify({
            error: "Service Unavailable",
            message:
              "API service is currently unavailable. Please try again later.",
            details: err.message,
            timestamp: new Date().toISOString(),
          })
        );
      }
      return res;
    },
  },
};

const llmServiceProxy: Options = {
  target: process.env.LLM_SERVICE_URL ?? "http://localhost:8081",
  changeOrigin: true,
  pathFilter: ["/llm-service/**"],
  pathRewrite: {
    "^/llm-service": "",
  },
};

app.use(express.static(join(__dirname, "../..", "dist")));
app.use(createProxyMiddleware(llmServiceProxy));
app.use(createProxyMiddleware(apiProxy));

// OTLP/HTTP trace sink: CORS-safe endpoint that forwards to the collector and logs locally
const tracesForwardHandler: RequestHandler = (req: Request, res: Response) => {
  const contentType =
    (req.headers["content-type"] as string) ?? "application/json";
  const buf: Buffer = Buffer.isBuffer(req.body)
    ? (req.body as Buffer)
    : Buffer.from(JSON.stringify(req.body ?? {}), "utf8");

  // Always append to local log for visibility
  try {
    const logPath =
      process.env.OTEL_TRACE_LOG_FILE ?? join(__dirname, "../..", "traces.log");
    const entry = {
      ts: new Date().toISOString(),
      contentType,
      size: buf.byteLength,
    };
    fs.appendFileSync(logPath, JSON.stringify(entry) + "\n", {
      encoding: "utf8",
    });
  } catch (e) {
    console.warn("Failed to append local traces.log:", e);
  }

  // Forward to collector (optional but preferred for Grafana/Tempo)
  const collectorUrl =
    process.env.OTEL_COLLECTOR_URL ?? "http://127.0.0.1:4318/v1/traces";
  (async () => {
    try {
      const resp = await fetch(collectorUrl, {
        method: "POST",
        headers: { "content-type": contentType },
        body: buf,
      });
      if (!resp.ok) {
        const text = await resp.text().catch(() => "");
        console.error("Collector forward failed:", resp.status, text);
        res.status(502).send("collector error");
        return;
      }
      res.status(200).send("ok");
    } catch (e) {
      console.error("Failed to forward to collector:", collectorUrl, e);
      // still OK for the UI exporter; we've logged locally
      res.status(200).send("ok");
    }
  })();
};
app.post("/v1/traces", tracesForwardHandler);

app.get("*", (req: Request, res: Response) => {
  console.log("Serving up req.url: ", req.url);
  res.sendFile(join(__dirname, "../..", "dist", "index.html"));
  console.log("Served up req.url: ", req.url);
});

const server = app.listen(port, host, () => {
  console.log(`Node proxy listening on host:port ${host}:${port}`);
});

function shutdown() {
  console.log("termination signal received: closing HTTP server");
  server.close(() => {
    process.exit(0);
  });
  setTimeout(() => {
    console.error(
      "Could not close connections in time, forcefully shutting down"
    );
    process.exit(1);
  }, 5000);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
