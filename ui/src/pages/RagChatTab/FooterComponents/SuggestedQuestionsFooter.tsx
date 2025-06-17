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

import {
  Alert,
  Collapse,
  Flex,
  Skeleton,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { useState } from "react";
import { SendOutlined } from "@ant-design/icons";
import { cdlBlue600, cdlOrange500 } from "src/cuix/variables.ts";
import AiAssistantIcon from "src/cuix/icons/AiAssistantIcon.ts";

export const SuggestedQuestionButton = ({
  question,
  handleChat,
  rewritten,
}: {
  question: string;
  handleChat: (input: string) => void;
  rewritten?: boolean;
}) => {
  return (
    <Tag
      onClick={() => {
        handleChat(question);
      }}
      icon={
        rewritten ? (
          <AiAssistantIcon style={{ marginRight: 6 }} />
        ) : (
          <SendOutlined />
        )
      }
      style={{
        width: "fit-content",
        height: "auto",
        alignItems: "start",
        color: cdlBlue600,
        borderColor: cdlBlue600,
        cursor: "pointer",
      }}
    >
      <Typography.Text
        style={{
          textWrap: "wrap",
          textAlign: "left",
          color: cdlBlue600,
          fontWeight: 300,
        }}
      >
        {question}
      </Typography.Text>
    </Tag>
  );
};

const SuggestedQuestionsFooter = ({
  isLoading,
  handleChat,
  questions,
  condensedQuestion,
  error,
}: {
  isLoading: boolean;
  handleChat: (input: string) => void;
  questions: string[];
  condensedQuestion?: string;
  error?: Error | null;
}) => {
  const [toggleCollapse, setToggleCollapse] = useState(false);

  return (
    <Flex
      onClick={() => {
        setToggleCollapse(!toggleCollapse);
      }}
      vertical
      gap={10}
      style={{ width: "100%" }}
    >
      <Collapse
        defaultActiveKey={["1"]}
        size="small"
        ghost
        activeKey={toggleCollapse ? ["1"] : [""]}
        items={[
          {
            key: "1",
            label: (
              <Flex gap={8} align="center">
                <Typography.Text
                  type="secondary"
                  style={{ margin: 0, marginTop: 1, fontSize: 12 }}
                >
                  Suggested Questions
                </Typography.Text>
                {condensedQuestion ? (
                  <Tooltip title="Alternative question available">
                    <AiAssistantIcon style={{ color: cdlOrange500 }} />
                  </Tooltip>
                ) : null}
              </Flex>
            ),
            children: (
              <Flex vertical gap={12}>
                {condensedQuestion ? (
                  <SuggestedQuestionButton
                    question={condensedQuestion}
                    handleChat={handleChat}
                    rewritten={true}
                    key={condensedQuestion}
                  />
                ) : null}
                {error ? (
                  <Alert
                    type="error"
                    message={`Error fetching suggested questions: ${error}`}
                  />
                ) : null}
                {isLoading ? (
                  <Skeleton paragraph={{ rows: 2 }} active />
                ) : (
                  questions.map((question) => (
                    <SuggestedQuestionButton
                      question={question}
                      handleChat={handleChat}
                      rewritten={false}
                      key={question}
                    />
                  ))
                )}
              </Flex>
            ),
          },
        ]}
      />
    </Flex>
  );
};

export default SuggestedQuestionsFooter;
