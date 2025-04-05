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
import { DataSourceType } from "src/api/dataSourceApi.ts";
import { Card, Flex, Select, Tag, Typography } from "antd";
import { cdlGreen600 } from "src/cuix/variables.ts";

const ProjectSelection = ({
  session,
  projects,
  setSelectedProject,
  dataSourcesForProject,
  dataSourcesToTransfer,
  dataSources,
  selectedProject,
}: {
  session: Session;
  projects?: Project[];
  setSelectedProject: (projectId: number) => void;
  dataSourcesForProject?: DataSourceType[];
  dataSourcesToTransfer: number[];
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
          {dataSourcesToTransfer.map((kb) => {
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

export default ProjectSelection;
