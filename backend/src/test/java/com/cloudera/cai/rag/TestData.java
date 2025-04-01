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

package com.cloudera.cai.rag;

import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.files.RagFileRepository;
import java.time.Instant;
import java.util.List;
import org.springframework.mock.web.MockHttpServletRequest;

public class TestData {
  public static final String TEST_USER_NAME = "fake-user";

  public static Types.Project createTestProjectInstance(String name, Boolean defaultProject) {
    return Types.Project.builder()
        .id(null)
        .name(name)
        .defaultProject(defaultProject)
        .timeCreated(null)
        .timeUpdated(null)
        .createdById(TEST_USER_NAME)
        .updatedById(TEST_USER_NAME)
        .build();
  }

  public static Types.CreateProject createProjectRequest(String name) {
    return new Types.CreateProject(name);
  }

  public static Types.Session createTestSessionInstance(String sessionName) {
    return createTestSessionInstance(sessionName, List.of());
  }

  public static Types.Session createTestSessionInstance(
      String sessionName, List<Long> dataSourceIds) {
    return new Types.Session(
        null,
        sessionName,
        dataSourceIds,
        1L,
        null,
        null,
        TEST_USER_NAME,
        TEST_USER_NAME,
        null,
        "test-model",
        "test-rerank-model",
        3,
        new Types.QueryConfiguration(false, true));
  }

  public static Types.CreateSession createSessionInstance(String sessionName) {
    return createSessionInstance(sessionName, List.of(), 1L);
  }

  public static Types.CreateSession createSessionInstance(
      String sessionName, List<Long> dataSourceIds, Long projectId) {
    return new Types.CreateSession(
        sessionName,
        dataSourceIds,
        "test-model",
        "test-rerank-model",
        3,
        new Types.QueryConfiguration(false, true),
        projectId);
  }

  public static Types.RagDataSource createTestDataSourceInstance(
      String name,
      Integer chunkSize,
      Integer chunkOverlapPercent,
      Types.ConnectionType connectionType) {
    return new Types.RagDataSource(
        null,
        name,
        "test_embedding_model",
        "summarizationModel",
        chunkSize,
        chunkOverlapPercent,
        null,
        null,
        null,
        null,
        connectionType,
        null,
        null,
        true);
  }

  public static long createTestDataSource(RagDataSourceRepository dataSourceRepository) {
    return dataSourceRepository.createRagDataSource(
        TestData.createTestDataSourceInstance("test", 3, 0, Types.ConnectionType.API)
            .withCreatedById("test")
            .withUpdatedById("test"));
  }

  public static Long createTestDocument(
      long dataSourceId, String documentId, RagFileRepository ragFileRepository) {
    Types.RagDocument ragDocument =
        Types.RagDocument.builder()
            .dataSourceId(dataSourceId)
            .documentId(documentId)
            .filename("doesn't matter")
            .s3Path("doesn't matter")
            .timeCreated(Instant.now())
            .timeUpdated(Instant.now())
            .createdById("doesn't matter")
            .updatedById("doesn't matter")
            .build();
    return ragFileRepository.insertDocumentMetadata(ragDocument);
  }

  public static void addUserToRequest(MockHttpServletRequest request) {
    addUserToRequest(request, "test-user");
  }

  public static void addUserToRequest(MockHttpServletRequest request, String username) {
    request.addHeader("remote-user", username);
  }
}
