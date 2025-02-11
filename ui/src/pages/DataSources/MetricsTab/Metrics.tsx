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
import { useContext } from "react";
import { DataSourceContext } from "pages/DataSources/Layout.tsx";
import { Col, Flex, Row, Statistic, Typography } from "antd";
import { DislikeOutlined, LikeOutlined } from "@ant-design/icons";
import { BarChart } from "@mui/x-charts/BarChart";
import { axisClasses } from "@mui/x-charts";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { useGetMetricsByDataSource } from "src/api/metricsApi.ts";

const labels = [
  "Inaccurate",
  "Not Helpful",
  "Out of date",
  "Too short",
  "Too long",
  "Other",
];

const Metrics = () => {
  const { dataSourceId } = useContext(DataSourceContext);
  const { data, isLoading } = useGetMetricsByDataSource({
    data_source_id: Number(dataSourceId),
  });

  const maxScoreData =
    data?.max_score_over_time
      .map((entry) => {
        return {
          x: entry[0],
          y: entry[1],
        };
      })
      .reverse() ?? [];

  const barchartData = [
    {
      data: labels.map((label) => {
        return data?.aggregated_feedback[label] ?? 0;
      }),
    },
  ];
  return (
    <Flex vertical gap={24}>
      <Typography.Title level={4}>Knowledge base metrics</Typography.Title>
      <Row gutter={16}>
        <Col span={8} style={{ textAlign: "center" }}>
          <Statistic
            title="Rag Inference Count"
            loading={isLoading}
            value={data?.count_of_interactions}
          />
        </Col>
        <Col span={8} style={{ textAlign: "center" }}>
          <Statistic
            title="Non-RAG Inference Count"
            loading={isLoading}
            value={data?.count_of_direct_interactions}
          />
        </Col>
        <Col span={8} style={{ textAlign: "center" }}>
          <Statistic
            title="Unique Users"
            loading={isLoading}
            value={data?.unique_users}
          />
        </Col>
      </Row>
      <Typography.Title level={4}>Feedback metrics</Typography.Title>
      <Row gutter={16}>
        <Col span={8} style={{ textAlign: "center" }}>
          <Statistic
            title="Positive Rating"
            loading={isLoading}
            value={data?.positive_ratings}
            prefix={<LikeOutlined />}
          />
        </Col>
        <Col span={8} style={{ textAlign: "center" }}>
          <Statistic
            title="Negative Rating"
            loading={isLoading}
            value={data?.negative_ratings}
            prefix={<DislikeOutlined />}
          />
        </Col>
        <Col span={8} style={{ textAlign: "center" }}>
          <Statistic
            title="No Rating"
            loading={isLoading}
            value={data?.no_ratings}
          />
        </Col>
      </Row>
      <Typography.Title level={4}>
        Aggregated feedback categories
      </Typography.Title>
      <Col span={16}>
        <Row>
          <BarChart
            margin={{ top: 0, bottom: 50, left: 50, right: 0 }}
            height={250}
            width={500}
            series={barchartData}
            bottomAxis={{
              label: "Feedback Category",
            }}
            yAxis={[
              {
                disableTicks: true,
                scaleType: "band",
                data: labels,
              },
            ]}
            layout={"horizontal"}
          />
        </Row>
      </Col>
      <Typography.Title level={4}>
        Max score of chunk over time
      </Typography.Title>
      <Col span={16}>
        <Row>
          <ScatterChart
            margin={{ top: 10, bottom: 100, left: 95 }}
            xAxis={[
              {
                label: "Time of interaction",
                id: "time",
                dataKey: "x",
                scaleType: "time",
                tickLabelStyle: {
                  angle: 45,
                  textAnchor: "start",
                },
                labelStyle: {
                  transform: "translateY(30px)",
                },
              },
            ]}
            yAxis={[
              {
                min: 0,
                max: 1,
                tickInterval: [0, 0.2, 0.4, 0.6, 0.8, 1.0],
                label: "Max Score",
              },
            ]}
            sx={{
              [`.${axisClasses.left} .${axisClasses.label}`]: {
                transform: "translate(-20px, 0)",
              },
            }}
            series={[
              {
                datasetKeys: {
                  id: "y",
                  x: "x",
                  y: "y",
                },
                valueFormatter: (value) => value.y.toString(),
              },
            ]}
            disableVoronoi={true}
            dataset={maxScoreData}
            height={300}
          />
        </Row>
      </Col>
      {/*TODO: visualize max score, input count, and output counts over time?*/}
    </Flex>
  );
};

export default Metrics;
