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

package com.cloudera.cai.rag.sessions;

import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.util.exceptions.NotFound;
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
  private final Jdbi jdbi;

  public SessionRepository(Jdbi jdbi) {
    this.jdbi = jdbi;
  }

  public Long create(Types.Session input) {
    return jdbi.inTransaction(
        handle -> {
          var sql =
              """
            INSERT INTO CHAT_SESSION (name, created_by_id, updated_by_id)
            VALUES (:name, :createdById, :updatedById)
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
      update.bindMethods(input);
      return update.executeAndReturnGeneratedKeys("id").mapTo(Long.class).one();
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
                    sessionId ->
                        Types.Session.builder()
                            .id(sessionId)
                            .name(rowView.getColumn("name", String.class))
                            .createdById(rowView.getColumn("created_by_id", String.class))
                            .timeCreated(rowView.getColumn("time_created", Instant.class))
                            .updatedById(rowView.getColumn("updated_by_id", String.class))
                            .timeUpdated(rowView.getColumn("time_updated", Instant.class))
                            .lastInteractionTime(
                                rowView.getColumn("last_interaction_time", Instant.class)));
            if (rowView.getColumn("data_source_id", Long.class) != null) {
              sessionBuilder.dataSourceId(rowView.getColumn("data_source_id", Long.class));
            }
          });
    }
  }

  public List<Types.Session> getSessions() {
    return jdbi.withHandle(
        handle -> {
          var sql =
              """
                SELECT cs.*, csds.data_source_id FROM CHAT_SESSION cs
                LEFT JOIN CHAT_SESSION_DATA_SOURCE csds ON cs.id=csds.chat_session_id
                WHERE cs.DELETED IS NULL
                ORDER BY last_interaction_time DESC, time_created DESC
              """;
          return querySessions(handle.createQuery(sql))
              .map(Types.Session.SessionBuilder::build)
              .toList();
        });
  }

  public static SessionRepository createNull() {
    return new SessionRepository(JdbiConfiguration.createNull());
  }

  public void delete(Long id) {
    jdbi.useHandle(
        handle -> {
          handle.execute("UPDATE CHAT_SESSION SET DELETED = ? WHERE ID = ?", true, id);
        });
  }
}
