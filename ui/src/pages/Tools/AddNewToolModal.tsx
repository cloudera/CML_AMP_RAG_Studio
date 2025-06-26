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

import { Button, Flex, Form, Input, Modal, Space, Typography } from "antd";
import {
  AddToolFormValues,
  Tool,
  useAddToolMutation,
} from "src/api/toolsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { useState } from "react";
import { MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";

const CommandFormFields = () => {
  return (
    <>
      <Form.Item
        name="command"
        label="Command"
        rules={[{ required: true, message: "Please enter a command" }]}
      >
        <Input placeholder="tool executable (ex. uvx, npx)" />
      </Form.Item>

      <Form.Item name="args" label="Arguments (comma-separated)">
        <Input placeholder="--option,value" />
      </Form.Item>

      <Flex gap={6} vertical={true}>
        <Typography.Text>Environment Variables</Typography.Text>
        <Form.List name="env">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Space
                  key={key}
                  style={{ display: "flex", marginBottom: 8 }}
                  align="baseline"
                >
                  <Form.Item
                    {...restField}
                    name={[name, "key"]}
                    rules={[{ required: true, message: "Missing key" }]}
                  >
                    <Input placeholder="API_KEY" />
                  </Form.Item>
                  <Form.Item
                    {...restField}
                    name={[name, "value"]}
                    rules={[{ required: true, message: "Missing value" }]}
                  >
                    <Input.Password placeholder="api-key" />
                  </Form.Item>
                  <MinusCircleOutlined
                    onClick={() => {
                      remove(name);
                    }}
                  />
                </Space>
              ))}
              <Form.Item>
                <Button
                  type="dashed"
                  onClick={() => {
                    add();
                  }}
                  block
                  icon={<PlusOutlined />}
                >
                  Add environment variable
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>
      </Flex>
    </>
  );
};

const UrlFormFields = () => {
  return (
    <Form.Item
      name="url"
      label="URLs (comma-separated)"
      rules={[{ required: true, message: "Please enter at least one URL" }]}
    >
      <Input placeholder="http://api.example.com/endpoint" />
    </Form.Item>
  );
};

export const AddNewToolModal = ({
  isModalVisible,
  setIsModalVisible,
}: {
  isModalVisible: boolean;
  setIsModalVisible: (visible: boolean) => void;
}) => {
  const [form] = Form.useForm<AddToolFormValues>();
  const [toolType, setToolType] = useState<"command" | "url">("command");
  const addToolMutation = useAddToolMutation({
    onSuccess: () => {
      messageQueue.success("Tool added successfully");
      setIsModalVisible(false);
      form.resetFields();
    },
    onError: (error) => {
      messageQueue.error(`Failed to add tool: ${error.message}`);
    },
  });

  const handleAddTool = () => {
    void form.validateFields().then((values) => {
      const newTool: Tool = {
        name: values.name,
        metadata: {
          display_name: values.display_name,
          description: values.description,
        },
      };

      if (toolType === "command") {
        newTool.command = values.command;
        if (values.args) {
          newTool.args = values.args.split(",").map((arg) => arg.trim());
        }
        if (values.env?.length) {
          newTool.env = values.env.reduce((accum, val) => {
            return { ...accum, [val.key]: val.value };
          }, {});
        }
      } else {
        if (values.url) {
          newTool.url = values.url.split(",").map((url) => url.trim());
        }
      }

      addToolMutation.mutate(newTool);
    });
  };

  return (
    <Modal
      title="Add New Tool"
      open={isModalVisible}
      onCancel={() => {
        setIsModalVisible(false);
        form.resetFields();
      }}
      footer={[
        <Button
          key="cancel"
          onClick={() => {
            setIsModalVisible(false);
            form.resetFields();
          }}
        >
          Cancel
        </Button>,
        <Button
          key="submit"
          type="primary"
          onClick={handleAddTool}
          loading={addToolMutation.isPending}
        >
          Add
        </Button>,
      ]}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="Internal Name"
          rules={[
            { required: true, message: "Please enter a name" },
            {
              pattern: /^[a-zA-Z0-9\\-]+$/,
              message: "Only alphanumeric characters and dashes are allowed",
              warningOnly: false,
            },
          ]}
        >
          <Input placeholder="my-tool-name" />
        </Form.Item>

        <Form.Item
          name="display_name"
          label="Display Name"
          rules={[{ required: true, message: "Please enter a display name" }]}
        >
          <Input placeholder="My Tool" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Description"
          rules={[{ required: true, message: "Please enter a description" }]}
        >
          <Input.TextArea
            placeholder="This tool performs a specific function..."
            rows={3}
          />
        </Form.Item>

        <Form.Item label="Tool Type">
          <Space>
            <Button
              type={toolType === "command" ? "primary" : "default"}
              onClick={() => {
                setToolType("command");
              }}
            >
              Command-based
            </Button>
            <Button
              type={toolType === "url" ? "primary" : "default"}
              onClick={() => {
                setToolType("url");
              }}
            >
              URL-based
            </Button>
          </Space>
        </Form.Item>

        {toolType === "command" ? CommandFormFields() : UrlFormFields()}
      </Form>
    </Modal>
  );
};
