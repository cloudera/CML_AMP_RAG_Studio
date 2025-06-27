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

package com.cloudera.cai.rag.datasources;

import com.cloudera.cai.rag.Types;
import com.cloudera.cai.rag.Types.RagDataSource;
import com.cloudera.cai.util.ResourceUtils;
import java.io.IOException;
import java.util.List;
import org.springframework.stereotype.Component;

@Component
public class RagDataSourceService {
  public static final int DEFAULT_CHUNK_OVERLAP = 10;
  public static final int DEFAULT_CHUNK_SIZE = 512;
  private final RagDataSourceRepository ragDataSourceRepository;

  public RagDataSourceService(RagDataSourceRepository ragDataSourceRepository) {
    this.ragDataSourceRepository = ragDataSourceRepository;
  }

  public RagDataSource createRagDataSource(RagDataSource input) {
    if (input.chunkOverlapPercent() == null) {
      input = input.withChunkOverlapPercent(DEFAULT_CHUNK_OVERLAP);
    }
    if (input.chunkSize() == null) {
      input = input.withChunkSize(DEFAULT_CHUNK_SIZE);
    }
    var id =
        ragDataSourceRepository.createRagDataSource(
            input.withCreatedById(input.createdById()).withUpdatedById(input.updatedById()));
    return ragDataSourceRepository.getRagDataSourceById(id);
  }

  public RagDataSource updateRagDataSource(RagDataSource input) {
    ragDataSourceRepository.updateRagDataSource(input);
    return ragDataSourceRepository.getRagDataSourceById(input.id());
  }

  public void deleteDataSource(Long id) {
    ragDataSourceRepository.deleteDataSource(id);
  }

  public List<RagDataSource> getRagDataSources() {
    return ragDataSourceRepository.getRagDataSources();
  }

  public RagDataSource getRagDataSourceById(Long id) {
    return ragDataSourceRepository.getRagDataSourceById(id);
  }

  public List<Types.NifiConfigOptions> getNifiConfigOptions() {
    return List.of(
        new Types.NifiConfigOptions(
            "S3 Cloudera DataFlow Definition",
            "Flow definition for pointing a S3 bucket to RAG Studio.  Requires AWS credentials.",
            Types.DataFlowConfigType.S3),
        new Types.NifiConfigOptions(
            "Azure Blob Storage Cloudera DataFlow Definition",
            "Flow definition for pointing an Azure Blob Store to RAG Studio.  Requires Azure credentials.",
            Types.DataFlowConfigType.AZURE_BLOB));
  }

  public String getNifiConfig(Long id, String ragStudioUrl, Types.DataFlowConfigType configType) {
    try {
      String fileName =
          switch (configType) {
            case AZURE_BLOB -> "AzureBlob-To-RagStudio-Nifi-template.json";
            case S3 -> "S3-To-RagStudio-Nifi-template.json";
          };
      return ResourceUtils.getFileContents(fileName)
          .replace("$$$RAG_STUDIO_DATASOURCE_ID$$$", id.toString())
          .replace("$$$RAG_STUDIO_URL$$$", ragStudioUrl);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
  }

  // Nullables stuff below here.

  public static RagDataSourceService createNull() {
    return new RagDataSourceService(RagDataSourceRepository.createNull());
  }
}
