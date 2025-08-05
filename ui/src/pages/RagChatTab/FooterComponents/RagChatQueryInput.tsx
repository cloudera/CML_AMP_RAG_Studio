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

import {
  Button,
  Flex,
  Input,
  InputRef,
  Select,
  Tooltip,
  Typography,
} from "antd";
import {
  MouseEventHandler,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  DatabaseFilled,
  DatabaseOutlined,
  SendOutlined,
  StopOutlined,
} from "@ant-design/icons";
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
import ChatSessionDocuments from "pages/RagChatTab/FooterComponents/ChatSessionDocuments.tsx";
import { ChatSessionDragAndDrop } from "pages/RagChatTab/FooterComponents/ChatSessionDragAndDrop.tsx";
import useModal from "src/utils/useModal.ts";
import { formatDataSource } from "src/utils/formatters.ts";
import { useTransformModelOptions } from "src/utils/modelUtils.ts";
import { getLlmModelsQueryOptions } from "src/api/modelsApi.ts";
import { useUpdateSessionMutation } from "src/api/sessionApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { QueryKeys } from "src/api/utils.ts";
import { DataSourceType } from "src/api/dataSourceApi.ts";

const { TextArea } = Input;

export interface NewSessionCallbackProps {
  userInput: string;
  selectedDataSourceIds: number[];
  inferenceModel?: string;
}

const RagChatQueryInput = ({
  newSessionCallback,
  validDataSources,
}: {
  newSessionCallback: (props: NewSessionCallbackProps) => void;
  validDataSources?: DataSourceType[];
}) => {
  const {
    activeSession,
    excludeKnowledgeBaseState: [excludeKnowledgeBase, setExcludeKnowledgeBase],
    chatHistoryQuery: { flatChatHistory },
    dataSourceSize,
    dataSourcesQuery: { dataSourcesStatus, dataSources: allDataSources },
    streamedChatState: [, setStreamedChat],
    streamedEventState: [, setStreamedEvent],
    streamedAbortControllerState: [
      streamedAbortController,
      setStreamedAbortController,
    ],
  } = useContext(RagChatContext);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedDataSourceIds, setSelectedDataSourceIds] = useState<number[]>(
    [],
  );

  const [userInput, setUserInput] = useState("");
  const { sessionId } = useParams({ strict: false });
  const search: { question?: string } = useSearch({
    strict: false,
  });
  const { data: llmModels } = useSuspenseQuery(getLlmModelsQueryOptions);
  const [inferenceModel, setInferenceModel] = useState<string>(() => {
    if (sessionId) {
      if (activeSession?.inferenceModel) {
        return activeSession.inferenceModel;
      }
      return "";
    }
    return llmModels.length > 0 ? llmModels[0].model_id : "";
  });
  const inputRef = useRef<InputRef>(null);
  const queryClient = useQueryClient();
  const dataSources = validDataSources ?? allDataSources;
  const modelOptions = useTransformModelOptions(llmModels);

  const updateSession = useUpdateSessionMutation({
    onSuccess: () => {
      queryClient
        .invalidateQueries({
          queryKey: [QueryKeys.getSessions],
        })
        .catch((error: unknown) => {
          messageQueue.error(`Error refetching sessions: ${String(error)}`);
        });
    },
    onError: (error) => {
      messageQueue.error(`Failed to update session: ${error.message}`);
    },
  });

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

  // Chunk queue and timer refs
  const chunkQueueRef = useRef<string[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Modified onChunk to queue chunks
  const streamChatMutation = useStreamingChatMutation({
    onChunk: (chunk) => {
      chunkQueueRef.current.push(chunk);
    },
    onEvent: getOnEvent(setStreamedEvent),
    onSuccess: () => {
      console.log("Chat streaming completed successfully.");
      setUserInput("");
      setStreamedChat("");
      // Clear queue and timer
      chunkQueueRef.current = [];
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    },
    getController: (ctrl) => {
      setStreamedAbortController(ctrl);
    },
  });

  // Timer effect to flush chunk queue to streamed chat
  useEffect(() => {
    if (streamChatMutation.isPending) {
      timerRef.current = setInterval(() => {
        if (chunkQueueRef.current.length > 0) {
          setStreamedChat((prev) => prev + chunkQueueRef.current.join(""));
          chunkQueueRef.current = [];
        }
      }, 10);
    } else {
      // Clean up timer and queue when not streaming
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      chunkQueueRef.current = [];
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      chunkQueueRef.current = [];
    };
  }, [streamChatMutation.isPending, setStreamedChat]);

  const documentModal = useModal();

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

  useEffect(() => {
    if (activeSession?.inferenceModel) {
      setInferenceModel(activeSession.inferenceModel);
    }
  }, [activeSession?.inferenceModel]);

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
        newSessionCallback({
          userInput,
          selectedDataSourceIds,
          inferenceModel,
        });
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

  const handleChangeInferenceModel = (modelId: string) => {
    setInferenceModel(modelId);
    if (activeSession) {
      const supportsToolCalling = llmModels.find(
        (model) => model.model_id === modelId,
      )?.tool_calling_supported;
      updateSession.mutate({
        ...activeSession,
        inferenceModel: modelId,
        queryConfiguration: {
          ...activeSession.queryConfiguration,
          enableToolCalling: supportsToolCalling ?? false,
        },
      });
    }
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
        {!documentModal.isModalOpen ? (
          <ChatSessionDragAndDrop
            isDragging={isDragging}
            setIsDragging={setIsDragging}
          />
        ) : null}
        {!isDragging ? (
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
                autoSize={{ minRows: 1, maxRows: 20 }}
                disabled={streamChatMutation.isPending}
                style={{ paddingBottom: 30 }}
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
                    {!activeSession && dataSources.length > 0 ? (
                      <Select
                        mode="multiple"
                        placeholder="Knowledge base(s)"
                        style={{
                          marginTop: 4,
                          minWidth: 167,
                        }}
                        options={dataSources.map((ds) => formatDataSource(ds))}
                        onChange={setSelectedDataSourceIds}
                        value={selectedDataSourceIds}
                        size="small"
                        variant="borderless"
                        optionFilterProp="label"
                        popupMatchSelectWidth={false}
                      />
                    ) : null}
                    <Tooltip title={"Inference Model"}>
                      <Select
                        style={{
                          marginTop: 4,
                          minWidth: 168,
                        }}
                        size="small"
                        popupMatchSelectWidth={false}
                        variant="borderless"
                        optionFilterProp="label"
                        value={inferenceModel}
                        onChange={handleChangeInferenceModel}
                        options={modelOptions}
                        labelRender={(label) => (
                          <Typography.Text
                            style={{ fontSize: 14, color: "rgba(0,0,0,0.25)" }}
                            type={"secondary"}
                          >
                            {label.label}
                          </Typography.Text>
                        )}
                      />
                    </Tooltip>
                    <ToolsManagerButton />
                    <Tooltip
                      title={
                        excludeKnowledgeBase
                          ? "Knowledge base excluded from chat."
                          : "Knowledge base included in chat."
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

                    <ChatSessionDocuments
                      activeSession={activeSession}
                      documentModal={documentModal}
                    />
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
        ) : null}
      </Flex>
    </div>
  );
};

export default RagChatQueryInput;
