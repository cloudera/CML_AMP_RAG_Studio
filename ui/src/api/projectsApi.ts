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
import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  ApiError,
  CustomError,
  deleteRequest,
  getRequest,
  MutationKeys,
  postRequest,
  QueryKeys,
  ragPath,
  UseMutationType,
} from "src/api/utils.ts";
import { DataSourceType } from "./dataSourceApi";

export interface Project {
  id: number;
  name: string;
  defaultProject: boolean;
  timeCreated: number;
  timeUpdated: number;
  createdById: string;
  updatedById: string;
}

export interface CreateProject {
  name: string;
}

// Project API hooks and functions

export const useGetProjects = () => {
  return useQuery({
    queryKey: [QueryKeys.getProjects],
    queryFn: async () => {
      return await getProjects();
    },
  });
};

export const getProjectsQueryOptions = queryOptions({
  queryKey: [QueryKeys.getProjects],
  queryFn: async () => {
    return await getProjects();
  },
});

export const getProjects = async (): Promise<Project[]> => {
  return await getRequest(`${ragPath}/projects`);
};

export const getDefaultProjectQueryOptions = queryOptions({
  queryKey: [QueryKeys.getDefaultProject],
  queryFn: async () => {
    return await getDefaultProject();
  },
  staleTime: Infinity,
});

const getDefaultProject = async (): Promise<Project> => {
  return await getRequest(`${ragPath}/projects/default`);
};

// Create project
export const useCreateProject = ({
  onSuccess,
  onError,
}: UseMutationType<Project>) => {
  return useMutation({
    mutationKey: [MutationKeys.createProject],
    mutationFn: createProject,
    onError,
    onSuccess,
  });
};

const createProject = async (input: CreateProject): Promise<Project> => {
  return await postRequest(`${ragPath}/projects`, input);
};

export const useUpdateProject = ({
  onSuccess,
  onError,
}: UseMutationType<Project>) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: [MutationKeys.updateProject],
    mutationFn: updateProject,
    onError,
    onSuccess: (data) => {
      queryClient.setQueryData(
        [QueryKeys.getProjects],
        (oldData: Project[]) => {
          const index = oldData.findIndex((item) => item.id === data.id);
          if (index !== -1) {
            const updatedData = [...oldData];
            updatedData[index] = data;
            return updatedData;
          }
          return [...oldData, data];
        },
      );
      if (onSuccess) {
        onSuccess(data);
      }
    },
  });
};

const updateProject = async (project: Project): Promise<Project> => {
  if (!project.id) {
    throw new Error("Project ID is required for update");
  }
  return await postRequest(
    `${ragPath}/projects/${String(project.id)}`,
    project,
  );
};

export const useDeleteProject = ({
  onSuccess,
  onError,
}: UseMutationType<void>) => {
  return useMutation({
    mutationKey: [MutationKeys.deleteProject],
    mutationFn: deleteProject,
    onError,
    onSuccess,
  });
};

const deleteProject = async (projectId: number): Promise<void> => {
  await deleteRequest(`${ragPath}/projects/${String(projectId)}`);
};

// Get data source IDs for project
export const useGetDataSourcesForProject = (projectId?: number) => {
  return useQuery({
    queryKey: [QueryKeys.getDataSourcesForProject, { projectId }],
    queryFn: async () => {
      if (!projectId) {
        return [];
      }
      return await getDataSourcesForProject(projectId);
    },
    enabled: !!projectId,
  });
};

export const getDataSourcesForProjectQueryOptions = (projectId: number) =>
  queryOptions({
    queryKey: [QueryKeys.getDataSourcesForProject, { projectId }],
    queryFn: async () => {
      return await getDataSourcesForProject(projectId);
    },
  });

const getDataSourcesForProject = async (
  projectId: number,
): Promise<DataSourceType[]> => {
  return await getRequest(
    `${ragPath}/projects/${String(projectId)}/dataSources`,
  );
};

export const useAddDataSourceToProject = ({
  onSuccess,
  onError,
}: UseMutationType<void>) => {
  return useMutation({
    mutationKey: [MutationKeys.addDataSourceToProject],
    mutationFn: addDataSourceToProject,
    onError,
    onSuccess,
  });
};

const addDataSourceToProject = async ({
  projectId,
  dataSourceId,
}: {
  projectId: number;
  dataSourceId: number;
}): Promise<void> => {
  await fetch(
    `${ragPath}/projects/${String(projectId)}/dataSources/${String(dataSourceId)}`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
    },
  ).then(async (res) => {
    if (!res.ok) {
      const detail = (await res.json()) as CustomError;
      throw new ApiError(detail.message ?? detail.detail, res.status);
    }
  });
};

// Remove data source from project
export const useRemoveDataSourceFromProject = ({
  onSuccess,
  onError,
}: UseMutationType<void>) => {
  return useMutation({
    mutationKey: [MutationKeys.removeDataSourceFromProject],
    mutationFn: removeDataSourceFromProject,
    onError,
    onSuccess,
  });
};

const removeDataSourceFromProject = async ({
  projectId,
  dataSourceId,
}: {
  projectId: number;
  dataSourceId: number;
}): Promise<void> => {
  await deleteRequest(
    `${ragPath}/projects/${String(projectId)}/dataSources/${String(dataSourceId)}`,
  );
};
