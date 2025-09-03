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
  MetadataDBProvider,
  ProjectConfig,
  useGetPollingAmpConfig,
  useRestartApplication,
  useUpdateAmpConfig,
} from "src/api/ampMetadataApi.ts";
import { useEffect, useMemo, useState } from "react";
import messageQueue from "src/utils/messageQueue.ts";
import { ModalHook } from "src/utils/useModal.ts";
import { cdlBlue600, cdlGray200, cdlGreen600 } from "src/cuix/variables.ts";
import { ModelSource } from "src/api/modelsApi.ts";
import { FileStorage } from "pages/Settings/AmpSettingsPage.tsx";
import { useSuspenseQuery } from "@tanstack/react-query";

const PROGRESS_STATES = {
  WAITING: {
    percent: 33,
    color: cdlBlue600,
    text: "Waiting",
  },
  RESTARTING: {
    percent: 67,
    color: cdlBlue600,
    text: "Restarting",
  },
  READY: {
    percent: 100,
    color: cdlGreen600,
    text: "Ready",
  },
};

const ProgressIndicator = ({
  hasSeenRestarting,
  config,
  isRestarting,
  waitingToRestart,
}: {
  hasSeenRestarting: boolean;
  config?: ProjectConfig | null;
  isRestarting: boolean;
  waitingToRestart: boolean;
}) => {
  const currentProgress = useMemo(() => {
    if (hasSeenRestarting && config) {
      return PROGRESS_STATES.READY;
    }

    if (isRestarting) {
      return PROGRESS_STATES.RESTARTING;
    }

    if (waitingToRestart) {
      return PROGRESS_STATES.WAITING;
    }

    return PROGRESS_STATES.READY;
  }, [waitingToRestart, isRestarting]);

  return (
    <Progress
      type="circle"
      percent={currentProgress.percent}
      steps={3}
      trailColor={cdlGray200}
      strokeColor={currentProgress.color}
      strokeWidth={10}
      format={() => (
        <Flex align="center" justify="center">
          <Typography.Text style={{ fontSize: 10, textWrap: "wrap" }}>
            {currentProgress.text}
          </Typography.Text>
        </Flex>
      )}
    />
  );
};
const RestartAppModal = ({
  confirmationModal,
  form,
  selectedFileStorage,
  modelProvider,
  selectedMetadataDb,
}: {
  confirmationModal: ModalHook;
  form: FormInstance<ProjectConfig>;
  selectedFileStorage: FileStorage;
  modelProvider?: ModelSource;
  selectedMetadataDb: MetadataDBProvider;
}) => {
  const [polling, setPolling] = useState(false);
  const [hasSeenRestarting, setHasSeenRestarting] = useState(false);
  const restartApplication = useRestartApplication({
    onSuccess: () => {
      setPolling(true);
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
  const { data: config } = useSuspenseQuery(useGetPollingAmpConfig(polling));

  const isRestarting = !config && polling;

  useEffect(() => {
    if (isRestarting) {
      setHasSeenRestarting(true);
    }
  }, [isRestarting, setHasSeenRestarting]);

  useEffect(() => {
    if (config && polling && hasSeenRestarting) {
      setPolling(false);
    }
  }, [setPolling, config, polling, hasSeenRestarting]);

  const handleSubmit = () => {
    form
      .validateFields()
      .then((values) => {
        // Ensure model_provider is always a valid ModelSource (not undefined)
        values.model_provider = modelProvider ?? "Bedrock";
        if (modelProvider === "CAII") {
          values.azure_config = {};
          values.openai_config = {};
        } else if (modelProvider === "Bedrock") {
          values.azure_config = {};
          values.caii_config = {};
          values.openai_config = {};
        } else if (modelProvider === "Azure") {
          values.caii_config = {};
          values.openai_config = {};
        } else if (modelProvider === "OpenAI") {
          values.azure_config = {};
          values.caii_config = {};
        }

        if (selectedFileStorage === "Local") {
          values.aws_config.document_bucket_name = undefined;
          values.aws_config.bucket_prefix = undefined;
          values.summary_storage_provider = "Local";
          values.chat_store_provider = "Local";
        }

        if (selectedMetadataDb === "H2") {
          values.metadata_db_config = {
            jdbc_url: undefined,
            username: undefined,
            password: undefined,
          };
        }

        // clear open search and chromadb configs if QDRANT is selected
        if (values.vector_db_provider === "QDRANT") {
          values.opensearch_config = {
            opensearch_username: undefined,
            opensearch_password: undefined,
            opensearch_endpoint: undefined,
            opensearch_namespace: undefined,
          };
          values.chromadb_config = {
            chromadb_host: undefined,
            chromadb_port: undefined,
            chromadb_api_key: undefined,
            chromadb_namespace: undefined,
          };
        }

        // clear chromadb config if opensearch is selected
        if (values.vector_db_provider === "OPENSEARCH"){
          values.chromadb_config = {
            chromadb_host: undefined,
            chromadb_port: undefined,
            chromadb_api_key: undefined,
            chromadb_namespace: undefined,
          };
        }

        // clear opensearch config if chromadb is selected
        if (values.vector_db_provider === "CHROMADB") {
          values.opensearch_config = {
            opensearch_username: undefined,
            opensearch_password: undefined,
            opensearch_endpoint: undefined,
            opensearch_namespace: undefined,
          };
        }

        updateAmpConfig.mutate(values);
      })
      .catch(() => {
        messageQueue.error("Please fill all required fields");
      });
  };

  const waitingToRestart = polling && !hasSeenRestarting;
  const updateInProgress = updateAmpConfig.isSuccess && polling;

  return (
    <Modal
      title="Update settings"
      okButtonProps={{ style: { display: "none" } }}
      cancelButtonProps={{ disabled: updateInProgress }}
      closable={false}
      open={confirmationModal.isModalOpen}
      destroyOnHidden={true}
      loading={updateAmpConfig.isPending}
      maskClosable={!updateInProgress}
      onCancel={() => {
        setPolling(false);
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
          <ProgressIndicator
            hasSeenRestarting={hasSeenRestarting}
            isRestarting={isRestarting}
            waitingToRestart={waitingToRestart}
            config={config}
          />
        ) : null}
        {updateAmpConfig.isSuccess && !waitingToRestart && !isRestarting ? (
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
