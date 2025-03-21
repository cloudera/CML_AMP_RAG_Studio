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
import { Card, Flex, Skeleton, Typography } from "antd";
import {
  useGetProjectById,
  useGetSessionsForProject,
} from "src/api/projectsApi.ts";
import { Route } from "src/routes/_layout/projects/_layout-projects/$projectId";
import { Session } from "src/api/sessionApi.ts";
import { useChatHistoryQuery } from "src/api/chatApi.ts";
import { format } from "date-fns";
import { useNavigate } from "@tanstack/react-router";

const SessionCard = ({ session }: { session: Session }) => {
  const navigate = useNavigate();
  const { data: chatHistory, isSuccess } = useChatHistoryQuery(session.id);

  const lastMessage = chatHistory.length
    ? chatHistory[chatHistory.length - 1]
    : null;

  const handleNavOnClick = () => {
    navigate({
      to: "/sessions/$sessionId",
      params: { sessionId: session.id.toString() },
    }).catch(() => null);
  };

  return (
    <Card
      title={session.name}
      extra={
        <Typography.Text type="secondary">
          Created by: {session.createdById}
        </Typography.Text>
      }
      hoverable={true}
      onClick={handleNavOnClick}
    >
      <Typography.Paragraph ellipsis={{ rows: 2 }}>
        {isSuccess && lastMessage ? lastMessage.rag_message.assistant : null}
      </Typography.Paragraph>
      <Typography.Text type="secondary">
        Last message:{" "}
        {lastMessage?.timestamp
          ? format(lastMessage.timestamp * 1000, "MMM dd yyyy, pp")
          : "No messages"}
      </Typography.Text>
    </Card>
  );
};

const Sessions = () => {
  const { projectId } = Route.useParams();
  const { data: sessions, isLoading } = useGetSessionsForProject(+projectId);

  if (isLoading) {
    return (
      <Flex>
        <Typography.Title level={3}>Chats</Typography.Title>
        <Skeleton active />
        <Skeleton active />
        <Skeleton active />
        <Skeleton active />
      </Flex>
    );
  }

  return (
    <Flex vertical gap={15}>
      <Typography.Title level={4} style={{ margin: 0 }}>
        Chats
      </Typography.Title>
      {sessions?.map((session) => (
        <SessionCard session={session} key={session.id} />
      ))}
    </Flex>
  );
};

const ProjectPage = () => {
  const { projectId } = Route.useParams();
  const { data: project } = useGetProjectById(+projectId);

  return (
    <Flex style={{ padding: 40 }} vertical>
      <h1>{project?.name}</h1>
      <Flex gap={32}>
        <Flex flex={2} vertical>
          <Sessions />
        </Flex>
        <Flex flex={1} vertical gap={16}>
          <Card title="Settings">This is where settings goes</Card>
          <Card title="Knowledge Bases">This is where KBs go</Card>
        </Flex>
      </Flex>
    </Flex>
  );
};

export default ProjectPage;
