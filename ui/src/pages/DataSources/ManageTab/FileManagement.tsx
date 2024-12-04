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

import React, { useState } from "react";
import { Button, Divider, Flex, Upload, UploadFile, UploadProps } from "antd";
import { QueryKeys } from "src/api/utils.ts";
import { InboxOutlined } from "@ant-design/icons";
import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import UploadedFilesTable from "pages/DataSources/ManageTab/UploadedFilesTable.tsx";
import { useCreateRagDocumentsMutation } from "src/api/ragDocumentsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";

const DragAndDrop = () => {
  return (
    <div style={{ width: 400 }}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <div className="ant-upload-text">Drag and drop or click to upload.</div>
    </div>
  );
};

const isFulfilled = <T,>(
  p: PromiseSettledResult<T>,
): p is PromiseFulfilledResult<T> => p.status === "fulfilled";
const isRejected = <T,>(
  p: PromiseSettledResult<T>,
): p is PromiseRejectedResult => p.status === "rejected";

interface RejectReasonType {
  message: string;
}

const FileManagement: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const queryClient = useQueryClient();
  const dataSourceId = useParams({
    from: "/_layout/data/_layout-datasources/$dataSourceId",
  }).dataSourceId;
  const ragDocumentMutation = useCreateRagDocumentsMutation({
    onSuccess: (settledPromises) => {
      const fulfilledValues = settledPromises
        .filter(isFulfilled)
        .map((p) => p.value).length;
      const rejectedReasons = settledPromises
        .filter(isRejected)
        .map((p) => p.reason as RejectReasonType);

      rejectedReasons.forEach((reason: RejectReasonType) => {
        messageQueue.error(reason.message);
      });

      setFileList([]);
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.getRagDocuments],
      });

      if (fulfilledValues > 0) {
        messageQueue.success(
          `Uploaded ${fulfilledValues.toString()} document${fulfilledValues > 1 ? "s" : ""} successfully.`,
        );
      }
    },
    onError: () => {
      messageQueue.error("upload failed.");
    },
  });

  const handleUpload = () => {
    ragDocumentMutation.mutate({ files: fileList, dataSourceId });
  };

  const props: UploadProps = {
    onRemove: (file) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (_, newFileLIst) => {
      setFileList([...fileList, ...newFileLIst]);
      return false;
    },
    fileList,
  };

  return (
    <Flex vertical style={{ marginTop: 50 }}>
      <Flex
        vertical
        align="center"
        style={{ maxWidth: 300, alignSelf: "center" }}
      >
        <Upload.Dragger
          {...props}
          multiple
          itemRender={(originNode) => {
            return <div style={{ width: 432 }}>{originNode}</div>;
          }}
        >
          <DragAndDrop />
        </Upload.Dragger>
        <Button
          type="primary"
          onClick={handleUpload}
          disabled={fileList.length === 0}
          loading={ragDocumentMutation.isPending}
          style={{ marginTop: 16 }}
        >
          {ragDocumentMutation.isPending ? "Uploading" : "Start Upload"}
        </Button>
      </Flex>
      <Divider />
      <UploadedFilesTable />
    </Flex>
  );
};

export default FileManagement;
