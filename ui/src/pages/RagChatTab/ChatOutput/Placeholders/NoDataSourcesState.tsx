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

import { useNavigate } from "@tanstack/react-router";
import { Button, Flex, Typography } from "antd";
import { useContext, ReactNode } from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";

const PlaceholderContainer = ({
  message,
  children,
}: {
  message: string;
  children: ReactNode;
}) => {
  return (
    <Flex
      vertical
      align="center"
      justify="center"
      style={{ height: "100%" }}
      gap={10}
    >
      <Typography.Title level={4} type="secondary" italic={true}>
        Ask any question
      </Typography.Title>
      <Typography.Text>{message}</Typography.Text>
      {children}
    </Flex>
  );
};

const NoDataSourcesState = () => {
  const navigate = useNavigate();
  const {
    activeSession,
    dataSourcesQuery: { dataSources, dataSourcesStatus },
  } = useContext(RagChatContext);

  if (activeSession) {
    return null;
  }

  if (dataSourcesStatus === "success" && dataSources.length > 0) {
    return null;
  }

  return (
    <PlaceholderContainer message="Create a knowledge base to chat with your documents.">
      <Button
        type="default"
        style={{ width: 200 }}
        onClick={() => {
          navigate({
            to: "/data",
            search: { create: true },
          }).catch(() => null);
          return;
        }}
      >
        Create Knowledge Base
      </Button>
    </PlaceholderContainer>
  );
};

export default NoDataSourcesState;
