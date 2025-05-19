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

import {
  ChatMessageType,
  CrewEventResponse,
  SourceNode,
} from "src/api/chatApi.ts";
import UserQuestion from "pages/RagChatTab/ChatOutput/ChatMessages/UserQuestion.tsx";
import { Divider, Flex, Typography } from "antd";
import Images from "src/components/images/Images.ts";
import { cdlBlue500, cdlGray200 } from "src/cuix/variables.ts";
import Markdown from "react-markdown";
import Remark from "remark-gfm";
import { Evaluations } from "pages/RagChatTab/ChatOutput/ChatMessages/Evaluations.tsx";
import RatingFeedbackWrapper from "pages/RagChatTab/ChatOutput/ChatMessages/RatingFeedbackWrapper.tsx";
import CopyButton from "pages/RagChatTab/ChatOutput/ChatMessages/CopyButton.tsx";
import StreamedEvents from "pages/RagChatTab/ChatOutput/ChatMessages/StreamedEvents.tsx";
import rehypeRaw from "rehype-raw";
import { SourceCard } from "pages/RagChatTab/ChatOutput/Sources/SourceCard.tsx";
import { ComponentProps, ReactElement } from "react";
import SourceNodes from "pages/RagChatTab/ChatOutput/Sources/SourceNodes.tsx";

export const ChatMessageBody = ({
  data,
  streamedEvents,
}: {
  data: ChatMessageType;
  streamedEvents?: CrewEventResponse[];
}) => {
  return (
    <div data-testid="chat-message">
      {data.rag_message.user ? (
        <div>
          <UserQuestion question={data.rag_message.user} />
          <Flex
            style={{ marginTop: 15 }}
            align="self-start"
            justify="space-between"
            gap={8}
          >
            <div style={{ flex: 1, marginTop: 24 }}>
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
              <StreamedEvents streamedEvents={streamedEvents} />
              <Typography.Text style={{ fontSize: 16, marginTop: 8 }}>
                <Markdown
                  // skipHtml={true}
                  remarkPlugins={[Remark]}
                  rehypePlugins={[rehypeRaw]}
                  className="styled-markdown"
                  children={data.rag_message.assistant.trimStart()}
                  components={{
                    a: (
                      props: ComponentProps<"a">,
                    ): ReactElement<SourceNode> | undefined => {
                      const { href, className, children, ...other } = props;
                      if (className === "rag_citation") {
                        if (data.source_nodes.length === 0) {
                          return undefined;
                        }
                        const { source_nodes } = data;
                        const sourceNodeIndex = source_nodes.findIndex(
                          (source_node) => source_node.node_id === href,
                        );
                        if (sourceNodeIndex >= 0) {
                          return (
                            <SourceCard
                              source={source_nodes[sourceNodeIndex]}
                              index={sourceNodeIndex + 1}
                            />
                          );
                        }
                        if (!href?.startsWith("http")) {
                          return undefined;
                        }
                      }
                      return (
                        <a href={href} className={className} {...other}>
                          {children}
                        </a>
                      );
                    },
                  }}
                />
              </Typography.Text>
              <SourceNodes data={data} />
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
