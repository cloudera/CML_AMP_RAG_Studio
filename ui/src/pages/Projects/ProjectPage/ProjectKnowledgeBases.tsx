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

import { Dispatch, SetStateAction, useState } from "react";
import {
  useAddDataSourceToProject,
  useGetDataSourcesForProject,
  useRemoveDataSourceFromProject,
} from "src/api/projectsApi.ts";
import { useProjectContext } from "pages/Projects/ProjectContext.tsx";
import {
  DataSourceType,
  useGetDataSourcesQuery,
} from "src/api/dataSourceApi.ts";
import { useQueryClient } from "@tanstack/react-query";
import messageQueue from "src/utils/messageQueue.ts";
import { QueryKeys } from "src/api/utils.ts";
import {
  Button,
  Card,
  Flex,
  Form,
  Popover,
  Select,
  Spin,
  Typography,
} from "antd";
import FormItem from "antd/es/form/FormItem";
import { formatDataSource } from "pages/RagChatTab/SessionsSidebar/CreateSession/CreateSessionForm.tsx";
import { MinusCircleOutlined, PlusCircleOutlined } from "@ant-design/icons";
import { bytesConversion } from "src/utils/bytesConversion.ts";

const SelectKnowledgeBaseForm = ({
  setPopoverVisible,
  unusedDataSources,
}: {
  setPopoverVisible: Dispatch<SetStateAction<boolean>>;
  unusedDataSources?: DataSourceType[];
}) => {
  const { project } = useProjectContext();
  const [form] = Form.useForm<{ dataSourceId: number }>();
  const queryClient = useQueryClient();
  const { data: allDataSources, isLoading: allAreLoading } =
    useGetDataSourcesQuery();
  const { mutate: addDataSourceToProject } = useAddDataSourceToProject({
    onError: (res: Error) => {
      messageQueue.error(res.toString());
    },
    onSuccess: () => {
      messageQueue.success("Knowledge Base added to project");
      setPopoverVisible(false);
      queryClient
        .invalidateQueries({
          queryKey: [
            QueryKeys.getDataSourcesForProject,
            { projectId: project.id },
          ],
        })
        .catch(() => {
          messageQueue.error("Error re-fetching Knowledge Bases for project");
        });
    },
  });

  const handleAddDataSource = () => {
    form
      .validateFields()
      .catch(() => null)
      .then((values) => {
        if (values?.dataSourceId) {
          addDataSourceToProject({
            projectId: project.id,
            dataSourceId: values.dataSourceId,
          });
        }
      })
      .catch(() => null);
  };

  return (
    <Form autoCorrect="off" form={form} clearOnDestroy={true}>
      <FormItem
        name="dataSourceId"
        rules={[{ required: true, message: "Please select a Knowledge Base" }]}
      >
        <Select
          disabled={allAreLoading || allDataSources?.length === 0}
          style={{ width: 300 }}
          options={unusedDataSources?.map((value) => {
            return formatDataSource(value);
          })}
        />
      </FormItem>
      <Flex style={{ width: "100%" }} justify="end">
        <Button
          type="primary"
          style={{ marginTop: 8 }}
          disabled={unusedDataSources?.length === 0}
          onClick={handleAddDataSource}
        >
          Add
        </Button>
      </Flex>
    </Form>
  );
};

const RemoveKnowledgeBaseConfirmation = ({
  dataSource,
}: {
  dataSource: DataSourceType;
}) => {
  const { project } = useProjectContext();
  const queryClient = useQueryClient();
  const removeDataSourceFromProject = useRemoveDataSourceFromProject({
    onError: (res: Error) => {
      messageQueue.error(res.toString());
    },
    onSuccess: () => {
      queryClient
        .invalidateQueries({
          queryKey: [
            QueryKeys.getDataSourcesForProject,
            { projectId: project.id },
          ],
        })
        .catch(() => {
          messageQueue.error("Error re-fetching Knowledge Bases for project");
        });
      messageQueue.success("Knowledge Base removed from project");
    },
  });

  const handleRemoveKnowledgeBase = () => {
    removeDataSourceFromProject.mutate({
      projectId: project.id,
      dataSourceId: dataSource.id,
    });
  };

  return (
    <Flex style={{ width: 350, padding: 12 }} vertical gap={8}>
      <Typography>
        Removing Knowledge Base from the Project will remove it from associated
        Chats
      </Typography>
      <Flex justify="end">
        <Button
          style={{ width: 100 }}
          danger
          onClick={handleRemoveKnowledgeBase}
        >
          Remove
        </Button>
      </Flex>
    </Flex>
  );
};

