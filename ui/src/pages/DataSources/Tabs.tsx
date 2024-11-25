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

import { Flex, Tabs, TabsProps } from "antd";
import FileManagement from "pages/DataSources/ManageTab/FileManagement.tsx";
import IndexSettings from "pages/DataSources/IndexSettingsTab/IndexSettings.tsx";
import DataSourceConnections from "pages/DataSources/DataSourceConnectionsTab/DataSourceConnections.tsx";
import { useQuery } from "@tanstack/react-query";
import { getVisualizeDataSource, Point2d } from "src/api/dataSourceApi.ts";
import { useParams } from "@tanstack/react-router";
import { Scatter } from "react-chartjs-2";
import "chart.js/auto";
import { hash } from "crypto";

// Chart.register(ChartDataLabels);

const DataSourceVisualization = () => {
  const dataSourceId = useParams({
    from: "/_layout/data/_layout-datasources/$dataSourceId",
  }).dataSourceId;
  const { data, isPending } = useQuery(getVisualizeDataSource(dataSourceId));
  if (isPending) {
    return <div>Loading...</div>;
  }

  const points: Record<string, [{ x: number; y: number }]> = {};

  data?.forEach((d: Point2d) => {
    if (d[1] in points) {
      points[d[1]].push({ x: d[0][0], y: d[0][1] });
    } else {
      points[d[1]] = [{ x: d[0][0], y: d[0][1] }];
    }
  });

  const colors = [
    "rgba(255, 99, 132)",
    "rgba(54, 162, 235)",
    "rgba(255, 206, 86)",
    "rgba(75, 192, 192)",
    "rgba(153, 102, 255)",
    "rgba(255, 159, 64)",
    "rgba(199, 199, 199)",
    "rgba(83, 102, 255)",
    "rgba(255, 99, 255)",
    "rgba(99, 255, 132)",
  ];

  const hashStringToIndex = (str: string): number => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = (hash << 5) - hash + str.charCodeAt(i);
      hash |= 0; // Convert to 32bit integer
    }
    return Math.abs(hash % 10);
  };

  const datasets = Object.entries(points).map(([label, points]) => {
    return {
      label: label,
      data: points,
      backgroundColor: colors[hashStringToIndex(label)],
      borderColor: colors[hashStringToIndex(label)],
      borderWidth: 1,
    };
  });

  return (
    <div>
      <Scatter
        data={{
          datasets: datasets,
        }}
        options={{
          plugins: {
            legend: {
              display: false,
            },
            tooltip: {
              callbacks: {
                title: function (context: any) {
                  console.log(context);
                  return context[0].dataset.label;
                },
                label: function () {
                  return "";
                },
              },
            },
          },
          interaction: { mode: "dataset" },
        }}
      />
    </div>
  );
};

export const tabItems: TabsProps["items"] = [
  {
    key: "1",
    label: "Manage",
    children: <FileManagement />,
  },
  {
    key: "2",
    label: "Index Settings",
    children: <IndexSettings />,
  },
  {
    key: "3",
    label: "Connections",
    children: <DataSourceConnections />,
  },
  {
    key: "4",
    label: "Visualize",
    children: <DataSourceVisualization />,
  },
];

const DataSourcesTabs = () => {
  return (
    <Flex vertical style={{ width: "80%", maxWidth: 1000 }} gap={20}>
      <Tabs defaultActiveKey="1" items={tabItems} centered />
    </Flex>
  );
};

export default DataSourcesTabs;
