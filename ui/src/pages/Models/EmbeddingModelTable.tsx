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

import { Table, TableProps } from "antd";
import { Model, useTestEmbeddingModel } from "src/api/modelsApi.ts";
import { useState } from "react";
import { modelColumns, TestCell } from "pages/Models/ModelTable.tsx";

const EmbeddingModelTestCell = ({ model }: { model: Model }) => {
  const [testModel, setTestModel] = useState("");
  const {
    data: testResult,
    isLoading,
    error,
  } = useTestEmbeddingModel(testModel);

  const handleTestModel = () => {
    setTestModel(model.model_id);
  };

  return (
    <TestCell
      onClick={handleTestModel}
      model={model}
      loading={isLoading}
      error={error}
      testResult={testResult}
    />
  );
};

const testCell: TableProps<Model>["columns"] = [
  {
    title: "Test",
    width: 140,
    render: (_, model) => {
      return <EmbeddingModelTestCell model={model} />;
    },
  },
];

const EmbeddingModelTable = ({
  embeddingModels,
  areEmbeddingModelsLoading,
}: {
  embeddingModels?: Model[];
  areEmbeddingModelsLoading: boolean;
}) => {
  return (
    <Table
      dataSource={embeddingModels}
      columns={modelColumns ? [...modelColumns, ...testCell] : testCell}
      style={{ width: "100%" }}
      loading={areEmbeddingModelsLoading}
      rowKey={(record) => record.model_id}
    />
  );
};

export default EmbeddingModelTable;
