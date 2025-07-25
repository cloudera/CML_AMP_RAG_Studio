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
  Alert,
  Button,
  Collapse,
  Divider,
  Form,
  FormInstance,
  Input,
  InputNumber,
  Select,
  Switch,
  Typography,
} from "antd";
import { ConnectionType, DataSourceBaseType } from "src/api/dataSourceApi";
import { useGetEmbeddingModels, useGetLlmModels } from "src/api/modelsApi.ts";
import { useEffect } from "react";
import { useTransformModelOptions } from "src/utils/modelUtils.ts";
import { useNavigate } from "@tanstack/react-router";
import messageQueue from "src/utils/messageQueue.ts";

export const distanceMetricOptions = [
  {
    value: "Cosine",
    label: "Cosine",
  },
  {
    value: "Manhattan",
    label: "Manhattan",
    disabled: true,
  },
];

export const connectionsOptions = [
  {
    value: ConnectionType.MANUAL,
    label: "Manual",
  },
  {
    value: ConnectionType.CDF,
    label: "CDF",
  },
  {
    value: ConnectionType.API,
    label: "Custom API",
  },
];

export const advancedOptions = (
  updateMode: DataSourcesFormProps["updateMode"],
  initialValues: DataSourcesFormProps["initialValues"],
) => [
  {
    key: "1",
    label: "Advanced Options",
    children: (
      <>
        <Form.Item
          name="distanceMetric"
          label="Distance metric"
          initialValue="Cosine"
        >
          <Select options={distanceMetricOptions} disabled={updateMode} />
        </Form.Item>
        <Form.Item
          name="chunkOverlapPercent"
          label="Chunk overlap"
          initialValue={initialValues.chunkOverlapPercent}
          rules={[{ required: true }]}
        >
          <InputNumber<number>
            min={0}
            max={50}
            formatter={(value) => (value ? `${value.toString()}%` : "")}
            disabled={updateMode}
            parser={(value) => value?.replace("%", "") as unknown as number}
          />
        </Form.Item>
      </>
    ),
  },
];

export const dataSourceCreationInitialValues = {
  id: -1,
  name: "",
  chunkSize: 512,
  connectionType: ConnectionType.MANUAL,
  chunkOverlapPercent: 10,
  embeddingModel: "",
  summarizationModel: "",
  availableForDefaultProject: true,
};

export interface DataSourcesFormProps {
  form: FormInstance;
  updateMode: boolean;
  initialValues: DataSourceBaseType;
}

const layout = {
  labelCol: { span: 8 },
  wrapperCol: { span: 16 },
};

const DataSourcesForm = ({
  form,
  updateMode,
  initialValues = dataSourceCreationInitialValues,
}: DataSourcesFormProps) => {
  const embeddingsModels = useGetEmbeddingModels();
  const llmModels = useGetLlmModels();
  const navigate = useNavigate();
  const embeddingModelOptions = useTransformModelOptions(embeddingsModels.data);
  const llmModelOptions = useTransformModelOptions(llmModels.data);

  useEffect(() => {
    if (initialValues.embeddingModel) {
      return;
    }
    form.setFieldsValue({
      embeddingModel: embeddingsModels.data?.[0]?.model_id,
    });
  }, [embeddingsModels.data, initialValues.embeddingModel]);

  return (
    <Form
      id="create-new-dataset"
      form={form}
      style={{ width: "100%" }}
      {...layout}
    >
      {embeddingsModels.isSuccess && embeddingsModels.data.length === 0 ? (
        <Alert
          type="warning"
          showIcon={true}
          message={
            "One embedding model must be available to create a knowledge base"
          }
          style={{ marginBottom: 16 }}
          action={
            <Button
              onClick={() => {
                navigate({
                  to: "/settings",
                  hash: "modelConfiguration",
                }).catch(() => {
                  messageQueue.error("Failed to navigate to models page");
                });
              }}
            >
              Model Config
            </Button>
          }
        />
      ) : null}
      <Form.Item
        name="name"
        label="Name"
        initialValue={initialValues.name}
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="chunkSize"
        label="Chunk size (tokens)"
        initialValue={initialValues.chunkSize}
        rules={[{ required: true }]}
      >
        <Select
          options={[
            { value: 8, label: "8" },
            { value: 16, label: "16" },
            { value: 32, label: "32" },
            { value: 64, label: "64" },
            { value: 128, label: "128" },
            { value: 256, label: "256" },
            { value: 512, label: "512" },
            { value: 1024, label: "1024" },
            { value: 2048, label: "2048" },
            { value: 4096, label: "4096" },
          ]}
          disabled={updateMode}
        />
      </Form.Item>
      <Form.Item
        name="embeddingModel"
        label="Embedding model"
        rules={[{ required: true }]}
        initialValue={initialValues.embeddingModel}
      >
        <Select
          options={embeddingModelOptions}
          disabled={updateMode}
          loading={embeddingsModels.isLoading}
        />
      </Form.Item>
      <Form.Item
        name="connectionType"
        label="Connection"
        initialValue={initialValues.connectionType}
        hidden={!updateMode}
      >
        <Select options={connectionsOptions} />
      </Form.Item>
      <Form.Item
        name="summarizationModel"
        tooltip="Summarization relies on an response synthesizer model to generate summaries.  Leaving this field blank will disable summarization."
        label={<Typography>Summarization model</Typography>}
        initialValue={initialValues.summarizationModel}
      >
        <Select
          options={llmModelOptions}
          allowClear
          loading={llmModels.isLoading}
        />
      </Form.Item>
      <Divider />
      <Form.Item
        name="availableForDefaultProject"
        label="Available without project"
        initialValue={initialValues.availableForDefaultProject}
        valuePropName="checked"
        tooltip="Allow this knowledge base to be used outside of the context of a project."
        hidden={!updateMode}
      >
        <Switch style={{ marginLeft: 4 }} />
      </Form.Item>
      <Collapse items={advancedOptions(updateMode, initialValues)} />
    </Form>
  );
};

export default DataSourcesForm;
