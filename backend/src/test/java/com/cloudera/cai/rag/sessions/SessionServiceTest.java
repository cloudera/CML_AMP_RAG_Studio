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

import static org.assertj.core.api.Assertions.assertThat;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.projects.ProjectService;
import java.util.List;
import org.junit.jupiter.api.Test;

class SessionServiceTest {
  @Test
  void create() {
    SessionService sessionService = new SessionService(SessionRepository.createNull());
    Types.Session result =
        sessionService.create(
            TestData.createTestSessionInstance("test")
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    assertThat(result).isNotNull();
  }

  @Test
  void create_cleanData() {
    SessionService sessionService = new SessionService(SessionRepository.createNull());
    Types.Session result =
        sessionService.create(
            TestData.createTestSessionInstance("test")
                .withRerankModel("")
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    assertThat(result.rerankModel()).isNull();
    assertThat(result).isNotNull();
  }

  @Test
  void update() {
    SessionService sessionService = new SessionService(SessionRepository.createNull());
    Types.Session result =
        sessionService.create(
            TestData.createTestSessionInstance("test")
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    var updated = result.withRerankModel("").withDataSourceIds(List.of(4L));
    var updatedResult = sessionService.update(updated);
    assertThat(updatedResult.rerankModel()).isNull();
    assertThat(updatedResult.dataSourceIds()).containsExactly(4L);
  }

  @Test
  void delete() {
    SessionService sessionService = new SessionService(SessionRepository.createNull());
    var input =
        TestData.createTestSessionInstance("test").withCreatedById("abc").withUpdatedById("abc");
    var createdSession = sessionService.create(input);
    sessionService.delete(createdSession.id());
    assertThat(sessionService.getSessions()).doesNotContain(createdSession);
  }

  @Test
  void getSessions() {
    SessionService sessionService = new SessionService(SessionRepository.createNull());
    var input =
        TestData.createTestSessionInstance("test").withCreatedById("abc").withUpdatedById("abc");
    var input2 =
        TestData.createTestSessionInstance("test2").withCreatedById("abc2").withUpdatedById("abc2");
    sessionService.create(input);
    sessionService.create(input2);

    var result = sessionService.getSessions();

    assertThat(result).hasSizeGreaterThanOrEqualTo(2);
  }

  @Test
  void getSessionsByProjectId() {
    SessionService sessionService = new SessionService(SessionRepository.createNull());
    ProjectService projectService = ProjectService.createNull();

    var project =
        projectService.createProject(TestData.createTestProjectInstance("test-project", false));
    var project2 =
        projectService.createProject(TestData.createTestProjectInstance("test-project2", false));

    // Create sessions with different project IDs
    var session1 =
        TestData.createTestSessionInstance("test1")
            .withProjectId(project.id())
            .withCreatedById("user1")
            .withUpdatedById("user1");

    var session2 =
        TestData.createTestSessionInstance("test2")
            .withProjectId(project.id())
            .withCreatedById("user2")
            .withUpdatedById("user2");

    var session3 =
        TestData.createTestSessionInstance("test3")
            .withProjectId(project2.id())
            .withCreatedById("user3")
            .withUpdatedById("user3");

    // Save the sessions
    sessionService.create(session1);
    sessionService.create(session2);
    sessionService.create(session3);

    // Get sessions for project ID 1
    var projectOneSessions = sessionService.getSessionsByProjectId(project.id());

    // Verify that sessions with project ID 1 are returned
    assertThat(projectOneSessions).hasSizeGreaterThanOrEqualTo(2);
    assertThat(projectOneSessions).extracting("name").contains("test1", "test2");
    assertThat(projectOneSessions).extracting("projectId").containsOnly(project.id());

    // Get sessions for project ID 2
    var projectTwoSessions = sessionService.getSessionsByProjectId(project2.id());

    // Verify that only sessions with project ID 2 are returned
    assertThat(projectTwoSessions).hasSize(1);
    assertThat(projectTwoSessions).extracting("name").containsExactly("test3");
    assertThat(projectTwoSessions).extracting("projectId").containsOnly(project2.id());

    // Get sessions for non-existent project ID
    var nonExistentProjectSessions = sessionService.getSessionsByProjectId(999L);

    // Verify that no sessions are returned
    assertThat(nonExistentProjectSessions).isEmpty();
  }
}
