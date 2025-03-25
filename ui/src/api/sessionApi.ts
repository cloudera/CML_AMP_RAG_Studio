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
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  deleteRequest,
  getRequest,
  llmServicePath,
  MutationKeys,
  paths,
  postRequest,
  QueryKeys,
  ragPath,
  UseMutationType,
} from "src/api/utils.ts";
import { suggestedQuestionKey } from "src/api/ragQueryApi.ts";

interface SessionQueryConfiguration {
  enableHyde: boolean;
  enableSummaryFilter: boolean;
}

export interface Session {
  id: number;
  name: string;
  dataSourceIds: number[];
  inferenceModel?: string;
  rerankModel?: string;
  responseChunks: number;
  timeCreated: number;
  timeUpdated: number;
  createdById: string;
  updatedById: string;
  lastInteractionTime: number;
  queryConfiguration: SessionQueryConfiguration;
  projectId: number;
}

export type CreateSessionRequest = Pick<
  Session,
  | "name"
  | "dataSourceIds"
  | "inferenceModel"
  | "rerankModel"
  | "responseChunks"
  | "queryConfiguration"
  | "projectId"
>;

export type UpdateSessionRequest = Pick<
  Session,
  | "queryConfiguration"
  | "responseChunks"
  | "inferenceModel"
  | "name"
  | "id"
  | "dataSourceIds"
>;

export const getSessionsQueryOptions = queryOptions({
  queryKey: [QueryKeys.getSessions],
  queryFn: async () => await getSessionsQuery(),
});

export const useGetSessions = () => {
  return useQuery({
    queryKey: [QueryKeys.getSessions],
    queryFn: async () => await getSessionsQuery(),
  });
};

export const getSessionsQuery = async (): Promise<Session[]> => {
  return await getRequest(`${ragPath}/${paths.sessions}`);
};

export const useCreateSessionMutation = ({
  onSuccess,
  onError,
}: UseMutationType<Session>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: [MutationKeys.createSession],
    mutationFn: createSessionMutation,
    onSuccess: (session) => {
      queryClient
        .invalidateQueries({
          queryKey: [QueryKeys.getSessions],
        })
        .catch((error: unknown) => {
          console.error(error);
        });
      if (onSuccess) {
        onSuccess(session);
      }
    },
    onError,
  });
};

export const createSessionMutation = async (
  request: CreateSessionRequest,
): Promise<Session> => {
  return await postRequest(`${ragPath}/${paths.sessions}`, request);
};

export const useUpdateSessionMutation = ({
  onSuccess,
  onError,
}: UseMutationType<UpdateSessionRequest>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: [MutationKeys.updateSession],
    mutationFn: updateSessionMutation,
    onSuccess: (session) => {
      queryClient
        .invalidateQueries({
          queryKey: suggestedQuestionKey(session.id),
        })
        .catch((error: unknown) => {
          console.error(error);
        });
      if (onSuccess) {
        onSuccess(session);
      }
    },
    onError,
  });
};

const updateSessionMutation = async (
  request: UpdateSessionRequest,
): Promise<Session> => {
  return await postRequest(
    `${ragPath}/${paths.sessions}/${request.id.toString()}`,
    request,
  );
};

export const useRenameNameMutation = ({
  onSuccess,
  onError,
}: UseMutationType<string>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: [MutationKeys.renameSession],
    mutationFn: renameSessionMutation,
    onSuccess: (name) => {
      queryClient
        .invalidateQueries({
          queryKey: [QueryKeys.getSessions],
        })
        .catch((error: unknown) => {
          console.error(error);
        });
      if (onSuccess) {
        onSuccess(name);
      }
    },
    onError,
  });
};

const renameSessionMutation = async (sessionId: string): Promise<string> => {
  return await postRequest(
    `${llmServicePath}/sessions/${sessionId}/rename-session`,
    {},
  );
};

export const useDeleteSessionMutation = ({
  onSuccess,
  onError,
}: UseMutationType<void>) => {
  return useMutation({
    mutationKey: [MutationKeys.deleteSession],
    mutationFn: deleteSessionMutation,
    onSuccess,
    onError,
  });
};

export const deleteSessionMutation = async (
  sessionId: string,
): Promise<void> => {
  await deleteRequest(`${ragPath}/${paths.sessions}/${sessionId}`);
};

export const useDeleteChatHistoryMutation = ({
  onSuccess,
  onError,
}: UseMutationType<void>) => {
  return useMutation({
    mutationKey: [MutationKeys.deleteChatHistory],
    mutationFn: deleteChatHistoryMutation,
    onSuccess,
    onError,
  });
};

export const deleteChatHistoryMutation = async (
  sessionId: string,
): Promise<void> => {
  await deleteRequest(`${llmServicePath}/${paths.sessions}/${sessionId}`);
};
