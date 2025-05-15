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

import { ChatMessageType, CrewEventResponse } from "src/api/chatApi.ts";
import UserQuestion from "pages/RagChatTab/ChatOutput/ChatMessages/UserQuestion.tsx";
import { Divider, Flex, Typography } from "antd";
import Images from "src/components/images/Images.ts";
import { cdlBlue500, cdlGray200 } from "src/cuix/variables.ts";
import SourceNodes from "pages/RagChatTab/ChatOutput/Sources/SourceNodes.tsx";
import Markdown from "react-markdown";
import Remark from "remark-gfm";
import { Evaluations } from "pages/RagChatTab/ChatOutput/ChatMessages/Evaluations.tsx";
import RatingFeedbackWrapper from "pages/RagChatTab/ChatOutput/ChatMessages/RatingFeedbackWrapper.tsx";
import CopyButton from "pages/RagChatTab/ChatOutput/ChatMessages/CopyButton.tsx";
import StreamedEvents from "pages/RagChatTab/ChatOutput/ChatMessages/StreamedEvents.tsx";

export const ChatMessageBody = ({
  data,
  streamedEvents,
}: {
  data: ChatMessageType;
  streamedEvents?: CrewEventResponse[];
}) => {
  // streamedEvents = [
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer",
  //     timestamp: 1747321016.211383,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "searcher",
  //     data: "Thought: I now know the final answer.",
  //     timestamp: 1747321018.258643,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "researcher",
  //     data: "The query calls for an in-depth exploration of how the index addresses the impact of economic sanctions on crisis management. The context emphasizes missing sanctions data, external actors' influences, and the potential resource limitations faced by countries under sanctions during humanitarian crises. Using the provided context, I aim to build a thorough response based on the textual insights and their role within an index framework.",
  //     timestamp: 1747321036.084759,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer",
  //     timestamp: 1747321265.41863,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer",
  //     timestamp: 1747321459.718286,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "searcher",
  //     data: "Thought: I now know the final answer",
  //     timestamp: 1747321461.3717902,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "researcher",
  //     data: "Failed to parse LLM response",
  //     timestamp: 1747321482.936766,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer.",
  //     timestamp: 1747321500.357913,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "searcher",
  //     data: "Thought: I now know the final answer. The current date is already provided: 2025-05-15T09:04:59.504493. Let me clarify if you have a specific query related to searching the internet or if this date alone suffices as an answer. Kindly refine your request for further assistance.",
  //     timestamp: 1747321503.355131,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "researcher",
  //     data: "Thought: I now have relevant sources to understand how the intervention index optimizes resource allocation in humanitarian crises.",
  //     timestamp: 1747321531.380204,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer.",
  //     timestamp: 1747321593.87309,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "searcher",
  //     data: "Thought: I now know the final answer.",
  //     timestamp: 1747321595.371118,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "researcher",
  //     data: "To address the user's query about the role of the intervention index in optimizing resource allocation in humanitarian crises, I need to analyze how the proposed index from the context provided improves resource allocation before, during, and after crises while incorporating ethical, operational, and dynamic factors rooted in the research provided. \n\nThe context from the user also emphasizes issues such as cross-organization planning, ethical concerns about data use and representation, and the need for dynamic adaptability in crises. I can arrive at a comprehensive answer using the detail already shared, cross-referencing this with the methodology and benefits of the intervention index discussed.",
  //     timestamp: 1747321613.301375,
  //   },
  // ];
  return (
    <div data-testid="chat-message">
      {data.rag_message.user ? (
        <div>
          <UserQuestion question={data.rag_message.user} />
          <Flex
            style={{ marginTop: 15 }}
            align="baseline"
            justify="space-between"
            gap={8}
          >
            <div style={{ flex: 1 }}>
              {data.source_nodes.length > 0 ? (
                <Images.AiAssistantWhite
                  style={{
                    padding: 4,
                    backgroundColor: cdlBlue500,
                    borderRadius: 20,
                    width: 24,
                    height: 24,
                    flex: 1,
                  }}
                />
              ) : (
                <Images.Models
                  style={{
                    padding: 4,
                    backgroundColor: cdlGray200,
                    borderRadius: 20,
                    width: 26,
                    height: 24,
                    flex: 1,
                  }}
                />
              )}
            </div>
            <Flex vertical gap={8} style={{ width: "100%" }}>
              <SourceNodes data={data} />
              <StreamedEvents streamedEvents={streamedEvents} />
              <Typography.Text style={{ fontSize: 16, marginTop: 8 }}>
                <Markdown
                  skipHtml
                  remarkPlugins={[Remark]}
                  className="styled-markdown"
                >
                  {data.rag_message.assistant.trimStart()}
                </Markdown>
              </Typography.Text>
              <Flex gap={16} align="center">
                <CopyButton message={data} />
                <Evaluations evaluations={data.evaluations} />
                <RatingFeedbackWrapper responseId={data.id} />
              </Flex>
            </Flex>
          </Flex>
        </div>
      ) : null}
      <Divider />
    </div>
  );
};
