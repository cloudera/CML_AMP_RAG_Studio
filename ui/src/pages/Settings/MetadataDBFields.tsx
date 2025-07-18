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
  ProjectConfig,
  MetadataDBProvider,
  useValidateJdbcConnection,
} from "src/api/ampMetadataApi.ts";
import { Button, Flex, Form, FormInstance, Input, Radio } from "antd";
import { StyledHelperText } from "pages/Settings/AmpSettingsPage.tsx";
import messageQueue from "src/utils/messageQueue.ts";

const MetadataDatabaseFields = ({
  selectedMetadataDBProvider,
  projectConfig,
  enableModification,
  form,
}: {
  selectedMetadataDBProvider: MetadataDBProvider;
  projectConfig?: ProjectConfig | null;
  enableModification?: boolean;
  form: FormInstance<ProjectConfig>;
}) => {
  const testConnection = useValidateJdbcConnection({
    onSuccess: () => {
      messageQueue.success("Connection successful!");
    },
    onError: (error) => {
      messageQueue.error(`Connection failed: ${error.message}`);
    },
  });
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
        initialValue={projectConfig?.metadata_db_config.username}
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
        initialValue={projectConfig?.metadata_db_config.password}
        name={["metadata_db_config", "password"]}
        required={selectedMetadataDBProvider === "PostgreSQL"}
        tooltip="PostgreSQL password"
        rules={[{ required: selectedMetadataDBProvider === "PostgreSQL" }]}
        hidden={selectedMetadataDBProvider !== "PostgreSQL"}
      >
        <Input.Password placeholder="password" disabled={!enableModification} />
      </Form.Item>
      <Flex justify="flex-end">
        <Button
          type="primary"
          onClick={() => {
            // pass the values from the form to the testConnection mutation
            testConnection.mutate({
              jdbc_url: form.getFieldValue(["metadata_db_config", "jdbc_url"]),
              username: form.getFieldValue(["metadata_db_config", "username"]),
              password: form.getFieldValue(["metadata_db_config", "password"]),
              db_type: selectedMetadataDBProvider,
            });
          }}
          style={{ width: 160 }}
          disabled={}
        >
          Test Connection
        </Button>
      </Flex>
    </Flex>
  );
};

export default MetadataDatabaseFields;
