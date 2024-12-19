/*
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
 */

const express = require("express");
const { join } = require("path");
const { createProxyMiddleware } = require("http-proxy-middleware");
const WebSocket = require("ws");
const expressWs = require("express-ws");

const app = express();
expressWs(app);
const port = process.env.CDSW_APP_PORT ?? 3000;
const host = process.env.NODE_HOST ?? "127.0.0.1";

app.get("/test", (req, res) => {
  res.send(`<!DOCTYPE html>
  <html>
  <head>
  <title>Chat</title>
</head>
  <body>
  <h1>WebSocket Chat</h1>
  <form action="" onsubmit="sendMessage(event)">
    <input type="text" id="messageText" autocomplete="off"/>
    <button>Send</button>
  </form>
  <ul id='messages'>
  </ul>
  <script>
    var ws = new WebSocket("ws://localhost:3000/ws");
    ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('span')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
    };
    function sendMessage(event) {
    var input = document.getElementById("messageText")
    ws.send(input.value)
    input.value = ''
    event.preventDefault()
  }
  </script>
  </body>
</html>
  `);
});

app.ws("/ws", (ws, req) => {
  ws.on("message", function (msg) {
    console.log("received: %s", msg);
    ws.send(msg);
  });

  console.log("socket", req.testing);
  // const destinationWs = new WebSocket("ws://localhost:8000/sessions/1/ws");
  //
  // destinationWs.on("error", console.error);
  //
  // destinationWs.on("open", function open() {
  //   ws.send("something");
  // });
  //
  // destinationWs.on("message", function message(data) {
  //   console.log("received: %s", data);
  // });
});

const apiProxy = createProxyMiddleware({
  target: (process.env.API_URL || "http://localhost:8080") + "/api",
  changeOrigin: true,
});

const llmServiceProxy = createProxyMiddleware({
  target: process.env.LLM_SERVICE_URL ?? "http://localhost:8000",
  changeOrigin: true,
});

app.use(express.static(join(__dirname, "..", "dist")));
app.use("/api", apiProxy);
app.use("/llm-service", llmServiceProxy);

app.get("*", (req, res) => {
  console.log("Serving up req.url: ", req.url);
  res.sendFile(join(__dirname, "..", "dist", "index.html"));
  console.log("Served up req.url: ", req.url);
});

const server = app.listen(port, host, () => {
  console.log(`Node proxy listening on host:port ${host}:${port}`);
});

function shutdown() {
  console.log("termination signal received: closing HTTP server");
  server.close(() => {
    process.exit(0);
    console.log("HTTP server closed");
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
