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

import com.cloudera.cai.util.s3.AmazonS3Client;
import com.cloudera.cai.util.s3.RefCountedS3Client;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.io.InputStreamResource;
import org.springframework.core.io.Resource;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.core.sync.ResponseTransformer;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

@Slf4j
public class S3RagFileUploader implements RagFileUploader {
  private final AmazonS3Client s3Client;
  private final String bucketName;

  public S3RagFileUploader(
      AmazonS3Client s3Client, @Qualifier("s3BucketName") String s3BucketName) {
    this.s3Client = s3Client;
    this.bucketName = s3BucketName;
  }

  /**
   * Gets the S3 client used by this uploader.
   *
   * @return The S3 client
   */
  public AmazonS3Client getS3Client() {
    return s3Client;
  }

  /**
   * Gets the S3 bucket name used by this uploader.
   *
   * @return The S3 bucket name
   */
  public String getBucketName() {
    return bucketName;
  }

  @Override
  public void uploadFile(UploadableFile file, String s3Path) {
    log.info("Uploading file to S3: {}", s3Path);
    PutObjectRequest objectRequest =
        PutObjectRequest.builder().bucket(bucketName).key(s3Path).build();
    try (RefCountedS3Client refCountedS3Client = s3Client.getRefCountedClient()) {
      refCountedS3Client
          .getClient()
          .putObject(
              objectRequest, RequestBody.fromInputStream(file.getInputStream(), file.getSize()));
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
  }

  @Override
  public Resource downloadFile(String s3Path) throws IOException {
    log.info("Downloading file from S3: {}", s3Path);

    try {
      // Create a temporary file to store the downloaded content
      Path tempFile = Files.createTempFile("s3-download-", null);

      // Download the file from S3
      try (RefCountedS3Client refCountedS3Client = s3Client.getRefCountedClient()) {
        GetObjectRequest getObjectRequest =
            GetObjectRequest.builder().bucket(bucketName).key(s3Path).build();

        // Download the object to the temporary file
        refCountedS3Client
            .getClient()
            .getObject(getObjectRequest, ResponseTransformer.toFile(tempFile.toFile()));
      }

      // Create an input stream from the temporary file
      // The file will be deleted when the JVM exits
      tempFile.toFile().deleteOnExit();

      // Return the file as a resource
      return new InputStreamResource(Files.newInputStream(tempFile));
    } catch (Exception e) {
      log.error("Error downloading file from S3: {}", s3Path, e);
      throw new RuntimeException("Error downloading file from S3: " + e.getMessage(), e);
    }
  }

  // nullables below here

  /**
   * Creates a test double for S3RagFileUploader.
   *
   * @param bucketName The S3 bucket name to use
   * @param tempDir The temporary directory to use for file storage
   * @return A test double for S3RagFileUploader
   */
  public static S3RagFileUploader createNull(String bucketName, String tempDir) {
    return new S3RagFileUploaderTestDouble(bucketName, tempDir);
  }

  /** Test double implementation of S3RagFileUploader. */
  public static class S3RagFileUploaderTestDouble extends S3RagFileUploader {
    private final String tempDir;

    public S3RagFileUploaderTestDouble(String bucketName, String tempDir) {
      super(null, bucketName); // null S3Client, won't be used
      this.tempDir = tempDir;
    }

    @Override
    public void uploadFile(UploadableFile file, String s3Path) {
      log.info("Test double uploading file to S3: {}", s3Path);
      // In the test double, we'll just save to the temp directory
      try {
        java.nio.file.Path filePath = java.nio.file.Path.of(tempDir, s3Path);
        java.nio.file.Files.createDirectories(filePath.getParent());
        java.nio.file.Files.copy(file.getInputStream(), filePath);
      } catch (IOException e) {
        throw new RuntimeException(e);
      }
    }

    @Override
    public Resource downloadFile(String s3Path) throws IOException {
      log.info("Test double downloading file from S3: {}", s3Path);
      java.nio.file.Path filePath = java.nio.file.Path.of(tempDir, s3Path);
      if (!java.nio.file.Files.exists(filePath)) {
        throw new com.cloudera.cai.util.exceptions.NotFound("File not found at path: " + filePath);
      }
      return new InputStreamResource(java.nio.file.Files.newInputStream(filePath));
    }

    @Override
    public AmazonS3Client getS3Client() {
      throw new UnsupportedOperationException("S3Client not available in test double");
    }

    @Override
    public String getBucketName() {
      return super.getBucketName();
    }
  }
}
