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
  });
};

export interface ChatHistoryResponse {
  data: ChatMessageType[];
  next_id: number | null;
  previous_id: number | null;
}

export const chatHistoryQuery = async (
  request: ChatHistoryRequestType,
  pageParam: number | undefined,
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
      params.toString(),
  );
};

export const appendPlaceholderToChatHistory = (
  query: string,
  cachedData?: InfiniteData<ChatHistoryResponse>,
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
    index > 0 && typeof pageParam === "number" ? ++pageParam : pageParam,
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
  return {
    pageParams,
    pages: [
      ...pages.slice(0, -1),
      {
        ...lastPage,
        data: [...lastPage.data, placeholderChatResponse(query)],
      },
    ],
  };
};

export const replacePlaceholderInChatHistory = (
  data: ChatMessageType,
  cachedData?: InfiniteData<ChatHistoryResponse>,
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

export const createQueryConfiguration = (
  excludeKnowledgeBase: boolean,
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
    { rating },
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
    { feedback },
  );
};

export interface ChatMutationResponse {
  text?: string;
  response_id?: string;
  error?: string;
}

export interface CrewEventResponse {
  event_type: string;
  crew_name?: string;
  timestamp: number;
  error?: string;
}

const errorChatMessage = (variables: ChatMutationRequest, error: Error) => {
  const uuid = crypto.randomUUID();
  const errorMessage: ChatMessageType = {
    id: `error-${uuid}`,
    session_id: variables.session_id,
    source_nodes: [],
    rag_message: {
      user: variables.query,
      assistant: error.message,
    },
    evaluations: [],
    timestamp: Date.now(),
  };
  return errorMessage;
};

export const useStreamingChatMutation = ({
  onError,
  onSuccess,
  onChunk,
}: UseMutationType<ChatMessageType> & { onChunk: (msg: string) => void }) => {
  const queryClient = useQueryClient();
  const handleError = (variables: ChatMutationRequest, error: Error) => {
    const errorMessage = errorChatMessage(variables, error);
    queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
      chatHistoryQueryKey({
        session_id: variables.session_id,
        offset: 0,
      }),
      (cachedData) => replacePlaceholderInChatHistory(errorMessage, cachedData),
    );
  };
  return useMutation({
    mutationKey: [MutationKeys.chatMutation],
    mutationFn: (request: ChatMutationRequest) => {
      const convertError = (errorMessage: string) => {
        const error = new Error(errorMessage);
        handleError(request, error);
        onError?.(error);
      };
      return streamChatMutation(request, onChunk, convertError);
    },
    onMutate: (variables) => {
      queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
        chatHistoryQueryKey({
          session_id: variables.session_id,
        }),
        (cachedData) =>
          appendPlaceholderToChatHistory(variables.query, cachedData),
      );
    },
    onSuccess: (messageId, variables) => {
      if (!messageId) {
        return;
      }
      fetch(
        `${llmServicePath}/sessions/${variables.session_id.toString()}/chat-history/${messageId}`,
      )
        .then(async (res) => {
          const message = (await res.json()) as ChatMessageType;
          queryClient.setQueryData<InfiniteData<ChatHistoryResponse>>(
            chatHistoryQueryKey({
              session_id: variables.session_id,
            }),
            (cachedData) =>
              replacePlaceholderInChatHistory(message, cachedData),
          );
          queryClient
            .invalidateQueries({
              queryKey: suggestedQuestionKey(variables.session_id),
            })
            .catch((error: unknown) => {
              console.error(error);
            });
          onSuccess?.(message);
        })
        .catch((error: unknown) => {
          handleError(variables, error as Error);
          onError?.(error as Error);
        });
    },
    onError: (error: Error, variables) => {
      handleError(variables, error);
      onError?.(error);
    },
  });
};

const streamCrewEvents = async (
  sessionId: number,
  onEvent?: (event: CrewEventResponse) => void,
  onError?: (error: string) => void,
): Promise<void> => {
  const ctrl = new AbortController();

  try {
    await fetchEventSource(
      `${llmServicePath}/sessions/${sessionId.toString()}/crew-events`,
      {
        method: "GET",
        signal: ctrl.signal,
        onmessage(msg: EventSourceMessage) {
          const data = JSON.parse(msg.data) as CrewEventResponse;

          if (data.error) {
            ctrl.abort();
            onError?.(data.error);
            return;
          }

          onEvent?.(data);
        },
        onerror(err: unknown) {
          ctrl.abort();
          onError?.(String(err));
        },
        async onopen(response) {
          if (
            response.ok &&
            response.headers
              .get("content-type")
              ?.includes(EventStreamContentType)
          ) {
            await Promise.resolve();
          } else if (
            response.status >= 400 &&
            response.status < 500 &&
            response.status !== 429
          ) {
            onError?.("An error occurred: " + response.statusText);
          } else {
            onError?.("An error occurred: " + response.statusText);
          }
        },
      },
    );
  } catch (error) {
    onError?.(String(error));
  }
};

const streamChatMutation = async (
  request: ChatMutationRequest,
  onChunk: (chunk: string) => void,
  onError: (error: string) => void,
): Promise<string> => {
  const ctrl = new AbortController();
  let responseId = "";
  await fetchEventSource(
    `${llmServicePath}/sessions/${request.session_id.toString()}/stream-completion`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: request.query,
        configuration: request.configuration,
      }),
      signal: ctrl.signal,
      onmessage(msg: EventSourceMessage) {
        const data = JSON.parse(msg.data) as ChatMutationResponse;

        if (data.error) {
          ctrl.abort();
          onError(data.error);
        }

        if (data.text) {
          onChunk(data.text);
        }
        if (data.response_id) {
          responseId = data.response_id;
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
          // Start streaming crew events after chat stream is opened
          await streamCrewEvents(
            request.session_id,
            (event) => {
              console.log("Crew event received:", event);
              // Handle crew events here if needed
            },
            (error) => {
              console.error("Crew events stream error:", error);
            },
          );
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
    },
  );
  return responseId;
};
