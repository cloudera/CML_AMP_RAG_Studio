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
import { Session, useUpdateSessionMutation } from "src/api/sessionApi.ts";
import { ModalHook } from "src/utils/useModal.ts";
import {
  DataSourceType,
  useGetDataSourcesQuery,
} from "src/api/dataSourceApi.ts";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import {
  Project,
  useAddDataSourceToProject,
  useGetDataSourcesForProject,
  useGetProjects,
} from "src/api/projectsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "src/api/utils.ts";
import { useNavigate } from "@tanstack/react-router";

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
  dataSourcesNotInProject,
  setDataSourcesNotInProject,
}: {
  dataSources?: DataSourceType[];
  dataSourcesNotInProject: number[];
  setDataSourcesNotInProject: Dispatch<SetStateAction<number[]>>;
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
      {dataSourcesNotInProject.length > 0 && (
        <Card title={<Typography>New knowledge base</Typography>}>
          {dataSourcesNotInProject.map((kb) => {
            const dataSource = dataSources?.find((ds) => ds.id === kb);

            const handleClose = () => {
              setDataSourcesNotInProject((prev) =>
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
  dataSourcesNotInProject,
  dataSources,
  selectedProject,
}: {
  session: Session;
  projects?: Project[];
  setSelectedProject: (projectId: number) => void;
  dataSourcesForProject?: DataSourceType[];
  dataSourcesNotInProject: number[];
  dataSources?: DataSourceType[];
  selectedProject?: number;
}) => {
  const projectOptions = projects
    ?.filter((project) => !project.defaultProject)
    .filter((project) => project.id !== session.projectId)
    .map((project) => ({
      label: project.name,
      value: project.id,
    }));

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
          {dataSourcesNotInProject.map((kb) => {
            const dataSource = dataSources?.find((ds) => ds.id === kb);
            return (
              <Tag key={kb} color={cdlGreen600}>
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
  const queryClient = useQueryClient();
  const { data: dataSources } = useGetDataSourcesQuery();
  const { data: projects } = useGetProjects();
  const navigate = useNavigate();
  const addDataSourceToProject = useAddDataSourceToProject({
    onError: () => {
      messageQueue.error("Failed to add data source to project");
    },
  });
  const updateSession = useUpdateSessionMutation({
    onSuccess: () => {
      const project = projects?.find((proj) => proj.id === selectedProject);
      if (!project) {
        messageQueue.error("Failed to find project");
        return;
      }
      messageQueue.success(
        `Session ${session.name} moved to project ${project.name}`,
      );
      queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getSessions] })
        .catch(() => {
          messageQueue.error("Failed to refetch session");
        });
      queryClient
        .invalidateQueries({
          queryKey: [
            QueryKeys.getDataSourcesForProject,
            { projectId: project.id },
          ],
        })
        .catch(() => {
          messageQueue.error("Failed to refetch project");
        });
      navigate({
        to: "/chats/projects/$projectId/sessions/$sessionId",
        params: {
          projectId: project.id.toString(),
          sessionId: session.id.toString(),
        },
      }).catch(() => {
        messageQueue.error("Failed to navigate to session");
      });
      moveModal.handleCancel();
    },
    onError: () => {
      messageQueue.error("Failed to update session");
    },
  });
  const [selectedProject, setSelectedProject] = useState<number>();
  const { data: dataSourcesForProject } =
    useGetDataSourcesForProject(selectedProject);
  const [dataSourcesNotInProject, setDataSourcesNotInProject] = useState<
    number[]
  >([]);

  useEffect(() => {
    setDataSourcesNotInProject(
      session.dataSourceIds.filter(
        (dataSourceId) =>
          !dataSourcesForProject?.some(
            (projectDs) => projectDs.id === dataSourceId,
          ),
      ),
    );
  }, [selectedProject, session.dataSourceIds, dataSourcesForProject]);

  const handleMoveit = () => {
    if (!selectedProject) {
      messageQueue.error("Please select a project");
      return;
    }
    Promise.all(
      dataSourcesNotInProject.map((dataSourceId) => {
        return addDataSourceToProject.mutateAsync({
          projectId: selectedProject,
          dataSourceId: dataSourceId,
        });
      }),
    )
      .then(() => {
        updateSession.mutate({
          ...session,
          dataSourceIds: dataSourcesNotInProject,
          projectId: selectedProject,
        });
      })
      .catch(() => {
        messageQueue.error("Failed to move session.");
      });
  };

  return (
    <Modal
      title="Move session?"
      open={moveModal.isModalOpen}
      onOk={(e) => {
        e.stopPropagation();
        handleMoveit();
      }}
      onCancel={(e) => {
        e.stopPropagation();
        setSelectedProject(undefined);
        setDataSourcesNotInProject([]);
        moveModal.handleCancel();
      }}
      okButtonProps={{
        disabled: !selectedProject,
      }}
      okText={"Move it"}
      destroyOnClose={true}
      width={1000}
    >
      <Flex
        vertical
        gap={8}
        align={"center"}
        justify={"center"}
        wrap={true}
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <Flex gap={8} wrap={true}>
          <CurrentSession session={session} dataSources={dataSources} />
          <TransferItems
            dataSourcesNotInProject={dataSourcesNotInProject}
            dataSources={dataSources}
            setDataSourcesNotInProject={setDataSourcesNotInProject}
          />
          <ProjectSelection
            session={session}
            projects={projects}
            dataSourcesForProject={dataSourcesForProject}
            setSelectedProject={setSelectedProject}
            dataSourcesNotInProject={dataSourcesNotInProject}
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
