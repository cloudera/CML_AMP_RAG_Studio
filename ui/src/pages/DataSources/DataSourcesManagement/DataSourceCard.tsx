import { DataSourceType } from "src/api/dataSourceApi.ts";
import { UseQueryResult } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Card, Flex, Spin, Typography } from "antd";
import messageQueue from "src/utils/messageQueue.ts";
import { format } from "date-fns";
import { bytesConversion } from "src/utils/bytesConversion.ts";

export const DataSourceCard = ({
  dataSource,
  dataSourcesSummaries,
}: {
  dataSource: DataSourceType;
  dataSourcesSummaries: UseQueryResult<Record<string, string>>;
}) => {
  const navigate = useNavigate();
  return (
    <Card
      title={
        <Flex
          vertical
          style={{ marginBottom: 8, marginTop: 14, cursor: "pointer" }}
          onClick={() => {
            navigate({
              to: "/data/$dataSourceId",
              params: { dataSourceId: dataSource.id.toString() },
            }).catch(() => {
              messageQueue.error("Failed to navigate to data source.");
            });
          }}
        >
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
        <Flex vertical align="end">
          <Flex gap={4} align="baseline">
            <Typography.Text style={{ fontSize: 12 }} type="secondary">
              Number of documents:
            </Typography.Text>
            <Typography>{dataSource.documentCount}</Typography>
          </Flex>
          <Flex gap={4} align="baseline">
            <Typography.Text style={{ fontSize: 12 }} type="secondary">
              Total document size:
            </Typography.Text>
            <Typography>
              {dataSource.totalDocSize
                ? bytesConversion(dataSource.totalDocSize.toString())
                : "N/A"}
            </Typography>
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
