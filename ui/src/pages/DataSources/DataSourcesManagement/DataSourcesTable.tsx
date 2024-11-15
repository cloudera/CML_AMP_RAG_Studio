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

import { Link } from "@tanstack/react-router";
import { Flex, Table, TableProps, Tooltip } from "antd";
import ProductDataFlowLg from "src/cuix/icons/ProductDataFlowLgIcon";
import { DataSource, DataSourceConnectionType } from "src/services/api/api";

const columns: TableProps<DataSource>["columns"] = [
  {
    title: "ID",
    dataIndex: "id",
    key: "id",
    width: 180,
  },
  {
    title: "Name",
    dataIndex: "name",
    key: "name",
    render: (_, { id, name }) => {
      return (
        <Link
          to={"/data/$dataSourceId"}
          params={{ dataSourceId: id.toString() }}
        >
          {name}
        </Link>
      );
    },
  },
  {
    title: "Connection",
    dataIndex: "connection_type",
    key: "connection_type",
    render: (connectionType) => {
      return connectionType === DataSourceConnectionType.Cdf ? (
        <Flex style={{ height: "100%" }}>
          <Tooltip title="Cloudera DataFlow">
            <ProductDataFlowLg fontSize={25} />
          </Tooltip>
        </Flex>
      ) : null;
    },
    width: 180,
  },
];

const DataSourcesTable = ({
  dataSources,
  dataSourcesLoading,
}: {
  dataSources?: DataSource[];
  dataSourcesLoading: boolean;
}) => {
  return (
    <Table
      dataSource={dataSources}
      columns={columns}
      style={{ width: "100%" }}
      loading={dataSourcesLoading}
    />
  );
};

export default DataSourcesTable;
