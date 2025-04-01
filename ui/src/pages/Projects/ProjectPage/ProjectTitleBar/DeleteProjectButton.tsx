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

import { Project, useDeleteProject } from "src/api/projectsApi.ts";
import { useLocation, useNavigate } from "@tanstack/react-router";
import useModal from "src/utils/useModal.ts";
import { useState } from "react";
import messageQueue from "src/utils/messageQueue.ts";
import { Button, Input, Modal, Typography } from "antd";
import DeleteIcon from "src/cuix/icons/DeleteIcon.ts";
import { cdlRed600 } from "src/cuix/variables.ts";
import { useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "src/api/utils.ts";

export const DeleteProjectButton = ({ project }: { project: Project }) => {
  const location = useLocation();
  const deleteProjectModal = useModal();
  const [confirmationText, setConfirmationText] = useState("");
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { mutate: deleteProjectMutate } = useDeleteProject({
    onSuccess: () => {
      messageQueue.success("Project deleted successfully");
      queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getProjects] })
        .catch(() => {
          messageQueue.error("Failed to refresh projects");
        });
      if (location.pathname.includes("/chats/")) {
        return navigate({
          to: "/chats",
        });
      }
      return navigate({
        to: "/projects",
      });
    },
    onError: (res: Error) => {
      messageQueue.error("Failed to delete project : " + res.message);
    },
  });

  const deleteProject = () => {
    deleteProjectMutate(project.id);
  };

  const handleConfirmationText = (text: string) => {
    setConfirmationText(text);
  };

  return (
    <>
      <Button
        icon={<DeleteIcon style={{ width: 18, height: 22 }} />}
        type="text"
        style={{ color: cdlRed600 }}
        onClick={() => {
          deleteProjectModal.setIsModalOpen(true);
        }}
      />
      <Modal
        title="Delete this Project?"
        open={deleteProjectModal.isModalOpen}
        onOk={deleteProject}
        okText={"Yes, delete it!"}
        okButtonProps={{
          danger: true,
          disabled: confirmationText !== "delete",
        }}
        onCancel={() => {
          deleteProjectModal.setIsModalOpen(false);
        }}
      >
        <Typography>
          Deleting a Project is permanent and cannot be undone
        </Typography>
        <Input
          style={{ marginTop: 15 }}
          placeholder='type "delete" to confirm'
          onChange={(e) => {
            handleConfirmationText(e.target.value);
          }}
        />
      </Modal>
    </>
  );
};
