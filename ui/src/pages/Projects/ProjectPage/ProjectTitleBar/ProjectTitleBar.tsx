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

import { useProjectContext } from "pages/Projects/ProjectContext.tsx";
import { Button, Flex, Input, Typography } from "antd";
import { EditOutlined, ProjectOutlined } from "@ant-design/icons";
import { DeleteProjectButton } from "pages/Projects/ProjectPage/ProjectTitleBar/DeleteProjectButton.tsx";
import { useUpdateProject } from "src/api/projectsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { useEffect, useState } from "react";

export const ProjectTitleBar = () => {
  const { project } = useProjectContext();
  const editProject = useUpdateProject({
    onSuccess: () => {
      messageQueue.success("Project name updated");
      setEditing(false);
    },
    onError: () => {
      messageQueue.error("Failed to update project name");
      setEditing(false);
    },
  });
  const [editing, setEditing] = useState(false);
  const [newName, setNewName] = useState(project.name);

  useEffect(() => {
    setNewName(project.name);
  }, [project.name, editing]);

  const handleEditProjectName = () => {
    if (newName.length > 0 && newName !== project.name) {
      editProject.mutate({
        ...project,
        name: newName,
      });
    }
  };

  return (
    <Flex justify="space-between" align="baseline">
      <Flex align="baseline" style={{ height: 80 }}>
        <Typography.Title level={2}>
          <ProjectOutlined style={{ marginLeft: 16, marginRight: 8 }} />
        </Typography.Title>
        {editing ? (
          <Input
            onChange={(e) => {
              setNewName(e.target.value);
            }}
            onPressEnter={() => {
              handleEditProjectName();
            }}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setEditing(false);
              }
            }}
            value={newName}
            style={{
              fontSize: 30,
              fontWeight: 600,
              width: 500,
            }}
            onBlur={() => {
              setEditing(false);
            }}
            autoFocus={true}
          />
        ) : (
          <>
            <Typography.Title level={2} style={{ margin: 0 }}>
              {project.name}
            </Typography.Title>
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => {
                setEditing(true);
              }}
            />
          </>
        )}
      </Flex>
      <DeleteProjectButton project={project} />
    </Flex>
  );
};
