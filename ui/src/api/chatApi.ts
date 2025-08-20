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

import {
  getRequest,
  llmServicePath,
  MutationKeys,
  postRequest,
  QueryKeys,
  UseMutationType,
} from "src/api/utils.ts";
import {
  InfiniteData,
  keepPreviousData,
  QueryClient,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { suggestedQuestionKey } from "src/api/ragQueryApi.ts";
import {
  EventSourceMessage,
  EventStreamContentType,
  fetchEventSource,
} from "@microsoft/fetch-event-source";
import { Dispatch, SetStateAction } from "react";

export interface SourceNode {
  node_id: string;
  doc_id: string;
  source_file_name: string;
  score: number;
  dataSourceId?: number;
}

export interface Evaluation {
  name: "relevance" | "faithfulness";
  value: number;
}

export interface RagMessageV2 {
  user: string;
  assistant: string;
}

export interface QueryConfiguration {
  exclude_knowledge_base: boolean;
  use_question_condensing: boolean;
}

export interface ChatMutationRequest {
  query: string;
  session_id: number;
  configuration: QueryConfiguration;
  response_id?: string;
}

interface ChatHistoryRequestType {
  session_id: number;
  limit?: number;
  offset?: number;
}

export interface ChatMessageType {
  id: string;
  session_id: number;
  source_nodes: SourceNode[];
  inference_model?: string;
  rag_message: RagMessageV2;
  evaluations: Evaluation[];
  timestamp: number;
  condensed_question?: string;
}

export interface ChatResponseFeedback {
  rating: boolean;
}

export const placeholderChatResponseId = "placeholder";

export const isPlaceholder = (chatMessage: ChatMessageType): boolean => {
  return chatMessage.id === placeholderChatResponseId;
};

export const placeholderChatResponse = (query: string): ChatMessageType => {
  return {
    id: placeholderChatResponseId,
    session_id: 0,
    source_nodes: [],
    rag_message: {
      user: query,
      assistant: "",
    },
    evaluations: [],
    timestamp: Date.now(),
  };
};

const DEFAULT_PAGE_SIZE = 10;
export const chatHistoryQueryKey = ({ session_id }: ChatHistoryRequestType) => {
  return [QueryKeys.chatHistoryQuery, { session_id }];
};

export const useChatHistoryQuery = ({
  session_id,
  offset,
  limit = DEFAULT_PAGE_SIZE,
}: ChatHistoryRequestType) => {
  const request: ChatHistoryRequestType = {
    session_id,
    offset,
    limit,
  };
  return useInfiniteQuery({
    queryKey: chatHistoryQueryKey(request),
    queryFn: ({ pageParam }) => chatHistoryQuery(request, pageParam),
    enabled: request.session_id > 0,
    placeholderData: keepPreviousData,
    initialData: { pages: [], pageParams: [0] },
    initialPageParam: 0,
    getPreviousPageParam: (data) => data.next_id,
    getNextPageParam: (data) => data.previous_id,
    refetchOnWindowFocus: false,
  });
};

export interface ChatHistoryResponse {
  data: ChatMessageType[];
  next_id: number | null;
  previous_id: number | null;
}

export const chatHistoryQuery = async (
  request: ChatHistoryRequestType,
  pageParam: number | undefined
): Promise<ChatHistoryResponse> => {
  const params = new URLSearchParams();
  if (request.limit !== undefined) {
    params.append("limit", request.limit.toString());
  }
  if (pageParam !== undefined) {
    params.append("offset", pageParam.toString());
  }

  return await getRequest(
    `${llmServicePath}/sessions/${request.session_id.toString()}/chat-history?` +
      params.toString()
  );
};

export const appendPlaceholderToChatHistory = (
  query: string,
  cachedData?: InfiniteData<ChatHistoryResponse>
): InfiniteData<ChatHistoryResponse> => {
  if (!cachedData || cachedData.pages.length === 0) {
    const firstPage: ChatHistoryResponse = {
      data: [placeholderChatResponse(query)],
      next_id: null,
      previous_id: null,
    };
    return {
      pages: [firstPage],
      pageParams: [0],
    };
  }

  const pageParams = cachedData.pageParams.map((pageParam, index) =>
    index > 0 && typeof pageParam === "number" ? ++pageParam : pageParam
  );

  const pages = cachedData.pages.map((page) => {
    return {
      ...page,
      next_id: typeof page.next_id === "number" ? ++page.next_id : page.next_id,
      previous_id:
        typeof page.previous_id === "number"
          ? ++page.previous_id
          : page.previous_id,
    };
  });

  const lastPage = pages[pages.length - 1];
  const filteredLastPageData = lastPage.data.filter(
    (chatMessage) => !isPlaceholder(chatMessage)
  );
  return {
    pageParams,
    pages: [
      ...pages.slice(0, -1),
      {
        ...lastPage,
        data: [...filteredLastPageData, placeholderChatResponse(query)],
      },
    ],
  };
};

export const replacePlaceholderInChatHistory = (
  data: ChatMessageType,
  cachedData?: InfiniteData<ChatHistoryResponse>
): InfiniteData<ChatHistoryResponse> => {
  if (!cachedData || cachedData.pages.length == 0) {
    return (
      cachedData ?? {
        pages: [{ data: [data], previous_id: null, next_id: null }],
        pageParams: [0],
      }
    );
  }
  const pages = cachedData.pages.map((page) => {
    const pages = page.data.map((message) => {
      if (isPlaceholder(message)) {
        return data;
      }
      return message;
    });
    return {
      ...page,
      data: pages,
    };
  });

  const noDataInPages = pages[pages.length - 1].data.length === 0;

  return {
    pageParams: cachedData.pageParams,
    pages: noDataInPages
      ? [{ data: [data], previous_id: null, next_id: null }]
      : pages,
  };
};

export const replaceMessageInChatHistoryById = (
  data: ChatMessageType,
  cachedData?: InfiniteData<ChatHistoryResponse>
): InfiniteData<ChatHistoryResponse> => {
  if (!cachedData || cachedData.pages.length == 0) {
    return (
      cachedData ?? {
        pages: [{ data: [data], previous_id: null, next_id: null }],
        pageParams: [0],
      }
    );
  }
  const pages = cachedData.pages.map((page) => {
    const updated = page.data.map((message) =>
      message.id === data.id ? data : message
    );
    return {
      ...page,
      data: updated,
    };
  });
  return {
    pageParams: cachedData.pageParams,
    pages,
  };
};

const updateAssistantTextById = (
  messageId: string,
  assistantText: string,
  cachedData?: InfiniteData<ChatHistoryResponse>
): InfiniteData<ChatHistoryResponse> => {
  if (!cachedData || cachedData.pages.length == 0) {
    return cachedData ?? { pages: [], pageParams: [0] };
  }
  const pages = cachedData.pages.map((page) => {
    const updated = page.data.map((message) => {
      if (message.id === messageId) {
        return {
          ...message,
          rag_message: {
            ...message.rag_message,
            assistant: assistantText,
          },
        };
      }
      return message;
    });
    return {
      ...page,
      data: updated,
    };
  });
  return {
    pageParams: cachedData.pageParams,
    pages,
  };
};

export const createQueryConfiguration = (
  excludeKnowledgeBase: boolean
): QueryConfiguration => {
  return {
    exclude_knowledge_base: excludeKnowledgeBase,
    use_question_condensing: false,
  };
};

export const useRatingMutation = ({
  onSuccess,
  onError,
}: UseMutationType<ChatResponseFeedback>) => {
  return useMutation({
    mutationKey: [MutationKeys.ratingMutation],
    mutationFn: ratingMutation,
    onSuccess: onSuccess,
    onError: (error: Error) => onError?.(error),
  });
};

const ratingMutation = async ({
  sessionId,
  responseId,
  rating,
}: {
  sessionId: string;
  responseId: string;
  rating: boolean;
}): Promise<ChatResponseFeedback> => {
  return await postRequest(
    `${llmServicePath}/sessions/${sessionId}/responses/${responseId}/rating`,
    { rating }
  );
};

export const useFeedbackMutation = ({
  onSuccess,
  onError,
}: UseMutationType<ChatResponseFeedback>) => {
  return useMutation({
    mutationKey: [MutationKeys.feedbackMutation],
    mutationFn: feedbackMutation,
    onSuccess: onSuccess,
    onError: (error: Error) => onError?.(error),
  });
};

const feedbackMutation = async ({
  sessionId,
  responseId,
  feedback,
}: {
  sessionId: string;
  responseId: string;
  feedback: string;
}): Promise<ChatResponseFeedback> => {
  return await postRequest(
    `${llmServicePath}/sessions/${sessionId}/responses/${responseId}/feedback`,
    { feedback }
  );
};

export interface ChatMutationResponse {
  text?: string;
  response_id?: string;
  error?: string;
  event?: ChatEvent;
}

export interface ChatEvent {
  type: string;
  name: string;
  data?: string;
  timestamp: number;
}

const customChatMessage = (
  variables: ChatMutationRequest,
  message: string,
  prefix: string
) => {
  const uuid = crypto.randomUUID();
  const customMessage: ChatMessageType = {
    id: `${prefix}${uuid}`,
    session_id: variables.session_id,
    source_nodes: [],
    rag_message: {
      user: variables.query,
      assistant: message,
    },
    evaluations: [],
    timestamp: Date.now(),
  };
  return customMessage;
};

export const ERROR_PREFIX_ID = "error-";
export const CANCELED_PREFIX_ID = "canceled-";

const errorChatMessage = (variables: ChatMutationRequest, error: Error) => {
  return customChatMessage(variables, error.message, ERROR_PREFIX_ID);
};

const canceledChatMessage = (variables: ChatMutationRequest) => {
  return customChatMessage(
    variables,
    "Request canceled by user",
    CANCELED_PREFIX_ID
  );
};

interface StreamingChatCallbacks {
  onChunk: (msg: string) => void;
  onEvent: (event: ChatEvent) => void;
  getController?: (ctrl: AbortController) => void;
}

const modifyPlaceholderInChatHistory = (
  queryClient: QueryClient,
  variables: ChatMutationRequest,
  replacementMessage: ChatMessageType
) => {
  queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
    chatHistoryQueryKey({
      session_id: variables.session_id,
      offset: 0,
    }),
    (cachedData) =>
      replacePlaceholderInChatHistory(replacementMessage, cachedData)
  );
};

