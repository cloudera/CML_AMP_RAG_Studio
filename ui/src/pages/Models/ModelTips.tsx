/*
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2025
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
 */

import { ModelSource } from "src/api/modelsApi.ts";
import { Collapse, CollapseProps, Flex, Typography } from "antd";
import { CaretRightOutlined, InfoCircleOutlined } from "@ant-design/icons";
import { cdlGray050 } from "src/cuix/variables.ts";

const helpText = {
  CAII: (
    <Typography>
      <ul>
        <li>
          Cloudera AI models must be enabled in the Cloudera AI Model Hub to use
          them within RAG Studio.
        </li>
        <li>
          At least one Inference and one Embedding model must available in the
          Model Hub.
        </li>
      </ul>
    </Typography>
  ),
  Azure: (
    <Typography>
      <ul>
        <li>
          Azure OpenAI models must be deployed in the Azure OpenAI portal.
        </li>
        <li>
          The default models for Azure OpenAI are as follows. Note that these
          will still need to be enabled in Azure OpenAI.
          <li>Inference model: gpt-35-turbo</li>
          <li>Embedding model: text-embedding-3-small</li>
        </li>
        <li>The deployment name in Azure OpenAI must match the model name.</li>
      </ul>
    </Typography>
  ),
  Bedrock: (
    <Typography>
      <ul>
        <li>
          Access to Amazon Bedrock models may need to be granted within Bedrock.
        </li>
        <li>All enabled Inference and Embedding models will appear below.</li>
        <li>
          For reranking models, we support the following models:
          <li>Cohere Rerank v3.5</li>
          <li>Amazon Rerank v1</li>
        </li>
      </ul>
    </Typography>
  ),
  OpenAI: (
    <Typography>
      <ul>
        <li>
          OpenAI models must be enabled in the OpenAI portal to use them within
          RAG Studio.
        </li>
        <li>
          At least one Inference and one Embedding model must available in the
          OpenAI portal.
        </li>
        <li>
          We support the follow models Inference models:
          <li>gpt-4o</li>
        </li>
        <li>
          We also support the following Embedding models:
          <li>text-embedding-ada-002</li>
          <li>text-embedding-3-large</li>
        </li>
      </ul>
    </Typography>
  ),
};

const getItems: (modelSource: ModelSource) => CollapseProps["items"] = (
  modelSource,
) => [
  {
    key: "1",
    label: (
      <Flex gap={8}>
        <InfoCircleOutlined />
        Tips: {modelSource} Configuration
      </Flex>
    ),
    children: helpText[modelSource],
  },
];

const ModelTips = ({ modelSource }: { modelSource?: ModelSource }) => {
  if (!modelSource) {
    return null;
  }
  return (
    <Collapse
      ghost={true}
      expandIcon={({ isActive }) => (
        <CaretRightOutlined rotate={isActive ? 90 : 0} />
      )}
      style={{ background: cdlGray050 }}
      items={getItems(modelSource)}
    />
  );
};

export default ModelTips;
