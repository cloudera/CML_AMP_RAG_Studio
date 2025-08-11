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
import com.cloudera.cai.util.IdGenerator;
import com.cloudera.cai.util.exceptions.BadRequest;
import com.cloudera.cai.util.exceptions.NotFound;
import java.io.ByteArrayOutputStream;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

class RagFileControllerTest {

  private final RagDataSourceRepository dataSourceRepository = RagDataSourceRepository.createNull();
  private final RagFileRepository ragFileRepository = RagFileRepository.createNull();

  @Test
  void uploadFile() {
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
  void uploadFile_noBytes() {
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
    ragFileController.deleteRagFile(dataSourceId, documentId);
    assertThat(ragFileController.getRagDocuments(dataSourceId)).extracting("id").doesNotContain(id);
  }

  @Test
  void download_success_streamsAttachment() throws Exception {
    var dsRepo = RagDataSourceRepository.createNull();
    var repo = RagFileRepository.createNull();
    long dataSourceId = TestData.createTestDataSource(dsRepo);
    String documentId = UUID.randomUUID().toString();
    String originalFilename = "mydoc.pdf";
    byte[] bytes = "hello world".getBytes();
    String prefix = "prefix";
    String s3Path = prefix + "/" + dataSourceId + "/" + documentId;

    RagFileService ragFileService =
        new RagFileService(
            IdGenerator.createNull(documentId),
            repo,
            RagFileUploader.createNull(),
            RagFileIndexReconciler.createNull(),
            prefix,
            dsRepo,
            RagFileDeleteReconciler.createNull(),
            RagFileSummaryReconciler.createNull(),
            RagFileDownloader.createNull(Map.of(s3Path, bytes)));
    RagFileController controller = new RagFileController(ragFileService);

    // First upload to create metadata with known documentId
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    controller.uploadRagDocument(
        new MockMultipartFile("file", originalFilename, "application/pdf", bytes),
        dataSourceId,
        request);

    // Find the created document id by filename
    String foundDocumentId =
        repo.getRagDocuments(dataSourceId).stream()
            .filter(d -> d.filename().equals(originalFilename))
            .map(RagDocument::documentId)
            .findFirst()
            .orElseThrow();

    ResponseEntity<StreamingResponseBody> response =
        controller.downloadRagDocument(dataSourceId, foundDocumentId);
    assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
    assertThat(response.getHeaders().getFirst(HttpHeaders.CONTENT_DISPOSITION))
        .isEqualTo("attachment; filename=\"" + originalFilename + "\"");
    StreamingResponseBody body = response.getBody();
    assertThat(body).isNotNull();
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    body.writeTo(out);
    assertThat(out.toByteArray()).isEqualTo(bytes);
  }

  @Test
  void download_wrongDataSource_throwsNotFound() {
    var dsRepo = RagDataSourceRepository.createNull();
    var repo = RagFileRepository.createNull();
    long dataSourceId = TestData.createTestDataSource(dsRepo);
    String documentId = UUID.randomUUID().toString();
    String prefix = "prefix";
    String s3Path = prefix + "/" + dataSourceId + "/" + documentId;

    RagFileService ragFileService =
        new RagFileService(
            IdGenerator.createNull(documentId),
            repo,
            RagFileUploader.createNull(),
            RagFileIndexReconciler.createNull(),
            prefix,
            dsRepo,
            RagFileDeleteReconciler.createNull(),
            RagFileSummaryReconciler.createNull(),
            RagFileDownloader.createNull(Map.of(s3Path, "x".getBytes())));
    RagFileController controller = new RagFileController(ragFileService);

    // Create the metadata
    var request = new MockHttpServletRequest();
    TestData.addUserToRequest(request);
    controller.uploadRagDocument(
        new MockMultipartFile("file", "f.txt", "text/plain", new byte[] {1, 2, 3}),
        dataSourceId,
        request);

    String foundDocumentId =
        repo.getRagDocuments(dataSourceId).stream()
            .filter(d -> d.filename().equals("f.txt"))
            .map(RagDocument::documentId)
            .findFirst()
            .orElseThrow();

    assertThatThrownBy(() -> controller.downloadRagDocument(Long.MAX_VALUE, foundDocumentId))
        .isInstanceOf(NotFound.class);
  }
}