const handlePrepareController = (
  getController: ((ctrl: AbortController) => void) | undefined,
  queryClient: QueryClient,
  request: ChatMutationRequest
) => {
  return (ctrl: AbortController) => {
    if (getController) {
      getController(ctrl);

      const onAbort = () => {
        if (request.response_id) {
          queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
            chatHistoryQueryKey({ session_id: request.session_id }),
            (cachedData) =>
              updateAssistantTextById(
                request.response_id as string,
                canceledChatMessage(request).rag_message.assistant,
                cachedData
              )
          );
        } else {
          modifyPlaceholderInChatHistory(
            queryClient,
            request,
            canceledChatMessage(request)
          );
        }
        ctrl.signal.removeEventListener("abort", onAbort);
      };

      ctrl.signal.addEventListener("abort", onAbort);
    }
  };
};

const handleStreamingSuccess = (
  request: ChatMutationRequest,
  messageId: string,
  queryClient: QueryClient,
  onSuccess:
    | ((data: ChatMessageType, request?: unknown, context?: unknown) => unknown)
    | undefined,
  handleError: (request: ChatMutationRequest, error: Error) => void,
  onError: ((error: Error) => void) | undefined
) => {
  fetch(
    `${llmServicePath}/sessions/${request.session_id.toString()}/chat-history/${messageId}`
  )
    .then(async (res) => {
      const message = (await res.json()) as ChatMessageType;
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
        chatHistoryQueryKey({
          session_id: request.session_id,
        }),
        (cachedData) =>
          request.response_id
            ? replaceMessageInChatHistoryById(message, cachedData)
            : replacePlaceholderInChatHistory(message, cachedData)
      );
      queryClient
        .invalidateQueries({
          queryKey: suggestedQuestionKey(request.session_id),
        })
        .catch((error: unknown) => {
          console.error(error);
        });
      onSuccess?.(message);
    })
    .catch((error: unknown) => {
      handleError(request, error as Error);
      onError?.(error as Error);
    });
};

