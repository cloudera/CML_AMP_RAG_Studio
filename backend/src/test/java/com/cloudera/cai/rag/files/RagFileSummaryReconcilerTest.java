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
import static org.awaitility.Awaitility.await;

import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.Types.RagDataSource;
import com.cloudera.cai.rag.Types.RagDocument;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.external.RagBackendClient;
import com.cloudera.cai.util.Tracker;
import com.cloudera.cai.util.exceptions.NotFound;
import com.cloudera.cai.util.reconcilers.ReconcilerConfig;
import io.opentelemetry.api.OpenTelemetry;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import org.jdbi.v3.core.Jdbi;
import org.junit.jupiter.api.Test;

class RagFileSummaryReconcilerTest {
  private final RagFileRepository ragFileRepository = RagFileRepository.createNull();
  private final RagDataSourceRepository ragDataSourceRepository =
      RagDataSourceRepository.createNull();

  // todo: test for the time limit on how long we will retry document
  // summarization (and also that
  // updated the data source will re-trigger tries)

  @Test
  void reconcile() {
    Tracker<RagBackendClient.TrackedRequest<?>> requestTracker = new Tracker<>();
    RagFileSummaryReconciler reconciler = createTestInstance(requestTracker);

    String documentId = UUID.randomUUID().toString();
    var dataSourceId = createDataSource("summarizationModel");
    var document = createTestDoc(documentId, dataSourceId, "path_in_s3");
    Long id = ragFileRepository.insertDocumentMetadata(document);
    assertThat(ragFileRepository.findDocumentByDocumentId(documentId).summaryCreationTimestamp())
        .isNull();

    reconciler.submit(document.withId(id));
    // add a copy that has already been summarized to make sure we don't try to
    // re-summarize with long-running summarizations
    reconciler.submit(document.withId(id).withSummaryCreationTimestamp(Instant.now()));

    await().until(reconciler::isEmpty);
    await()
        .untilAsserted(
            () -> {
              assertThat(reconciler.isEmpty()).isTrue();
              RagDocument updatedDocument = ragFileRepository.findDocumentByDocumentId(documentId);
              assertThat(updatedDocument.summaryCreationTimestamp()).isNotNull();
              assertThat(updatedDocument.summaryStatus())
                  .isEqualTo(Types.RagDocumentStatus.SUCCESS);
              assertThat(requestTracker.getValues())
                  .hasSize(1)
                  .contains(
                      new RagBackendClient.TrackedRequest<>(
                          new RagBackendClient.SummaryRequest(
                              "rag-files", document.s3Path(), document.filename())));
            });
  }

  private static RagDocument createTestDoc(
      String documentId, long dataSourceId, String path_in_s3) {
    return RagDocument.builder()
        .documentId(documentId)
        .dataSourceId(dataSourceId)
        .s3Path(path_in_s3)
        .extension("pdf")
        .filename("myfile.pdf")
        .timeCreated(Instant.now())
        .timeUpdated(Instant.now())
        .createdById("test-id")
        .build();
  }

  @Test
  void reconcile_stateChanges() {
    Tracker<RagBackendClient.TrackedRequest<?>> requestTracker = new Tracker<>();
    var waiter = new CountDownLatch(1);
    RagFileSummaryReconciler reconciler =
        createTestInstance(
            requestTracker,
            List.of(
                () -> {
                  try {
                    waiter.await();
                  } catch (InterruptedException e) {
                    throw new RuntimeException(e);
                  }
                }));

    String documentId = UUID.randomUUID().toString();
    var dataSourceId = createDataSource("summarizationModel");
    var document = createTestDoc(documentId, dataSourceId, "path_in_s3");
    Long id = ragFileRepository.insertDocumentMetadata(document);
    assertThat(ragFileRepository.findDocumentByDocumentId(documentId).summaryCreationTimestamp())
        .isNull();

    reconciler.submit(document.withId(id));

    await()
        .untilAsserted(
            () -> {
              RagDocument updatedDocument = ragFileRepository.findDocumentByDocumentId(documentId);
              assertThat(updatedDocument.summaryCreationTimestamp()).isNull();
              assertThat(updatedDocument.summaryStatus())
                  .isEqualTo(Types.RagDocumentStatus.IN_PROGRESS);
            });

    waiter.countDown();
    await().until(reconciler::isEmpty);
    await()
        .untilAsserted(
            () -> {
              assertThat(reconciler.isEmpty()).isTrue();
              RagDocument updatedDocument = ragFileRepository.findDocumentByDocumentId(documentId);
              assertThat(updatedDocument.summaryCreationTimestamp()).isNotNull();
              assertThat(requestTracker.getValues())
                  .hasSize(1)
                  .contains(
                      new RagBackendClient.TrackedRequest<>(
                          new RagBackendClient.SummaryRequest(
                              "rag-files", document.s3Path(), document.filename())));
            });
  }

  private long createDataSource(String summarizationModel) {
    return ragDataSourceRepository.createRagDataSource(
        new RagDataSource(
            null,
            "test_datasource",
            "test_embedding_model",
            summarizationModel,
            1024,
            20,
            null,
            null,
            "test-id",
            "test-id",
            Types.ConnectionType.API,
            null,
            null,
            true));
  }

