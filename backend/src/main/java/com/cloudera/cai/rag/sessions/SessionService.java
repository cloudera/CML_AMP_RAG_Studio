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
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.datasources.RagDataSourceService;
import com.cloudera.cai.rag.projects.ProjectRepository;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.jdbi.v3.core.Jdbi;
import org.springframework.stereotype.Component;

@Component
public class SessionService {

  private final SessionRepository sessionRepository;
  private final ProjectRepository projectRepository;
  private final Jdbi jdbi;
  private final RagDataSourceRepository ragDataSourceRepository;

  public SessionService(
      SessionRepository sessionRepository,
      ProjectRepository projectRepository,
      Jdbi jdbi,
      RagDataSourceRepository ragDataSourceRepository) {
    this.sessionRepository = sessionRepository;
    this.projectRepository = projectRepository;
    this.jdbi = jdbi;
    this.ragDataSourceRepository = ragDataSourceRepository;
  }

  public Types.Session create(Types.CreateSession createSession, String username) {
    return jdbi.inTransaction(
        handle -> {
          var session = Types.Session.fromCreateRequest(createSession, username);
          validateDataSourceIds(session);
          var id = sessionRepository.create(cleanInputs(session), handle);
          session = sessionRepository.getSessionById(id, username, handle);
          if (createSession.embeddingModel() != null) {
            Types.RagDataSource newDataSource =
                createDataSourceInstance(createSession, username, id);
            Long ragDataSourceId =
                ragDataSourceRepository.createRagDataSource(newDataSource, handle);
            session = session.withAssociatedDataSourceId(ragDataSourceId);
          }
          sessionRepository.update(cleanInputs(session), handle);
          return sessionRepository.getSessionById(session.id(), username, handle);
        });
  }

  private static Types.RagDataSource createDataSourceInstance(
      Types.CreateSession createSession, String username, Long sessionId) {
    return new Types.RagDataSource(
        null,
        "session-" + sessionId,
        createSession.embeddingModel(),
        createSession.inferenceModel(),
        RagDataSourceService.DEFAULT_CHUNK_SIZE,
        RagDataSourceService.DEFAULT_CHUNK_OVERLAP,
        null,
        null,
        username,
        username,
        Types.ConnectionType.MANUAL,
        null,
        null,
        false,
        sessionId);
  }

  private void validateDataSourceIds(Types.Session input) {
    List<Long> dataSourceIds = input.dataSourceIds();
    if (dataSourceIds == null || dataSourceIds.isEmpty()) {
      return;
    }

    Set<Long> validDataSourceIds =
        new HashSet<>(projectRepository.getDataSourceIdsForProject(input.projectId()));
    if (!validDataSourceIds.containsAll(dataSourceIds)) {
      throw new IllegalArgumentException("Invalid data source IDs provided.");
    }
  }

  public Types.Session update(Types.Session input, String username) {
    validateDataSourceIds(input);
    sessionRepository.update(cleanInputs(input));
    return sessionRepository.getSessionById(input.id(), username);
  }

  private Types.Session cleanInputs(Types.Session input) {
    if (input.rerankModel() != null && input.rerankModel().isEmpty()) {
      input = input.withRerankModel(null);
    }
    if (input.dataSourceIds() == null) {
      input = input.withDataSourceIds(List.of());
    }
    return input;
  }

  public List<Types.Session> getSessions(String username) {
    return sessionRepository.getSessions(username);
  }

  public List<Types.Session> getSessionsByProjectId(Long projectId) {
    return sessionRepository.getSessionsByProjectId(projectId);
  }

  public Types.Session getSessionById(Long id, String username) {
    return sessionRepository.getSessionById(id, username);
  }

  public void delete(Long id, String username) {
    Types.Session session = sessionRepository.getSessionById(id, username);
    jdbi.useTransaction(
        handle -> {
          ragDataSourceRepository.deleteDataSource(handle, session.associatedDataSourceId());
          sessionRepository.delete(handle, id);
        });
  }

  public static SessionService createNull() {
    return new SessionService(
        SessionRepository.createNull(),
        ProjectRepository.createNull(),
        JdbiConfiguration.createNull(),
        RagDataSourceRepository.createNull());
  }
}
