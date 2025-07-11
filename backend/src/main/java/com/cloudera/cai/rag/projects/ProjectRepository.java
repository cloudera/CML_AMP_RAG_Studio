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
public class ProjectRepository {
  private final DatabaseOperations databaseOperations;

  public ProjectRepository(DatabaseOperations databaseOperations) {
    this.databaseOperations = databaseOperations;
  }

  public Long createProject(Project input) {
    return databaseOperations.inTransaction(
        handle -> {
          var sql =
              """
                INSERT INTO project (name, default_project, created_by_id, updated_by_id)
                VALUES (:name, :defaultProject, :createdById, :updatedById)
              """;
          try (var update = handle.createUpdate(sql)) {
            update.bindMethods(input);
            update.bind("defaultProject", false);
            return update.executeAndReturnGeneratedKeys("id").mapTo(Long.class).one();
          }
        });
  }

  public void updateProject(Project input) {
    databaseOperations.inTransaction(
        handle -> {
          var sql =
              """
              UPDATE project
              SET name = :name, updated_by_id = :updatedById, time_updated = :now
              WHERE id = :id
          """;
          try (var update = handle.createUpdate(sql)) {
            return update
                .bind("name", input.name())
                .bind("updatedById", input.updatedById())
                .bind("id", input.id())
                .bind("now", Instant.now())
                .execute();
          }
        });
  }

  public Project getProjectById(Long id) {
    return databaseOperations.withHandle(
        handle -> {
          var sql =
              """
               SELECT *
                 FROM project
               WHERE id = :id
              """;
          handle.registerRowMapper(ConstructorMapper.factory(Project.class));
          try (Query query = handle.createQuery(sql)) {
            query.bind("id", id);
            return query
                .mapTo(Project.class)
                .findOne()
                .orElseThrow(() -> new NotFound("Project not found with id: " + id));
          }
        });
  }

  public List<Project> getProjects(String username) {
    return databaseOperations.withHandle(
        handle -> {
          var sql =
              """
              SELECT *
                FROM project
                WHERE created_by_id = :createdById
                OR default_project = :default
              """;
          handle.registerRowMapper(ConstructorMapper.factory(Project.class));
          try (Query query = handle.createQuery(sql)) {
            query.bind("createdById", username).bind("default", true);
            return query.mapTo(Project.class).list();
          }
        });
  }

  public void deleteProject(Handle handle, Long id) {
    handle.execute("DELETE FROM project_data_source WHERE project_id = ?", id);
    handle.execute("DELETE FROM project WHERE id = ?", id);
  }

  public Project getDefaultProject() {
    return databaseOperations.withHandle(
        handle -> {
          var sql =
              """
               SELECT *
                 FROM project
               WHERE default_project = :default
              """;
          handle.registerRowMapper(ConstructorMapper.factory(Project.class));
          try (Query query = handle.createQuery(sql)) {
            return query
                .bind("default", true)
                .mapTo(Project.class)
                .findOne()
                .orElseThrow(() -> new NotFound("Default project not found"));
          }
        });
  }

  public void addDataSourceToProject(Long projectId, Long dataSourceId) {
    databaseOperations.inTransaction(
        handle -> {
          var sql =
              """
                INSERT INTO project_data_source (project_id, data_source_id)
                VALUES (:projectId, :dataSourceId)
              """;
          try (var update = handle.createUpdate(sql)) {
            return update.bind("projectId", projectId).bind("dataSourceId", dataSourceId).execute();
          }
        });
  }

  public void removeDataSourceFromProject(Long projectId, Long dataSourceId) {
    databaseOperations.inTransaction(
        handle -> {
          var sql =
              """
                DELETE FROM project_data_source
                WHERE project_id = :projectId AND data_source_id = :dataSourceId
              """;
          try (var update = handle.createUpdate(sql)) {
            return update.bind("projectId", projectId).bind("dataSourceId", dataSourceId).execute();
          }
        });
  }

  public List<Long> getDataSourceIdsForProject(Long projectId) {
    return databaseOperations.withHandle(
        handle -> {
          var sql =
              """
               SELECT data_source_id
                 FROM project_data_source
               WHERE project_id = :projectId
              """;
          try (Query query = handle.createQuery(sql)) {
            query.bind("projectId", projectId);
            return query.mapTo(Long.class).list();
          }
        });
  }

  // Nullables stuff below here.

  public static ProjectRepository createNull() {
    // the db configuration will use in-memory db based on env vars.
    return new ProjectRepository(JdbiConfiguration.createNull());
  }
}
