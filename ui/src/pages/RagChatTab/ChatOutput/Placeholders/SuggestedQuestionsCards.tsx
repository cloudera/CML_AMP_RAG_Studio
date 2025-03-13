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

import { Card, Flex, Skeleton, Typography } from "antd";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { useContext } from "react";
import { useSuggestQuestions } from "src/api/ragQueryApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { createQueryConfiguration, useChatMutation } from "src/api/chatApi.ts";
import useCreateSessionAndRedirect from "pages/RagChatTab/ChatOutput/hooks/useCreateSessionAndRedirect";

const SuggestedQuestionsCards = () => {
  const {
    activeSession,
    excludeKnowledgeBaseState: [excludeKnowledgeBase],
  } = useContext(RagChatContext);
  const sessionId = activeSession?.id.toString();
  const {
    data,
    isPending: suggestedQuestionsIsPending,
    isFetching: suggestedQuestionsIsFetching,
  } = useSuggestQuestions({
    configuration: createQueryConfiguration(excludeKnowledgeBase),
    session_id: sessionId ?? "",
  });
  const createSessionAndRedirect = useCreateSessionAndRedirect();
  const { mutate: chatMutation, isPending: askRagIsPending } = useChatMutation({
    onError: (res: Error) => {
      messageQueue.error(res.toString());
    },
  });

  const handleAskSample = (suggestedQuestion: string) => {
    if (suggestedQuestion.length > 0) {
      if (sessionId) {
        chatMutation({
          query: suggestedQuestion,
          session_id: sessionId,
          configuration: createQueryConfiguration(excludeKnowledgeBase),
        });
      } else {
        createSessionAndRedirect(suggestedQuestion);
      }
    }
  };

  if (
    suggestedQuestionsIsPending ||
    askRagIsPending ||
    suggestedQuestionsIsFetching
  ) {
    return (
      <Flex gap={10} wrap="wrap" justify="space-between">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton
            key={index}
            active
            style={{
              width: 178,
              padding: 0,
            }}
          />
        ))}
      </Flex>
    );
  }

  return (
    <Flex gap={10} wrap="wrap" justify="space-between">
      {data?.suggested_questions.map((question, index) => {
        return (
          <Card
            key={question}
            size={"small"}
            hoverable
            style={{
              width: 178,
              margin: 0,
              padding: 0,
            }}
            extra={
              <Typography.Text type="secondary">{`#${(index + 1).toString()}`}</Typography.Text>
            }
            onClick={() => {
              handleAskSample(question);
            }}
          >
            <Card.Meta
              description={<Typography.Text>{question}</Typography.Text>}
            />
          </Card>
        );
      })}
    </Flex>
  );
};

export default SuggestedQuestionsCards;
