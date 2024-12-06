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

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.Types.RagDataSource;
import com.cloudera.cai.rag.util.UserTokenCookieDecoderTest;
import com.cloudera.cai.util.exceptions.BadRequest;
import com.cloudera.cai.util.exceptions.NotFound;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockCookie;
import org.springframework.mock.web.MockHttpServletRequest;

class RagDataSourceControllerTest {

  @Test
  void create() throws Exception {
    RagDataSourceController controller =
        new RagDataSourceController(RagDataSourceService.createNull());
    RagDataSource dataSource =
        TestData.createTestDataSourceInstance("test-name", 512, 10, Types.ConnectionType.MANUAL)
            .withEmbeddingModel("test_embedding_model");
    var request = new MockHttpServletRequest();
    request.setCookies(
        new MockCookie("_basusertoken", UserTokenCookieDecoderTest.encodeCookie("test-user")));
    var res = controller.create(dataSource, request);
    assertThat(res.id()).isNotNull();
    assertThat(res.name()).isEqualTo(dataSource.name());
    assertThat(res.embeddingModel()).isEqualTo("test_embedding_model");
    assertThat(res.timeCreated()).isNotNull();
    assertThat(res.timeUpdated()).isNotNull();
    assertThat(res.createdById()).isEqualTo("test-user");
    assertThat(res.updatedById()).isEqualTo("test-user");
    assertThat(res.connectionType()).isEqualTo(Types.ConnectionType.MANUAL);
  }

  @Test
  void updateName() {
    RagDataSourceController controller =
        new RagDataSourceController(RagDataSourceService.createNull());

    // Create a new RagDataSource
    RagDataSource dataSource =
        TestData.createTestDataSourceInstance(
            "original-name", 1024, 20, Types.ConnectionType.MANUAL);
    var newDataSource = controller.create(dataSource, new MockHttpServletRequest());

    // Update the name of the created RagDataSource
    RagDataSource expectedDataSource =
        new RagDataSource(
            newDataSource.id(),
            "updated-name",
            "test_embedding_model",
            newDataSource.chunkSize(),
            newDataSource.chunkOverlapPercent(),
            newDataSource.timeCreated(),
            newDataSource.timeUpdated(),
            newDataSource.createdById(),
            newDataSource.updatedById(),
            newDataSource.connectionType(),
            0,
            null);
    controller.update(expectedDataSource, new MockHttpServletRequest());

    // Retrieve the updated RagDataSource and verify the name change
    RagDataSource result = controller.getRagDataSourceById(newDataSource.id());
    assertThat(result.name()).isEqualTo("updated-name");
  }

  @Test
  void create_nonDefaultConnectionType() {
    RagDataSourceController controller =
        new RagDataSourceController(RagDataSourceService.createNull());
    RagDataSource dataSource =
        TestData.createTestDataSourceInstance("test-name", 512, 10, Types.ConnectionType.CDF);
    var request = new MockHttpServletRequest();
    var res = controller.create(dataSource, request);
    assertThat(res.connectionType()).isEqualTo(Types.ConnectionType.CDF);
  }

  @Test
  void getRagDataSources() {
    RagDataSourceController controller =
        new RagDataSourceController(RagDataSourceService.createNull());
    RagDataSource dataSource =
        TestData.createTestDataSourceInstance("test-name", 1024, 20, Types.ConnectionType.MANUAL);
    var newDataSource = controller.create(dataSource, new MockHttpServletRequest());

    List<RagDataSource> results = controller.getRagDataSources();
    assertThat(results)
        .filteredOn(ragDataSource -> ragDataSource.id().equals(newDataSource.id()))
        .contains(newDataSource)
        .first()
        .matches(ragDataSource -> ragDataSource.chunkOverlapPercent() == 20);
  }

  @Test
  void getRagDataSourceById() {
    RagDataSourceController controller =
        new RagDataSourceController(RagDataSourceService.createNull());
    RagDataSource dataSource =
        TestData.createTestDataSourceInstance("test-name", 1024, 20, Types.ConnectionType.MANUAL);
    var newDataSource = controller.create(dataSource, new MockHttpServletRequest());

    RagDataSource result = controller.getRagDataSourceById(newDataSource.id());
    assertThat(result).isEqualTo(newDataSource);
  }

  @Test
  void delete() {
    RagDataSourceController controller =
        new RagDataSourceController(RagDataSourceService.createNull());
    RagDataSource dataSource =
        TestData.createTestDataSourceInstance("test-name", 1024, 20, Types.ConnectionType.MANUAL);
    var newDataSource = controller.create(dataSource, new MockHttpServletRequest());
    controller.deleteDataSource(newDataSource.id());
    assertThatThrownBy(() -> controller.getRagDataSourceById(newDataSource.id()))
        .isInstanceOf(NotFound.class);
  }

  @Test
  void getRagDataSourceById_notFound() {
    RagDataSourceController controller =
        new RagDataSourceController(RagDataSourceService.createNull());
    assertThatThrownBy(() -> controller.getRagDataSourceById(8765432312L))
        .isInstanceOf(NotFound.class);
  }

  @Test
  void emptyChunkSizeNotAllowed() {
    RagDataSourceController controller =
        new RagDataSourceController(RagDataSourceService.createNull());
    RagDataSource dataSource =
        TestData.createTestDataSourceInstance("test-name", null, 20, Types.ConnectionType.MANUAL);
    assertThatThrownBy(() -> controller.create(dataSource, new MockHttpServletRequest()))
        .isInstanceOf(BadRequest.class);
  }
}
