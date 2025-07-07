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
import { Button, Modal, Tooltip } from "antd";
import DocumentationIcon from "src/cuix/icons/DocumentationIcon.ts";
import { cdlBlue600 } from "src/cuix/variables.ts";
import UploadedFilesTable from "pages/DataSources/ManageTab/UploadedFilesTable.tsx";
import useModal from "src/utils/useModal.ts";

const documentModal = useModal();

const SessionDocuments = ({ activeSession }: { activeSession?: Session }) => {
  if (!activeSession?.associatedDataSourceId) {
    return null;
  }
  return (
    <>
      <Tooltip title={"Add documents to Session"}>
        <Button
          size="small"
          type="text"
          onClick={() => {
            documentModal.setIsModalOpen(true);
          }}
          icon={<DocumentationIcon style={{ color: cdlBlue600 }} />}
        />
      </Tooltip>
      <Modal
        title="Session Documents"
        open={documentModal.isModalOpen}
        footer={null}
        onCancel={() => {
          documentModal.setIsModalOpen(false);
        }}
        destroyOnHidden={true}
        width={800}
      >
        <UploadedFilesTable
          dataSourceId={activeSession.associatedDataSourceId.toString()}
          summarizationModel={activeSession.inferenceModel}
          simplifiedTable={true}
        />
      </Modal>
    </>
  );
};

export default SessionDocuments;
