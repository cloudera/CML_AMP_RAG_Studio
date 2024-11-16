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
import { queryOptions, useQuery } from "@tanstack/react-query";
import {
  ApiError,
  CustomError,
  getRequest,
  llmServicePath,
  QueryKeys,
} from "src/api/utils.ts";

export interface Model {
  name?: string;
  model_id: string;
  available?: boolean;
  replica_count?: number;
}

export const useGetLlmModels = () => {
  return useQuery({
    queryKey: [QueryKeys.getLlmModels],
    queryFn: async () => {
      return await getLlmModels();
    },
  });
};

export const getLlmModelsQueryOptions = queryOptions({
  queryKey: [QueryKeys.getLlmModels],
  queryFn: async () => {
    return await getLlmModels();
  },
});

const getLlmModels = async (): Promise<Model[]> => {
  return await getRequest(`${llmServicePath}/index/models/llm`);
};

export const useGetEmbeddingModels = () => {
  return useQuery({
    queryKey: [QueryKeys.getEmbeddingModels],
    queryFn: async () => {
      return await getEmbeddingModels();
    },
  });
};

const getEmbeddingModels = async (): Promise<Model[]> => {
  return await getRequest(`${llmServicePath}/index/models/embeddings`);
};

type ModelSource = "CAII" | "Bedrock";

export const getModelSourceQueryOptions = queryOptions({
  queryKey: [QueryKeys.getModelSource],
  queryFn: async () => {
    return await getModelSource();
  },
});

const getModelSource = async (): Promise<ModelSource> => {
  return await getRequest(`${llmServicePath}/index/models/model_source`);
};

export const useTestLlmModel = (model_id: string) => {
  return useQuery({
    queryKey: [QueryKeys.testLlmModel, { model_id }],
    queryFn: async () => {
      return await testLlmModel(model_id);
    },
    enabled: !!model_id,
    retry: false,
  });
};

const testLlmModel = async (model_id: string): Promise<string> => {
  return await fetch(
    `${llmServicePath}/index/models/llm/${model_id}/test`,
  ).then(async (res) => {
    if (!res.ok) {
      const detail = (await res.json()) as CustomError;
      throw new ApiError(detail.message ?? detail.detail, res.status);
    }

    return (await res.json()) as Promise<string>;
  });
};

export const useTestEmbeddingModel = (model_id: string) => {
  return useQuery({
    queryKey: [QueryKeys.testEmbeddingModel, { model_id }],
    queryFn: async () => {
      return await testEmbeddingModel(model_id);
    },
    retry: false,
    enabled: !!model_id,
  });
};

const testEmbeddingModel = async (model_id: string): Promise<string> => {
  return await fetch(
    `${llmServicePath}/index/models/embedding/${model_id}/test`,
  ).then(async (res) => {
    if (!res.ok) {
      const detail = (await res.json()) as CustomError;
      throw new ApiError(detail.message ?? detail.detail, res.status);
    }

    return (await res.json()) as Promise<string>;
  });
};
