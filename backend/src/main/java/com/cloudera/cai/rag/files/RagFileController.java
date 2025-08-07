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

import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.Types.RagDocumentMetadata;
import com.cloudera.cai.rag.files.RagFileService.DocumentDownloadResult;
import com.cloudera.cai.rag.util.UsernameExtractor;
import com.cloudera.cai.util.exceptions.BadRequest;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@Slf4j
@RequestMapping("/api/v1/rag")
public class RagFileController {
  private final RagFileService ragFileService;
  private final UsernameExtractor usernameExtractor = new UsernameExtractor();

  @Autowired
  public RagFileController(RagFileService ragFileService) {
    this.ragFileService = ragFileService;
  }

  @PostMapping(
      value = "/dataSources/{dataSourceId}/files",
      consumes = "multipart/form-data",
      produces = "application/json")
  public List<RagDocumentMetadata> uploadRagDocument(
      @RequestPart("file") MultipartFile file,
      @PathVariable Long dataSourceId,
      HttpServletRequest request) {
    if (file.isEmpty()) {
      throw new BadRequest("File is empty");
    }
    return ragFileService.saveRagFile(
        file, dataSourceId, usernameExtractor.extractUsername(request));
  }

  @GetMapping(value = "/dataSources/{dataSourceId}/files", produces = "application/json")
  public List<Types.RagDocument> getRagDocuments(@PathVariable Long dataSourceId) {
    log.debug("retrieving document metadata for dataSource id: {}", dataSourceId);
    return ragFileService.getRagDocuments(dataSourceId);
  }

  @DeleteMapping(value = "/dataSources/{dataSourceId}/files/{id}")
  public void deleteRagFile(@PathVariable Long id, @PathVariable Long dataSourceId) {
    ragFileService.deleteRagFile(id, dataSourceId);
  }

  /**
   * Downloads a document file by ID.
   *
   * @param id The document ID
   * @param dataSourceId The data source ID
   * @return The document file as a downloadable resource
   * @throws IOException If there's an error reading the file
   */
  @GetMapping(value = "/dataSources/{dataSourceId}/files/{id}/download")
  public ResponseEntity<InputStreamResource> downloadRagFile(
      @PathVariable Long id, @PathVariable Long dataSourceId) throws IOException {
    DocumentDownloadResult downloadResult = ragFileService.downloadRagFile(id, dataSourceId);

    HttpHeaders headers = new HttpHeaders();
    headers.add(
        HttpHeaders.CONTENT_DISPOSITION,
        "attachment; filename=\"" + downloadResult.document().filename() + "\"");

    // Try to determine content type based on file extension
    String contentType = determineContentType(downloadResult.document().extension());

    return ResponseEntity.ok()
        .headers(headers)
        .contentType(MediaType.parseMediaType(contentType))
        .body(new InputStreamResource(downloadResult.content()));
  }

  /**
   * Determines the appropriate content type based on the file extension.
   *
   * @param extension The file extension
   * @return The content type as a string
   */
  private String determineContentType(String extension) {
    if (extension == null) {
      return "application/octet-stream";
    }

    return switch (extension.toLowerCase()) {
      case "pdf" -> "application/pdf";
      case "txt" -> "text/plain";
      case "html", "htm" -> "text/html";
      case "doc" -> "application/msword";
      case "docx" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
      case "xls" -> "application/vnd.ms-excel";
      case "xlsx" -> "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
      case "ppt" -> "application/vnd.ms-powerpoint";
      case "pptx" -> "application/vnd.openxmlformats-officedocument.presentationml.presentation";
      case "jpg", "jpeg" -> "image/jpeg";
      case "png" -> "image/png";
      case "gif" -> "image/gif";
      case "xml" -> "application/xml";
      case "json" -> "application/json";
      case "csv" -> "text/csv";
      default -> "application/octet-stream";
    };
  }
}
