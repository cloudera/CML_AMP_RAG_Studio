package com.cloudera.cai.rag.files;

import com.cloudera.cai.util.exceptions.NotFound;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/** Downloader abstraction to open a streaming InputStream for a stored document. */
public interface RagFileDownloader {
  /**
   * Opens a streaming InputStream for the provided storage path. The caller is responsible for
   * closing the returned stream.
   */
  InputStream openStream(String s3Path) throws NotFound;

  /**
   * Test double that serves InputStreams from an in-memory byte[] map. Useful for unit tests
   * without using a mocking framework.
   */
  static RagFileDownloader createNull() {
    return createNull(Map.of());
  }

  static RagFileDownloader createNull(Map<String, byte[]> pathToBytes) {
    Map<String, byte[]> backing = new HashMap<>(pathToBytes);
    return s3Path -> {
      byte[] data = backing.get(s3Path);
      if (data == null) {
        throw new NotFound("no document found with storage path: " + s3Path);
      }
      return new ByteArrayInputStream(data);
    };
  }
}
