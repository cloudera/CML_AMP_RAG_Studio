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
  Checkbox,
  CheckboxChangeEvent,
  Flex,
  List,
  Popover,
  Typography,
} from "antd";
import { useToolsQuery } from "src/api/toolsApi.ts";
import { Dispatch, ReactNode, SetStateAction } from "react";

const ToolsManagerContent = ({
  selectedTools,
  setSelectedTools,
}: {
  selectedTools: string[];
  setSelectedTools: Dispatch<SetStateAction<string[]>>;
}) => {
  const { data, isLoading } = useToolsQuery();

  const toolsList = data?.map((tool) => ({
    title: tool.name,
    description: tool.description,
  }));

  const handleCheck = (title: string, checked: boolean) => {
    if (checked) {
      setSelectedTools((prev) => [...prev, title]);
    } else {
      setSelectedTools((prev) => prev.filter((tool) => tool !== title));
    }
  };

  return (
    <Flex style={{ width: 600, height: 200 }} vertical>
      <Typography.Title level={5} style={{ margin: 2, marginBottom: 16 }}>
        Tools Manager
      </Typography.Title>
      <List
        dataSource={toolsList}
        loading={isLoading}
        style={{ overflowY: "auto" }}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={item.title}
              description={item.description}
              avatar={
                <Checkbox
                  checked={selectedTools.includes(item.title)}
                  onChange={(e: CheckboxChangeEvent) => {
                    handleCheck(item.title, e.target.checked);
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
  selectedTools,
  setSelectedTools,
  children,
}: {
  isOpen: boolean;
  setIsOpen: Dispatch<SetStateAction<boolean>>;
  selectedTools: string[];
  setSelectedTools: Dispatch<SetStateAction<string[]>>;
  children: ReactNode;
}) => {
  return (
    <Popover
      open={isOpen}
      trigger="click"
      onOpenChange={setIsOpen}
      content={
        <ToolsManagerContent
          selectedTools={selectedTools}
          setSelectedTools={setSelectedTools}
        />
      }
    >
      {children}
    </Popover>
  );
};

export default ToolsManager;
