import express, { Request, Response } from "express";
import { join } from "path";
import { createProxyMiddleware, Options } from "http-proxy-middleware";

const app = express();

const port: number = parseInt(process.env.CDSW_APP_PORT ?? "3000", 10);
const host: string = process.env.NODE_HOST ?? "127.0.0.1";

const lookupUrl = async (fallback: string) => {
  try {
    const res = await fetch(
      process.env.CDSW_DOMAIN +
        "/api/v2/projects/" +
        process.env.CDSW_PROJECT_ID +
        "/applications",
    );
    if (res.ok) {
      const data = await res.json();
      const application = data.find(
        (item: any) => item.name === "RagStudioMetadata",
      )?.subdomain;
      if (application) {
        return application.subdomain + "." + process.env.CDSW_DOMAIN;
      } else {
        return fallback;
      }
    } else {
      console.error("Error fetching metadata API address:", res.statusText);
      return fallback;
    }
  } catch (error) {
    console.error("Error during fetch:", error);
    return fallback;
  }
};

const apiProxy: Options = {
  target: async () => await lookupUrl("http://localhost:8080"),
  changeOrigin: true,
  pathFilter: ["/api/**"],
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
