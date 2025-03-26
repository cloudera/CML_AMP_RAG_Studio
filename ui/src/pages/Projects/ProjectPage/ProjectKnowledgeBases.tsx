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
import { PlusCircleOutlined } from "@ant-design/icons";

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
      <FormItem name="dataSourceId">
        <Select
          disabled={allAreLoading || allDataSources?.length === 0}
          style={{ width: 300 }}
          options={unusedDataSources?.map((value) => {
            return formatDataSource(value);
          })}
        />
      </FormItem>
      <Button
        type="primary"
        style={{ marginTop: 8 }}
        disabled={unusedDataSources?.length === 0}
        onClick={handleAddDataSource}
      >
        Add
      </Button>
    </Form>
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
        <Flex>
          {dataSources?.map((dataSource) => (
            <Card
              title={dataSource.name}
              style={{ margin: 4 }}
              key={dataSource.id}
              styles={{
                body: {
                  padding: 12,
                },
                header: {
                  minHeight: 40,
                  paddingTop: 0,
                  paddingBottom: 0,
                  paddingLeft: 12,
                  paddingRight: 12,
                },
              }}
            >
              <Flex gap={8} align="baseline">
                <Typography.Text
                  type="secondary"
                  style={{ fontSize: "smaller" }}
                >
                  Documents:
                </Typography.Text>
                <Typography.Text style={{ fontSize: "small" }}>
                  {dataSource.documentCount}
                </Typography.Text>
              </Flex>
              <Flex gap={8} align="baseline">
                <Typography.Text
                  type="secondary"
                  style={{ fontSize: "smaller" }}
                >
                  Total doc size:
                </Typography.Text>
                <Typography.Text style={{ fontSize: "small" }}>
                  {dataSource.totalDocSize ?? "N/A"}
                </Typography.Text>
              </Flex>
            </Card>
          ))}
        </Flex>
      )}
    </Card>
  );
};
