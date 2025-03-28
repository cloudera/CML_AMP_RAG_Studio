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

package com.cloudera.cai.rag.sessions;

import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.util.exceptions.NotFound;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;
import org.jdbi.v3.core.Handle;
import org.jdbi.v3.core.Jdbi;
import org.jdbi.v3.core.mapper.reflect.ConstructorMapper;
import org.jdbi.v3.core.result.RowView;
import org.jdbi.v3.core.statement.Query;
import org.springframework.stereotype.Component;

@Component
public class SessionRepository {
  public static final Types.QueryConfiguration DEFAULT_QUERY_CONFIGURATION =
      new Types.QueryConfiguration(false, true);
  private final Jdbi jdbi;
  private final ObjectMapper objectMapper = new ObjectMapper();

  public SessionRepository(Jdbi jdbi) {
    this.jdbi = jdbi;
  }

  public Long create(Types.Session input) {
    return jdbi.inTransaction(
        handle -> {
          var sql =
              """
            INSERT INTO CHAT_SESSION (name, created_by_id, updated_by_id, inference_model, rerank_model, response_chunks, query_configuration, project_id)
            VALUES (:name, :createdById, :updatedById, :inferenceModel, :rerankModel, :responseChunks, :queryConfiguration, :projectId)
          """;
          Long id = insertSession(input, handle, sql);
          insertSessionDataSources(handle, id, input.dataSourceIds());
          return id;
        });
  }

  private void insertSessionDataSources(Handle handle, Long sessionId, List<Long> dataSourceId) {
    var otherSql =
        """
              INSERT INTO CHAT_SESSION_DATA_SOURCE (chat_session_id, data_source_id)
              VALUES (:id, :data_source_id)
            """;
    try (var update = handle.createUpdate(otherSql)) {
      for (Long dataSource : dataSourceId) {
        update.bind("id", sessionId).bind("data_source_id", dataSource);
        update.execute();
      }
    }
  }

  private Long insertSession(Types.Session input, Handle handle, String sql) {
    try (var update = handle.createUpdate(sql)) {
      Types.QueryConfiguration queryConfiguration = input.queryConfiguration();
      String json = objectMapper.writeValueAsString(queryConfiguration);
      update.bind("queryConfiguration", json);
      update.bindMethods(input);
      return update.executeAndReturnGeneratedKeys("id").mapTo(Long.class).one();
    } catch (JsonProcessingException e) {
      throw new RuntimeException(e);
    }
  }

  public Types.Session getSessionById(Long id) {
    return jdbi.withHandle(
            handle -> {
              handle.registerRowMapper(ConstructorMapper.factory(Types.Session.class));
              var sql =
                  """
                SELECT cs.*, csds.data_source_id FROM CHAT_SESSION cs
                LEFT JOIN CHAT_SESSION_DATA_SOURCE csds ON cs.id=csds.chat_session_id
                WHERE cs.ID = :id AND cs.DELETED IS NULL
              """;
              return querySessions(handle.createQuery(sql).bind("id", id))
                  .findFirst()
                  .orElseThrow(() -> new NotFound("Session not found"));
            })
        .build();
  }

  private Stream<Types.Session.SessionBuilder> querySessions(Query query) {
    try (query) {
      return query.reduceRows(
          (Map<Long, Types.Session.SessionBuilder> map, RowView rowView) -> {
            Types.Session.SessionBuilder sessionBuilder =
                map.computeIfAbsent(
                    rowView.getColumn("id", Long.class),
                    sessionId -> {
                      try {
                        var queryConfiguration = extractQueryConfiguration(rowView);
                        return Types.Session.builder()
                            .id(sessionId)
                            .name(rowView.getColumn("name", String.class))
                            .inferenceModel(rowView.getColumn("inference_model", String.class))
                            .responseChunks(rowView.getColumn("response_chunks", Integer.class))
                            .rerankModel(rowView.getColumn("rerank_model", String.class))
                            .queryConfiguration(queryConfiguration)
                            .createdById(rowView.getColumn("created_by_id", String.class))
                            .timeCreated(rowView.getColumn("time_created", Instant.class))
                            .updatedById(rowView.getColumn("updated_by_id", String.class))
                            .timeUpdated(rowView.getColumn("time_updated", Instant.class))
                            .lastInteractionTime(
                                rowView.getColumn("last_interaction_time", Instant.class))
                            .projectId(rowView.getColumn("project_id", Long.class));
                      } catch (JsonProcessingException e) {
                        throw new RuntimeException(e);
                      }
                    });
            if (rowView.getColumn("data_source_id", Long.class) != null) {
              sessionBuilder.dataSourceId(rowView.getColumn("data_source_id", Long.class));
            }
          });
    }
  }

