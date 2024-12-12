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

import { useContext } from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { Card, Flex, Image, Typography } from "antd";
import { Link } from "@tanstack/react-router";
import SuggestedQuestionsCards from "pages/RagChatTab/ChatOutput/Placeholders/SuggestedQuestionsCards.tsx";
import { useGetDataSourceSummary } from "src/api/summaryApi.ts";
import { cdlGray700 } from "src/cuix/variables.ts";
import Images from "src/components/images/Images.ts";

const DataSourceSummaryCard = () => {
  const { activeSession } = useContext(RagChatContext);
  const dataSourceId = activeSession?.dataSourceIds[0];
  const dataSourceSummary = useGetDataSourceSummary({
    data_source_id: dataSourceId?.toString() ?? "",
    queryEnabled: true,
  });

  return (
    <Card
      style={{ width: "100%", minWidth: 300, maxWidth: 800 }}
      loading={dataSourceSummary.isLoading}
    >
      <Flex style={{ marginBottom: 16 }} gap={8}>
        <img
          src={Images.AiAssistant}
          alt="AI Assistant Icon"
          style={{ height: 24 }}
        />
        <Typography.Title
          level={5}
          style={{ fontWeight: 500, color: cdlGray700, margin: 0 }}
        >
          Knowledge Base Summary
        </Typography.Title>
      </Flex>
      <Typography.Text>
        {dataSourceSummary.data ?? (
          <Typography.Text italic>No summary available</Typography.Text>
        )}
      </Typography.Text>
    </Card>
  );
};

const EmptyChatState = ({ dataSourceSize }: { dataSourceSize: number }) => {
  const { activeSession } = useContext(RagChatContext);
  const dataSourceId = activeSession?.dataSourceIds[0];

  return (
    <Flex vertical align="center" style={{ height: "100%" }}>
      <Image
        src={Images.BrandTalking}
        alt="Brand Talking"
        style={{ width: 80 }}
        preview={false}
      />
      <Typography.Title
        level={3}
        style={{
          padding: 16,
          textAlign: "center",
          width: "80%",
          fontWeight: "lighter",
          margin: 0,
        }}
      >
        Got a question? Dive in and ask away!
      </Typography.Title>
      {dataSourceSize > 0 ? (
        <Flex vertical gap={16}>
          <DataSourceSummaryCard />
          <Typography.Text type={"secondary"}>
            Suggested Questions
          </Typography.Text>
          <SuggestedQuestionsCards />
          <div style={{ height: 30 }} />
        </Flex>
      ) : (
        <Typography.Text
          style={{ padding: 10, textAlign: "center", width: "80%" }}
        >
          In order to get started,&nbsp;
          <Link
            to={"/data/$dataSourceId"}
            params={{ dataSourceId: dataSourceId?.toString() ?? "" }}
          >
            add documents
          </Link>{" "}
          to the selected knowledge base.
        </Typography.Text>
      )}
    </Flex>
  );
};

export default EmptyChatState;
