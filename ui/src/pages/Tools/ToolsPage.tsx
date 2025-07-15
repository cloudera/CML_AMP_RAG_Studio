/*
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2025
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
 */

import { useState } from "react";
import {
  Alert,
  Button,
  Card,
  Flex,
  Layout,
  Modal,
  Table,
  Typography,
} from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import {
  useDeleteToolMutation,
  useDeleteCustomToolMutation,
  useToolsQuery,
  useCustomToolsQuery,
} from "src/api/toolsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import useModal from "src/utils/useModal.ts";
import { AddNewToolModal } from "pages/Tools/AddNewToolModal.tsx";

interface UnifiedTool {
  name: string;
  display_name: string;
  description: string;
  type: "mcp" | "custom";
}

const ToolsPage = () => {
  const confirmDeleteModal = useModal();
  const {
    data: mcpTools = [],
    isLoading: mcpLoading,
    error: mcpError,
  } = useToolsQuery();
  const {
    data: customTools = [],
    isLoading: customLoading,
    error: customError,
  } = useCustomToolsQuery();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [toolToDelete, setToolToDelete] = useState<UnifiedTool | null>(null);

  // Transform data into unified format
  const unifiedTools: UnifiedTool[] = [
    ...mcpTools.map(
      (tool): UnifiedTool => ({
        name: tool.name,
        display_name: tool.metadata.display_name,
        description: tool.metadata.description,
        type: "mcp",
      })
    ),
    ...customTools.map(
      (tool): UnifiedTool => ({
        name: tool.name,
        display_name: tool.display_name,
        description: tool.description,
        type: "custom",
      })
    ),
  ];

  const isLoading = mcpLoading || customLoading;
  const toolsError = mcpError ?? customError;

  const deleteToolMutation = useDeleteToolMutation({
    onSuccess: () => {
      messageQueue.success("MCP tool deleted successfully");
      confirmDeleteModal.setIsModalOpen(false);
      setToolToDelete(null);
    },
    onError: (error) => {
      messageQueue.error(`Failed to delete MCP tool: ${error.message}`);
    },
  });

  const deleteCustomToolMutation = useDeleteCustomToolMutation({
    onSuccess: () => {
      messageQueue.success("Custom tool deleted successfully");
      confirmDeleteModal.setIsModalOpen(false);
      setToolToDelete(null);
    },
    onError: (error) => {
      messageQueue.error(`Failed to delete custom tool: ${error.message}`);
    },
  });

  const handleDeleteTool = (tool: UnifiedTool) => {
    setToolToDelete(tool);
    confirmDeleteModal.setIsModalOpen(true);
  };

  const confirmDelete = () => {
    if (!toolToDelete) return;

    if (toolToDelete.type === "mcp") {
      deleteToolMutation.mutate(toolToDelete.name);
    } else {
      deleteCustomToolMutation.mutate(toolToDelete.name);
    }
  };

  const columns = [
    {
      title: "Internal Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Display Name",
      dataIndex: "display_name",
      key: "display_name",
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
    },
    {
      title: "Type",
      dataIndex: "type",
      key: "type",
      render: (type: "mcp" | "custom") => (
        <span
          style={{
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "12px",
            fontWeight: "500",
            backgroundColor: type === "mcp" ? "#e6f4ff" : "#f6ffed",
            color: type === "mcp" ? "#1890ff" : "#52c41a",
            border: `1px solid ${type === "mcp" ? "#91caff" : "#b7eb8f"}`,
          }}
        >
          {type === "mcp" ? "MCP Tool" : "Custom Tool"}
        </span>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      width: 80,
      render: (_: unknown, tool: UnifiedTool) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteTool(tool)}
        />
      ),
    },
  ];

  return (
    <Layout
      style={{
        alignItems: "center",
        width: "100%",
        paddingLeft: 60,
      }}
    >
      <Flex vertical gap={20}>
        <Typography.Title level={3}>Tools Management</Typography.Title>
        <Typography.Paragraph>
          Manage external tools and services that can be used by the RAG Studio
          application. This includes both MCP (Model Context Protocol) tools and
          custom user-submitted tools. These tools can be used during query
          processing to enhance the capabilities of the system.
          <br />
          <br />
          See{" "}
          <Typography.Link
            onClick={() => {
              window.open(
                "https://github.com/cloudera/CML_AMP_RAG_Studio/tree/main/tools",
                "_blank"
              );
            }}
          >
            docs
          </Typography.Link>{" "}
          for manually adding additional MCP tools.
        </Typography.Paragraph>

        {toolsError ? (
          <Alert type="error" description={toolsError.message} />
        ) : (
          <Card>
            <Flex
              justify="space-between"
              align="center"
              style={{ marginBottom: 16 }}
            >
              <Typography.Title level={4} style={{ margin: 0 }}>
                Available Tools ({unifiedTools.length})
              </Typography.Title>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setIsModalVisible(true);
                }}
              >
                Add Tool
              </Button>
            </Flex>
            <Table
              dataSource={unifiedTools}
              columns={columns}
              rowKey="name"
              loading={isLoading}
              scroll={{ x: 1 }}
            />
          </Card>
        )}

        <AddNewToolModal
          setIsModalVisible={setIsModalVisible}
          isModalVisible={isModalVisible}
        />

        <Modal
          title={`Delete ${toolToDelete?.type === "mcp" ? "MCP" : "custom"} tool?`}
          open={confirmDeleteModal.isModalOpen}
          onOk={confirmDelete}
          okText="Yes, delete it!"
          okButtonProps={{
            danger: true,
            loading:
              deleteToolMutation.isPending ||
              deleteCustomToolMutation.isPending,
          }}
          onCancel={() => {
            confirmDeleteModal.handleCancel();
            setToolToDelete(null);
          }}
        >
          Are you sure you want to delete the tool "{toolToDelete?.display_name}
          "? This action cannot be undone.
        </Modal>
      </Flex>
    </Layout>
  );
};

export default ToolsPage;
