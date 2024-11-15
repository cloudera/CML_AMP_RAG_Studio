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

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Button, Card, Flex, Form, Input, Modal, Typography } from "antd";
import DataSourcesForm, {
  DataSourcesFormProps,
} from "pages/DataSources/DataSourcesManagement/DataSourcesForm.tsx";
import { DataSourceContext } from "pages/DataSources/Layout.tsx";
import { useContext, useState } from "react";
import {
  deleteDataSourceMutation,
  useUpdateDataSourceMutation,
} from "src/api/dataSourceApi.ts";
import { MutationKeys, QueryKeys } from "src/api/utils.ts";
import { DataSourceUpdateRequest } from "src/services/api/api";
import messageQueue from "src/utils/messageQueue.ts";

const IndexSettings = () => {
  const dataSourceResponse = useContext(DataSourceContext);
  const { data } = dataSourceResponse;
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const navigate = useNavigate();
  const [confirmationText, setConfirmationText] = useState("");
  const [form] = Form.useForm<DataSourcesFormProps["initialValues"]>();
  const queryClient = useQueryClient();
  const {
    mutate: updateDataSourceMutate,
    isPending: isUpdateDataSourcePending,
  } = useUpdateDataSourceMutation({
    onSuccess: () => {
      messageQueue.success("Knowledge base updated successfully");
      return queryClient.invalidateQueries({
        queryKey: [QueryKeys.getDataSourceById],
      });
    },
    onError: (res: Error) => {
      messageQueue.error("Failed to update knowledge base : " + res.message);
    },
  });

  const showModal = () => {
    setIsDeleteModalOpen(true);
  };

  const { mutate: deleteMe } = useMutation({
    mutationKey: [MutationKeys.deleteDataSource],
    mutationFn: () => {
      if (data) {
        return deleteDataSourceMutation(data.id);
      }
      return Promise.resolve();
    },
    onSuccess: () => {
      messageQueue.success("Knowledge base deleted successfully");
      return navigate({
        to: "/data",
      });
    },
    onError: (res: Error) => {
      messageQueue.error("Failed to delete knowledge base : " + res.message);
    },
  });

  const deleteDataSource = () => {
    deleteMe();
  };

  const handleConfirmationText = (text: string) => {
    setConfirmationText(text);
  };

  const handleFormSubmission = () => {
    form
      .validateFields()
      .then((values) => {
        if (data) {
          const payload: DataSourceUpdateRequest = { ...values };
          updateDataSourceMutate({ id: data.id, request: payload });
        }
      })
      .catch(() => {
        messageQueue.error("Please fill all the required fields.");
      });
  };

  return (
    <Flex vertical align="left" style={{ width: "100%" }} gap={20}>
      <Card
        title="Edit knowledge base settings"
        actions={[
          <Flex align="left" gap={15} style={{ paddingLeft: 20 }}>
            <Button
              loading={isUpdateDataSourcePending}
              onClick={handleFormSubmission}
              style={{ width: 120, paddingLeft: 15 }}
            >
              Update
            </Button>
          </Flex>,
        ]}
      >
        <Flex
          vertical
          align="baseline"
          justify="left"
          gap={20}
          style={{ width: "100%", paddingLeft: 25, maxWidth: 600 }}
        >
          {data ? (
            <DataSourcesForm
              form={form}
              updateMode={true}
              initialValues={data}
            />
          ) : null}
        </Flex>
      </Card>
      <Flex align="baseline" justify="left" style={{ width: "100%" }}>
        <Typography style={{ paddingLeft: 15 }}>
          Delete knowledge base:
        </Typography>
        <Button
          danger
          style={{ width: 120, marginLeft: 20 }}
          onClick={showModal}
        >
          Delete
        </Button>
      </Flex>
      <Modal
        title="Delete this knowledge base?"
        open={isDeleteModalOpen}
        onOk={deleteDataSource}
        okText={"Yes, delete it!"}
        okButtonProps={{
          danger: true,
          disabled: confirmationText !== "delete",
        }}
        onCancel={() => {
          setIsDeleteModalOpen(false);
        }}
      >
        <Typography>
          Deleting a knowledge base is permanent and cannot be undone
        </Typography>
        <Input
          style={{ marginTop: 15 }}
          placeholder='type "delete" to confirm'
          onChange={(e) => {
            handleConfirmationText(e.target.value);
          }}
        />
      </Modal>
    </Flex>
  );
};

export default IndexSettings;
