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

package com.cloudera.cai.rag.datasources;

import static com.cloudera.cai.rag.Types.*;
import static com.cloudera.cai.rag.Types.ConnectionType.MANUAL;
import static org.assertj.core.api.Assertions.*;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.util.exceptions.NotFound;
import java.util.List;
import org.junit.jupiter.api.Test;

class RagDataSourceServiceTest {
  @Test
  void getNifiS3Config() {
    RagDataSourceService ragDataSourceService =
        new RagDataSourceService(RagDataSourceRepository.createNull());
    var dataSourceId = 6666666L;
    var url = "https://testing.dev/xyz";
    var configType = DataFlowConfigType.S3;
    String nifiConfig = ragDataSourceService.getNifiConfig(dataSourceId, url, configType);
    assertThat(nifiConfig).contains("\"value\": \"" + dataSourceId + "\"");
    assertThat(nifiConfig).contains("\"value\": \"" + url + "\"");
  }

  @Test
  void getNifiAzureBlobConfig() {
    RagDataSourceService ragDataSourceService =
        new RagDataSourceService(RagDataSourceRepository.createNull());
    var dataSourceId = 6666666L;
    var url = "https://testing.dev/xyz";
    var configType = DataFlowConfigType.AZURE_BLOB;
    String nifiConfig = ragDataSourceService.getNifiConfig(dataSourceId, url, configType);
    assertThat(nifiConfig).contains("\"value\": \"" + dataSourceId + "\"");
    assertThat(nifiConfig).contains("\"value\": \"" + url + "\"");
  }

  @Test
  void getNifiConfigOptions() {
    RagDataSourceService ragDataSourceService =
        new RagDataSourceService(RagDataSourceRepository.createNull());
    List<NifiConfigOptions> nifiConfig = ragDataSourceService.getNifiConfigOptions();
    assertThat(nifiConfig).size().isEqualTo(2);
  }

  @Test
  void createDataSource() {
    RagDataSourceService ragDataSourceService =
        new RagDataSourceService(RagDataSourceRepository.createNull());
    var ragDataSource =
        ragDataSourceService.createRagDataSource(
            TestData.createTestDataSourceInstance("test-name", null, null, ConnectionType.MANUAL)
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    assertThat(ragDataSource).isNotNull();
    assertThat(ragDataSource.name()).isEqualTo("test-name");
    assertThat(ragDataSource.createdById()).isEqualTo("abc");
    assertThat(ragDataSource.updatedById()).isEqualTo("abc");
    assertThat(ragDataSource.chunkOverlapPercent()).isEqualTo(10);
    assertThat(ragDataSource.chunkSize()).isEqualTo(512);
  }

  @Test
  void updateDataSourceName() {
    RagDataSourceService ragDataSourceService =
        new RagDataSourceService(RagDataSourceRepository.createNull());
    var ragDataSource =
        ragDataSourceService.createRagDataSource(
            TestData.createTestDataSourceInstance("test-name", 512, 10, ConnectionType.MANUAL)
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    assertThat(ragDataSource.name()).isEqualTo("test-name");
    assertThat(ragDataSource.updatedById()).isEqualTo("abc");

    var expectedRagDataSource =
        TestData.createTestDataSourceInstance("new-name", 512, 10, MANUAL)
            .withCreatedById("abc")
            .withUpdatedById("def")
            .withId(ragDataSource.id());
    ragDataSourceService.updateRagDataSource(expectedRagDataSource);

    var updatedRagDataSource = ragDataSourceService.getRagDataSourceById(ragDataSource.id());
    assertThat(updatedRagDataSource.name()).isEqualTo("new-name");
    assertThat(updatedRagDataSource.updatedById()).isEqualTo("def");
  }

  @Test
  void deleteDataSource() {
    RagDataSourceService ragDataSourceService =
        new RagDataSourceService(RagDataSourceRepository.createNull());
    var ragDataSource =
        ragDataSourceService.createRagDataSource(
            TestData.createTestDataSourceInstance("test-name", 512, 10, ConnectionType.MANUAL)
                .withCreatedById("abc")
                .withUpdatedById("abc"));
    assertThat(ragDataSource).isNotNull();
    ragDataSourceService.deleteDataSource(ragDataSource.id());
    assertThatThrownBy(() -> ragDataSourceService.getRagDataSourceById(ragDataSource.id()))
        .isInstanceOf(NotFound.class);
  }
}
