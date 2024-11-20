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

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getRequest,
  llmServicePath,
  MutationKeys,
  postRequest,
  QueryKeys,
} from "src/api/utils.ts";
import { QueryConfiguration } from "src/api/chatApi.ts";

export interface RagMessage {
  role: "user" | "assistant";
  content: string;
}

export interface SuggestQuestionsRequest {
  data_source_id: string;
  configuration: QueryConfiguration;
  session_id: string;
}

export interface SuggestQuestionsResponse {
  suggested_questions: string[];
}

export const suggestedQuestionKey = (
  data_source_id: SuggestQuestionsRequest["data_source_id"],
) => {
  return [
    QueryKeys.suggestQuestionsQuery,
    {
      data_source_id,
    },
  ];
};

export const useSuggestQuestions = (request: SuggestQuestionsRequest) => {
  return useQuery({
    // Note: We only want to invalidate the query when the data_source_id changes, not when chat history changes
    // eslint-disable-next-line @tanstack/query/exhaustive-deps
    queryKey: suggestedQuestionKey(request.data_source_id),
    queryFn: () => suggestQuestionsQuery(request),
    enabled:
      Boolean(request.data_source_id) &&
      Boolean(request.configuration.model_name),
    gcTime: 0,
  });
};

const suggestQuestionsQuery = async (
  request: SuggestQuestionsRequest,
): Promise<SuggestQuestionsResponse> => {
  return await postRequest(
    `${llmServicePath}/sessions/${request.session_id}/suggest-questions`,
    request,
  );
};

type ChunkContents = string;

interface ChunkContentsRequest {
  data_source_id: string;
  chunk_id: string;
}

export const useGetChunkContents = () => {
  return useMutation({
    mutationKey: [MutationKeys.getChunkContents],
    mutationFn: getChunkContents,
  });
};

const getChunkContents = async (
  request: ChunkContentsRequest,
): Promise<ChunkContents> => {
  return getRequest(
    `${llmServicePath}/data_sources/${request.data_source_id}/chunks/${request.chunk_id}`,
  );
};
