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

import { Button, Flex, Input, InputRef, Tooltip } from "antd";
import {
  DatabaseFilled,
  DatabaseOutlined,
  SendOutlined,
  StopOutlined,
} from "@ant-design/icons";
import {
  MouseEventHandler,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import {
  createQueryConfiguration,
  getOnEvent,
  useStreamingChatMutation,
} from "src/api/chatApi.ts";
import { useParams, useSearch } from "@tanstack/react-router";
import { cdlBlue600, cdlRed600 } from "src/cuix/variables.ts";
import { useSuggestQuestions } from "src/api/ragQueryApi.ts";
import SuggestedQuestionsFooter from "pages/RagChatTab/FooterComponents/SuggestedQuestionsFooter.tsx";
import ToolsManagerButton from "pages/RagChatTab/FooterComponents/ToolsManager.tsx";
import SessionDocuments from "pages/RagChatTab/FooterComponents/SessionDocuments.tsx";

const { TextArea } = Input;

const RagChatQueryInput = ({
  newSessionCallback,
}: {
  newSessionCallback: (userInput: string) => void;
}) => {
  const {
    activeSession,
    excludeKnowledgeBaseState: [excludeKnowledgeBase, setExcludeKnowledgeBase],
    chatHistoryQuery: { flatChatHistory },
    dataSourceSize,
    dataSourcesQuery: { dataSourcesStatus },
    streamedChatState: [, setStreamedChat],
    streamedEventState: [, setStreamedEvent],
    streamedAbortControllerState: [
      streamedAbortController,
      setStreamedAbortController,
    ],
  } = useContext(RagChatContext);

  const [userInput, setUserInput] = useState("");
  const { sessionId } = useParams({ strict: false });
  const search: { question?: string } = useSearch({
    strict: false,
  });
  const inputRef = useRef<InputRef>(null);
  const {
    data: sampleQuestions,
    isFetching: sampleQuestionsIsFetching,
    error: sampleQuestionsError,
  } = useSuggestQuestions(
    {
      session_id: sessionId ? +sessionId : undefined,
    },
    // don't make a request to get suggest questions if we know a question will be in flight soon
    !search.question,
  );

  const streamChatMutation = useStreamingChatMutation({
    onChunk: (chunk) => {
      setStreamedChat((prev) => prev + chunk);
    },
    onEvent: getOnEvent(setStreamedEvent),
    onSuccess: () => {
      setUserInput("");
      setStreamedChat("");
    },
    getController: (ctrl) => {
      setStreamedAbortController(ctrl);
    },
  });

  useEffect(() => {
    // Check if any modal is currently open
    const isModalOpen = document.querySelector(
      ".ant-modal-root, .ant-modal-mask",
    );

    if (inputRef.current && !isModalOpen) {
      inputRef.current.focus();
    }
  }, [inputRef.current, flatChatHistory.length]);

  useEffect(() => {
    if (streamChatMutation.isSuccess) {
      setStreamedAbortController(undefined);
    }
  }, [streamChatMutation.isSuccess, setStreamedAbortController]);

  const handleChat = (userInput: string) => {
    if (userInput.trim().length <= 0) {
      return;
    }
    if (userInput.length > 0) {
      if (sessionId) {
        streamChatMutation.mutate({
          query: userInput,
          session_id: +sessionId,
          configuration: createQueryConfiguration(excludeKnowledgeBase),
        });
      } else {
        newSessionCallback(userInput);
      }
    }
  };

  const handleExcludeKnowledgeBase:
    | MouseEventHandler<HTMLElement>
    | undefined = () => {
    setExcludeKnowledgeBase(() => !excludeKnowledgeBase);
  };

  const handleCancelStream = () => {
    if (streamedAbortController) {
      streamedAbortController.abort();
    }
    setStreamedAbortController(undefined);
    setStreamedChat("");
    setStreamedEvent([]);
    streamChatMutation.reset();
  };

  return (
    <div>
      <Flex vertical align="center" gap={10}>
        {flatChatHistory.length > 0 ? (
          <SuggestedQuestionsFooter
            questions={sampleQuestions?.suggested_questions ?? []}
            isLoading={sampleQuestionsIsFetching}
            error={sampleQuestionsError}
            handleChat={handleChat}
            condensedQuestion={
              flatChatHistory.length > 0
                ? flatChatHistory[flatChatHistory.length - 1].condensed_question
                : undefined
            }
          />
        ) : null}
        <Flex style={{ width: "100%" }} justify="space-between" gap={5}>
          <div style={{ position: "relative", width: "100%" }}>
            <TextArea
              ref={inputRef}
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
                if (e.shiftKey && e.key === "Enter") {
                  return null;
                } else if (e.key === "Enter") {
                  e.preventDefault();
                  handleChat(userInput);
                }
              }}
              autoSize={{ minRows: 2, maxRows: 20 }}
              disabled={streamChatMutation.isPending}
              style={{ paddingRight: 110 }}
            />
            <div
              style={{
                position: "absolute",
                right: "8px",
                bottom: "5px",
                display: "flex",
                gap: "4px",
                zIndex: 1,
              }}
            >
              {streamChatMutation.isPending ? (
                <Tooltip title="Stop streaming response">
                  <Button
                    icon={<StopOutlined />}
                    type="text"
                    size="small"
                    style={{ color: cdlRed600 }}
                    onClick={handleCancelStream}
                  />
                </Tooltip>
              ) : (
                <Flex gap={4} align="end">
                  <ToolsManagerButton />
                  <Tooltip
                    title={
                      excludeKnowledgeBase
                        ? "Knowledge base excluded from chat. "
                        : " Knowledge base included in chat. "
                    }
                  >
                    <Button
                      size="small"
                      type="text"
                      icon={
                        excludeKnowledgeBase ? (
                          <DatabaseOutlined style={{ color: cdlBlue600 }} />
                        ) : (
                          <DatabaseFilled style={{ color: cdlBlue600 }} />
                        )
                      }
                      style={{
                        display: dataSourceSize ? "block" : "none",
                      }}
                      onClick={handleExcludeKnowledgeBase}
                    />
                  </Tooltip>

                  <SessionDocuments activeSession={activeSession} />
                  <Button
                    size="small"
                    type="text"
                    onClick={() => {
                      handleChat(userInput);
                    }}
                    icon={<SendOutlined style={{ color: cdlBlue600 }} />}
                    disabled={streamChatMutation.isPending}
                  />
                </Flex>
              )}
            </div>
          </div>
        </Flex>
      </Flex>
    </div>
  );
};

export default RagChatQueryInput;
