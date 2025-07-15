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
import com.cloudera.cai.rag.configuration.DatabaseOperations;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.util.exceptions.NotFound;
import java.time.Instant;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.jdbi.v3.core.Handle;
import org.jdbi.v3.core.mapper.reflect.ConstructorMapper;
import org.jdbi.v3.core.statement.Query;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class RagDataSourceRepository {
  private final DatabaseOperations databaseOperations;

  public RagDataSourceRepository(DatabaseOperations databaseOperations) {
    this.databaseOperations = databaseOperations;
  }

  public Long createRagDataSource(RagDataSource input) {
    return databaseOperations.inTransaction(handle -> createRagDataSource(handle, input));
  }

  public Long createRagDataSource(Handle handle, RagDataSource input) {
    RagDataSource cleanedInputs = cleanInputs(input);
    var sql =
        """
          INSERT INTO rag_data_source (name, chunk_size, chunk_overlap_percent, created_by_id, updated_by_id, connection_type, embedding_model, summarization_model, ASSOCIATED_SESSION_ID)
          VALUES (:name, :chunkSize, :chunkOverlapPercent, :createdById, :updatedById, :connectionType, :embeddingModel, :summarizationModel, :associatedSessionId)
        """;
    Long result;
    try (var update = handle.createUpdate(sql)) {
      update.bindMethods(cleanedInputs);
      result = update.executeAndReturnGeneratedKeys("id").mapTo(Long.class).one();
    }
    if (input.availableForDefaultProject()) {
      handle.execute(
          "INSERT INTO project_data_source (data_source_id, project_id) VALUES (?, 1)", result);
    }
    return result;
  }

  private static RagDataSource cleanInputs(RagDataSource input) {
    if (input.summarizationModel() != null && input.summarizationModel().isEmpty()) {
      input = input.withSummarizationModel(null);
    }
    return input;
  }

  public void updateRagDataSource(RagDataSource input) {
    RagDataSource cleanedInputs = cleanInputs(input);
    databaseOperations.useTransaction(
        handle -> {
          var sql =
              """
                                        UPDATE rag_data_source
                                        SET name = :name, connection_type = :connectionType, updated_by_id = :updatedById, summarization_model = :summarizationModel, time_updated = :now
                                        WHERE id = :id AND deleted IS NULL
                                    """;
          try (var update = handle.createUpdate(sql)) {
            update
                .bind("name", cleanedInputs.name())
                .bind("updatedById", cleanedInputs.updatedById())
                .bind("connectionType", cleanedInputs.connectionType())
                .bind("id", cleanedInputs.id())
                .bind("summarizationModel", cleanedInputs.summarizationModel())
                .bind("now", Instant.now())
                .execute();
          }
          handle.execute(
              "DELETE FROM project_data_source WHERE data_source_id = ? AND project_id = 1",
              input.id());
          if (input.availableForDefaultProject()) {
            handle.execute(
                "INSERT INTO project_data_source (data_source_id, project_id) VALUES (?, 1)",
                input.id());
          }
        });
  }

  public RagDataSource getRagDataSourceById(Long id) {
    return databaseOperations.withHandle(
        handle -> {
          var sql =
              """
                                    SELECT rds.*, count(rdsd.ID) as document_count, sum(rdsd.SIZE_IN_BYTES) as total_doc_size,
                                    EXISTS(
                                        SELECT 1 from project_data_source pds
                                        WHERE pds.data_source_id = rds.id
                                          AND pds.project_id = 1
                                    ) as available_for_default_project
                                    FROM rag_data_source rds
                                        LEFT JOIN RAG_DATA_SOURCE_DOCUMENT rdsd ON rds.id = rdsd.data_source_id
                                    WHERE rds.deleted IS NULL
                                     AND rds.id = :id
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
    log.debug("Getting all RagDataSources");
    return databaseOperations.withHandle(
        handle -> {
          var sql =
              """
                SELECT rds.*, count(rdsd.ID) as document_count, sum(rdsd.SIZE_IN_BYTES) as total_doc_size,
                EXISTS(
                    SELECT 1 from project_data_source pds
                    WHERE pds.data_source_id = rds.id
                      AND pds.project_id = 1
                ) as available_for_default_project
                FROM rag_data_source rds
                         LEFT JOIN RAG_DATA_SOURCE_DOCUMENT rdsd ON rds.id = rdsd.data_source_id
                WHERE rds.deleted IS NULL
                  AND rds.ASSOCIATED_SESSION_ID IS NULL
                GROUP BY rds.ID
                """;
          handle.registerRowMapper(ConstructorMapper.factory(RagDataSource.class));
          try (Query query = handle.createQuery(sql)) {
            return query.mapTo(RagDataSource.class).list();
          }
        });
  }

  public void deleteDataSource(Long id) {
    databaseOperations.useTransaction(handle -> deleteDataSource(handle, id));
  }

  public void deleteDataSource(Handle handle, Long id) {
    handle.execute("UPDATE RAG_DATA_SOURCE SET DELETED = ? where ID = ?", true, id);
    handle.execute("DELETE FROM PROJECT_DATA_SOURCE WHERE DATA_SOURCE_ID = ?", id);
    handle.execute("DELETE FROM CHAT_SESSION_DATA_SOURCE WHERE DATA_SOURCE_ID = ?", id);
  }

  public int getNumberOfDataSources() {
    return databaseOperations.withHandle(
        handle -> {
          try (var query =
              handle.createQuery(
                  "SELECT count(*) FROM RAG_DATA_SOURCE where ASSOCIATED_SESSION_ID IS NULL AND DELETED IS NULL")) {
            return query.mapTo(Integer.class).one();
          }
        });
  }

  // Nullables stuff below here.

  public static RagDataSourceRepository createNull() {
    // the db configuration will use in-memory db based on env vars.
    return new RagDataSourceRepository(JdbiConfiguration.createNull());
  }
}
