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
import { Button, Flex, Input, Select, Typography } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { useFeedbackMutation } from "src/api/chatApi.ts";
import {
  Dispatch,
  SetStateAction,
  useContext,
  useEffect,
  useState,
} from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import messageQueue from "src/utils/messageQueue.ts";
import { cdlGreen700 } from "src/cuix/variables.ts";

const Feedback = ({
  responseId,
  showFeedbackInput,
  setShowFeedbackInput,
}: {
  responseId: string;
  showFeedbackInput: boolean;
  setShowFeedbackInput: Dispatch<SetStateAction<boolean>>;
}) => {
  const session = useContext(RagChatContext).activeSession;
  const [showCustomFeedbackInput, setShowCustomFeedbackInput] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const { mutate: feedbackMutate } = useFeedbackMutation({
    onSuccess: () => {
      setShowFeedbackInput(false);
      setShowCustomFeedbackInput(false);
      setFeedbackSubmitted(true);
    },
    onError: () => {
      messageQueue.error("Failed submit feedback");
    },
  });

  useEffect(() => {
    if (feedbackSubmitted) {
      const timer = setTimeout(() => {
        setFeedbackSubmitted(false);
      }, 3000);
      return () => {
        clearTimeout(timer);
      };
    }
  }, [feedbackSubmitted, setFeedbackSubmitted]);

  const handleSubmitFeedbackInput = (value: string) => {
    if (!session) {
      return;
    }
    if (value === "Other") {
      setShowFeedbackInput(false);
      setShowCustomFeedbackInput(true);
    } else {
      feedbackMutate({
        sessionId: session.id.toString(),
        responseId,
        feedback: value,
      });
      setShowFeedbackInput(false);
    }
  };

  const handleSubmitCustomFeedbackInput = (value: string) => {
    if (!session) {
      return;
    }
    feedbackMutate({
      sessionId: session.id.toString(),
      responseId,
      feedback: value,
    });
    setShowCustomFeedbackInput(false);
  };

  const handleClickBackOnCustomFeedbackInput = () => {
    setShowFeedbackInput(true);
    setShowCustomFeedbackInput(false);
  };

  return (
    <Flex style={{ marginLeft: 16 }} align="center" gap={8}>
      {showCustomFeedbackInput ? (
        <Button
          icon={<ArrowLeftOutlined />}
          type="text"
          size="small"
          onClick={handleClickBackOnCustomFeedbackInput}
        />
      ) : (
        <div style={{ width: 24 }} />
      )}
      {showFeedbackInput ? (
        <Select
          placeholder="What can be improved (optional)?"
          onChange={handleSubmitFeedbackInput}
          options={[
            { value: "Inaccurate", label: "Inaccurate" },
            { value: "Not helpful", label: "Not helpful" },
            { value: "Out of date", label: "Out of date" },
            { value: "Too short", label: "Too short" },
            { value: "Too long", label: "Too long" },
            { value: "Other", label: "Other" },
          ]}
        />
      ) : null}
      {showCustomFeedbackInput ? (
        <Input
          placeholder="Please provide feedback"
          style={{ width: 400 }}
          onPressEnter={(e) => {
            handleSubmitCustomFeedbackInput(e.currentTarget.value);
          }}
        />
      ) : null}
      {feedbackSubmitted ? (
        <Typography.Text style={{ fontSize: 12, color: cdlGreen700 }}>
          Feedback submitted
        </Typography.Text>
      ) : null}
    </Flex>
  );
};

export default Feedback;
