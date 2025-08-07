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

import com.cloudera.cai.util.exceptions.NotFound;
import com.cloudera.cai.util.s3.AmazonS3Client;
import com.cloudera.cai.util.s3.RefCountedS3Client;
import java.io.IOException;
import java.io.InputStream;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.NoSuchKeyException;
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
  public InputStream downloadFile(String s3Path) {
    log.info("Downloading file from S3: {}", s3Path);
    GetObjectRequest getObjectRequest =
        GetObjectRequest.builder().bucket(bucketName).key(s3Path).build();

    try {
      RefCountedS3Client refCountedS3Client = s3Client.getRefCountedClient();
      try {
        InputStream response = refCountedS3Client.getClient().getObject(getObjectRequest);

        // Return a wrapped input stream that closes the RefCountedS3Client when done
        return new S3WrappedInputStream(response, refCountedS3Client);
      } catch (NoSuchKeyException e) {
        refCountedS3Client.close();
        throw new NotFound("File not found at path: " + s3Path);
      } catch (Exception e) {
        refCountedS3Client.close();
        throw new RuntimeException("Failed to download file from S3: " + e.getMessage(), e);
      }
    } catch (Exception e) {
      throw new RuntimeException("Failed to create S3 client: " + e.getMessage(), e);
    }
  }

  /** A wrapped input stream that closes the RefCountedS3Client when the stream is closed. */
  private static class S3WrappedInputStream extends InputStream {
    private final InputStream delegate;
    private final RefCountedS3Client client;

    public S3WrappedInputStream(InputStream delegate, RefCountedS3Client client) {
      this.delegate = delegate;
      this.client = client;
    }

    @Override
    public int read() throws IOException {
      return delegate.read();
    }

    @Override
    public int read(byte[] b) throws IOException {
      return delegate.read(b);
    }

    @Override
    public int read(byte[] b, int off, int len) throws IOException {
      return delegate.read(b, off, len);
    }

    @Override
    public byte[] readAllBytes() throws IOException {
      return delegate.readAllBytes();
    }

    @Override
    public long skip(long n) throws IOException {
      return delegate.skip(n);
    }

    @Override
    public int available() throws IOException {
      return delegate.available();
    }

    @Override
    public void close() throws IOException {
      try {
        delegate.close();
      } finally {
        client.close();
      }
    }
  }
}
