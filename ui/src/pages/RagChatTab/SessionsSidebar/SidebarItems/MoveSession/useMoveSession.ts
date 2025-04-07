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

import { Session, useUpdateSessionMutation } from "src/api/sessionApi.ts";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import messageQueue from "src/utils/messageQueue.ts";
import { QueryKeys } from "src/api/utils.ts";
import { ModalHook } from "src/utils/useModal.ts";
import { Project } from "src/api/projectsApi.ts";

interface UseMoveSessionProps {
  session: Session;
  selectedProject?: number;
  projects?: Project[];
  handleCancel: ModalHook["handleCancel"];
}

export const useMoveSession = ({
  session,
  selectedProject,
  projects,
  handleCancel,
}: UseMoveSessionProps) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useUpdateSessionMutation({
    onSuccess: () => {
      const project = projects?.find((proj) => proj.id === selectedProject);
      if (!project) {
        messageQueue.error("Failed to find project");
        return;
      }
      messageQueue.success(
        `Session ${session.name} moved to project ${project.name}`,
      );
      queryClient
        .invalidateQueries({ queryKey: [QueryKeys.getSessions] })
        .catch(() => {
          messageQueue.error("Failed to refetch session");
        });
      queryClient
        .invalidateQueries({
          queryKey: [
            QueryKeys.getDataSourcesForProject,
            { projectId: project.id },
          ],
        })
        .catch(() => {
          messageQueue.error("Failed to refetch project");
        });
      navigate({
        to: "/chats/projects/$projectId/sessions/$sessionId",
        params: {
          projectId: project.id.toString(),
          sessionId: session.id.toString(),
        },
      }).catch(() => {
        messageQueue.error("Failed to navigate to session");
      });
      handleCancel();
    },
    onError: () => {
      messageQueue.error("Failed to update session");
    },
  });
};
