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

import {
  Button,
  Checkbox,
  CheckboxChangeEvent,
  Flex,
  List,
  Popover,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { useToolsQuery } from "src/api/toolsApi.ts";
import {
  Dispatch,
  ReactNode,
  SetStateAction,
  useContext,
  useState,
} from "react";
import { ToolOutlined } from "@ant-design/icons";
import { cdlBlue600, cdlOrange500, cdlWhite } from "src/cuix/variables.ts";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import {
  Session,
  UpdateSessionRequest,
  useUpdateSessionMutation,
} from "src/api/sessionApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { QueryKeys } from "src/api/utils.ts";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { getAmpConfigQueryOptions } from "src/api/ampMetadataApi.ts";

const ToolsManagerContent = ({ activeSession }: { activeSession: Session }) => {
  const { data, isLoading } = useToolsQuery();
  const { data: config } = useSuspenseQuery(getAmpConfigQueryOptions);

  const toolsList = data?.map((tool) => ({
    name: tool.name,
    displayName: tool.metadata.display_name,
    description: tool.metadata.description,
  }));

  const queryClient = useQueryClient();

  const updateSession = useUpdateSessionMutation({
    onError: () => {
      messageQueue.error("Failed to update session");
    },
    onSuccess: async () => {
      messageQueue.success("Session updated successfully");
      await queryClient.invalidateQueries({
        queryKey: [QueryKeys.getSessions],
      });
    },
  });

  const handleUpdateSession = (selectedTools: string[]) => {
    const request: UpdateSessionRequest = {
      ...activeSession,
      queryConfiguration: {
        ...activeSession.queryConfiguration,
        selectedTools: selectedTools,
      },
    };
    updateSession.mutate(request);
  };

  const handleCheck = (title: string, checked: boolean) => {
    if (checked) {
      handleUpdateSession([
        ...activeSession.queryConfiguration.selectedTools,
        title,
      ]);
    } else {
      handleUpdateSession(
        activeSession.queryConfiguration.selectedTools.filter(
          (tool) => tool !== title,
        ),
      );
    }
  };

  return (
    <Flex style={{ width: 500, height: 300, margin: 8 }} vertical>
      <Flex align={"start"}>
        <Tooltip title="Tool Calling (Beta)">
          <Tag
            style={{
              backgroundColor: cdlOrange500,
              color: cdlWhite,
              borderRadius: 10,
            }}
          >
            &beta;
          </Tag>
        </Tooltip>
        <Typography.Title level={5} style={{ margin: 0, marginBottom: 16 }}>
          Tools Manager{" "}
          {config ? (
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              (Manage available tools <Link to={"/tools"}>here</Link>)
            </Typography.Text>
          ) : null}
        </Typography.Title>
      </Flex>
      <List
        dataSource={toolsList}
        loading={isLoading}
        style={{ overflowY: "auto" }}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={item.displayName || item.name}
              description={item.description}
              avatar={
                <Checkbox
                  checked={activeSession.queryConfiguration.selectedTools.includes(
                    item.name,
                  )}
                  onChange={(e: CheckboxChangeEvent) => {
                    handleCheck(item.name, e.target.checked);
                  }}
                />
              }
            />
          </List.Item>
        )}
      />
    </Flex>
  );
};

const ToolsManager = ({
  isOpen,
  setIsOpen,
  children,
  activeSession,
}: {
  isOpen: boolean;
  setIsOpen: Dispatch<SetStateAction<boolean>>;
  children: ReactNode;
  activeSession: Session;
}) => {
  return (
    <Popover
      open={isOpen}
      trigger="click"
      onOpenChange={setIsOpen}
      placement="topRight"
      content={<ToolsManagerContent activeSession={activeSession} />}
    >
      {children}
    </Popover>
  );
};

const ToolsManagerButton = () => {
  const { activeSession } = useContext(RagChatContext);
  const [toolsManagerOpen, setToolsManagerOpen] = useState(false);

  if (!activeSession?.queryConfiguration.enableToolCalling) {
    return null;
  }

  return (
    <ToolsManager
      isOpen={toolsManagerOpen}
      setIsOpen={setToolsManagerOpen}
      activeSession={activeSession}
    >
      <Tooltip title={!toolsManagerOpen ? "Tools Manager" : ""}>
        <Button
          icon={<ToolOutlined />}
          type="text"
          size={"small"}
          style={{ color: cdlBlue600 }}
          onClick={() => {
            setToolsManagerOpen(!toolsManagerOpen);
          }}
        />
      </Tooltip>
    </ToolsManager>
  );
};

export default ToolsManagerButton;
