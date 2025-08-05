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

import { useContext, useEffect, useRef, useCallback, useMemo } from "react";
import { useInView } from "react-intersection-observer";
import ChatMessage from "pages/RagChatTab/ChatOutput/ChatMessages/ChatMessage.tsx";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { Skeleton } from "antd";
import PendingRagOutputSkeleton from "pages/RagChatTab/ChatOutput/Loaders/PendingRagOutputSkeleton.tsx";
import { ChatLoading } from "pages/RagChatTab/ChatOutput/Loaders/ChatLoading.tsx";
import { useSearch } from "@tanstack/react-router";
import messageQueue from "src/utils/messageQueue.ts";
import {
  createQueryConfiguration,
  getOnEvent,
  isPlaceholder,
  useStreamingChatMutation,
} from "src/api/chatApi.ts";
import { useRenameNameMutation } from "src/api/sessionApi.ts";
import EmptyChatState from "pages/RagChatTab/ChatOutput/ChatMessages/EmptyChatState.tsx";

const ChatMessageController = () => {
  const {
    chatHistoryQuery: {
      flatChatHistory,
      chatHistoryStatus,
      fetchPreviousPage,
      isFetching: isFetchingHistory,
      isFetchingPreviousPage,
    },
    streamedChatState: [, setStreamedChat],
    streamedEventState: [, setStreamedEvent],
    streamedAbortControllerState: [, setStreamedAbortControllerState],
    activeSession,
  } = useContext(RagChatContext);
  const { ref: refToFetchNextPage, inView } = useInView({ threshold: 0 });
  const bottomElement = useRef<HTMLDivElement>(null);
  const search: { question?: string } = useSearch({
    strict: false,
  });

  const { mutate: renameMutation } = useRenameNameMutation({
    onError: (err) => {
      messageQueue.error(err.message);
    },
  });

  const { mutate: chatMutation } = useStreamingChatMutation({
    onChunk: useCallback(
      (chunk: string) => {
        setStreamedChat((prev) => prev + chunk);
      },
      [setStreamedChat]
    ),
    onEvent: useMemo(() => getOnEvent(setStreamedEvent), [setStreamedEvent]),
    onSuccess: useCallback(() => {
      setStreamedChat("");
      const url = new URL(window.location.href);
      url.searchParams.delete("question");
      window.history.pushState(null, "", url.toString());
    }, [setStreamedChat]),
    getController: useCallback(
      (ctrl: AbortController) => {
        setStreamedAbortControllerState(ctrl);
      },
      [setStreamedAbortControllerState]
    ),
  });

  useEffect(() => {
    if (activeSession?.name === "") {
      const lastMessage =
        flatChatHistory.length > 0
          ? flatChatHistory[flatChatHistory.length - 1]
          : null;
      if (lastMessage && !isPlaceholder(lastMessage)) {
        renameMutation(activeSession.id.toString());
      }
    }
  }, [
    activeSession?.name,
    flatChatHistory,
    chatHistoryStatus,
    activeSession?.id,
  ]);

  const excludeKnowledgeBases =
    !activeSession?.dataSourceIds || activeSession.dataSourceIds.length === 0;
  const { question } = search;
  const activeSessionId = activeSession?.id;

  useEffect(() => {
    // note: when creating a new session, we run the risk of firing this off twice without the isFetchingHistory check
    if (question && activeSessionId && !isFetchingHistory) {
      chatMutation({
        query: question,
        session_id: activeSessionId,
        configuration: createQueryConfiguration(excludeKnowledgeBases),
      });
    }
  }, [question, activeSessionId, excludeKnowledgeBases, isFetchingHistory]);

  useEffect(() => {
    if (inView) {
      fetchPreviousPage().catch(() => {
        messageQueue.error("An error occurred fetching the next page");
      });
    }
  }, [fetchPreviousPage, inView]);

  useEffect(() => {
    if (bottomElement.current) {
      bottomElement.current.scrollIntoView({ behavior: "instant" });
    }
  }, [activeSession?.id]);

  useEffect(() => {
    if (bottomElement.current) {
      if (
        flatChatHistory.length > 0 &&
        isPlaceholder(flatChatHistory[flatChatHistory.length - 1])
      ) {
        bottomElement.current.scrollIntoView({
          behavior: "smooth",
        });
      } else {
        bottomElement.current.scrollIntoView({ behavior: "instant" });
      }
    }
  }, [flatChatHistory.length]);

  if (chatHistoryStatus === "pending") {
    return <ChatLoading />;
  }
  if (flatChatHistory.length === 0) {
    if (search.question) {
      return <PendingRagOutputSkeleton question={search.question} />;
    }
    if (isFetchingHistory) {
      return <ChatLoading />;
    }
    return <EmptyChatState />;
  }

  return (
    <div data-testid="chat-message-controller" style={{ width: "100%" }}>
      {isFetchingPreviousPage && <Skeleton />}
      {flatChatHistory.map((historyMessage, index) => {
        const isLast = index === flatChatHistory.length - 1;
        // trigger fetching on second to last item
        if (index === 2) {
          return (
            <div ref={refToFetchNextPage} key={historyMessage.id}>
              {isLast && <div ref={bottomElement} />}
              <ChatMessage data={historyMessage} />
            </div>
          );
        }

        return (
          <div
            key={historyMessage.id}
            ref={isLast ? bottomElement : null}
            style={isLast ? { minHeight: window.innerHeight - 200 } : {}}
          >
            <ChatMessage data={historyMessage} />
          </div>
        );
      })}
    </div>
  );
};

export default ChatMessageController;
