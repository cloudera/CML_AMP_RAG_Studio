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

import { Session, useDeleteSessionMutation } from "src/api/sessionApi.ts";
import { useNavigate } from "@tanstack/react-router";
import { useChatHistoryQuery } from "src/api/chatApi.ts";
import { Button, Card, Flex, Modal, Typography } from "antd";
import { format } from "date-fns";
import DeleteIcon from "src/cuix/icons/DeleteIcon.ts";
import { cdlRed600 } from "src/cuix/variables.ts";
import { QueryKeys } from "src/api/utils.ts";
import messageQueue from "src/utils/messageQueue.ts";
import useModal from "src/utils/useModal.ts";
import { useQueryClient } from "@tanstack/react-query";

const DeleteSession = ({ session }: { session: Session }) => {
  const deleteSessionModal = useModal();
  const queryClient = useQueryClient();
  const { mutate: deleteSessionMutate } = useDeleteSessionMutation({
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.getSessions],
      });
      deleteSessionModal.setIsModalOpen(false);
      messageQueue.success("Session deleted successfully");
    },
    onError: () => {
      messageQueue.error("Failed to delete session");
    },
  });

  const handleDeleteSession = () => {
    deleteSessionMutate(session.id.toString());
  };

  return (
    <div
      onClick={(event) => {
        event.stopPropagation();
      }}
    >
      <Button
        type="text"
        style={{ color: cdlRed600 }}
        icon={<DeleteIcon style={{ width: 16, height: 20 }} />}
        onClick={() => {
          deleteSessionModal.setIsModalOpen(true);
        }}
      />
      <Modal
        title="Delete session?"
        open={deleteSessionModal.isModalOpen}
        onOk={() => {
          handleDeleteSession();
        }}
        okText={"Yes, delete it!"}
        okButtonProps={{
          danger: true,
        }}
        onCancel={() => {
          deleteSessionModal.handleCancel();
        }}
      />
    </div>
  );
};

const SessionCard = ({ session }: { session: Session }) => {
  const navigate = useNavigate();
  const { data: chatHistory, isSuccess } = useChatHistoryQuery(session.id);

  const lastMessage = chatHistory.length
    ? chatHistory[chatHistory.length - 1]
    : null;

  const handleNavOnClick = () => {
    navigate({
      to: "/chats/projects/$projectId/sessions/$sessionId",
      params: {
        sessionId: session.id.toString(),
        projectId: session.projectId.toString(),
      },
    }).catch(() => null);
  };

  return (
    <Card
      title={session.name}
      extra={<DeleteSession session={session} />}
      onClick={handleNavOnClick}
      hoverable={true}
      // style={{ cursor: "pointer" }}
    >
      <Typography.Paragraph ellipsis={{ rows: 2 }}>
        {isSuccess && lastMessage ? lastMessage.rag_message.assistant : null}
      </Typography.Paragraph>
      <Flex justify="space-between">
        <Typography.Text type="secondary">
          Last message:{" "}
          {lastMessage?.timestamp
            ? format(lastMessage.timestamp * 1000, "MMM dd yyyy, pp")
            : "No messages"}
        </Typography.Text>
        <Typography.Text type="secondary">
          Created by: {session.createdById}
        </Typography.Text>
      </Flex>
    </Card>
  );
};

export default SessionCard;
