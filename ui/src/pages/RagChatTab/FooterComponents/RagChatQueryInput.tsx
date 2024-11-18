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

import { Button, Flex, Input } from "antd";
import SuggestedQuestionsFooter from "pages/RagChatTab/FooterComponents/SuggestedQuestionsFooter.tsx";
import { SendOutlined } from "@ant-design/icons";
import { useContext, useState } from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import messageQueue from "src/utils/messageQueue.ts";
import { ChatMessageType, useChatMutation } from "src/api/chatApi.ts";
import { RagMessage, useSuggestQuestions } from "src/api/ragQueryApi.ts";
import { useParams } from "@tanstack/react-router";
import { cdlBlue600 } from "src/cuix/variables.ts";

const convertedChatHistory = (chatHistory: ChatMessageType[]): RagMessage[] => {
  return chatHistory.flatMap((message) => {
    return [
      {
        role: "user",
        content: message.rag_message.user,
      },
      {
        role: "assistant",
        content: message.rag_message.assistant,
      },
    ];
  });
};

const RagChatQueryInput = () => {
  const {
    dataSourceId,
    queryConfiguration,
    setCurrentQuestion,
    chatHistory,
    dataSourceSize,
    dataSourcesStatus,
  } = useContext(RagChatContext);

  const [userInput, setUserInput] = useState("");
  const { sessionId } = useParams({ strict: false });

  const {
    data: sampleQuestions,
    isPending: sampleQuestionsIsPending,
    isFetching: sampleQuestionsIsFetching,
  } = useSuggestQuestions({
    data_source_id: dataSourceId?.toString() ?? "",
    configuration: queryConfiguration,
    chat_history: convertedChatHistory(chatHistory),
  });

  const chatMutation = useChatMutation({
    onSuccess: () => {
      setUserInput("");
      setCurrentQuestion("");
    },
    onError: (res: Error) => {
      messageQueue.error(res.toString());
    },
  });

  const handleChat = (userInput: string) => {
    if (dataSourceId && dataSourceId > 0 && userInput.length > 0 && sessionId) {
      setCurrentQuestion(userInput);
      chatMutation.mutate({
        query: userInput,
        data_source_id: dataSourceId.toString(),
        session_id: sessionId,
        configuration: queryConfiguration,
      });
    }
  };

  return (
    <div>
      <Flex vertical align="center" gap={10}>
        {chatHistory.length > 0 ? (
          <SuggestedQuestionsFooter
            questions={sampleQuestions?.suggested_questions ?? []}
            isLoading={sampleQuestionsIsPending || sampleQuestionsIsFetching}
            handleChat={handleChat}
          />
        ) : null}
        <Flex style={{ width: "100%" }} justify="space-between" gap={5}>
          <Input
            placeholder={
              dataSourceSize && dataSourceSize > 0
                ? "Ask a question"
                : "No documents available"
            }
            status={dataSourcesStatus === "error" ? "error" : undefined}
            value={userInput}
            onChange={(e) => {
              setUserInput(e.target.value);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleChat(userInput);
              }
            }}
            disabled={!dataSourceSize || chatMutation.isPending}
          />
          <Button
            style={{ padding: 0 }}
            type="text"
            onClick={() => {
              handleChat(userInput);
            }}
            icon={<SendOutlined style={{ color: cdlBlue600 }} />}
          />
        </Flex>
      </Flex>
    </div>
  );
};

export default RagChatQueryInput;
