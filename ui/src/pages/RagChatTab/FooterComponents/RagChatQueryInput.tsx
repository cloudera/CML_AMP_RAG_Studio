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

import { Button, Flex, Input, Switch, Tooltip } from "antd";
import SuggestedQuestionsFooter from "pages/RagChatTab/FooterComponents/SuggestedQuestionsFooter.tsx";
import { DatabaseFilled, SendOutlined } from "@ant-design/icons";
import { useContext, useState } from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import messageQueue from "src/utils/messageQueue.ts";
import { createQueryConfiguration, useChatMutation } from "src/api/chatApi.ts";
import { useSuggestQuestions } from "src/api/ragQueryApi.ts";
import { useNavigate, useParams } from "@tanstack/react-router";
import { cdlBlue600 } from "src/cuix/variables.ts";

import type { SwitchChangeEventHandler } from "antd/lib/switch";
import {
  CreateSessionRequest,
  useCreateSessionMutation,
  useRenameNameMutation,
} from "src/api/sessionApi.ts";
import { QueryKeys } from "src/api/utils.ts";
import { useQueryClient } from "@tanstack/react-query";
import { useGetLlmModels } from "src/api/modelsApi.ts";

const RagChatQueryInput = () => {
  const navigate = useNavigate();
  const {
    excludeKnowledgeBaseState: [excludeKnowledgeBase, setExcludeKnowledgeBase],
    currentQuestionState: [, setCurrentQuestion],
    chatHistoryQuery: { chatHistory },
    dataSourceSize,
    dataSourcesQuery: { dataSourcesStatus },
    activeSession,
    firstQuestionState: [, setFirstQuestion],
  } = useContext(RagChatContext);

  const { data: models } = useGetLlmModels();
  const [userInput, setUserInput] = useState("");
  const { sessionId } = useParams({ strict: false });
  const [newSessionId, setNewSessionId] = useState(0);

  const configuration = createQueryConfiguration(excludeKnowledgeBase);
  const {
    data: sampleQuestions,
    isPending: sampleQuestionsIsPending,
    isFetching: sampleQuestionsIsFetching,
  } = useSuggestQuestions({
    configuration,
    session_id: sessionId && sessionId != "0" ? sessionId : "",
  });

  const chatMutation = useChatMutation({
    onSuccess: () => {
      if (activeSession && activeSession.name === "") {
        renameSessionMutation.mutate(activeSession.id.toString());
      }
      setUserInput("");
      setCurrentQuestion("");
    },
    onError: (res: Error) => {
      messageQueue.error(res.toString());
    },
  });

  const newChatMutation = useChatMutation({
    onSuccess: () => {
      if (newSessionId) {
        renameSessionMutation.mutate(newSessionId.toString());
      }
      return navigate({
        to: "/sessions/$sessionId",
        params: { sessionId: newSessionId.toString() },
      });
    },
    onError: (res: Error) => {
      messageQueue.error(res.toString());
    },
  });

  const renameSessionMutation = useRenameNameMutation({
    onSuccess: (name) => {
      messageQueue.success(`session renamed to ${name}`);
    },
    onError: (res) => {
      messageQueue.error(res.toString());
    },
  });

  const queryClient = useQueryClient();
  const { mutate: createSessionAndAskQuestion } = useCreateSessionMutation({
    onSuccess: async (data) => {
      await queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getSessions] })
        .then(() => {
          setNewSessionId(data.id);
          setFirstQuestion(userInput);

          newChatMutation.mutate({
            query: userInput,
            session_id: data.id.toString(),
            configuration: createQueryConfiguration(excludeKnowledgeBase),
          });
        })
        .catch((x: unknown) => {
          messageQueue.error(String(x));
        });
    },
    onError: () => {
      messageQueue.error("Session creation failed.");
    },
  });

  const handleChat = (userInput: string) => {
    if (userInput.trim().length <= 0) {
      return;
    }
    setCurrentQuestion(userInput);
    if (activeSession && sessionId) {
      chatMutation.mutate({
        query: userInput,
        session_id: sessionId,
        configuration: createQueryConfiguration(excludeKnowledgeBase),
      });
    } else if (models && models.length > 0) {
      const requestBody: CreateSessionRequest = {
        name: "New Chat",
        dataSourceIds: [],
        inferenceModel: models[0].model_id,
        responseChunks: 10,
        queryConfiguration: {
          enableHyde: false,
          enableSummaryFilter: true,
        },
      };
      createSessionAndAskQuestion(requestBody);
    }
  };

  const handleExcludeKnowledgeBase: SwitchChangeEventHandler = (checked) => {
    setExcludeKnowledgeBase(() => !checked);
  };

  return (
    <div>
      <Flex vertical align="center" gap={10}>
        {chatHistory.length > 0 || dataSourceSize ? (
          <SuggestedQuestionsFooter
            questions={sampleQuestions?.suggested_questions ?? []}
            isLoading={sampleQuestionsIsPending || sampleQuestionsIsFetching}
            handleChat={handleChat}
            condensedQuestion={
              chatHistory.length > 0
                ? chatHistory[chatHistory.length - 1].condensed_question
                : undefined
            }
          />
        ) : null}
        <Flex style={{ width: "100%" }} justify="space-between" gap={5}>
          <Input
            autoFocus
            placeholder={
              dataSourceSize && dataSourceSize > 0
                ? "Ask a question"
                : "Chat with the LLM"
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
            suffix={
              <Tooltip title="Whether to query against the knowledge base.  Disabling will query only against the model's training data.">
                <Switch
                  checkedChildren={<DatabaseFilled />}
                  value={!excludeKnowledgeBase}
                  style={{ display: dataSourceSize ? "block" : "none" }}
                  onChange={handleExcludeKnowledgeBase}
                />
              </Tooltip>
            }
            disabled={chatMutation.isPending}
          />
          <Button
            style={{ padding: 0 }}
            type="text"
            onClick={() => {
              handleChat(userInput);
            }}
            icon={<SendOutlined style={{ color: cdlBlue600 }} />}
            disabled={chatMutation.isPending}
          />
        </Flex>
      </Flex>
    </div>
  );
};

export default RagChatQueryInput;
