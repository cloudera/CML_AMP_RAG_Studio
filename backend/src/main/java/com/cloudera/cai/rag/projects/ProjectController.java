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

import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.Types.RagDataSource;
import com.cloudera.cai.rag.sessions.SessionService;
import com.cloudera.cai.rag.util.UsernameExtractor;
import com.cloudera.cai.util.exceptions.BadRequest;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@Slf4j
@RequestMapping("/api/v1/rag/projects")
public class ProjectController {
  private final ProjectService projectService;
  private final SessionService sessionService;
  private final UsernameExtractor usernameExtractor = new UsernameExtractor();

  @Autowired
  public ProjectController(ProjectService projectService, SessionService sessionService) {
    this.projectService = projectService;
    this.sessionService = sessionService;
  }

  @PostMapping(consumes = "application/json", produces = "application/json")
  public Types.Project create(@RequestBody Types.CreateProject input, HttpServletRequest request) {
    log.debug("Creating Project: {}", input);
    if (input.name() == null || input.name().isEmpty()) {
      throw new BadRequest("name must be a non-empty string");
    }
    String username = usernameExtractor.extractUsername(request);
    return projectService.createProject(Types.Project.fromCreateRequest(input, username));
  }

  @PostMapping(value = "/{id}", consumes = "application/json", produces = "application/json")
  public Types.Project update(
      @PathVariable Long id, @RequestBody Types.Project input, HttpServletRequest request) {
    log.info("Updating Project: {}", input);
    if (input.name() == null || input.name().isEmpty()) {
      throw new BadRequest("name must be a non-empty string");
    }
    String username = usernameExtractor.extractUsername(request);
    input = input.withId(id).withUpdatedById(username);
    return projectService.updateProject(input);
  }

  public Types.Project getProjectById(Long id) {
    return projectService.getProjectById(id);
  }

  @DeleteMapping(value = "/{id}")
  public void deleteProject(@PathVariable long id) {
    log.debug("Deleting Project with id: {}", id);
    projectService.deleteProject(id);
  }

  @GetMapping(produces = "application/json")
  public List<Types.Project> getProjects(HttpServletRequest request) {
    log.debug("Getting user's Projects");
    String username = usernameExtractor.extractUsername(request);
    return projectService.getProjects(username);
  }

  @GetMapping(value = "/default", produces = "application/json")
  public Types.Project getDefaultProject() {
    log.debug("Getting default Project");
    return projectService.getDefaultProject();
  }

  @PostMapping(value = "/{projectId}/dataSources/{dataSourceId}")
  public void addDataSourceToProject(
      @PathVariable Long projectId, @PathVariable Long dataSourceId) {
    log.debug("Adding DataSource {} to Project {}", dataSourceId, projectId);
    projectService.addDataSourceToProject(projectId, dataSourceId);
  }

  @DeleteMapping(value = "/{projectId}/dataSources/{dataSourceId}")
  public void removeDataSourceFromProject(
      @PathVariable Long projectId, @PathVariable Long dataSourceId) {
    log.debug("Removing DataSource {} from Project {}", dataSourceId, projectId);
    projectService.removeDataSourceFromProject(projectId, dataSourceId);
  }

  @GetMapping(value = "/{projectId}/dataSources", produces = "application/json")
  public List<RagDataSource> getDataSourcesForProject(@PathVariable Long projectId) {
    log.debug("Getting DataSource IDs for Project {}", projectId);
    return projectService.getDataSourcesForProject(projectId);
  }

  @GetMapping(value = "/{projectId}/sessions", produces = "application/json")
  public List<Types.Session> getSessionsForProject(@PathVariable Long projectId) {
    log.debug("Getting Sessions for Project {}", projectId);
    return sessionService.getSessionsByProjectId(projectId);
  }
}
