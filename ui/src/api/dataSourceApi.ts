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
  MutationKeys,
  QueryKeys,
  UseMutationType
} from "src/api/utils.ts";
import { DataSource, DataSourceCreateRequest, DataSourceUpdateRequest } from "src/services/api/api";
import { dataSourceApi } from "src/services/api_config";

export const useCreateDataSourceMutation = ({
  onSuccess,
  onError,
}: UseMutationType<DataSource>) => {
  return useMutation({
    mutationKey: [MutationKeys.createDataSource],
    mutationFn: createDataSourceMutation,
    onSuccess,
    onError,
  });
};

const createDataSourceMutation = async (
  request: DataSourceCreateRequest
): Promise<DataSource> => {
  return (await dataSourceApi.createDataSource(request)).data;
};

export const useUpdateDataSourceMutation = ({
  onSuccess,
  onError,
}: UseMutationType<DataSource>) => {
  return useMutation({
    mutationKey: [MutationKeys.updateDataSource],
    mutationFn: updateDataSourceMutation,
    onSuccess,
    onError,
  });
};

const updateDataSourceMutation = async (
  {
    id,
    request,
  }: {
    id: number;
    request: DataSourceUpdateRequest;
  }
): Promise<DataSource> => {
  return (await dataSourceApi.updateDataSource(id, request)).data;
};

export const useGetDataSourcesQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.getDataSources],
    queryFn: async () => {
      const res = await getDataSourcesQuery();

      return res
        .map((source: DataSource) => ({ ...source, key: source.id }))
        .reverse();
    },
  });
};

export const getDataSourcesQueryOptions = queryOptions({
  queryKey: [QueryKeys.getDataSources],
  queryFn: async () => {
    const res = await getDataSourcesQuery();

    return res
      .map((source: DataSource) => ({ ...source, key: source.id }))
      .reverse();
  },
});

const getDataSourcesQuery = async (): Promise<DataSource[]> => {
  return (await dataSourceApi.listDataSources()).data.items;
};

export const getDataSourceById = (dataSourceId: number | string) => {
  return queryOptions({
    queryKey: [QueryKeys.getDataSourceById, { dataSourceId }],
    queryFn: () => getDataSourceByIdQuery(dataSourceId),
  });
};

const getDataSourceByIdQuery = async (
  dataSourceId: number | string,
): Promise<DataSource> => {
  const id = typeof dataSourceId === 'string' ? parseInt(dataSourceId, 10) : dataSourceId;
  return (await dataSourceApi.getDataSource(id)).data;
};

export const getCdfConfigQuery = async (
  dataSourceId: number | string,
): Promise<string> => {
  const id = typeof dataSourceId === 'string' ? parseInt(dataSourceId, 10) : dataSourceId;
  return id.toString(); // TODO: Implement
  // return await getRequest(
  //   `${ragPath}/${paths.dataSources}/${dataSourceId}/nifiConfig?ragStudioUrl=${window.location.origin}`,
  // );
};

export const deleteDataSourceMutation = async (
  dataSourceId: number,
): Promise<void> => {
  await dataSourceApi.deleteDataSource(dataSourceId);
};
