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
import { Divider, Flex, Form, Input, Radio, Switch, Typography } from "antd";
import { ProjectConfig, useGetAmpConfig } from "src/api/ampMetadataApi.ts";
import { useState } from "react";
import { ModelSource, useGetModelSource } from "src/api/modelsApi.ts";

const isModelSource = (value: string): value is ModelSource => {
  return value === "CAII" || value === "Bedrock" || value === "Azure";
};

type FileStorage = "AWS" | "Local";

const SettingsPage = () => {
  const [form] = Form.useForm<ProjectConfig>();
  const { data: projectConfig } = useGetAmpConfig();
  const { data: currentModelSource } = useGetModelSource();
  const [selectedFileStorage, setSelectedFileStorage] = useState<
    "AWS" | "Local"
  >(projectConfig?.aws_config.document_bucket_name ? "AWS" : "Local");
  const [modelProvider, setModelProvider] = useState<ModelSource | undefined>(
    currentModelSource,
  );

  const FileStorageFields = () => (
    <Flex vertical style={{ maxWidth: 600 }}>
      <Radio.Group
        style={{ marginBottom: 20 }}
        optionType="button"
        buttonStyle="solid"
        onChange={(e) => {
          if (e.target.value === "AWS" || e.target.value === "Local") {
            setSelectedFileStorage(e.target.value as FileStorage);
          }
        }}
        value={selectedFileStorage}
        options={[
          { value: "Local", label: "Project Filesystem" },
          { value: "AWS", label: "AWS S3" },
        ]}
      />
      {selectedFileStorage === "Local" && (
        <Typography.Paragraph italic>
          CAI Project file system will be used for file storage.
        </Typography.Paragraph>
      )}
      <Form.Item
        label={"Document Bucket Name"}
        initialValue={projectConfig?.aws_config.document_bucket_name}
        name="document_bucket_name"
        required
        tooltip="Document Bucket Name"
        hidden={selectedFileStorage !== "AWS"}
      >
        <Input placeholder="Document Bucket Name" />
      </Form.Item>
      <Form.Item
        label={"Bucket Prefix"}
        initialValue={projectConfig?.aws_config.bucket_prefix}
        name="bucket_prefix"
        required
        tooltip="Bucket Prefix"
        hidden={selectedFileStorage !== "AWS"}
      >
        <Input placeholder="Bucket Prefix" />
      </Form.Item>
    </Flex>
  );

  const ModelProviderContent = () => (
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
          { value: "CAII", label: "CAII" },
          { value: "Bedrock", label: "AWS Bedrock" },
          { value: "Azure", label: "Azure OpenAI" },
        ]}
      />
      {modelProvider === "Bedrock" && (
        <Typography.Paragraph italic>
          Please provide the AWS region and credentials for Bedrock below.
        </Typography.Paragraph>
      )}
      <Form.Item
        label={"CAII Domain"}
        initialValue={projectConfig?.caii_config.caii_domain}
        name={["caii_config", "caii_domain"]}
        required
        tooltip="Domain for CAII"
        hidden={modelProvider !== "CAII"}
      >
        <Input placeholder="CAII Domain" />
      </Form.Item>
      <Form.Item
        label={"Azure OpenAI Endpoint"}
        initialValue={projectConfig?.azure_config.openai_endpoint}
        name="openai_endpoint"
        required
        hidden={modelProvider !== "Azure"}
      >
        <Input placeholder="Azure OpenAI Endpoint" />
      </Form.Item>
      <Form.Item
        label={"API Version"}
        initialValue={projectConfig?.azure_config.openai_api_version}
        name="openai_model"
        required
        hidden={modelProvider !== "Azure"}
      >
        <Input placeholder="API Version" />
      </Form.Item>
    </Flex>
  );

  const AuthenticationFields = () => (
    <Flex vertical style={{ maxWidth: 600 }}>
      {modelProvider === "CAII" && selectedFileStorage === "Local" && (
        <Typography.Paragraph italic>
          No authentication needed
        </Typography.Paragraph>
      )}
      <Form.Item
        label={"AWS Region"}
        initialValue={projectConfig?.aws_config.region}
        name="region"
        required
        tooltip="AWS Region"
        hidden={modelProvider !== "Bedrock" && selectedFileStorage !== "AWS"}
      >
        <Input placeholder="AWS Region" />
      </Form.Item>
      <Form.Item
        label={"Access Key ID"}
        initialValue={projectConfig?.aws_config.access_key_id}
        name="access_key_id"
        required
        tooltip="Access Key ID"
        hidden={modelProvider !== "Bedrock" && selectedFileStorage !== "AWS"}
      >
        <Input placeholder="Access Key ID" />
      </Form.Item>
      <Form.Item
        label={"Secret Access Key"}
        initialValue={projectConfig?.aws_config.secret_access_key}
        name="secret_access_key"
        required
        tooltip="Secret Access Key"
        hidden={modelProvider !== "Bedrock" && selectedFileStorage !== "AWS"}
      >
        <Input placeholder="Secret Access Key" type="password" />
      </Form.Item>
      <Form.Item
        label={"Azure OpenAI Key"}
        initialValue={projectConfig?.azure_config.openai_key}
        name="openai_key"
        required
        hidden={modelProvider !== "Azure"}
      >
        <Input placeholder="Azure OpenAI Key" type="password" />
      </Form.Item>
    </Flex>
  );

  const ProcessingFields = () => {
    return (
      <Flex vertical style={{ maxWidth: 600 }}>
        <Form.Item
          label="Enhanced PDF Processing"
          name={["use_enhanced_pdf_processing"]}
          initialValue={projectConfig?.use_enhanced_pdf_processing}
          valuePropName="checked"
          tooltip={
            "Enable enhanced PDF processing for enhanced PDF processing."
          }
        >
          <Switch />
        </Form.Item>
      </Flex>
    );
  };

  return (
    <Flex style={{ marginLeft: 60 }} vertical>
      <Form form={form} labelCol={{ offset: 1 }} disabled={true}>
        <Typography.Title level={4}>Processing Settings</Typography.Title>
        <ProcessingFields />
        <Divider />
        <Typography.Title level={4}>File Storage</Typography.Title>
        <FileStorageFields />
        <Typography.Title level={4}>Model Provider</Typography.Title>
        <ModelProviderContent />
        <Typography.Title level={4}>Authentication</Typography.Title>
        <AuthenticationFields />
      </Form>
    </Flex>
  );
};

export default SettingsPage;
