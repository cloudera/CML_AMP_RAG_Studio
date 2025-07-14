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

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, afterEach, vi, beforeEach, Mock } from "vitest";
import RagChatQueryInput from "./RagChatQueryInput";
import {
  RagChatContext,
  RagChatContextType,
} from "pages/RagChatTab/State/RagChatContext.tsx";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock the API modules
vi.mock("src/api/chatApi.ts", () => ({
  createQueryConfiguration: vi.fn(() => ({ exclude_knowledge_base: false })),
  getOnEvent: vi.fn(() => vi.fn()),
  useStreamingChatMutation: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
    reset: vi.fn(),
  })),
}));

vi.mock("src/api/modelsApi.ts", () => ({
  getLlmModelsQueryOptions: {
    queryKey: ["llmModels"],
    queryFn: () =>
      Promise.resolve([
        { model_id: "test-llm", tool_calling_supported: false },
      ]),
  },
  useGetLlmModels: vi.fn(() => ({
    data: [{ model_id: "test-llm" }],
    isFetching: false,
    error: null,
  })),
}));

vi.mock("src/api/ragQueryApi.ts", () => ({
  useSuggestQuestions: vi.fn(() => ({
    data: { suggested_questions: ["Sample question 1", "Sample question 2"] },
    isFetching: false,
    error: null,
  })),
}));

vi.mock("@tanstack/react-router", () => ({
  useParams: vi.fn(() => ({ sessionId: "123" })),
  useSearch: vi.fn(() => ({ question: undefined })),
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useSuspenseQuery: vi.fn(() => ({
      data: [{ model_id: "test-llm", tool_calling_supported: false }],
    })),
  };
});

vi.mock("src/utils/useModal.ts", () => ({
  default: vi.fn(() => ({
    isModalOpen: false,
    openModal: vi.fn(),
    closeModal: vi.fn(),
  })),
}));

// Mock child components
vi.mock(
  "pages/RagChatTab/FooterComponents/SuggestedQuestionsFooter.tsx",
  () => ({
    default: ({ handleChat }: { handleChat: (query: string) => void }) => {
      return (
        <div data-testid="suggested-questions">
          <button
            onClick={() => {
              handleChat("suggested question");
            }}
          >
            Suggested Question
          </button>
        </div>
      );
    },
  }),
);

vi.mock("pages/RagChatTab/FooterComponents/ToolsManager.tsx", () => ({
  default: () => {
    return <div data-testid="tools-manager">Tools Manager</div>;
  },
}));

vi.mock("pages/RagChatTab/FooterComponents/ChatSessionDocuments.tsx", () => ({
  default: () => {
    return <div data-testid="chat-session-documents">Session Documents</div>;
  },
}));

vi.mock("pages/RagChatTab/FooterComponents/ChatSessionDragAndDrop.tsx", () => ({
  ChatSessionDragAndDrop: ({
    isDragging,
    setIsDragging,
  }: {
    isDragging: boolean;
    setIsDragging: (dragging: boolean) => void;
  }) => {
    return (
      <div data-testid="drag-and-drop">
        {isDragging ? "Dragging" : "Not Dragging"}
        <button
          onClick={() => {
            setIsDragging(!isDragging);
          }}
        >
          Toggle Drag
        </button>
      </div>
    );
  },
}));

const mockStreamingChatMutation = {
  mutate: vi.fn(),
  isPending: false,
  isSuccess: false,
  reset: vi.fn(),
};

const mockUseSuggestQuestions = {
  data: { suggested_questions: ["Sample question 1", "Sample question 2"] },
  isFetching: false,
  error: null,
};

// Import the mocked modules to access their mock functions
import { useStreamingChatMutation } from "src/api/chatApi.ts";
import { useSuggestQuestions } from "src/api/ragQueryApi.ts";
import { useParams, useSearch } from "@tanstack/react-router";

beforeEach(() => {
  vi.clearAllMocks();
  (useStreamingChatMutation as Mock).mockReturnValue(mockStreamingChatMutation);
  (useSuggestQuestions as Mock).mockReturnValue(mockUseSuggestQuestions);
  (useParams as Mock).mockReturnValue({ sessionId: "123" });
  (useSearch as Mock).mockReturnValue({ question: undefined });
});

