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

import { describe, it, expect, vi, beforeEach } from "vitest";
import { useMoveSession } from "./useMoveSession";
import { renderHook } from "@testing-library/react";
import { Session } from "src/api/sessionApi";
import { Project } from "src/api/projectsApi";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import messageQueue from "src/utils/messageQueue";
import React from "react";
import { ModalHook } from "src/utils/useModal";

// Mock dependencies
vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual("@tanstack/react-query");
  return {
    ...actual,
    useQueryClient: vi.fn(() => ({
      invalidateQueries: vi.fn().mockResolvedValue(undefined),
    })),
  };
});

vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual("@tanstack/react-router");
  return {
    ...actual,
    useNavigate: vi.fn(() => {
      return vi.fn(() => Promise.resolve(true));
    }),
  };
});

vi.mock("src/utils/messageQueue", () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("src/api/sessionApi", () => ({
  useUpdateSessionMutation: vi.fn(({ onSuccess }) => ({
    mutate: vi.fn((session) => {
      // Type assertion to avoid unsafe call warning
      (onSuccess as (data: unknown) => void)(session);
    }),
    isPending: false,
  })),
}));

describe("useMoveSession", () => {
  let queryClient: QueryClient;
  let wrapper: ({ children }: { children: ReactNode }) => React.JSX.Element;

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
      enableToolCalling: false,
      enableStreaming: true,
      selectedTools: [],
    },
  };

  const mockProjects: Project[] = [
    {
      id: 2,
      name: "Target Project",
      defaultProject: false,
      timeCreated: 0,
      timeUpdated: 0,
      createdById: "1",
      updatedById: "1",
    },
  ];

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

    wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    vi.clearAllMocks();
  });

  it("should return a mutation function", () => {
    const { result } = renderHook(
      () =>
        useMoveSession({
          session: mockSession,
          selectedProject: 2,
          projects: mockProjects,
          handleCancel: mockModalHook.handleCancel,
        }),
      { wrapper }
    );

    expect(result.current).toBeDefined();
    expect(result.current.mutate).toBeDefined();
  });

  it("should show success message and close modal on successful update", () => {
    const { result } = renderHook(
      () =>
        useMoveSession({
          session: mockSession,
          selectedProject: 2,
          projects: mockProjects,
          handleCancel: mockModalHook.handleCancel,
        }),
      { wrapper }
    );

    result.current.mutate(mockSession);

    expect(messageQueue.success).toHaveBeenCalledWith(
      `Session ${mockSession.name} moved to project ${mockProjects[0].name}`
    );
    expect(mockModalHook.handleCancel).toHaveBeenCalled();
  });

  it("should show error message when project is not found", () => {
    const { result } = renderHook(
      () =>
        useMoveSession({
          session: mockSession,
          selectedProject: 3, // Non-existent project ID
          projects: mockProjects,
          handleCancel: mockModalHook.handleCancel,
        }),
      { wrapper }
    );

    result.current.mutate(mockSession);

    expect(messageQueue.error).toHaveBeenCalledWith("Failed to find project");
    expect(mockModalHook.handleCancel).not.toHaveBeenCalled();
  });
});
