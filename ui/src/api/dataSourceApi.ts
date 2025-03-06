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

import { queryOptions, useMutation, useQuery } from "@tanstack/react-query";
import {
  deleteRequest,
  getRequest,
  llmServicePath,
  MutationKeys,
  paths,
  postRequest,
  QueryKeys,
  ragPath,
  UseMutationType,
} from "src/api/utils.ts";

export interface CreateDataSourceType {
  name: string;
  chunkSize: number;
  chunkOverlapPercent: number;
  embeddingModel: string;
}

export enum ConnectionType {
  "MANUAL" = "MANUAL",
  "CDF" = "CDF",
  "API" = "API",
  "OTHER" = "OTHER",
}

export interface DataSourceBaseType {
  id: number;
  name: string;
  chunkSize: number;
  chunkOverlapPercent: number;
  connectionType: ConnectionType;
  embeddingModel: string;
  summarizationModel?: string;
}

export type DataSourceType = DataSourceBaseType & {
  totalDocSize: number | null;
  documentCount: number;
};

export type Point2d = [[number, number], string];

export const useCreateDataSourceMutation = ({
  onSuccess,
  onError,
}: UseMutationType<DataSourceBaseType>) => {
  return useMutation({
    mutationKey: [MutationKeys.createDataSource],
    mutationFn: createDataSourceMutation,
    onSuccess,
    onError,
  });
};

const createDataSourceMutation = async (
  dataSource: CreateDataSourceType,
): Promise<DataSourceBaseType> => {
  return await postRequest(`${ragPath}/${paths.dataSources}`, dataSource);
};

export const useUpdateDataSourceMutation = ({
  onSuccess,
  onError,
}: UseMutationType<DataSourceBaseType>) => {
  return useMutation({
    mutationKey: [MutationKeys.updateDataSource],
    mutationFn: updateDataSourceMutation,
    onSuccess,
    onError,
  });
};

const updateDataSourceMutation = async (
  dataSource: DataSourceBaseType,
): Promise<DataSourceBaseType> => {
  return await postRequest(
    `${ragPath}/${paths.dataSources}/${dataSource.id.toString()}`,
    dataSource,
  );
};

export const useGetDataSourcesQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.getDataSources],
    queryFn: async () => {
      const res = await getDataSourcesQuery();

      return res
        .map((source: DataSourceType) => ({ ...source, key: source.id }))
        .reverse();
    },
  });
};

export const getDataSourcesQueryOptions = queryOptions({
  queryKey: [QueryKeys.getDataSources],
  queryFn: async () => {
    const res = await getDataSourcesQuery();

    return res
      .map((source: DataSourceType) => ({ ...source, key: source.id }))
      .reverse();
  },
});

const getDataSourcesQuery = async (): Promise<DataSourceType[]> => {
  return await getRequest(`${ragPath}/${paths.dataSources}`);
};

export const getDataSourceById = (dataSourceId: string) => {
  return queryOptions({
    queryKey: [QueryKeys.getDataSourceById, { dataSourceId }],
    queryFn: () => getDataSourceByIdQuery(dataSourceId),
    staleTime: 1000 * 5,
  });
};

const getDataSourceByIdQuery = async (
  dataSourceId: string,
): Promise<DataSourceType> => {
  return await getRequest(`${ragPath}/${paths.dataSources}/${dataSourceId}`);
};

export const getVisualizeDataSource = (dataSourceId: string) => {
  return useQuery({
    queryKey: [QueryKeys.getVisualizeDataSource, { dataSourceId }],
    queryFn: () => getVisualizeDataSourceQuery(dataSourceId),
    staleTime: 1000 * 5 * 60,
  });
};

const getVisualizeDataSourceQuery = async (
  dataSourceId: string,
): Promise<Point2d[]> => {
  return await getRequest(
    `${llmServicePath}/data_sources/${dataSourceId}/visualize`,
  );
};

export const useVisualizeDataSourceWithUserQuery = ({
  onSuccess,
  onError,
}: UseMutationType<Point2d[]>) => {
  return useMutation({
    mutationKey: [MutationKeys.visualizeDataSourceWithUserQuery],
    mutationFn: visualizeDataSourceWithUserQuery,
    onSuccess,
    onError,
  });
};

export interface VisualizationRequest {
  dataSourceId: string;
  userQuery: string;
}

const visualizeDataSourceWithUserQuery = async (
  request: VisualizationRequest,
): Promise<Point2d[]> => {
  return await postRequest(
    `${llmServicePath}/data_sources/${request.dataSourceId}/visualize`,
    { user_query: request.userQuery },
  );
};

export type ConfigType = "S3" | "AZURE_BLOB";

export interface CdfConfigMetadataType {
  name: string;
  description: string;
  configType: ConfigType;
}

export const getCdfConfigQuery = async (
  dataSourceId: string,
  configType: ConfigType,
): Promise<string> => {
  return await getRequest(
    `${ragPath}/${paths.dataSources}/${dataSourceId}/nifiConfig?ragStudioUrl=${window.location.origin}&configType=${configType}`,
  );
};

export const useGetCdfConfigMetadataQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.getCdfConfigMetadata],
    queryFn: async () => {
      return await getCdfConfigMetadataQuery();
    },
  });
};

const getCdfConfigMetadataQuery = async (): Promise<
  CdfConfigMetadataType[]
> => {
  return await getRequest(`${ragPath}/${paths.dataSources}/nifiConfigMetadata`);
};

export const deleteDataSourceMutation = async (
  dataSourceId: string,
): Promise<void> => {
  await deleteRequest(`${ragPath}/${paths.dataSources}/${dataSourceId}`);
};
