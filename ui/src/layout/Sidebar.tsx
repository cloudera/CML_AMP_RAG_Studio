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

import React, { useRef } from "react";
import { DatabaseFilled, DesktopOutlined } from "@ant-design/icons";
import { Flex, Image, Layout, Menu, MenuProps, Tag, Typography } from "antd";
import { useMatchRoute, useNavigate } from "@tanstack/react-router";
import Images from "src/components/images/Images.ts";
import LightbulbIcon from "src/cuix/icons/LightbulbIcon";
import { cdlAmber200, cdlAmber900 } from "src/cuix/variables.ts";
import ThumbUpIcon from "src/cuix/icons/ThumbUpIcon";
import useModal from "src/utils/useModal.ts";
import FeedbackModal from "src/components/Feedback/FeedbackModal.tsx";

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
  const matchRoute = useMatchRoute();
  const navigate = useNavigate();
  const ref = useRef<HTMLDivElement>(null);
  const feedbackModal = useModal();

  const navToRagApp = () => {
    navigate({ to: "/sessions" })
      .then(() => null)
      .catch(() => null);
    return;
  };

  const navToData = () => {
    navigate({ to: "/data" })
      .then(() => null)
      .catch(() => null);
    return;
  };

  const navToModels = () => {
    navigate({ to: "/models" })
      .then(() => null)
      .catch(() => null);
  };

  const popupFeedback = () => {
    feedbackModal.setIsModalOpen(true);
  };

  const baseItems: MenuItem[] = [
    {
      label: (
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
      <DesktopOutlined />,
    ),
    getItem(
      <div data-testid="data-management-nav">Knowledge Bases</div>,
      "data",
      navToData,
      <DatabaseFilled />,
    ),
  ];

  const models = getItem(
    <div data-testid="data-management-nav">Models</div>,
    "models",
    navToModels,
    <DatabaseFilled />,
  );

  const feedbackItem = getItem(
    <div data-testid="data-management-nav">Leave Feedback</div>,
    "leave-feedback",
    popupFeedback,
    <ThumbUpIcon />,
  );

  const items = [...baseItems, models, feedbackItem];

  function chooseRoute() {
    if (matchRoute({ to: "/data", fuzzy: true })) {
      return ["data"];
    } else if (matchRoute({ to: "/sessions", fuzzy: true })) {
      return ["chat"];
    } else if (matchRoute({ to: "/models", fuzzy: true })) {
      return ["models"];
    } else {
      return ["chat"];
    }
  }

  return (
    <Sider width={250} ref={ref} collapsed={false}>
      <div style={{ padding: 20 }}>
        <Image
          src={Images.ClouderaSmall}
          preview={false}
          height={36}
          style={{ paddingRight: 5 }}
        />
        <Image src={Images.RagStudioProduct} preview={false} />
      </div>
      <Menu selectedKeys={chooseRoute()} mode="inline" items={items} />
      <FeedbackModal
        handleCancel={() => {
          feedbackModal.setIsModalOpen(false);
        }}
        isModalOpen={feedbackModal.isModalOpen}
      />
    </Sider>
  );
};

export default Sidebar;
