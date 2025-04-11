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

import React from "react";
import {
  CommentOutlined,
  DatabaseOutlined,
  LineChartOutlined,
  RobotFilled,
  SettingOutlined,
} from "@ant-design/icons";
import {Flex, Menu, MenuProps, Tag, Tooltip, Typography} from "antd";
import { useMatchRoute, useNavigate } from "@tanstack/react-router";
import LightbulbIcon from "src/cuix/icons/LightbulbIcon";
import {
  cdlAmber200,
  cdlAmber900,
  cdlBlue200,
  cdlGray200,
  cdlSlate800,
} from "src/cuix/variables.ts";
import AmpUpdateBanner from "src/components/AmpUpdate/AmpUpdateBanner.tsx";

import "./style.css";
import { useGetAmpConfig } from "src/api/ampMetadataApi.ts";

const TopNav: React.FC = () => {
  const matchRoute = useMatchRoute();
  const navigate = useNavigate();
  const { data: config } = useGetAmpConfig();

  const navigateTo = (path: string) => () => {
    navigate({ to: path }).catch(() => null);
  };

  const TechPreviewItem = () => {
    return (
      <Flex
        justify="center"
        align="center"
        style={{
          paddingRight: 20,
          backgroundColor: cdlSlate800,
        }}
      >
        <Tag
          color={cdlAmber200}
          style={{
            borderRadius: 20,
            height: 24,
            paddingLeft: 6,
            paddingRight: 8,
            marginLeft: 10,
            cursor: "default",
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
      </Flex>
    );
  };

  const baseItems: MenuItem[] = [
    getItem(
      <span data-testid="rag-apps-nav">Chats</span>,
      "chat",
      !config?.is_valid_config,
      navigateTo("/chats"),
      <CommentOutlined />,
    ),
    getItem(
      <span data-testid="data-management-nav">Knowledge Bases</span>,
      "data",
      !config?.is_valid_config,
      navigateTo("/data"),
      <DatabaseOutlined />,
    ),
  ];

  const models = getItem(
    <span data-testid="models-nav">Models</span>,
    "models",
    !config?.is_valid_config,
    navigateTo("/models"),
    <RobotFilled />,
  );

  const analyticsItem = getItem(
    <span data-testid="analytics-nav">Analytics</span>,
    "analytics",
    !config?.is_valid_config,
    navigateTo("/analytics"),
    <LineChartOutlined />,
  );

  const settingsItem = getItem(
    <span data-testid="settings-nav">Settings</span>,
    "settings",
    false,
    navigateTo("/settings"),
    <SettingOutlined />,
  );

  const items = [...baseItems, models, analyticsItem];
  if (config) {
    items.push(settingsItem);
  }

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
    <Flex justify="space-between" style={{ width: "100vw" }}>
      <Menu
        selectedKeys={chooseRoute()}
        mode="horizontal"
        items={items}
        style={{ width: "100%" }}
      />
      <AmpUpdateBanner />
      <TechPreviewItem />
    </Flex>
  );
};

type MenuItem = Required<MenuProps>["items"][number];

function getItem(
  label: React.ReactNode,
  key: React.Key,
  disabled: boolean,
  onClick: () => void,
  icon?: React.ReactNode,
  children?: MenuItem[],
): MenuItem {
  return {
    key,
    icon,
    children,
   <Tooltip>{label}</Tooltip>,
    onClick,
    disabled: disabled,
  } as MenuItem;
}

export default TopNav;
