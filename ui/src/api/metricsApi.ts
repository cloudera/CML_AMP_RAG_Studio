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
import { useQuery } from "@tanstack/react-query";
import { llmServicePath, postRequest, QueryKeys } from "src/api/utils.ts";

export interface MetricFilter {
  data_source_id?: number;
  inference_model?: string;
  rerank_model?: string;
  has_rerank_model?: boolean;
  top_k?: number;
  session_id?: number;
  use_summary_filter?: boolean;
  use_hyde?: boolean;
  use_question_condensing?: boolean;
  exclude_knowledge_base?: boolean;
  project_id?: number;
}

export interface MetadataMetrics {
  number_of_data_sources: number;
  number_of_sessions: number;
  number_of_documents: number;
}

export interface AppMetrics {
  positive_ratings: number;
  negative_ratings: number;
  no_ratings: number;
  count_of_interactions: number;
  count_of_direct_interactions: number;
  aggregated_feedback: Record<string, number>;
  unique_users: number;
  max_score_over_time: [number, number][];
  input_word_count_over_time: [number, number][];
  output_word_count_over_time: [number, number][];
  evaluation_averages: Record<string, number>;
  metadata_metrics: MetadataMetrics;
}

export const useGetMetrics = (metricFilter: MetricFilter) => {
  return useQuery({
    queryKey: [QueryKeys.getMetricsByDataSource, metricFilter],
    queryFn: () => getMetricsQuery(metricFilter),
  });
};

const getMetricsQuery = async (
  metricFilter: MetricFilter,
): Promise<AppMetrics> => {
  return await postRequest(`${llmServicePath}/app-metrics`, metricFilter);
};
