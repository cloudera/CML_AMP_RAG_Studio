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

import { Button, Form, Modal } from "antd";
import { Dispatch, SetStateAction, useContext } from "react";
import CreateSessionForm from "./CreateSessionForm.tsx";
import messageQueue from "src/utils/messageQueue.ts";
import {
  CreateSessionRequest,
  useCreateSessionMutation,
} from "src/api/sessionApi.ts";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { QueryKeys } from "src/api/utils.ts";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import { useNavigate } from "@tanstack/react-router";
import { getDefaultProjectQueryOptions } from "src/api/projectsApi.ts";

const CreateSessionModal = ({
  handleCancel,
  isModalOpen,
  setIsModalOpen,
}: {
  handleCancel: () => void;
  isModalOpen: boolean;
  setIsModalOpen: Dispatch<SetStateAction<boolean>>;
}) => {
  const [form] = Form.useForm<CreateSessionRequest>();
  const queryClient = useQueryClient();
  const {
    dataSourcesQuery: { dataSources },
  } = useContext(RagChatContext);
  const navigate = useNavigate();
  const { data: defaultProject } = useSuspenseQuery(
    getDefaultProjectQueryOptions,
  );
  const { mutate: createSessionMutation } = useCreateSessionMutation({
    onSuccess: async (data) => {
      setIsModalOpen(false);
      await queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getSessions] })
        .then(() => {
          return navigate({
            to: "/chats/$sessionId",
            params: { sessionId: data.id.toString() },
          });
        })
        .finally(() => {
          form.resetFields();
          messageQueue.success("New session created successfully.");
        });
    },
    onError: () => {
      messageQueue.error("Session creation failed.");
    },
  });

  const handleFormSubmission = () => {
    form
      .validateFields()
      .then((values) => {
        const requestBody: CreateSessionRequest = {
          name: values.name,
          dataSourceIds: values.dataSourceIds,
          inferenceModel: values.inferenceModel,
          rerankModel: values.rerankModel,
          responseChunks: values.responseChunks,
          queryConfiguration: {
            enableHyde: values.queryConfiguration.enableHyde,
            enableSummaryFilter: values.queryConfiguration.enableSummaryFilter,
            enableToolCalling: values.queryConfiguration.enableToolCalling,
            selectedTools: values.queryConfiguration.selectedTools,
          },
          projectId: defaultProject.id,
        };
        createSessionMutation(requestBody);
      })
      .catch(() => {
        messageQueue.error("Please fill all the required fields.");
      });
  };

  return (
    <Modal
      title="Chat Settings"
      open={isModalOpen}
      width={600}
      onOk={() => {
        setIsModalOpen(false);
      }}
      onCancel={handleCancel}
      footer={[
        <Button onClick={handleFormSubmission} key="submit" htmlType="submit">
          Create
        </Button>,
      ]}
    >
      <CreateSessionForm form={form} dataSources={dataSources} />
    </Modal>
  );
};

export default CreateSessionModal;
