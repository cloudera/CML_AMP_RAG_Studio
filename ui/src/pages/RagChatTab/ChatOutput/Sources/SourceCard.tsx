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

import Icon from "@ant-design/icons";
import {
  Alert,
  Card,
  Flex,
  Popover,
  Spin,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { useContext, useState } from "react";
import { SourceNode } from "src/api/chatApi.ts";
import { useGetChunkContents } from "src/api/ragQueryApi.ts";
import { useGetDocumentSummary } from "src/api/summaryApi.ts";
import DocumentationIcon from "src/cuix/icons/DocumentationIcon";
import { cdlGray600 } from "src/cuix/variables.ts";
import MetaData from "pages/RagChatTab/ChatOutput/Sources/MetaData.tsx";
import Markdown from "react-markdown";
import Remark from "remark-gfm";
import "./sourceCard.css";

export const SourceCard = ({ source }: { source: SourceNode }) => {
  const { activeSession } = useContext(RagChatContext);
  const [showContent, setShowContent] = useState(false);
  const chunkContents = useGetChunkContents();
  const dataSourceId = activeSession?.dataSourceIds[0];
  const documentSummary = useGetDocumentSummary({
    data_source_id: dataSourceId?.toString() ?? "",
    doc_id: source.doc_id,
    queryEnabled: showContent,
  });

  const handleGetChunkContents = () => {
    if (dataSourceId && !showContent) {
      chunkContents.mutate({
        data_source_id: dataSourceId.toString(),
        chunk_id: source.node_id,
      });
    }
    setShowContent(true);
  };

  return (
    <Popover
      trigger="click"
      onOpenChange={handleGetChunkContents}
      content={
        <Card
          title={
            <Flex justify="space-between">
              <Tooltip title={source.source_file_name}>
                <Typography.Paragraph ellipsis style={{ width: "70%" }}>
                  {source.source_file_name}
                </Typography.Paragraph>
              </Tooltip>
              <Typography.Text style={{ color: cdlGray600 }}>
                Score: {source.score}
              </Typography.Text>
            </Flex>
          }
          bordered={false}
          style={{ width: 600, height: 300, overflowY: "auto" }}
        >
          <Flex justify="center" vertical>
            <Flex vertical>
              <Typography.Title level={5} style={{ marginTop: 10 }}>
                Generated document summary
              </Typography.Title>
              <Typography.Text>
                {documentSummary.data ?? "No summary available"}
              </Typography.Text>
            </Flex>
            {chunkContents.isError ? (
              <Alert
                message="Error: Could not fetch source node contents"
                type="error"
                showIcon
              />
            ) : null}
            {chunkContents.isPending ? (
              <Flex align="center" justify="center" vertical gap={20}>
                <Typography.Text type="secondary">
                  Fetching source contents
                </Typography.Text>
                <div>
                  <Spin />
                </div>
              </Flex>
            ) : (
              chunkContents.data && (
                <Flex vertical>
                  <Typography.Title level={5} style={{ marginTop: 10 }}>
                    Extracted reference content
                  </Typography.Title>
                  {chunkContents.data.metadata.chunk_format === "markdown" ? (
                    <div
                      style={{ marginBottom: 12 }}
                      className="styled-markdown"
                    >
                      <Markdown skipHtml remarkPlugins={[Remark]}>
                        {chunkContents.data.text}
                      </Markdown>
                    </div>
                  ) : (
                    <Typography.Paragraph
                      style={{ textAlign: "left", whiteSpace: "pre-wrap" }}
                    >
                      chunkContents.data.text
                    </Typography.Paragraph>
                  )}
                  <MetaData metadata={chunkContents.data.metadata} />
                </Flex>
              )
            )}
          </Flex>
        </Card>
      }
    >
      <Tag
        style={{ width: 180, borderRadius: 20, height: 24, cursor: "pointer" }}
      >
        <Flex style={{ height: "100%" }} justify="center" align="center">
          <Typography.Paragraph
            ellipsis={{
              rows: 1,
              expandable: false,
              tooltip: source.source_file_name,
            }}
            style={{ margin: 0, fontSize: 12 }}
          >
            <Icon component={DocumentationIcon} style={{ marginRight: 8 }} />
            {source.source_file_name}
          </Typography.Paragraph>
        </Flex>
      </Tag>
    </Popover>
  );
};
