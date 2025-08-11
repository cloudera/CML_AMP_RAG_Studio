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

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  commonHeaders,
  deleteRequest,
  getRequest,
  MutationKeys,
  paths,
  QueryKeys,
  ragPath,
  UseMutationType,
} from "src/api/utils.ts";
import { GetProp, UploadProps } from "antd";

type FileType = Parameters<GetProp<UploadProps, "beforeUpload">>[0];

interface RagDocumentMetadata {
  fileName: string;
  documentId: string;
  extension: string;
  sizeInBytes: number;
}

export const useCreateRagDocumentsMutation = ({
  onSuccess,
  onError,
}: UseMutationType<PromiseSettledResult<RagDocumentMetadata[]>[]>) => {
  return useMutation({
    mutationKey: [MutationKeys.createRagDocuments],
    mutationFn: createRagDocumentsMutation,
    onSuccess,
    onError,
  });
};

const createRagDocumentsMutation = async ({
  files,
  dataSourceId,
}: {
  files: File[];
  dataSourceId: string;
}) => {
  const promises = files.map((file) =>
    createRagDocumentMutation(file, dataSourceId)
  );

  return Promise.allSettled(promises);
};

const createRagDocumentMutation = async (file: File, dataSourceId: string) => {
  const formData = new FormData();
  formData.append("file", file as FileType, file.name);
  return await fetch(
    `${ragPath}/${paths.dataSources}/${dataSourceId}/${paths.files}`,
    {
      method: "POST",
      body: formData,
      headers: commonHeaders,
    }
  ).then((res) => {
    if (!res.ok) {
      if (res.status === 413) {
        throw new Error(
          `File is too large. Maximum size is 100MB: ${file.name}`
        );
      }
      throw new Error(
        `Failed to call API backend. status: ${res.status.toString()} : ${res.statusText}`
      );
    }
    return res.json() as Promise<RagDocumentMetadata[]>;
  });
};

export enum RagDocumentStatus {
  QUEUED = "QUEUED",
  IN_PROGRESS = "IN_PROGRESS",
  SUCCESS = "SUCCESS",
  ERROR = "ERROR",
}

export interface RagDocumentResponseType {
  id: number;
  filename: string;
  dataSourceId: number;
  documentId: string;
  s3Path: string;
  vectorUploadTimestamp: number | null;
  sizeInBytes: number;
  extension: string;
  timeCreated: number;
  timeUpdated: number;
  createdById: number;
  updatedById: number;
  summaryCreationTimestamp: number | null;
  summaryStatus: RagDocumentStatus | null;
  summaryError: string | null;
  indexingStatus: RagDocumentStatus | null;
  indexingError: string | null;
}

export const useGetRagDocuments = (
  dataSourceId?: string,
  summarizationModel?: string
) => {
  return useQuery({
    queryKey: [QueryKeys.getRagDocuments, { dataSourceId }],
    queryFn: () => {
      if (!dataSourceId) {
        return [];
      }
      return getRagDocuments(dataSourceId).then((res) => {
        return res.map((doc) => ({ ...doc, key: doc.id }));
      });
    },
    enabled: !!dataSourceId,
    initialData: [],
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) {
        return false;
      }
      const nullTimestampDocuments = data.find(
        (file: RagDocumentResponseType) => file.vectorUploadTimestamp === null
      );

      let nullSummaryCreation = null;

      if (summarizationModel && summarizationModel.length > 0) {
        nullSummaryCreation = data.find(
          (file: RagDocumentResponseType) =>
            file.summaryCreationTimestamp === null
        );
      }

      return nullTimestampDocuments || nullSummaryCreation ? 3000 : false;
    },
  });
};

const getRagDocuments = async (
  dataSourceId: string
): Promise<RagDocumentResponseType[]> => {
  return getRequest(
    `${ragPath}/${paths.dataSources}/${dataSourceId}/${paths.files}`
  );
};

export const useDeleteDocumentMutation = ({
  onSuccess,
  onError,
}: UseMutationType<void>) => {
  return useMutation({
    mutationKey: [MutationKeys.deleteRagDocument],
    mutationFn: deleteDocumentMutation,
    onSuccess,
    onError,
  });
};

export const deleteDocumentMutation = async ({
  documentId,
  dataSourceId,
}: {
  documentId: string;
  dataSourceId: string;
}): Promise<void> => {
  await deleteRequest(
    `${ragPath}/${paths.dataSources}/${dataSourceId}/${paths.files}/${documentId}`
  );
};
