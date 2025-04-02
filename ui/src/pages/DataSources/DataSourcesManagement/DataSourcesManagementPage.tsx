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

import { Button, Flex, Typography } from "antd";
import { useEffect, useState } from "react";
import DataSourcesList from "pages/DataSources/DataSourcesManagement/DataSourcesList.tsx";
import CreateNewDataSourcesModal from "pages/DataSources/DataSourcesManagement/CreateNewDataSourcesModal.tsx";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { getDataSourcesQueryOptions } from "src/api/dataSourceApi.ts";
import { useSuspenseQuery } from "@tanstack/react-query";
import NoDataSources from "src/components/GettingStarted/NoDataSources.tsx";

const DataSourcesManagementPage = () => {
  const navigate = useNavigate();
  const dataSources = useSuspenseQuery(getDataSourcesQueryOptions);
  const search: { create: boolean } = useSearch({
    from: "/_layout/data/_layout-datasources",
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    navigate({ to: "/data" }).catch(() => null);
  };

  useEffect(() => {
    if (search.create) {
      setIsModalOpen(true);
    }
  }, [search]);

  if (dataSources.data.length === 0) {
    return (
      <Flex align="center" justify="center" style={{ height: "85vh" }}>
        <NoDataSources />
        <CreateNewDataSourcesModal
          isModalOpen={isModalOpen}
          handleCancel={handleCancel}
          setIsModalOpen={setIsModalOpen}
        />
      </Flex>
    );
  }

  return (
    <Flex vertical align="center">
      <Typography.Title>RAG Knowledge Bases</Typography.Title>
      <Flex
        vertical
        align="end"
        style={{ width: "80%", maxWidth: 1000 }}
        gap={20}
      >
        <Button onClick={showModal}>Create Knowledge Base</Button>

        <DataSourcesList
          dataSources={dataSources.data}
          dataSourcesLoading={dataSources.isPending}
        />
      </Flex>
      <CreateNewDataSourcesModal
        isModalOpen={isModalOpen}
        handleCancel={handleCancel}
        setIsModalOpen={setIsModalOpen}
      />
    </Flex>
  );
};

export default DataSourcesManagementPage;
