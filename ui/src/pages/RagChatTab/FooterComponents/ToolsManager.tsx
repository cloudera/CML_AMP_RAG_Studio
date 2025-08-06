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
import {
  useToolsQuery,
  useImageGenerationConfigQuery,
  useImageGenerationToolsQuery,
} from "src/api/toolsApi.ts";
import {
  Dispatch,
  ReactNode,
  SetStateAction,
  useContext,
  useState,
  useMemo,
  useEffect,
} from "react";
import { ToolOutlined } from "@ant-design/icons";
import { cdlBlue600, cdlOrange500, cdlWhite } from "src/cuix/variables.ts";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { getAmpConfigQueryOptions } from "src/api/ampMetadataApi.ts";

const ToolsManagerContent = ({
  selectedTools,
  onToolSelectionChange,
}: {
  selectedTools: string[];
  onToolSelectionChange: (tools: string[]) => void;
}) => {
  const { data: regularTools, isLoading: regularToolsLoading } =
    useToolsQuery();
  const { data: imageConfig } = useImageGenerationConfigQuery();
  const { data: imageTools } = useImageGenerationToolsQuery();
  const { data: config } = useSuspenseQuery(getAmpConfigQueryOptions);

  // Combine regular tools with the selected image generation tool (if enabled)
  const toolsList = useMemo(() => {
    const tools = [];

    // Add regular tools
    if (regularTools) {
      tools.push(
        ...regularTools.map((tool) => ({
          name: tool.name,
          displayName: tool.metadata.display_name,
          description: tool.metadata.description,
        }))
      );
    }

    // Only add image generation tool if it's enabled AND selected
    if (imageConfig?.enabled && imageConfig.selected_tool && imageTools) {
      const selectedTool = imageTools.find(
        (tool) => tool.name === imageConfig.selected_tool
      );
      if (selectedTool) {
        tools.push({
          name: selectedTool.name,
          displayName: selectedTool.metadata.display_name,
          description: selectedTool.metadata.description,
        });
      }
    }

    return tools;
  }, [regularTools, imageConfig, imageTools]);

  const handleCheck = (title: string, checked: boolean) => {
    if (checked) {
      onToolSelectionChange([...selectedTools, title]);
    } else {
      onToolSelectionChange(selectedTools.filter((tool) => tool !== title));
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
          Tool Selection{" "}
          {config ? (
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              (Manage available tools{" "}
              <Link to={"/settings"} hash={"tools"}>
                here
              </Link>
              )
            </Typography.Text>
          ) : null}
        </Typography.Title>
      </Flex>
      <List
        dataSource={toolsList}
        loading={regularToolsLoading}
        style={{ overflowY: "auto" }}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={item.displayName || item.name}
              description={item.description}
              avatar={
                <Checkbox
                  checked={selectedTools.includes(item.name)}
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
  selectedTools,
  onToolSelectionChange,
}: {
  isOpen: boolean;
  setIsOpen: Dispatch<SetStateAction<boolean>>;
  children: ReactNode;
  selectedTools: string[];
  onToolSelectionChange: (tools: string[]) => void;
}) => {
  return (
    <Popover
      open={isOpen}
      trigger="click"
      onOpenChange={setIsOpen}
      placement="topRight"
      content={
        <ToolsManagerContent
          selectedTools={selectedTools}
          onToolSelectionChange={onToolSelectionChange}
        />
      }
    >
      {children}
    </Popover>
  );
};

const ToolsManagerButton = ({
  onSelectedToolsChange,
}: {
  onSelectedToolsChange?: (tools: string[]) => void;
} = {}) => {
  const { activeSession } = useContext(RagChatContext);
  const [toolsManagerOpen, setToolsManagerOpen] = useState(false);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);

  // Initialize with session tools when activeSession changes
  useEffect(() => {
    if (activeSession) {
      setSelectedTools(activeSession.queryConfiguration.selectedTools);
    }
  }, [activeSession]);

  // Notify parent when selected tools change
  const handleToolSelectionChange = (tools: string[]) => {
    setSelectedTools(tools);
    onSelectedToolsChange?.(tools);
  };

  if (!activeSession?.queryConfiguration.enableToolCalling) {
    return null;
  }

  return (
    <ToolsManager
      isOpen={toolsManagerOpen}
      setIsOpen={setToolsManagerOpen}
      selectedTools={selectedTools}
      onToolSelectionChange={handleToolSelectionChange}
    >
      <Tooltip title={!toolsManagerOpen ? "Tool Selection" : ""}>
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
