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

import { ProjectConfig } from "src/api/ampMetadataApi.ts";
import { Checkbox, Flex, Form, Input, Radio } from "antd";
import { FileStorage, StyledHelperText } from "pages/Settings/SettingsPage.tsx";

export const FileStorageFields = ({
  projectConfig,
  setSelectedFileStorage,
  selectedFileStorage,
  enableModification,
}: {
  projectConfig?: ProjectConfig;
  setSelectedFileStorage: (value: FileStorage) => void;
  selectedFileStorage: FileStorage;
  enableModification?: boolean;
}) => (
  <Flex vertical style={{ maxWidth: 600 }}>
    <Radio.Group
      style={{ marginBottom: 20 }}
      optionType="button"
      buttonStyle="solid"
      onChange={(e) => {
        if (e.target.value === "AWS" || e.target.value === "Local") {
          setSelectedFileStorage(e.target.value as FileStorage);
        }
      }}
      value={selectedFileStorage}
      options={[
        { value: "Local", label: "Project Filesystem" },
        { value: "AWS", label: "AWS S3" },
      ]}
      disabled={!enableModification}
    />
    {selectedFileStorage === "Local" && (
      <StyledHelperText>
        CAI Project file system will be used for file storage.
      </StyledHelperText>
    )}
    <Form.Item
      label={"Document Bucket Name"}
      initialValue={projectConfig?.aws_config.document_bucket_name}
      name={["aws_config", "document_bucket_name"]}
      required={selectedFileStorage === "AWS"}
      tooltip="The S3 bucket where uploaded documents are stored."
      rules={[{ required: selectedFileStorage === "AWS" }]}
      hidden={selectedFileStorage !== "AWS"}
    >
      <Input
        placeholder="document-bucket-name"
        disabled={!enableModification}
      />
    </Form.Item>
    <Form.Item
      label={"Bucket Prefix"}
      initialValue={projectConfig?.aws_config.bucket_prefix}
      name={["aws_config", "bucket_prefix"]}
      tooltip="A prefix added to all S3 paths used by RAG Studio."
      hidden={selectedFileStorage !== "AWS"}
    >
      <Input placeholder="example-prefix" disabled={!enableModification} />
    </Form.Item>
    <Form.Item
      label={"Store document summaries in S3"}
      name={["summary_storage_provider"]}
      initialValue={projectConfig?.summary_storage_provider === "S3"}
      valuePropName={"checked"}
      hidden={selectedFileStorage !== "AWS"}
    >
      <Checkbox
        onChange={(e) => {
          if (e.target.value) {
            setSelectedSummaryStorage("S3");
          }
        }}
      />
    </Form.Item>
  </Flex>
);
