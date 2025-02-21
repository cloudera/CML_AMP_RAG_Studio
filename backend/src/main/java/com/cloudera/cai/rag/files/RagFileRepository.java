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

package com.cloudera.cai.rag.files;

import com.cloudera.cai.rag.Types.RagDocument;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.util.exceptions.NotFound;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.jdbi.v3.core.Jdbi;
import org.jdbi.v3.core.mapper.reflect.ConstructorMapper;
import org.jdbi.v3.core.statement.Query;
import org.jdbi.v3.core.statement.Update;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class RagFileRepository {
  private final Jdbi jdbi;

  @Autowired
  public RagFileRepository(Jdbi jdbi) {
    this.jdbi = jdbi;
  }

  public Long insertDocumentMetadata(RagDocument ragDocument) {
    return jdbi.inTransaction(
        handle -> {
          String insertSql =
              """
              INSERT INTO rag_data_source_document(data_source_id, filename, document_id, s3_path, created_by_id, updated_by_id, time_created, extension, size_in_bytes)
              VALUES (:dataSourceId, :filename, :documentId, :s3Path, :createdById, :createdById, :timeCreated, :extension, :sizeInBytes)
              """;
          try (var update = handle.createUpdate(insertSql)) {
            update.bindMethods(ragDocument);
            return update.executeAndReturnGeneratedKeys("id").mapTo(Long.class).one();
          }
        });
  }

  public RagDocument findDocumentByDocumentId(String documentId) {
    return jdbi.withHandle(
        handle -> {
          String sql =
              """
                  SELECT * FROM rag_data_source_document
                  WHERE document_id = :documentId
                  AND deleted is null OR deleted = :deleted
                  """;
          handle.registerRowMapper(ConstructorMapper.factory(RagDocument.class));
          try (Query query = handle.createQuery(sql)) {
            query.bind("documentId", documentId).bind("deleted", false);
            return query
                .mapTo(RagDocument.class)
                .findOne()
                .orElseThrow(() -> new NotFound("no document found with id: " + documentId));
          }
        });
  }

  public List<RagDocument> getRagDocuments(Long dataSourceId) {
    return jdbi.withHandle(
        handle -> {
          String sql =
              """
              SELECT * FROM rag_data_source_document
               WHERE data_source_id = :dataSourceId
                AND deleted is null OR deleted = :deleted
              """;
          handle.registerRowMapper(ConstructorMapper.factory(RagDocument.class));
          try (Query query = handle.createQuery(sql)) {
            return query
                .bind("dataSourceId", dataSourceId)
                .bind("deleted", false)
                .mapTo(RagDocument.class)
                .list();
          }
        });
  }

  // Nullables stuff below here.

  public static RagFileRepository createNull() {
    // the db configuration will use in-memory db based on env vars.
    return new RagFileRepository(new JdbiConfiguration().jdbi());
  }

  public void deleteById(Long id) {
    jdbi.useTransaction(
        handle -> {
          String sql = "UPDATE rag_data_source_document SET deleted = :deleted WHERE id = :id";
          try (Update update = handle.createUpdate(sql)) {
            update.bind("deleted", true).bind("id", id).execute();
          }
        });
  }

  public RagDocument getRagDocumentById(Long id) {
    return jdbi.withHandle(
        handle -> {
          handle.registerRowMapper(ConstructorMapper.factory(RagDocument.class));
          String sql = "SELECT * FROM rag_data_source_document WHERE id = :id";
          try (Query query = handle.createQuery(sql)) {
            return query
                .bind("id", id)
                .mapTo(RagDocument.class)
                .findFirst()
                .orElseThrow(() -> new NotFound("no document found with id: " + id));
          }
        });
  }

  public int getNumberOfRagDocuments() {
    return jdbi.withHandle(
        handle -> {
          try (var query = handle.createQuery("SELECT count(*) FROM rag_data_source_document")) {
            return query.mapTo(Integer.class).one();
          }
        });
  }
}