  @Test
  void reconcile_notFound() {
    Tracker<RagBackendClient.TrackedRequest<?>> requestTracker = new Tracker<>();
    RagFileSummaryReconciler reconciler =
        createTestInstance(requestTracker, new NotFound("not found"));

    String documentId = UUID.randomUUID().toString();
    var dataSourceId = createDataSource("summarizationModel");
    var document = createTestDoc(documentId, dataSourceId, "path_in_s3");
    Long id = ragFileRepository.insertDocumentMetadata(document);
    assertThat(ragFileRepository.findDocumentByDocumentId(documentId).summaryCreationTimestamp())
        .isNull();

    reconciler.submit(document.withId(id));
    await().until(reconciler::isEmpty);
    await()
        .untilAsserted(
            () -> {
              assertThat(reconciler.isEmpty()).isTrue();
              RagDocument updatedDocument = ragFileRepository.findDocumentByDocumentId(documentId);
              assertThat(updatedDocument.summaryCreationTimestamp()).isEqualTo(Instant.EPOCH);
              assertThat(updatedDocument.summaryStatus()).isEqualTo(Types.RagDocumentStatus.ERROR);
              assertThat(updatedDocument.summaryError()).isEqualTo("not found");
              assertThat(requestTracker.getValues())
                  .hasSize(1)
                  .contains(
                      new RagBackendClient.TrackedRequest<>(
                          new RagBackendClient.SummaryRequest(
                              "rag-files", "path_in_s3", "myfile.pdf")));
            });
  }

  @Test
  void reconcile_exception() {
    Tracker<RagBackendClient.TrackedRequest<?>> requestTracker = new Tracker<>();
    RagFileSummaryReconciler reconciler =
        createTestInstance(requestTracker, new RuntimeException("document summarization failed"));

    String documentId = UUID.randomUUID().toString();
    var dataSourceId = createDataSource("summarizationModel");
    var document = createTestDoc(documentId, dataSourceId, "path_in_s3");
    Long id = ragFileRepository.insertDocumentMetadata(document);
    assertThat(ragFileRepository.findDocumentByDocumentId(documentId).summaryCreationTimestamp())
        .isNull();

    reconciler.submit(document.withId(id));
    await().until(reconciler::isEmpty);
    await()
        .untilAsserted(
            () -> {
              assertThat(reconciler.isEmpty()).isTrue();
              RagDocument updatedDocument = ragFileRepository.findDocumentByDocumentId(documentId);
              assertThat(updatedDocument.summaryCreationTimestamp()).isNull();
              assertThat(updatedDocument.summaryStatus()).isEqualTo(Types.RagDocumentStatus.ERROR);
              assertThat(updatedDocument.summaryError()).isEqualTo("document summarization failed");
              assertThat(requestTracker.getValues())
                  .hasSize(1)
                  .contains(
                      new RagBackendClient.TrackedRequest<>(
                          new RagBackendClient.SummaryRequest(
                              "rag-files", "path_in_s3", "myfile.pdf")));
            });
  }

  @Test
  void reconcile_noSummarizationModel() {
    Tracker<RagBackendClient.TrackedRequest<?>> requestTracker = new Tracker<>();
    RagFileSummaryReconciler reconciler = createTestInstance(requestTracker);

    var dataSourceId = createDataSource(null);
    String documentId = UUID.randomUUID().toString();
    var document = createTestDoc(documentId, dataSourceId, "path_in_s3_no_summarization_model");
    ragFileRepository.insertDocumentMetadata(document);
    assertThat(ragFileRepository.findDocumentByDocumentId(documentId).summaryCreationTimestamp())
        .isNull();

    reconciler.resync();
    await().until(reconciler::isEmpty);

    RagDocument updatedDocument = ragFileRepository.findDocumentByDocumentId(documentId);
    assertThat(updatedDocument.summaryCreationTimestamp()).isNull();
    List<RagBackendClient.TrackedRequest<?>> values = requestTracker.getValues();
    var relevantSummarizationRequests =
        values.stream()
            .filter(
                r -> {
                  var summaryRequest = (RagBackendClient.SummaryRequest) r.detail();
                  return summaryRequest.s3DocumentKey().equals("path_in_s3_no_summarization_model");
                })
            .count();
    assertThat(relevantSummarizationRequests).isEqualTo(0);
  }

  private RagFileSummaryReconciler createTestInstance(
      Tracker<RagBackendClient.TrackedRequest<?>> tracker, RuntimeException... exceptions) {
    return createTestInstance(
        tracker,
        Arrays.stream(exceptions)
            .map(
                e ->
                    (Runnable)
                        () -> {
                          throw e;
                        })
            .toList());
  }

  private RagFileSummaryReconciler createTestInstance(
      Tracker<RagBackendClient.TrackedRequest<?>> tracker, List<Runnable> runnables) {
    Jdbi jdbi = new JdbiConfiguration().jdbi();
    var reconcilerConfig = ReconcilerConfig.builder().isTestReconciler(true).workerCount(1).build();
    RagFileSummaryReconciler reconciler =
        new RagFileSummaryReconciler(
            "rag-files",
            jdbi,
            RagBackendClient.createNull(tracker, runnables),
            ragFileRepository,
            reconcilerConfig,
            OpenTelemetry.noop());
    reconciler.init();
    return reconciler;
  }
}