export const useStreamingChatMutation = ({
  onError,
  onSuccess,
  onChunk,
  onEvent,
  getController,
}: UseMutationType<ChatMessageType> & StreamingChatCallbacks) => {
  const queryClient = useQueryClient();
  const handleError = (variables: ChatMutationRequest, error: Error) => {
    if (variables.response_id) {
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
        chatHistoryQueryKey({ session_id: variables.session_id }),
        (cachedData) =>
          updateAssistantTextById(
            variables.response_id as string,
            error.message,
            cachedData
          )
      );
    } else {
      const errorMessage = errorChatMessage(variables, error);
      modifyPlaceholderInChatHistory(queryClient, variables, errorMessage);
    }
  };
  return useMutation({
    mutationKey: [MutationKeys.chatMutation],
    mutationFn: (request: ChatMutationRequest) => {
      const convertError = (errorMessage: string) => {
        const error = new Error(errorMessage);
        handleError(request, error);
        onError?.(error);
      };
      const handleGetController = handlePrepareController(
        getController,
        queryClient,
        request
      );

      // Wrap onChunk to update the in-place message assistant text during regeneration
      let accumulatedText = "";
      const onChunkWrapped = (chunk: string) => {
        accumulatedText += chunk;
        if (request.response_id) {
          queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
            chatHistoryQueryKey({ session_id: request.session_id }),
            (cachedData) =>
              updateAssistantTextById(
                request.response_id as string,
                accumulatedText,
                cachedData
              )
          );
        }
        onChunk(chunk);
      };

      return streamChatMutation(
        request,
        onChunkWrapped,
        onEvent,
        convertError,
        handleGetController
      );
    },
    onMutate: (variables) => {
      // Only append a placeholder when we are creating a brand new response
      // For regeneration (response_id provided), we update the existing entry in-place after success
      if (!variables.response_id) {
        queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
          chatHistoryQueryKey({
            session_id: variables.session_id,
          }),
          (cachedData) =>
            appendPlaceholderToChatHistory(variables.query, cachedData)
        );
      } else {
        // For regeneration, immediately clear the assistant text of the existing message
        queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
          chatHistoryQueryKey({
            session_id: variables.session_id,
          }),
          (cachedData) =>
            updateAssistantTextById(
              variables.response_id as string,
              "",
              cachedData
            )
        );
      }
    },
    onSuccess: (messageId, variables) => {
      if (!messageId) {
        return;
      }
      handleStreamingSuccess(
        variables,
        messageId,
        queryClient,
        onSuccess,
        handleError,
        onError
      );
    },
    onError: (error: Error, variables) => {
      handleError(variables, error);
      onError?.(error);
    },
  });
};

