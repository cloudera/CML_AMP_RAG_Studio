/*
 * CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
 * (C) Cloudera, Inc. 2025
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
 */

import { CrewEventResponse } from "src/api/chatApi.ts";
import { Button, Card, Flex, Spin, Typography } from "antd";
import { format } from "date-fns";
import { useState } from "react";
import { MinusOutlined, PlusOutlined } from "@ant-design/icons";

const StreamedEvent = ({ event }: { event: CrewEventResponse }) => {
  return (
    <Flex vertical style={{ paddingRight: 16 }}>
      <Flex justify="space-between">
        <Flex gap={8}>
          <Typography.Text style={{ fontSize: 10 }} type="secondary">
            {event.type}:
          </Typography.Text>
          <Typography.Text style={{ fontSize: 10 }}>
            {event.name}
          </Typography.Text>
        </Flex>
        <Typography.Text style={{ fontSize: 10 }} type="secondary">
          {format(event.timestamp * 1000, "pp")}
        </Typography.Text>
      </Flex>
      <Flex>
        <Typography.Paragraph
          style={{ fontSize: 10, marginLeft: 8 }}
          ellipsis={{
            rows: 1,
            expandable: true,
            symbol: (
              <Typography.Link style={{ fontSize: 10 }}>more</Typography.Link>
            ),
          }}
        >
          {event.data}
        </Typography.Paragraph>
      </Flex>
    </Flex>
  );
};

const StreamedEvents = ({
  streamedEvents,
}: {
  streamedEvents?: CrewEventResponse[];
}) => {
  const [collapsed, setCollapsed] = useState(true);
  // streamedEvents = [
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer",
  //     timestamp: 1747321016.211383,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "searcher",
  //     data: "Thought: I now know the final answer.",
  //     timestamp: 1747321018.258643,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "researcher",
  //     data: "The query calls for an in-depth exploration of how the index addresses the impact of economic sanctions on crisis management. The context emphasizes missing sanctions data, external actors' influences, and the potential resource limitations faced by countries under sanctions during humanitarian crises. Using the provided context, I aim to build a thorough response based on the textual insights and their role within an index framework.",
  //     timestamp: 1747321036.084759,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer",
  //     timestamp: 1747321265.41863,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer",
  //     timestamp: 1747321459.718286,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "searcher",
  //     data: "Thought: I now know the final answer",
  //     timestamp: 1747321461.3717902,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "researcher",
  //     data: "Failed to parse LLM response",
  //     timestamp: 1747321482.936766,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer.",
  //     timestamp: 1747321500.357913,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "searcher",
  //     data: "Thought: I now know the final answer. The current date is already provided: 2025-05-15T09:04:59.504493. Let me clarify if you have a specific query related to searching the internet or if this date alone suffices as an answer. Kindly refine your request for further assistance.",
  //     timestamp: 1747321503.355131,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "researcher",
  //     data: "Thought: I now have relevant sources to understand how the intervention index optimizes resource allocation in humanitarian crises.",
  //     timestamp: 1747321531.380204,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "date finder",
  //     data: "Thought: I now know the final answer.",
  //     timestamp: 1747321593.87309,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "searcher",
  //     data: "Thought: I now know the final answer.",
  //     timestamp: 1747321595.371118,
  //   },
  //   {
  //     type: "agent_finish",
  //     name: "researcher",
  //     data: "To address the user's query about the role of the intervention index in optimizing resource allocation in humanitarian crises, I need to analyze how the proposed index from the context provided improves resource allocation before, during, and after crises while incorporating ethical, operational, and dynamic factors rooted in the research provided. \n\nThe context from the user also emphasizes issues such as cross-organization planning, ethical concerns about data use and representation, and the need for dynamic adaptability in crises. I can arrive at a comprehensive answer using the detail already shared, cross-referencing this with the methodology and benefits of the intervention index discussed.",
  //     timestamp: 1747321613.301375,
  //   },
  // ];

  const lastEvent = streamedEvents?.[streamedEvents.length - 1];

  return (
    <Card
      style={{ marginTop: 8 }}
      title={
        <Flex align="center" gap={8}>
          <Spin size="small" />
          <Typography.Text>Agent Events -</Typography.Text>
          {lastEvent ? (
            <Typography.Text type="secondary">
              {lastEvent.type}: {lastEvent.name} (
              {format(lastEvent.timestamp * 1000, "pp")})
            </Typography.Text>
          ) : (
            <Typography.Text type="secondary">No event</Typography.Text>
          )}
        </Flex>
      }
      extra={
        <Button
          type="text"
          size="small"
          onClick={() => {
            setCollapsed(!collapsed);
          }}
          icon={collapsed ? <PlusOutlined /> : <MinusOutlined />}
        />
      }
      size="small"
      styles={{ body: { display: collapsed ? "none" : "inherit" } }}
    >
      <Flex
        vertical
        style={{
          maxHeight: 150,
          overflowY: "auto",
        }}
      >
        {streamedEvents?.map((event) => (
          <StreamedEvent
            key={event.name + event.timestamp.toString()}
            event={event}
          />
        ))}
      </Flex>
    </Card>
  );
};

export default StreamedEvents;
