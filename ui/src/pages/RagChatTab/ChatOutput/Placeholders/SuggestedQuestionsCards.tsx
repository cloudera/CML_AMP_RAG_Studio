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
import { createQueryConfiguration } from "src/api/chatApi.ts";
import useChatActions from "src/utils/useChatActions.ts";

const SAMPLE_QUESTIONS = [
  "How does Cloudera Machine Learning handle data preparation and ingestion from various data sources?",
  "What data formats are supported by Cloudera Machine Learning, and how are they processed?",
  "Can Cloudera Machine Learning handle large-scale data ingestion and processing?",
  "How does Cloudera Machine Learning support data quality and data governance?",
  "Can Cloudera Machine Learning integrate with other data preparation and ingestion tools?",
  "What machine learning algorithms are supported by Cloudera Machine Learning?",
  "How does Cloudera Machine Learning support model development and training, including hyperparameter tuning?",
  "Can Cloudera Machine Learning handle large-scale model training and deployment?",
  "How does Cloudera Machine Learning support model explainability and interpretability?",
  "Can Cloudera Machine Learning integrate with other machine learning frameworks and tools?",
  "How does Cloudera Machine Learning support model deployment and serving, including model scoring and prediction?",
  "Can Cloudera Machine Learning handle high-volume and high-velocity data streams?",
  "How does Cloudera Machine Learning support model updates and retraining?",
  "Can Cloudera Machine Learning integrate with other model serving and deployment platforms?",
  "What are the security and access controls for model deployment and serving in Cloudera Machine Learning?",
  "What security features are built into Cloudera Machine Learning, including data encryption and access controls?",
  "How does Cloudera Machine Learning support data governance and compliance, including regulatory requirements?",
  "Can Cloudera Machine Learning handle sensitive data, such as PII or PHI?",
  "How does Cloudera Machine Learning support auditing and logging?",
  "Can Cloudera Machine Learning integrate with other security and governance tools?",
];

const SuggestedQuestionsCards = () => {
  const {
    activeSession,
    excludeKnowledgeBaseState: [excludeKnowledgeBase],
    firstQuestionState: [, setFirstQuestion],
  } = useContext(RagChatContext);
  const sessionId = activeSession?.id.toString();
  const { data, isFetching: suggestedQuestionsIsFetching } =
    useSuggestQuestions({
      configuration: createQueryConfiguration(excludeKnowledgeBase),
      session_id: sessionId ?? "",
    });

  const { handleChat, chatMutation, setUserInput } = useChatActions({
    sessionId,
    activeSession,
    excludeKnowledgeBase,
    setFirstQuestion,
  });

  let suggestedQuestions = data?.suggested_questions ?? [];
  if (!sessionId) {
    suggestedQuestions = SAMPLE_QUESTIONS.sort(() => 0.5 - Math.random()).slice(
      0,
      4
    );
  }

  const handleAskSample = (suggestedQuestion: string) => {
    if (suggestedQuestion.length > 0) {
      setFirstQuestion(suggestedQuestion);
      setUserInput(suggestedQuestion);
      handleChat(suggestedQuestion);
    }
  };

  if (suggestedQuestionsIsFetching || chatMutation.isPending) {
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
      {suggestedQuestions.map((question, index) => {
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
