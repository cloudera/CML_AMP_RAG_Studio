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

import { Session } from "src/api/sessionApi.ts";
import { Badge, Button, Modal, Tooltip } from "antd";
import DocumentationIcon from "src/cuix/icons/DocumentationIcon.ts";
import { cdlAmber600, cdlBlue600, cdlGreen600 } from "src/cuix/variables.ts";
import useModal from "src/utils/useModal.ts";
import FileManagement from "pages/DataSources/ManageTab/FileManagement.tsx";
import { CheckCircleOutlined, ClockCircleOutlined } from "@ant-design/icons";
import { useGetRagDocuments } from "src/api/ragDocumentsApi.ts";
import { getCompletedIndexing } from "pages/DataSources/ManageTab/UploadedFilesHeader.tsx";

const ChatSessionDocuments = ({
  activeSession,
}: {
  activeSession?: Session;
}) => {
  const documentModal = useModal();

  const { data: ragDocuments, isFetching: ragDocumentsIsFetching } =
    useGetRagDocuments(
      activeSession?.associatedDataSourceId?.toString(),
      activeSession?.inferenceModel,
    );

  const indexingStatus = getCompletedIndexing(
    ragDocuments,
    ragDocumentsIsFetching,
  );

  if (!activeSession?.associatedDataSourceId) {
    return null;
  }
  const getCountIcon = () => {
    if (ragDocuments.length === 0 || ragDocumentsIsFetching) {
      return null;
    } else if (indexingStatus.fullyIndexed) {
      return (
        <CheckCircleOutlined style={{ color: cdlGreen600, fontSize: 10 }} />
      );
    } else {
      return (
        <ClockCircleOutlined
          style={{ fontSize: 10, color: cdlAmber600, bottom: 0 }}
        />
      );
    }
  };

  return (
    <>
      <Tooltip title={"Drag or add documents to chat"}>
        <Button
          size="small"
          type="text"
          onClick={() => {
            documentModal.setIsModalOpen(true);
          }}
          icon={
            // TODO: only display this badge when data source is working/pending
            <Badge size="small" status={"processing"} count={getCountIcon()}>
              <DocumentationIcon style={{ color: cdlBlue600, fontSize: 20 }} />
            </Badge>
          }
        />
      </Tooltip>
      <Modal
        title="Chat Documents"
        open={documentModal.isModalOpen}
        footer={null}
        onCancel={() => {
          documentModal.setIsModalOpen(false);
        }}
        destroyOnHidden={true}
        width={800}
      >
        <FileManagement
          simplifiedTable={true}
          summarizationModel={activeSession.inferenceModel}
          dataSourceId={activeSession.associatedDataSourceId.toString()}
        />
      </Modal>
    </>
  );
};

export default ChatSessionDocuments;
