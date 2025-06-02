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

import { useContext, useEffect, useState } from "react";
import {
  getVisualizeDataSource,
  Point2d,
  useVisualizeDataSourceWithUserQuery,
} from "src/api/dataSourceApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { Flex, Input, Tooltip, Typography } from "antd";
import VectorGraph from "pages/DataSources/VisualizationTab/VectorGraph.tsx";
import { QuestionCircleOutlined } from "@ant-design/icons";
import { DataSourceContext } from "pages/DataSources/Layout.tsx";

const DataSourceVisualization = () => {
  const { dataSourceId } = useContext(DataSourceContext);
  const [userInput, setUserInput] = useState("");
  const [vectorData, setVectorData] = useState<Point2d[]>([]);

  const { data, isLoading: isGetVisualizationIsLoading } =
    getVisualizeDataSource(dataSourceId);

  useEffect(() => {
    if (data) {
      setVectorData(data);
    }
  }, [data]);

  const questionMutation = useVisualizeDataSourceWithUserQuery({
    onSuccess: (result) => {
      setVectorData(result);
    },
    onError: (res: Error) => {
      messageQueue.error(res.toString());
    },
  });

  const handleQuestion = (question: string) => {
    questionMutation.mutate({
      userQuery: question,
      dataSourceId: dataSourceId.toString(),
    });
  };

  const loading = isGetVisualizationIsLoading || questionMutation.isPending;

  return (
    <Flex vertical align="center" justify="center" gap={20}>
      <Flex align="start" style={{ marginTop: 10 }}>
        <Typography.Title level={4} style={{ marginTop: 0, marginBottom: 0 }}>
          2d Chunk Vector Projection
        </Typography.Title>
        <Tooltip
          styles={{ body: { width: 500 } }}
          title={
            "This graph shows a 2d projection of the chunks of data. Each dot represents a chunk of data from a document, and they are organized in a way such that every document has a consistent color."
          }
        >
          <QuestionCircleOutlined
            style={{ width: 14, paddingLeft: 2, marginTop: 0 }}
          />
        </Tooltip>
      </Flex>
      <Flex align="center" justify="center" style={{ width: "100%" }}>
        {!isGetVisualizationIsLoading && vectorData.length === 0 ? (
          <Typography.Text type="secondary" style={{ height: 400 }}>
            No visualization available
          </Typography.Text>
        ) : (
          <VectorGraph
            rawData={vectorData}
            userInput={userInput}
            loading={loading}
          />
        )}
      </Flex>
      <Input
        disabled={loading || vectorData.length === 0}
        style={{ width: 700, margin: 20 }}
        placeholder={"Ask a question to place it on the graph"}
        value={userInput}
        onChange={(e) => {
          setUserInput(e.target.value);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            handleQuestion(userInput);
          }
        }}
      />
    </Flex>
  );
};

export default DataSourceVisualization;