afterEach(() => {
  cleanup();
});

const createMockContext = (
  overrides: Partial<RagChatContextType> = {},
): RagChatContextType => ({
  activeSession: {
    id: 123,
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

const renderWithContext = (
  contextValue: RagChatContextType,
  newSessionCallback = vi.fn(),
) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <RagChatContext.Provider value={contextValue}>
        <RagChatQueryInput newSessionCallback={newSessionCallback} />
      </RagChatContext.Provider>
    </QueryClientProvider>,
  );
};

describe("RagChatQueryInput", () => {
  describe("Basic Rendering", () => {
    it("renders the text area with correct placeholder when data sources exist", () => {
      const mockContext = createMockContext({ dataSourceSize: 5 });
      renderWithContext(mockContext);

      expect(screen.getByPlaceholderText("Ask a question")).toBeInTheDocument();
    });

    it("renders the text area with LLM placeholder when no data sources exist", () => {
      const mockContext = createMockContext({ dataSourceSize: 0 });
      renderWithContext(mockContext);

      expect(
        screen.getByPlaceholderText("Chat with the LLM"),
      ).toBeInTheDocument();
    });

    it("renders send button", () => {
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      const sendButton = screen.getByRole("button", { name: /send/i });
      expect(sendButton).toBeInTheDocument();
    });

    it("renders knowledge base toggle button when data sources exist", () => {
      const mockContext = createMockContext({ dataSourceSize: 5 });
      renderWithContext(mockContext);

      const kbButton = screen.getByRole("button", { name: /database/i });
      expect(kbButton).toBeInTheDocument();
    });

    it("hides knowledge base toggle button when no data sources exist", () => {
      const mockContext = createMockContext({ dataSourceSize: 0 });
      renderWithContext(mockContext);

      const kbButton = screen.queryByRole("button", {
        name: /database/i,
      });
      expect(kbButton).not.toBeInTheDocument();
    });
  });

  describe("Text Input Functionality", () => {
    it("updates input value when user types", async () => {
      const user = userEvent.setup();
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      const textArea = screen.getByPlaceholderText("Ask a question");
      await user.type(textArea, "Hello world");

      expect(textArea).toHaveValue("Hello world");
    });

    it("submits query on Enter key press", async () => {
      const user = userEvent.setup();
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      const textArea = screen.getByPlaceholderText("Ask a question");
      await user.type(textArea, "Test query");
      await user.keyboard("{Enter}");

      expect(mockStreamingChatMutation.mutate).toHaveBeenCalledWith({
        query: "Test query",
        session_id: 123,
        configuration: { exclude_knowledge_base: false },
      });
    });

    it("allows new line on Shift+Enter", async () => {
      const user = userEvent.setup();
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      const textArea = screen.getByPlaceholderText("Ask a question");
      await user.type(textArea, "Line 1");
      await user.keyboard("{Shift>}{Enter}{/Shift}");
      await user.type(textArea, "Line 2");

      expect(textArea).toHaveValue("Line 1\nLine 2");
      expect(mockStreamingChatMutation.mutate).not.toHaveBeenCalled();
    });

    it("does not submit empty or whitespace-only queries", async () => {
      const user = userEvent.setup();
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      const textArea = screen.getByPlaceholderText("Ask a question");
      const sendButton = screen.getByRole("button", { name: /send/i });

      // Test empty string
      await user.click(sendButton);
      expect(mockStreamingChatMutation.mutate).not.toHaveBeenCalled();

      // Test whitespace only
      await user.type(textArea, "   ");
      await user.click(sendButton);
      expect(mockStreamingChatMutation.mutate).not.toHaveBeenCalled();
    });
  });

  describe("Send Button Functionality", () => {
    it("submits query when send button is clicked", async () => {
      const user = userEvent.setup();
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      const textArea = screen.getByPlaceholderText("Ask a question");
      const sendButton = screen.getByRole("button", { name: /send/i });

      await user.type(textArea, "Test query");
      await user.click(sendButton);

      expect(mockStreamingChatMutation.mutate).toHaveBeenCalledWith({
        query: "Test query",
        session_id: 123,
        configuration: { exclude_knowledge_base: false },
      });
    });

    it("replaces send button with stop button when streaming is in progress", () => {
      const mockContext = createMockContext();
      (useStreamingChatMutation as Mock).mockReturnValue({
        ...mockStreamingChatMutation,
        isPending: true,
      });
      renderWithContext(mockContext);

      // Send button should not be present when streaming
      const sendButton = screen.queryByRole("button", { name: /send/i });
      expect(sendButton).not.toBeInTheDocument();

      // Stop button should be present instead
      const stopButton = screen.getByRole("button", { name: /stop/i });
      expect(stopButton).toBeInTheDocument();
    });
  });

  describe("Knowledge Base Toggle", () => {
    it("toggles knowledge base exclusion when clicked", async () => {
      const user = userEvent.setup();
      const mockSetExcludeKnowledgeBase = vi.fn();
      const mockContext = createMockContext({
        dataSourceSize: 5,
        excludeKnowledgeBaseState: [false, mockSetExcludeKnowledgeBase],
      });
      renderWithContext(mockContext);

      const kbButton = screen.getByRole("button", { name: /database/i });
      await user.click(kbButton);

      expect(mockSetExcludeKnowledgeBase).toHaveBeenCalledWith(
        expect.any(Function),
      );
    });

    it("shows correct tooltip when knowledge base is included", () => {
      const mockContext = createMockContext({
        dataSourceSize: 5,
        excludeKnowledgeBaseState: [false, vi.fn()],
      });
      renderWithContext(mockContext);

      const kbButton = screen.getByRole("button", { name: /database/i });
      expect(kbButton).toHaveAttribute("aria-describedby");
    });

    it("shows correct tooltip when knowledge base is excluded", () => {
      const mockContext = createMockContext({
        dataSourceSize: 5,
        excludeKnowledgeBaseState: [true, vi.fn()],
      });
      renderWithContext(mockContext);

      const kbButton = screen.getByRole("button", { name: /database/i });
      expect(kbButton).toHaveAttribute("aria-describedby");
    });
  });

  describe("Streaming State", () => {
    it("shows stop button when streaming is in progress", () => {
      const mockAbortController = new AbortController();
      const mockContext = createMockContext({
        streamedAbortControllerState: [mockAbortController, vi.fn()],
      });
      (useStreamingChatMutation as Mock).mockReturnValue({
        ...mockStreamingChatMutation,
        isPending: true,
      });
      renderWithContext(mockContext);

      const stopButton = screen.getByRole("button", { name: /stop/i });
      expect(stopButton).toBeInTheDocument();
    });

    it("cancels stream when stop button is clicked", async () => {
      const user = userEvent.setup();
      const mockAbortController = new AbortController();
      const mockSetStreamedAbortController = vi.fn();
      const mockSetStreamedChat = vi.fn();
      const mockSetStreamedEvent = vi.fn();

      const mockContext = createMockContext({
        streamedAbortControllerState: [
          mockAbortController,
          mockSetStreamedAbortController,
        ],
        streamedChatState: ["", mockSetStreamedChat],
        streamedEventState: [[], mockSetStreamedEvent],
      });

      (useStreamingChatMutation as Mock).mockReturnValue({
        ...mockStreamingChatMutation,
        isPending: true,
      });

      const abortSpy = vi.spyOn(mockAbortController, "abort");
      renderWithContext(mockContext);

      const stopButton = screen.getByRole("button", { name: /stop/i });
      await user.click(stopButton);

      expect(abortSpy).toHaveBeenCalled();
      expect(mockSetStreamedAbortController).toHaveBeenCalledWith(undefined);
      expect(mockSetStreamedChat).toHaveBeenCalledWith("");
      expect(mockSetStreamedEvent).toHaveBeenCalledWith([]);
      expect(mockStreamingChatMutation.reset).toHaveBeenCalled();
    });

    it("disables text area when streaming is in progress", () => {
      const mockContext = createMockContext();
      (useStreamingChatMutation as Mock).mockReturnValue({
        ...mockStreamingChatMutation,
        isPending: true,
      });
      renderWithContext(mockContext);

      const textArea = screen.getByPlaceholderText("Ask a question");
      expect(textArea).toBeDisabled();
    });
  });

  describe("New Session Callback", () => {
    it("calls newSessionCallback when no session exists", async () => {
      const user = userEvent.setup();
      const newSessionCallback = vi.fn();
      (useParams as Mock).mockReturnValue({ sessionId: undefined });
      const mockContext = createMockContext();
      renderWithContext(mockContext, newSessionCallback);

      const textArea = screen.getByPlaceholderText("Ask a question");
      await user.type(textArea, "Test query");
      await user.click(screen.getByRole("button", { name: /send/i }));

      expect(newSessionCallback).toHaveBeenCalledWith({
        userInput: "Test query",
        selectedDataSourceIds: [],
        inferenceModel: "test-llm",
      });
    });
  });

  describe("Suggested Questions", () => {
    it("renders suggested questions when chat history exists", () => {
      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: [
            {
              id: "1",
              session_id: 123,
              source_nodes: [],
              rag_message: {
                user: "Previous question",
                assistant: "Previous answer",
              },
              evaluations: [],
              timestamp: Date.now(),
              condensed_question: "Previous question",
            },
          ],
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      expect(screen.getByTestId("suggested-questions")).toBeInTheDocument();
    });

    it("does not render suggested questions when chat history is empty", () => {
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

      expect(
        screen.queryByTestId("suggested-questions"),
      ).not.toBeInTheDocument();
    });

    it("handles suggested question clicks", async () => {
      const user = userEvent.setup();
      const mockContext = createMockContext({
        chatHistoryQuery: {
          flatChatHistory: [
            {
              id: "1",
              session_id: 123,
              source_nodes: [],
              rag_message: {
                user: "Previous question",
                assistant: "Previous answer",
              },
              evaluations: [],
              timestamp: Date.now(),
              condensed_question: "Previous question",
            },
          ],
          isFetching: false,
          isFetchingPreviousPage: false,
          chatHistoryStatus: "success",
          fetchPreviousPage: vi.fn(),
        },
      });
      renderWithContext(mockContext);

      const suggestedButton = screen.getByText("Suggested Question");
      await user.click(suggestedButton);

      expect(mockStreamingChatMutation.mutate).toHaveBeenCalledWith({
        query: "suggested question",
        session_id: 123,
        configuration: { exclude_knowledge_base: false },
      });
    });
  });

  describe("Drag and Drop", () => {
    it("renders drag and drop component when not dragging", () => {
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      expect(screen.getByTestId("drag-and-drop")).toBeInTheDocument();
      expect(screen.getByText("Not Dragging")).toBeInTheDocument();
    });

    it("hides input controls when dragging", async () => {
      const user = userEvent.setup();
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      const toggleButton = screen.getByText("Toggle Drag");
      await user.click(toggleButton);

      expect(screen.getByText("Dragging")).toBeInTheDocument();
      expect(
        screen.queryByPlaceholderText("Ask a question"),
      ).not.toBeInTheDocument();
    });
  });

  describe("Error States", () => {
    it("shows error status on text area when data sources have error", () => {
      const mockContext = createMockContext({
        dataSourcesQuery: {
          dataSources: [],
          dataSourcesStatus: "error",
        },
      });
      renderWithContext(mockContext);

      const textArea = screen.getByPlaceholderText("Ask a question");
      expect(textArea).toHaveClass("ant-input-status-error");
    });
  });

  describe("Focus Management", () => {
    it("focuses input on mount", async () => {
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      await waitFor(() => {
        const textArea = screen.getByPlaceholderText("Ask a question");
        expect(textArea).toHaveFocus();
      });
    });
  });

  describe("Child Components", () => {
    it("renders tools manager button", () => {
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      expect(screen.getByTestId("tools-manager")).toBeInTheDocument();
    });

    it("renders chat session documents", () => {
      const mockContext = createMockContext();
      renderWithContext(mockContext);

      expect(screen.getByTestId("chat-session-documents")).toBeInTheDocument();
    });
  });
});
