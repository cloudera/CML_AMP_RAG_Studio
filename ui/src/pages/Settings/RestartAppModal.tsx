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
import { Button, Flex, FormInstance, Modal, Progress, Typography } from "antd";
import {
  ProjectConfig,
  useGetAmpConfig,
  useRestartApplication,
  useUpdateAmpConfig,
} from "src/api/ampMetadataApi.ts";
import { useEffect, useState } from "react";
import messageQueue from "src/utils/messageQueue.ts";
import { ModalHook } from "src/utils/useModal.ts";
import { cdlAmber400, cdlGray200, cdlGreen600 } from "src/cuix/variables.ts";

const RestartAppModal = ({
  confirmationModal,
  form,
}: {
  confirmationModal: ModalHook;
  form: FormInstance<ProjectConfig>;
}) => {
  const [startPolling, setStartPolling] = useState(false);
  const [hasSeenRestarting, setHasSeenRestarting] = useState(false);
  const restartApplication = useRestartApplication({
    onSuccess: () => {
      setStartPolling(true);
    },
    onError: () => {
      messageQueue.error("Failed to restart application");
    },
  });
  const updateAmpConfig = useUpdateAmpConfig({
    onError: (err) => {
      messageQueue.error(err.message);
    },
    onSuccess: () => {
      messageQueue.success(
        "Settings updated successfully.  Restarting the application.",
      );
      restartApplication.mutate({});
    },
  });
  const {
    data: projectConfig,
    isSuccess: isProjectConfigSuccess,
    isError: isProjectConfigError,
  } = useGetAmpConfig(startPolling);
  console.log({
    projectConfig,
    isProjectConfigSuccess,
    isProjectConfigError,
  });

  const inPollingMode = isProjectConfigError && !projectConfig;
  useEffect(() => {
    if (inPollingMode) {
      setHasSeenRestarting(true);
    }
  }, [inPollingMode, setHasSeenRestarting]);

  const handleSubmit = () => {
    form
      .validateFields()
      .then((values) => {
        updateAmpConfig.mutate(values);
      })
      .catch(() => {
        messageQueue.error("Please fill all required fields");
      });
  };

  return (
    <Modal
      title="Update settings"
      okButtonProps={{ style: { display: "none" } }}
      open={confirmationModal.isModalOpen}
      destroyOnClose={true}
      loading={updateAmpConfig.isPending}
      onCancel={() => {
        confirmationModal.setIsModalOpen(false);
      }}
    >
      <Flex align="center" justify="center" vertical gap={20}>
        <Typography>
          Are you sure you want to update the settings? This will restart the
          application and may take a few minutes.
        </Typography>
        <Button
          type="primary"
          onClick={handleSubmit}
          loading={updateAmpConfig.isPending}
          disabled={updateAmpConfig.isSuccess}
        >
          Update Settings
        </Button>
        {updateAmpConfig.isSuccess ? (
          <Progress
            type="circle"
            percent={inPollingMode ? 10 : 100}
            steps={2}
            trailColor={cdlGray200}
            strokeColor={inPollingMode ? cdlAmber400 : cdlGreen600}
            strokeWidth={10}
            format={() => (
              <Flex align="center" justify="center">
                <Typography.Text style={{ fontSize: 10, textWrap: "wrap" }}>
                  {inPollingMode ? "Restarting" : "Ready"}
                </Typography.Text>
              </Flex>
            )}
          />
        ) : null}
        {hasSeenRestarting && projectConfig ? (
          <>
            <Typography.Text>
              RAG Studio has been updated successfully. Please refresh the page
              to use the latest configuration.
            </Typography.Text>
            <Button
              type="primary"
              onClick={() => {
                location.reload();
              }}
            >
              Refresh
            </Button>
          </>
        ) : null}
      </Flex>
    </Modal>
  );
};

export default RestartAppModal;
