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
  Tool,
  useDeleteToolMutation,
  useToolsQuery,
} from "src/api/toolsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import useModal from "src/utils/useModal.ts";
import { AddNewToolModal } from "pages/Tools/AddNewToolModal.tsx";

const ToolsPage = () => {
  const confirmDeleteModal = useModal();
  const { data: tools = [], isLoading, error: toolsError } = useToolsQuery();
  const [isModalVisible, setIsModalVisible] = useState(false);

  const deleteToolMutation = useDeleteToolMutation({
    onSuccess: () => {
      messageQueue.success("Tool deleted successfully");
      confirmDeleteModal.setIsModalOpen(false);
    },
    onError: (error) => {
      messageQueue.error(`Failed to delete tool: ${error.message}`);
    },
  });

  const columns = [
    {
      title: "Internal Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Display Name",
      dataIndex: ["metadata", "display_name"],
      key: "display_name",
    },
    {
      title: "Description",
      dataIndex: ["metadata", "description"],
      key: "description",
    },
    {
      title: "Actions",
      key: "actions",
      width: 80,
      render: (_: unknown, tool: Tool) => (
        <>
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              confirmDeleteModal.setIsModalOpen(true);
            }}
          />
          <Modal
            title="Delete tool?"
            open={confirmDeleteModal.isModalOpen}
            onOk={() => {
              deleteToolMutation.mutate(tool.name);
            }}
            okText={"Yes, delete it!"}
            okButtonProps={{
              danger: true,
            }}
            onCancel={() => {
              confirmDeleteModal.handleCancel();
            }}
          />
        </>
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
        <Typography.Title level={3}>MCP Tools Management</Typography.Title>
        <Typography.Paragraph>
          Manage external tools and services that can be used by the RAG Studio
          application. These tools can be used during query processing to
          enhance the capabilities of the system.
          <br />
          <br />
          See{" "}
          <Typography.Link
            onClick={() => {
              window.open(
                "https://github.com/cloudera/CML_AMP_RAG_Studio/tree/main/tools",
                "_blank",
              );
            }}
          >
            docs
          </Typography.Link>{" "}
          for manually adding additional tools.
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
                Available Tools
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
              dataSource={tools}
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
      </Flex>
    </Layout>
  );
};

export default ToolsPage;
