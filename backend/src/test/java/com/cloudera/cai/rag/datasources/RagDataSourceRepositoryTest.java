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

package com.cloudera.cai.rag.datasources;

import static com.cloudera.cai.rag.Types.ConnectionType.API;
import static com.cloudera.cai.rag.Types.ConnectionType.MANUAL;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.awaitility.Awaitility.await;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.configuration.JdbiConfiguration;
import com.cloudera.cai.util.exceptions.NotFound;
import java.time.Duration;
import java.time.Instant;
import org.junit.jupiter.api.Test;

class RagDataSourceRepositoryTest {
  @Test
  void create() {
    RagDataSourceRepository repository =
        new RagDataSourceRepository(JdbiConfiguration.createNull());
    var id =
        repository.createRagDataSource(
            TestData.createTestDataSourceInstance("test-name", 512, 10, MANUAL)
                .withCreatedById("abc")
                .withUpdatedById("abc")
                .withEmbeddingModel("test-embedding-model"));
    var savedDataSource = repository.getRagDataSourceById(id);
    assertThat(savedDataSource.name()).isEqualTo("test-name");
    assertThat(savedDataSource.updatedById()).isEqualTo("abc");
    assertThat(savedDataSource.embeddingModel()).isEqualTo("test-embedding-model");
  }

  @Test
  void update() {
    RagDataSourceRepository repository =
        new RagDataSourceRepository(JdbiConfiguration.createNull());
    var id =
        repository.createRagDataSource(
            TestData.createTestDataSourceInstance("test-name", 512, 10, MANUAL)
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    var insertedDataSource = repository.getRagDataSourceById(id);
    assertThat(insertedDataSource.name()).isEqualTo("test-name");
    assertThat(insertedDataSource.updatedById()).isEqualTo("abc");
    var timeInserted = insertedDataSource.timeUpdated();
    assertThat(timeInserted).isNotNull();

    var expectedRagDataSource =
        TestData.createTestDataSourceInstance("new-name", 512, 10, API)
            .withCreatedById("abc")
            .withUpdatedById("def")
            .withId(id)
            .withDocumentCount(0);
    // wait a moment so the updated time will always be later than insert time
    await().atLeast(Duration.ofMillis(1));
    repository.updateRagDataSource(expectedRagDataSource);
    var updatedDataSource = repository.getRagDataSourceById(id);
    assertThat(updatedDataSource)
        .usingRecursiveComparison()
        .ignoringFieldsOfTypes(Instant.class)
        .isEqualTo(expectedRagDataSource);
    assertThat(updatedDataSource.timeUpdated()).isAfter(timeInserted);
  }

  @Test
  void delete() {
    RagDataSourceRepository repository =
        new RagDataSourceRepository(JdbiConfiguration.createNull());
    var id =
        repository.createRagDataSource(
            TestData.createTestDataSourceInstance("test-name", 512, 10, MANUAL)
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    assertThat(repository.getRagDataSourceById(id)).isNotNull();

    repository.deleteDataSource(id);
    assertThatThrownBy(() -> repository.getRagDataSourceById(id)).isInstanceOf(NotFound.class);
  }
}
