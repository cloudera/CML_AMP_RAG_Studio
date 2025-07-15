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
 ******************************************************************************/

package com.cloudera.cai.rag.sessions;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.awaitility.Awaitility.await;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.configuration.DatabaseOperations;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.rag.external.RagBackendClient;
import com.cloudera.cai.rag.files.RagFileRepository;
import com.cloudera.cai.util.Tracker;
import com.cloudera.cai.util.exceptions.NotFound;
import com.cloudera.cai.util.exceptions.ServerError;
import com.cloudera.cai.util.reconcilers.ReconcilerConfig;
import io.opentelemetry.api.OpenTelemetry;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import org.jdbi.v3.core.statement.UnableToExecuteStatementException;
import org.junit.jupiter.api.Test;

class DeleteSessionReconcilerTest {
  private final SessionRepository ragSessionRepository = SessionRepository.createNull();
  private final RagFileRepository ragFileRepository = RagFileRepository.createNull();
  private final DatabaseOperations databaseOperations = JdbiConfiguration.createNull();
  private final Tracker<RagBackendClient.TrackedRequest<?>> tracker = new Tracker<>();

  @Test
  void reconcile_basicHappyPath() {
    var reconciler = createTestInstance(tracker);
    var sessionId =
        ragSessionRepository.create(
            TestData.createTestSessionInstance("test-name")
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    var documentId = UUID.randomUUID().toString();

    reconciler.resync();
    await().until(reconciler::isEmpty);
    databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId));

    reconciler.resync();
    await().until(reconciler::isEmpty);

