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
import { Flex, Form, Input } from "antd";
import { FileStorage, StyledHelperText } from "pages/Settings/SettingsPage.tsx";

export const AuthenticationFields = ({
  modelProvider,
  selectedFileStorage,
  projectConfig,
}: {
  modelProvider?: ModelSource;
  selectedFileStorage?: FileStorage;
  projectConfig?: ProjectConfig;
}) => (
  <Flex vertical style={{ maxWidth: 600 }}>
    {modelProvider === "CAII" && selectedFileStorage === "Local" && (
      <StyledHelperText>No additional authentication needed.</StyledHelperText>
    )}
    <Form.Item
      label={"AWS Region"}
      initialValue={projectConfig?.aws_config.region}
      name={["aws_config", "region"]}
      required={modelProvider === "Bedrock" || selectedFileStorage === "AWS"}
      rules={[
        {
          required:
            modelProvider === "Bedrock" || selectedFileStorage === "AWS",
        },
      ]}
      tooltip="AWS Region where Bedrock is configured and/or the S3 bucket is located."
      hidden={modelProvider !== "Bedrock" && selectedFileStorage !== "AWS"}
    >
      <Input placeholder="us-west-2" />
    </Form.Item>
    <Form.Item
      label={"Access Key ID"}
      initialValue={projectConfig?.aws_config.access_key_id}
      name={["aws_config", "access_key_id"]}
      required={modelProvider === "Bedrock" || selectedFileStorage === "AWS"}
      rules={[
        {
          required:
            modelProvider === "Bedrock" || selectedFileStorage === "AWS",
        },
      ]}
      tooltip="Access Key ID"
      hidden={modelProvider !== "Bedrock" && selectedFileStorage !== "AWS"}
    >
      <Input placeholder="access-key-id" />
    </Form.Item>
    <Form.Item
      label={"Secret Access Key"}
      initialValue={projectConfig?.aws_config.secret_access_key}
      name={["aws_config", "secret_access_key"]}
      required={modelProvider === "Bedrock" || selectedFileStorage === "AWS"}
      rules={[
        {
          required:
            modelProvider === "Bedrock" || selectedFileStorage === "AWS",
        },
      ]}
      tooltip="AWS Secret Access Key"
      hidden={modelProvider !== "Bedrock" && selectedFileStorage !== "AWS"}
    >
      <Input placeholder="secret-access-key" type="password" />
    </Form.Item>
    <Form.Item
      label={"Azure OpenAI Key"}
      initialValue={projectConfig?.azure_config.openai_key}
      name={["azure_config", "openai_key"]}
      required={modelProvider === "Azure"}
      rules={[{ required: modelProvider === "Azure" }]}
      hidden={modelProvider !== "Azure"}
    >
      <Input placeholder="azure-openai-key" type="password" />
    </Form.Item>
  </Flex>
);
