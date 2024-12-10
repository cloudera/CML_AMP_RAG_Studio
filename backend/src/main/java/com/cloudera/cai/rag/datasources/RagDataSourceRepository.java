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

import com.cloudera.cai.rag.Types.RagDataSource;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.util.exceptions.NotFound;
import java.time.Instant;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.jdbi.v3.core.Jdbi;
import org.jdbi.v3.core.mapper.reflect.ConstructorMapper;
import org.jdbi.v3.core.statement.Query;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class RagDataSourceRepository {
  private final Jdbi jdbi;

  public RagDataSourceRepository(Jdbi jdbi) {
    this.jdbi = jdbi;
  }

  public Long createRagDataSource(RagDataSource input) {
    return jdbi.inTransaction(
        handle -> {
          var sql =
              """
                INSERT INTO rag_data_source (name, chunk_size, chunk_overlap_percent, created_by_id, updated_by_id, connection_type, embedding_model, summarization_model)
                VALUES (:name, :chunkSize, :chunkOverlapPercent, :createdById, :updatedById, :connectionType, :embeddingModel, :summarizationModel)
              """;
          try (var update = handle.createUpdate(sql)) {
            update.bindMethods(input);
            return update.executeAndReturnGeneratedKeys("id").mapTo(Long.class).one();
          }
        });
  }

  public void updateRagDataSource(RagDataSource input) {
    jdbi.inTransaction(
        handle -> {
          var sql =
              """
              UPDATE rag_data_source
              SET name = :name, connection_type = :connectionType, updated_by_id = :updatedById, summarization_model = :summarizationModel, time_updated = :now
              WHERE id = :id AND deleted IS NULL
          """;
          try (var update = handle.createUpdate(sql)) {
            return update
                .bind("name", input.name())
                .bind("updatedById", input.updatedById())
                .bind("connectionType", input.connectionType())
                .bind("id", input.id())
                .bind("summarizationModel", input.summarizationModel())
                .bind("now", Instant.now())
                .execute();
          }
        });
  }

  public RagDataSource getRagDataSourceById(Long id) {
    return jdbi.withHandle(
        handle -> {
          var sql =
              """
               SELECT rds.*, count(rdsd.ID) as document_count, sum(rdsd.SIZE_IN_BYTES) as total_doc_size
                 FROM rag_data_source rds
                  LEFT JOIN RAG_DATA_SOURCE_DOCUMENT rdsd ON rds.id = rdsd.data_source_id
               WHERE rds.ID = :id AND rds.deleted IS NULL
                GROUP BY rds.ID
              """;
          handle.registerRowMapper(ConstructorMapper.factory(RagDataSource.class));
          try (Query query = handle.createQuery(sql)) {
            query.bind("id", id);
            return query
                .mapTo(RagDataSource.class)
                .findOne()
                .orElseThrow(() -> new NotFound("Data source not found with id: " + id));
          }
        });
  }

  public List<RagDataSource> getRagDataSources() {
    log.info("Getting all RagDataSources");
    return jdbi.withHandle(
        handle -> {
          var sql =
              """
              SELECT rds.*, count(rdsd.ID) as document_count, sum(rdsd.SIZE_IN_BYTES) as total_doc_size
                FROM rag_data_source rds
                LEFT JOIN RAG_DATA_SOURCE_DOCUMENT rdsd ON rds.id = rdsd.data_source_id
              WHERE rds.deleted IS NULL
               GROUP BY rds.ID
              """;
          handle.registerRowMapper(ConstructorMapper.factory(RagDataSource.class));
          try (Query query = handle.createQuery(sql)) {
            return query.mapTo(RagDataSource.class).list();
          }
        });
  }

  public void deleteDataSource(Long id) {
    jdbi.useTransaction(
        handle -> handle.execute("UPDATE RAG_DATA_SOURCE SET DELETED = ? where ID = ?", true, id));
  }

  // Nullables stuff below here.

  public static RagDataSourceRepository createNull() {
    // the db configuration will use in-memory db based on env vars.
    return new RagDataSourceRepository(new JdbiConfiguration().jdbi());
  }
}
