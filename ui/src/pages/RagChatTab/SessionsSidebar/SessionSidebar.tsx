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

import { useContext, useEffect, useState } from "react";
import { Session } from "src/api/sessionApi.ts";
import {
  ConfigProvider,
  Flex,
  Layout,
  Menu,
  MenuProps,
  theme,
  Typography,
} from "antd";
import {
  cdlGray200,
  cdlGray800,
  cdlSlate800,
  cdlWhite,
} from "src/cuix/variables.ts";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { defaultSessionItems } from "pages/RagChatTab/SessionsSidebar/SidebarItems/DefaultSessionItems.tsx";
import { newChatItem } from "pages/RagChatTab/SessionsSidebar/SidebarItems/NewChatItem.tsx";
import { ItemType } from "antd/lib/menu/interface";
import Images from "src/components/images/Images.ts";
import "./index.css";
import { ProjectsHeaderItem } from "pages/RagChatTab/SessionsSidebar/SidebarItems/ProjectsHeaderItem.tsx";
import { getProjectItems } from "pages/RagChatTab/SessionsSidebar/SidebarItems/ProjectItems.tsx";
import { useParams } from "@tanstack/react-router";

const { Sider } = Layout;

export type MenuItem = Required<MenuProps>["items"];

const SessionMenuTheme = {
  algorithm: theme.defaultAlgorithm,
  token: { colorBgBase: cdlWhite },
  components: {
    Menu: {
      itemSelectedBg: cdlGray200,
      itemActiveBg: cdlSlate800,
      itemBg: cdlSlate800,
      colorText: cdlGray800,
      itemColor: cdlGray800,
      itemSelectedColor: cdlSlate800,
    },
    Layout: {
      triggerBg: cdlWhite,
      lightTriggerBg: cdlWhite,
      lightTriggerColor: cdlWhite,
      triggerColor: cdlWhite,
      siderBg: cdlWhite,
      bodyBg: cdlWhite,
      footerBg: cdlWhite,
      lightSiderBg: cdlWhite,
    },
  },
};

export function SessionSidebar({ sessions }: { sessions: Session[] }) {
  const { activeSession } = useContext(RagChatContext);
  const { projectId } = useParams({ strict: false });
  const projectItems = getProjectItems();

  const chooseKeys = (): string[] => {
    if (activeSession) {
      return [
        activeSession.id.toString(),
        `project-${activeSession.projectId.toString()}`,
      ];
    } else {
      if (projectId) {
        return [`project-${projectId}`];
      }
      return [];
    }
  };

  const [openItems, setOpenItems] = useState<string[]>(chooseKeys());
  useEffect(() => {
    setOpenItems(chooseKeys());
  }, [activeSession, projectId]);

  const items: ItemType[] = [
    ...newChatItem(18),
    { type: "divider", key: "newChatDivider" },
    {
      type: "group",
      label: <ProjectsHeaderItem />,
    },
    { type: "divider", key: "projectHeaderDivider" },
    ...projectItems,
    {
      type: "group",
      label: (
        <Flex gap={6} style={{ paddingLeft: 12, paddingTop: 32 }}>
          <Images.History style={{ fontSize: 18 }} />
          <Typography.Text type="secondary">Chat History</Typography.Text>
        </Flex>
      ),
    },
    ...defaultSessionItems(sessions),
  ];

  return (
    <ConfigProvider theme={SessionMenuTheme}>
      <div className="session-sider">
        <Sider width={280} style={{ height: "94vh" }}>
          <Menu
            defaultOpenKeys={chooseKeys()}
            onOpenChange={setOpenItems}
            openKeys={openItems}
            selectedKeys={chooseKeys()}
            multiple={true}
            mode="inline"
            style={{
              backgroundColor: cdlWhite,
              height: "100%",
              borderRight: 0,
              overflowY: "auto",
              scrollbarWidth: "thin",
              paddingTop: 20,
            }}
            items={items}
          />
        </Sider>
      </div>
    </ConfigProvider>
  );
}
