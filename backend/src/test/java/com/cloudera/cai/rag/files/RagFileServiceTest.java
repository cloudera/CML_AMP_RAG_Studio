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

package com.cloudera.cai.rag.files;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.cloudera.cai.rag.TestData;
import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.Types.RagDocumentMetadata;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.rag.files.RagFileService.MultipartUploadableFile;
import com.cloudera.cai.rag.files.RagFileUploader.UploadRequest;
import com.cloudera.cai.util.IdGenerator;
import com.cloudera.cai.util.Tracker;
import com.cloudera.cai.util.exceptions.BadRequest;
import com.cloudera.cai.util.exceptions.NotFound;
import java.io.ByteArrayOutputStream;
import java.util.List;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;

class RagFileServiceTest {

  private final RagDataSourceRepository dataSourceRepository = RagDataSourceRepository.createNull();
  private final RagFileRepository ragFileRepository = RagFileRepository.createNull();

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
        ragFileService.saveRagFile(mockMultipartFile, dataSourceId, "test-id").getFirst();
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
        .containsExactly(
            new UploadRequest(new MultipartUploadableFile(mockMultipartFile), expectedS3Path));
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
        ragFileService.saveRagFile(mockMultipartFile, newDataSourceId(), "test-id").getFirst();
    Types.RagDocumentMetadata expected =
        new Types.RagDocumentMetadata(originalFilename, documentId, "", 11);
    assertThat(result).isEqualTo(expected);
  }

  @Test
  void saveRagFile_noS3Prefix() {
    String originalFilename = "real-filename.";
    String name = "test-file";
    byte[] bytes = "23243223423".getBytes();
    MockMultipartFile mockMultipartFile =
        new MockMultipartFile(name, originalFilename, "text/plain", bytes);
    String documentId = UUID.randomUUID().toString();
    RagFileService ragFileService = createRagFileService(documentId, new Tracker<>(), "");
    var dataSourceId = newDataSourceId();
    Types.RagDocumentMetadata result =
        ragFileService.saveRagFile(mockMultipartFile, dataSourceId, "test-id").getFirst();
    var savedDocumentMetadata = ragFileRepository.findDocumentByDocumentId(result.documentId());
    assertThat(savedDocumentMetadata.s3Path()).isEqualTo(dataSourceId + "/" + documentId);
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
        ragFileService.saveRagFile(mockMultipartFile, dataSourceId, "test-id").getFirst();
    Types.RagDocumentMetadata expected =
        new Types.RagDocumentMetadata("staging/real-filename.pdf", documentId, "pdf", 11);
    assertThat(result).isEqualTo(expected);
    assertThat(requestTracker.getValues())
        .containsExactly(
            new UploadRequest(new MultipartUploadableFile(mockMultipartFile), expectedS3Path));
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
    return createRagFileService(staticDocumentId, tracker, "prefix");
  }

  private RagFileService createRagFileService(
      String staticDocumentId, Tracker<UploadRequest> tracker, String prefix) {
    return new RagFileService(
        staticDocumentId == null
            ? IdGenerator.createNull()
            : IdGenerator.createNull(staticDocumentId),
        RagFileRepository.createNull(),
        tracker == null ? RagFileUploader.createNull() : RagFileUploader.createNull(tracker),
        RagFileIndexReconciler.createNull(),
        prefix,
        dataSourceRepository,
        RagFileDeleteReconciler.createNull(),
        RagFileSummaryReconciler.createNull(),
        RagFileDownloader.createNull());
  }

  private long newDataSourceId() {
    return TestData.createTestDataSource(dataSourceRepository);
  }

  @Test
  void saveRagFile_processZipFile() throws Exception {
    var service = createRagFileService();
    var dataSourceId = newDataSourceId();
    var actorCrn = "fake-user";

    String[][] fileEntries = {
      {"doc1.txt", "content1"},
      {"doc2.txt", "content2"},
      {"subfolder/doc3.txt", "content3"}
    };
    var zipFile = createZipFile(fileEntries, "application/zip");

    var results = service.saveRagFile(zipFile, dataSourceId, actorCrn);
    assertThat(results).hasSize(3);
    assertThat(results.stream().map(RagDocumentMetadata::fileName))
        .containsExactlyInAnyOrder("doc1.txt", "doc2.txt", "subfolder/doc3.txt");
  }

  @Test
  void saveRagFile_processZipFile_noContentType() throws Exception {
    var service = createRagFileService();
    var dataSourceId = newDataSourceId();
    var actorCrn = "fake-user";

    String[][] fileEntries = {
      {"doc1.txt", "content1"},
      {"doc2.txt", "content2"},
      {"subfolder/doc3.txt", "content3"}
    };
    var zipFile = createZipFile(fileEntries, null);

    var results = service.saveRagFile(zipFile, dataSourceId, actorCrn);
    assertThat(results).hasSize(3);
    assertThat(results.stream().map(RagDocumentMetadata::fileName))
        .containsExactlyInAnyOrder("doc1.txt", "doc2.txt", "subfolder/doc3.txt");
  }

  @Test
  void saveRagFile_emptyZipFile() throws Exception {
    var service = createRagFileService();
    var dataSourceId = newDataSourceId();
    var actorCrn = "fake-user";

    String[][] fileEntries = {};
    var zipFile = createZipFile(fileEntries, "application/zip");

    assertThatThrownBy(() -> service.saveRagFile(zipFile, dataSourceId, actorCrn))
        .isInstanceOf(BadRequest.class)
        .hasMessageContaining("Invalid or empty zip file");
  }

  @Test
  void saveRagFile_invalidZipContent() {
    var service = createRagFileService();
    var dataSourceId = newDataSourceId();
    var actorCrn = "fake-user";

    var invalidZipFile =
        new MockMultipartFile(
            "test.zip", "test.zip", "application/zip", "invalid zip content".getBytes());

    assertThatThrownBy(() -> service.saveRagFile(invalidZipFile, dataSourceId, actorCrn))
        .isInstanceOf(BadRequest.class)
        .hasMessageContaining("Invalid or empty zip file");
  }

  private MockMultipartFile createZipFile(String[][] fileEntries, String contentType)
      throws Exception {
    ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
    try (ZipOutputStream zipStream = new ZipOutputStream(outputStream)) {
      for (String[] entry : fileEntries) {
        ZipEntry zipEntry = new ZipEntry(entry[0]);
        zipStream.putNextEntry(zipEntry);
        zipStream.write(entry[1].getBytes());
        zipStream.closeEntry();
      }
    }
    return new MockMultipartFile("test.zip", "test.zip", contentType, outputStream.toByteArray());
  }

  @Test
  void downloadDocumentById_success() throws Exception {
    var repo = RagFileRepository.createNull();
    var dsRepo = RagDataSourceRepository.createNull();
    long dataSourceId = TestData.createTestDataSource(dsRepo);
    String documentId = UUID.randomUUID().toString();
    Long id = TestData.createTestDocument(dataSourceId, documentId, repo);

    byte[] content = "hello by id".getBytes();
    RagFileService service =
        new RagFileService(
            IdGenerator.createNull(),
            repo,
            RagFileUploader.createNull(),
            RagFileIndexReconciler.createNull(),
            "prefix",
            dsRepo,
            RagFileDeleteReconciler.createNull(),
            RagFileSummaryReconciler.createNull(),
            RagFileDownloader.createNull(java.util.Map.of("doesn't matter", content)));

    var downloaded = service.downloadDocument(dataSourceId, id);
    assertThat(downloaded.filename()).isNotNull();
    try (var in = downloaded.stream()) {
      byte[] read = in.readAllBytes();
      assertThat(read).isNotEmpty();
    }
  }

  @Test
  void downloadDocumentById_wrongDataSourceId() {
    var repo = RagFileRepository.createNull();
    var dsRepo = RagDataSourceRepository.createNull();
    long dataSourceId = TestData.createTestDataSource(dsRepo);
    String documentId = UUID.randomUUID().toString();
    Long id = TestData.createTestDocument(dataSourceId, documentId, repo);

    RagFileService service =
        new RagFileService(
            IdGenerator.createNull(),
            repo,
            RagFileUploader.createNull(),
            RagFileIndexReconciler.createNull(),
            "prefix",
            dsRepo,
            RagFileDeleteReconciler.createNull(),
            RagFileSummaryReconciler.createNull(),
            RagFileDownloader.createNull());

    assertThatThrownBy(() -> service.downloadDocument(Long.MAX_VALUE, id))
        .isInstanceOf(NotFound.class);
  }

  @Test
  void downloadDocumentById_notFound() {
    var repo = RagFileRepository.createNull();
    var dsRepo = RagDataSourceRepository.createNull();
    long dataSourceId = TestData.createTestDataSource(dsRepo);

    RagFileService service =
        new RagFileService(
            IdGenerator.createNull(),
            repo,
            RagFileUploader.createNull(),
            RagFileIndexReconciler.createNull(),
            "prefix",
            dsRepo,
            RagFileDeleteReconciler.createNull(),
            RagFileSummaryReconciler.createNull(),
            RagFileDownloader.createNull());

    // Using a negative id to ensure it's not present
    assertThatThrownBy(() -> service.downloadDocument(dataSourceId, -9999L))
        .isInstanceOf(NotFound.class);
  }
}
