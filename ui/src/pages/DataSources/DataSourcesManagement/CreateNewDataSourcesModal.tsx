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

import { Button, Form, Modal } from "antd";
import {
  DataSourceBaseType,
  useCreateDataSourceMutation,
} from "src/api/dataSourceApi.ts";
import { QueryKeys } from "src/api/utils.ts";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import messageQueue from "src/utils/messageQueue";
import DataSourcesForm, {
  dataSourceCreationInitialValues,
  DataSourcesFormProps,
} from "./DataSourcesForm";
import { Dispatch, SetStateAction } from "react";

const CreateNewDataSourcesModal = ({
  handleCancel,
  isModalOpen,
  setIsModalOpen,
}: {
  handleCancel: () => void;
  isModalOpen: boolean;
  setIsModalOpen: Dispatch<SetStateAction<boolean>>;
}) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [form] = Form.useForm<DataSourcesFormProps["initialValues"]>();

  const createDatasourceMutation = useCreateDataSourceMutation({
    onSuccess: (data: DataSourceBaseType) => {
      setIsModalOpen(false);
      queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getDataSources] })
        .then(() => {
          return navigate({
            to: "/data/$dataSourceId",
            params: { dataSourceId: data.id.toString() },
          });
        })
        .catch(() => {
          messageQueue.error("Failed to reload knowledge bases");
        })
        .finally(() => {
          messageQueue.success("New knowledge base created successfully.");
        });
    },
    onError: () => {
      messageQueue.error("Knowledge Base save failed.");
    },
  });

  const handleFormSubmission = () => {
    form
      .validateFields()
      .then((values) => {
        createDatasourceMutation.mutate(values);
      })
      .catch(() => {
        messageQueue.error("Please fill all the required fields.");
      });
  };

  return (
    <Modal
      title="New Knowledge Base"
      open={isModalOpen}
      width={600}
      onCancel={handleCancel}
      footer={[
        <Button onClick={handleFormSubmission} key="submit" htmlType="submit">
          Create
        </Button>,
      ]}
    >
      <DataSourcesForm
        form={form}
        updateMode={false}
        initialValues={dataSourceCreationInitialValues}
      />
    </Modal>
  );
};

export default CreateNewDataSourcesModal;
