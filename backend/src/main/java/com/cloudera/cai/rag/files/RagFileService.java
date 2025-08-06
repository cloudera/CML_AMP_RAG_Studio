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

import static java.nio.file.StandardCopyOption.*;

import com.cloudera.cai.rag.Types.RagDocument;
import com.cloudera.cai.rag.Types.RagDocumentMetadata;
import com.cloudera.cai.rag.datasources.RagDataSourceRepository;
import com.cloudera.cai.util.IdGenerator;
import com.cloudera.cai.util.exceptions.BadRequest;
import com.cloudera.cai.util.exceptions.NotFound;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@Component
public class RagFileService {
  private final IdGenerator idGenerator;
  private final RagFileRepository ragFileRepository;
  private final RagFileUploader ragFileUploader;
  private final RagFileIndexReconciler ragFileIndexReconciler;
  private final String s3PathPrefix;
  private final RagDataSourceRepository ragDataSourceRepository;
  private final RagFileDeleteReconciler ragFileDeleteReconciler;
  private final RagFileSummaryReconciler ragFileSummaryReconciler;

  @Autowired
  public RagFileService(
      IdGenerator idGenerator,
      RagFileRepository ragFileRepository,
      RagFileUploader ragFileUploader,
      RagFileIndexReconciler ragFileIndexReconciler,
      @Qualifier("s3BucketPrefix") String s3PathPrefix,
      RagDataSourceRepository ragDataSourceRepository,
      RagFileDeleteReconciler ragFileDeleteReconciler,
      RagFileSummaryReconciler ragFileSummaryReconciler) {
    this.idGenerator = idGenerator;
    this.ragFileRepository = ragFileRepository;
    this.ragFileUploader = ragFileUploader;
    this.ragFileIndexReconciler = ragFileIndexReconciler;
    this.s3PathPrefix = s3PathPrefix;
    this.ragDataSourceRepository = ragDataSourceRepository;
    this.ragFileDeleteReconciler = ragFileDeleteReconciler;
    this.ragFileSummaryReconciler = ragFileSummaryReconciler;
  }

  public List<RagDocumentMetadata> saveRagFile(
      MultipartFile file, Long dataSourceId, String actorCrn) {
    ragDataSourceRepository.getRagDataSourceById(dataSourceId);

    if (isZipFile(file)) {
      List<RagDocumentMetadata> results = processZipFile(file, dataSourceId, actorCrn);
      if (results.isEmpty()) {
        throw new BadRequest("Invalid or empty zip file");
      }
      return results;
    }
    return List.of(processFile(dataSourceId, actorCrn, new MultipartUploadableFile(file)));
  }

  private boolean isZipFile(MultipartFile file) {
    return file.getContentType() != null && file.getContentType().equals("application/zip")
        || (file.getOriginalFilename() != null
            && file.getOriginalFilename().toLowerCase().endsWith(".zip"));
  }

  private List<RagDocumentMetadata> processZipFile(
      MultipartFile file, Long dataSourceId, String actorCrn) {
    List<RagDocumentMetadata> results = new ArrayList<>();
    try (ZipInputStream zipInputStream = new ZipInputStream(file.getInputStream())) {
      ZipEntry entry;
      while ((entry = zipInputStream.getNextEntry()) != null) {
        if (entry.isDirectory()) {
          continue;
        }
        Path tempFile = Files.createTempFile(UUID.randomUUID().toString(), null);
        Files.copy(zipInputStream, tempFile, REPLACE_EXISTING);
        results.add(
            processFile(
                dataSourceId,
                actorCrn,
                new ZipEntryUploadableFile(
                    entry, Files.newInputStream(tempFile), Files.size(tempFile))));
        zipInputStream.closeEntry();
      }
    } catch (IOException e) {
      throw new BadRequest("Failed to process zip file: " + e.getMessage());
    }
    return results;
  }

  private RagDocumentMetadata processFile(
      Long dataSourceId, String actorCrn, UploadableFile uploadableFile) {
    String documentId = idGenerator.generateId();
    var s3Path = buildS3Path(dataSourceId, documentId);

    ragFileUploader.uploadFile(uploadableFile, s3Path);
    var ragDocument =
        createUnsavedDocument(uploadableFile, documentId, s3Path, dataSourceId, actorCrn);
    Long id = ragFileRepository.insertDocumentMetadata(ragDocument);
    log.info("Saved document with id: {}", id);

    ragFileIndexReconciler.submit(ragDocument.withId(id));
    ragFileSummaryReconciler.resync();

    return new RagDocumentMetadata(
        ragDocument.filename(), documentId, ragDocument.extension(), ragDocument.sizeInBytes());
  }

  private String buildS3Path(Long dataSourceId, String documentId) {
    var dataSourceDocumentPart = dataSourceId + "/" + documentId;
    if (s3PathPrefix.isEmpty()) {
      return dataSourceDocumentPart;
    }
    return s3PathPrefix + "/" + dataSourceDocumentPart;
  }

  private String extractFileExtension(String originalFilename) {
    if (originalFilename == null || !originalFilename.contains(".")) {
      return null;
    }
    return originalFilename.substring(originalFilename.lastIndexOf('.') + 1);
  }

  private RagDocument createUnsavedDocument(
      UploadableFile file, String documentId, String s3Path, Long dataSourceId, String actorCrn) {
    return new RagDocument(
        null,
        validateFilename(file.getOriginalFilename()),
        dataSourceId,
        documentId,
        s3Path,
        null,
        file.getSize(),
        extractFileExtension(file.getOriginalFilename()),
        Instant.now(),
        Instant.now(),
        actorCrn,
        actorCrn,
        null,
        null,
        null,
        null,
        null);
  }

  private static String validateFilename(String originalFilename) {
    if (originalFilename == null || originalFilename.isBlank()) {
      throw new BadRequest("Filename is required");
    }
    return originalFilename;
  }

  public void deleteRagFile(Long id, Long dataSourceId) {
    var document = ragFileRepository.getRagDocumentById(id);
    if (!document.dataSourceId().equals(dataSourceId)) {
      throw new NotFound("Document with id " + id + " not found for dataSourceId: " + dataSourceId);
    }
    ragFileRepository.deleteById(id);
    ragFileDeleteReconciler.submit(document);
  }

  public List<RagDocument> getRagDocuments(Long dataSourceId) {
    return ragFileRepository.getRagDocuments(dataSourceId);
  }

  public record MultipartUploadableFile(MultipartFile file) implements UploadableFile {

    @Override
    public InputStream getInputStream() throws IOException {
      return file.getInputStream();
    }

    @Override
    public long getSize() {
      return file.getSize();
    }

    @Override
    public String getOriginalFilename() {
      return file.getOriginalFilename();
    }
  }

  private record ZipEntryUploadableFile(ZipEntry entry, InputStream inputStream, long size)
      implements UploadableFile {

    @Override
    public String getOriginalFilename() {
      return entry.getName();
    }

    @Override
    public InputStream getInputStream() {
      return inputStream;
    }

    @Override
    public long getSize() {
      return size;
    }
  }

  // Nullables stuff down here

  public static RagFileService createNull(String... dummyIds) {
    return new RagFileService(
        IdGenerator.createNull(dummyIds),
        RagFileRepository.createNull(),
        RagFileUploader.createNull(),
        RagFileIndexReconciler.createNull(),
        "prefix",
        RagDataSourceRepository.createNull(),
        RagFileDeleteReconciler.createNull(),
        RagFileSummaryReconciler.createNull());
  }
}
