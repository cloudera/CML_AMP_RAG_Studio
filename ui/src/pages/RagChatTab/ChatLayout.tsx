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

import { Divider, Flex, Layout } from "antd";
import RagChat from "pages/RagChatTab/RagChat.tsx";
import { SessionSidebar } from "pages/RagChatTab/Sessions/SessionSidebar.tsx";
import { getSessionsQueryOptions, Session } from "src/api/sessionApi.ts";
import { groupBy } from "lodash";
import { format } from "date-fns";
import { useParams } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useChatHistoryQuery } from "src/api/chatApi.ts";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  getDefaultProjectQueryOptions,
  useGetDataSourcesForProject,
} from "src/api/projectsApi.ts";

const getSessionForSessionId = (sessionId?: string, sessions?: Session[]) => {
  return sessions?.find((session) => session.id.toString() === sessionId);
};

function ChatLayout() {
  const { data: defaultProject } = useSuspenseQuery(
    getDefaultProjectQueryOptions,
  );

  const { data: sessions } = useSuspenseQuery(getSessionsQueryOptions);

  const { sessionId } = useParams({ strict: false });
  const activeSession = getSessionForSessionId(sessionId, sessions);
  const { data: dataSources, status: dataSourcesStatus } =
    useGetDataSourcesForProject(activeSession?.projectId);
  const [excludeKnowledgeBase, setExcludeKnowledgeBase] = useState(false);
  const { status: chatHistoryStatus, data: chatHistory } = useChatHistoryQuery(
    sessionId ? +sessionId : 0,
  );

  const dataSourceId = activeSession?.dataSourceIds[0];

  const dataSourceSize = useMemo(() => {
    return (
      dataSources?.find((ds) => ds.id === dataSourceId)?.totalDocSize ?? null
    );
  }, [dataSources, dataSourceId]);

  const sessionsByDate = groupBy(sessions, (session) => {
    const relevantTime = session.lastInteractionTime || session.timeUpdated;
    return format(relevantTime * 1000, "yyyyMMdd");
  });

  return (
    <RagChatContext.Provider
      value={{
        excludeKnowledgeBaseState: [
          excludeKnowledgeBase,
          setExcludeKnowledgeBase,
        ],
        chatHistoryQuery: { chatHistory, chatHistoryStatus },
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
      >
        <div style={{ paddingTop: 20 }}>
          <SessionSidebar sessionsByDate={sessionsByDate} />
        </div>
        <Divider
          key="chatLayoutDivider"
          type="vertical"
          style={{ height: "100%", padding: 0, margin: 0 }}
        />
        <Flex style={{ width: "100%" }} justify="center">
          <Flex
            vertical
            align="center"
            justify="center"
            style={{
              maxWidth: 900,
              width: "100%",
              margin: 20,
            }}
            gap={20}
          >
            <RagChat />
          </Flex>
        </Flex>
      </Layout>
    </RagChatContext.Provider>
  );
}

export default ChatLayout;
