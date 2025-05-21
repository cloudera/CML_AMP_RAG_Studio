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
  createFileRoute,
  ErrorComponent,
  ErrorComponentProps,
  useNavigate,
} from "@tanstack/react-router";
import { getSessionsQueryOptions } from "src/api/sessionApi.ts";
import {
  getLlmModelsQueryOptions,
  useGetModelSource,
} from "src/api/modelsApi.ts";
import { getDefaultProjectQueryOptions } from "src/api/projectsApi.ts";
import { ApiError } from "src/api/utils.ts";
import { Button, Card, Flex, Typography } from "antd";
import messageQueue from "src/utils/messageQueue.ts";
import { WarningOutlined } from "@ant-design/icons";

export const getErrorComponent = (error: ErrorComponentProps) => {
  const modelSource = useGetModelSource();
  const navigate = useNavigate();
  if (
    error.error instanceof ApiError &&
    error.error.status === 401 &&
    modelSource.data === "CAII"
  ) {
    return (
      <Flex
        align={"center"}
        justify={"center"}
        style={{ height: "100%", width: "100%" }}
      >
        <Card
          title={
            <Typography.Text type="danger">
              <WarningOutlined style={{ marginRight: 8 }} />
              Invalid or missing CDP token
            </Typography.Text>
          }
          style={{
            width: "100%",
            maxWidth: 600,
          }}
        >
          <Flex vertical gap={16}>
            <Typography.Text italic>
              Provide a valid CDP token on the Settings page to use Cloudera AI
              Inference
            </Typography.Text>
            <Flex gap={8}>
              <Button
                type="default"
                onClick={() => {
                  navigate({
                    to: "/settings",
                    hash: "modelConfiguration",
                  }).catch(() => {
                    messageQueue.error("Error occurred navigating to settings");
                  });
                }}
              >
                Settings
              </Button>
            </Flex>
          </Flex>
        </Card>
      </Flex>
    );
  }

  return <ErrorComponent error={error} />;
};
export const Route = createFileRoute("/_layout/chats/_layout-chats/")({
  loader: async ({ context }) =>
    await Promise.all([
      context.queryClient.ensureQueryData(getSessionsQueryOptions),
      context.queryClient.ensureQueryData(getDefaultProjectQueryOptions),
      context.queryClient.ensureQueryData(getLlmModelsQueryOptions),
    ]),
  errorComponent: getErrorComponent,
});
