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
import Metrics from "pages/Analytics/Metrics.tsx";
import {
  Collapse,
  Divider,
  Flex,
  Form,
  FormInstance,
  Select,
  Typography,
} from "antd";
import { transformModelOptions } from "src/utils/modelUtils.ts";
import { useGetLlmModels, useGetRerankingModels } from "src/api/modelsApi.ts";
import { MetricFilter } from "src/api/metricsApi.ts";
import MetadataMetrics from "pages/Analytics/AppMetrics.tsx";
import { Project, useGetProjects } from "src/api/projectsApi.ts";

const BooleanFilterOption = ({
  name,
  label,
}: {
  name: string;
  label: string;
}) => {
  return (
    <Form.Item name={name} label={label} style={{ marginTop: 8 }}>
      <Select
        options={[
          { value: true, label: "True" },
          { value: false, label: "False" },
        ]}
        style={{ width: 100 }}
        allowClear
      />
    </Form.Item>
  );
};

const SelectFilterOption = ({
  name,
  label,
  options,
}: {
  name: string;
  label: string;
  options: { value: string; label: string | undefined }[];
}) => {
  return (
    <Form.Item name={name} label={label} style={{ marginTop: 8 }}>
      <Select options={options} allowClear style={{ width: 250 }} />
    </Form.Item>
  );
};

const transformProjectOptions = (projects?: Project[]) => {
  if (!projects) {
    return [];
  }
  return projects.map((project) => ({
    value: project.id.toString(),
    label: project.name,
  }));
};

const MetricFilterOptions = ({
  metricFilterForm,
}: {
  metricFilterForm: FormInstance<MetricFilter>;
}) => {
  const { data: llmModels } = useGetLlmModels();
  const { data: rerankingModels } = useGetRerankingModels();
  const { data: projects } = useGetProjects();

  return (
    <Form
      autoCorrect="off"
      form={metricFilterForm}
      clearOnDestroy={true}
      layout="inline"
    >
      <SelectFilterOption
        name="inference_model"
        label="Response synthesizer model"
        options={transformModelOptions(llmModels)}
      />
      <SelectFilterOption
        name="rerank_model"
        label="Reranking model"
        options={[
          ...transformModelOptions(rerankingModels),
          { value: "none", label: "None" },
        ]}
      />
      <BooleanFilterOption
        name="use_summary_filter"
        label="Summary filter used"
      />
      <BooleanFilterOption name="use_hyde" label="HyDE expansion enabled" />
      <BooleanFilterOption
        name="exclude_knowledge_base"
        label="Knowledge base not used"
      />
      <SelectFilterOption
        name="project_id"
        label="Project"
        options={transformProjectOptions(projects)}
      />
    </Form>
  );
};

const AnalyticsPage = () => {
  const [form] = Form.useForm<MetricFilter>();
  Form.useWatch((values) => {
    return values;
  }, form);

  function transFormValues() {
    const values = form.getFieldsValue();
    if (values.rerank_model === "none") {
      values.has_rerank_model = false;
      values.rerank_model = undefined;
    }
    return values;
  }

  return (
    <Flex vertical align="center">
      <Flex vertical style={{ width: "80%", maxWidth: 1000 }} gap={20}>
        <Typography.Title level={3}>App Metrics</Typography.Title>
        <MetadataMetrics />
        <Divider style={{ margin: 0 }} />
        <Typography.Title level={3} style={{ marginTop: 12 }}>
          Session Metrics
        </Typography.Title>
        <Collapse
          items={[
            {
              key: "form",
              label: "Filter",
              children: <MetricFilterOptions metricFilterForm={form} />,
            },
          ]}
        />
        <Metrics metricFilter={transFormValues()} />;
      </Flex>
    </Flex>
  );
};

export default AnalyticsPage;
