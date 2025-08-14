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
 * Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
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
 */

package com.cloudera.cai.rag;

import jakarta.annotation.Nullable;
import java.time.Instant;
import java.util.List;
import lombok.*;

public class Types {
  /** Data returned from the file upload endpoint. */
  public record RagDocumentMetadata(
      String fileName, String documentId, String extension, long sizeInBytes) {}

  public enum RagDocumentStatus {
    QUEUED,
    IN_PROGRESS,
    SUCCESS,
    ERROR
  }

  /** Data representing the database table for RAG file metadata (llm_project_rag_document) */
  @Builder(toBuilder = true)
  public record RagDocument(
      @With Long id,
      String filename,
      Long dataSourceId,
      String documentId,
      String s3Path,
      @With Instant vectorUploadTimestamp,
      Long sizeInBytes,
      String extension,
      Instant timeCreated,
      @With Instant timeUpdated,
      String createdById,
      String updatedById,
      @With Instant summaryCreationTimestamp,
      @With RagDocumentStatus summaryStatus,
      @With String summaryError,
      @With RagDocumentStatus indexingStatus,
      @With String indexingError) {}

  @Getter
  public enum ConnectionType {
    MANUAL,
    CDF,
    API,
    OTHER
  }

  @With
  public record RagDataSource(
      Long id,
      String name,
      String embeddingModel,
      String summarizationModel,
      Integer chunkSize,
      Integer chunkOverlapPercent,
      Instant timeCreated,
      Instant timeUpdated,
      String createdById,
      String updatedById,
      ConnectionType connectionType,
      @Nullable Integer documentCount,
      @Nullable Long totalDocSize,
      boolean availableForDefaultProject,
      Long associatedSessionId) {}

  @With
  public record QueryConfiguration(
      boolean enableHyde,
      boolean enableSummaryFilter,
      boolean enableToolCalling,
      Boolean enableStreaming,
      List<String> selectedTools) {}

  @With
  @Builder
  public record Session(
      Long id,
      String name,
      @Singular List<Long> dataSourceIds,
      Long projectId,
      Instant timeCreated,
      Instant timeUpdated,
      String createdById,
      String updatedById,
      Instant lastInteractionTime,
      String inferenceModel,
      Long associatedDataSourceId,
      String rerankModel,
      Integer responseChunks,
      QueryConfiguration queryConfiguration) {

    public static Session fromCreateRequest(CreateSession input, String username) {
      return new Session(
          null,
          input.name(),
          input.dataSourceIds(),
          input.projectId(),
          null,
          null,
          username,
          username,
          null,
          input.inferenceModel(),
          null,
          input.rerankModel(),
          input.responseChunks(),
          input.queryConfiguration());
    }
  }

  @With
  public record CreateSession(
      String name,
      @Singular List<Long> dataSourceIds,
      String inferenceModel,
      String embeddingModel,
      String rerankModel,
      Integer responseChunks,
      QueryConfiguration queryConfiguration,
      Long projectId) {}

  public record MetadataMetrics(
      int numberOfDataSources, int numberOfSessions, int numberOfDocuments) {}

  public record NifiConfigOptions(String name, String description, DataFlowConfigType configType) {}

  public enum DataFlowConfigType {
    AZURE_BLOB,
    S3
  }

  @Builder
  public record Project(
      @With Long id,
      @With String name,
      boolean defaultProject,
      Instant timeCreated,
      Instant timeUpdated,
      @With String createdById,
      @With String updatedById) {

    public static Project fromCreateRequest(CreateProject input, String username) {
      return new Project(null, input.name(), false, null, null, username, username);
    }
  }

  @With
  public record CreateProject(String name) {}
}
