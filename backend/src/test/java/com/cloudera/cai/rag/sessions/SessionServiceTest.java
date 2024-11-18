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
}
