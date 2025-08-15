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
  Collapse,
  Flex,
  Form,
  FormInstance,
  Input,
  Modal,
  Popover,
  Select,
  Slider,
  Switch,
  Tag,
  Typography,
} from "antd";
import {
  Model,
  useGetLlmModels,
  useGetRerankingModels,
} from "src/api/modelsApi.ts";
import { useTransformModelOptions } from "src/utils/modelUtils.ts";
import { ResponseChunksRange } from "pages/RagChatTab/Settings/ResponseChunksSlider.tsx";
import { useContext, useEffect } from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import {
  CreateSessionRequest,
  UpdateSessionRequest,
  useUpdateSessionMutation,
} from "src/api/sessionApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { QueryKeys } from "src/api/utils.ts";
import { useQueryClient } from "@tanstack/react-query";

import { formatDataSource } from "src/utils/formatters.ts";
import { cdlOrange500, cdlWhite } from "src/cuix/variables.ts";

export const onInferenceModelChange = (
  changedValues: Partial<Omit<CreateSessionRequest, "id">>,
  form: FormInstance<Omit<CreateSessionRequest, "id">>,
  llmModels?: Model[],
) => {
  if (changedValues.inferenceModel) {
    const model = llmModels?.find(
      (model) => model.model_id === changedValues.inferenceModel,
    );
    form.setFieldValue(
      ["queryConfiguration", "enableToolCalling"],
      model?.tool_calling_supported ?? false,
    );
  }
};

