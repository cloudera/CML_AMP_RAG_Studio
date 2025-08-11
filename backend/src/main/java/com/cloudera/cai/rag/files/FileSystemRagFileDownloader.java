package com.cloudera.cai.rag.files;

import com.cloudera.cai.util.exceptions.NotFound;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class FileSystemRagFileDownloader implements RagFileDownloader {
  private static final String FILE_STORAGE_ROOT = fileStoragePath();

  private static String fileStoragePath() {
    var fileStoragePath = System.getenv("RAG_DATABASES_DIR") + "/file_storage";
    log.info("configured with fileStoragePath = {}", fileStoragePath);
    return fileStoragePath;
  }

  @Override
  public InputStream openStream(String s3Path) throws NotFound {
    try {
      Path filePath = Path.of(FILE_STORAGE_ROOT, s3Path);
      if (!Files.exists(filePath)) {
        throw new NotFound("no document found with storage path: " + s3Path);
      }
      return Files.newInputStream(filePath);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
  }
}
