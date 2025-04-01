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

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.Types.Project;
import com.cloudera.cai.rag.Types.RagDataSource;
import com.cloudera.cai.rag.Types.Session;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.sessions.SessionService;
import com.cloudera.cai.util.exceptions.BadRequest;
import com.cloudera.cai.util.exceptions.NotFound;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

class ProjectControllerTest {

  private final ProjectService projectService = ProjectService.createNull();

  @Test
  void create() {
    ProjectController controller = createController();
    Types.CreateProject createProject = TestData.createProjectRequest("test-project");

    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);

    var result = controller.create(createProject, request);

    assertThat(result.id()).isNotNull();
    assertThat(result.name()).isEqualTo("test-project");
    assertThat(result.defaultProject()).isFalse();
    assertThat(result.timeCreated()).isNotNull();
    assertThat(result.timeUpdated()).isNotNull();
    assertThat(result.createdById()).isEqualTo("test-user");
    assertThat(result.updatedById()).isEqualTo("test-user");
  }

  @Test
  void update() {
    ProjectController controller = createController();

    // Create a new Project
    Types.CreateProject createProject = TestData.createProjectRequest("original-name");
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var newProject = controller.create(createProject, request);

    // Update the project
    Project updatedProject = newProject.withName("updated-name");
    var result = controller.update(newProject.id(), updatedProject, request);

    assertThat(result.id()).isEqualTo(newProject.id());
    assertThat(result.name()).isEqualTo("updated-name");
    assertThat(result.defaultProject()).isFalse();
    assertThat(result.createdById()).isEqualTo("test-user");
    assertThat(result.updatedById()).isEqualTo("test-user");
  }

  @Test
  void deleteProject() {
    ProjectController controller = createController();

    // Create a new Project
    Types.CreateProject createProject = TestData.createProjectRequest("test-project");
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var newProject = controller.create(createProject, request);

    // Delete the project
    controller.deleteProject(newProject.id());

    // Verify the project is deleted
    assertThatThrownBy(() -> projectService.getProjectById(newProject.id()))
        .isInstanceOf(NotFound.class);
  }

  @Test
  void deleteProjectWithAssociatedData() {
    // Create controller with both ProjectService and SessionService
    ProjectService projectService = ProjectService.createNull();
    SessionService sessionService = SessionService.createNull();
    ProjectController controller = new ProjectController(projectService, sessionService);

    // Create a new Project
    Types.CreateProject createProject = TestData.createProjectRequest("test-project");
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var newProject = controller.create(createProject, request);

    // Create a data source
    var dataSourceId = TestData.createTestDataSource(RagDataSourceRepository.createNull());

    // Add the data source to the project
    controller.addDataSourceToProject(newProject.id(), dataSourceId);

    // Create a session for the project
    Types.CreateSession createSession = TestData.createSessionInstance("test-session");
    String username = "test-user";
    var session =
        sessionService.create(
            Types.Session.fromCreateRequest(createSession, username).withProjectId(newProject.id()),
            username);

    // Verify the data source is associated with the project
    List<RagDataSource> dataSources = controller.getDataSourcesForProject(newProject.id());
    assertThat(dataSources).extracting("id").contains(dataSourceId);

    // Verify the session is associated with the project
    List<Types.Session> sessions = controller.getSessionsForProject(newProject.id());
    assertThat(sessions).extracting(Types.Session::id).contains(session.id());

    // Delete the project
    controller.deleteProject(newProject.id());

    // Verify the project is deleted
    assertThatThrownBy(() -> projectService.getProjectById(newProject.id()))
        .isInstanceOf(NotFound.class);

    // Verify the data source associations are deleted
    assertThat(projectService.getDataSourcesForProject(newProject.id())).isEmpty();

    // Verify the sessions are marked as deleted
    assertThat(sessionService.getSessionsByProjectId(newProject.id())).isEmpty();
  }

  @Test
  void getProjects() {
    ProjectController controller = createController();

    // Create a new Project
    Types.CreateProject createProject = TestData.createProjectRequest("test-project");
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var newProject = controller.create(createProject, request);

    // Create a new Project from a different user
    Types.CreateProject createDiffUserProject =
        TestData.createProjectRequest("diff-user-test-project");
    var request2 = new MockHttpServletRequest();
    TestData.addUserToRequest(request2, "diff-user");
    var diffUserProject = controller.create(createDiffUserProject, request2);

    // Get user's projects
    List<Project> results = controller.getProjects(request);

    assertThat(results)
        .filteredOn(project -> project.id().equals(newProject.id()))
        .contains(newProject)
        .doesNotContain(diffUserProject);
  }

  @Test
  void getDefaultProject() {
    ProjectController controller = createController();

    // Get the default project
    var result = controller.getDefaultProject();

    assertThat(result.name()).isEqualTo("Default");
    assertThat(result.defaultProject()).isTrue();
  }

  @Test
  void addAndRemoveDataSourceToProject() {
    ProjectController controller = createController();

    // Create a new Project
    Types.CreateProject createProject = TestData.createProjectRequest("test-project");
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var newProject = controller.create(createProject, request);

    var dataSourceId = TestData.createTestDataSource(RagDataSourceRepository.createNull());

    controller.addDataSourceToProject(newProject.id(), dataSourceId);

    List<RagDataSource> dataSources = controller.getDataSourcesForProject(newProject.id());

    assertThat(dataSources).extracting("id").contains(dataSourceId);

    controller.removeDataSourceFromProject(newProject.id(), dataSourceId);

    dataSources = controller.getDataSourcesForProject(newProject.id());

    assertThat(dataSources).extracting("id").doesNotContain(dataSourceId);
  }

  @Test
  void createWithEmptyName() {
    ProjectController controller = createController();
    Types.CreateProject createProject = TestData.createProjectRequest("");

    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);

    assertThatThrownBy(() -> controller.create(createProject, request))
        .isInstanceOf(BadRequest.class)
        .hasMessageContaining("name must be a non-empty string");
  }

  @Test
  void updateWithEmptyName() {
    ProjectController controller = createController();

    // Create a new Project
    Types.CreateProject createProject = TestData.createProjectRequest("original-name");
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var newProject = controller.create(createProject, request);

    // Update with empty name
    Project updatedProject = newProject.withName("");

    assertThatThrownBy(() -> controller.update(newProject.id(), updatedProject, request))
        .isInstanceOf(BadRequest.class)
        .hasMessageContaining("name must be a non-empty string");
  }

  @Test
  void getProjectByIdNotFound() {

    assertThatThrownBy(() -> projectService.getProjectById(999L)).isInstanceOf(NotFound.class);
  }

  @Test
  void getSessionsForProject() {
    // Create controller with both ProjectService and SessionService
    ProjectService projectService = ProjectService.createNull();
    SessionService sessionService = SessionService.createNull();
    ProjectController controller = new ProjectController(projectService, sessionService);

    // Create a project
    Types.CreateProject createProject = TestData.createProjectRequest("test-project");
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var project = controller.create(createProject, request);

    // Create another project
    Types.CreateProject createProject2 = TestData.createProjectRequest("test-project-2");
    var project2 = controller.create(createProject2, request);

    // Create sessions with different project IDs
    var session1 =
        TestData.createTestSessionInstance("session1")
            .withProjectId(project.id())
            .withCreatedById("user1")
            .withUpdatedById("user1");

    var session2 =
        TestData.createTestSessionInstance("session2")
            .withProjectId(project.id())
            .withCreatedById("user2")
            .withUpdatedById("user2");

    var session3 =
        TestData.createTestSessionInstance("session3")
            .withProjectId(project2.id())
            .withCreatedById("user3")
            .withUpdatedById("user3");

    // Save the sessions
    sessionService.create(session1, "user1");
    sessionService.create(session2, "user2");
    sessionService.create(session3, "user3");

    // Get sessions for the first project
    List<Session> projectSessions = controller.getSessionsForProject(project.id());

    // Verify that only sessions with the specified project ID are returned
    assertThat(projectSessions).hasSize(2);
    assertThat(projectSessions)
        .extracting("name")
        .containsExactlyInAnyOrder("session1", "session2");
    assertThat(projectSessions).extracting("projectId").containsOnly(project.id());

    // Get sessions for the second project
    List<Session> project2Sessions = controller.getSessionsForProject(project2.id());

    // Verify that only sessions with the specified project ID are returned
    assertThat(project2Sessions).hasSize(1);
    assertThat(project2Sessions).extracting("name").containsExactly("session3");
    assertThat(project2Sessions).extracting("projectId").containsOnly(project2.id());

    // Get sessions for non-existent project ID
    List<Session> nonExistentProjectSessions = controller.getSessionsForProject(999L);

    // Verify that no sessions are returned
    assertThat(nonExistentProjectSessions).isEmpty();
  }

  @Test
  void removeDataSourceFromProjectRemovesFromSessions() {
    // Create controller with both ProjectService and SessionService
    ProjectService projectService = ProjectService.createNull();
    SessionService sessionService = SessionService.createNull();
    ProjectController controller = new ProjectController(projectService, sessionService);

    // Create a new Project
    Types.CreateProject createProject = TestData.createProjectRequest("test-project");
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var newProject = controller.create(createProject, request);

    // Create a data source
    var dataSourceId = TestData.createTestDataSource(RagDataSourceRepository.createNull());

    // Add the data source to the project
    controller.addDataSourceToProject(newProject.id(), dataSourceId);

    // Create a session for the project with the data source
    Types.CreateSession createSession =
        TestData.createSessionInstance("test-session", List.of(dataSourceId), newProject.id());
    String username = "test-user";
    var session =
        sessionService.create(
            Types.Session.fromCreateRequest(createSession, username).withProjectId(newProject.id()),
            username);

    // Verify the data source is in the session's list of data sources
    assertThat(session.dataSourceIds()).contains(dataSourceId);

    // Remove the data source from the project
    controller.removeDataSourceFromProject(newProject.id(), dataSourceId);

    // Get the updated session
    var updatedSession = sessionService.getSessionById(session.id(), username);

    // Verify the data source is no longer in the session's list of data sources
    assertThat(updatedSession.dataSourceIds()).doesNotContain(dataSourceId);
  }

  private ProjectController createController() {
    return new ProjectController(projectService, SessionService.createNull());
  }
}
