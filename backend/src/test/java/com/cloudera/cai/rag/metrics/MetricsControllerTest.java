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

package com.cloudera.cai.rag.metrics;

import static org.assertj.core.api.Assertions.assertThat;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.files.RagFileRepository;
import com.cloudera.cai.rag.sessions.SessionService;
import org.junit.jupiter.api.Test;

class MetricsControllerTest {
  @Test
  void metrics() {
    var metricsController = new MetricsController(MetricsService.createNull());
    var beginningMetrics = metricsController.getMetrics();

    var seshService = SessionService.createNull();
    seshService.create(TestData.createSessionInstance("test-session-1"), "test");
    seshService.create(TestData.createSessionInstance("test-session-2"), "test");
    seshService.create(TestData.createSessionInstance("test-session-3"), "test");
    seshService.create(TestData.createSessionInstance("test-session-4"), "test");
    seshService.create(TestData.createSessionInstance("test-session-5"), "test");

    var dataSourceRepo = RagDataSourceRepository.createNull();
    var id1 = TestData.createTestDataSource(dataSourceRepo);
    var id2 = TestData.createTestDataSource(dataSourceRepo);
    var id3 = TestData.createTestDataSource(dataSourceRepo);

    var id4 = TestData.createTestDataSource(dataSourceRepo);
    dataSourceRepo.deleteDataSource(id4);

    RagFileRepository ragFileRepo = RagFileRepository.createNull();
    TestData.createTestDocument(id1, "doc-1", ragFileRepo);
    TestData.createTestDocument(id2, "doc-2", ragFileRepo);
    TestData.createTestDocument(id3, "doc-3", ragFileRepo);
    TestData.createTestDocument(id3, "doc-4", ragFileRepo);

    Types.MetadataMetrics metrics = metricsController.getMetrics();

    assertThat(metrics.numberOfSessions()).isEqualTo(5 + beginningMetrics.numberOfSessions());
    assertThat(metrics.numberOfDataSources()).isEqualTo(3 + beginningMetrics.numberOfDataSources());
    assertThat(metrics.numberOfDocuments()).isEqualTo(4 + beginningMetrics.numberOfDocuments());
  }
}
