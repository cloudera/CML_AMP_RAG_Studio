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

import { Card, Flex, Spin, TableProps, Tooltip, Typography } from "antd";
import { Link, useNavigate } from "@tanstack/react-router";
import { ConnectionType, DataSourceType } from "src/api/dataSourceApi.ts";
import ProductDataFlowLg from "src/cuix/icons/ProductDataFlowLgIcon";
import { format } from "date-fns";
import { useGetDataSourcesSummaries } from "src/api/summaryApi.ts";
import { UseQueryResult } from "@tanstack/react-query";
import messageQueue from "src/utils/messageQueue.ts";

const columns: TableProps<DataSourceType>["columns"] = [
  {
    title: "ID",
    dataIndex: "id",
    key: "id",
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
    title: "Created By",
    dataIndex: "createdById",
    key: "createdById",
  },
  {
    title: "Date Created",
    dataIndex: "timeCreated",
    key: "timeCreated",
    render: (_, { timeCreated }) => {
      return format(timeCreated * 1000, "MMM dd yyyy, pp");
    },
  },
  {
    title: "Documents",
    dataIndex: "documentCount",
    key: "documentCount",
  },
  {
    title: "Connection",
    dataIndex: "connectionType",
    key: "connectionType",
    render: (connectionType) => {
      return connectionType === ConnectionType[ConnectionType.CDF] ? (
        <Flex style={{ height: "100%" }}>
          <Tooltip title="Cloudera DataFlow">
            <ProductDataFlowLg fontSize={25} />
          </Tooltip>
        </Flex>
      ) : null;
    },
  },
];

const DataSourceCard = ({
  dataSource,
  dataSourcesSummaries,
}: {
  dataSource: DataSourceType;
  dataSourcesSummaries: UseQueryResult<Record<string, string>>;
}) => {
  const navigate = useNavigate();
  return (
    <Card
      hoverable={true}
      onClick={() => {
        navigate({
          to: "/data/$dataSourceId",
          params: { dataSourceId: dataSource.id.toString() },
        }).catch(() => {
          messageQueue.error("Failed to navigate to data source.");
        });
      }}
      title={
        <Flex vertical style={{ marginBottom: 8, marginTop: 14 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>
            {dataSource.name}
          </Typography.Title>
          <Flex gap={4} align="baseline">
            <Typography.Text style={{ fontSize: 12 }} type="secondary">
              ID:
            </Typography.Text>
            <Typography>{dataSource.id}</Typography>
          </Flex>
        </Flex>
      }
      extra={
        <Flex vertical>
          <Flex gap={4} align="baseline">
            <Typography.Text style={{ fontSize: 12 }} type="secondary">
              Documents:
            </Typography.Text>
            <Typography>{dataSource.documentCount}</Typography>
          </Flex>
          <Flex gap={4} align="baseline">
            <Typography.Text style={{ fontSize: 12 }} type="secondary">
              Connection:
            </Typography.Text>
            <Typography>{dataSource.connectionType}</Typography>
          </Flex>
        </Flex>
      }
    >
      <Flex vertical>
        <Flex
          style={{
            width: "100%",
            height: "100%",
          }}
          justify={"center"}
        >
          {dataSourcesSummaries.isLoading && <Spin />}
          {dataSourcesSummaries.isError && (
            <Typography.Text type="danger">
              Error loading summary.
            </Typography.Text>
          )}
          {dataSourcesSummaries.data?.[dataSource.id] ? (
            <Typography.Paragraph ellipsis={{ rows: 2, expandable: true }}>
              {dataSourcesSummaries.data[dataSource.id]}
            </Typography.Paragraph>
          ) : (
            <Typography.Text type="secondary">
              No summary available.
            </Typography.Text>
          )}
        </Flex>
        <Flex justify="space-between">
          <Flex gap={4} align="baseline">
            <Typography.Text style={{ fontSize: 12 }} type="secondary">
              Created by:
            </Typography.Text>
            <Typography>{dataSource.createdById}</Typography>
          </Flex>
          <Flex gap={4} align="baseline">
            <Typography.Text style={{ fontSize: 12 }} type="secondary">
              Date created:
            </Typography.Text>
            <Typography>
              {format(dataSource.timeCreated * 1000, "MMM dd yyyy, pp")}
            </Typography>
          </Flex>
        </Flex>
      </Flex>
    </Card>
  );
};

const DataSourcesTable = ({
  dataSources,
  dataSourcesLoading,
}: {
  dataSources?: DataSourceType[];
  dataSourcesLoading: boolean;
}) => {
  const dataSourcesSummaries = useGetDataSourcesSummaries();

  return (
    <Flex vertical style={{ width: "100%", paddingBottom: 40 }} gap={16}>
      {dataSourcesLoading && <Spin />}
      {dataSources?.map((dataSource) => (
        <DataSourceCard
          dataSource={dataSource}
          dataSourcesSummaries={dataSourcesSummaries}
          key={dataSource.id}
        />
      ))}
    </Flex>
  );

  // return (
  //   <Table
  //     dataSource={dataSourcesWithKey}
  //     columns={columns}
  //     style={{ width: "100%" }}
  //     loading={dataSourcesLoading}
  //   />
  // );
};

export default DataSourcesTable;
