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

import { ModelSource } from "src/api/modelsApi.ts";
import { ProjectConfig } from "src/api/ampMetadataApi.ts";
import { Flex, Form, Input, Radio } from "antd";
import { StyledHelperText } from "pages/Settings/AmpSettingsPage.tsx";

const isModelSource = (value: string): value is ModelSource => {
  return (
    value === "CAII" ||
    value === "Bedrock" ||
    value === "Azure" ||
    value === "OpenAI"
  );
};

export const ModelProviderFields = ({
  setModelProvider,
  modelProvider,
  projectConfig,
  enableModification,
}: {
  setModelProvider: (value: ModelSource) => void;
  modelProvider?: ModelSource;
  projectConfig?: ProjectConfig | null;
  enableModification?: boolean;
}) => (
  <Flex vertical style={{ maxWidth: 600 }}>
    <Radio.Group
      style={{ marginBottom: 20 }}
      optionType="button"
      buttonStyle="solid"
      onChange={(e) => {
        if (e.target.value && isModelSource(e.target.value as string)) {
          setModelProvider(e.target.value as ModelSource);
        }
      }}
      value={modelProvider}
      options={[
        { value: "CAII", label: "Cloudera AI" },
        { value: "Bedrock", label: "AWS Bedrock" },
        { value: "Azure", label: "Azure OpenAI" },
        { value: "OpenAI", label: "OpenAI" },
      ]}
      disabled={!enableModification}
    />
    {modelProvider === "Bedrock" && (
      <StyledHelperText>
        Please provide the AWS region and credentials for Bedrock below.
      </StyledHelperText>
    )}
    <Form.Item
      label={"Cloudera AI Inference Domain"}
      initialValue={projectConfig?.caii_config.caii_domain}
      name={["caii_config", "caii_domain"]}
      required={modelProvider === "CAII"}
      rules={[{ required: modelProvider === "CAII" }]}
      tooltip="The domain of the Cloudera AI Inference service."
      hidden={modelProvider !== "CAII"}
    >
      <Input
        placeholder="Cloudera AI Inference Domain"
        disabled={!enableModification}
      />
    </Form.Item>
    <Form.Item
      label={"Azure OpenAI Endpoint"}
      initialValue={projectConfig?.azure_config.openai_endpoint}
      name={["azure_config", "openai_endpoint"]}
      required={modelProvider === "Azure"}
      rules={[{ required: modelProvider === "Azure" }]}
      tooltip="The endpoint of the Azure OpenAI service. This can be found in the Azure portal."
      hidden={modelProvider !== "Azure"}
    >
      <Input
        placeholder="https://myendpoint.openai.azure.com/"
        disabled={!enableModification}
      />
    </Form.Item>
    <Form.Item
      label={"OpenAI Base URL"}
      initialValue={projectConfig?.openai_config.openai_api_base}
      name={["openai_config", "openai_api_base"]}
      tooltip="The base URL for the OpenAI service."
      hidden={modelProvider !== "OpenAI"}
    >
      <Input
        placeholder="https://myendpoint.openai.com/"
        disabled={!enableModification}
      />
    </Form.Item>
    <Form.Item
      label={"API Version"}
      initialValue={projectConfig?.azure_config.openai_api_version}
      name={["azure_config", "openai_api_version"]}
      required={modelProvider === "Azure"}
      rules={[{ required: modelProvider === "Azure" }]}
      tooltip="The API version of the Azure OpenAI service. This can be found in the Azure portal."
      hidden={modelProvider !== "Azure"}
    >
      <Input placeholder="2024-05-01-preview" disabled={!enableModification} />
    </Form.Item>
  </Flex>
);
