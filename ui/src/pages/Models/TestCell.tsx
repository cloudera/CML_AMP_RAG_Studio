/*
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2025
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
 */

import {
  Model,
  useGetCAIIModelStatus,
  useGetModelSource,
} from "src/api/modelsApi.ts";
import { CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";
import { cdlGreen600, cdlRed600 } from "src/cuix/variables.ts";
import { Button, Flex, Tooltip } from "antd";

const StatusCellButton = ({
  onClick,
  model,
  loading,
  error,
  testResult,
  testingDisabled,
}: {
  onClick: () => void;
  model: Model;
  loading: boolean;
  error: Error | null;
  testResult: string | undefined;
  testingDisabled?: boolean;
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
        disabled={testingDisabled}
        loading={loading}
        style={{ width: 80 }}
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
const CAIIModelStatusCell = ({
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
  const {
    data: modelStatus,
    isLoading,
    error: caiiModelStatusError,
  } = useGetCAIIModelStatus(model.model_id, "CAII");

  return (
    <StatusCellButton
      onClick={onClick}
      model={model}
      loading={loading || isLoading}
      error={error ?? caiiModelStatusError}
      testResult={testResult}
      testingDisabled={
        model.available != undefined &&
        !model.available &&
        !modelStatus?.available
      }
    />
  );
};
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
  const { data: modelSource, error: modelSourceError } = useGetModelSource();

  if (modelSourceError) {
    return (
      <Tooltip title={modelSourceError.message}>
        <CloseCircleOutlined style={{ color: cdlRed600 }} />
      </Tooltip>
    );
  }

  if (modelSource === "CAII") {
    return (
      <CAIIModelStatusCell
        onClick={onClick}
        model={model}
        loading={loading}
        error={error}
        testResult={testResult}
      />
    );
  }

  return (
    <StatusCellButton
      onClick={onClick}
      model={model}
      loading={loading}
      error={error}
      testResult={testResult}
      testingDisabled={model.available != undefined && !model.available}
    />
  );
};
