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
  MutationKeys,
  QueryKeys,
  UseMutationType
} from "src/api/utils.ts";
import { DataSourceFile } from "src/services/api/api";
import { dataSourceFilesApi } from "src/services/api_config";

export const useCreateRagDocumentsMutation = ({
  onSuccess,
  onError,
}: UseMutationType<PromiseSettledResult<DataSourceFile>[]>) => {
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
  dataSourceId: number | string;
}) => {
  const dataSourceIdNumber = typeof dataSourceId === 'string' ? parseInt(dataSourceId, 10) : dataSourceId;
  const promises = files.map((file) =>
    createRagDocumentMutation(file, dataSourceIdNumber),
  );
  return await Promise.allSettled(promises);
};

const createRagDocumentMutation = async (
  file: File,
  dataSourceId: number,
) => {
  const response = await dataSourceFilesApi.uploadFileToDataSource(dataSourceId, file);
  return response.data;
};

export const useGetRagDocuments = (dataSourceId: string) => {
  return useQuery({
    queryKey: [QueryKeys.getRagDocuments, { dataSourceId }],
    queryFn: () => getRagDocuments(dataSourceId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) {
        return false;
      }
      const nullTimestampDocuments = data.find(
        (file: DataSourceFile) => file.vector_upload_timestamp === null,
      );
      const nullSummaryCreation = data.find(
        (file: DataSourceFile) =>
          file.summary_creation_timestamp === null,
      );
      return nullTimestampDocuments || nullSummaryCreation ? 3000 : false;
    },
  });
};

const getRagDocuments = async (
  dataSourceId: number | string,
): Promise<DataSourceFile[]> => {
  const id = typeof dataSourceId === 'string' ? parseInt(dataSourceId, 10) : dataSourceId;
  return (await dataSourceFilesApi.listFilesInDataSource(id)).data.items;
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
  id,
  dataSourceId,
}: {
  id: string;
  dataSourceId: number | string;
}): Promise<void> => {
  const dataSourceIdNumber = typeof dataSourceId === 'string' ? parseInt(dataSourceId, 10) : dataSourceId;
  await dataSourceFilesApi.deleteFileInDataSource(dataSourceIdNumber, id);
};
