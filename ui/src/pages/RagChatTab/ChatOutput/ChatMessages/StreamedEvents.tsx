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

import { ToolEventResponse } from "src/api/chatApi.ts";
import { Button, Card, Flex, Spin, Typography } from "antd";
import { format } from "date-fns";
import { useState } from "react";
import { MinusOutlined, PlusOutlined } from "@ant-design/icons";

const StreamedEvent = ({ event }: { event: ToolEventResponse }) => {
  return (
    <Flex vertical style={{ paddingRight: 16 }}>
      <Flex justify="space-between">
        <Flex gap={8}>
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
  streamedEvents?: ToolEventResponse[];
}) => {
  const [collapsed, setCollapsed] = useState(true);

  if (!streamedEvents || streamedEvents.length === 0) {
    return null;
  }

  const lastEvent = streamedEvents[streamedEvents.length - 1];

  return (
    <Card
      style={{ marginTop: 16 }}
      title={
        <Flex align="center" gap={8}>
          <Spin size="small" />
          <div>
            <Typography.Text>Query Events - </Typography.Text>
            <Typography.Text type="secondary">
              {lastEvent.name} ({format(lastEvent.timestamp * 1000, "pp")})
            </Typography.Text>
          </div>
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
        {streamedEvents.map((event) => (
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
