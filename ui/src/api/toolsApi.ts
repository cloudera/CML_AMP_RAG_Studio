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
  deleteRequest,
  getRequest,
  llmServicePath,
  postRequest,
  QueryKeys,
  UseMutationType,
} from "src/api/utils.ts";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export interface Tool {
  name: string;
  command?: string;
  url?: string[];
  args?: string[];
  env?: Record<string, string>;
  metadata: {
    description: string;
    display_name: string;
  };
  type?: "mcp" | "custom"; // Add tool type to distinguish MCP vs custom tools
}

export interface CustomTool {
  name: string;
  display_name: string;
  description: string;
  function_schema: {
    type: "object";
    properties: Record<
      string,
      {
        type: string;
        description: string;
        enum?: string[];
      }
    >;
    required: string[];
  };
  script_path: string;
}

export interface AddToolFormValues {
  name: string;
  command?: string;
  url?: string;
  args?: string;
  env?: { key: string; value: string }[];
  display_name: string;
  description: string;
}

export interface CustomToolFormValues {
  name: string;
  display_name: string;
  description: string;
  function_schema: string; // JSON string
  script_file: File;
}

export interface CustomToolTestRequest {
  input_data: Record<string, unknown>;
}

export const getTools = async (): Promise<Tool[]> => {
  return getRequest(`${llmServicePath}/tools`);
};

export const useToolsQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.getTools],
    queryFn: getTools,
  });
};

export const addTool = async (tool: Tool): Promise<Tool> => {
  return postRequest(`${llmServicePath}/tools`, tool);
};

export const useAddToolMutation = ({
  onSuccess,
  onError,
}: UseMutationType<Tool>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: addTool,
    onSuccess: (tool) => {
      void queryClient.invalidateQueries({ queryKey: [QueryKeys.getTools] });
      if (onSuccess) {
        onSuccess(tool);
      }
    },
    onError,
  });
};

export const deleteTool = async (name: string): Promise<void> => {
  return deleteRequest(`${llmServicePath}/tools/${name}`);
};

export const useDeleteToolMutation = ({
  onSuccess,
  onError,
}: UseMutationType<void>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTool,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [QueryKeys.getTools] });
      if (onSuccess) {
        onSuccess();
      }
    },
    onError,
  });
};

// User Tools API
export const getCustomTools = async (): Promise<CustomTool[]> => {
  return getRequest(`${llmServicePath}/custom-tools`);
};

export const useCustomToolsQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.getCustomTools],
    queryFn: getCustomTools,
  });
};

export const createCustomTool = async (toolData: {
  name: string;
  display_name: string;
  description: string;
  function_schema: string;
  script_file: File;
}): Promise<CustomTool> => {
  const formData = new FormData();
  formData.append("name", toolData.name);
  formData.append("display_name", toolData.display_name);
  formData.append("description", toolData.description);
  formData.append("function_schema", toolData.function_schema);
  formData.append("script_file", toolData.script_file);

  const response = await fetch(`${llmServicePath}/custom-tools`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const useCreateCustomToolMutation = ({
  onSuccess,
  onError,
}: UseMutationType<CustomTool>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createCustomTool,
    onSuccess: (tool) => {
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.getCustomTools],
      });
      if (onSuccess) {
        onSuccess(tool);
      }
    },
    onError,
  });
};

export const updateCustomTool = async (
  toolName: string,
  toolData: {
    name: string;
    display_name: string;
    description: string;
    function_schema: string;
    script_file: File;
  },
): Promise<CustomTool> => {
  const formData = new FormData();
  formData.append("name", toolData.name);
  formData.append("display_name", toolData.display_name);
  formData.append("description", toolData.description);
  formData.append("function_schema", toolData.function_schema);
  formData.append("script_file", toolData.script_file);

  const response = await fetch(`${llmServicePath}/custom-tools/${toolName}`, {
    method: "PUT",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const useUpdateCustomToolMutation = ({
  onSuccess,
  onError,
}: UseMutationType<CustomTool>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      toolName,
      toolData,
    }: {
      toolName: string;
      toolData: {
        name: string;
        display_name: string;
        description: string;
        function_schema: string;
        script_file: File;
      };
    }) => updateCustomTool(toolName, toolData),
    onSuccess: (tool) => {
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.getCustomTools],
      });
      if (onSuccess) {
        onSuccess(tool);
      }
    },
    onError,
  });
};

export const deleteCustomTool = async (toolName: string): Promise<void> => {
  return deleteRequest(`${llmServicePath}/custom-tools/${toolName}`);
};

export const useDeleteCustomToolMutation = ({
  onSuccess,
  onError,
}: UseMutationType<void>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCustomTool,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.getCustomTools],
      });
      if (onSuccess) {
        onSuccess();
      }
    },
    onError,
  });
};

export const testCustomTool = async (
  toolName: string,
  testData: CustomToolTestRequest,
): Promise<{ success: boolean; result?: unknown; error?: string }> => {
  return postRequest(
    `${llmServicePath}/custom-tools/${toolName}/test`,
    testData,
  );
};

export const useTestCustomToolMutation = ({
  onSuccess,
  onError,
}: UseMutationType<{ success: boolean; result?: unknown; error?: string }>) => {
  return useMutation({
    mutationFn: ({
      toolName,
      testData,
    }: {
      toolName: string;
      testData: CustomToolTestRequest;
    }) => testCustomTool(toolName, testData),
    onSuccess,
    onError,
  });
};
