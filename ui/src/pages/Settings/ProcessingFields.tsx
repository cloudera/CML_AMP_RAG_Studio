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
import { Flex, Form, Switch } from "antd";

export const ProcessingFields = ({
  projectConfig,
}: {
  projectConfig?: ProjectConfig | null;
}) => {
  return (
    <Flex vertical style={{ maxWidth: 600 }}>
      <Form.Item
        label="Enhanced PDF Processing"
        name={["use_enhanced_pdf_processing"]}
        initialValue={projectConfig?.use_enhanced_pdf_processing}
        valuePropName="checked"
        tooltip={
          "Use enhanced PDF processing for better text extraction. This option makes PDF parsing take significantly longer. A GPU and at least 16GB of RAM is required for this option."
        }
        validateTrigger="onChange"
        rules={[
          ({ getFieldValue }) => ({
            validator() {
              if (
                projectConfig &&
                (projectConfig.application_config.num_of_gpus === 0 ||
                  projectConfig.application_config.memory_size_gb < 16) &&
                getFieldValue("use_enhanced_pdf_processing")
              ) {
                return Promise.reject(
                  new Error(
                    "Insufficient resources available for enhanced PDF processing. Please make sure you have at least 16GB of RAM and a GPU available.  Failure to do so may crash the application.",
                  ),
                );
              }
              return Promise.resolve();
            },
          }),
        ]}
      >
        <Switch />
      </Form.Item>
    </Flex>
  );
};
