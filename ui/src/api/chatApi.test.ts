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

import { describe, it, expect } from "vitest";
import {
  ChatHistoryResponse,
  replacePlaceholderInChatHistory,
} from "src/api/chatApi.ts";
import { InfiniteData } from "@tanstack/react-query";

describe("replacePlaceholderInChatHistory", () => {
  it("replaces placeholder with actual data when cachedData contains placeholder", () => {
    const placeholder = {
      id: "placeholder",
      session_id: 0,
      source_nodes: [],
      rag_message: { user: "query", assistant: "" },
      evaluations: [],
      timestamp: Date.now(),
    };
    const actualData = {
      id: "actual",
      session_id: 1,
      source_nodes: [],
      rag_message: { user: "query", assistant: "response" },
      evaluations: [],
      timestamp: Date.now(),
    };
    const cachedData: InfiniteData<ChatHistoryResponse> = {
      pages: [{ data: [placeholder], next_id: null, previous_id: null }],
      pageParams: [0],
    };

    const result = replacePlaceholderInChatHistory(actualData, cachedData);

    expect(result).toEqual({
      pages: [{ data: [actualData], next_id: null, previous_id: null }],
      pageParams: [0],
    });
  });

  it("returns actual data when cachedData is undefined", () => {
    const actualData = {
      id: "actual",
      session_id: 1,
      source_nodes: [],
      rag_message: { user: "query", assistant: "response" },
      evaluations: [],
      timestamp: Date.now(),
    };

    const result = replacePlaceholderInChatHistory(actualData, undefined);

    expect(result).toEqual({
      pages: [{ data: [actualData], next_id: null, previous_id: null }],
      pageParams: [0],
    });
  });

  it("does not replace any data when cachedData does not contain placeholder", () => {
    const actualData = {
      id: "actual",
      session_id: 1,
      source_nodes: [],
      rag_message: { user: "query", assistant: "response" },
      evaluations: [],
      timestamp: Date.now(),
    };
    const cachedItem = [
      {
        id: "other",
        session_id: 2,
        source_nodes: [],
        rag_message: { user: "query", assistant: "response" },
        evaluations: [],
        timestamp: Date.now(),
      },
    ];

    const cachedData: InfiniteData<ChatHistoryResponse> = {
      pages: [{ data: cachedItem, next_id: null, previous_id: null }],
      pageParams: [0],
    };

    const result = replacePlaceholderInChatHistory(actualData, cachedData);

    expect(result).toEqual(cachedData);
  });
});
