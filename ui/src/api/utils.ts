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

export const ragPath = "/api/v1/rag";
export const llmServicePath = "/llm-service";

export const paths = {
  files: "files",
  dataSources: "dataSources",
  sessions: "sessions",
};

export interface UseMutationType<T> {
  onSuccess?:
    | ((data: T, variables?: unknown, context?: unknown) => unknown)
    | undefined;
  onError?: (error: Error) => void;
}

export enum MutationKeys {
  "createRagDocuments" = "createRagDocuments",
  "deleteRagDocument" = "deleteRagDocument",
  "chatMutation" = "chatMutation",
  "createDataSource" = "createDataSource",
  "updateDataSource" = "updateDataSource",
  "getCdfConfig" = "getCdfConfig",
  "deleteDataSource" = "deleteDataSource",
  "getChunkContents" = "getChunkContents",
  "createSession" = "createSession",
  "deleteChatHistory" = "deleteChatHistory",
  "deleteSession" = "deleteSession",
  "updateAmp" = "updateAmp",
  "testLlmModel" = "testLlmModel",
  "testEmbeddingModel" = "testEmbeddingModel",
  "visualizeDataSourceWithUserQuery" = "visualizeDataSourceWithUserQuery",
}

export enum QueryKeys {
  "getRagDocuments" = "getRagDocuments",
  "getDataSources" = "getDataSources",
  "getDataSourceById" = "getDataSourceById",
  "chatHistoryQuery" = "chatHistoryQuery",
  "suggestQuestionsQuery" = "suggestQuestionsQuery",
  "getSessions" = "getSessions",
  "getDocumentSummary" = "getDocumentSummary",
  "getAmpUpdateStatus" = "getAmpUpdateStatus",
  "getDataSourceSummary" = "getDataSourceSummary",
  "getAmpUpdateJobStatus" = "getAmpUpdateJobStatus",
  "getLlmModels" = "getLlmModels",
  "getEmbeddingModels" = "getEmbeddingModels",
  "getModelSource" = "getModelSource",
  "getVisualizeDataSource" = "getVisualizeDataSource",
}

export const commonHeaders = {
  Accept: "application/json",
};

export interface ApiBackendErrorDetail {
  error: string;
  message: string;
  status: number;
}

export interface CustomError {
  detail?: string;
  message?: string;
}

export class ApiError extends Error {
  constructor(
    message = "unknown",
    public status: number,
  ) {
    super(message);
    this.name = "CustomError";
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

export const postRequest = async <T>(
  url: string,
  body: Record<never, never>,
): Promise<T> => {
  const res = await fetch(url, {
    method: "POST",
    body: JSON.stringify(body),
    headers: {
      ...commonHeaders,
      "Content-Type": "application/json",
    },
  });
  if (!res.ok) {
    const detail = (await res.json()) as CustomError;
    throw new ApiError(detail.message ?? detail.detail, res.status);
  }
  return await ((await res.json()) as Promise<T>);
};

export const getRequest = async <T>(url: string): Promise<T> => {
  const res = await fetch(url, {
    method: "GET",
    headers: { ...commonHeaders },
  });

  if (!res.ok) {
    const detail = (await res.json()) as CustomError;
    throw new ApiError(detail.message ?? detail.detail, res.status);
  }

  return await ((await res.json()) as Promise<T>);
};

export const deleteRequest = async (url: string) => {
  const res = await fetch(url, {
    method: "DELETE",
    headers: commonHeaders,
  });

  if (!res.ok) {
    const detail = (await res.json()) as CustomError;
    throw new ApiError(detail.message ?? detail.detail, res.status);
  }
};
