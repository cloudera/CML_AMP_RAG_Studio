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

package com.cloudera.cai.rag.files;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.awaitility.Awaitility.await;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.external.RagBackendClient;
import com.cloudera.cai.rag.external.RagBackendClient.TrackedDeleteDocumentRequest;
import com.cloudera.cai.rag.external.RagBackendClient.TrackedRequest;
import com.cloudera.cai.util.Tracker;
import com.cloudera.cai.util.exceptions.NotFound;
import com.cloudera.cai.util.reconcilers.ReconcilerConfig;
import io.opentelemetry.api.OpenTelemetry;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class RagFileDeleteReconcilerTest {
  @Test
  void reconciler() throws Exception {
    Tracker<TrackedRequest<?>> tracker = new Tracker<>();
    RagFileDeleteReconciler reconciler = createTestReconciler(tracker);

    RagFileRepository ragFileRepository = RagFileRepository.createNull();
    var dataSourceId = TestData.createTestDataSource(RagDataSourceRepository.createNull());
    String documentId = UUID.randomUUID().toString();
    var id = TestData.createTestDocument(dataSourceId, documentId, ragFileRepository);

    ragFileRepository.deleteById(id);
    reconciler.resync();

    await()
        .untilAsserted(
            () -> {
              assertThat(tracker.getValues())
                  .contains(
                      new TrackedRequest<>(
                          new TrackedDeleteDocumentRequest(dataSourceId, documentId)));
              assertThatThrownBy(() -> ragFileRepository.getRagDocumentById(id))
                  .isInstanceOf(NotFound.class);
            });
  }

  private static RagFileDeleteReconciler createTestReconciler(Tracker<TrackedRequest<?>> tracker) {
    RagFileDeleteReconciler reconciler =
        new RagFileDeleteReconciler(
            ReconcilerConfig.createTestConfig(),
            OpenTelemetry.noop(),
            JdbiConfiguration.createNull(),
            RagBackendClient.createNull(tracker));
    reconciler.init();
    return reconciler;
  }
}
