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

import React, { useRef, useState } from "react";
import {
  CommentOutlined,
  DatabaseOutlined,
  LineChartOutlined,
  RobotFilled,
  SettingOutlined,
} from "@ant-design/icons";
import {
  Flex,
  Image,
  Layout,
  Menu,
  MenuProps,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { useMatchRoute, useNavigate } from "@tanstack/react-router";
import Images from "src/components/images/Images.ts";
import LightbulbIcon from "src/cuix/icons/LightbulbIcon";
import { cdlAmber200, cdlAmber900 } from "src/cuix/variables.ts";
import "./style.css";
import AmpUpdateBanner from "src/components/AmpUpdate/AmpUpdateBanner.tsx";

const { Sider } = Layout;

type MenuItem = Required<MenuProps>["items"][number];

function getItem(
  label: React.ReactNode,
  key: React.Key,
  onClick: () => void,
  icon?: React.ReactNode,
  children?: MenuItem[],
): MenuItem {
  return {
    key,
    icon,
    children,
    label,
    onClick,
  } as MenuItem;
}

const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const matchRoute = useMatchRoute();
  const navigate = useNavigate();
  const ref = useRef<HTMLDivElement>(null);

  const navToRagApp = () => {
    navigate({ to: "/chats" }).catch(() => null);
    return;
  };

  const navToData = () => {
    navigate({ to: "/data" }).catch(() => null);
    return;
  };

  const navToAnalytics = () => {
    navigate({ to: "/analytics" }).catch(() => null);
  };

  const navToSettings = () => {
    navigate({ to: "/settings" }).catch(() => null);
  };

  const navToModels = () => {
    navigate({ to: "/models" }).catch(() => null);
  };

  const baseItems: MenuItem[] = [
    {
      label: collapsed ? (
        <Tooltip title="Technical Preview">
          <Tag
            color={cdlAmber200}
            style={{
              borderRadius: 4,
              height: 24,
              width: 30,
              marginLeft: 18,
            }}
          >
            <Flex
              gap={4}
              justify="center"
              align="center"
              style={{ height: "100%" }}
            >
              <LightbulbIcon color="#000" />
            </Flex>
          </Tag>
        </Tooltip>
      ) : (
        <Tag
          color={cdlAmber200}
          style={{
            borderRadius: 20,
            height: 24,
            paddingLeft: 6,
            paddingRight: 8,
            marginLeft: 10,
          }}
        >
          <Flex
            gap={4}
            justify="center"
            align="center"
            style={{ height: "100%" }}
          >
            <LightbulbIcon color="#000" />
            <Typography.Text style={{ fontSize: 12 }} color={cdlAmber900}>
              Technical Preview
            </Typography.Text>
          </Flex>
        </Tag>
      ),
      key: "tech-preview",
      type: "group",
    },
    getItem(
      <div data-testid="rag-apps-nav">Chats</div>,
      "chat",
      navToRagApp,
      <CommentOutlined />,
    ),
    getItem(
      <div data-testid="data-management-nav">Knowledge Bases</div>,
      "data",
      navToData,
      <DatabaseOutlined />,
    ),
  ];

  const models = getItem(
    <div data-testid="models-nav">Models</div>,
    "models",
    navToModels,
    <RobotFilled />,
  );

  const analyticsItem = getItem(
    <div data-testid="analytics-nav">Analytics</div>,
    "analytics",
    navToAnalytics,
    <LineChartOutlined />,
  );

  const settingsItem = getItem(
    <div data-testid="settings-nav">Settings</div>,
    "settings",
    navToSettings,
    <SettingOutlined />,
  );

  const items = [...baseItems, models, analyticsItem, settingsItem];

  function chooseRoute() {
    if (matchRoute({ to: "/data", fuzzy: true })) {
      return ["data"];
    } else if (matchRoute({ to: "/chats", fuzzy: true })) {
      return ["chat"];
    } else if (matchRoute({ to: "/models", fuzzy: true })) {
      return ["models"];
    } else if (matchRoute({ to: "/analytics", fuzzy: true })) {
      return ["analytics"];
    } else if (matchRoute({ to: "/projects", fuzzy: true })) {
      return ["projects"];
    } else if (matchRoute({ to: "/settings", fuzzy: true })) {
      return ["settings"];
    } else {
      return ["chat"];
    }
  }

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={(value) => {
        setCollapsed(value);
      }}
      style={{
        transition: "none",
        height: "100vh",
        top: 0,
        position: "sticky",
      }}
      width={250}
      ref={ref}
    >
      <div style={{ padding: 20 }}>
        <Image
          src={Images.ClouderaSmall}
          preview={false}
          height={36}
          style={{ paddingLeft: 4 }}
        />
        {!collapsed ? (
          <Image
            src={Images.RagStudioProduct}
            preview={false}
            style={{ transition: "ease-in", paddingLeft: 5 }}
          />
        ) : null}
      </div>
      <Flex vertical justify="space-between" style={{ height: "85%" }}>
        <Menu selectedKeys={chooseRoute()} mode="inline" items={items} />
        <AmpUpdateBanner isCollapsed={collapsed} />
      </Flex>
    </Sider>
  );
};

export default Sidebar;
