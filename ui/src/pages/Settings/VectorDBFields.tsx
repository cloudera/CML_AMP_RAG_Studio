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
  selectedVectorDBProvider,
  projectConfig,
  enableModification,
}: {
  selectedVectorDBProvider: VectorDBProvider;
  projectConfig?: ProjectConfig | null;
  enableModification?: boolean;
}) => (
  <Flex vertical style={{ maxWidth: 600 }}>
    <Form.Item
      initialValue={projectConfig?.vector_db_provider}
      name="vector_db_provider"
    >
      <Radio.Group
        optionType="button"
        buttonStyle="solid"
        options={[
          { value: "QDRANT", label: "Qdrant" },
          { value: "OPENSEARCH", label: "Cloudera Semantic Search" },
        ]}
        disabled={!enableModification}
      />
    </Form.Item>
    {selectedVectorDBProvider === "QDRANT" && (
      <StyledHelperText>
        Embedded Qdrant will be used as the vector database.
      </StyledHelperText>
    )}
    {selectedVectorDBProvider === "OPENSEARCH" ? (
      <StyledHelperText>
        We currently support OpenSearch versions up to and including 2.19.3
      </StyledHelperText>
    ) : null}
    <Form.Item
      label={"OpenSearch Endpoint"}
      initialValue={projectConfig?.opensearch_config.opensearch_endpoint}
      name={["opensearch_config", "opensearch_endpoint"]}
      required={selectedVectorDBProvider === "OPENSEARCH"}
      tooltip="Cloudera Semantic Search instance endpoint."
      rules={[{ required: selectedVectorDBProvider === "OPENSEARCH" }]}
      hidden={selectedVectorDBProvider !== "OPENSEARCH"}
    >
      <Input
        placeholder="http://localhost:9200/"
        disabled={!enableModification}
      />
    </Form.Item>
    <Form.Item
      label={"OpenSearch Namespace"}
      initialValue={projectConfig?.opensearch_config.opensearch_namespace}
      name={["opensearch_config", "opensearch_namespace"]}
      required={selectedVectorDBProvider === "OPENSEARCH"}
      tooltip="The namespace or prefix to use for Cloudera Semantic Search. This is arbitrary, but must be unique to your project."
      rules={[
        { required: selectedVectorDBProvider === "OPENSEARCH" },
        {
          pattern: /^[a-zA-Z0-9]+$/,
          message: "Only alphanumeric characters are allowed",
          warningOnly: false,
        },
      ]}
      hidden={selectedVectorDBProvider !== "OPENSEARCH"}
    >
      <Input placeholder="rag_document_index" disabled={!enableModification} />
    </Form.Item>
    <Form.Item
      label={"OpenSearch Username"}
      initialValue={projectConfig?.opensearch_config.opensearch_username}
      name={["opensearch_config", "opensearch_username"]}
      tooltip="Cloudera Semantic Search username."
      hidden={selectedVectorDBProvider !== "OPENSEARCH"}
    >
      <Input placeholder="admin" />
    </Form.Item>
    <Form.Item
      label={"OpenSearch Password"}
      initialValue={projectConfig?.opensearch_config.opensearch_password}
      name={["opensearch_config", "opensearch_password"]}
      tooltip="Cloudera Semantic Search password."
      hidden={selectedVectorDBProvider !== "OPENSEARCH"}
    >
      <Input type="password" placeholder="admin" />
    </Form.Item>
  </Flex>
);
