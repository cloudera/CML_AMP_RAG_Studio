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
 * Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
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

import { Alert, Flex, Typography } from "antd";
import EmbeddingModelTable from "pages/Models/EmbeddingModelTable.tsx";
import { useGetEmbeddingModels, useGetLlmModels } from "src/api/modelsApi.ts";
import InferenceModelTable from "pages/Models/InferenceModelTable.tsx";
import { useEffect, useState } from "react";
import { useChat } from "ai/react";

export const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const ws = new WebSocket(url);
    setSocket(ws);

    ws.onmessage = (event) => {
      setMessages((prevMessages) => [...prevMessages, event.data]);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };

    return () => {
      ws.close();
    };
  }, [url]);

  const sendMessage = (message: string) => {
    if (socket) {
      socket.send(message);
    }
  };
  return { messages, sendMessage };
};

const WebSocketComponent = () => {
  const chat = useChat({
    api: "/sessions/1/ws",
  });
  console.log(chat);
  // console.log(chat);
  // const { messages, sendMessage } = useWebSocket("/sessions/1/ws");
  // const [input, setInput] = useState("");
  //
  // const handleSend = () => {
  //   sendMessage(input);
  //   setInput("");
  // };

  return (
    <div>
      <h1>WebSocket Messages</h1>
      <input
        type="text"
        value={chat.input}
        onChange={(e) => chat.setInput(e.target.value)}
      />
      <button onClick={chat.handleSubmit}>Send</button>
      {chat.isLoading ? <div>loading...</div> : null}
      <div>
        {chat.messages.map((message, i) => (
          <div key={i}>{message.content}</div>
        ))}
        {/*{messages.length ? <div>response: {messages}</div> : "no messages yet"}*/}
      </div>
    </div>
  );
};

const ModelPage = () => {
  const {
    data: embeddingModels,
    isLoading: areEmbeddingModelsLoading,
    error: embeddingError,
  } = useGetEmbeddingModels();
  const {
    data: inferenceModels,
    isLoading: areInferenceModelsLoading,
    error: inferenceError,
  } = useGetLlmModels();

  return (
    <Flex vertical align="center">
      <div style={{ maxWidth: 800 }}>
        {inferenceError ? (
          <Alert
            style={{ margin: 10 }}
            message={`Inference model error: ${inferenceError.message}`}
            type="error"
          />
        ) : null}
        {embeddingError ? (
          <Alert
            style={{ margin: 10 }}
            message={`Embedding model error: ${embeddingError.message}`}
            type="error"
          />
        ) : null}
      </div>
      <Flex vertical style={{ width: "80%", maxWidth: 1000 }} gap={20}>
        <WebSocketComponent />
        <Typography.Title level={3}>Embedding Models</Typography.Title>
        <EmbeddingModelTable
          embeddingModels={embeddingModels}
          areEmbeddingModelsLoading={areEmbeddingModelsLoading}
        />
        <Typography.Title level={3}>Inference Models</Typography.Title>
        <InferenceModelTable
          inferenceModels={inferenceModels}
          areInferenceModelsLoading={areInferenceModelsLoading}
        />
      </Flex>
    </Flex>
  );
};

export default ModelPage;
