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

import { useContext } from "react";
import { Card, Flex, Tooltip, Typography } from "antd";
import {
  CloseCircleFilled,
  PlusCircleOutlined,
  RightCircleOutlined,
} from "@ant-design/icons";
import { cdlGray400, cdlGreen600 } from "src/cuix/variables.ts";
import { DataSourceTag } from "pages/RagChatTab/SessionsSidebar/SidebarItems/MoveSession/DataSourceTag.tsx";

import { MoveSessionContext } from "pages/RagChatTab/SessionsSidebar/SidebarItems/MoveSession/MoveSessionContext.tsx";

const TransferItems = () => {
  const {
    session,
    dataSources,
    dataSourcesToTransfer,
    setDataSourcesToTransfer,
    dataSourcesForProject,
    dataSourcesForProjectIsLoading,
    selectedProject,
  } = useContext(MoveSessionContext);
  const removedDataSources = session.dataSourceIds.filter(
    (sessionDataSource) => {
      return !dataSourcesToTransfer.includes(sessionDataSource);
    },
  );

  const handleAddDataSource = (dataSourceId: number) => {
    setDataSourcesToTransfer((prev) => [...prev, dataSourceId]);
  };

  const handleRemoveDataSource = (dataSourceId: number) => {
    setDataSourcesToTransfer((prev) =>
      prev.filter((id) => id !== dataSourceId),
    );
  };

  const diff = session.dataSourceIds.filter(
    (dataSourceId) =>
      !dataSourcesForProject?.some(
        (projectDs) => projectDs.id === dataSourceId,
      ),
  );

  const showDataSourceCard =
    Boolean(selectedProject) &&
    !dataSourcesForProjectIsLoading &&
    diff.length > 0;

  return (
    <Flex vertical align="center" justify="center" style={{ width: 200 }}>
      <RightCircleOutlined style={{ fontSize: 20, height: 56 }} />
      {showDataSourceCard ? (
        <Card
          title={<Typography>New knowledge base</Typography>}
          style={{ flex: 1 }}
        >
          {dataSourcesToTransfer.map((dataSourceToTransfer) => (
            <DataSourceTag
              key={dataSourceToTransfer}
              handleClose={handleRemoveDataSource}
              dataSources={dataSources}
              dataSourceId={dataSourceToTransfer}
              color={cdlGreen600}
              closeIcon={
                <Tooltip title="Exclude from transfer">
                  <CloseCircleFilled style={{ marginLeft: 8 }} />
                </Tooltip>
              }
            />
          ))}
          {removedDataSources.map((removedDataSourceId) => (
            <DataSourceTag
              key={removedDataSourceId}
              handleClose={handleAddDataSource}
              color={cdlGray400}
              dataSources={dataSources}
              dataSourceId={removedDataSourceId}
              closeIcon={
                <Tooltip title="Include in transfer">
                  <PlusCircleOutlined style={{ marginLeft: 8 }} />
                </Tooltip>
              }
            />
          ))}
        </Card>
      ) : (
        <div style={{ flex: 1 }} />
      )}
    </Flex>
  );
};

export default TransferItems;
