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

import Icon, { DownloadOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
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
import "../tableMarkdown.css";
import ChunkContainer from "pages/RagChatTab/ChatOutput/Sources/ChunkContainer.tsx";
import { paths, ragPath } from "src/api/utils.ts";
import { downloadFile } from "src/utils/downloadFile.ts";

const CardTitle = ({ source }: { source: SourceNode }) => {
  const handleDownloadFile = () => {
    if (!source.dataSourceId) {
      return;
    }
    const url = `${ragPath}/${paths.dataSources}/${source.dataSourceId.toString()}/${paths.files}/${source.doc_id}/download`;
    void downloadFile(url, source.source_file_name);
  };

  return (
    <Flex justify="space-between" align="center" gap={8}>
      {source.dataSourceId ? (
        <Tooltip title="Download source file">
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={handleDownloadFile}
          />
        </Tooltip>
      ) : null}
      <Tooltip title={source.source_file_name}>
        <Typography.Paragraph ellipsis style={{ width: "100%", margin: 0 }}>
          {source.source_file_name}
        </Typography.Paragraph>
      </Tooltip>
      <Typography.Text style={{ color: cdlGray600 }}>
        Score: {source.score.toFixed(2)}
      </Typography.Text>
    </Flex>
  );
};

const getTag = (source: SourceNode, index?: number) => {
  return (
    <Tag
      style={{
        borderRadius: 20,
        height: 24,
        minWidth: 24,
        cursor: "pointer",
        margin: 0,
        marginLeft: 4,
        bottom: 2,
      }}
    >
      <Flex
        style={{ height: "100%", width: "100%" }}
        justify="center"
        align="center"
      >
        <Typography.Paragraph
          ellipsis={{
            rows: 1,
            expandable: false,
            tooltip: source.source_file_name,
          }}
          style={{ margin: 0, padding: 0, fontSize: index ? 10 : 12 }}
        >
          {!index && (
            <Icon component={DocumentationIcon} style={{ marginRight: 8 }} />
          )}
          {index ?? source.source_file_name}
        </Typography.Paragraph>
      </Flex>
    </Tag>
  );
};

export const SourceCard = ({
  source,
  index,
}: {
  source: SourceNode;
  index?: number;
}) => {
  const { activeSession } = useContext(RagChatContext);
  const [showContent, setShowContent] = useState(false);
  const { dataSourceId: nodeDataSourceId } = source;
  // Older chats did not store dataSourceId.  Need to check activeSession for legacy chats only.
  const dataSourceId = nodeDataSourceId ?? activeSession?.dataSourceIds[0];
  const chunkContents = useGetChunkContents();
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
          title={<CardTitle source={source} />}
          variant="borderless"
          style={{
            width: 800,
            height: 600,
            overflowY: "auto",
            maxWidth: "100%",
            maxHeight: "100%",
          }}
        >
          <Flex justify="center" vertical>
            {chunkContents.isError ? (
              <Alert
                message="Error: Could not fetch source node contents"
                type="error"
                showIcon
              />
            ) : null}
            <ChunkContainer chunkContents={chunkContents} />
            <Card
              title={"Generated document summary"}
              type="inner"
              style={{ marginTop: 16 }}
            >
              <Typography.Paragraph
                ellipsis={
                  documentSummary.isLoading
                    ? false
                    : {
                        rows: 2,
                        expandable: true,
                      }
                }
              >
                {documentSummary.isLoading ? (
                  <Flex align="center" justify="center" vertical gap={20}>
                    <div>
                      <Spin />
                    </div>
                  </Flex>
                ) : (
                  (documentSummary.data ?? "No summary available")
                )}
              </Typography.Paragraph>
            </Card>
          </Flex>
        </Card>
      }
    >
      {getTag(source, index)}
    </Popover>
  );
};
