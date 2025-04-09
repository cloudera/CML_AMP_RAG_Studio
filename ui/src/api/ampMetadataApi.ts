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

import { queryOptions, useMutation, useQuery } from "@tanstack/react-query";
import {
  commonHeaders,
  getRequest,
  llmServicePath,
  MutationKeys,
  postRequest,
  QueryKeys,
  UseMutationType,
} from "src/api/utils.ts";

export const useGetAmpUpdateStatus = () => {
  return useQuery({
    queryKey: [QueryKeys.getAmpUpdateStatus],
    queryFn: getAmpUpdateStatus,
  });
};

const getAmpUpdateStatus = async (): Promise<boolean> => {
  return getRequest(`${llmServicePath}/amp`);
};

const getAmpIsComposable = async (): Promise<boolean> => {
  return getRequest(`${llmServicePath}/amp/is-composable`);
};

export const getAmpIsComposableQueryOptions = queryOptions({
  queryKey: [QueryKeys.getAmpIsComposable],
  queryFn: getAmpIsComposable,
});

export enum JobStatus {
  SCHEDULING = "ENGINE_SCHEDULING",
  STARTING = "ENGINE_STARTING",
  RUNNING = "ENGINE_RUNNING",
  STOPPING = "ENGINE_STOPPING",
  STOPPED = "ENGINE_STOPPED",
  UNKNOWN = "ENGINE_UNKNOWN",
  SUCCEEDED = "ENGINE_SUCCEEDED",
  FAILED = "ENGINE_FAILED",
  TIMEDOUT = "ENGINE_TIMEDOUT",
  RESTARTING = "RESTARTING",
}

export const useGetAmpUpdateJobStatus = (enabled: boolean) => {
  return useQuery({
    queryKey: [QueryKeys.getAmpUpdateJobStatus],
    queryFn: getAmpUpdateJobStatus,
    refetchInterval: () => {
      return 1000;
    },
    enabled: enabled,
  });
};

const getAmpUpdateJobStatus = async (): Promise<JobStatus> => {
  return getRequestJobStatus(`${llmServicePath}/amp/job-status`);
};

const getRequestJobStatus = async (url: string): Promise<JobStatus> => {
  const res = await fetch(url, {
    method: "GET",
    headers: { ...commonHeaders },
  });

  if (!res.ok) {
    return Promise.resolve(JobStatus.RESTARTING);
  }

  return (await res.json()) as JobStatus;
};

export const useUpdateAmpMutation = ({
  onSuccess,
  onError,
}: UseMutationType<string>) => {
  return useMutation({
    mutationKey: [MutationKeys.updateAmp],
    mutationFn: () => updateAmpMutation(),
    onSuccess,
    onError,
  });
};

const updateAmpMutation = async (): Promise<string> => {
  return await postRequest(`${llmServicePath}/amp`, {});
};

export const useGetAmpConfig = () => {
  return useQuery({
    queryKey: [QueryKeys.getAmpConfig],
    queryFn: getAmpConfig,
  });
};

export interface AwsConfig {
  region?: string;
  document_bucket_name?: string;
  bucket_prefix?: string;
  access_key_id?: string;
  secret_access_key?: string;
}

export interface AzureConfig {
  openai_key?: string;
  openai_endpoint?: string;
  openai_api_version?: string;
}

export interface CaiiConfig {
  caii_domain?: string;
}

export interface ProjectConfig {
  use_enhanced_pdf_processing: boolean;
  aws_config: AwsConfig;
  azure_config: AzureConfig;
  caii_config: CaiiConfig;
}

export const getAmpConfig = async (): Promise<ProjectConfig> => {
  return await getRequest(`${llmServicePath}/amp/config`);
};

export const getAmpConfigQueryOptions = queryOptions({
  queryKey: [QueryKeys.getAmpConfig],
  queryFn: getAmpConfig,
});
