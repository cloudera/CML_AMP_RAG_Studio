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

import { groupBy } from "lodash";
import { Session } from "src/api/sessionApi.ts";
import { useNavigate } from "@tanstack/react-router";
import { ItemType } from "antd/lib/menu/interface";
import { Typography } from "antd";
import { format, parse } from "date-fns";
import SessionItem from "pages/RagChatTab/Sessions/SessionItem.tsx";
import { MenuItem } from "pages/RagChatTab/Sessions/SessionSidebar.tsx";
import { useGetDefaultProject } from "src/api/projectsApi.ts";

export const defaultSessionItems = (sessions: Session[]): MenuItem => {
  const navigate = useNavigate();
  const { data: defaultProject } = useGetDefaultProject();

  const defaultSessions = sessions.filter(
    (session) => defaultProject?.id === session.projectId,
  );
  const defaultSessionsByDate = groupBy(defaultSessions, (session) => {
    const relevantTime = session.lastInteractionTime || session.timeUpdated;
    return format(relevantTime * 1000, "yyyyMMdd");
  });
  const sortedDates = Object.keys(defaultSessions).sort().reverse();
  debugger;
  const items: ItemType[][] = sortedDates.map((date) => {
    const dateItem: ItemType = {
      key: date,
      type: "group",
      label: (
        <Typography.Text strong style={{ paddingLeft: 12 }}>
          {parse(date, "yyyyMMdd", new Date()).toDateString()}
        </Typography.Text>
      ),
    };

    const sessionItems: ItemType[] = defaultSessionsByDate[date].map(
      (session) => {
        return {
          key: session.id.toString(),
          label: <SessionItem session={session} />,
          onClick: () => {
            navigate({
              to: `/sessions/${session.id.toString()}`,
            }).catch(() => null);
          },
        };
      },
    );

    return [
      { type: "divider", key: `divider-${dateItem.key?.toString() ?? ""}` },
      dateItem,
      ...sessionItems,
    ];
  });

  return [...items.flatMap((item) => item)];
};