    await().untilAsserted(() -> assertThat(sessionIsInTheDatabase(sessionId)).isFalse());
    assertThatThrownBy(() -> ragFileRepository.findDocumentByDocumentId(documentId))
        .isInstanceOf(NotFound.class);
    assertThat(tracker.getValues())
        .hasSizeGreaterThanOrEqualTo(1)
        .contains(
            new RagBackendClient.TrackedRequest<>(
                new RagBackendClient.TrackedDeleteSessionRequest(sessionId)));
  }

  @Test
  void resync_noSessionsToDelete() {
    var reconciler = createTestInstance(tracker);

    // Clean slate - remove any leftover sessions from previous tests
    databaseOperations.useHandle(
        handle -> handle.execute("DELETE FROM CHAT_SESSION WHERE deleted IS NOT NULL"));

    // Record initial tracker state
    var initialCallCount = tracker.getValues().size();

    reconciler.resync();
    await().until(reconciler::isEmpty);

    // Should not make any new RAG backend calls
    assertThat(tracker.getValues()).hasSize(initialCallCount);
  }

  @Test
  void resync_multipleSessionsToDelete() {
    var reconciler = createTestInstance(tracker);
    // Clean slate - remove any leftover sessions from previous tests
    reconciler.resync();
    await().until(reconciler::isEmpty);
    tracker.clear();

    var sessionId1 =
        ragSessionRepository.create(
            TestData.createTestSessionInstance("session-1")
                .withCreatedById("user1")
                .withUpdatedById("user1"));
    var sessionId2 =
        ragSessionRepository.create(
            TestData.createTestSessionInstance("session-2")
                .withCreatedById("user2")
                .withUpdatedById("user2"));

    // Mark both sessions for deletion
    databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId1));
    databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId2));

    reconciler.resync();
    await().until(reconciler::isEmpty);

    // Should process both sessions
    assertThat(tracker.getValues())
        .hasSize(2)
        .contains(
            new RagBackendClient.TrackedRequest<>(
                new RagBackendClient.TrackedDeleteSessionRequest(sessionId1)),
            new RagBackendClient.TrackedRequest<>(
                new RagBackendClient.TrackedDeleteSessionRequest(sessionId2)));

    // Both sessions should be removed from database
    await()
        .untilAsserted(
            () -> {
              assertThat(sessionIsInTheDatabase(sessionId1)).isFalse();
              assertThat(sessionIsInTheDatabase(sessionId2)).isFalse();
            });
  }

  @Test
  void reconcile_emptySessionSet() {
    var reconciler = createTestInstance(tracker);

    var result = reconciler.reconcile(Set.of());

    assertThat(result).isNotNull();
    assertThat(tracker.getValues()).isEmpty();
  }

  @Test
  void reconcile_nonExistentSessionId() {
    var reconciler = createTestInstance(tracker);
    var nonExistentId = 999999L;

    // Record initial tracker state
    var initialCallCount = tracker.getValues().size();

    var result = reconciler.reconcile(Set.of(nonExistentId));

    // Should complete successfully
    assertThat(result).isNotNull();
    assertThat(tracker.getValues()).hasSize(initialCallCount + 1);
  }

  @Test
  void reconcile_withRagBackendNotFound() {
    var ragBackendClient = RagBackendClient.createNull(tracker, new NotFound("Session not found"));

    var reconciler =
        new DeleteSessionReconciler(
            databaseOperations,
            ragBackendClient,
            ReconcilerConfig.builder().isTestReconciler(true).build(),
            OpenTelemetry.noop());
    reconciler.init();

    var sessionId =
        ragSessionRepository.create(
            TestData.createTestSessionInstance("test-session")
                .withCreatedById("user")
                .withUpdatedById("user"));

    databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId));
    var result = reconciler.reconcile(Set.of(sessionId));
    assertThat(result).isNotNull();
  }

  @Test
  void reconcile_withRagBackendServerError() {
    var ragBackendClient =
        RagBackendClient.createNull(tracker, new ServerError("Internal server error", 500));

    var reconciler =
        new DeleteSessionReconciler(
            databaseOperations,
            ragBackendClient,
            ReconcilerConfig.builder().isTestReconciler(true).build(),
            OpenTelemetry.noop());
    reconciler.init();

    var sessionId =
        ragSessionRepository.create(
            TestData.createTestSessionInstance("test-session")
                .withCreatedById("user")
                .withUpdatedById("user"));

    databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId));

    // Should fail if RAG backend throws server error
    assertThatThrownBy(() -> reconciler.reconcile(Set.of(sessionId)))
        .isInstanceOf(ServerError.class);
  }

  @Test
  void reconcile_databaseFailure() {
    // This test uses a DatabaseOperations that throws exceptions on any call
    var initialTrackerSize = tracker.getValues().size();

    var reconciler =
        new DeleteSessionReconciler(
            JdbiConfiguration.createNull(new RuntimeException("Mocked JDBI failure")),
            RagBackendClient.createNull(tracker),
            ReconcilerConfig.builder().isTestReconciler(true).build(),
            OpenTelemetry.noop());
    reconciler.init();

    // With a failing DatabaseOperations, the database check will fail and throw an exception
    assertThatThrownBy(() -> reconciler.reconcile(Set.of(1L))).isInstanceOf(RuntimeException.class);

    // RAG backend call is made before the db is updated
    assertThat(tracker.getValues()).hasSize(initialTrackerSize + 1);
  }

  @Test
  void reconcile_concurrentProcessing() {
    var reconciler = createTestInstance(tracker);
    var sessionId1 =
        ragSessionRepository.create(
            TestData.createTestSessionInstance("session-1")
                .withCreatedById("user1")
                .withUpdatedById("user1"));
    var sessionId2 =
        ragSessionRepository.create(
            TestData.createTestSessionInstance("session-2")
                .withCreatedById("user2")
                .withUpdatedById("user2"));

    databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId1));
    databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId2));

    // Process sessions concurrently
    var future1 = CompletableFuture.runAsync(() -> reconciler.reconcile(Set.of(sessionId1)));
    var future2 = CompletableFuture.runAsync(() -> reconciler.reconcile(Set.of(sessionId2)));

    // Both should complete successfully
    assertThat(future1.join()).isNull();
    assertThat(future2.join()).isNull();

    await()
        .untilAsserted(
            () -> {
              assertThat(sessionIsInTheDatabase(sessionId1)).isFalse();
              assertThat(sessionIsInTheDatabase(sessionId2)).isFalse();
            });
  }

  @Test
  void reconcile_largeSessionBatch() {
    var reconciler = createTestInstance(tracker);

    // Create actual sessions and mark them for deletion
    var sessionIds = new java.util.HashSet<Long>();
    for (int i = 1; i <= 10; i++) {
      var sessionId =
          ragSessionRepository.create(
              TestData.createTestSessionInstance("session-" + i)
                  .withCreatedById("user" + i)
                  .withUpdatedById("user" + i));
      databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId));
      sessionIds.add(sessionId);
    }

    var result = reconciler.reconcile(sessionIds);

    assertThat(result).isNotNull();
    assertThat(tracker.getValues()).hasSize(10);
  }

  @Test
  void init_successful() {
    var reconciler = createTestInstance(tracker);

    // Should initialize without error
    reconciler.init();

    // Should start empty
    assertThat(reconciler.isEmpty()).isTrue();
  }

  @Test
  void createNull_factoryMethod() {
    var testTracker = new Tracker<RagBackendClient.TrackedRequest<?>>();
    var reconciler = DeleteSessionReconciler.createNull(testTracker);

    assertThat(reconciler).isNotNull();
    assertThat(reconciler).isInstanceOf(DeleteSessionReconciler.class);

    // Should be able to initialize without errors
    reconciler.init();

    // Should start empty
    assertThat(reconciler.isEmpty()).isTrue();
  }

  @Test
  void reconcile_databaseTransactionRollback() {
    var ragBackendClient = RagBackendClient.createNull(tracker);

    // Create a session and mark it for deletion
    var sessionId =
        ragSessionRepository.create(
            TestData.createTestSessionInstance("test-session")
                .withCreatedById("user")
                .withUpdatedById("user"));
    databaseOperations.useHandle(handle -> ragSessionRepository.delete(handle, sessionId));

    // Create a DatabaseOperations that throws an exception on useTransaction
    var failingDatabaseOperations =
        JdbiConfiguration.createNull(new UnableToExecuteStatementException("Transaction rollback"));

    var reconciler =
        new DeleteSessionReconciler(
            failingDatabaseOperations,
            ragBackendClient,
            ReconcilerConfig.builder().isTestReconciler(true).build(),
            OpenTelemetry.noop());
    reconciler.init();

    assertThatThrownBy(() -> reconciler.reconcile(Set.of(sessionId)))
        .isInstanceOf(UnableToExecuteStatementException.class);

    // Should call RAG backend first
    assertThat(tracker.getValues())
        .hasSize(1)
        .contains(
            new RagBackendClient.TrackedRequest<>(
                new RagBackendClient.TrackedDeleteSessionRequest(sessionId)));
    // Then fail on database transaction - no need to verify since we're not using mocks
  }

  private DeleteSessionReconciler createTestInstance(
      Tracker<RagBackendClient.TrackedRequest<?>> tracker) {
    var reconcilerConfig = ReconcilerConfig.builder().isTestReconciler(true).build();

    var reconciler =
        new DeleteSessionReconciler(
            databaseOperations,
            RagBackendClient.createNull(tracker),
            reconcilerConfig,
            OpenTelemetry.noop());
    reconciler.init();
    return reconciler;
  }

  private Boolean sessionIsInTheDatabase(Long sessionId) {
    return databaseOperations.withHandle(
        handle -> {
          Integer count;
          try (var query = handle.createQuery("SELECT COUNT(*) FROM CHAT_SESSION WHERE id = :id")) {
            count = query.bind("id", sessionId).mapTo(Integer.class).one();
          }
          return count > 0;
        });
  }
}
