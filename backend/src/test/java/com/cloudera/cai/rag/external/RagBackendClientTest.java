/*******************************************************************************
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

package com.cloudera.cai.rag.external;

import static org.assertj.core.api.Assertions.assertThat;

import com.cloudera.cai.rag.Types.RagDocument;
import com.cloudera.cai.rag.external.RagBackendClient.IndexConfiguration;
import com.cloudera.cai.util.SimpleHttpClient;
import com.cloudera.cai.util.SimpleHttpClient.TrackedHttpRequest;
import com.cloudera.cai.util.Tracker;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;

class RagBackendClientTest {
  @Test
  void indexFile() {
    Tracker<TrackedHttpRequest<?>> tracker = new Tracker<>();
    RagBackendClient client = new RagBackendClient(SimpleHttpClient.createNull(tracker));
    IndexConfiguration indexConfiguration = new IndexConfiguration(123, 2);
    RagDocument document = indexRequest("s3Path", 1234L);

    client.indexFile(document, "bucketName", indexConfiguration);

    List<TrackedHttpRequest<?>> values = tracker.getValues();
    assertThat(values)
        .hasSize(1)
        .contains(
            new TrackedHttpRequest<>(
                HttpMethod.POST,
                "http://rag-backend:8000/index/download-and-index",
                new RagBackendClient.IndexRequest(
                    "bucketName", "s3Path", 1234L, indexConfiguration)));
  }

  @Test
  void createSummary() {
    Tracker<TrackedHttpRequest<?>> tracker = new Tracker<>();
    RagBackendClient client = new RagBackendClient(SimpleHttpClient.createNull(tracker));
    RagDocument document = indexRequest("s3Path", 1234L);

    client.createSummary(document, "bucketName");

    List<TrackedHttpRequest<?>> values = tracker.getValues();
    assertThat(values)
        .hasSize(1)
        .contains(
            new TrackedHttpRequest<>(
                HttpMethod.POST,
                "http://rag-backend:8000/index/data_sources/1234/summarize-document",
                new RagBackendClient.SummaryRequest("bucketName", "s3Path")));
  }

  @Test
  void deleteDataSource() {
    Tracker<TrackedHttpRequest<?>> tracker = new Tracker<>();
    RagBackendClient client = new RagBackendClient(SimpleHttpClient.createNull(tracker));
    client.deleteDataSource(1234L);
    List<TrackedHttpRequest<?>> values = tracker.getValues();
    assertThat(values)
        .hasSize(1)
        .contains(
            new TrackedHttpRequest<>(
                HttpMethod.DELETE, "http://rag-backend:8000/index/data_sources/1234", null));
  }

  @Test
  void deleteDocument() {
    Tracker<TrackedHttpRequest<?>> tracker = new Tracker<>();
    RagBackendClient client = new RagBackendClient(SimpleHttpClient.createNull(tracker));
    client.deleteDocument(1234L, "documentId");
    List<TrackedHttpRequest<?>> values = tracker.getValues();
    assertThat(values)
        .hasSize(1)
        .contains(
            new TrackedHttpRequest<>(
                HttpMethod.DELETE,
                "http://rag-backend:8000/index/data_sources/1234/documents/documentId",
                null));
  }

  @Test
  void deleteSession() {
    Tracker<TrackedHttpRequest<?>> tracker = new Tracker<>();
    RagBackendClient client = new RagBackendClient(SimpleHttpClient.createNull(tracker));
    client.deleteSession(1234L);
    List<TrackedHttpRequest<?>> values = tracker.getValues();
    assertThat(values)
        .hasSize(1)
        .contains(
            new TrackedHttpRequest<>(
                HttpMethod.DELETE, "http://rag-backend:8000/index/sessions/1234", null));
  }

  private static RagDocument indexRequest(String s3Path, Long dataSourceId) {
    return new RagDocument(
        null, null, dataSourceId, null, s3Path, null, null, null, null, null, null, null, null);
  }
}