  private Types.QueryConfiguration extractQueryConfiguration(RowView rowView)
      throws JsonProcessingException {
    String queryConfigurationJson = rowView.getColumn("query_configuration", String.class);
    if (queryConfigurationJson == null) {
      return DEFAULT_QUERY_CONFIGURATION;
    }
    Types.QueryConfiguration queryConfiguration =
        objectMapper.readValue(queryConfigurationJson, Types.QueryConfiguration.class);
    if (queryConfiguration == null) {
      return DEFAULT_QUERY_CONFIGURATION;
    }
    return queryConfiguration;
  }

  public List<Types.Session> getSessions(String username) {
    return jdbi.withHandle(
        handle -> {
          var sql =
              """
                SELECT cs.*, csds.data_source_id FROM CHAT_SESSION cs
                LEFT JOIN CHAT_SESSION_DATA_SOURCE csds ON cs.id=csds.chat_session_id
                WHERE cs.DELETED IS NULL AND cs.created_by_id = :username
                ORDER BY last_interaction_time DESC, time_created DESC
              """;
          return querySessions(handle.createQuery(sql).bind("username", username))
              .map(Types.Session.SessionBuilder::build)
              .toList();
        });
  }

  public List<Types.Session> getSessionsByProjectId(Long projectId) {
    return jdbi.withHandle(
        handle -> {
          var sql =
              """
                SELECT cs.*, csds.data_source_id FROM CHAT_SESSION cs
                LEFT JOIN CHAT_SESSION_DATA_SOURCE csds ON cs.id=csds.chat_session_id
                WHERE cs.DELETED IS NULL AND cs.project_id = :projectId
                ORDER BY last_interaction_time DESC, time_created DESC
              """;
          return querySessions(handle.createQuery(sql).bind("projectId", projectId))
              .map(Types.Session.SessionBuilder::build)
              .toList();
        });
  }

  public void delete(Long id) {
    jdbi.useHandle(
        handle -> handle.execute("UPDATE CHAT_SESSION SET DELETED = ? WHERE ID = ?", true, id));
  }

  public void deleteByProjectId(Long projectId) {
    jdbi.useHandle(
        handle ->
            handle.execute(
                "UPDATE CHAT_SESSION SET DELETED = ? WHERE project_id = ?", true, projectId));
  }

  public void deleteByProjectId(Handle handle, Long projectId) {
    handle.execute("UPDATE CHAT_SESSION SET DELETED = ? WHERE project_id = ?", true, projectId);
  }

  public void update(Types.Session input) {
    var updatedInput = input.withTimeUpdated(Instant.now());
    String json = serializeQueryConfiguration(input);
    jdbi.useTransaction(
        handle -> {
          var sql =
              """
                  UPDATE CHAT_SESSION
                  SET name = :name, updated_by_id = :updatedById, inference_model = :inferenceModel, query_configuration = :queryConfiguration,
                      response_chunks = :responseChunks, time_updated = :timeUpdated, rerank_model = :rerankModel
                  WHERE id = :id
                """;
          handle
              .createUpdate(sql)
              .bind("queryConfiguration", json)
              .bindMethods(updatedInput)
              .execute();
          handle
              .createUpdate("DELETE FROM CHAT_SESSION_DATA_SOURCE WHERE CHAT_SESSION_ID = :id")
              .bind("id", input.id())
              .execute();
          insertSessionDataSources(handle, input.id(), input.dataSourceIds());
        });
  }

  private String serializeQueryConfiguration(Types.Session input) {
    try {
      return objectMapper.writeValueAsString(input.queryConfiguration());
    } catch (JsonProcessingException e) {
      throw new RuntimeException(e);
    }
  }

  public int getNumberOfSessions() {
    return jdbi.withHandle(
        handle -> {
          try (var query = handle.createQuery("SELECT count(*) FROM CHAT_SESSION")) {
            return query.mapTo(Integer.class).one();
          }
        });
  }

  public static SessionRepository createNull() {
    return new SessionRepository(JdbiConfiguration.createNull());
  }
}
