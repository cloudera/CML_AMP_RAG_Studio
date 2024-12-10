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

package com.cloudera.cai.rag.files;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.files.RagFileUploader.UploadRequest;
import com.cloudera.cai.util.IdGenerator;
import com.cloudera.cai.util.Tracker;
import com.cloudera.cai.util.exceptions.BadRequest;
import com.cloudera.cai.util.exceptions.NotFound;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;

class RagFileServiceTest {

  private final RagDataSourceRepository dataSourceRepository = RagDataSourceRepository.createNull();

  @Test
  void saveRagFile() {
    String originalFilename = "real-filename.pdf";
    String name = "test-file";
    byte[] bytes = "23243223423".getBytes();
    MockMultipartFile mockMultipartFile =
        new MockMultipartFile(name, originalFilename, "text/plain", bytes);
    String documentId = UUID.randomUUID().toString();
    RagFileRepository ragFileRepository = RagFileRepository.createNull();
    Tracker<UploadRequest> requestTracker = new Tracker<>();
    RagFileService ragFileService = createRagFileService(documentId, requestTracker);
    var dataSourceId = newDataSourceId();
    Types.RagDocumentMetadata result =
        ragFileService.saveRagFile(mockMultipartFile, dataSourceId, "test-id");
    Types.RagDocumentMetadata expected =
        new Types.RagDocumentMetadata(originalFilename, documentId, "pdf", 11);
    assertThat(result).isEqualTo(expected);
    Types.RagDocument savedDocument =
        ragFileRepository.findDocumentByDocumentId(result.documentId());
    assertThat(savedDocument).isNotNull();
    assertThat(savedDocument.documentId()).isEqualTo(result.documentId());
    String expectedS3Path = "prefix/" + dataSourceId + "/" + result.documentId();
    assertThat(savedDocument.s3Path()).isEqualTo(expectedS3Path);
    assertThat(savedDocument.extension()).isEqualTo("pdf");
    assertThat(savedDocument.dataSourceId()).isEqualTo(dataSourceId);
    assertThat(requestTracker.getValues())
        .containsExactly(new UploadRequest(mockMultipartFile, expectedS3Path, "real-filename.pdf"));
  }

  @Test
  void deleteRagFile() {
    RagFileRepository ragFileRepository = RagFileRepository.createNull();
    var dataSourceId = TestData.createTestDataSource(RagDataSourceRepository.createNull());
    String documentId = UUID.randomUUID().toString();
    var id = TestData.createTestDocument(dataSourceId, documentId, ragFileRepository);
    RagFileService ragFileService = createRagFileService();
    ragFileService.deleteRagFile(id, dataSourceId);
    assertThat(ragFileService.getRagDocuments(dataSourceId)).extracting("id").doesNotContain(id);
  }

  @Test
  void deleteRagFile_wrongDataSourceId() {
    RagFileRepository ragFileRepository = RagFileRepository.createNull();
    var dataSourceId = TestData.createTestDataSource(RagDataSourceRepository.createNull());
    String documentId = UUID.randomUUID().toString();
    var id = TestData.createTestDocument(dataSourceId, documentId, ragFileRepository);
    RagFileService ragFileService = createRagFileService();
    Long nonExistentDataSourceId = Long.MAX_VALUE;

    assertThatThrownBy(() -> ragFileService.deleteRagFile(id, nonExistentDataSourceId))
        .isInstanceOf(NotFound.class);
  }

  @Test
  void saveRagFile_trailingPeriod() {
    String originalFilename = "real-filename.";
    String name = "test-file";
    byte[] bytes = "23243223423".getBytes();
    MockMultipartFile mockMultipartFile =
        new MockMultipartFile(name, originalFilename, "text/plain", bytes);
    String documentId = UUID.randomUUID().toString();
    RagFileService ragFileService = createRagFileService(documentId, new Tracker<>());
    Types.RagDocumentMetadata result =
        ragFileService.saveRagFile(mockMultipartFile, newDataSourceId(), "test-id");
    Types.RagDocumentMetadata expected =
        new Types.RagDocumentMetadata(originalFilename, documentId, "", 11);
    assertThat(result).isEqualTo(expected);
  }

  @Test
  void saveRagFile_removeDirectories() {
    String originalFilename = "staging/real-filename.pdf";
    String name = "file";
    byte[] bytes = "23243223423".getBytes();
    MockMultipartFile mockMultipartFile =
        new MockMultipartFile(name, originalFilename, "text/plain", bytes);
    String documentId = UUID.randomUUID().toString();
    var dataSourceId = newDataSourceId();
    String expectedS3Path = "prefix/" + dataSourceId + "/" + documentId;
    var requestTracker = new Tracker<UploadRequest>();
    RagFileService ragFileService = createRagFileService(documentId, requestTracker);
    Types.RagDocumentMetadata result =
        ragFileService.saveRagFile(mockMultipartFile, dataSourceId, "test-id");
    Types.RagDocumentMetadata expected =
        new Types.RagDocumentMetadata("real-filename.pdf", documentId, "pdf", 11);
    assertThat(result).isEqualTo(expected);
    assertThat(requestTracker.getValues())
        .containsExactly(new UploadRequest(mockMultipartFile, expectedS3Path, "real-filename.pdf"));
  }

  @Test
  void saveRagFile_noFilename() {
    String name = "file";
    byte[] bytes = "23243223423".getBytes();
    MockMultipartFile mockMultipartFile = new MockMultipartFile(name, null, "text/plain", bytes);
    String documentId = UUID.randomUUID().toString();
    RagFileService ragFileService = createRagFileService(documentId, new Tracker<>());
    assertThatThrownBy(
            () -> ragFileService.saveRagFile(mockMultipartFile, newDataSourceId(), "test-id"))
        .isInstanceOf(BadRequest.class);
  }

  @Test
  void saveRagFile_noDataSource() {
    String name = "file";
    byte[] bytes = "23243223423".getBytes();
    MockMultipartFile mockMultipartFile =
        new MockMultipartFile(name, "filename", "text/plain", bytes);
    String documentId = UUID.randomUUID().toString();
    RagFileService ragFileService = createRagFileService(documentId, new Tracker<>());
    assertThatThrownBy(() -> ragFileService.saveRagFile(mockMultipartFile, -1L, "test-id"))
        .isInstanceOf(NotFound.class);
  }

  @Test
  void getRagDocuments() {
    RagFileService ragFileService = createRagFileService("test-id", new Tracker<>());
    List<Types.RagDocument> ragDocuments = ragFileService.getRagDocuments(newDataSourceId());
    assertThat(ragDocuments).isNotNull();
  }

  private RagFileService createRagFileService() {
    return createRagFileService(null, null);
  }

  private RagFileService createRagFileService(
      String staticDocumentId, Tracker<UploadRequest> tracker) {
    return new RagFileService(
        staticDocumentId == null
            ? IdGenerator.createNull()
            : IdGenerator.createNull(staticDocumentId),
        RagFileRepository.createNull(),
        tracker == null ? RagFileUploader.createNull() : RagFileUploader.createNull(tracker),
        RagFileIndexReconciler.createNull(),
        "prefix",
        dataSourceRepository);
  }

  private long newDataSourceId() {
    return TestData.createTestDataSource(dataSourceRepository);
  }
}
