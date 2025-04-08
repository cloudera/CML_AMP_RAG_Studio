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
import { Flex, Form, Input, Radio, Switch } from "antd";
import { ProjectConfig, useGetAmpConfig } from "src/api/ampMetadataApi.ts";
import { useState } from "react";

const SettingsPage = () => {
  const [form] = Form.useForm<ProjectConfig>();
  const { data: projectConfig } = useGetAmpConfig();
  const [modelProvider, setModelProvider] = useState("CAII");
  console.log(projectConfig);
  return (
    <Flex>
      <Form form={form}>
        <Form.Item
          label="Enhanced PDF Processing"
          name={["use_enhanced_pdf_processing"]}
          initialValue={projectConfig?.use_enhanced_pdf_processing}
          valuePropName="checked"
          tooltip={
            "Enable enhanced PDF processing for enhanced PDF processing."
          }
        >
          <Switch checkedChildren="ENHANCE" />
        </Form.Item>
        <Radio.Group
          onChange={(e) => {
            if (e.target.value) {
              setModelProvider(e.target.value as string);
            }
          }}
          value={modelProvider}
          options={[
            { value: "CAII", label: "CAII" },
            { value: "Bedrock", label: "AWS Bedrock" },
            { value: "Azure", label: "Azure OpenAI" },
          ]}
        />
        {modelProvider === "CAII" && (
          <>
            <Form.Item
              label={"CAII Domain"}
              initialValue={projectConfig?.caii_config?.caii_domain}
              name={["caii_config", "caii_domain"]}
              required
              tooltip="Domain for CAII"
            >
              <Input placeholder="CAII Domain" />
            </Form.Item>
            <Form.Item
              label={"CDP Token Override"}
              initialValue={projectConfig?.caii_config.cdp_token_override}
              name="cdp_token_override"
              required
              tooltip="Token override for CDP"
            >
              <Input placeholder="CDP Token Override" />
            </Form.Item>
          </>
        )}
        {modelProvider === "Bedrock" && (
          <>
            <Form.Item
              label={"AWS Region"}
              initialValue={projectConfig?.aws_config.region}
              name="region"
              required
              tooltip="AWS Region"
            >
              <Input placeholder="AWS Region" />
            </Form.Item>
            <Form.Item
              label={"Document Bucket Name"}
              initialValue={projectConfig?.aws_config.document_bucket_name}
              name="document_bucket_name"
              required
              tooltip="Document Bucket Name"
            >
              <Input placeholder="Document Bucket Name" />
            </Form.Item>
            <Form.Item
              label={"Bucket Prefix"}
              initialValue={projectConfig?.aws_config.bucket_prefix}
              name="bucket_prefix"
              required
              tooltip="Bucket Prefix"
            >
              <Input placeholder="Bucket Prefix" />
            </Form.Item>
            <Form.Item
              label={"Access Key ID"}
              initialValue={projectConfig?.aws_config.access_key_id}
              name="access_key_id"
              required
              tooltip="Access Key ID"
            >
              <Input placeholder="Access Key ID" />
            </Form.Item>
            <Form.Item
              label={"Secret Access Key"}
              initialValue={projectConfig?.aws_config.secret_access_key}
              name="secret_access_key"
              required
              tooltip="Secret Access Key"
            >
              <Input placeholder="Secret Access Key" />
            </Form.Item>
          </>
        )}
        {modelProvider === "Azure" && (
          <>
            <Form.Item
              label={"Azure OpenAI Endpoint"}
              initialValue={projectConfig?.azure_config.openai_endpoint}
              name="openai_endpoint"
              required
            >
              <Input placeholder="Azure OpenAI Endpoint" />
            </Form.Item>
            <Form.Item
              label={"Azure OpenAI Key"}
              initialValue={projectConfig?.azure_config.openai_key}
              name="openai_key"
              required
            >
              <Input placeholder="Azure OpenAI Key" />
            </Form.Item>
            <Form.Item
              label={"API Version"}
              initialValue={projectConfig?.azure_config.openai_api_version}
              name="openai_model"
              required
            >
              <Input placeholder="API Version" />
            </Form.Item>
          </>
        )}
      </Form>
    </Flex>
  );
};

export default SettingsPage;
