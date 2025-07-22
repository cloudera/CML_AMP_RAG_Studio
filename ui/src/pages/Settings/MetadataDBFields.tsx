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

import {
  MetadataDBProvider,
  ProjectConfig,
  useValidateJdbcConnection,
  ValidationResult,
} from "src/api/ampMetadataApi.ts";
import { Button, Flex, Form, Input, Radio, Tooltip } from "antd";
import { StyledHelperText } from "pages/Settings/AmpSettingsPage.tsx";
import messageQueue from "src/utils/messageQueue.ts";
import { useState } from "react";
import { cdlGreen600, cdlRed600 } from "src/cuix/variables.ts";
import { CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";

const TestResultIcon = ({ result }: { result?: ValidationResult }) => {
  if (!result) {
    return null;
  }

  const OutlinedIcon = result.valid ? CheckCircleOutlined : CloseCircleOutlined;
  const color = result.valid ? cdlGreen600 : cdlRed600;

  return (
    <Tooltip title={result.message}>
      <OutlinedIcon
        style={{ color, marginRight: 12, fontSize: 20 }}
        size={32}
      />
    </Tooltip>
  );
};

const formItemLayout = {
  labelCol: {
    xs: { span: 24 },
    sm: { span: 8 },
  },
  wrapperCol: {
    xs: { span: 24 },
    sm: { span: 16 },
  },
};

const MetadataDatabaseFields = ({
  selectedMetadataDBProvider,
  projectConfig,
  enableModification,
  formValues,
}: {
  selectedMetadataDBProvider: MetadataDBProvider;
  projectConfig?: ProjectConfig | null;
  enableModification?: boolean;
  formValues?: ProjectConfig;
}) => {
  const [testResult, setTestResult] = useState<ValidationResult>();
  const testConnection = useValidateJdbcConnection({
    onSuccess: (result: ValidationResult) => {
      setTestResult(result);
    },
    onError: (error) => {
      setTestResult({
        valid: false,
        message: error.message || "Connection failed",
      });
    },
  });

  const handleTestConnection = () => {
    if (!formValues) {
      return;
    }

    const {
      metadata_db_config: { jdbc_url, username, password },
    } = formValues;

    if (!jdbc_url || !username || !password) {
      messageQueue.error("JDBC URL, username, and password are required for testing connection.");
      return;
    }

    setTestResult(undefined);
    testConnection.mutate({
      db_url: jdbc_url,
      username: username,
      password: password,
      db_type: selectedMetadataDBProvider,
    });
  };

  return (
    <Flex vertical style={{ maxWidth: 600 }}>
      <Form.Item
        initialValue={projectConfig?.metadata_db_provider ?? "H2"}
        name="metadata_db_provider"
      >
        <Radio.Group
          optionType="button"
          buttonStyle="solid"
          options={[
            { value: "H2", label: "Embedded" },
            { value: "PostgreSQL", label: "External PostgreSQL" },
          ]}
          disabled={!enableModification}
        />
      </Form.Item>
      {selectedMetadataDBProvider === "H2" && (
        <StyledHelperText>
          Embedded H2 database will be used as the metadata database.
        </StyledHelperText>
      )}
      <Form.Item
        label={"PostgreSQL JDBC URL"}
        {...formItemLayout}
        initialValue={projectConfig?.metadata_db_config.jdbc_url}
        name={["metadata_db_config", "jdbc_url"]}
        required={selectedMetadataDBProvider === "PostgreSQL"}
        tooltip="PostgreSQL instance JDBC URL. Example: jdbc:postgresql://xyz.us-west-2.rds.amazonaws.com:5432/rag"
        rules={[{ required: selectedMetadataDBProvider === "PostgreSQL" }]}
        hidden={selectedMetadataDBProvider !== "PostgreSQL"}
      >
        <Input
          placeholder="jdbc:postgresql://xyz.us-west-2.rds.amazonaws.com:5432/rag"
          disabled={!enableModification}
        />
      </Form.Item>
      <Form.Item
        label={"PostgreSQL Username"}
        {...formItemLayout}
        initialValue={projectConfig?.metadata_db_config.username ?? ""}
        name={["metadata_db_config", "username"]}
        required={selectedMetadataDBProvider === "PostgreSQL"}
        tooltip="PostgreSQL username"
        rules={[{ required: selectedMetadataDBProvider === "PostgreSQL" }]}
        hidden={selectedMetadataDBProvider !== "PostgreSQL"}
      >
        <Input placeholder="postgres" disabled={!enableModification} />
      </Form.Item>
      <Form.Item
        label={"PostgreSQL Password"}
        {...formItemLayout}
        initialValue={projectConfig?.metadata_db_config.password ?? ""}
        name={["metadata_db_config", "password"]}
        required={selectedMetadataDBProvider === "PostgreSQL"}
        tooltip="PostgreSQL password"
        rules={[{ required: selectedMetadataDBProvider === "PostgreSQL" }]}
        hidden={selectedMetadataDBProvider !== "PostgreSQL"}
      >
        <Input.Password placeholder="password" disabled={!enableModification} />
      </Form.Item>
      {selectedMetadataDBProvider === "PostgreSQL" && (
        <Flex justify="flex-end">
          <TestResultIcon result={testResult} />
          <Button
            type="default"
            onClick={handleTestConnection}
            style={{ width: 160 }}
            disabled={
              !formValues?.metadata_db_config.jdbc_url ||
              !formValues.metadata_db_config.username ||
              !formValues.metadata_db_config.password ||
              testConnection.isPending
            }
          >
            Test Connection
          </Button>
        </Flex>
      )}
    </Flex>
  );
};

export default MetadataDatabaseFields;
