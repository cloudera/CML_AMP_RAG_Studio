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
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.util.exceptions.NotFound;
import org.junit.jupiter.api.Test;

import java.util.UUID;

class SessionRepositoryTest {
  @Test
  void create() {
    SessionRepository sessionRepository = new SessionRepository(JdbiConfiguration.createNull());
    var input =
        TestData.createTestSessionInstance("test")
            .withCreatedById("abc")
            .withUpdatedById("abc")
            .withProjectId(2L);
    var id = sessionRepository.create(input);
    assertThat(id).isNotNull();

    var result = sessionRepository.getSessionById(id);

    assertThat(result.id()).isNotNull();
    assertThat(result.name()).isEqualTo(input.name());
    assertThat(result.dataSourceIds()).containsExactlyInAnyOrder(1L, 2L, 3L);
    assertThat(result.timeCreated()).isNotNull();
    assertThat(result.timeUpdated()).isNotNull();
    assertThat(result.createdById()).isEqualTo("abc");
    assertThat(result.updatedById()).isEqualTo("abc");
    assertThat(result.projectId()).isEqualTo(2L);
    assertThat(result.lastInteractionTime()).isNull();
  }

  @Test
  void getSessions() {
    SessionRepository sessionRepository = new SessionRepository(JdbiConfiguration.createNull());
    String username1 = UUID.randomUUID().toString();
    String username2 = UUID.randomUUID().toString();
    String username3 = UUID.randomUUID().toString();
    var input =
        TestData.createTestSessionInstance("test").withCreatedById(username1).withUpdatedById(username1);
    var input2 =
        TestData.createTestSessionInstance("test2").withCreatedById(username2).withUpdatedById(username2);
    var id = sessionRepository.create(input);
    var id2 = sessionRepository.create(input2);

    assertThat(sessionRepository.getSessions(username3)).hasSize(0);
    assertThat(sessionRepository.getSessions(username2)).hasSize(1).extracting("id").containsExactly(id2, id);
    assertThat(result).hasSize(0).extracting("id").containsSequence(id2, id);
  }

  @Test
  void delete() {
    SessionRepository sessionRepository = new SessionRepository(JdbiConfiguration.createNull());
    var id =
        sessionRepository.create(
            TestData.createTestSessionInstance("test")
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    assertThat(sessionRepository.getSessionById(id)).isNotNull();

    sessionRepository.delete(id);
    assertThatThrownBy(() -> sessionRepository.getSessionById(id)).isInstanceOf(NotFound.class);
  }
}
