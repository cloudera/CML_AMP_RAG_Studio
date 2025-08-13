package com.cloudera.cai.rag.files;

import com.cloudera.cai.util.exceptions.NotFound;
import com.cloudera.cai.util.s3.AmazonS3Client;
import com.cloudera.cai.util.s3.RefCountedS3Client;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.S3Exception;

@Slf4j
public class S3RagFileDownloader implements RagFileDownloader {
  private final AmazonS3Client s3Client;
  private final String bucketName;

  public S3RagFileDownloader(
      AmazonS3Client s3Client, @Qualifier("s3BucketName") String s3BucketName) {
    this.s3Client = s3Client;
    this.bucketName = s3BucketName;
  }

  @Override
  public InputStream openStream(String s3Path) throws NotFound {
    log.info("Downloading file from S3: {}", s3Path);
    GetObjectRequest request = GetObjectRequest.builder().bucket(bucketName).key(s3Path).build();
    RefCountedS3Client client = s3Client.getRefCountedClient();
    try {
      InputStream inner = client.getClient().getObject(request);
      return new ClosingInputStream(inner, client);
    } catch (S3Exception e) {
      if (e.statusCode() == 404) {
        client.close();
        throw new NotFound("no document found with storage path: " + s3Path);
      }
      client.close();
      throw e;
    }
  }

  private static class ClosingInputStream extends FilterInputStream {
    private final RefCountedS3Client client;

    protected ClosingInputStream(InputStream in, RefCountedS3Client client) {
      super(in);
      this.client = client;
    }

    @Override
    public void close() throws IOException {
      try {
        super.close();
      } finally {
        client.close();
      }
    }
  }
}
