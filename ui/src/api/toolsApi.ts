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

import { QueryKeys } from "src/api/utils.ts";
import { useQuery } from "@tanstack/react-query";

export interface ToolInputParameter {
  name: string;
  description: string;
  type: string;
  required: boolean;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  inputs: ToolInputParameter[];
  outputFormat: string;
}

export interface GetToolsResponse {
  tools: Tool[];
}

export const useToolsQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.getTools],
    queryFn: getTools,
  });
};

// Mock function to get tools
export const getTools = async (): Promise<GetToolsResponse> => {
  return Promise.resolve({
    tools: [
      {
        id: "1",
        name: "date",
        description: "Retrieves current date and time information",
        inputs: [
          {
            name: "timezone",
            description:
              "The timezone to get date/time for (e.g., 'UTC', 'America/New_York')",
            type: "string",
            required: false,
          },
          {
            name: "format",
            description: "Date format (e.g., 'YYYY-MM-DD', 'MM/DD/YYYY')",
            type: "string",
            required: false,
          },
        ],
        outputFormat: "String containing the formatted date and time",
      },
      {
        id: "2",
        name: "search",
        description: "Performs a search query and returns relevant results",
        inputs: [
          {
            name: "query",
            description: "The search query",
            type: "string",
            required: true,
          },
          {
            name: "limit",
            description: "Maximum number of results to return",
            type: "number",
            required: false,
          },
        ],
        outputFormat:
          "JSON array of search results with titles and descriptions",
      },
      {
        id: "3",
        name: "calculator",
        description: "Performs mathematical calculations",
        inputs: [
          {
            name: "expression",
            description: "The mathematical expression to evaluate",
            type: "string",
            required: true,
          },
        ],
        outputFormat: "Numerical result of the calculation",
      },
    ],
  });
};
