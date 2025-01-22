import express, { Request, Response } from "express";
import { join } from "path";
import { createProxyMiddleware, Options } from "http-proxy-middleware";

const app = express();
const port: number = parseInt(process.env.CDSW_APP_PORT ?? "3000", 10);
const host: string = process.env.NODE_HOST ?? "127.0.0.1";

const apiProxy: Options = {
  target: (process.env.API_URL || "http://localhost:8080") + "/api",
  changeOrigin: true,
};

const llmServiceProxy: Options = {
  target: process.env.LLM_SERVICE_URL ?? "http://localhost:8081",
  changeOrigin: true,
};

app.use(express.static(join(__dirname, "../..", "dist")));
app.use("/api", createProxyMiddleware(apiProxy));
app.use("/llm-service", createProxyMiddleware(llmServiceProxy));

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
