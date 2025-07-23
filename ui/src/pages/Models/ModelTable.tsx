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
import { Button, Flex, TableProps, Tooltip, Typography } from "antd";
import {
  Model,
  useGetCAIIModelStatus,
  useGetModelSource,
} from "src/api/modelsApi.ts";
import { CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";
import { cdlGreen600, cdlRed600 } from "src/cuix/variables.ts";

export const TestCell = ({
  onClick,
  model,
  loading,
  error,
  testResult,
}: {
  onClick: () => void;
  model: Model;
  loading: boolean;
  error: Error | null;
  testResult: string | undefined;
}) => {
  if (!model.name) {
    return null;
  }

  if (testResult === "ok") {
    return <CheckCircleOutlined style={{ color: cdlGreen600 }} />;
  }

  return (
    <Flex gap={8}>
      <Button
        onClick={onClick}
        disabled={model.available != undefined && !model.available}
        loading={loading}
      >
        Test
      </Button>
      {error || (testResult && testResult !== "ok") ? (
        <Tooltip title={error?.message ?? "an error occurred"}>
          <CloseCircleOutlined style={{ color: cdlRed600 }} />
        </Tooltip>
      ) : null}
    </Flex>
  );
};

export const modelColumns: TableProps<Model>["columns"] = [
  {
    title: "Model ID",
    dataIndex: "model_id",
    key: "model_id",
    width: 350,
  },
  {
    title: "Name",
    dataIndex: "name",
    key: "name",
    width: 350,
    render: (name?: string) =>
      name ?? <Typography.Text type="warning">No model found</Typography.Text>,
  },
  {
    title: "Status",
    dataIndex: "available",
    width: 150,
    key: "available",
    render: (_, model) => {
      const { data: modelSource } = useGetModelSource();
      const { data: modelStatus } = useGetCAIIModelStatus(
        model.name,
        modelSource,
      );

      const updatedModel = modelStatus ?? model;

      if (!updatedModel.name) {
        return null;
      }
      if (updatedModel.available === null) {
        return "Unknown";
      }
      return updatedModel.available ? "Available" : "Not Ready";
    },
  },
];
