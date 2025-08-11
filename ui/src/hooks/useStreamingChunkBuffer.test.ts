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

import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { useStreamingChunkBuffer } from "./useStreamingChunkBuffer";

describe("useStreamingChunkBuffer", () => {
  let mockOnUpdate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    mockOnUpdate = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe("basic functionality", () => {
    it("should return onChunk and flush functions", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate),
      );

      expect(result.current.onChunk).toBeTypeOf("function");
      expect(result.current.flush).toBeTypeOf("function");
    });

    it("should not call onUpdate immediately when receiving chunks", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate),
      );

      act(() => {
        result.current.onChunk("chunk1");
        result.current.onChunk("chunk2");
      });

      expect(mockOnUpdate).not.toHaveBeenCalled();
    });
  });

  describe("batching behavior", () => {
    it("should batch multiple chunks together after delay", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 10),
      );

      act(() => {
        result.current.onChunk("chunk1");
        result.current.onChunk("chunk2");
        result.current.onChunk("chunk3");
      });

      // Fast-forward time to trigger the timeout
      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(mockOnUpdate).toHaveBeenCalledTimes(1);
      expect(mockOnUpdate).toHaveBeenCalledWith("chunk1chunk2chunk3");
    });

    it("should use default 1ms delay when no delay specified", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate),
      );

      act(() => {
        result.current.onChunk("test");
        // Advance time in same act to ensure timeout triggers
        vi.advanceTimersByTime(1); // Use the default 1ms delay
      });

      expect(mockOnUpdate).toHaveBeenCalledWith("test");
    });

    it("should use custom delay when specified", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 50),
      );

      act(() => {
        result.current.onChunk("test");
      });

      // Should not trigger before custom delay
      act(() => {
        vi.advanceTimersByTime(25);
      });
      expect(mockOnUpdate).not.toHaveBeenCalled();

      // Should trigger after custom delay
      act(() => {
        vi.advanceTimersByTime(25);
      });
      expect(mockOnUpdate).toHaveBeenCalledWith("test");
    });

    it("should debounce rapid chunks correctly", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 10),
      );

      act(() => {
        result.current.onChunk("chunk1");
        vi.advanceTimersByTime(5); // Half the delay
        result.current.onChunk("chunk2");
        vi.advanceTimersByTime(5); // Half the delay again
        result.current.onChunk("chunk3");
      });

      // Should not have called yet
      expect(mockOnUpdate).not.toHaveBeenCalled();

      // Complete the delay
      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(mockOnUpdate).toHaveBeenCalledTimes(1);
      expect(mockOnUpdate).toHaveBeenCalledWith("chunk1chunk2chunk3");
    });

    it("should handle multiple separate batches", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 10),
      );

      // First batch
      act(() => {
        result.current.onChunk("batch1chunk1");
        result.current.onChunk("batch1chunk2");
        vi.advanceTimersByTime(10);
      });

      expect(mockOnUpdate).toHaveBeenCalledTimes(1);
      expect(mockOnUpdate).toHaveBeenCalledWith("batch1chunk1batch1chunk2");

      // Second batch
      act(() => {
        result.current.onChunk("batch2chunk1");
        result.current.onChunk("batch2chunk2");
        vi.advanceTimersByTime(10);
      });

      expect(mockOnUpdate).toHaveBeenCalledTimes(2);
      expect(mockOnUpdate).toHaveBeenLastCalledWith("batch2chunk1batch2chunk2");
    });
  });

  describe("manual flush", () => {
    it("should immediately flush buffered chunks when flush is called", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 10),
      );

      act(() => {
        result.current.onChunk("chunk1");
        result.current.onChunk("chunk2");
        result.current.flush();
      });

      expect(mockOnUpdate).toHaveBeenCalledTimes(1);
      expect(mockOnUpdate).toHaveBeenCalledWith("chunk1chunk2");
    });

    it("should do nothing when flush is called with empty buffer", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate),
      );

      act(() => {
        result.current.flush();
      });

      expect(mockOnUpdate).not.toHaveBeenCalled();
    });

    it("should clear buffer after flush", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 10),
      );

      act(() => {
        result.current.onChunk("chunk1");
        result.current.flush();
      });

      expect(mockOnUpdate).toHaveBeenCalledWith("chunk1");

      // Add more chunks after flush
      act(() => {
        result.current.onChunk("chunk2");
        vi.advanceTimersByTime(10);
      });

      expect(mockOnUpdate).toHaveBeenCalledTimes(2);
      expect(mockOnUpdate).toHaveBeenLastCalledWith("chunk2");
    });

    it("should cancel pending timeout when flush is called", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 10),
      );

      act(() => {
        result.current.onChunk("chunk1");
        result.current.flush();
        vi.advanceTimersByTime(10);
      });

      // Should only be called once from flush, not from timeout
      expect(mockOnUpdate).toHaveBeenCalledTimes(1);
    });
  });

  describe("edge cases", () => {
    it("should handle empty string chunks", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 1),
      );

      act(() => {
        result.current.onChunk("");
        result.current.onChunk("test");
        result.current.onChunk("");
        vi.advanceTimersByTime(1);
      });

      expect(mockOnUpdate).toHaveBeenCalledWith("test");
    });

    it("should handle special characters and unicode", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 1),
      );

      act(() => {
        result.current.onChunk("Hello 🌟");
        result.current.onChunk(" with émojis");
        result.current.onChunk(" and üñíçödé");
        vi.advanceTimersByTime(1);
      });

      expect(mockOnUpdate).toHaveBeenCalledWith(
        "Hello 🌟 with émojis and üñíçödé",
      );
    });

    it("should handle very large chunks", () => {
      const { result } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 1),
      );

      const largeChunk = "x".repeat(10000);

      act(() => {
        result.current.onChunk(largeChunk);
        vi.advanceTimersByTime(1);
      });

      expect(mockOnUpdate).toHaveBeenCalledWith(largeChunk);
    });
  });

  describe("cleanup behavior", () => {
    it("should cleanup timeout on unmount", () => {
      const clearTimeoutSpy = vi.spyOn(global, "clearTimeout");

      const { result, unmount } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 10),
      );

      act(() => {
        result.current.onChunk("test");
      });

      unmount();

      expect(clearTimeoutSpy).toHaveBeenCalled();
    });

    it("should not call onUpdate after unmount", () => {
      const { result, unmount } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 10),
      );

      act(() => {
        result.current.onChunk("test");
      });

      unmount();

      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(mockOnUpdate).not.toHaveBeenCalled();
    });
  });

  describe("performance considerations", () => {
    it("should not create new onChunk function on every render", () => {
      const { result, rerender } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, 1),
      );

      const firstOnChunk = result.current.onChunk;

      rerender();

      expect(result.current.onChunk).toBe(firstOnChunk);
    });

    it("should create new onChunk function when delay changes", () => {
      let delay = 1;
      const { result, rerender } = renderHook(() =>
        useStreamingChunkBuffer(mockOnUpdate, delay),
      );

      const firstOnChunk = result.current.onChunk;

      delay = 10;
      rerender();

      expect(result.current.onChunk).not.toBe(firstOnChunk);
    });

    it("should create new flush function when onUpdate changes", () => {
      let onUpdate = mockOnUpdate;
      const { result, rerender } = renderHook(() =>
        useStreamingChunkBuffer(onUpdate, 1),
      );

      const firstFlush = result.current.flush;

      onUpdate = vi.fn();
      rerender();

      expect(result.current.flush).not.toBe(firstFlush);
    });
  });
});
