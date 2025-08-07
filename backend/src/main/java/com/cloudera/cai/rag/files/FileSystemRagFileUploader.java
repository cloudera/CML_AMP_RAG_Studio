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

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.InputStreamResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class FileSystemRagFileUploader implements RagFileUploader {

  private static final String FILE_STORAGE_ROOT = fileStoragePath();

  // For testing
  private static String customStorageRoot = null;

  /**
   * Gets the root path for file storage.
   *
   * @return The file storage root path
   */
  public static String getFileStorageRoot() {
    return customStorageRoot != null ? customStorageRoot : FILE_STORAGE_ROOT;
  }

  /**
   * Sets a custom storage root for testing.
   *
   * @param rootPath The custom root path to use
   */
  public static void setCustomStorageRoot(String rootPath) {
    customStorageRoot = rootPath;
  }

  @Override
  public void uploadFile(UploadableFile file, String s3Path) {
    log.info("Uploading file to FS: {}", s3Path);
    try {
      Path filePath = Path.of(FILE_STORAGE_ROOT, s3Path);
      Files.createDirectories(filePath.getParent());
      Files.copy(file.getInputStream(), filePath);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
  }

  @Override
  public Resource downloadFile(String s3Path) throws IOException {
    log.info("Downloading file from local filesystem: {}", s3Path);
    Path filePath = Path.of(getFileStorageRoot(), s3Path);

    // Check if the file exists
    if (!Files.exists(filePath)) {
      throw new com.cloudera.cai.util.exceptions.NotFound("File not found at path: " + filePath);
    }

    // Create an input stream from the file
    return new InputStreamResource(Files.newInputStream(filePath));
  }

  private static String fileStoragePath() {
    var fileStoragePath = System.getenv("RAG_DATABASES_DIR") + "/file_storage";
    log.info("configured with fileStoragePath = {}", fileStoragePath);
    return fileStoragePath;
  }

  // nullables below here

  /**
   * Creates a test double for FileSystemRagFileUploader.
   *
   * @param tempDir The temporary directory to use for file storage
   * @return A FileSystemRagFileUploader test double
   */
  public static FileSystemRagFileUploader createNull(String tempDir) {
    setCustomStorageRoot(tempDir);
    return new FileSystemRagFileUploader();
  }
}
