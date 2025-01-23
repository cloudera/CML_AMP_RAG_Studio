"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
var _a, _b, _c;
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const path_1 = require("path");
const http_proxy_middleware_1 = require("http-proxy-middleware");
const swagger_ui_express_1 = __importDefault(require("swagger-ui-express"));
const api_json_1 = __importDefault(require("./api.json"));
const app = (0, express_1.default)();
const port = parseInt((_a = process.env.CDSW_APP_PORT) !== null && _a !== void 0 ? _a : "3000", 10);
const host = (_b = process.env.NODE_HOST) !== null && _b !== void 0 ? _b : "127.0.0.1";
const apiProxy = {
    target: process.env.API_URL || "http://localhost:8080",
    changeOrigin: true,
    pathFilter: ["/api/**"],
};
const llmServiceProxy = {
    target: (_c = process.env.LLM_SERVICE_URL) !== null && _c !== void 0 ? _c : "http://localhost:8081",
    changeOrigin: true,
    pathFilter: ["/llm-service/**", "/rag-studio/api/v1/sessions/*/chat"],
    pathRewrite: (path, req) => {
        if (path.startsWith("/rag-studio/api/v1/")) {
            return path.replace("/rag-studio/api/v1/", "/");
        }
        return path;
    },
};
app.use("/api-docs", swagger_ui_express_1.default.serve);
app.get("/api-docs", swagger_ui_express_1.default.setup(api_json_1.default));
app.use(express_1.default.static((0, path_1.join)(__dirname, "../..", "dist")));
app.use((0, http_proxy_middleware_1.createProxyMiddleware)(llmServiceProxy));
app.use((0, http_proxy_middleware_1.createProxyMiddleware)(apiProxy));
app.get("*", (req, res) => {
    console.log("Serving up req.url: ", req.url);
    res.sendFile((0, path_1.join)(__dirname, "../..", "dist", "index.html"));
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
        console.error("Could not close connections in time, forcefully shutting down");
        process.exit(1);
    }, 5000);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