const KnowledgeBaseCard = (props: { dataSource: DataSourceType }) => {
  const [popoverVisible, setPopoverVisible] = useState(false);
  return (
    <Card
      title={
        <Typography.Title level={5} style={{ margin: 0 }} ellipsis>
          {props.dataSource.name}
        </Typography.Title>
      }
      style={{ width: 225 }}
      extra={
        <Popover
          title={
            <Typography.Title level={5} style={{ margin: 12 }}>
              Remove from project
            </Typography.Title>
          }
          open={popoverVisible}
          destroyTooltipOnHide={true}
          onOpenChange={setPopoverVisible}
          trigger="click"
          content={
            <RemoveKnowledgeBaseConfirmation dataSource={props.dataSource} />
          }
        >
          <Button type="text" icon={<MinusCircleOutlined />} />
        </Popover>
      }
    >
      <Flex gap={8} align="baseline">
        <Typography.Text type="secondary" style={{ fontSize: "smaller" }}>
          Documents:
        </Typography.Text>
        <Typography.Text style={{ fontSize: "small" }}>
          {props.dataSource.documentCount}
        </Typography.Text>
      </Flex>
      <Flex gap={8} align="baseline">
        <Typography.Text type="secondary" style={{ fontSize: "smaller" }}>
          Total doc size:
        </Typography.Text>
        <Typography.Text style={{ fontSize: "small" }}>
          {props.dataSource.totalDocSize
            ? bytesConversion(props.dataSource.totalDocSize.toString())
            : "N/A"}
        </Typography.Text>
      </Flex>
    </Card>
  );
};

export const ProjectKnowledgeBases = () => {
  const { project } = useProjectContext();
  const [popoverVisible, setPopoverVisible] = useState(false);
  const { data: dataSources, isLoading } = useGetDataSourcesForProject(
    project.id,
  );

  const { data: allDataSources } = useGetDataSourcesQuery();

  const allDataSourcesIds = dataSources?.map((dataSource) => dataSource.id);
  const unusedDataSources = allDataSources?.filter((dataSource) => {
    return !allDataSourcesIds?.includes(dataSource.id);
  });

  return (
    <Card
      title="Knowledge Bases"
      extra={
        <Popover
          title="Add Knowledge Base"
          open={popoverVisible && unusedDataSources?.length !== 0}
          onOpenChange={setPopoverVisible}
          trigger="click"
          placement="bottomRight"
          destroyTooltipOnHide={true}
          content={
            <SelectKnowledgeBaseForm
              unusedDataSources={unusedDataSources}
              setPopoverVisible={setPopoverVisible}
            />
          }
        >
          <Button
            type="text"
            disabled={unusedDataSources?.length === 0}
            icon={<PlusCircleOutlined />}
          />
        </Popover>
      }
    >
      {isLoading ? (
        <Spin />
      ) : (
        <Flex gap={12} wrap="wrap">
          {dataSources?.length === 0 && (
            <Typography.Text type="secondary">
              No Knowledge Bases in this Project. Click the{" "}
              <PlusCircleOutlined /> button to add one.
            </Typography.Text>
          )}
          {dataSources?.map((dataSource) => (
            <KnowledgeBaseCard key={dataSource.id} dataSource={dataSource} />
          ))}
        </Flex>
      )}
    </Card>
  );
};
