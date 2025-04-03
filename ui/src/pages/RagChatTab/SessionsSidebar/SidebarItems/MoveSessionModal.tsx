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

import { Card, Flex, Modal, Select, Tag, Tooltip, Typography } from "antd";
import { CloseCircleFilled, RightCircleOutlined } from "@ant-design/icons";
import { cdlGreen600 } from "src/cuix/variables.ts";
import { Session } from "src/api/sessionApi.ts";
import { ModalHook } from "src/utils/useModal.ts";
import {
  DataSourceType,
  useGetDataSourcesQuery,
} from "src/api/dataSourceApi.ts";
import { Dispatch, SetStateAction, useState } from "react";
import {
  Project,
  useGetDataSourcesForProject,
  useGetProjects,
} from "src/api/projectsApi.ts";

const CurrentSession = ({
  session,
  dataSources,
}: {
  session: Session;
  dataSources?: DataSourceType[];
}) => {
  return (
    <Card title={`Selected session: ${session.name}`} style={{ width: 350 }}>
      <Typography style={{ marginBottom: 20 }}>
        Knowledge bases in session:
      </Typography>
      {session.dataSourceIds.map((dataSourceId) => {
        const dataSourceName = dataSources?.find(
          (ds) => ds.id === dataSourceId,
        );
        return (
          <Tag key={dataSourceId} color="blue">
            {dataSourceName?.name}
          </Tag>
        );
      })}
    </Card>
  );
};

const TransferItems = ({
  dataSources,
  knowledgeBaseNotInProject,
  setKnowledgeBaseNotInProject,
}: {
  dataSources?: DataSourceType[];
  knowledgeBaseNotInProject: number[];
  setKnowledgeBaseNotInProject: Dispatch<SetStateAction<number[]>>;
}) => {
  return (
    <Flex
      vertical
      align="center"
      justify="center"
      style={{ width: 200 }}
      gap={20}
    >
      <RightCircleOutlined style={{ fontSize: 20 }} />
      {knowledgeBaseNotInProject.length > 0 && (
        <Card title={<Typography>New knowledge base</Typography>}>
          {knowledgeBaseNotInProject.map((kb) => {
            const dataSource = dataSources?.find((ds) => ds.id === kb);

            const handleClose = () => {
              setKnowledgeBaseNotInProject((prev) =>
                prev.filter((id) => id !== kb),
              );
            };

            return (
              <Tag
                key={kb}
                color={cdlGreen600}
                onClose={handleClose}
                closeIcon={
                  <Tooltip title="Exclude from transfer">
                    <CloseCircleFilled style={{ marginLeft: 8 }} />
                  </Tooltip>
                }
              >
                {dataSource?.name}
              </Tag>
            );
          })}
        </Card>
      )}
    </Flex>
  );
};

const ProjectSelection = ({
  session,
  projects,
  setSelectedProject,
  dataSourcesForProject,
  knowledgeBasesNotInProject,
  dataSources,
  selectedProject,
}: {
  session: Session;
  projects?: Project[];
  setSelectedProject: (projectId: number) => void;
  dataSourcesForProject?: DataSourceType[];
  knowledgeBasesNotInProject: number[];
  dataSources?: DataSourceType[];
  selectedProject?: number;
}) => {
  const projectOptions = projects
    ?.map((project) => ({
      label: project.name,
      value: project.id,
    }))
    .filter((project) => project.value !== session.projectId);

  return (
    <Card
      title="Move to:"
      style={{ width: 350 }}
      extra={
        <>
          Project:{" "}
          <Select
            style={{ width: 150 }}
            options={projectOptions}
            onSelect={setSelectedProject}
          />
        </>
      }
    >
      <Typography style={{ marginBottom: 20 }}>
        Knowledge bases in project:
      </Typography>
      {selectedProject && (
        <Flex>
          {dataSourcesForProject?.map((ds) => {
            return (
              <Tag key={ds.id} color="blue">
                {ds.name}
              </Tag>
            );
          })}
          {knowledgeBasesNotInProject.map((kb) => {
            const dataSource = dataSources?.find((ds) => ds.id === kb);
            return (
              <Tag
                key={kb}
                color={cdlGreen600}
                // onClose={() => console.log("remove from call")}
                // closeIcon={<CloseCircleFilled />}
              >
                {dataSource?.name}
              </Tag>
            );
          })}
        </Flex>
      )}
    </Card>
  );
};

const MoveSessionModal = ({
  moveModal,
  session,
}: {
  moveModal: ModalHook;
  session: Session;
}) => {
  const { data: dataSources } = useGetDataSourcesQuery();
  const { data: projects } = useGetProjects();
  const [selectedProject, setSelectedProject] = useState<number>();
  const { data: dataSourcesForProject } =
    useGetDataSourcesForProject(selectedProject);
  const [knowledgeBasesNotInProject, setKnowledgeBasesNotInProject] = useState(
    () =>
      session.dataSourceIds.filter(
        (ds) =>
          !dataSourcesForProject?.some((projectDs) => projectDs.id === ds),
      ),
  );

  return (
    <Modal
      title="Move session?"
      open={moveModal.isModalOpen}
      // onOk={(event) => {
      //   handleDeleteSession(event);
      // }}
      onCancel={() => {
        setSelectedProject(undefined);
        setKnowledgeBasesNotInProject([]);
        moveModal.handleCancel();
      }}
      okText={"Yes, move it!"}
      destroyOnClose={true}
      width={1000}
    >
      <Flex vertical gap={8} align={"center"} justify={"center"} wrap={true}>
        <Flex gap={8} wrap={true}>
          <CurrentSession session={session} dataSources={dataSources} />
          <TransferItems
            knowledgeBaseNotInProject={knowledgeBasesNotInProject}
            dataSources={dataSources}
            setKnowledgeBaseNotInProject={setKnowledgeBasesNotInProject}
          />
          <ProjectSelection
            session={session}
            projects={projects}
            dataSourcesForProject={dataSourcesForProject}
            setSelectedProject={setSelectedProject}
            knowledgeBasesNotInProject={knowledgeBasesNotInProject}
            dataSources={dataSources}
            selectedProject={selectedProject}
          />
        </Flex>
        <Typography.Paragraph italic style={{ marginTop: 20 }}>
          Moving this session will add a new knowledge base to the project
          unless excluded.
        </Typography.Paragraph>
      </Flex>
    </Modal>
  );
};

export default MoveSessionModal;
