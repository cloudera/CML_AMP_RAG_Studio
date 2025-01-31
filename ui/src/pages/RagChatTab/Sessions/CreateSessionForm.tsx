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

import { Form, FormInstance, Input, Select, Slider } from "antd";
import { DataSourceType } from "src/api/dataSourceApi.ts";
import { CreateSessionType } from "pages/RagChatTab/Sessions/CreateSessionModal.tsx";
import { transformModelOptions } from "src/utils/modelUtils.ts";
import { ResponseChunksRange } from "pages/RagChatTab/Settings/ResponseChunksSlider.tsx";
import { useGetLlmModels, useGetRerankingModels } from "src/api/modelsApi.ts";

export interface CreateSessionFormProps {
  form: FormInstance<CreateSessionType>;
  dataSources?: DataSourceType[];
}

const layout = {
  labelCol: { span: 12 },
  wrapperCol: { span: 12 },
};

const CreateSessionForm = ({ form, dataSources }: CreateSessionFormProps) => {
  const { data } = useGetLlmModels();
  const { data: rerankingModels } = useGetRerankingModels();

  const formatDataSource = (value: DataSourceType) => {
    return {
      ...value,
      label: value.name,
      value: value.id,
    };
  };

  return (
    <Form
      id="create-new-session"
      form={form}
      style={{ width: "100%", paddingTop: 20 }}
      {...layout}
      onValuesChange={(changedValues: CreateSessionType, allValues) => {
        if (changedValues.dataSourceId && !allValues.name) {
          const dataSource = dataSources?.find(
            (value) => value.id === changedValues.dataSourceId,
          );
          form.setFieldsValue({
            name: dataSource?.name,
          });
        }
      }}
    >
      <Form.Item
        name="dataSourceId"
        label="Knowledge Base"
        rules={[{ required: true }]}
      >
        <Select
          disabled={dataSources?.length === 0}
          options={dataSources?.map((value) => formatDataSource(value))}
        />
      </Form.Item>
      <Form.Item name="name" label="Name" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item<CreateSessionType>
        initialValue={
          data === undefined || data.length === 0 ? "" : data[0].model_id
        }
        name="inferenceModel"
        label="Response synthesizer model"
        rules={[{ required: true }]}
      >
        <Select options={transformModelOptions(data)} />
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
        initialValue={5}
        label="Maximum number of documents"
      >
        <Slider marks={ResponseChunksRange} min={1} max={10} />
      </Form.Item>
    </Form>
  );
};

export default CreateSessionForm;
