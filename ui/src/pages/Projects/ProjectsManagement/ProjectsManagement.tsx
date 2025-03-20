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

import { useState } from "react";
import {
  Button,
  Card,
  Flex,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Table,
  Typography,
  message,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import {
  CreateProject,
  Project,
  useCreateProject,
  useDeleteProject,
  useGetDataSourceIdsForProject,
  useGetProjects,
  useUpdateProject,
} from "src/api/projectsApi";
import { DataSourceType, useGetDataSourcesQuery } from "src/api/dataSourceApi";

const { Title } = Typography;

interface ProjectFormValues {
  name: string;
}

const ProjectsManagement = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [form] = Form.useForm<ProjectFormValues>();
  const [messageApi, contextHolder] = message.useMessage();

  const { data: projects = [], refetch: refetchProjects } = useGetProjects();
  const { data: dataSources = [] } = useGetDataSourcesQuery();

  const { mutate: createProject } = useCreateProject({
    onSuccess: () => {
      messageApi.success("Project created successfully");
      setIsCreateModalOpen(false);
      form.resetFields();
      void refetchProjects();
    },
    onError: (error: Error) => {
      messageApi.error(`Failed to create project: ${error.message}`);
    },
  });

  const { mutate: updateProject } = useUpdateProject({
    onSuccess: () => {
      messageApi.success("Project updated successfully");
      setIsEditModalOpen(false);
      form.resetFields();
      void refetchProjects();
    },
    onError: (error: Error) => {
      messageApi.error(`Failed to update project: ${error.message}`);
    },
  });

  const { mutate: deleteProject } = useDeleteProject({
    onSuccess: () => {
      messageApi.success("Project deleted successfully");
      void refetchProjects();
    },
    onError: (error: Error) => {
      messageApi.error(`Failed to delete project: ${error.message}`);
    },
  });

  const handleCreateProject = (values: ProjectFormValues) => {
    const newProject: CreateProject = {
      name: values.name,
    };
    createProject(newProject);
  };

  const handleEditProject = (values: ProjectFormValues) => {
    if (!selectedProject) return;

    const updatedProject: Project = {
      ...selectedProject,
      name: values.name,
    };
    updateProject(updatedProject);
  };

  const handleDeleteProject = (projectId: number) => {
    deleteProject(projectId);
  };

  const openEditModal = (project: Project) => {
    setSelectedProject(project);
    form.setFieldsValue({
      name: project.name,
    });
    setIsEditModalOpen(true);
  };

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Default",
      dataIndex: "defaultProject",
      key: "defaultProject",
      render: (defaultProject: boolean) => (defaultProject ? "Yes" : "No"),
    },
    {
      title: "Created By",
      dataIndex: "createdById",
      key: "createdById",
    },
    {
      title: "Created At",
      dataIndex: "timeCreated",
      key: "timeCreated",
      render: (timeCreated: string) =>
        timeCreated ? new Date(timeCreated).toLocaleString() : "",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: Project) => (
        <Space size="middle">
          <Button
            type="link"
            onClick={() => {
              openEditModal(record);
            }}
          >
            Edit
          </Button>
          {!record.defaultProject && (
            <Popconfirm
              title="Are you sure you want to delete this project?"
              onConfirm={() => {
                if (record.id) {
                  handleDeleteProject(record.id);
                }
              }}
              okText="Yes"
              cancelText="No"
            >
              <Button type="link" danger>
                Delete
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  const ProjectDataSourcesTable = ({ projectId }: { projectId: number }) => {
    const { data: dataSourceIds = [] } =
      useGetDataSourceIdsForProject(projectId);

    const projectDataSources = dataSources.filter((ds: DataSourceType) =>
      dataSourceIds.includes(ds.id)
    );

    return (
      <Table
        dataSource={projectDataSources}
        columns={[
          {
            title: "Name",
            dataIndex: "name",
            key: "name",
          },
          {
            title: "Document Count",
            dataIndex: "documentCount",
            key: "documentCount",
          },
        ]}
        rowKey="id"
        pagination={false}
      />
    );
  };

  return (
    <>
      {contextHolder}
      <Flex justify="space-between" align="center" style={{ marginBottom: 16 }}>
        <Title level={2}>Projects</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setIsCreateModalOpen(true);
          }}
        >
          Create Project
        </Button>
      </Flex>

      <Table
        dataSource={projects}
        columns={columns}
        rowKey="id"
        expandable={{
          expandedRowRender: (record) => {
            if (record.id) {
              return (
                <Card title="Associated Data Sources">
                  <ProjectDataSourcesTable projectId={record.id} />
                </Card>
              );
            }
            return null;
          },
        }}
      />

      {/* Create Project Modal */}
      <Modal
        title="Create Project"
        open={isCreateModalOpen}
        onCancel={() => {
          setIsCreateModalOpen(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateProject}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="name"
            label="Project Name"
            rules={[
              { required: true, message: "Please enter a project name" },
              { max: 100, message: "Name cannot exceed 100 characters" },
            ]}
          >
            <Input placeholder="Enter project name" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: "right" }}>
            <Space>
              <Button
                onClick={() => {
                  setIsCreateModalOpen(false);
                  form.resetFields();
                }}
              >
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                Create
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Project Modal */}
      <Modal
        title="Edit Project"
        open={isEditModalOpen}
        onCancel={() => {
          setIsEditModalOpen(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEditProject}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="name"
            label="Project Name"
            rules={[
              { required: true, message: "Please enter a project name" },
              { max: 100, message: "Name cannot exceed 100 characters" },
            ]}
          >
            <Input placeholder="Enter project name" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: "right" }}>
            <Space>
              <Button
                onClick={() => {
                  setIsEditModalOpen(false);
                  form.resetFields();
                }}
              >
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                Update
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default ProjectsManagement;
