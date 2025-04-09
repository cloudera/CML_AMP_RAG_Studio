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
import {
  Button,
  Flex,
  Form,
  Input,
  Modal,
  Radio,
  Switch,
  Typography,
} from "antd";
import {
  JobStatus,
  ProjectConfig,
  useGetAmpConfig,
  useUpdateAmpConfig,
} from "src/api/ampMetadataApi.ts";
import { ReactNode, useEffect, useState } from "react";
import { ModelSource, useGetModelSource } from "src/api/modelsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import useModal from "src/utils/useModal.ts";
import JobStatusTracker from "src/components/AmpUpdate/JobStatusTracker.tsx";

const isModelSource = (value: string): value is ModelSource => {
  return value === "CAII" || value === "Bedrock" || value === "Azure";
};

type FileStorage = "AWS" | "Local";

const StyledHelperText = ({ children }: { children: ReactNode }) => {
  return (
    <Typography.Paragraph italic style={{ marginLeft: 24 }}>
      {children}
    </Typography.Paragraph>
  );
};

const SettingsPage = () => {
  const [form] = Form.useForm<ProjectConfig>();
  const { data: currentModelSource } = useGetModelSource();
  const confirmationModal = useModal();
  const [startPolling, setStartPolling] = useState(false);
  const [hasSeenRestarting, setHasSeenRestarting] = useState(false);
  const updateAmpConfig = useUpdateAmpConfig({
    onError: (err) => {
      messageQueue.error(err.message);
    },
    onSuccess: () => {
      messageQueue.success("Settings updated successfully");
      setStartPolling(true);
    },
  });
  const { data: projectConfig, error: projectConfigError } =
    useGetAmpConfig(startPolling);
  const [selectedFileStorage, setSelectedFileStorage] = useState<FileStorage>(
    projectConfig?.aws_config.document_bucket_name ? "AWS" : "Local",
  );
  const [modelProvider, setModelProvider] = useState<ModelSource | undefined>(
    currentModelSource,
  );

  useEffect(() => {
    if (projectConfigError) {
      setHasSeenRestarting(true);
    }
  }, [projectConfigError, setHasSeenRestarting]);

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
        <StyledHelperText>
          CAI Project file system will be used for file storage.
        </StyledHelperText>
      )}
      <Form.Item
        label={"Document Bucket Name"}
        initialValue={projectConfig?.aws_config.document_bucket_name}
        name={["aws_config", "document_bucket_name"]}
        required={selectedFileStorage === "AWS"}
        tooltip="The S3 bucket where uploaded documents are stored."
        rules={[{ required: selectedFileStorage === "AWS" }]}
        hidden={selectedFileStorage !== "AWS"}
      >
        <Input placeholder="document-bucket-name" />
      </Form.Item>
      <Form.Item
        label={"Bucket Prefix"}
        initialValue={projectConfig?.aws_config.bucket_prefix}
        name={["aws_config", "bucket_prefix"]}
        tooltip="A prefix added to all S3 paths used by RAG Studio."
        hidden={selectedFileStorage !== "AWS"}
      >
        <Input placeholder="example-prefix" />
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
        <StyledHelperText>
          Please provide the AWS region and credentials for Bedrock below.
        </StyledHelperText>
      )}
      <Form.Item
        label={"CAII Domain"}
        initialValue={projectConfig?.caii_config.caii_domain}
        name={["caii_config", "caii_domain"]}
        required={modelProvider === "CAII"}
        rules={[{ required: modelProvider === "CAII" }]}
        tooltip="The domain of the CAII service. Choosing this option will make CAII the only source of models for RAG Studio. This can be found ...... somewhere."
        hidden={modelProvider !== "CAII"}
      >
        <Input placeholder="CAII Domain" />
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
        <Input placeholder="https://myendpoint.openai.azure.com/" />
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
        <Input placeholder="2024-05-01-preview" />
      </Form.Item>
    </Flex>
  );

  const AuthenticationFields = () => (
    <Flex vertical style={{ maxWidth: 600 }}>
      {modelProvider === "CAII" && selectedFileStorage === "Local" && (
        <StyledHelperText>
          No additional authentication needed.
        </StyledHelperText>
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

  const ProcessingFields = () => {
    return (
      <Flex vertical style={{ maxWidth: 600 }}>
        <Form.Item
          label="Enhanced PDF Processing"
          name={["use_enhanced_pdf_processing"]}
          initialValue={projectConfig?.use_enhanced_pdf_processing}
          valuePropName="checked"
          tooltip={
            "Use enhanced PDF processing for better text extraction. This option makes PDF parsing take significantly longer. A GPU and at least 16G of RAM is required for this option."
          }
        >
          <Switch />
        </Form.Item>
      </Flex>
    );
  };

  const handleSubmit = () => {
    form
      .validateFields()
      .then((values) => {
        updateAmpConfig.mutate(values);
      })
      .catch(() => {
        messageQueue.error("Please fill all required fields");
      });
  };

  return (
    <Flex style={{ marginLeft: 60 }} vertical>
      <Form
        form={form}
        labelCol={{ offset: 1 }}
        disabled={false}
        onFinish={() => {
          handleSubmit();
        }}
      >
        <Typography.Title level={4}>Processing Settings</Typography.Title>
        <ProcessingFields />
        <Flex align={"baseline"} gap={8}>
          <Typography.Title level={4}>File Storage</Typography.Title>
          <Typography.Text type="secondary">
            (Choose one option)
          </Typography.Text>
        </Flex>
        <FileStorageFields />
        <Flex align={"baseline"} gap={8}>
          <Typography.Title level={4}>Model Provider</Typography.Title>
          <Typography.Text type="secondary">
            (Choose one option)
          </Typography.Text>
        </Flex>
        <ModelProviderContent />
        <Typography.Title level={4}>Authentication</Typography.Title>
        <AuthenticationFields />
        <Form.Item label={null} style={{ marginTop: 20 }}>
          <Button
            type="primary"
            onClick={() => {
              form
                .validateFields()
                .then(() => {
                  confirmationModal.setIsModalOpen(true);
                })
                .catch(() => {
                  messageQueue.error("Please fill all required fields");
                });
            }}
          >
            Submit
          </Button>
        </Form.Item>
      </Form>
      <Modal
        title="Update settings"
        okButtonProps={{ style: { display: "none" } }}
        open={confirmationModal.isModalOpen}
        destroyOnClose={true}
        loading={updateAmpConfig.isPending}
        onCancel={() => {
          confirmationModal.setIsModalOpen(false);
        }}
      >
        <Flex align="center" justify="center" vertical gap={20}>
          <Typography>
            Are you sure you want to update the settings? This will restart the
            application and may take a few minutes.
          </Typography>
          <Button
            type="primary"
            onClick={handleSubmit}
            loading={updateAmpConfig.isPending}
            disabled={updateAmpConfig.isSuccess}
          >
            Update Settings
          </Button>
          {updateAmpConfig.isSuccess ? (
            <JobStatusTracker
              jobStatus={
                projectConfigError ? JobStatus.RESTARTING : JobStatus.SUCCEEDED
              }
            />
          ) : null}
          {hasSeenRestarting && projectConfig ? (
            <>
              <Typography.Text>
                RAG Studio has been updated successfully. Please refresh the
                page to use the latest configuration.
              </Typography.Text>
              <Button
                type="primary"
                onClick={() => {
                  location.reload();
                }}
              >
                Refresh
              </Button>
            </>
          ) : null}
        </Flex>
      </Modal>
    </Flex>
  );
};

export default SettingsPage;
