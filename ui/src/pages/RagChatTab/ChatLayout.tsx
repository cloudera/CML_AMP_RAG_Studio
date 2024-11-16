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

import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { Divider, Flex, Layout } from "antd";
import { format } from "date-fns";
import { groupBy } from "lodash";
import RagChat from "pages/RagChatTab/RagChat.tsx";
import { SessionSidebar } from "pages/RagChatTab/Sessions/SessionSidebar.tsx";
import {
  defaultQueryConfig,
  RagChatContext,
} from "pages/RagChatTab/State/RagChatContext.tsx";
import { useEffect, useMemo, useState } from "react";
import { QueryConfiguration, useChatHistoryQuery } from "src/api/chatApi.ts";
import { useGetDataSourcesQuery } from "src/api/dataSourceApi.ts";
import { getLlmModelsQueryOptions } from "src/api/modelsApi.ts";
import { getSessionsQueryOptions } from "src/api/sessionApi.ts";
import { Session } from "src/services/api/api";

const getSessionForSessionId = (sessionId?: string, sessions?: Session[]) => {
  return sessions?.find((session) => session.id.toString() === sessionId);
};

const getDataSourceIdForSession = (session?: Session) => {
  return session?.data_source_ids[0];
};

function ChatLayout() {
  const { data: sessions } = useSuspenseQuery(getSessionsQueryOptions);
  const { data: llmModels } = useSuspenseQuery(getLlmModelsQueryOptions);
  const { sessionId } = useParams({ strict: false });
  const activeSession = getSessionForSessionId(sessionId, sessions);
  const dataSourceId = getDataSourceIdForSession(activeSession);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const { data: dataSources, status: dataSourcesStatus } =
    useGetDataSourcesQuery();
  const [queryConfiguration, setQueryConfiguration] =
    useState<QueryConfiguration>(defaultQueryConfig);
  const { status: chatHistoryStatus, data: chatHistory } = useChatHistoryQuery(
    sessionId?.toString() ?? ""
  );
  const dataSourceSize = useMemo(() => {
    return (
      dataSources?.find((ds) => ds.id === dataSourceId)?.status
        .total_doc_size ?? null
    );
  }, [dataSources, dataSourceId]);

  useEffect(() => {
    setCurrentQuestion("");
  }, [sessionId]);

  useEffect(() => {
    if (llmModels.length) {
      setQueryConfiguration((prev) => ({
        ...prev,
        model_name: llmModels[0].model_id,
      }));
    }
  }, [llmModels, setQueryConfiguration]);

  const sessionsByDate = groupBy(sessions, (session) => {
    const relevantTime = session.last_interaction_time || session.time_updated;
    return format(new Date(relevantTime), "yyyyMMdd");
  });

  return (
    <RagChatContext.Provider
      value={{
        dataSourceId,
        queryConfiguration,
        setQueryConfiguration,
        setCurrentQuestion,
        currentQuestion,
        chatHistory,
        dataSourceSize,
        chatHistoryStatus,
        dataSourcesStatus,
        activeSession,
        dataSources: dataSources ?? [],
      }}
    >
      <Layout
        style={{
          width: "100%",
          height: "100%",
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
