import { useNavigate, useParams } from "@tanstack/react-router";
import { useGetEmbeddingModels, useGetLlmModels } from "src/api/modelsApi";
import {
  CreateSessionRequest,
  Session,
  useCreateSessionMutation,
} from "src/api/sessionApi";
import messageQueue from "src/utils/messageQueue.ts";
import { getDefaultProjectQueryOptions } from "src/api/projectsApi.ts";
import { useSuspenseQuery } from "@tanstack/react-query";

const useCreateSessionAndRedirect = (
  onSuccess?: (session: Session) => void,
) => {
  const navigate = useNavigate();
  const { projectId } = useParams({ strict: false });
  const { data: defaultProject } = useSuspenseQuery(
    getDefaultProjectQueryOptions,
  );

  const { data: embeddingModels } = useGetEmbeddingModels();
  const { data: models } = useGetLlmModels();
  const createSession = useCreateSessionMutation({
    onSuccess: (session) => {
      messageQueue.success("Session created successfully");
      if (onSuccess) {
        onSuccess(session);
      }
    },
    onError: () => {
      messageQueue.error("Failed to create session");
    },
  });

  return (
    dataSourceIds: number[],
    question?: string,
    inferenceModel?: string,
  ) => {
    if (models) {
      const supportsToolCalling = models.find(
        (model) => model.model_id === inferenceModel,
      )?.tool_calling_supported;
      const requestBody: CreateSessionRequest = {
        name: "",
        dataSourceIds: dataSourceIds,
        inferenceModel: inferenceModel ?? models[0].model_id,
        responseChunks: 10,
        queryConfiguration: {
          enableHyde: false,
          enableSummaryFilter: true,
          enableToolCalling: supportsToolCalling ?? false,
          selectedTools: [],
        },
        embeddingModel: embeddingModels?.length
          ? embeddingModels[0].model_id
          : undefined,
        projectId: projectId ? parseInt(projectId) : defaultProject.id,
      };
      createSession
        .mutateAsync(requestBody)
        .then((session) => {
          const to =
            session.projectId === defaultProject.id
              ? "/chats/$sessionId"
              : "/chats/projects/$projectId/sessions/$sessionId";
          const params =
            session.projectId === defaultProject.id
              ? { sessionId: session.id.toString() }
              : {
                  projectId: session.projectId.toString(),
                  sessionId: session.id.toString(),
                };
          navigate({
            to,
            params,
            search: question ? { question: question } : undefined,
          }).catch(() => null);
        })
        .catch(() => {
          messageQueue.error("Failed to create session");
        });
    }
  };
};

export default useCreateSessionAndRedirect;
