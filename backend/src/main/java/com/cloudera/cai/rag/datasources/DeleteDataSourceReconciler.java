/*
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
 */

package com.cloudera.cai.rag.datasources;

import com.cloudera.cai.rag.configuration.DatabaseOperations;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.rag.external.RagBackendClient;
import com.cloudera.cai.util.Tracker;
import com.cloudera.cai.util.reconcilers.*;
import io.opentelemetry.api.OpenTelemetry;
import java.util.Set;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class DeleteDataSourceReconciler extends BaseReconciler<Long> {
  private final DatabaseOperations databaseOperations;
  private final RagBackendClient ragBackendClient;

  public DeleteDataSourceReconciler(
      DatabaseOperations databaseOperations,
      RagBackendClient ragBackendClient,
      @Qualifier("reconcilerConfig") ReconcilerConfig reconcilerConfig,
      OpenTelemetry openTelemetry) {
    super(reconcilerConfig, openTelemetry);
    this.databaseOperations = databaseOperations;
    this.ragBackendClient = ragBackendClient;
  }

  @Override
  public void resync() {
    log.debug("Checking for data sources to delete");
    databaseOperations.useHandle(
        handle ->
            handle
                .createQuery("SELECT id FROM rag_data_source WHERE deleted IS NOT NULL")
                .mapTo(Long.class)
                .forEach(this::submit));
  }

  @Override
  public ReconcileResult reconcile(Set<Long> dataSourceIds) {
    for (Long dataSourceId : dataSourceIds) {
      log.info("telling the rag backend to delete data source with id: {}", dataSourceId);
      ragBackendClient.deleteDataSource(dataSourceId);
      log.info(
          "deleting data source and documents from the database. data source id: {}", dataSourceId);
      databaseOperations.useTransaction(
          handle -> {
            handle.execute("DELETE FROM RAG_DATA_SOURCE WHERE ID = ?", dataSourceId);
            handle.execute(
                "DELETE FROM RAG_DATA_SOURCE_DOCUMENT WHERE DATA_SOURCE_ID = ?", dataSourceId);
          });
    }
    return new ReconcileResult();
  }

  // nullables stuff below here
  public static DeleteDataSourceReconciler createNull(
      Tracker<RagBackendClient.TrackedRequest<?>> tracker) {
    return new DeleteDataSourceReconciler(
        JdbiConfiguration.createNull(),
        RagBackendClient.createNull(tracker),
        ReconcilerConfig.builder().isTestReconciler(true).build(),
        OpenTelemetry.noop());
  }
}
