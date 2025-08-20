/*
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2025
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
 */

import { describe, expect, it } from "vitest";
import { InfiniteData } from "@tanstack/react-query";
import { ChatHistoryResponse, ChatMessageType } from "src/api/chatApi.ts";
import { flattenChatHistory } from "./useFlattenChatHistory.tsx";

describe("flattenChatHistory", () => {
  it("returns empty array when chatHistory is undefined", () => {
    const result = flattenChatHistory(undefined);
    expect(result).toEqual([]);
  });

  it("returns empty array when chatHistory has no pages", () => {
    const chatHistory: InfiniteData<ChatHistoryResponse> = {
      pages: [],
      pageParams: [],
    };
    const result = flattenChatHistory(chatHistory);
    expect(result).toEqual([]);
  });

  it("returns empty array when chatHistory has pages with no data", () => {
    const chatHistory: InfiniteData<ChatHistoryResponse> = {
      pages: [
        {
          data: [],
          next_id: null,
          previous_id: null,
        },
      ],
      pageParams: [0],
    };
    const result = flattenChatHistory(chatHistory);
    expect(result).toEqual([]);
  });

  it("flattens a single page with messages", () => {
    const message1: ChatMessageType = {
      id: "msg1",
      session_id: 1,
      source_nodes: [],
      rag_message: { user: "query 1", assistant: "response 1" },
      evaluations: [],
      timestamp: 1000,
    };

    const message2: ChatMessageType = {
      id: "msg2",
      session_id: 1,
      source_nodes: [],
      rag_message: { user: "query 2", assistant: "response 2" },
      evaluations: [],
      timestamp: 2000,
    };

    const chatHistory: InfiniteData<ChatHistoryResponse> = {
      pages: [
        {
          data: [message1, message2],
          next_id: null,
          previous_id: null,
        },
      ],
      pageParams: [0],
    };

    const result = flattenChatHistory(chatHistory);
    expect(result).toEqual([message1, message2]);
  });

  it("flattens multiple pages with messages", () => {
    const message1: ChatMessageType = {
      id: "msg1",
      session_id: 1,
      source_nodes: [],
      rag_message: { user: "query 1", assistant: "response 1" },
      evaluations: [],
      timestamp: 1000,
    };

    const message2: ChatMessageType = {
      id: "msg2",
      session_id: 1,
      source_nodes: [],
      rag_message: { user: "query 2", assistant: "response 2" },
      evaluations: [],
      timestamp: 2000,
    };

    const message3: ChatMessageType = {
      id: "msg3",
      session_id: 1,
      source_nodes: [],
      rag_message: { user: "query 3", assistant: "response 3" },
      evaluations: [],
      timestamp: 3000,
    };

    const chatHistory: InfiniteData<ChatHistoryResponse> = {
      pages: [
        {
          data: [message1],
          next_id: 5,
          previous_id: 10,
        },
        {
          data: [message2, message3],
          next_id: 15,
          previous_id: 20,
        },
      ],
      pageParams: [0, 10],
    };

    const result = flattenChatHistory(chatHistory);
    expect(result).toEqual([message1, message2, message3]);
  });
});
