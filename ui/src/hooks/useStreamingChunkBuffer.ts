import { useCallback, useEffect, useRef } from "react";

/**
 * Custom hook to handle batched streaming chunk updates to prevent React infinite loop errors.
 *
 * When streaming responses arrive rapidly, directly calling setState for each chunk can cause
 * React to hit its maximum update depth limit. This hook batches chunks together using a
 * timeout mechanism to ensure smooth updates without infinite loops.
 *
 * @param onUpdate - Callback function to update the accumulated chunks
 * @param batchDelayMs - Delay in milliseconds to batch chunks (default: 1ms)
 * @returns Object with onChunk callback and flush function
 */
export const useStreamingChunkBuffer = (
  onUpdate: (accumulatedChunks: string) => void,
  batchDelayMs = 1,
) => {
  const chunkBufferRef = useRef<string>("");
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const flushChunkBuffer = useCallback(() => {
    if (chunkBufferRef.current) {
      onUpdate(chunkBufferRef.current);
      chunkBufferRef.current = "";
    }
  }, [onUpdate]);

  const onChunk = useCallback(
    (chunk: string) => {
      // Accumulate chunks in buffer
      chunkBufferRef.current += chunk;

      // Clear any existing timeout
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }

      // Batch updates using setTimeout to prevent infinite loops
      updateTimeoutRef.current = setTimeout(() => {
        flushChunkBuffer();
      }, batchDelayMs);
    },
    [flushChunkBuffer, batchDelayMs],
  );

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    };
  }, []);

  return {
    onChunk,
    flush: flushChunkBuffer,
  };
};
