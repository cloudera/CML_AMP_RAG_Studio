import { Button, Tooltip } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import {
  ChatMessageType,
  createQueryConfiguration,
  getOnEvent,
  useStreamingChatMutation,
} from "src/api/chatApi.ts";
import { useStreamingChunkBuffer } from "src/hooks/useStreamingChunkBuffer.ts";
import { useContext } from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";

const RegenerateButton = ({
  message,
  excludeKnowledgeBase,
  onStarted,
}: {
  message: ChatMessageType;
  excludeKnowledgeBase: boolean;
  onStarted?: () => void;
}) => {
  const {
    streamedChatState: [, setStreamedChat],
    streamedEventState: [, setStreamedEvent],
    streamedAbortControllerState: [, setStreamedAbortController],
  } = useContext(RagChatContext);
  const {
    streamingMessageIdState: [, setStreamingMessageId],
  } = useContext(RagChatContext);
  // Use custom hook to handle batched streaming updates
  const { onChunk, flush } = useStreamingChunkBuffer((chunks) => {
    setStreamedChat((prev) => prev + chunks);
  });

  const streamChatMutation = useStreamingChatMutation({
    onChunk,
    onEvent: getOnEvent(setStreamedEvent),
    onSuccess: () => {
      // Flush any remaining chunks before cleanup
      flush();
      setStreamedChat("");
      setStreamingMessageId(undefined);
    },
    getController: (ctrl) => {
      setStreamedAbortController(ctrl);
    },
  });

  const handleClick = () => {
    onStarted?.();
    setStreamingMessageId(message.id);
    streamChatMutation.mutate({
      query: message.rag_message.user,
      session_id: message.session_id,
      configuration: createQueryConfiguration(excludeKnowledgeBase),
      response_id: message.id,
    });
  };

  return (
    <Tooltip title="Regenerate response">
      <Button
        type="text"
        icon={<ReloadOutlined />}
        size="small"
        onClick={handleClick}
      />
    </Tooltip>
  );
};

export default RegenerateButton;
