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

export interface Project {
  id?: number;
  name: string;
  defaultProject: boolean;
  timeCreated?: string;
  timeUpdated?: string;
  createdById?: string;
  updatedById?: string;
}

export interface CreateProject {
  name: string;
}

// Add QueryKeys for projects
declare module "src/api/utils.ts" {
  export enum QueryKeys {
    getProjects = "getProjects",
    getProjectById = "getProjectById",
    getDefaultProject = "getDefaultProject",
    getDataSourceIdsForProject = "getDataSourceIdsForProject",
  }

  export enum MutationKeys {
    createProject = "createProject",
    updateProject = "updateProject",
    deleteProject = "deleteProject",
    addDataSourceToProject = "addDataSourceToProject",
    removeDataSourceFromProject = "removeDataSourceFromProject",
  }
}

// Get all projects
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

const getProjects = async (): Promise<Project[]> => {
  return await getRequest(`${ragPath}/projects`);
};

// Get project by ID
export const useGetProjectById = (projectId?: number) => {
  return useQuery({
    queryKey: [QueryKeys.getProjectById, { projectId }],
    queryFn: async () => {
      if (!projectId) {
        return undefined;
      }
      return await getProjectById(projectId);
    },
    enabled: !!projectId,
  });
};

export const getProjectByIdQueryOptions = (projectId: number) =>
  queryOptions({
    queryKey: [QueryKeys.getProjectById, { projectId }],
    queryFn: async () => {
      return await getProjectById(projectId);
    },
  });

const getProjectById = async (projectId: number): Promise<Project> => {
  return await getRequest(`${ragPath}/projects/${projectId}`);
};

// Get default project
export const useGetDefaultProject = () => {
  return useQuery({
    queryKey: [QueryKeys.getDefaultProject],
    queryFn: async () => {
      return await getDefaultProject();
    },
  });
};

export const getDefaultProjectQueryOptions = queryOptions({
  queryKey: [QueryKeys.getDefaultProject],
  queryFn: async () => {
    return await getDefaultProject();
  },
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

// Update project
export const useUpdateProject = ({
  onSuccess,
  onError,
}: UseMutationType<Project>) => {
  return useMutation({
    mutationKey: [MutationKeys.updateProject],
    mutationFn: updateProject,
    onError,
    onSuccess,
  });
};

const updateProject = async (project: Project): Promise<Project> => {
  if (!project.id) {
    throw new Error("Project ID is required for update");
  }
  return await fetch(`${ragPath}/projects/${project.id}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(project),
  }).then(async (res) => {
    if (!res.ok) {
      const detail = (await res.json()) as CustomError;
      throw new ApiError(detail.message ?? detail.detail, res.status);
    }
    return (await res.json()) as Project;
  });
};

// Delete project
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
  return await deleteRequest(`${ragPath}/projects/${projectId}`);
};

// Get data source IDs for project
export const useGetDataSourceIdsForProject = (projectId?: number) => {
  return useQuery({
    queryKey: [QueryKeys.getDataSourceIdsForProject, { projectId }],
    queryFn: async () => {
      if (!projectId) {
        return [];
      }
      return await getDataSourceIdsForProject(projectId);
    },
    enabled: !!projectId,
  });
};

export const getDataSourceIdsForProjectQueryOptions = (projectId: number) =>
  queryOptions({
    queryKey: [QueryKeys.getDataSourceIdsForProject, { projectId }],
    queryFn: async () => {
      return await getDataSourceIdsForProject(projectId);
    },
  });

const getDataSourceIdsForProject = async (
  projectId: number
): Promise<number[]> => {
  return await getRequest(`${ragPath}/projects/${projectId}/dataSources`);
};

// Add data source to project
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
  return await fetch(
    `${ragPath}/projects/${projectId}/dataSources/${dataSourceId}`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
    }
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
  return await deleteRequest(
    `${ragPath}/projects/${projectId}/dataSources/${dataSourceId}`
  );
};
