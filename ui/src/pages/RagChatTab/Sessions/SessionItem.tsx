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
  Session,
  useDeleteChatHistoryMutation,
  useDeleteSessionMutation,
} from "src/api/sessionApi.ts";
import useModal from "src/utils/useModal.ts";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { chatHistoryQueryKey } from "src/api/chatApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { QueryKeys } from "src/api/utils.ts";
import { Flex, Menu, Modal, Popover, Tooltip, Typography } from "antd";
import { cdlWhite } from "src/cuix/variables.ts";
import { ClearOutlined, DeleteOutlined, MoreOutlined } from "@ant-design/icons";
import { useState } from "react";

const SessionItem = ({ session }: { session: Session }) => {
  const deleteChatHistoryModal = useModal();
  const deleteSessionModal = useModal();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [isHovered, setIsHovered] = useState(false);
  const { mutate: deleteChatHistoryMutate } = useDeleteChatHistoryMutation({
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: chatHistoryQueryKey(session.id.toString()),
      });
      deleteChatHistoryModal.setIsModalOpen(false);
      messageQueue.success("Chat history cleared successfully");
    },
    onError: () => {
      messageQueue.error("Failed to clear chat history");
    },
  });
  const { mutate: deleteSessionMutate } = useDeleteSessionMutation({
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.getSessions],
      });
      deleteSessionModal.setIsModalOpen(false);
      messageQueue.success("Session deleted successfully");
      return navigate({
        to: "/sessions",
      });
    },
    onError: () => {
      messageQueue.error("Failed to delete session");
    },
  });

  const handleDeleteChatHistory = () => {
    deleteChatHistoryMutate(session.id.toString());
  };

  const handleDeleteSession = () => {
    deleteSessionMutate(session.id.toString());
  };

  return (
    <Flex
      justify="space-between"
      style={{ paddingLeft: 8, width: "100%" }}
      onMouseEnter={() => {
        setIsHovered(true);
      }}
      onMouseLeave={() => {
        setIsHovered(false);
      }}
    >
      <Tooltip title={session.name.length > 15 ? session.name : ""}>
        {session.name === "" ? (
          <Typography.Text italic>...</Typography.Text>
        ) : (
          <Typography.Text ellipsis>{session.name}</Typography.Text>
        )}
      </Tooltip>
      <Popover
        style={{ padding: 0, margin: 0 }}
        arrow={false}
        content={
          <Menu
            style={{
              backgroundColor: cdlWhite,
              border: "none",
            }}
            items={[
              {
                key: "clear",
                label: "Clear",
                icon: <ClearOutlined />,
                onClick: ({ domEvent }) => {
                  domEvent.stopPropagation();
                  deleteChatHistoryModal.showModal();
                },
              },
              {
                key: "delete",
                label: "Delete",
                icon: <DeleteOutlined />,
                onClick: ({ domEvent }) => {
                  domEvent.stopPropagation();
                  deleteSessionModal.showModal();
                },
              },
            ]}
          />
        }
        placement="bottomLeft"
      >
        <MoreOutlined
          style={{
            visibility: isHovered ? "visible" : "hidden",
          }}
        />
      </Popover>
      <Modal
        title="Clear chat history?"
        open={deleteChatHistoryModal.isModalOpen}
        onOk={handleDeleteChatHistory}
        okText={"Yes, clear it!"}
        okButtonProps={{
          danger: true,
        }}
        onCancel={deleteChatHistoryModal.handleCancel}
      />
      <Modal
        title="Delete session?"
        open={deleteSessionModal.isModalOpen}
        onOk={handleDeleteSession}
        okText={"Yes, delete it!"}
        okButtonProps={{
          danger: true,
        }}
        onCancel={deleteSessionModal.handleCancel}
      />
    </Flex>
  );
};

export default SessionItem;
