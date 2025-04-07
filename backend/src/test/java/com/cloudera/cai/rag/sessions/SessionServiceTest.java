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

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.projects.ProjectRepository;
import com.cloudera.cai.rag.projects.ProjectService;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class SessionServiceTest {
  private static final String USERNAME = "test-user";
  private final RagDataSourceRepository ragDataSourceRepository =
      RagDataSourceRepository.createNull();

  @Test
  void create() {
    SessionService sessionService =
        new SessionService(SessionRepository.createNull(), ProjectRepository.createNull());
    Types.Session result =
        sessionService.create(
            TestData.createTestSessionInstance("test")
                .withCreatedById(USERNAME)
                .withUpdatedById(USERNAME),
            USERNAME);
    assertThat(result).isNotNull();
  }

  @Test
  void create_cleanData() {
    SessionService sessionService =
        new SessionService(SessionRepository.createNull(), ProjectRepository.createNull());
    Types.Session result =
        sessionService.create(
            TestData.createTestSessionInstance("test")
                .withRerankModel("")
                .withCreatedById(USERNAME)
                .withUpdatedById(USERNAME),
            USERNAME);
    assertThat(result.rerankModel()).isNull();
    assertThat(result).isNotNull();
  }

  @Test
  void update() {
    // Create repositories
    ProjectRepository projectRepository = ProjectRepository.createNull();
    SessionService sessionService =
        new SessionService(SessionRepository.createNull(), projectRepository);

    // Create a project
    ProjectService projectService = ProjectService.createNull();
    var project =
        projectService.createProject(TestData.createTestProjectInstance("test-project", false));

    long dataSourceId = TestData.createTestDataSource(ragDataSourceRepository);

    // Add data source ID 4L to the project
    projectRepository.addDataSourceToProject(project.id(), dataSourceId);

    // Create a session with the project ID
    Types.Session result =
        sessionService.create(
            TestData.createTestSessionInstance("test")
                .withProjectId(project.id())
                .withCreatedById(USERNAME)
                .withUpdatedById(USERNAME),
            USERNAME);

    // Update the session with dataSourceId
    var updated = result.withRerankModel("").withDataSourceIds(List.of(dataSourceId));
    var updatedResult = sessionService.update(updated, USERNAME);

    // Verify the update
    assertThat(updatedResult.rerankModel()).isNull();
    assertThat(updatedResult.dataSourceIds()).containsExactly(dataSourceId);
  }

  @Test
  void delete() {
    SessionService sessionService =
        new SessionService(SessionRepository.createNull(), ProjectRepository.createNull());
    var input =
        TestData.createTestSessionInstance("test")
            .withCreatedById(USERNAME)
            .withUpdatedById(USERNAME);
    var createdSession = sessionService.create(input, USERNAME);
    sessionService.delete(createdSession.id());
    assertThat(sessionService.getSessions("fake-user")).doesNotContain(createdSession);
  }

  @Test
  void getSessions() {
    SessionService sessionService =
        new SessionService(SessionRepository.createNull(), ProjectRepository.createNull());
    String username1 = UUID.randomUUID().toString();
    String username2 = UUID.randomUUID().toString();
    String username3 = UUID.randomUUID().toString();
    var input =
        TestData.createTestSessionInstance("test")
            .withCreatedById(username1)
            .withUpdatedById(username1);
    var input2 =
        TestData.createTestSessionInstance("test2")
            .withCreatedById(username2)
            .withUpdatedById(username2);
    sessionService.create(input, username1);
    sessionService.create(input2, username2);

    assertThat(sessionService.getSessions(username1)).hasSizeGreaterThanOrEqualTo(1);
    assertThat(sessionService.getSessions(username2)).hasSizeGreaterThanOrEqualTo(1);
    assertThat(sessionService.getSessions(username3)).hasSize(0);
  }

  @Test
  void getSessionsByProjectId() {
    SessionService sessionService =
        new SessionService(SessionRepository.createNull(), ProjectRepository.createNull());
    ProjectService projectService = ProjectService.createNull();

    var project =
        projectService.createProject(TestData.createTestProjectInstance("test-project", false));
    var project2 =
        projectService.createProject(TestData.createTestProjectInstance("test-project2", false));

    // Create sessions with different project IDs
    String user1 = "user1";
    var session1 =
        TestData.createTestSessionInstance("test1")
            .withProjectId(project.id())
            .withCreatedById(user1)
            .withUpdatedById(user1);

    String user2 = "user2";
    var session2 =
        TestData.createTestSessionInstance("test2")
            .withProjectId(project.id())
            .withCreatedById(user2)
            .withUpdatedById(user2);

    String user3 = "user3";
    var session3 =
        TestData.createTestSessionInstance("test3")
            .withProjectId(project2.id())
            .withCreatedById(user3)
            .withUpdatedById(user3);

    // Save the sessions
    sessionService.create(session1, user1);
    sessionService.create(session2, user2);
    sessionService.create(session3, user3);

    var projectOneSessions = sessionService.getSessionsByProjectId(project.id());

    assertThat(projectOneSessions).hasSizeGreaterThanOrEqualTo(2);
    assertThat(projectOneSessions).extracting("name").contains("test1", "test2");
    assertThat(projectOneSessions).extracting("projectId").containsOnly(project.id());

    var projectTwoSessions = sessionService.getSessionsByProjectId(project2.id());

    assertThat(projectTwoSessions).hasSize(1);
    assertThat(projectTwoSessions).extracting("name").containsExactly("test3");
    assertThat(projectTwoSessions).extracting("projectId").containsOnly(project2.id());

    // Get sessions for non-existent project ID
    var nonExistentProjectSessions = sessionService.getSessionsByProjectId(999L);

    // Verify that no sessions are returned
    assertThat(nonExistentProjectSessions).isEmpty();
  }

  @Test
  void create_withInvalidDataSourceId() {
    // Create a session service with null repositories
    SessionService sessionService =
        new SessionService(SessionRepository.createNull(), ProjectRepository.createNull());

    // Create a project to get a valid project ID
    ProjectService projectService = ProjectService.createNull();
    var project =
        projectService.createProject(TestData.createTestProjectInstance("test-project", false));

    // Create a session with an invalid data source ID (not in the project)
    var sessionWithInvalidDataSource =
        TestData.createTestSessionInstance("test-session")
            .withProjectId(project.id())
            .withDataSourceIds(List.of(999L)) // Invalid data source ID
            .withCreatedById(USERNAME)
            .withUpdatedById(USERNAME);

    // Verify that creating a session with an invalid data source ID throws an exception
    assertThatThrownBy(() -> sessionService.create(sessionWithInvalidDataSource, USERNAME))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Invalid data source IDs provided.");
  }

  @Test
  void update_withInvalidDataSourceId() {
    // Create a session service with null repositories
    SessionService sessionService =
        new SessionService(SessionRepository.createNull(), ProjectRepository.createNull());

    // Create a project to get a valid project ID
    ProjectService projectService = ProjectService.createNull();
    var project =
        projectService.createProject(TestData.createTestProjectInstance("test-project", false));

    // Create a session with no data source IDs
    var session =
        TestData.createTestSessionInstance("test-session")
            .withProjectId(project.id())
            .withDataSourceIds(List.of()) // No data source IDs
            .withCreatedById(USERNAME)
            .withUpdatedById(USERNAME);

    // Create the session
    var createdSession = sessionService.create(session, USERNAME);

    // Update the session with an invalid data source ID
    var updatedSession = createdSession.withDataSourceIds(List.of(999L)); // Invalid data source ID

    // Verify that updating a session with an invalid data source ID throws an exception
    // Note: This test will fail until the bug is fixed in SessionService.update()
    assertThatThrownBy(() -> sessionService.update(updatedSession, USERNAME))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Invalid data source IDs provided.");
  }
}
