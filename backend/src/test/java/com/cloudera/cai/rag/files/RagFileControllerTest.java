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

package com.cloudera.cai.rag.files;

import static com.cloudera.cai.rag.TestData.createTestDataSource;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.awaitility.Awaitility.await;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.Types.RagDocument;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.util.exceptions.BadRequest;
import java.util.List;
import java.util.Random;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockMultipartFile;

class RagFileControllerTest {

  private final RagDataSourceRepository dataSourceRepository = RagDataSourceRepository.createNull();
  private final RagFileRepository ragFileRepository = RagFileRepository.createNull();

  @Test
  void uploadFile() throws Exception {
    RagFileController ragFileController = new RagFileController(RagFileService.createNull());
    String fileName = "real-filename";
    String contentType = "text/plain";
    byte[] bytes = "23243223423".getBytes();
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    Types.RagDocumentMetadata metadata =
        ragFileController
            .uploadRagDocument(
                new MockMultipartFile("test-file", fileName, contentType, bytes),
                createTestDataSource(dataSourceRepository),
                request)
            .getFirst();
    assertThat(metadata).isNotNull();
    assertThat(metadata.fileName()).isEqualTo(fileName);
    assertThat(metadata.extension()).isEqualTo(null);
    assertThat(metadata.sizeInBytes()).isEqualTo(bytes.length);

    var uploadedDocument = ragFileRepository.findDocumentByDocumentId(metadata.documentId());
    assertThat(uploadedDocument.createdById())
        .isEqualTo(uploadedDocument.updatedById())
        .isEqualTo("test-user");
  }

  @Test
  void uploadFile_noBytes() throws Exception {
    RagFileController ragFileController = new RagFileController(RagFileService.createNull());
    String fileName = "file";
    String contentType = "text/plain";
    byte[] bytes = "".getBytes();
    var request = new MockHttpServletRequest();
    assertThatThrownBy(
            () ->
                ragFileController.uploadRagDocument(
                    new MockMultipartFile("test-file", fileName, contentType, bytes), 1L, request))
        .isInstanceOf(BadRequest.class);
  }

  @Test
  void getRagDocuments() {
    long dataSourceId =
        dataSourceRepository.createRagDataSource(
            new Types.RagDataSource(
                null,
                "test_datasource",
                "test_embedding_model",
                "summarizationModel",
                1024,
                20,
                null,
                null,
                "test-id",
                "test-id",
                Types.ConnectionType.API,
                null,
                null,
                true,
                null));

    RagFileController ragFileController = new RagFileController(RagFileService.createNull());
    String fileName = "test-get-rag-docs-" + new Random().nextLong();
    String contentType = "text/plain";
    byte[] bytes = "23243223423".getBytes();
    Types.RagDocumentMetadata uploadResult =
        ragFileController
            .uploadRagDocument(
                new MockMultipartFile("file", fileName, contentType, bytes),
                dataSourceId,
                new MockHttpServletRequest())
            .getFirst();
    assertThat(uploadResult.fileName()).isEqualTo(fileName);
    await()
        .untilAsserted(
            () -> {
              List<RagDocument> ragDocuments =
                  ragFileController.getRagDocuments(dataSourceId).stream()
                      .filter(ragDocument -> ragDocument.filename().equals(fileName))
                      .toList();
              assertThat(ragDocuments).isNotEmpty().hasSize(1);
            });
  }

  @Test
  void getRagDocument_badId() {
    long dataSourceId = -1L;
    RagFileController ragFileController = new RagFileController(RagFileService.createNull());
    List<RagDocument> ragDocuments =
        ragFileController.getRagDocuments(dataSourceId).stream().toList();
    assertThat(ragDocuments).isEmpty();
  }

  @Test
  void delete() {
    RagFileRepository ragFileRepository = RagFileRepository.createNull();
    var dataSourceId = TestData.createTestDataSource(RagDataSourceRepository.createNull());
    String documentId = UUID.randomUUID().toString();
    var id = TestData.createTestDocument(dataSourceId, documentId, ragFileRepository);

    RagFileController ragFileController = new RagFileController(RagFileService.createNull());
    ragFileController.deleteRagFile(id, dataSourceId);
    assertThat(ragFileController.getRagDocuments(dataSourceId)).extracting("id").doesNotContain(id);
  }

  @Test
  void downloadFile() throws Exception {
    // Create a test document
    var dataSourceId = createTestDataSource(dataSourceRepository);
    String documentId = UUID.randomUUID().toString();
    var id = TestData.createTestDocument(dataSourceId, documentId, ragFileRepository);

    // Create the controller with our service
    RagFileController controller = new RagFileController(RagFileService.createNull());

    // Call the download endpoint - this should not throw an exception
    var response = controller.downloadRagFile(id, dataSourceId);

    // Basic verification - just make sure we get a response
    assertThat(response).isNotNull();
    assertThat(response.getStatusCodeValue()).isEqualTo(200);
  }

  @Test
  void downloadFile_unknownExtension() throws Exception {
    // Create a test document
    var dataSourceId = createTestDataSource(dataSourceRepository);
    var documentId = UUID.randomUUID().toString();

    // Setup the mock service with a test document
    RagFileService mockService = RagFileService.createNull();
    var docId = TestData.createTestDocument(dataSourceId, documentId, ragFileRepository);

    // Create the controller with the mock service
    RagFileController controller = new RagFileController(mockService);

    // Call the download endpoint
    var response = controller.downloadRagFile(docId, dataSourceId);

    // Verify the response uses default content type for unknown extensions
    assertThat(response.getHeaders().getContentType().toString())
        .isEqualTo("application/octet-stream");
  }
}
