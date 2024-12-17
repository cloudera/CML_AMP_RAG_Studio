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

import {
  Button,
  Flex,
  Modal,
  Popover,
  Table,
  TableProps,
  Tooltip,
  Typography,
} from "antd";
import Icon, {
  CheckCircleOutlined,
  DeleteOutlined,
  LoadingOutlined,
  MinusCircleOutlined,
} from "@ant-design/icons";
import {
  RagDocumentResponseType,
  useDeleteDocumentMutation,
  useGetRagDocuments,
} from "src/api/ragDocumentsApi.ts";
import { bytesConversion } from "src/utils/bytesConversion.ts";
import UploadedFilesHeader from "pages/DataSources/ManageTab/UploadedFilesHeader.tsx";
import AiAssistantIcon from "src/cuix/icons/AiAssistantIcon";
import DocumentationIcon from "src/cuix/icons/DocumentationIcon";
import { useGetDocumentSummary } from "src/api/summaryApi.ts";
import { useContext, useState } from "react";
import messageQueue from "src/utils/messageQueue.ts";
import { useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "src/api/utils.ts";
import useModal from "src/utils/useModal.ts";
import { cdlWhite } from "src/cuix/variables.ts";
import { DataSourceContext } from "pages/DataSources/Layout.tsx";

const ReadyColumn = ({ file }: { file: RagDocumentResponseType }) => {
  return file.vectorUploadTimestamp == null ? (
    <LoadingOutlined spin />
  ) : (
    <CheckCircleOutlined />
  );
};

function SummaryPopover({
  dataSourceId,
  timestamp,
  docId,
}: {
  dataSourceId: string;
  timestamp: number | null;
  docId: string;
}) {
  const [visible, setVisible] = useState(false);
  const documentSummary = useGetDocumentSummary({
    data_source_id: dataSourceId,
    doc_id: docId,
    queryEnabled: timestamp != null && visible,
  });

  return (
    <Popover
      title="Generated summary"
      content={<div style={{ width: 400 }}>{documentSummary.data}</div>}
      open={visible && documentSummary.isSuccess}
      onOpenChange={setVisible}
    >
      <Icon component={DocumentationIcon} style={{ fontSize: 20 }} />
    </Popover>
  );
}

const columns = (
  dataSourceId: string,
  handleDeleteFile: (document: RagDocumentResponseType) => void,
  summarizationModel?: string,
): TableProps<RagDocumentResponseType>["columns"] => [
  {
    title: (
      <Tooltip
        title={
          <Flex vertical gap={4}>
            <Typography.Text style={{ color: cdlWhite }}>
              Document Summary
            </Typography.Text>
            <Typography.Text style={{ fontSize: 10, color: cdlWhite }}>
              Note: Document summarization requires a summarization model to be
              selected.
            </Typography.Text>
            <Typography.Text style={{ fontSize: 10, color: cdlWhite }}>
              Document summarization can take a significant amount of time, but
              will not impact the ability to use the document for Chat.
            </Typography.Text>
          </Flex>
        }
      >
        <Icon component={AiAssistantIcon} style={{ fontSize: 20 }} />
      </Tooltip>
    ),
    dataIndex: "summaryCreationTimestamp",
    key: "summaryCreationTimestamp",
    render: (
      timestamp: RagDocumentResponseType["summaryCreationTimestamp"],
      data,
    ) => {
      if (timestamp) {
        return (
          <SummaryPopover
            dataSourceId={dataSourceId}
            docId={data.documentId}
            timestamp={timestamp}
          />
        );
      }

      if (!summarizationModel) {
        return (
          <Popover
            title={"No summary available"}
            content={"A summarization model must be selected."}
          >
            <MinusCircleOutlined style={{ fontSize: 16 }} />
          </Popover>
        );
      }

      return <LoadingOutlined spin />;
    },
  },
  {
    title: "Filename",
    dataIndex: "filename",
    key: "filename",
    showSorterTooltip: false,
    sorter: (a, b) => a.filename.localeCompare(b.filename),
  },
  {
    title: "Size",
    dataIndex: "sizeInBytes",
    key: "sizeInBytes",
    render: (sizeInBytes: RagDocumentResponseType["sizeInBytes"]) =>
      bytesConversion(sizeInBytes.toString()),
  },
  {
    title: "Extension",
    dataIndex: "extension",
    key: "extension",
  },
  {
    title: "Creation date",
    dataIndex: "timeCreated",
    key: "timeCreated",
    showSorterTooltip: false,
    sorter: (a, b) => {
      return a.timeCreated - b.timeCreated;
    },
    defaultSortOrder: "descend",
    render: (timestamp) => new Date(timestamp * 1000).toLocaleString(),
  },
  {
    title: <Tooltip title="Document indexing complete">Ready</Tooltip>,
    dataIndex: "vectorUploadTimestamp",
    key: "vectorUploadTimestamp",
    render: (_, file: RagDocumentResponseType) => <ReadyColumn file={file} />,
  },
  {
    title: "Actions",
    render: (_, record) => {
      return (
        <Button
          type="text"
          icon={<DeleteOutlined />}
          onClick={() => {
            handleDeleteFile(record);
          }}
        />
      );
    },
  },
];

const UploadedFilesTable = () => {
  const { dataSourceId, dataSourceMetaData } = useContext(DataSourceContext);
  const [selectedDocument, setSelectedDocument] =
    useState<RagDocumentResponseType>();
  const deleteConfirmationModal = useModal();
  const queryClient = useQueryClient();
  const getRagDocuments = useGetRagDocuments(
    dataSourceId,
    dataSourceMetaData?.summarizationModel,
  );
  const deleteDocumentMutation = useDeleteDocumentMutation({
    onSuccess: () => {
      messageQueue.success("Document deleted successfully");
      deleteConfirmationModal.setIsModalOpen(false);
      setSelectedDocument(undefined);
      queryClient
        .invalidateQueries({
          queryKey: [QueryKeys.getRagDocuments, { dataSourceId }],
        })
        .catch(() => {
          messageQueue.error("Failed to refresh document list");
        });
    },
    onError: () => {
      messageQueue.error("Failed to delete document");
    },
  });
  const ragDocuments = getRagDocuments.data
    ? getRagDocuments.data.map((doc) => ({ ...doc, key: doc.id }))
    : [];
  const docsLoading = getRagDocuments.isLoading || getRagDocuments.isPending;

  const handleDeleteFile = () => {
    if (!selectedDocument) {
      return null;
    }

    deleteDocumentMutation.mutate({
      id: selectedDocument.id,
      dataSourceId: selectedDocument.dataSourceId.toString(),
    });
  };

  const handleDeleteFileModal = (document: RagDocumentResponseType) => {
    setSelectedDocument(document);
    deleteConfirmationModal.setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    deleteConfirmationModal.setIsModalOpen(false);
    setSelectedDocument(undefined);
  };

  return (
    <>
      <UploadedFilesHeader
        ragDocuments={ragDocuments}
        docsLoading={docsLoading}
      />
      <Table<RagDocumentResponseType>
        loading={docsLoading}
        dataSource={ragDocuments}
        columns={columns(
          dataSourceId,
          handleDeleteFileModal,
          dataSourceMetaData?.summarizationModel,
        )}
      />
      <Modal
        title="Delete document?"
        open={deleteConfirmationModal.isModalOpen}
        onOk={handleDeleteFile}
        okText={"Yes, delete"}
        loading={deleteDocumentMutation.isPending}
        okButtonProps={{
          danger: true,
        }}
        onCancel={handleCloseModal}
      >
        <Flex style={{ marginTop: 20 }} vertical gap={16}>
          <Typography.Text italic>{selectedDocument?.filename}</Typography.Text>
        </Flex>
      </Modal>
    </>
  );
};

export default UploadedFilesTable;
