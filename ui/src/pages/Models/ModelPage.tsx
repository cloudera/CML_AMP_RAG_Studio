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

import { Alert, Button, Card, Flex, Input, Typography } from "antd";
import EmbeddingModelTable from "pages/Models/EmbeddingModelTable.tsx";
import {
  ModelSource,
  useGetEmbeddingModels,
  useGetLlmModels,
  useGetModelSource,
  useGetRerankingModels,
} from "src/api/modelsApi.ts";
import InferenceModelTable from "pages/Models/InferenceModelTable.tsx";
import RerankingModelTable from "pages/Models/RerankingModelTable.tsx";
import { useState } from "react";
import { useSetCdpToken } from "src/api/ampMetadataApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError, QueryKeys } from "src/api/utils.ts";

const ModelPageAlert = ({
  error,
  type,
}: {
  error: Error | null;
  type: string;
}) => {
  if (!error) {
    return null;
  }
  return (
    <Alert
      style={{ margin: 10 }}
      message={`${type} model error: ${error.message}`}
      type="error"
    />
  );
};

const CDPTokenInput = () => {
  const [token, setToken] = useState("");
  const queryClient = useQueryClient();
  const setAuthToken = useSetCdpToken({
    onSuccess: () => {
      messageQueue.success("Token saved successfully");
      queryClient
        .invalidateQueries({
          queryKey: [QueryKeys.getRerankingModels],
        })
        .catch(() => {
          messageQueue.error("Error occurred fetching reranking models");
        });
      queryClient
        .invalidateQueries({
          queryKey: [QueryKeys.getLlmModels],
        })
        .catch(() => {
          messageQueue.error("Error occurred fetching LLM models");
        });
      queryClient
        .invalidateQueries({
          queryKey: [QueryKeys.getEmbeddingModels],
        })
        .catch(() => {
          messageQueue.error("Error occurred fetching embedding models");
        });
    },
    onError: () => {
      messageQueue.error("Error occurred setting token");
    },
  });

  const handleSubmit = () => {
    if (token) {
      setAuthToken.mutate(token);
    }
  };

  return (
    <Card title="CDP Token Expired - Update to use Cloudera AI Inference Models">
      <Flex gap={8}>
        <Input
          placeholder="CDP Token"
          value={token}
          onChange={(e) => {
            setToken(e.target.value);
          }}
        />
        <Button onClick={handleSubmit}>Submit</Button>
      </Flex>
    </Card>
  );
};

const checkHandledCaiiError = (
  inferenceError: Error | null | ApiError,
  rerankingError: Error | null | ApiError,
  embeddingError: Error | null | ApiError,
) => {
  return (
    (inferenceError instanceof ApiError &&
      (inferenceError.status === 401 || inferenceError.status === 500)) ||
    (rerankingError instanceof ApiError &&
      (rerankingError.status === 401 || rerankingError.status === 500)) ||
    (embeddingError instanceof ApiError &&
      (embeddingError.status === 401 || embeddingError.status === 500))
  );
};

const ModelErrors = ({
  inferenceError,
  rerankingError,
  embeddingError,
  modelSource,
}: {
  inferenceError: Error | null;
  embeddingError: Error | null;
  rerankingError: Error | null;
  modelSource?: ModelSource;
}) => {
  if (modelSource === "CAII") {
    if (checkHandledCaiiError(inferenceError, rerankingError, embeddingError)) {
      return null;
    }
  }

  return (
    <>
      <ModelPageAlert error={inferenceError} type="Inference" />
      <ModelPageAlert error={embeddingError} type="Embedding" />
      <ModelPageAlert error={rerankingError} type="Reranking" />
    </>
  );
};
const ModelPage = () => {
  const {
    data: embeddingModels,
    isLoading: areEmbeddingModelsLoading,
    error: embeddingError,
  } = useGetEmbeddingModels();
  const {
    data: inferenceModels,
    isLoading: areInferenceModelsLoading,
    error: inferenceError,
  } = useGetLlmModels();
  const {
    data: rerankingModels,
    isLoading: areRerankingModelsLoading,
    error: rerankingError,
  } = useGetRerankingModels();
  const getModelSource = useGetModelSource();

  return (
    <Flex vertical style={{ marginLeft: 60 }}>
      <ModelErrors
        inferenceError={inferenceError}
        embeddingError={embeddingError}
        rerankingError={rerankingError}
        modelSource={getModelSource.data}
      />
      <Flex vertical style={{ width: "80%", maxWidth: 1000 }} gap={20}>
        {checkHandledCaiiError(
          inferenceError,
          rerankingError,
          embeddingError,
        ) ? (
          <CDPTokenInput />
        ) : null}
        <Typography.Title level={3}>Embedding Models</Typography.Title>
        <EmbeddingModelTable
          embeddingModels={embeddingModels}
          areEmbeddingModelsLoading={areEmbeddingModelsLoading}
        />
        <Typography.Title level={3}>Inference Models</Typography.Title>
        <InferenceModelTable
          inferenceModels={inferenceModels}
          areInferenceModelsLoading={areInferenceModelsLoading}
        />
        <Typography.Title level={3}>Reranking Models</Typography.Title>
        <RerankingModelTable
          rerankingModels={rerankingModels}
          areRerankingModelsLoading={areRerankingModelsLoading}
        />
      </Flex>
    </Flex>
  );
};

export default ModelPage;
