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

import static com.cloudera.cai.rag.Types.*;

import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.rag.external.RagBackendClient;
import com.cloudera.cai.util.exceptions.NotFound;
import com.cloudera.cai.util.reconcilers.*;
import io.opentelemetry.api.OpenTelemetry;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Set;
import lombok.extern.slf4j.Slf4j;
import org.jdbi.v3.core.Jdbi;
import org.jdbi.v3.core.mapper.reflect.ConstructorMapper;
import org.jdbi.v3.core.statement.Query;
import org.jdbi.v3.core.statement.Update;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class RagFileSummaryReconciler extends BaseReconciler<RagDocument> {
  private final String bucketName;
  private final Jdbi jdbi;
  private final RagBackendClient ragBackendClient;
  private final RagFileRepository ragFileRepository;

  @Autowired
  public RagFileSummaryReconciler(
      @Qualifier("s3BucketName") String bucketName,
      Jdbi jdbi,
      RagBackendClient ragBackendClient,
      RagFileRepository ragFileRepository,
      @Qualifier("singleWorkerReconcilerConfig") ReconcilerConfig reconcilerConfig,
      OpenTelemetry openTelemetry) {
    super(reconcilerConfig, openTelemetry);
    this.bucketName = bucketName;
    this.jdbi = jdbi;
    this.ragBackendClient = ragBackendClient;
    this.ragFileRepository = ragFileRepository;
  }

  @Override
  public void resync() {
    log.debug("checking for RAG documents to be summarized");
    String sql =
        """
        SELECT * from rag_data_source_document
         WHERE summary_creation_timestamp IS NULL
           AND time_created > :yesterday
        """;
    jdbi.useHandle(
        handle -> {
          handle.registerRowMapper(ConstructorMapper.factory(RagDocument.class));

          try (Query query = handle.createQuery(sql)) {
            query.bind("yesterday", Instant.now().minus(1, ChronoUnit.DAYS));
            query.mapTo(RagDocument.class).forEach(this::submit);
          }
        });
  }

  @Override
  public ReconcileResult reconcile(Set<RagDocument> documents) {
    for (RagDocument document : documents) {
      log.info("starting summarizing document: {}", document);
      var currentDocumentState = ragFileRepository.findDocumentByDocumentId(document.documentId());
      if (currentDocumentState.summaryCreationTimestamp() != null) {
        log.info("Document already summarized: {}", document.filename());
        continue;
      }
      var updateTimestamp = generateSummary(document);
      log.info("finished requesting summarization of file {}", document);
      String updateSql =
          """
        UPDATE rag_data_source_document
        SET summary_creation_timestamp = :now
        WHERE id = :id
      """;
      jdbi.useHandle(
          handle -> {
            try (Update update = handle.createUpdate(updateSql)) {
              update.bind("id", document.id()).bind("now", updateTimestamp).execute();
            }
          });
    }
    return new ReconcileResult();
  }

  private Instant generateSummary(RagDocument document) {
    var updateTimestamp = Instant.now();
    try {
      String summary = ragBackendClient.createSummary(document, bucketName);
      log.info("Doc summary: {}", summary);
    } catch (NotFound e) {
      updateTimestamp = Instant.EPOCH;
      log.info("got a not found exception from the rag backend: {}", e.getMessage());
    }
    return updateTimestamp;
  }

  // nullables stuff below here...
  public static RagFileSummaryReconciler createNull() {
    return new RagFileSummaryReconciler(
        "rag-files",
        JdbiConfiguration.createNull(),
        RagBackendClient.createNull(),
        RagFileRepository.createNull(),
        ReconcilerConfig.builder().isTestReconciler(true).build(),
        OpenTelemetry.noop());
  }
}
