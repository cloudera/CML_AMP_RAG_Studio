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

import { useContext, useEffect, useRef } from "react";
import ChatMessage from "pages/RagChatTab/ChatOutput/ChatMessages/ChatMessage.tsx";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { Flex, Image, Typography } from "antd";
import Images from "src/components/images/Images.ts";
import PendingRagOutputSkeleton from "pages/RagChatTab/ChatOutput/Loaders/PendingRagOutputSkeleton.tsx";
import { ChatLoading } from "pages/RagChatTab/ChatOutput/Loaders/ChatLoading.tsx";

const ChatMessageController = () => {
  const {
    chatHistoryQuery: { chatHistory, chatHistoryStatus },
    activeSession,
    firstQuestionState: [firstQuestion],
  } = useContext(RagChatContext);
  const scrollEl = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTimeout(() => {
      if (scrollEl.current) {
        scrollEl.current.scrollIntoView({ behavior: "auto" });
      }
    }, 50);
  }, [scrollEl.current, chatHistory.length, activeSession?.id]);

  if (chatHistoryStatus === "pending") {
    return <ChatLoading />;
  }

  if (firstQuestion) {
    return <PendingRagOutputSkeleton question={firstQuestion} />;
  }

  if (chatHistory.length == 0) {
    return (
      <Flex vertical align="center" gap={16}>
        <Image
          src={Images.BrandTalking}
          alt="Machines Chatting"
          style={{ width: 80 }}
          preview={false}
        />
        <Typography.Title level={4} style={{ fontWeight: 300, margin: 0 }}>
          Welcome to Chatbot Studio
        </Typography.Title>
      </Flex>
    );
  }
  return (
    <div data-testid="chat-message-controller">
      {chatHistory.map((historyMessage, index) => (
        <ChatMessage
          data={historyMessage}
          key={historyMessage.id}
          isLast={index === history.length - 1}
        />
      ))}
      <div ref={scrollEl} />
    </div>
  );
};

export default ChatMessageController;
