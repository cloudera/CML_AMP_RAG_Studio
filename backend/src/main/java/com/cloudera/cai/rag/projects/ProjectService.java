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

package com.cloudera.cai.rag.projects;

import com.cloudera.cai.rag.Types.Project;
import com.cloudera.cai.rag.Types.RagDataSource;
import com.cloudera.cai.rag.Types.Session;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.sessions.SessionRepository;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.jdbi.v3.core.Jdbi;
import org.springframework.stereotype.Component;

@Component
public class ProjectService {
  private final ProjectRepository projectRepository;
  private final SessionRepository sessionRepository;
  private final RagDataSourceRepository dataSourceRepository;
  private final Jdbi jdbi;

  public ProjectService(
      ProjectRepository projectRepository,
      SessionRepository sessionRepository,
      RagDataSourceRepository dataSourceRepository,
      Jdbi jdbi) {
    this.projectRepository = projectRepository;
    this.sessionRepository = sessionRepository;
    this.dataSourceRepository = dataSourceRepository;
    this.jdbi = jdbi;
  }

  public Project createProject(Project input) {
    var id =
        projectRepository.createProject(
            input.withCreatedById(input.createdById()).withUpdatedById(input.updatedById()));
    return projectRepository.getProjectById(id);
  }

  public Project updateProject(Project input) {
    projectRepository.updateProject(input);
    return projectRepository.getProjectById(input.id());
  }

  public void deleteProject(Long id) {
    jdbi.useTransaction(
        handle -> {
          projectRepository.deleteProject(handle, id);
          sessionRepository.deleteByProjectId(handle, id);
        });
  }

  public List<Project> getProjects() {
    return projectRepository.getProjects();
  }

  public Project getProjectById(Long id) {
    return projectRepository.getProjectById(id);
  }

  public Project getDefaultProject() {
    return projectRepository.getDefaultProject();
  }

  public void addDataSourceToProject(Long projectId, Long dataSourceId) {
    projectRepository.addDataSourceToProject(projectId, dataSourceId);
  }

  public void removeDataSourceFromProject(Long projectId, Long dataSourceId) {
    projectRepository.removeDataSourceFromProject(projectId, dataSourceId);

    removeDataSourceFromProjectSessions(projectId, dataSourceId);
  }

  private void removeDataSourceFromProjectSessions(Long projectId, Long dataSourceId) {
    List<Session> sessions = sessionRepository.getSessionsByProjectId(projectId);
    for (Session session : sessions) {
      if (session.dataSourceIds().contains(dataSourceId)) {
        List<Long> updatedDataSourceIds = new ArrayList<>(session.dataSourceIds());
        updatedDataSourceIds.remove(dataSourceId);
        Session updatedSession = session.withDataSourceIds(updatedDataSourceIds);
        sessionRepository.update(updatedSession);
      }
    }
  }

  public List<RagDataSource> getDataSourcesForProject(Long projectId) {
    Set<Long> dataSourceIds =
        new HashSet<>(projectRepository.getDataSourceIdsForProject(projectId));
    List<RagDataSource> dataSources = dataSourceRepository.getRagDataSources();
    return dataSources.stream()
        .filter(dataSource -> dataSourceIds.contains(dataSource.id()))
        .toList();
  }

  // Nullables stuff below here.

  public static ProjectService createNull() {
    return new ProjectService(
        ProjectRepository.createNull(),
        SessionRepository.createNull(),
        RagDataSourceRepository.createNull(),
        JdbiConfiguration.createNull());
  }
}
