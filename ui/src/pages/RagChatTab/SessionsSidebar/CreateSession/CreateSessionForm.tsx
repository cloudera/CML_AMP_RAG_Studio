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
  Collapse,
  Form,
  FormInstance,
  Input,
  Popover,
  Select,
  Slider,
  Switch,
  Tag,
  Typography,
} from "antd";
import { DataSourceType } from "src/api/dataSourceApi.ts";
import { CreateSessionType } from "pages/RagChatTab/SessionsSidebar/CreateSession/CreateSessionModal.tsx";
import { transformModelOptions } from "src/utils/modelUtils.ts";
import { ResponseChunksRange } from "pages/RagChatTab/Settings/ResponseChunksSlider.tsx";
import { useGetLlmModels, useGetRerankingModels } from "src/api/modelsApi.ts";
import { formatDataSource } from "src/utils/formatters.ts";
import { cdlOrange500, cdlWhite } from "src/cuix/variables.ts";
import { onInferenceModelChange } from "pages/RagChatTab/Settings/ChatSettingsModal.tsx";

export interface CreateSessionFormProps {
  form: FormInstance<CreateSessionType>;
  dataSources?: DataSourceType[];
}

const layout = {
  labelCol: { span: 12 },
  wrapperCol: { span: 12 },
};

const CreateSessionForm = ({ form, dataSources }: CreateSessionFormProps) => {
  const { data: llmModels } = useGetLlmModels();
  const { data: rerankingModels } = useGetRerankingModels();

  const advancedOptions = () => [
    {
      key: "1",
      forceRender: true,
      label: "Advanced Options",
      children: (
        <>
          <Form.Item<CreateSessionType>
            name={["queryConfiguration", "enableToolCalling"]}
            initialValue={
              llmModels === undefined || llmModels.length === 0
                ? false
                : llmModels[0].tool_calling_supported
            }
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
          <Form.Item<CreateSessionType>
            name={["queryConfiguration", "enableHyde"]}
            initialValue={false}
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
          <Form.Item<CreateSessionType>
            name={["queryConfiguration", "enableSummaryFilter"]}
            initialValue={true}
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
        </>
      ),
    },
  ];

  return (
    <Form
      id="create-new-session"
      form={form}
      style={{ width: "100%", paddingTop: 20 }}
      {...layout}
      onValuesChange={(
        changedValues: Partial<Omit<CreateSessionType, "id">>,
      ) => {
        onInferenceModelChange(changedValues, form, llmModels);
      }}
    >
      <Form.Item name="dataSourceIds" label="Knowledge Base">
        <Select
          mode="multiple"
          disabled={dataSources?.length === 0}
          allowClear={true}
          options={dataSources?.map((value) => formatDataSource(value))}
        />
      </Form.Item>
      <Form.Item
        name="name"
        label="Name"
        rules={[{ required: false }]}
        initialValue={""}
      >
        <Input />
      </Form.Item>
      <Form.Item<CreateSessionType>
        initialValue={
          llmModels === undefined || llmModels.length === 0
            ? ""
            : llmModels[0].model_id
        }
        name="inferenceModel"
        label="Response synthesizer model"
        rules={[{ required: true }]}
      >
        <Select options={transformModelOptions(llmModels)} />
      </Form.Item>
      <Form.Item
        name="rerankModel"
        label="Reranking model"
        initialValue={
          rerankingModels?.length ? rerankingModels[0].model_id : ""
        }
      >
        <Select allowClear options={transformModelOptions(rerankingModels)} />
      </Form.Item>
      <Form.Item<CreateSessionType>
        name="responseChunks"
        initialValue={10}
        label="Maximum number of documents"
      >
        <Slider marks={ResponseChunksRange} min={1} max={20} />
      </Form.Item>
      <Collapse items={advancedOptions()} />
    </Form>
  );
};

export default CreateSessionForm;
