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

import { Button, Flex, Modal, Tooltip, Typography } from "antd";
import useModal from "src/utils/useModal.ts";
import {
  JobStatus,
  useGetAmpUpdateJobStatus,
  useGetAmpUpdateStatus,
  useUpdateAmpMutation,
} from "src/api/ampMetadataApi.ts";
import messageQueue from "src/utils/messageQueue.ts";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import JobStatusTracker from "src/components/AmpUpdate/JobStatusTracker.tsx";
import { cdlSlate800 } from "src/cuix/variables.ts";
import { RefreshButton } from "src/components/AmpUpdate/RefreshButton.tsx";

const UpdateButton = ({
  setIsModalOpen,
  isCollapsed,
}: {
  setIsModalOpen: Dispatch<SetStateAction<boolean>>;
  isCollapsed: boolean;
}) => {
  return (
    <Flex
      justify="center"
      align="center"
      style={{
        background: cdlSlate800,
        rotate: isCollapsed ? "-450deg" : "0deg",
        transition: "rotate 0.3s",
      }}
    >
      <Tooltip
        title="Your RAG Studio version is out of date. Click here to update to the latest
          version."
      >
        <Button
          danger
          type="primary"
          onClick={() => {
            setIsModalOpen(true);
          }}
        >
          Update Available
        </Button>
      </Tooltip>
    </Flex>
  );
};

const AmpUpdateBanner = ({
  isCollapsed = false,
}: {
  isCollapsed?: boolean;
}) => {
  const { data: ampUpdateStatus } = useGetAmpUpdateStatus();
  const updateModal = useModal();
  const ampUpdateJobStatus = useGetAmpUpdateJobStatus(updateModal.isModalOpen);
  const [hasSeenRestarting, setHasSeenRestarting] = useState(false);
  const updateAmpMutation = useUpdateAmpMutation({
    onSuccess: () => {
      messageQueue.success(
        "RAG Studio update initiated.  Please hold on while we get you the latest features!",
      );
    },
    onError: () => {
      messageQueue.error("Failed to update AMP.");
      updateModal.setIsModalOpen(false);
    },
  });

  useEffect(() => {
    if (ampUpdateJobStatus.data === JobStatus.RESTARTING) {
      setHasSeenRestarting(true);
    }
  }, [ampUpdateJobStatus.data, setHasSeenRestarting]);

  function handleUpdate() {
    updateAmpMutation.mutate({});
  }

  return (
    <>
      {ampUpdateStatus ? (
        <UpdateButton
          setIsModalOpen={updateModal.setIsModalOpen}
          isCollapsed={isCollapsed}
        />
      ) : null}
      <Modal
        okButtonProps={{ style: { display: "none" } }}
        destroyOnHidden={true}
        title="Update RAG Studio to the latest version?"
        open={updateModal.isModalOpen}
        maskClosable={updateAmpMutation.isSuccess}
        onCancel={() => {
          updateModal.handleCancel();
        }}
        cancelText="Close"
      >
        <Typography.Paragraph>
          Updating the AMP will give you access to the latest RAG Studio
          features.
        </Typography.Paragraph>
        <Typography.Paragraph>
          The update can take a few minutes to complete. While the update is
          occurring, you will lose access to RAG Studio.
        </Typography.Paragraph>
        <Flex align="center" justify="center" vertical gap={20}>
          <Button
            danger
            type="primary"
            onClick={handleUpdate}
            loading={updateAmpMutation.isPending}
            disabled={updateAmpMutation.isSuccess}
          >
            Start Update
          </Button>
          {updateAmpMutation.isSuccess ? (
            <JobStatusTracker jobStatus={ampUpdateJobStatus.data} />
          ) : null}
          {hasSeenRestarting &&
          ampUpdateJobStatus.data === JobStatus.SUCCEEDED ? (
            <RefreshButton />
          ) : null}
        </Flex>
      </Modal>
    </>
  );
};

export default AmpUpdateBanner;
