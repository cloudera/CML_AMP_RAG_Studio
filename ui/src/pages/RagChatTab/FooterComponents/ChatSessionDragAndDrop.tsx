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

import {
  DragEvent as ReactDragEvent,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { useCreateRagDocumentsMutation } from "src/api/ragDocumentsApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { Upload } from "antd";
import { QueryKeys } from "src/api/utils.ts";
import { useQueryClient } from "@tanstack/react-query";
import {
  DragAndDrop,
  isFulfilled,
  isRejected,
  RejectReasonType,
} from "pages/DataSources/ManageTab/fileManagementUtils.tsx";
import useCreateSessionAndRedirect from "pages/RagChatTab/ChatOutput/hooks/useCreateSessionAndRedirect.tsx";
import { Session } from "src/api/sessionApi.ts";

export const ChatSessionDragAndDrop = () => {
  const { activeSession } = useContext(RagChatContext);
  const [isDragging, setIsDragging] = useState(false);
  const queryClient = useQueryClient();
  // Counter to track nested dragenter/dragleave events
  const dragCounter = useRef(0);
  const [filesToUpload, setFilesToUpload] = useState<FileList>();
  const onSuccess = (session: Session) => {
    const files = [];
    if (!filesToUpload || filesToUpload.length === 0) {
      return;
    }
    for (const file of filesToUpload) {
      files.push(file);
    }
    if (session.associatedDataSourceId) {
      ragDocumentMutation.mutate({
        files: files,
        dataSourceId: session.associatedDataSourceId.toString(),
      });
    }
  };
  const createSessionAndRedirect = useCreateSessionAndRedirect(onSuccess);
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

      queryClient
        .invalidateQueries({
          queryKey: [QueryKeys.getRagDocuments],
        })
        .catch(() => null);

      queryClient
        .invalidateQueries({
          queryKey: [
            QueryKeys.getDataSourceById,
            { dataSourceId: activeSession?.associatedDataSourceId },
          ],
        })
        .catch(() => null);

      if (fulfilledValues > 0) {
        messageQueue.success(
          `Uploaded ${fulfilledValues.toString()} document${fulfilledValues > 1 ? "s" : ""} successfully.`,
        );
      }
    },
    onError: (error) => {
      messageQueue.error(`Failed to upload documents: ${error.message}`);
    },
  });

  useEffect(() => {
    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
    };

    const handleDragEnter = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current++;
      if (e.dataTransfer?.items && e.dataTransfer.items.length > 0) {
        setIsDragging(true);
      }
    };

    const handleDragLeave = (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current--;
      if (dragCounter.current === 0) {
        setIsDragging(false);
      }
    };

    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      dragCounter.current = 0;
    };

    window.addEventListener("dragenter", handleDragEnter);
    window.addEventListener("dragleave", handleDragLeave);
    window.addEventListener("dragover", handleDragOver);
    window.addEventListener("drop", handleDrop);

    return () => {
      window.removeEventListener("dragenter", handleDragEnter);
      window.removeEventListener("dragleave", handleDragLeave);
      window.removeEventListener("dragover", handleDragOver);
      window.removeEventListener("drop", handleDrop);
    };
  }, []);

  const handleDrop = (e: ReactDragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;
    if (!activeSession) {
      setFilesToUpload(e.dataTransfer.files);
      e.dataTransfer.clearData();
      createSessionAndRedirect([]);
    }
    if (
      e.dataTransfer.files.length > 0 &&
      activeSession?.associatedDataSourceId
    ) {
      const files = [];
      for (const file of e.dataTransfer.files) {
        files.push(file);
      }
      ragDocumentMutation.mutate({
        files: files,
        dataSourceId: activeSession.associatedDataSourceId.toString(),
      });
      e.dataTransfer.clearData();
    }
  };

  if (!isDragging) {
    return null;
  }
  return (
    <Upload.Dragger onDrop={handleDrop} showUploadList={false}>
      <DragAndDrop
        helpText={"Drag and drop to upload documents to the chat session."}
      />
    </Upload.Dragger>
  );
};
