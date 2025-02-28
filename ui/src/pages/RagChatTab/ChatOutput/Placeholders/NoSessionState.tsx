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

import { Button, Flex, Image, Typography } from "antd";
import CreateSessionModal from "pages/RagChatTab/Sessions/CreateSessionModal.tsx";
import useModal from "src/utils/useModal.ts";
import { PlusCircleOutlined } from "@ant-design/icons";
import Images from "src/components/images/Images.ts";

const NoSessionState = () => {
  const { isModalOpen, setIsModalOpen, showModal, handleCancel } = useModal();
  return (
    <Flex style={{ height: "100%" }} vertical>
      <Flex
        vertical
        align="center"
        justify="center"
        gap={24}
        style={{ height: "100%" }}
      >
        <Flex vertical align="center" gap={16}>
          <Image
            src={Images.BrandTalking}
            alt="Machines Chatting"
            style={{ width: 80 }}
            preview={false}
          />
          <Typography.Title level={4} style={{ fontWeight: 300, margin: 0 }}>
            Welcome to RAG Studio
          </Typography.Title>
        </Flex>
        <Typography.Text
          style={{ padding: 10, textAlign: "center", width: "80%" }}
        >
          You can use this chat to get answers to any questions related to your
          company data, configure your services, analyze and much more.
        </Typography.Text>
        <Button
          type="primary"
          onClick={showModal}
          icon={<PlusCircleOutlined />}
        >
          Create New Chat
        </Button>
        <CreateSessionModal
          isModalOpen={isModalOpen}
          handleCancel={handleCancel}
          setIsModalOpen={setIsModalOpen}
        />
      </Flex>
    </Flex>
  );
};

export default NoSessionState;
