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

import { Divider, Layout } from "antd";
import { SessionSidebar } from "pages/RagChatTab/SessionsSidebar/SessionSidebar.tsx";
import { Session, useGetSessions } from "src/api/sessionApi.ts";
import { Outlet, useParams } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  ChatMessageType,
  ChatEvent,
  useChatHistoryQuery,
} from "src/api/chatApi.ts";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import {
  getDefaultProjectQueryOptions,
  useGetDataSourcesForProject,
} from "src/api/projectsApi.ts";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useFlattenChatHistory } from "pages/RagChatTab/hooks/useFlattenChatHistory.tsx";

const getSessionForSessionId = (sessionId?: string, sessions?: Session[]) => {
  return sessions?.find((session) => session.id.toString() === sessionId);
};

function ChatLayout() {
  const { data: allSessions } = useGetSessions();

  const sessions = allSessions ?? [];

  const { projectId: routeProjectId, sessionId } = useParams({ strict: false });
  const { data: defaultProject } = useSuspenseQuery(
    getDefaultProjectQueryOptions,
  );

  const activeSession = getSessionForSessionId(sessionId, sessions);
  const projectId: string =
    routeProjectId ??
    activeSession?.projectId.toString() ??
    defaultProject.id.toString();

  const { data: dataSources, status: dataSourcesStatus } =
    useGetDataSourcesForProject(+projectId);
  const [excludeKnowledgeBase, setExcludeKnowledgeBase] = useState(false);
  const [streamedChat, setStreamedChat] = useState("");
  const [streamedEvent, setStreamedEvent] = useState<ChatEvent[]>([]);
  const [streamedAbortController, setStreamedAbortController] =
    useState<AbortController>();
  const {
    status: chatHistoryStatus,
    data: chatHistory,
    fetchPreviousPage,
    isFetching,
    isFetchingPreviousPage,
  } = useChatHistoryQuery({
    session_id: sessionId ? +sessionId : 0,
    offset: 0,
  });

  const flatChatHistory: ChatMessageType[] = useFlattenChatHistory(chatHistory);

  const dataSourceId = activeSession?.dataSourceIds[0];

  const dataSourceSize = useMemo(() => {
    return (
      dataSources?.find((ds) => ds.id === dataSourceId)?.totalDocSize ?? null
    );
  }, [dataSources, dataSourceId]);

  return (
    <RagChatContext.Provider
      value={{
        excludeKnowledgeBaseState: [
          excludeKnowledgeBase,
          setExcludeKnowledgeBase,
        ],
        chatHistoryQuery: {
          flatChatHistory,
          chatHistoryStatus,
          fetchPreviousPage,
          isFetching,
          isFetchingPreviousPage,
        },
        streamedChatState: [streamedChat, setStreamedChat],
        streamedEventState: [streamedEvent, setStreamedEvent],
        streamedAbortControllerState: [
          streamedAbortController,
          setStreamedAbortController,
        ],
        dataSourceSize,
        dataSourcesQuery: {
          dataSources: dataSources ?? [],
          dataSourcesStatus: dataSourcesStatus,
        },
        activeSession,
      }}
    >
      <Layout
        style={{
          width: "100%",
          height: "95vh",
          transition: "height 0.5s",
        }}
        hasSider={true}
      >
        <SessionSidebar sessions={sessions} />
        <Divider
          key="chatLayoutDivider"
          type="vertical"
          style={{ height: "100%", padding: 0, margin: 0 }}
        />
        <Outlet />
      </Layout>
    </RagChatContext.Provider>
  );
}

export default ChatLayout;
