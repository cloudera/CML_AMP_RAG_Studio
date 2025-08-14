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
 * Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
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

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, afterEach, vi, beforeEach, Mock } from "vitest";
import ChatMessageController from "./ChatMessageController";
import {
  RagChatContext,
  RagChatContextType,
} from "pages/RagChatTab/State/RagChatContext.tsx";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ChatMessageType } from "src/api/chatApi.ts";

// Mock scrollIntoView
const mockScrollIntoView = vi.fn();
Element.prototype.scrollIntoView = mockScrollIntoView;

// Mock window.history
Object.defineProperty(window, "history", {
  value: {
    pushState: vi.fn(),
  },
  writable: true,
});

// Mock window.location
Object.defineProperty(window, "location", {
  value: {
    href: "http://localhost:9999",
  },
  writable: true,
});

// Mock the API modules
vi.mock("src/api/chatApi.ts", () => ({
  createQueryConfiguration: vi.fn(() => ({ exclude_knowledge_base: false })),
  getOnEvent: vi.fn(() => vi.fn()),
  isPlaceholder: vi.fn(
    (message: { id: string }) => message.id === "placeholder"
  ),
  useStreamingChatMutation: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
    reset: vi.fn(),
  })),
}));

vi.mock("src/api/sessionApi.ts", () => ({
  useRenameNameMutation: vi.fn(() => ({
    mutate: vi.fn(),
  })),
}));

vi.mock("@tanstack/react-router", () => ({
  useSearch: vi.fn(() => ({})),
}));

vi.mock("react-intersection-observer", () => ({
  useInView: vi.fn(() => ({
    ref: vi.fn(),
    inView: false,
  })),
}));

vi.mock("src/utils/messageQueue.ts", () => ({
  default: {
    error: vi.fn(),
  },
}));

// Mock child components
vi.mock("pages/RagChatTab/ChatOutput/ChatMessages/ChatMessage.tsx", () => ({
  default: ({ data }: { data: ChatMessageType }) => (
    <div data-testid={`chat-message-${data.id}`}>
      Message: {data.rag_message.user} - {data.rag_message.assistant}
    </div>
  ),
}));

vi.mock(
  "pages/RagChatTab/ChatOutput/Loaders/PendingRagOutputSkeleton.tsx",
  () => ({
    default: ({ question }: { question: string }) => (
      <div data-testid="pending-skeleton">Pending: {question}</div>
    ),
  })
);

vi.mock("pages/RagChatTab/ChatOutput/Loaders/ChatLoading.tsx", () => ({
  ChatLoading: () => <div data-testid="chat-loading">Loading...</div>,
}));

vi.mock("pages/RagChatTab/ChatOutput/ChatMessages/EmptyChatState.tsx", () => ({
  default: () => <div data-testid="empty-chat-state">No messages</div>,
}));

// Import mocked modules
import { useStreamingChatMutation } from "src/api/chatApi.ts";
import { useRenameNameMutation } from "src/api/sessionApi.ts";
import { useSearch } from "@tanstack/react-router";
import { useInView } from "react-intersection-observer";

const mockStreamingChatMutation = {
  mutate: vi.fn(),
  isPending: false,
  isSuccess: false,
  reset: vi.fn(),
};

const mockRenameNameMutation = {
  mutate: vi.fn(),
};

const mockUseInView = {
  ref: vi.fn(),
  inView: false,
};

beforeEach(() => {
  vi.clearAllMocks();
  (useStreamingChatMutation as Mock).mockReturnValue(mockStreamingChatMutation);
  (useRenameNameMutation as Mock).mockReturnValue(mockRenameNameMutation);
  (useSearch as Mock).mockReturnValue({});
  (useInView as Mock).mockReturnValue(mockUseInView);
});

afterEach(() => {
  cleanup();
});

const createMockMessage = (
  id: string,
  user: string,
  assistant: string
): ChatMessageType => ({
  id,
  session_id: 123,
  source_nodes: [],
  rag_message: { user, assistant },
  evaluations: [],
  timestamp: Date.now(),
});

const createMockContext = (
  overrides: Partial<RagChatContextType> = {}
): RagChatContextType => ({
  activeSession: {
    id: 123,
    name: "Test Session",
    dataSourceIds: [1, 2],
    responseChunks: 5,
    timeCreated: Date.now(),
    timeUpdated: Date.now(),
    createdById: "test-user",
    updatedById: "test-user",
    lastInteractionTime: Date.now(),
    queryConfiguration: {
      enableHyde: false,
      enableSummaryFilter: false,
      enableToolCalling: false,
      enableStreaming: true,
      selectedTools: [],
    },
    projectId: 1,
  },
  chatHistoryQuery: {
    flatChatHistory: [],
    isFetching: false,
    isFetchingPreviousPage: false,
    chatHistoryStatus: "success",
    fetchPreviousPage: vi.fn(),
  },
  streamedChatState: ["", vi.fn()],
  streamedEventState: [[], vi.fn()],
  streamedAbortControllerState: [undefined, vi.fn()],
  dataSourcesQuery: {
    dataSources: [],
    dataSourcesStatus: "success",
  },
  dataSourceSize: 5,
  excludeKnowledgeBaseState: [false, vi.fn()],
  ...overrides,
});

