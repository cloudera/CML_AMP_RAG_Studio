import express, { Request, Response } from "express";
import cors from "cors";
import { join } from "path";
import { createProxyMiddleware, Options } from "http-proxy-middleware";
import fs from "fs";

const app = express();

const port: number = parseInt(process.env.CDSW_APP_PORT ?? "3000", 10);
const host: string = process.env.NODE_HOST ?? "127.0.0.1";

const lookupUrl = (fileLocation: string, fallback: string): string => {
  try {
    const fileContents = fs.readFileSync(
      `../addresses/${fileLocation}`,
      "utf8",
    );
    if (fileContents) {
      return fileContents.trim();
    }
  } catch (err) {
    console.error("Error reading file:", err);
  }
  return fallback;
};

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
  // target: "http://localhost:8080",
  router: () => lookupUrl("metadata_api_address.txt", "http://localhost:8080"),
  changeOrigin: true,
  pathFilter: ["/api/**"],
  secure: false,
  protocolRewrite: "http",
  logger: console,
  followRedirects: true,
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
