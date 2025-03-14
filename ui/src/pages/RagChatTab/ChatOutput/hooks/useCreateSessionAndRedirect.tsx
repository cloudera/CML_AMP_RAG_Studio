import { useNavigate } from "@tanstack/react-router";
import { useGetLlmModels } from "src/api/modelsApi";
import {
  createSessionMutation,
  CreateSessionRequest,
} from "src/api/sessionApi";

const useCreateSessionAndRedirect = () => {
  const navigate = useNavigate();
  const { data: models } = useGetLlmModels();

  return (question?: string, dataSourceId?: number) => {
    if (models) {
      const requestBody: CreateSessionRequest = {
        name: "New Chat",
        dataSourceIds: dataSourceId ? [dataSourceId] : [],
        inferenceModel: models[0].model_id,
        responseChunks: 10,
        queryConfiguration: {
          enableHyde: false,
          enableSummaryFilter: true,
        },
      };
      createSessionMutation(requestBody)
        .then((session) => {
          navigate({
            to: `/sessions/${session.id.toString()}`,
            params: { sessionId: session.id.toString() },
            search: question ? { question: question } : undefined,
          }).catch(() => null);
        })
        .catch(() => null);
    }
  };
};

export default useCreateSessionAndRedirect;
