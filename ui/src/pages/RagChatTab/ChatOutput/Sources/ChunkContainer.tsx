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

import { Flex, List, Spin, Typography } from "antd";
import {
  ChunkContentsRequest,
  ChunkContentsResponse,
} from "src/api/ragQueryApi";
import Markdown from "react-markdown";
import Remark from "remark-gfm";
import { UseMutationResult } from "@tanstack/react-query";
import MetaData from "pages/RagChatTab/ChatOutput/Sources/MetaData.tsx";

const TextRenderer = ({ text }: { text: string }) => {
  return (
    <Typography.Paragraph style={{ textAlign: "left", whiteSpace: "pre-wrap" }}>
      {text}
    </Typography.Paragraph>
  );
};

const ChunkContents = ({ data }: { data: ChunkContentsResponse }) => {
  if (data.metadata.chunk_format === "markdown") {
    return (
      <div style={{ marginBottom: 12 }} className="styled-markdown">
        <Markdown skipHtml remarkPlugins={[Remark]}>
          {data.text}
        </Markdown>
      </div>
    );
  }

  if (data.metadata.chunk_format === "json") {
    try {
      const jsonData = JSON.parse(data.text) as Record<string, unknown>;

      const formattedData = Object.keys(jsonData).map((key) => ({
        title: key,
        content: String(jsonData[key]) || "",
      }));

      return (
        <List
          itemLayout="horizontal"
          dataSource={formattedData}
          renderItem={(item, index) => {
            return (
              <List.Item key={index}>
                <List.Item.Meta
                  title={item.title}
                  description={
                    <Typography.Text>{item.content}</Typography.Text>
                  }
                />
              </List.Item>
            );
          }}
        />
      );
    } catch (e: unknown) {
      console.error("Error parsing JSON data", e);
      return <TextRenderer text={data.text} />;
    }
  }

  return <TextRenderer text={data.text} />;
};

const ChunkContainer = ({
  chunkContents,
}: {
  chunkContents: UseMutationResult<
    ChunkContentsResponse,
    Error,
    ChunkContentsRequest
  >;
}) => {
  if (chunkContents.isPending) {
    return (
      <Flex align="center" justify="center" vertical gap={20}>
        <Typography.Text type="secondary">
          Fetching source contents
        </Typography.Text>
        <div>
          <Spin />
        </div>
      </Flex>
    );
  }
  if (!chunkContents.data) {
    return null;
  }
  return (
    <Flex vertical gap={16}>
      <ChunkContents data={chunkContents.data} />
      <MetaData metadata={chunkContents.data.metadata} />
    </Flex>
  );
};

export default ChunkContainer;