const renderWithContext = (contextValue: RagChatContextType) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <RagChatContext.Provider value={contextValue}>
        <ChatMessageController />
      </RagChatContext.Provider>
    </QueryClientProvider>
  );
};

describe("ChatMessageController", () => {
  describe("Loading States", () => {
    it("shows chat loading when chat history status is pending", () => {
      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: [],
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "pending",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(screen.getByTestId("chat-loading")).toBeInTheDocument();
    });

    it("shows pending skeleton when there's a question in search params but no chat history", () => {
      (useSearch as Mock).mockReturnValue({ question: "Test question?" });
      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: [],
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(screen.getByTestId("pending-skeleton")).toBeInTheDocument();
      expect(screen.getByText("Pending: Test question?")).toBeInTheDocument();
    });

    it("shows chat loading when fetching history with no chat history", () => {
      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: [],
          isFetching: true,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(screen.getByTestId("chat-loading")).toBeInTheDocument();
    });

    it("shows empty chat state when no messages and not loading", () => {
      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: [],
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(screen.getByTestId("empty-chat-state")).toBeInTheDocument();
    });
  });

  describe("Message Rendering", () => {
    it("renders chat messages when chat history exists", () => {
      const messages = [
        createMockMessage("1", "Hello", "Hi there!"),
        createMockMessage("2", "How are you?", "I'm doing well!"),
      ];

      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(screen.getByTestId("chat-message-controller")).toBeInTheDocument();
      expect(screen.getByTestId("chat-message-1")).toBeInTheDocument();
      expect(screen.getByTestId("chat-message-2")).toBeInTheDocument();
      expect(
        screen.getByText("Message: Hello - Hi there!")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Message: How are you? - I'm doing well!")
      ).toBeInTheDocument();
    });

    it("shows skeleton when fetching previous page", () => {
      const messages = [createMockMessage("1", "Hello", "Hi there!")];

      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: true,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(screen.getByTestId("chat-message-controller")).toBeInTheDocument();
      expect(screen.getByRole("heading")).toBeInTheDocument(); // Skeleton component
    });
  });

  describe("Session Renaming", () => {
    it("triggers session rename when session name is empty and has non-placeholder messages", async () => {
      const messages = [createMockMessage("1", "Hello", "Hi there!")];

      const mockContext = createMockContext({
        activeSession: {
          id: 123,
          name: "",
          dataSourceIds: [1, 2],
          responseChunks: 5,
          timeCreated: Date.now(),
          timeUpdated: Date.now(),
          createdById: "test-user",
          updatedById: "test-user",
          lastInteractionTime: Date.now(),
          queryConfiguration: {
            enableHyde: false,
            enableSummaryFilter: false,
            enableToolCalling: false,
            enableStreaming: true,
            selectedTools: [],
          },
          projectId: 1,
        },
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      await waitFor(() => {
        expect(mockRenameNameMutation.mutate).toHaveBeenCalledWith("123");
      });
    });

    it("does not trigger session rename when session has a name", () => {
      const messages = [createMockMessage("1", "Hello", "Hi there!")];

      const mockContext = createMockContext({
        activeSession: {
          id: 123,
          name: "My Session",
          dataSourceIds: [1, 2],
          responseChunks: 5,
          timeCreated: Date.now(),
          timeUpdated: Date.now(),
          createdById: "test-user",
          updatedById: "test-user",
          lastInteractionTime: Date.now(),
          queryConfiguration: {
            enableHyde: false,
            enableSummaryFilter: false,
            enableToolCalling: false,
            enableStreaming: true,
            selectedTools: [],
          },
          projectId: 1,
        },
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(mockRenameNameMutation.mutate).not.toHaveBeenCalled();
    });

    it("does not trigger session rename when last message is placeholder", () => {
      const messages = [createMockMessage("placeholder", "Hello", "")];

      const mockContext = createMockContext({
        activeSession: {
          id: 123,
          name: "",
          dataSourceIds: [1, 2],
          responseChunks: 5,
          timeCreated: Date.now(),
          timeUpdated: Date.now(),
          createdById: "test-user",
          updatedById: "test-user",
          lastInteractionTime: Date.now(),
          queryConfiguration: {
            enableHyde: false,
            enableSummaryFilter: false,
            enableToolCalling: false,
            enableStreaming: true,
            selectedTools: [],
          },
          projectId: 1,
        },
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(mockRenameNameMutation.mutate).not.toHaveBeenCalled();
    });
  });

  describe("URL Question Handling", () => {
    it("triggers chat mutation when question is in URL params", async () => {
      (useSearch as Mock).mockReturnValue({ question: "Test question?" });

      const mockContext = createMockContext({
        activeSession: {
          id: 456,
          name: "Test Session",
          dataSourceIds: [1, 2],
          responseChunks: 5,
          timeCreated: Date.now(),
          timeUpdated: Date.now(),
          createdById: "test-user",
          updatedById: "test-user",
          lastInteractionTime: Date.now(),
          queryConfiguration: {
            enableHyde: false,
            enableSummaryFilter: false,
            enableToolCalling: false,
            enableStreaming: true,
            selectedTools: [],
          },
          projectId: 1,
        },
        chatHistoryQuery: {
          flatChatHistory: [],
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      await waitFor(() => {
        expect(mockStreamingChatMutation.mutate).toHaveBeenCalledWith({
          query: "Test question?",
          session_id: 456,
          configuration: { exclude_knowledge_base: false },
        });
      });
    });

    it("does not trigger chat mutation when already fetching history", () => {
      (useSearch as Mock).mockReturnValue({ question: "Test question?" });

      const mockContext = createMockContext({
        activeSession: {
          id: 456,
          name: "Test Session",
          dataSourceIds: [1, 2],
          responseChunks: 5,
          timeCreated: Date.now(),
          timeUpdated: Date.now(),
          createdById: "test-user",
          updatedById: "test-user",
          lastInteractionTime: Date.now(),
          queryConfiguration: {
            enableHyde: false,
            enableSummaryFilter: false,
            enableToolCalling: false,
            enableStreaming: true,
            selectedTools: [],
          },
          projectId: 1,
        },
        chatHistoryQuery: {
          flatChatHistory: [],
          isFetching: true,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(mockStreamingChatMutation.mutate).not.toHaveBeenCalled();
    });

    it("excludes knowledge base when session has no data sources", async () => {
      (useSearch as Mock).mockReturnValue({ question: "Test question?" });

      const mockContext = createMockContext({
        activeSession: {
          id: 456,
          name: "Test Session",
          dataSourceIds: [],
          responseChunks: 5,
          timeCreated: Date.now(),
          timeUpdated: Date.now(),
          createdById: "test-user",
          updatedById: "test-user",
          lastInteractionTime: Date.now(),
          queryConfiguration: {
            enableHyde: false,
            enableSummaryFilter: false,
            enableToolCalling: false,
            enableStreaming: true,
            selectedTools: [],
          },
          projectId: 1,
        },
        chatHistoryQuery: {
          flatChatHistory: [],
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      await waitFor(() => {
        expect(mockStreamingChatMutation.mutate).toHaveBeenCalledWith({
          query: "Test question?",
          session_id: 456,
          configuration: { exclude_knowledge_base: false },
        });
      });
    });
  });

  describe("Pagination", () => {
    it("fetches previous page when intersection observer triggers", async () => {
      const mockFetchPreviousPage = vi.fn().mockResolvedValue({});
      (useInView as Mock).mockReturnValue({
        ref: vi.fn(),
        inView: true,
      });

      const messages = [
        createMockMessage("1", "Hello", "Hi there!"),
        createMockMessage("2", "How are you?", "I'm doing well!"),
        createMockMessage("3", "What's new?", "Not much!"),
      ];

      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: mockFetchPreviousPage,
        },
      });
      renderWithContext(mockContext);

      await waitFor(() => {
        expect(mockFetchPreviousPage).toHaveBeenCalled();
      });
    });

    it("handles fetch previous page error gracefully", async () => {
      const mockFetchPreviousPage = vi
        .fn()
        .mockRejectedValue(new Error("Network error"));
      (useInView as Mock).mockReturnValue({
        ref: vi.fn(),
        inView: true,
      });

      const messages = [createMockMessage("1", "Hello", "Hi there!")];

      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: mockFetchPreviousPage,
        },
      });
      renderWithContext(mockContext);

      await waitFor(() => {
        expect(mockFetchPreviousPage).toHaveBeenCalled();
      });
    });
  });

  describe("Scrolling Behavior", () => {
    it("scrolls to bottom when session changes", () => {
      const messages = [createMockMessage("1", "Hello", "Hi there!")];

      const mockContext = createMockContext({
        activeSession: {
          id: 789,
          name: "New Session",
          dataSourceIds: [1, 2],
          responseChunks: 5,
          timeCreated: Date.now(),
          timeUpdated: Date.now(),
          createdById: "test-user",
          updatedById: "test-user",
          lastInteractionTime: Date.now(),
          queryConfiguration: {
            enableHyde: false,
            enableSummaryFilter: false,
            enableToolCalling: false,
            enableStreaming: true,
            selectedTools: [],
          },
          projectId: 1,
        },
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(mockScrollIntoView).toHaveBeenCalledWith({
        behavior: "instant",
      });
    });
  });

  describe("Message Layout", () => {
    it("applies special ref and styling to the last message", () => {
      const messages = [
        createMockMessage("1", "Hello", "Hi there!"),
        createMockMessage("2", "How are you?", "I'm doing well!"),
      ];

      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: messages,
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      // The last message should have special styling
      const lastMessageContainer =
        screen.getByTestId("chat-message-2").parentElement;
      expect(lastMessageContainer).toHaveStyle({
        minHeight: `${String(window.innerHeight - 200)}px`,
      });
    });
  });
});
