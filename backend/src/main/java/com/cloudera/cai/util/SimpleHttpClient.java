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

package com.cloudera.cai.util;

import com.cloudera.cai.util.exceptions.ClientError;
import com.cloudera.cai.util.exceptions.NotFound;
import com.cloudera.cai.util.exceptions.ServerError;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

@Component
public class SimpleHttpClient {
  private final HttpClient httpClient;
  private final ObjectMapper objectMapper;

  @Autowired
  public SimpleHttpClient(HttpClient httpClient, ObjectMapper objectMapper) {
    this.httpClient = httpClient;
    this.objectMapper = objectMapper;
  }

  public <T> String post(String url, T bodyObject, String... headers) throws IOException {
    String body = marshalBody(bodyObject);
    HttpRequest request =
        HttpRequest.newBuilder()
            .uri(URI.create(url))
            .version(HttpClient.Version.HTTP_1_1)
            .POST(HttpRequest.BodyPublishers.ofString(body))
            .headers(headers)
            .build();
    try {
      HttpResponse<String> response =
          httpClient.send(request, HttpResponse.BodyHandlers.ofString());
      int statusCode = response.statusCode();
      if (statusCode == 404) {
        throw new NotFound("Failed to post to " + url + " code: " + statusCode);
      }

      if (400 <= statusCode && statusCode < 500) {
        throw new ClientError(response.body(), statusCode);
      }

      if (statusCode >= 500) {
        throw new ServerError(response.body(), statusCode);
      }
      return response.body();
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new RuntimeException(e);
    }
  }

  private <T> String marshalBody(T bodyObject) {
    try {
      return objectMapper.writeValueAsString(bodyObject);
    } catch (JsonProcessingException e) {
      throw new RuntimeException(e);
    }
  }

  public void delete(String path, String... headers) {
    HttpRequest request =
        HttpRequest.newBuilder().uri(URI.create(path)).DELETE().headers(headers).build();
    try {
      HttpResponse<String> response =
          httpClient.send(request, HttpResponse.BodyHandlers.ofString());
      int statusCode = response.statusCode();
      if (statusCode >= 400) {
        throw new RuntimeException(
            "Failed to delete " + path + " code: " + statusCode + ", body : " + response.body());
      }
    } catch (IOException | InterruptedException e) {
      throw new RuntimeException(e);
    }
  }

  // nullable stuff below here

  public static SimpleHttpClient createNull() {
    return createNull(new Tracker<>());
  }

  public static SimpleHttpClient createNull(
      Tracker<TrackedHttpRequest<?>> tracker, RuntimeException... t) {
    return new SimpleHttpClient(null, new ObjectMapper()) {
      private final RuntimeException[] exceptions = t;
      private int exceptionIndex = 0;

      private void checkForException() {
        if (exceptionIndex < exceptions.length) {
          throw exceptions[exceptionIndex++];
        }
      }

      @Override
      public <T> String post(String url, T bodyObject, String... headers) {
        tracker.track(new TrackedHttpRequest<>(HttpMethod.POST, url, bodyObject));
        checkForException();
        return "";
      }

      @Override
      public void delete(String path, String... headers) {
        tracker.track(new TrackedHttpRequest<>(HttpMethod.DELETE, path, null));
        checkForException();
        // no-op
      }
    };
  }

  public record TrackedHttpRequest<T>(HttpMethod method, String url, T body) {}
}
