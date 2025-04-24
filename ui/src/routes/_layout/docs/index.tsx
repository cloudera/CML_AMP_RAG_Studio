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

import { createFileRoute } from "@tanstack/react-router";
import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import { Flex, Select, Typography } from "antd";
import { useState } from "react";

const metadataApiLink = "api/api-docs";
const llmServiceLink = "/llm-service/openapi.json";

const SwaggerComponent = () => {
  const [selectedSwagger, setSelectedSwagger] = useState(metadataApiLink);
  return (
    <Flex vertical align="center">
      <Flex vertical style={{ maxWidth: 1200, minWidth: 1000, marginTop: 20 }}>
        <Flex align="center" gap={8} style={{ marginLeft: 20 }}>
          <Typography.Title level={3} style={{ margin: 0 }}>
            API Service
          </Typography.Title>
          <Select
            defaultValue={selectedSwagger}
            options={[
              { label: "Metadata API", value: metadataApiLink },
              { label: "LLM Service API", value: llmServiceLink },
            ]}
            onSelect={(value) => {
              setSelectedSwagger(value);
            }}
            title="API Service"
            style={{ width: 200 }}
          />
        </Flex>
        <SwaggerUI url={selectedSwagger} />
      </Flex>
    </Flex>
  );
};

export const Route = createFileRoute("/_layout/docs/")({
  component: SwaggerComponent,
});
