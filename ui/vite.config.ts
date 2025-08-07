/*******************************************************************************
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2024
 * All rights reserved.
 *
 * Applicable Open Source License: Apache 2.0
 *
 * NOTE: Cloudera open source products are modular software products
 * made up of hundreds of individual components, each of which was
 * individually copyrighted.  Each Cloudera open source product is a
 * collective work under U.S. Copyright Law. Your license to use the
 * collective work is as provided in your written agreement with
 * Cloudera.  Used apart from the collective work, this file is
 * licensed for your use pursuant to the open source license
 * identified above.
 *
 * This code is provided to you pursuant a written agreement with
 * (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
 * this code. If you do not have a written agreement with Cloudera nor
 * with an authorized and properly licensed third party, you do not
 * have any rights to access nor to use this code.
 *
 * Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
 * contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
 * KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
 * WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
 * IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
 * FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
 * AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
 * ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
 * OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
 * CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
 * RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
 * BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
 * DATA.
 ******************************************************************************/

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import tsConfigPathsPlugin from "vite-tsconfig-paths";
import svgr from "vite-plugin-svgr";
import { resolve } from "path";
import fs from "fs";
import path from "path";

// Custom plugin to serve cache directory
function cacheStaticPlugin() {
  return {
    name: "cache-static",
    configureServer(server: any) {
      const cacheDir = resolve(process.cwd(), "../cache");
      
      server.middlewares.use("/cache", (req: any, res: any, next: any) => {
        if (!req.url) {
          return next();
        }
        
        // Clean the URL - remove leading /cache and any query params
        let fileName = req.url;
        if (fileName.startsWith("/cache/")) {
          fileName = fileName.substring(7); // Remove "/cache/"
        } else if (fileName.startsWith("/")) {
          fileName = fileName.substring(1); // Remove leading "/"
        }
        
        // Remove query params
        const queryIndex = fileName.indexOf('?');
        if (queryIndex !== -1) {
          fileName = fileName.substring(0, queryIndex);
        }
        
        const filePath = path.join(cacheDir, fileName);
        
        // Security check - ensure the file is within cache directory
        const normalizedCacheDir = path.resolve(cacheDir);
        const normalizedFilePath = path.resolve(filePath);
        if (!normalizedFilePath.startsWith(normalizedCacheDir)) {
          res.statusCode = 403;
          res.end("Forbidden");
          return;
        }
        
        // Check if file exists
        if (!fs.existsSync(filePath)) {
          res.statusCode = 404;
          res.end("Not found");
          return;
        }
        
        const stats = fs.statSync(filePath);
        if (!stats.isFile()) {
          res.statusCode = 404;
          res.end("Not found");
          return;
        }
        
        // Set appropriate headers
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Access-Control-Allow-Methods", "GET");
        res.setHeader("Access-Control-Allow-Headers", "*");
        
        const ext = path.extname(filePath).toLowerCase();
        const mimeTypes: Record<string, string> = {
          ".png": "image/png",
          ".jpg": "image/jpeg",
          ".jpeg": "image/jpeg", 
          ".gif": "image/gif",
          ".svg": "image/svg+xml",
          ".webp": "image/webp"
        };
        res.setHeader("Content-Type", mimeTypes[ext] || "application/octet-stream");
        res.setHeader("Content-Length", stats.size);
        
        // Stream the file
        const stream = fs.createReadStream(filePath);
        stream.pipe(res);
        stream.on("error", () => {
          if (!res.headersSent) {
            res.statusCode = 500;
            res.end("Server error");
          }
        });
      });
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tsConfigPathsPlugin(),
    svgr({ svgrOptions: { icon: true } }),
    cacheStaticPlugin(),
  ],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    globals: true,
  },
  server: {
    proxy: {
      "/api": "http://localhost:8080",
      "/llm-service": {
        target: "http://localhost:8081",
        rewrite: (path) => path.replace(/^\/llm-service/, ""),
      },
    },
    fs: {
      // Allow serving files from the cache directory outside of the workspace
      allow: [".", "../cache"],
    },
  },
  // Configure additional static asset directories
  assetsInclude: ["**/*.png", "**/*.jpg", "**/*.jpeg", "**/*.gif", "**/*.svg"],
});
