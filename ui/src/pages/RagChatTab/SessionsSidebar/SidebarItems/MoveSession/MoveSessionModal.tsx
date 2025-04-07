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

import { ModalHook } from "src/utils/useModal.ts";
import { Session } from "src/api/sessionApi.ts";
import { useGetDataSourcesQuery } from "src/api/dataSourceApi.ts";
import {
  useAddDataSourceToProject,
  useGetDataSourcesForProject,
  useGetProjects,
} from "src/api/projectsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { useEffect, useState } from "react";
import { Flex, Modal, Typography } from "antd";
import CurrentSession from "pages/RagChatTab/SessionsSidebar/SidebarItems/MoveSession/CurrentSession.tsx";
import TransferItems from "pages/RagChatTab/SessionsSidebar/SidebarItems/MoveSession/TransferItems.tsx";
import ProjectSelection from "pages/RagChatTab/SessionsSidebar/SidebarItems/MoveSession/ProjectSelection.tsx";
import { useMoveSession } from "./useMoveSession.ts";

const MoveSessionModal = ({
  moveModal,
  session,
}: {
  moveModal: ModalHook;
  session: Session;
}) => {
  const { data: dataSources, isLoading: isDataSourcesLoading } =
    useGetDataSourcesQuery();
  const { data: projects, isLoading: isProjectsLoading } = useGetProjects();
  const addDataSourceToProject = useAddDataSourceToProject({
    onError: () => {
      messageQueue.error("Failed to add data source to project");
    },
  });
  const [selectedProject, setSelectedProject] = useState<number>();
  const updateSession = useMoveSession({
    session,
    selectedProject,
    projects,
    moveModal,
  });
  const {
    data: dataSourcesForProject,
    isLoading: dataSourcesForProjectIsLoading,
  } = useGetDataSourcesForProject(selectedProject);
  const [dataSourcesToTransfer, setDataSourcesToTransfer] = useState<number[]>(
    [],
  );

  useEffect(() => {
    setDataSourcesToTransfer(
      session.dataSourceIds.filter(
        (dataSourceId) =>
          !dataSourcesForProject?.some(
            (projectDs) => projectDs.id === dataSourceId,
          ),
      ),
    );
  }, [selectedProject, session.dataSourceIds, dataSourcesForProject]);

  const handleMoveSession = () => {
    if (!selectedProject) {
      messageQueue.error("Please select a project");
      return;
    }
    Promise.all(
      dataSourcesToTransfer.map((dataSourceId) => {
        return addDataSourceToProject.mutateAsync({
          projectId: selectedProject,
          dataSourceId: dataSourceId,
        });
      }),
    )
      .then(() => {
        updateSession.mutate({
          ...session,
          dataSourceIds: dataSourcesToTransfer,
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
      loading={isDataSourcesLoading || isProjectsLoading}
      open={moveModal.isModalOpen}
      onOk={(e) => {
        e.stopPropagation();
        handleMoveSession();
      }}
      confirmLoading={
        addDataSourceToProject.isPending || updateSession.isPending
      }
      onCancel={(e) => {
        e.stopPropagation();
        setSelectedProject(undefined);
        setDataSourcesToTransfer([]);
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
            dataSourcesToTransfer={dataSourcesToTransfer}
            dataSources={dataSources}
            setDataSourcesToTransfer={setDataSourcesToTransfer}
            session={session}
            selectedProject={selectedProject}
            dataSourcesForProject={dataSourcesForProject}
            dataSourcesForProjectIsLoading={dataSourcesForProjectIsLoading}
          />
          <ProjectSelection
            session={session}
            projects={projects}
            dataSourcesForProject={dataSourcesForProject}
            setSelectedProject={setSelectedProject}
            dataSourcesToTransfer={dataSourcesToTransfer}
            dataSources={dataSources}
            selectedProject={selectedProject}
            dataSourcesForProjectIsLoading={dataSourcesForProjectIsLoading}
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
