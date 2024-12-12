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
 * Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
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

import { useMutation } from "@tanstack/react-query";
import { MutationKeys } from "src/api/utils.ts";
import { getCdfConfigQuery } from "src/api/dataSourceApi.ts";
import { useContext, useEffect } from "react";
import { downloadObjectAsJson } from "src/utils/convertJsonToFile.ts";
import { Button, Card, Flex, Typography } from "antd";
import { CheckCircleOutlined } from "@ant-design/icons";
import { DataSourceContext } from "pages/DataSources/Layout.tsx";

export const ClouderaDataFlowConnection = () => {
  const { dataSourceId } = useContext(DataSourceContext);
  const {
    data,
    isPending,
    mutate: fetchCdfConfigQuery,
    isSuccess,
  } = useMutation({
    mutationKey: [MutationKeys.getCdfConfig],
    mutationFn: () => getCdfConfigQuery(dataSourceId),
    gcTime: 0,
  });

  useEffect(() => {
    if (data) {
      downloadObjectAsJson(
        data,
        `cdf-flow-definition-datasource-${dataSourceId}`,
      );
    }
  }, [data]);

  return (
    <Card title={"Cloudera DataFlow from S3"}>
      <Flex vertical gap={20}>
        <Typography.Text type="secondary">
          Download flow definition to be imported into Cloudera DataFlow
        </Typography.Text>
        <Flex gap={20}>
          <Button
            loading={isPending}
            type="primary"
            onClick={() => {
              fetchCdfConfigQuery();
            }}
          >
            Download
          </Button>
          {isSuccess ? (
            <CheckCircleOutlined style={{ fontSize: 20, color: "#4CCF4C" }} />
          ) : null}
        </Flex>
      </Flex>
    </Card>
  );
};
