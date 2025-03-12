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

import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { createQueryConfiguration, useChatMutation } from "src/api/chatApi.ts";
import {
  CreateSessionRequest,
  useCreateSessionMutation,
  useRenameNameMutation,
} from "src/api/sessionApi.ts";
import { QueryKeys } from "src/api/utils.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { Session } from "src/api/sessionApi.ts";

interface UseChatActionsProps {
  sessionId?: string;
  activeSession?: Session;
  excludeKnowledgeBase: boolean;
  setFirstQuestion: (question: string) => void;
}

const useChatActions = ({
  sessionId,
  activeSession,
  excludeKnowledgeBase,
  setFirstQuestion,
}: UseChatActionsProps) => {
  const navigate = useNavigate();
  const [userInput, setUserInput] = useState("");
  const [newSessionId, setNewSessionId] = useState<number>();
  const queryClient = useQueryClient();

  function chatOnSuccess() {
    if (newSessionId) {
      renameSessionMutation.mutate(newSessionId.toString());
      return navigate({
        to: "/sessions/$sessionId",
        params: { sessionId: newSessionId.toString() },
      });
    }
    if (activeSession && activeSession.name === "") {
      renameSessionMutation.mutate(activeSession.id.toString());
    }
    setUserInput("");
  }

  const renameSessionMutation = useRenameNameMutation({
    onSuccess: (name) => {
      messageQueue.success(`session renamed to ${name}`);
    },
    onError: (res) => {
      messageQueue.error(res.toString());
    },
  });

  const chatMutation = useChatMutation({
    onSuccess: chatOnSuccess,
    onError: (res: Error) => {
      messageQueue.error(res.toString());
    },
  });

  const { mutate } = useCreateSessionMutation({
    onSuccess: async (session) => {
      await queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getSessions] })
        .then(() => {
          setNewSessionId(session.id);
          setFirstQuestion(userInput);

          chatMutation.mutate({
            query: userInput,
            session_id: session.id.toString(),
            configuration: createQueryConfiguration(excludeKnowledgeBase),
          });
        })
        .catch((x: unknown) => {
          messageQueue.error(String(x));
        });
    },
    onError: () => {
      messageQueue.error("Session creation failed.");
    },
  });

  const createSessionAndAskQuestion = (
    requestBody: CreateSessionRequest,
    question: string,
  ) => {
    setUserInput(question);
    mutate(requestBody);
  };

  const reallyHandleChat = (question: string) => {
    if (activeSession && sessionId) {
      chatMutation.mutate({
        query: question,
        session_id: sessionId,
        configuration: createQueryConfiguration(excludeKnowledgeBase),
      });
    } else if (question.trim().length > 0) {
      setUserInput(question);
      const requestBody: CreateSessionRequest = {
        name: "New Chat",
        dataSourceIds: [],
        inferenceModel: undefined,
        responseChunks: 10,
        queryConfiguration: {
          enableHyde: false,
          enableSummaryFilter: true,
        },
      };
      createSessionAndAskQuestion(requestBody, question);
    }
  };

  const handleChat = (input: string) => {
    if (input.trim().length <= 0) {
      return;
    }
    reallyHandleChat(input);
  };

  return {
    handleChat,
    chatMutation,
  };
};

export default useChatActions;