const ChatSettingsModal = ({
  modelIsOpen,
  closeModal,
}: {
  modelIsOpen: boolean;
  closeModal: () => void;
}) => {
  const { data: llmModels } = useGetLlmModels();
  const { data: rerankingModels } = useGetRerankingModels();
  const llmModelOptions = useTransformModelOptions(llmModels);
  const rerankModelOptions = useTransformModelOptions(rerankingModels);
  const {
    dataSourcesQuery: { dataSources },
    activeSession,
  } = useContext(RagChatContext);
  const [form] = Form.useForm<Omit<CreateSessionRequest, "id">>();
  const queryClient = useQueryClient();
  const updateSession = useUpdateSessionMutation({
    onError: (error) => {
      console.error(error);
      messageQueue.error("Failed to update session");
    },
    onSuccess: async () => {
      messageQueue.success("Session updated successfully");
      await queryClient.invalidateQueries({
        queryKey: [QueryKeys.getSessions],
      });
      closeModal();
    },
  });

  if (!activeSession) {
    return null;
  }

  useEffect(() => {
    if (modelIsOpen && activeSession.name) {
      form.setFieldsValue({
        name: activeSession.name,
      });
    }
  }, [activeSession.name, form.setFieldsValue, modelIsOpen]);

  const handleUpdateSession = () => {
    form
      .validateFields()
      .then((values) => {
        const request: UpdateSessionRequest = {
          ...values,
          id: activeSession.id,
          projectId: activeSession.projectId,
          dataSourceIds: values.dataSourceIds,
          queryConfiguration: {
            ...activeSession.queryConfiguration,
            enableToolCalling: values.queryConfiguration.enableToolCalling,
            enableHyde: values.queryConfiguration.enableHyde,
            enableSummaryFilter: values.queryConfiguration.enableSummaryFilter,
            enableStreaming: values.queryConfiguration.enableStreaming,
          },
        };
        updateSession.mutate(request);
      })
      .catch(() => {
        messageQueue.error("Please fill all the required fields.");
      });
  };

  const advancedOptions = () => [
    {
      key: "1",
      forceRender: true,
      label: "Advanced Options",
      children: (
        <>
          <Form.Item
            name={["queryConfiguration", "enableToolCalling"]}
            initialValue={activeSession.queryConfiguration.enableToolCalling}
            valuePropName="checked"
            label={
              <Popover
                title="Tool Calling (Beta)"
                content={
                  <Typography style={{ width: 300 }}>
                    Enable tool calling. This feature is highly dependent on the
                    power of the selected response synthesizer model.
                  </Typography>
                }
              >
                <Tag
                  style={{
                    backgroundColor: cdlOrange500,
                    color: cdlWhite,
                    borderRadius: 10,
                  }}
                >
                  &beta;
                </Tag>
                Enable Tool Calling
              </Popover>
            }
          >
            <Switch />
          </Form.Item>
          <Form.Item
            name={["queryConfiguration", "enableHyde"]}
            initialValue={activeSession.queryConfiguration.enableHyde}
            valuePropName="checked"
            label={
              <Popover
                title="HyDE (Hypothetical Document Embeddings)"
                content={
                  <Typography style={{ width: 300 }}>
                    HyDE is a technique that can improve the quality of the
                    chunk retrieval by generating a hypothetical response to a
                    query. This hypothetical response is then used to retrieve
                    the most relevant chunks.
                  </Typography>
                }
              >
                Enable HyDE
              </Popover>
            }
          >
            <Switch />
          </Form.Item>
          <Form.Item<CreateSessionRequest>
            name={["queryConfiguration", "enableSummaryFilter"]}
            initialValue={activeSession.queryConfiguration.enableSummaryFilter}
            valuePropName="checked"
            label={
              <Popover
                title="Enable Summary-Based Filtering"
                content={
                  <Typography style={{ width: 300 }}>
                    This option will provide two-stage retrieval, using the
                    document summary to provide an additional way to get access
                    to the appropriate chunks of the document. In order for this
                    to work, a summarization model must be assigned to the
                    knowledge base.
                  </Typography>
                }
              >
                Enable Summary Filtering
              </Popover>
            }
          >
            <Switch />
          </Form.Item>
          <Form.Item<CreateSessionRequest>
            name={["queryConfiguration", "enableStreaming"]}
            initialValue={activeSession.queryConfiguration.enableStreaming}
            valuePropName="checked"
            label={
              <Popover
                title="Enable Streaming"
                content={
                  <Typography style={{ width: 300 }}>
                    When enabled, responses are streamed in real-time as they
                    are generated. When disabled, the complete response is
                    delivered all at once after generation is finished.
                    Streaming provides better user experience for longer
                    responses.
                  </Typography>
                }
              >
                Enable Streaming
              </Popover>
            }
          >
            <Switch />
          </Form.Item>
        </>
      ),
    },
  ];

  return (
    <Modal
      title={
        <Typography.Paragraph
          style={{ margin: 0, fontSize: 16, fontWeight: 500, width: "95%" }}
          ellipsis={{ rows: 1 }}
        >
          Chat Settings: {activeSession.name}
        </Typography.Paragraph>
      }
      open={modelIsOpen}
      onCancel={closeModal}
      destroyOnHidden={true}
      onOk={handleUpdateSession}
      maskClosable={false}
      width={600}
    >
      <Flex vertical gap={10}>
        <Form
          autoCorrect="off"
          form={form}
          clearOnDestroy={true}
          onValuesChange={(
            changedValues: Partial<Omit<CreateSessionRequest, "id">>,
          ) => {
            onInferenceModelChange(changedValues, form, llmModels);
          }}
        >
          <Form.Item
            name="dataSourceIds"
            label="Knowledge Base"
            initialValue={activeSession.dataSourceIds}
          >
            <Select
              mode="multiple"
              disabled={dataSources.length === 0}
              allowClear={true}
              options={dataSources.map((value) => {
                return formatDataSource(value);
              })}
            />
          </Form.Item>
          <Form.Item
            name="name"
            label="Name"
            initialValue={activeSession.name}
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="inferenceModel"
            label="Response synthesizer model"
            initialValue={
              activeSession.inferenceModel ??
              (llmModels ? llmModels[0].model_id : "")
            }
            rules={[{ required: true, message: "Please select a model" }]}
          >
            <Select options={llmModelOptions} />
          </Form.Item>
          <Form.Item
            name="rerankModel"
            label="Reranking model"
            initialValue={activeSession.rerankModel}
          >
            <Select allowClear options={rerankModelOptions} />
          </Form.Item>
          <Form.Item
            name="responseChunks"
            initialValue={activeSession.responseChunks}
            label="Maximum number of documents"
          >
            <Slider marks={ResponseChunksRange} min={1} max={20} />
          </Form.Item>
          <Collapse items={advancedOptions()} />
        </Form>
      </Flex>
    </Modal>
  );
};

export default ChatSettingsModal;
