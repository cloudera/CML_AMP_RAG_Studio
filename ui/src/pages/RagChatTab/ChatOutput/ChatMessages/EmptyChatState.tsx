/*
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2025
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
 */

import { Alert, Button, Image, Typography } from "antd";
import Images from "src/components/images/Images.ts";
import SuggestedQuestionsCards from "pages/RagChatTab/ChatOutput/Placeholders/SuggestedQuestionsCards.tsx";
import NoDataSourcesState from "pages/RagChatTab/ChatOutput/Placeholders/NoDataSourcesState.tsx";
import { useGetLlmModels } from "src/api/modelsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { useNavigate } from "@tanstack/react-router";

const EmptyChatState = () => {
  const { data: llmModels, isSuccess } = useGetLlmModels();
  const navigate = useNavigate();

  return (
    <>
      {isSuccess && llmModels.length === 0 ? (
        <Alert
          type="warning"
          showIcon
          message={"One inference model must be available to chat"}
          action={
            <Button
              style={{ marginLeft: 12 }}
              onClick={() => {
                navigate({
                  to: "/settings",
                  hash: "modelConfiguration",
                }).catch(() => {
                  messageQueue.error("Failed to navigate to models page");
                });
              }}
            >
              Model Config
            </Button>
          }
        />
      ) : null}
      <Image
        src={Images.BrandTalking}
        alt="Machines Chatting"
        style={{ width: 80 }}
        preview={false}
      />
      <Typography.Title level={4} style={{ fontWeight: 300, margin: 0 }}>
        Welcome to RAG Studio
      </Typography.Title>
      <SuggestedQuestionsCards />
      <NoDataSourcesState />
    </>
  );
};

export default EmptyChatState;