const streamChatMutation = async (
  request: ChatMutationRequest,
  onChunk: (chunk: string) => void,
  onEvent: (event: ChatEvent) => void,
  onError: (error: string) => void,
  getController?: (ctrl: AbortController) => void
): Promise<string> => {
  const ctrl = new AbortController();
  if (getController) {
    getController(ctrl);
  }
  let responseId = "";
  await fetchEventSource(
    `${llmServicePath}/sessions/${request.session_id.toString()}/stream-completion`,
    {
      openWhenHidden: true,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: request.query,
        configuration: request.configuration,
        response_id: request.response_id,
      }),
      signal: ctrl.signal,
      onmessage(msg: EventSourceMessage) {
        try {
          const data = JSON.parse(msg.data) as ChatMutationResponse;

          if (data.error) {
            onError(data.error);
            ctrl.abort();
          }

          if (data.text) {
            onChunk(data.text);
          }

          if (data.event) {
            onEvent(data.event);
          }

          if (data.response_id) {
            responseId = data.response_id;
          }
        } catch (error) {
          console.error("Error parsing message data:", error);
          onError(
            `An error occurred while processing the response.  Error message: ${JSON.stringify(msg)}. Error details: ${JSON.stringify(error)}.`
          );
          ctrl.abort();
        }
      },
      onerror(err: unknown) {
        ctrl.abort();
        onError(String(err));
      },
      async onopen(response) {
        if (
          response.ok &&
          response.headers.get("content-type")?.includes(EventStreamContentType)
        ) {
          await Promise.resolve();
        } else if (
          response.status >= 400 &&
          response.status < 500 &&
          response.status !== 429
        ) {
          onError("An error occurred: " + response.statusText);
        } else {
          onError("An error occurred: " + response.statusText);
        }
      },
    }
  );
  return responseId;
};

export const getOnEvent = (
  setStreamedEvent: Dispatch<SetStateAction<ChatEvent[]>>
) => {
  return (event: ChatEvent) => {
    if (event.type === "done") {
      setStreamedEvent([]);
    } else {
      setStreamedEvent((prev) => {
        return [...prev, event];
      });
    }
  };
};
