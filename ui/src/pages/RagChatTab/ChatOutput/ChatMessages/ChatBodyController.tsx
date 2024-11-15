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

import { useParams } from "@tanstack/react-router";
import { Result } from "antd";
import ChatMessageController from "pages/RagChatTab/ChatOutput/ChatMessages/ChatMessageController.tsx";
import { ChatLoading } from "pages/RagChatTab/ChatOutput/Loaders/ChatLoading.tsx";
import EmptyChatState from "pages/RagChatTab/ChatOutput/Placeholders/EmptyChatState.tsx";
import NoDataSourceForSession from "pages/RagChatTab/ChatOutput/Placeholders/NoDataSourceForSession.tsx";
import NoDataSourcesState from "pages/RagChatTab/ChatOutput/Placeholders/NoDataSourcesState.tsx";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { useContext } from "react";
import NoSessionState from "../Placeholders/NoSessionState";

const ChatBodyController = () => {
  const {
    currentQuestion,
    chatHistory,
    dataSourcesStatus,
    chatHistoryStatus,
    dataSourceSize,
    dataSources,
    activeSession,
  } = useContext(RagChatContext);
  const { sessionId } = useParams({ strict: false });

  if (!sessionId && dataSources.length > 0) {
    return <NoSessionState />;
  }

  if (dataSourcesStatus === "pending" || chatHistoryStatus === "pending") {
    return <ChatLoading />;
  }

  if (dataSourcesStatus === "error" || chatHistoryStatus === "error") {
    return <Result title="We encountered an error" />;
  }

  const chatHistoryExists = chatHistory.length > 0;

  if (chatHistoryExists) {
    return <ChatMessageController />;
  }

  if (dataSources.length === 0) {
    return <NoDataSourcesState />;
  }

  const currentDataSource = dataSources.find((dataSource) => {
    return dataSource.id === activeSession?.data_source_ids[0];
  });

  if (!currentDataSource) {
    return <NoDataSourceForSession />;
  }

  if (currentQuestion && dataSourceSize) {
    return <ChatMessageController />;
  }

  return <EmptyChatState dataSourceSize={dataSourceSize ?? 0} />;
};

export default ChatBodyController;
