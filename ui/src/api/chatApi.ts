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
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { suggestedQuestionKey } from "src/api/ragQueryApi.ts";

export interface SourceNode {
  node_id: string;
  doc_id: string;
  source_file_name: string;
  score: number;
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
  use_hyde: boolean;
}

export interface ChatMutationRequest {
  query: string;
  session_id: string;
  configuration: QueryConfiguration;
}

interface ChatHistoryRequestType {
  session_id: string;
}

export interface ChatMessageType {
  id: string;
  source_nodes: SourceNode[];
  inference_model?: string;
  rag_message: RagMessageV2;
  evaluations: Evaluation[];
  timestamp: number;
  condensed_question?: string;
}

const placeholderChatResponseId = "placeholder";

export const isPlaceholder = (chatMessage: ChatMessageType): boolean => {
  return chatMessage.id === placeholderChatResponseId;
};

export const placeholderChatResponse = (query: string): ChatMessageType => {
  return {
    id: placeholderChatResponseId,
    source_nodes: [],
    rag_message: {
      user: query,
      assistant: "",
    },
    evaluations: [],
    timestamp: Date.now(),
  };
};

export const chatHistoryQueryKey = (session_id: string) => {
  return [QueryKeys.chatHistoryQuery, { session_id }];
};

export const useChatHistoryQuery = (session_id: string) => {
  return useQuery({
    queryKey: chatHistoryQueryKey(session_id),
    queryFn: () => chatHistoryQuery({ session_id }),
    enabled: !!session_id,
    initialData: [],
  });
};

export const chatHistoryQuery = async (
  request: ChatHistoryRequestType,
): Promise<ChatMessageType[]> => {
  return await getRequest(
    `${llmServicePath}/sessions/${request.session_id}/chat-history`,
  );
};

const appendPlaceholderToChatHistory = (
  query: string,
  cachedData?: ChatMessageType[],
) => {
  if (!cachedData) {
    return [placeholderChatResponse(query)];
  }
  return [...cachedData, placeholderChatResponse(query)];
};

export const replacePlaceholderInChatHistory = (
  data: ChatMessageType,
  cachedData?: ChatMessageType[],
) => {
  if (!cachedData) {
    return [data];
  }
  return cachedData.map((message) => {
    if (isPlaceholder(message)) {
      return data;
    }
    return message;
  });
};

export const useChatMutation = ({
  onSuccess,
  onError,
}: UseMutationType<ChatMessageType>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: [MutationKeys.chatMutation],
    mutationFn: chatMutation,
    onMutate: (variables) => {
      queryClient.setQueryData<ChatMessageType[]>(
        chatHistoryQueryKey(variables.session_id),
        (cachedData) =>
          appendPlaceholderToChatHistory(variables.query, cachedData),
      );
    },
    onSuccess: (data, variables) => {
      queryClient.setQueryData<ChatMessageType[]>(
        chatHistoryQueryKey(variables.session_id),
        (cachedData) => replacePlaceholderInChatHistory(data, cachedData),
      );
      queryClient
        .invalidateQueries({
          queryKey: suggestedQuestionKey(variables.session_id),
        })
        .catch((error: unknown) => {
          console.error(error);
        });
      onSuccess?.(data);
    },
    onError: (error: Error) => onError?.(error),
  });
};

const chatMutation = async (
  request: ChatMutationRequest,
): Promise<ChatMessageType> => {
  return await postRequest(
    `${llmServicePath}/sessions/${request.session_id}/chat`,
    request,
  );
};

export const createQueryConfiguration = (
  excludeKnowledgeBase: boolean,
): QueryConfiguration => {
  return {
    exclude_knowledge_base: excludeKnowledgeBase,
    use_question_condensing: false,
    use_hyde: true,
  };
};
