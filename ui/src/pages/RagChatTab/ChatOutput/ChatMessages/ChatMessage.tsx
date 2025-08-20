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

import { Alert, AlertProps, Divider, Flex, Typography } from "antd";
import PendingRagOutputSkeleton from "pages/RagChatTab/ChatOutput/Loaders/PendingRagOutputSkeleton.tsx";
import {
  CANCELED_PREFIX_ID,
  ChatMessageType,
  ERROR_PREFIX_ID,
  isPlaceholder,
} from "src/api/chatApi.ts";
import UserQuestion from "pages/RagChatTab/ChatOutput/ChatMessages/UserQuestion.tsx";

import "../tableMarkdown.css";
import { ExclamationCircleTwoTone } from "@ant-design/icons";
import { ChatMessageBody } from "pages/RagChatTab/ChatOutput/ChatMessages/ChatMessageBody.tsx";
import { useContext } from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { cdlAmber500 } from "src/cuix/variables.ts";

const isError = (data: ChatMessageType) => {
  return data.id.startsWith(ERROR_PREFIX_ID);
};

const isCanceled = (data: ChatMessageType) => {
  return data.id.startsWith(CANCELED_PREFIX_ID);
};

const WarningMessage = ({
  data,
  color,
  alertType,
}: {
  data: ChatMessageType;
  color: string;
  alertType: AlertProps["type"];
}) => {
  return (
    <div data-testid="chat-message">
      <div>
        <UserQuestion question={data.rag_message.user} />
        <Flex
          style={{ marginTop: 15 }}
          align="baseline"
          justify="space-between"
          gap={8}
        >
          <div style={{ flex: 1 }}>
            <ExclamationCircleTwoTone
              type={alertType}
              twoToneColor={color}
              style={{ fontSize: 22 }}
            />
          </div>
          <Flex vertical gap={8} style={{ width: "100%" }}>
            <Typography.Text style={{ fontSize: 16, marginTop: 8 }}>
              <Alert
                type={alertType}
                message={data.rag_message.assistant.trimStart()}
              />
            </Typography.Text>
          </Flex>
        </Flex>
        <Divider />
      </div>
    </div>
  );
};
const ChatMessage = ({ data }: { data: ChatMessageType }) => {
  const { activeSession } = useContext(RagChatContext);
  const excludeKnowledgeBases =
    !activeSession?.dataSourceIds || activeSession.dataSourceIds.length === 0;

  if (isError(data)) {
    return <WarningMessage data={data} color={"#ff4d4f"} alertType={"error"} />;
  }
  if (isCanceled(data)) {
    return (
      <WarningMessage data={data} color={cdlAmber500} alertType={"warning"} />
    );
  }

  if (isPlaceholder(data)) {
    return <PendingRagOutputSkeleton question={data.rag_message.user} />;
  }

  return (
    <ChatMessageBody
      data={data}
      sessionId={activeSession?.id ?? 0}
      excludeKnowledgeBase={excludeKnowledgeBases}
    />
  );
};

export default ChatMessage;
