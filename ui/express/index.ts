import express, { Request, Response } from "express";
import cors from "cors";
import { join } from "path";
import { createProxyMiddleware, Options } from "http-proxy-middleware";

const app = express();

const port: number = parseInt(process.env.CDSW_APP_PORT ?? "3000", 10);
const host: string = process.env.NODE_HOST ?? "127.0.0.1";

app.use(
  cors({
    allowedHeaders: ["*"],
    exposedHeaders: ["*"],
    credentials: true,
    preflightContinue: true,
    origin: ["*"],
  }),
);

const apiProxy: Options = {
  target: process.env.API_URL,
  changeOrigin: true,
  pathFilter: ["/api/**"],
  secure: false,
  logger: console,
  followRedirects: true,
  headers: {
    Authorization: `Bearer ${process.env.CDSW_APIV2_KEY}`,
  },
  on: {
    proxyReq: (proxyReq, req) => {
      proxyReq.setHeader(
        "origin-remote-user",
        req.headers["remote-user"] || "unknown",
      );
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
  on: {
    proxyReq: (proxyReq, req) => {
      proxyReq.setHeader(
        "origin-remote-user",
        req.headers["remote-user"] || "unknown",
      );
    },
  },
};

app.use(express.static(join(__dirname, "../..", "dist")));
app.use(createProxyMiddleware(llmServiceProxy));
app.use(createProxyMiddleware(apiProxy));

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
      "Could not close connections in time, forcefully shutting down",
    );
    process.exit(1);
  }, 5000);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
