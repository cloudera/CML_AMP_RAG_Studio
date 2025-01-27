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

import { Flex, Form, Input, Modal, Select, Slider } from "antd";
import RequestModels from "pages/RagChatTab/Settings/RequestModels.tsx";
import { useGetLlmModels, useGetRerankingModels } from "src/api/modelsApi.ts";
import { transformModelOptions } from "src/utils/modelUtils.ts";
import { ResponseChunksRange } from "pages/RagChatTab/Settings/ResponseChunksSlider.tsx";
import { useContext } from "react";
import { RagChatContext } from "pages/RagChatTab/State/RagChatContext.tsx";
import {
  UpdateSessionRequest,
  useUpdateSessionMutation,
} from "src/api/sessionApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { QueryKeys } from "src/api/utils.ts";
import { useQueryClient } from "@tanstack/react-query";

const ChatSettingsModal = ({
  open,
  closeModal,
}: {
  open: boolean;
  closeModal: () => void;
}) => {
  const { data: llmModels } = useGetLlmModels();
  const { data: rerankingModels } = useGetRerankingModels();
  const { activeSession } = useContext(RagChatContext);
  const [form] = Form.useForm<Omit<UpdateSessionRequest, "id">>();
  const queryClient = useQueryClient();
  const updateSession = useUpdateSessionMutation({
    onError: (error) => {
      console.error(error);
      messageQueue.error("Failed to update session");
    },
    onSuccess: async () => {
      messageQueue.success("Session updated successfully");
      await queryClient.invalidateQueries({
        queryKey: [QueryKeys.getSessions],
      });
      closeModal();
    },
  });

  if (!activeSession) {
    return null;
  }

  const handleUpdateSession = () => {
    form
      .validateFields()
      .then((values) => {
        const request: UpdateSessionRequest = {
          ...values,
          id: activeSession.id,
        };
        updateSession.mutate(request);
      })
      .catch(() => {
        messageQueue.error("Please fill all the required fields.");
      });
  };

  return (
    <Modal
      title={`Chat Settings: ${activeSession.name}`}
      open={open}
      onCancel={closeModal}
      destroyOnClose={true}
      onOk={handleUpdateSession}
      maskClosable={false}
      width={600}
    >
      <Flex vertical gap={10}>
        <Form autoCorrect="off" form={form} clearOnDestroy={true}>
          <Form.Item
            name="name"
            label="Name"
            initialValue={activeSession.name}
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="inferenceModel"
            label="Response synthesizer model"
            initialValue={
              activeSession.inferenceModel ??
              (llmModels ? llmModels[0].model_id : "")
            }
            rules={[{ required: true, message: "Please select a model" }]}
          >
            <Select options={transformModelOptions(llmModels)} />
          </Form.Item>
          <Form.Item
            name="rerankModel"
            label="Reranking model"
            initialValue={
              activeSession.rerankModel ??
              (rerankingModels ? rerankingModels[0].model_id : "")
            }
          >
            <Select options={transformModelOptions(rerankingModels)} />
          </Form.Item>
          <RequestModels />
          <Form.Item
            name="responseChunks"
            initialValue={activeSession.responseChunks}
            label="Maximum number of documents"
          >
            <Slider marks={ResponseChunksRange} min={1} max={10} />
          </Form.Item>
        </Form>
      </Flex>
    </Modal>
  );
};

export default ChatSettingsModal;
