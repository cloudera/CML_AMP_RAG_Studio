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

import { Session } from "src/api/sessionApi.ts";
import { DataSourceType } from "src/api/dataSourceApi.ts";
import { Button, Flex, Layout, Typography } from "antd";
import ChatSettingsModal from "pages/RagChatTab/Settings/ChatSettingsModal.tsx";
import useModal from "src/utils/useModal.ts";
import SettingsIcon from "src/cuix/icons/SettingsIcon";
import { cdlBlue600 } from "src/cuix/variables.ts";
import CreateSessionModal from "pages/RagChatTab/SessionsSidebar/CreateSession/CreateSessionModal.tsx";

const { Header } = Layout;

function getHeaderTitle(activeSession?: Session): string {
  if (!activeSession?.name) {
    return "...";
  }
  return activeSession.name;
}

export const RagChatHeader = ({
  activeSession,
  currentDataSources,
}: {
  activeSession?: Session;
  currentDataSources: DataSourceType[];
}) => {
  const settingsModal = useModal();

  const handleOpenModal = () => {
    settingsModal.setIsModalOpen(!settingsModal.isModalOpen);
  };

  return (
    <Header style={{ padding: 0, margin: 20, width: "95%" }}>
      <Flex justify="space-between">
        <Flex vertical>
          <Typography.Title
            level={5}
            style={{
              fontWeight: "normal",
              fontSize: 14,
              marginTop: 5,
              marginBottom: 0,
            }}
          >
            {getHeaderTitle(activeSession)}
          </Typography.Title>
          {currentDataSources.length > 0 ? (
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              Knowledge bases:{" "}
              {currentDataSources.map((ds) => ds.name).join(", ")}
            </Typography.Text>
          ) : null}
        </Flex>
        <Button
          style={{ width: 140, alignItems: "center" }}
          onClick={handleOpenModal}
        >
          <Flex
            align="center"
            gap={5}
            style={{ margin: 0, padding: 0, height: "100%" }}
          >
            <SettingsIcon color={cdlBlue600} fontSize={18} />
            <Typography.Text style={{ color: cdlBlue600 }}>
              Chat Settings
            </Typography.Text>
          </Flex>
        </Button>
      </Flex>{" "}
      {activeSession ? (
        <ChatSettingsModal
          open={settingsModal.isModalOpen}
          closeModal={() => {
            settingsModal.setIsModalOpen(false);
          }}
        />
      ) : (
        <CreateSessionModal
          isModalOpen={settingsModal.isModalOpen}
          handleCancel={settingsModal.handleCancel}
          setIsModalOpen={settingsModal.setIsModalOpen}
        />
      )}
    </Header>
  );
};
