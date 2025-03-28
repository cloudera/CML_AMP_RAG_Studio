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

import useModal from "src/utils/useModal.ts";
import { Button, Flex, Form, Input, Modal, Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";
import { useCreateProject } from "src/api/projectsApi.ts";
import { QueryKeys } from "src/api/utils.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { PlusCircleOutlined, ProjectOutlined } from "@ant-design/icons";
import { useNavigate } from "@tanstack/react-router";

export const ProjectsHeaderItem = () => {
  const createProjectModal = useModal();
  const [form] = Form.useForm<{ name: string }>();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const createProject = useCreateProject({
    onSuccess: (project) => {
      createProjectModal.setIsModalOpen(false);
      queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getProjects] })
        .then(() => {
          return navigate({
            to: "/chats/projects/$projectId",
            params: { projectId: project.id.toString() },
          });
        })
        .catch(() => {
          messageQueue.error("Failed to refresh projects");
        });
    },
    onError: () => {
      messageQueue.error("Failed to create a new project");
    },
  });
  const handleCreateNewProject = () => {
    form
      .validateFields()
      .then((values) => {
        createProject.mutate({ name: values.name });
      })
      .catch(() => null);
  };

  return (
    <Flex
      justify="space-between"
      gap={6}
      style={{ paddingLeft: 12, paddingTop: 8 }}
    >
      <Flex gap={8} align="center">
        <ProjectOutlined />
        <Typography.Text type="secondary">Projects</Typography.Text>
      </Flex>
      <Button
        type="text"
        icon={<PlusCircleOutlined />}
        onClick={() => {
          createProjectModal.setIsModalOpen(true);
        }}
      />
      <Modal
        title="Create New Project"
        open={createProjectModal.isModalOpen}
        destroyOnClose={true}
        onCancel={() => {
          createProjectModal.setIsModalOpen(false);
        }}
        footer={
          <Button onClick={handleCreateNewProject} type="primary">
            OK
          </Button>
        }
      >
        <Form form={form} clearOnDestroy={true}>
          <Form.Item
            name="name"
            label="Project name"
            rules={[
              { required: true, message: "Please provide a project name" },
            ]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Flex>
  );
};
