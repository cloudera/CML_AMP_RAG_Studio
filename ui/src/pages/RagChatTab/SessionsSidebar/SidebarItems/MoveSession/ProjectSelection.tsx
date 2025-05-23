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

import { Session } from "src/api/sessionApi.ts";
import { Project } from "src/api/projectsApi.ts";
import { Card, Flex, Select, Skeleton, Tag, Typography } from "antd";
import { cdlBlue600, cdlGreen600 } from "src/cuix/variables.ts";
import { useContext } from "react";

import { MoveSessionContext } from "pages/RagChatTab/SessionsSidebar/SidebarItems/MoveSession/MoveSessionContext.tsx";
import { DataSourceType } from "src/api/dataSourceApi.ts";

const getProjectOptions = (session: Session, projects?: Project[]) =>
  projects
    ?.filter((project) => !project.defaultProject)
    .filter((project) => project.id !== session.projectId)
    .map((project) => ({
      label: project.name,
      value: project.id,
    }));

const ProjectKnowledgeBases = ({
  dataSourcesForProjectIsLoading,
  selectedProject,
  dataSourcesToDisplay,
}: {
  dataSourcesForProjectIsLoading: boolean;
  selectedProject: number;
  dataSourcesToDisplay: (DataSourceType & { color: string })[];
}) => {
  return (
    <>
      <Typography style={{ marginBottom: 20 }}>
        Knowledge bases in project:
      </Typography>
      {dataSourcesForProjectIsLoading && (
        <Skeleton active={true} paragraph={{ rows: 0 }} />
      )}
      {selectedProject && !dataSourcesForProjectIsLoading ? (
        <Flex>
          {dataSourcesToDisplay.map((ds) => {
            return (
              <Tag key={ds.id} color={ds.color}>
                {ds.name}
              </Tag>
            );
          })}
        </Flex>
      ) : (
        <Typography.Paragraph italic>
          No knowledge bases present
        </Typography.Paragraph>
      )}
    </>
  );
};

const ProjectSelection = () => {
  const {
    session,
    projects,
    dataSources,
    selectedProject,
    setSelectedProject,
    dataSourcesForProjectIsLoading,
    dataSourcesForProject,
    dataSourcesToTransfer,
  } = useContext(MoveSessionContext);
  const projectOptions = getProjectOptions(session, projects);
  const dataSourcesToDisplay = !dataSourcesForProject
    ? []
    : dataSourcesForProject.map((ds) => {
        return { ...ds, color: cdlBlue600 };
      });
  dataSourcesToTransfer.forEach((kb) => {
    const dataSource = dataSources?.find((ds) => ds.id === kb);
    if (dataSource) {
      dataSourcesToDisplay.push({ ...dataSource, color: cdlGreen600 });
    }
  });

  return (
    <Card
      title="Move to:"
      style={{ width: 350, minHeight: 200 }}
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
      {selectedProject ? (
        <ProjectKnowledgeBases
          dataSourcesForProjectIsLoading={dataSourcesForProjectIsLoading}
          selectedProject={selectedProject}
          dataSourcesToDisplay={dataSourcesToDisplay}
        />
      ) : null}
    </Card>
  );
};

export default ProjectSelection;
