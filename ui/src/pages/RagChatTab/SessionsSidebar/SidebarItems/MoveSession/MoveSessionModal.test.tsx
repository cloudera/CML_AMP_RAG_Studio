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

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import MoveSessionModal from "./MoveSessionModal";
import { Session } from "src/api/sessionApi";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import messageQueue from "src/utils/messageQueue";
import { ModalHook } from "src/utils/useModal";

// Mock dependencies
vi.mock("src/api/dataSourceApi.ts", () => ({
  useGetDataSourcesQuery: vi.fn(() => ({
    data: [
      {
        id: 1,
        name: "Data Source 1",
        description: "Description 1",
      },
      {
        id: 2,
        name: "Data Source 2",
        description: "Description 2",
      },
    ],
    isLoading: false,
    isSuccess: false,
  })),
}));

vi.mock("src/api/projectsApi.ts", () => ({
  useGetProjects: vi.fn(() => ({
    data: [
      {
        id: 2,
        name: "Target Project",
        description: "Target project description",
        timeCreated: 0,
        timeUpdated: 0,
        createdById: 1,
        updatedById: 1,
      },
    ],
    isLoading: false,
    isSuccess: false,
  })),
  useAddDataSourceToProject: vi.fn(() => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
    isSuccess: false,
  })),
  useGetDataSourcesForProject: vi.fn(() => ({
    data: [],
    isLoading: false,
    isSuccess: false,
  })),
}));

vi.mock("src/utils/messageQueue.ts", () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("./useMoveSession.ts", () => ({
  useMoveSession: vi.fn(() => ({
    isPending: false,
    isSuccess: false,
  })),
}));

// Mock the child components to simplify testing
vi.mock("./CurrentSession.tsx", () => ({
  default: vi.fn(() => (
    <div data-testid="current-session">Current Session</div>
  )),
}));

vi.mock("./TransferItems.tsx", () => ({
  default: vi.fn(() => <div data-testid="transfer-items">Transfer Items</div>),
}));

vi.mock("./ProjectSelection.tsx", () => ({
  default: vi.fn(() => (
    <div data-testid="project-selection">Project Selection</div>
  )),
}));

describe.skip("MoveSessionModal", () => {
  let queryClient: QueryClient;
  const mockSession: Session = {
    id: 1,
    name: "Test Session",
    projectId: 1,
    dataSourceIds: [1, 2],
    timeCreated: 0,
    timeUpdated: 0,
    createdById: "1",
    updatedById: "1",
    responseChunks: 3,
    lastInteractionTime: 0,
    queryConfiguration: {
      enableHyde: false,
      enableSummaryFilter: false,
    },
  };

  const mockModalHook: ModalHook = {
    isModalOpen: true,
    showModal: vi.fn(),
    handleCancel: vi.fn(),
    setIsModalOpen: vi.fn(),
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    vi.clearAllMocks();
  });

  it("renders the modal with all components when open", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MoveSessionModal moveModal={mockModalHook} session={mockSession} />,
      </QueryClientProvider>,
    );

    // Check that the modal title is rendered
    expect(screen.getByText("Move session?")).toBeTruthy();

    // Check that all child components are rendered
    expect(screen.getByTestId("current-session")).toBeTruthy();
    expect(screen.getByTestId("transfer-items")).toBeTruthy();
    expect(screen.getByTestId("project-selection")).toBeTruthy();

    // Check that the footer text is rendered
    expect(
      screen.getByText(/Moving this session will add a new knowledge base/),
    ).toBeTruthy();
  });

  it("calls handleCancel when cancel button is clicked", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MoveSessionModal moveModal={mockModalHook} session={mockSession} />
      </QueryClientProvider>,
    );

    // Find and click the cancel button
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    fireEvent.click(cancelButton);

    // Check that handleCancel was called
    expect(mockModalHook.handleCancel).toHaveBeenCalled();
  });

  it("shows error message when trying to move without selecting a project", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MoveSessionModal moveModal={mockModalHook} session={mockSession} />
      </QueryClientProvider>,
    );

    // Find and click the OK button
    const okButton = screen.getByRole("button", { name: /move it/i });
    fireEvent.click(okButton);

    // Check that error message was shown
    await waitFor(() => {
      expect(messageQueue.error).toHaveBeenCalledWith(
        "Please select a project",
      );
    });
  });
});
