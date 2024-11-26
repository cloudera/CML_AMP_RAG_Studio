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
import "chart.js/auto";
import DataSourceVisualization from "pages/DataSources/VisualizationTab/DataSourceVisualization.tsx";

export const tabItems: TabsProps["items"] = [
  {
    key: "manage",
    label: "Manage",
    children: <FileManagement />,
  },
  {
    key: "settings",
    label: "Index Settings",
    children: <IndexSettings />,
  },
  {
    key: "connections",
    label: "Connections",
    children: <DataSourceConnections />,
  },
  {
    key: "viz",
    label: "Visualize",
    children: <DataSourceVisualization />,
  },
];

const DataSourcesTabs = () => {
  return (
    <Flex vertical style={{ width: "80%", maxWidth: 1000 }} gap={20}>
      <Tabs defaultActiveKey="manage" items={tabItems} centered />
    </Flex>
  );
};

export default DataSourcesTabs;
