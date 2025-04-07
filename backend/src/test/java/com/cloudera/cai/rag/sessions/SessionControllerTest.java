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
import com.cloudera.cai.rag.projects.ProjectService;
import com.cloudera.cai.util.exceptions.NotFound;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

class SessionControllerTest {
  @Test
  void create() {
    SessionController sessionController = new SessionController(SessionService.createNull());
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var sessionName = "test";
    Types.CreateSession input = TestData.createSessionInstance(sessionName);
    Types.Session result = sessionController.create(input, request);
    assertThat(result.id()).isNotNull();
    assertThat(result.name()).isEqualTo(sessionName);
    assertThat(result.inferenceModel()).isEqualTo(input.inferenceModel());
    assertThat(result.rerankModel()).isEqualTo(input.rerankModel());
    assertThat(result.responseChunks()).isEqualTo(input.responseChunks());
    assertThat(result.dataSourceIds()).isEmpty();
    assertThat(result.timeCreated()).isNotNull();
    assertThat(result.timeUpdated()).isNotNull();
    assertThat(result.createdById()).isEqualTo("test-user");
    assertThat(result.updatedById()).isEqualTo("test-user");
    assertThat(result.lastInteractionTime()).isNull();
    assertThat(result.queryConfiguration()).isNotNull();
  }

  @Test
  void create_noDataSource() {
    SessionController sessionController = new SessionController(SessionService.createNull());
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var sessionName = "test";
    Types.CreateSession input = TestData.createSessionInstance(sessionName, List.of(), 1L);
    Types.Session result = sessionController.create(input, request);
    assertThat(result.id()).isNotNull();
    assertThat(result.name()).isEqualTo(sessionName);
    assertThat(result.inferenceModel()).isEqualTo(input.inferenceModel());
    assertThat(result.rerankModel()).isEqualTo(input.rerankModel());
    assertThat(result.responseChunks()).isEqualTo(input.responseChunks());
    assertThat(result.dataSourceIds()).isEmpty();
    assertThat(result.timeCreated()).isNotNull();
    assertThat(result.timeUpdated()).isNotNull();
    assertThat(result.createdById()).isEqualTo("test-user");
    assertThat(result.updatedById()).isEqualTo("test-user");
    assertThat(result.lastInteractionTime()).isNull();
    assertThat(result.queryConfiguration()).isNotNull();
  }

  @Test
  void get() {
    SessionController sessionController = new SessionController(SessionService.createNull());
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var input = TestData.createSessionInstance("test");
    var createdSession = sessionController.create(input, request);
    var result = sessionController.getSession(createdSession.id(), request);
    assertThat(result).isEqualTo(createdSession);
  }

  @Test
  void get_otherUserSession() {
    SessionController sessionController = new SessionController(SessionService.createNull());
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var input = TestData.createSessionInstance("test");
    var createdSession = sessionController.create(input, request);

    var request2 = new MockHttpServletRequest();
    TestData.addUserToRequest(request2, "other-user");
    assertThatThrownBy(() -> sessionController.getSession(createdSession.id(), request2))
        .isInstanceOf(NotFound.class);
  }

  @Test
  void update() {
    SessionController sessionController = new SessionController(SessionService.createNull());
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    var sessionName = "test";
    var input = TestData.createSessionInstance(sessionName);
    Types.Session insertedSession = sessionController.create(input, request);
    ProjectService projectService = ProjectService.createNull();
    var project =
        projectService.createProject(TestData.createTestProjectInstance("test-project", false));

    var updatedResponseChunks = 1;
    var updatedInferenceModel = "new-model-name";
    var updatedName = "new-name";
    var updatedRerankModel = "new-rerank-model";
    var updatedProjectId = project.id();

    var updatedSession =
        sessionController.update(
            insertedSession
                .withInferenceModel(updatedInferenceModel)
                .withResponseChunks(updatedResponseChunks)
                .withRerankModel(updatedRerankModel)
                .withName(updatedName)
                .withProjectId(updatedProjectId)
                .withQueryConfiguration(new Types.QueryConfiguration(true, false)),
            request);

    assertThat(updatedSession.id()).isNotNull();
    assertThat(updatedSession.name()).isEqualTo(updatedName);
    assertThat(updatedSession.inferenceModel()).isEqualTo(updatedInferenceModel);
    assertThat(updatedSession.rerankModel()).isEqualTo(updatedRerankModel);
    assertThat(updatedSession.responseChunks()).isEqualTo(updatedResponseChunks);
    assertThat(updatedSession.dataSourceIds()).isEmpty();
    assertThat(updatedSession.projectId()).isEqualTo(updatedProjectId);
    assertThat(updatedSession.timeCreated()).isNotNull();
    assertThat(updatedSession.timeUpdated()).isAfter(insertedSession.timeUpdated());
    assertThat(updatedSession.createdById()).isEqualTo("test-user");
    assertThat(updatedSession.lastInteractionTime()).isNull();
    assertThat(updatedSession.queryConfiguration().enableHyde()).isTrue();
    assertThat(updatedSession.queryConfiguration().enableSummaryFilter()).isFalse();
  }

  @Test
  void noQueryConfiguration_create() {
    SessionController sessionController = new SessionController(SessionService.createNull());
    var request = new MockHttpServletRequest();
    var sessionName = "test";
    Types.CreateSession input =
        TestData.createSessionInstance(sessionName).withQueryConfiguration(null);
    var createdSession = sessionController.create(input, request);
    assertThat(createdSession.queryConfiguration()).isNotNull();
    assertThat(createdSession.queryConfiguration().enableHyde()).isFalse();
  }

  @Test
  void delete() {
    SessionService sessionService = SessionService.createNull();
    SessionController sessionController = new SessionController(sessionService);
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request, "test-user");

    var input = TestData.createSessionInstance("test");
    var createdSession = sessionController.create(input, request);
    sessionController.delete(createdSession.id());
    assertThatThrownBy(() -> sessionService.getSessionById(createdSession.id(), "test-user"))
        .isInstanceOf(NotFound.class);
  }

  @Test
  void getSessions() {
    SessionController sessionController = new SessionController(SessionService.createNull());
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request, "user-one");
    var input = TestData.createSessionInstance("test");
    var input2 = TestData.createSessionInstance("test2");
    sessionController.create(input, request);
    sessionController.create(input2, request);

    var request2 = new MockHttpServletRequest();
    TestData.addUserToRequest(request2, "user-two");
    var input3 = TestData.createSessionInstance("test");
    var otherPersonsSession = sessionController.create(input3, request2);

    var result = sessionController.getSessions(request);

    assertThat(result).hasSizeGreaterThanOrEqualTo(2);
    assertThat(result).doesNotContain(otherPersonsSession);
  }
}
