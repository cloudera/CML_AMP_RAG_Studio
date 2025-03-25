import { useNavigate, useParams } from "@tanstack/react-router";
import { useGetLlmModels } from "src/api/modelsApi";
import {
  CreateSessionRequest,
  useCreateSessionMutation,
} from "src/api/sessionApi";
import messageQueue from "src/utils/messageQueue.ts";
import {
  getDefaultProjectQueryOptions,
  useGetDefaultProject,
} from "src/api/projectsApi.ts";
import { useSuspenseQuery } from "@tanstack/react-query";

const useCreateSessionAndRedirect = () => {
  const navigate = useNavigate();
  const { projectId } = useParams({ strict: false });
  const { data: defaultProject } = useSuspenseQuery(
    getDefaultProjectQueryOptions,
  );

  const { data: models } = useGetLlmModels();
  const createSession = useCreateSessionMutation({
    onSuccess: () => {
      messageQueue.success("Session created successfully");
    },
    onError: () => {
      messageQueue.error("Failed to create session");
    },
  });

  return (question?: string, dataSourceId?: number) => {
    if (models) {
      const requestBody: CreateSessionRequest = {
        name: "",
        dataSourceIds: dataSourceId ? [dataSourceId] : [],
        inferenceModel: models[0].model_id,
        responseChunks: 10,
        queryConfiguration: {
          enableHyde: false,
          enableSummaryFilter: true,
        },
        projectId: projectId ? parseInt(projectId) : defaultProject.id,
      };
      createSession
        .mutateAsync(requestBody)
        .then((session) => {
          const to =
            projectId === defaultProject.id.toString()
              ? `/chats/${session.id.toString()}`
              : `/chats/projects/${session.projectId.toString()}/sessions/${session.id.toString()}`;
          navigate({
            to,
            params: { sessionId: session.id.toString() },
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
