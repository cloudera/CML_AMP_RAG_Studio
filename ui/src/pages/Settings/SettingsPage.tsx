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
import { Alert, Button, Flex, Form, Typography } from "antd";
import { ProjectConfig, useGetAmpConfig } from "src/api/ampMetadataApi.ts";
import { ReactNode, useState } from "react";
import { ModelSource, useGetModelSource } from "src/api/modelsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import useModal from "src/utils/useModal.ts";
import RestartAppModal from "pages/Settings/RestartAppModal.tsx";
import { ProcessingFields } from "pages/Settings/ProcessingFields.tsx";
import { FileStorageFields } from "pages/Settings/FileStorageFields.tsx";
import { ModelProviderFields } from "pages/Settings/ModelProviderFields.tsx";
import { AuthenticationFields } from "pages/Settings/AuthenticationFields.tsx";
import { getDataSourcesQueryOptions } from "src/api/dataSourceApi.ts";
import { useSuspenseQuery } from "@tanstack/react-query";
import { getSessionsQueryOptions } from "src/api/sessionApi.ts";
import { SummaryStorageFields } from "pages/Settings/SummaryStorageFields.tsx";

export type FileStorage = "AWS" | "Local";

export const StyledHelperText = ({ children }: { children: ReactNode }) => {
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
  const { data: projectConfig } = useGetAmpConfig();
  const [selectedFileStorage, setSelectedFileStorage] = useState<FileStorage>(
    projectConfig?.aws_config.document_bucket_name ? "AWS" : "Local",
  );
  const [modelProvider, setModelProvider] = useState<ModelSource | undefined>(
    currentModelSource,
  );
  const dataSourcesQuery = useSuspenseQuery(getDataSourcesQueryOptions);
  const sessionsQuery = useSuspenseQuery(getSessionsQueryOptions);

  const enableSettingsModification =
    dataSourcesQuery.data.length === 0 && sessionsQuery.data.length === 0;

  return (
    <Flex style={{ marginLeft: 60 }} vertical>
      {!projectConfig?.is_valid_config && (
        <Alert
          message={
            <div>
              <Typography.Text>
                For initial configuration of RAG Studio, please provide valid
                credentials for CAII, AWS Bedrock, or Azure OpenAI.
              </Typography.Text>
            </div>
          }
          type="warning"
          showIcon
          style={{ marginTop: 40, width: "fit-content" }}
        />
      )}
      {!enableSettingsModification && (
        <Alert
          message="Storage and model provider settings cannot be modified if there are any chats or knowledge bases."
          type="warning"
          showIcon
          style={{ marginTop: 40, width: "fit-content" }}
        />
      )}

      <Form form={form} labelCol={{ offset: 1 }}>
        <Typography.Title level={4}>Processing Settings</Typography.Title>
        <ProcessingFields projectConfig={projectConfig} />
        <Flex align={"baseline"} gap={8}>
          <Typography.Title level={4}>File Storage</Typography.Title>
          <Typography.Text type="secondary">
            (Choose one option)
          </Typography.Text>
        </Flex>
        <FileStorageFields
          selectedFileStorage={selectedFileStorage}
          setSelectedFileStorage={setSelectedFileStorage}
          projectConfig={projectConfig}
          enableModification={enableSettingsModification}
        />
        <Flex align={"baseline"} gap={8}>
          <Typography.Title level={4}>Summary Storage</Typography.Title>
          <Typography.Text type="secondary">
            (Choose one option)
          </Typography.Text>
        </Flex>
        <SummaryStorageFields
          form={form}
          projectConfig={projectConfig}
          enableModification={enableSettingsModification}
        />
        <Flex align={"baseline"} gap={8}>
          <Typography.Title level={4}>Model Provider</Typography.Title>
          <Typography.Text type="secondary">
            (Choose one option)
          </Typography.Text>
        </Flex>
        <ModelProviderFields
          modelProvider={modelProvider}
          setModelProvider={setModelProvider}
          projectConfig={projectConfig}
          enableModification={enableSettingsModification}
        />
        <Typography.Title level={4}>Authentication</Typography.Title>
        <AuthenticationFields
          projectConfig={projectConfig}
          modelProvider={modelProvider}
          selectedFileStorage={selectedFileStorage}
          enableModification={enableSettingsModification}
        />
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
      <RestartAppModal
        confirmationModal={confirmationModal}
        form={form}
        selectedFileStorage={selectedFileStorage}
        modelProvider={modelProvider}
      />
    </Flex>
  );
};

export default SettingsPage;
