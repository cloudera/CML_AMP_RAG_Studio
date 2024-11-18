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

package com.cloudera.cai.util.s3;

import static com.cloudera.cai.util.s3.CommonUtils.*;
import static java.time.temporal.ChronoUnit.MILLIS;

import java.net.URI;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.AwsCredentials;
import software.amazon.awssdk.core.client.config.ClientOverrideConfiguration;
import software.amazon.awssdk.http.apache.ApacheHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3AsyncClient;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3ClientBuilder;

// S3Client provides a wrapper to the regular AmazonS3 object. The goal is to ensure that the
// AmazonS3 object is
// _always_ valid when performing operations. If it is not, then that's a bug. This simplifies the
// handling of the API
// calls so that we don't have to keep worrying about refreshing the credentials on every call.
// We use a reference counter to keep track of when we have to shutdown a previous client that
// should not be used anymore.
@Slf4j
public class AmazonS3Client {
  // AWS Related Constants
  public static final String AWS_ROLE_ARN = "AWS_ROLE_ARN";
  public static final String AWS_WEB_IDENTITY_TOKEN_FILE = "AWS_WEB_IDENTITY_TOKEN_FILE";
  private final ClientOverrideConfiguration defaultClientConfig;

  private final String bucketName;
  private final S3Config s3Config;

  private volatile S3Client s3Client;
  private volatile S3AsyncClient asyncClient;
  private volatile AtomicInteger referenceCounter;
  private volatile AwsCredentials awsCredentials;
  private volatile AwsCredentials v2Credentials;

  public AmazonS3Client(S3Config s3Config) {
    this.s3Config = s3Config;
    String cloudAccessKey = s3Config.getAccessKey();
    String cloudSecretKey = s3Config.getSecretKey();
    Region awsRegion = Region.of(s3Config.getAwsRegion());
    this.bucketName = s3Config.getBucketName();
    this.defaultClientConfig = ClientOverrideConfiguration.builder().build();

    // Start the counter with one because this class has a reference to it
    referenceCounter = new AtomicInteger(1);

    if (cloudAccessKey != null && cloudSecretKey != null && !overrideUrlIsSet(s3Config)) {
      log.debug("config based credentials based s3 client");
      initializeS3ClientWithAccessKey(cloudAccessKey, cloudSecretKey, awsRegion);
    } else if (isEnvSet(AWS_ROLE_ARN) && isEnvSet(AWS_WEB_IDENTITY_TOKEN_FILE)) {
      log.debug("temporary token based s3 client");
      initializeWithWebIdentity(awsRegion);
    } else {
      log.debug("environment credentials based s3 client");
      // reads credentials from OS Environment
      initializeWithEnvironment(awsRegion);
    }
  }

  private static boolean overrideUrlIsSet(S3Config s3Config) {
    return s3Config.getEndpointUrl() != null && !s3Config.getEndpointUrl().isEmpty();
  }

  private void initializeWithEnvironment(Region awsRegion) {
    this.s3Client = buildEnvironmentClient(awsRegion);
    scheduleRefresh(() -> buildEnvironmentClient(awsRegion));
  }

  private S3Client buildEnvironmentClient(Region awsRegion) {
    S3ClientBuilder builder = S3Client.builder();
    if (overrideUrlIsSet(s3Config)) {
      builder.endpointOverride(URI.create(s3Config.getEndpointUrl())).forcePathStyle(true);
    }
    return builder
        .overrideConfiguration(defaultClientConfig)
        .httpClientBuilder(
            ApacheHttpClient.builder()
                .maxConnections(s3Config.getConnectionPoolSize())
                .connectionTimeout(Duration.of(s3Config.getRequestTimeoutMs(), MILLIS)))
        .region(awsRegion)
        .build();
  }

  /**
   * schedule swapping out with a new client periodically, to clear up any possible stuck connection
   * pool issues.
   */
  private void scheduleRefresh(Supplier<S3Client> s3) {
    scheduleTask(
        () -> refreshS3Client(awsCredentials, s3.get(), v2Credentials),
        0L,
        s3Config.getRefreshIntervalSeconds(),
        TimeUnit.SECONDS);
  }

  private void initializeS3ClientWithAccessKey(
      String cloudAccessKey, String cloudSecretKey, Region awsRegion) {
    this.v2Credentials = AwsBasicCredentials.create(cloudAccessKey, cloudSecretKey);
    this.s3Client = buildAccessKeyClient(awsRegion);
    scheduleRefresh(() -> buildAccessKeyClient(awsRegion));
  }

  private S3Client buildAccessKeyClient(Region awsRegion) {
    return S3Client.builder()
        .region(awsRegion)
        .overrideConfiguration(defaultClientConfig)
        .credentialsProvider(() -> v2Credentials)
        .build();
  }

  public RefCountedS3Client getRefCountedClient() {
    return new RefCountedS3Client(awsCredentials, s3Client, asyncClient, referenceCounter);
  }

  private void initializeWithWebIdentity(Region awsRegion) {
    // While creating RoleCredentials we have a configurable time (900 seconds (15 minutes) by
    // default) in the AssumeRoleWithWebIdentityRequest so here expiration will be 900 seconds
    // so set cron to 1/3 of the duration of the credentials which will be (300 seconds (5 minutes))
    var durationSeconds =
        s3Config.getRefreshIntervalSeconds() * 3; // by default 900 seconds (15 minutes)
    var refreshTokenFrequency =
        s3Config.getRefreshIntervalSeconds(); // by default 300 seconds (5 minutes)
    log.trace("S3 Client refresh frequency {} seconds", refreshTokenFrequency);
    scheduleTask(
        new RefreshS3ClientCron(bucketName, awsRegion, durationSeconds, this),
        0L /*initialDelay*/,
        refreshTokenFrequency /*periodic refresh frequency*/,
        TimeUnit.SECONDS);
  }

  void refreshS3Client(
      AwsCredentials awsCredentials, S3Client s3Client, AwsCredentials v2Credentials) {
    var s3AsyncClient =
        S3AsyncClient.builder()
            .credentialsProvider(() -> v2Credentials)
            .region(Region.of(s3Config.getAwsRegion()))
            .build();
    // Once we get to this point, we know that we have a good new s3 client, so it's time to swap
    // it. No fail can happen now
    log.debug("Replacing S3 Client");
    try (RefCountedS3Client client = getRefCountedClient()) {
      // Decrement the current reference counter represented by this object pointing to it
      this.referenceCounter.decrementAndGet();

      // Swap the references
      this.referenceCounter = new AtomicInteger(1);
      this.awsCredentials = awsCredentials;
      this.v2Credentials = v2Credentials;
      this.s3Client = s3Client;
      this.asyncClient = s3AsyncClient;
      log.debug("S3 Client replaced");
      // At the end of the try, the reference counter will be decremented again and shutdown will
      // be called
    }
  }
}
