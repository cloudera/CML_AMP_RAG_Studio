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

import { ProjectConfig, VectorDBProvider } from "src/api/ampMetadataApi.ts";
import { Flex, Form, Input, Radio } from "antd";
import { StyledHelperText } from "pages/Settings/AmpSettingsPage.tsx";

export const VectorDBFields = ({
  projectConfig,
  setSelectedVectorDB,
  selectedVectorDB,
  enableModification,
}: {
  projectConfig?: ProjectConfig | null;
  setSelectedVectorDB: (value: VectorDBProvider) => void;
  selectedVectorDB: VectorDBProvider;
  enableModification?: boolean;
}) => (
  <Flex vertical style={{ maxWidth: 600 }}>
    <Radio.Group
      style={{ marginBottom: 20 }}
      optionType="button"
      buttonStyle="solid"
      onChange={(e) => {
        if (e.target.value === "QDRANT" || e.target.value === "OPENSEARCH") {
          setSelectedVectorDB(e.target.value as VectorDBProvider);
        }
      }}
      value={selectedVectorDB}
      options={[
        { value: "QDRANT", label: "Qdrant" },
        { value: "OPENSEARCH", label: "Cloudera Semantic Search" },
      ]}
      disabled={!enableModification}
    />
    {selectedVectorDB === "QDRANT" && (
      <StyledHelperText>
        Qdrant will be used as the vector database.
      </StyledHelperText>
    )}
    <Form.Item
      label={"Endpoint"}
      initialValue={projectConfig?.opensearch_config.opensearch_endpoint}
      name={["opensearch_config", "opensearch_endpoint"]}
      required={selectedVectorDB === "OPENSEARCH"}
      tooltip="Cloudera Semantic Search instance endpoint."
      rules={[{ required: selectedVectorDB === "OPENSEARCH" }]}
      hidden={selectedVectorDB !== "OPENSEARCH"}
    >
      <Input
        placeholder="http://localhost:9200/"
        disabled={!enableModification}
      />
    </Form.Item>
    <Form.Item
      label={"Username"}
      initialValue={projectConfig?.opensearch_config.opensearch_username}
      name={["opensearch_config", "opensearch_username"]}
      required={selectedVectorDB === "OPENSEARCH"}
      tooltip="Cloudera Semantic Search username."
      rules={[{ required: selectedVectorDB === "OPENSEARCH" }]}
      hidden={selectedVectorDB !== "OPENSEARCH"}
    >
      <Input placeholder="admin" disabled={!enableModification} />
    </Form.Item>
    <Form.Item
      label={"Password"}
      initialValue={projectConfig?.opensearch_config.opensearch_password}
      name={["opensearch_config", "opensearch_password"]}
      required={selectedVectorDB === "OPENSEARCH"}
      tooltip="Cloudera Semantic Search password."
      rules={[{ required: selectedVectorDB === "OPENSEARCH" }]}
      hidden={selectedVectorDB !== "OPENSEARCH"}
    >
      <Input
        type="password"
        placeholder="admin"
        disabled={!enableModification}
      />
    </Form.Item>
  </Flex>
);
