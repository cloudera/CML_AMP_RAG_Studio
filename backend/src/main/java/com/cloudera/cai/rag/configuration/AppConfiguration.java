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

package com.cloudera.cai.rag.configuration;

import com.cloudera.cai.rag.files.FileSystemRagFileDownloader;
import com.cloudera.cai.rag.files.FileSystemRagFileUploader;
import com.cloudera.cai.rag.files.RagFileDownloader;
import com.cloudera.cai.rag.files.RagFileUploader;
import com.cloudera.cai.rag.files.S3RagFileDownloader;
import com.cloudera.cai.rag.files.S3RagFileUploader;
import com.cloudera.cai.util.reconcilers.ReconcilerConfig;
import com.cloudera.cai.util.s3.AmazonS3Client;
import com.cloudera.cai.util.s3.S3Config;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.instrumentation.httpclient.JavaHttpClientTelemetry;
import java.net.Socket;
import java.net.http.HttpClient;
import java.security.KeyManagementException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.cert.X509Certificate;
import java.util.Optional;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLEngine;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509ExtendedTrustManager;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@Slf4j
public class AppConfiguration {

  @Bean
  public String s3BucketName(S3Config s3Config) {
    return s3Config.getBucketName();
  }

  @Bean
  public String s3BucketPrefix(S3Config s3Config) {
    return s3Config.getBucketPrefix();
  }

  @Bean
  public S3Config s3Config() {
    return S3Config.builder()
        .endpointUrl(System.getenv("AWS_ENDPOINT_URL_S3"))
        .accessKey(System.getenv("AWS_ACCESS_KEY_ID"))
        .secretKey(System.getenv("AWS_SECRET_ACCESS_KEY"))
        .awsRegion(System.getenv("AWS_DEFAULT_REGION"))
        .bucketName(Optional.ofNullable(System.getenv("S3_RAG_DOCUMENT_BUCKET")).orElse(""))
        .bucketPrefix(Optional.ofNullable(System.getenv("S3_RAG_BUCKET_PREFIX")).orElse(""))
        .build();
  }

  @Bean
  public boolean testEnvironment() {
    return false;
  }

  @Bean
  public ReconcilerConfig singleWorkerReconcilerConfig(
      @Qualifier("testEnvironment") boolean testEnvironment) {
    return ReconcilerConfig.builder().workerCount(1).isTestReconciler(testEnvironment).build();
  }

  @Bean
  public ReconcilerConfig reconcilerConfig(@Qualifier("testEnvironment") boolean testEnvironment) {
    return ReconcilerConfig.builder().isTestReconciler(testEnvironment).build();
  }

  @Bean
  public HttpClient httpClient(OpenTelemetry openTelemetry)
      throws NoSuchAlgorithmException, KeyManagementException {
    var trustManager =
        new X509ExtendedTrustManager() {
          @Override
          public X509Certificate[] getAcceptedIssuers() {
            return new X509Certificate[] {};
          }

          @Override
          public void checkClientTrusted(X509Certificate[] chain, String authType) {}

          @Override
          public void checkServerTrusted(X509Certificate[] chain, String authType) {}

          @Override
          public void checkClientTrusted(X509Certificate[] chain, String authType, Socket socket) {}

          @Override
          public void checkServerTrusted(X509Certificate[] chain, String authType, Socket socket) {}

          @Override
          public void checkClientTrusted(
              X509Certificate[] chain, String authType, SSLEngine engine) {}

          @Override
          public void checkServerTrusted(
              X509Certificate[] chain, String authType, SSLEngine engine) {}
        };
    var sslContext = SSLContext.getInstance("TLS");
    sslContext.init(null, new TrustManager[] {trustManager}, new SecureRandom());

    var httpClientBuilder = HttpClient.newBuilder();

    if (isDevEnv()) {
      httpClientBuilder.sslContext(sslContext);
    }

    return JavaHttpClientTelemetry.builder(openTelemetry)
        .build()
        .newHttpClient(httpClientBuilder.followRedirects(HttpClient.Redirect.NORMAL).build());
  }

  private boolean isDevEnv() {
    // todo: how can we detect that we're in an env with a self-signed cert?
    return true;
  }

  @Bean
  public RagFileUploader ragFileUploader(S3Config configuration) {
    if (configuration.getBucketName().isEmpty()) {
      return new FileSystemRagFileUploader();
    }
    AmazonS3Client s3Client = new AmazonS3Client(configuration);
    return new S3RagFileUploader(s3Client, configuration.getBucketName());
  }

  @Bean
  public RagFileDownloader ragFileDownloader(S3Config configuration) {
    if (configuration.getBucketName().isEmpty()) {
      return new FileSystemRagFileDownloader();
    }
    AmazonS3Client s3Client = new AmazonS3Client(configuration);
    return new S3RagFileDownloader(s3Client, configuration.getBucketName());
  }

  public static String getLlmServiceUrl() {
    var llmServiceUrl =
        Optional.ofNullable(System.getenv("LLM_SERVICE_URL"))
            .map(url -> url + "/llm-service")
            .orElse("http://localhost:8081");
    log.info("LLM Service URL: {}", llmServiceUrl);
    return llmServiceUrl;
  }
}
