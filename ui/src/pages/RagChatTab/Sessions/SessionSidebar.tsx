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

import { useContext } from "react";
import { Session } from "src/api/sessionApi.ts";
import {
  Button,
  ConfigProvider,
  Flex,
  Form,
  Input,
  Layout,
  Menu,
  MenuProps,
  Modal,
  theme,
  Typography,
} from "antd";
import {
  cdlGray200,
  cdlGray800,
  cdlSlate800,
  cdlWhite,
} from "src/cuix/variables.ts";
import { Dictionary } from "lodash";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { sessionItems } from "pages/RagChatTab/Sessions/SessionItems.tsx";
import { newChatItem } from "pages/RagChatTab/Sessions/NewChatItem.tsx";
import { ItemType } from "antd/lib/menu/interface";
import Images from "src/components/images/Images.ts";
import "./index.css";
import {
  Project,
  useCreateProject,
  useGetProjects,
} from "src/api/projectsApi.ts";
import {
  FolderAddOutlined,
  FolderOpenFilled,
  FolderOpenOutlined,
  FolderOutlined,
  FolderTwoTone,
  FolderViewOutlined,
  PlusCircleOutlined,
  ProjectOutlined,
} from "@ant-design/icons";
import useModal from "src/utils/useModal.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "src/api/utils.ts";

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

const ProjectsHeaderItem = () => {
  const createProjectModal = useModal();
  const [form] = Form.useForm<{ name: string }>();
  const queryClient = useQueryClient();

  const createProject = useCreateProject({
    onSuccess: () => {
      createProjectModal.setIsModalOpen(false);
      queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getProjects] })
        .catch(() => {
          messageQueue.error("Failed to refresh projects");
        });
    },
    onError: () => {
      messageQueue.error("Failed to create a new project");
    },
  });
  const handleCreateNewProject = () => {
    form
      .validateFields()
      .then((values) => {
        createProject.mutate({ name: values.name });
      })
      .catch(() => null);
  };

  return (
    <Flex
      justify="space-between"
      gap={6}
      style={{ paddingLeft: 12, paddingTop: 8 }}
    >
      <Flex gap={6} align="center">
        <ProjectOutlined style={{ fontSize: 18 }} />
        <Typography.Text type="secondary">Projects</Typography.Text>
      </Flex>
      <Button
        type="text"
        icon={<PlusCircleOutlined />}
        onClick={() => {
          createProjectModal.setIsModalOpen(true);
        }}
      />
      <Modal
        title="Create New Project"
        open={createProjectModal.isModalOpen}
        onCancel={() => {
          createProjectModal.setIsModalOpen(false);
        }}
        footer={
          <Button onClick={handleCreateNewProject} type="primary">
            OK
          </Button>
        }
      >
        <Form form={form}>
          <Form.Item
            name="name"
            label="Project name"
            rules={[
              { required: true, message: "Please provide a project name" },
            ]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Flex>
  );
};

const projectSessionSidebarItem = ({
  project,
}: {
  project: Project;
}): ItemType => {
  return {
    key: project.id,
    icon: <FolderOutlined />,
    label: (
      <Typography.Text strong style={{ paddingLeft: 12 }}>
        {project.name}
      </Typography.Text>
    ),
  };
};

export function SessionSidebar({
  sessionsByDate,
}: {
  sessionsByDate: Dictionary<Session[]>;
}) {
  const { activeSession } = useContext(RagChatContext);
  const { data: projects } = useGetProjects();

  const projectItems: ItemType[] = projects
    ? projects.map((project) => {
        return projectSessionSidebarItem({ project });
      })
    : [];

  const items: ItemType[] = [
    ...newChatItem(18),
    { type: "divider", key: "newChatDivider" },
    {
      type: "group",
      label: <ProjectsHeaderItem />,
    },
    ...projectItems,
    {
      type: "group",
      label: (
        <Flex gap={6} style={{ paddingLeft: 12, paddingTop: 8 }}>
          <Images.History style={{ fontSize: 18 }} />
          <Typography.Text type="secondary">Chat History</Typography.Text>
        </Flex>
      ),
    },
    ...sessionItems(sessionsByDate),
  ];

  return (
    <ConfigProvider theme={SessionMenuTheme}>
      <div className="session-sider">
        <Sider width={250} style={{ height: "88vh" }}>
          <Menu
            selectedKeys={[activeSession?.id.toString() ?? ""]}
            mode="inline"
            style={{
              backgroundColor: cdlWhite,
              height: "100%",
              borderRight: 0,
              overflowY: "auto",
              scrollbarWidth: "thin",
            }}
            items={items}
          />
        </Sider>
      </div>
    </ConfigProvider>
  );
}
