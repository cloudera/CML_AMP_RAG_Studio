package com.cloudera.cai.rag.files;

import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.configuration.DatabaseOperations;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.rag.external.RagBackendClient;
import com.cloudera.cai.util.exceptions.NotFound;
import com.cloudera.cai.util.reconcilers.BaseReconciler;
import com.cloudera.cai.util.reconcilers.ReconcileResult;
import com.cloudera.cai.util.reconcilers.ReconcilerConfig;
import io.opentelemetry.api.OpenTelemetry;
import java.util.Set;
import lombok.extern.slf4j.Slf4j;
import org.jdbi.v3.core.mapper.reflect.ConstructorMapper;
import org.jdbi.v3.core.statement.Query;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class RagFileDeleteReconciler extends BaseReconciler<Types.RagDocument> {
  private final DatabaseOperations databaseOperations;
  private final RagBackendClient ragBackendClient;

  public RagFileDeleteReconciler(
      ReconcilerConfig reconcilerConfig,
      OpenTelemetry openTelemetry,
      DatabaseOperations databaseOperations,
      RagBackendClient ragBackendClient) {
    super(reconcilerConfig, openTelemetry);
    this.databaseOperations = databaseOperations;
    this.ragBackendClient = ragBackendClient;
  }

  @Override
  public void resync() throws Exception {
    log.debug("checking for RAG documents to be deleted");
    databaseOperations.useHandle(
        handle -> {
          handle.registerRowMapper(ConstructorMapper.factory(Types.RagDocument.class));
          Query query =
              handle.createQuery("SELECT * FROM rag_data_source_document WHERE deleted = :deleted");
          query.bind("deleted", true);
          query.mapTo(Types.RagDocument.class).list().forEach(this::submit);
        });
  }

  @Override
  public ReconcileResult reconcile(Set<Types.RagDocument> documents) throws Exception {
    for (Types.RagDocument document : documents) {
      log.debug("starting deletion of document: {}", document);
      try {
        ragBackendClient.deleteDocument(document.dataSourceId(), document.documentId());
        log.debug("finished requesting deletion of document {}", document);
      } catch (NotFound e) {
        log.debug("got a not found exception from the rag backend: {}", e.getMessage());
      }
      databaseOperations.useHandle(
          handle ->
              handle.execute("DELETE from rag_data_source_document WHERE id = ?", document.id()));
    }
    return new ReconcileResult();
  }

  //    Nullables
  public static RagFileDeleteReconciler createNull() {
    return new RagFileDeleteReconciler(
        ReconcilerConfig.builder().isTestReconciler(true).build(),
        OpenTelemetry.noop(),
        JdbiConfiguration.createNull(),
        RagBackendClient.createNull());
  }
}
