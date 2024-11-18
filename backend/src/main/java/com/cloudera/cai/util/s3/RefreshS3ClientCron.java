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

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.auth.credentials.AwsSessionCredentials;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.CreateBucketRequest;
import software.amazon.awssdk.services.s3.model.HeadBucketRequest;
import software.amazon.awssdk.services.s3.model.NoSuchBucketException;
import software.amazon.awssdk.services.s3.model.SessionCredentials;
import software.amazon.awssdk.services.sts.StsClient;
import software.amazon.awssdk.services.sts.model.*;

@Slf4j
public class RefreshS3ClientCron implements Runnable {
  private final String bucketName;
  private final Region awsRegion;
  private final Integer durationSeconds;
  private final AmazonS3Client s3Client;

  public RefreshS3ClientCron(
      String bucketName, Region awsRegion, Integer durationSeconds, AmazonS3Client s3Client) {
    this.bucketName = bucketName;
    this.awsRegion = awsRegion;
    this.durationSeconds = durationSeconds;
    this.s3Client = s3Client;
  }

  /** The action to be performed by this timer task. */
  @Override
  public void run() {
    log.info("Refreshing S3Client");
    try {
      var awsCredentials = getBasicSessionCredentials();
      createAndRefreshNewClient(awsCredentials);
    } catch (Throwable ex) {
      log.error("Failed to refresh S3 Client: {}", ex.getMessage(), ex);
      return;
    }
    log.info("Refreshing S3Client complete");
  }

  private void createAndRefreshNewClient(SessionCredentials awsCredentials) {
    log.trace("Creating new S3 Client");
    var newS3Client =
        S3Client.builder()
            .credentialsProvider(
                () ->
                    AwsSessionCredentials.create(
                        awsCredentials.accessKeyId(),
                        awsCredentials.secretAccessKey(),
                        awsCredentials.sessionToken()))
            .region(awsRegion)
            .build();

    try {
      newS3Client.headBucket(HeadBucketRequest.builder().bucket(bucketName).build());
    } catch (NoSuchBucketException e) {
      newS3Client.createBucket(CreateBucketRequest.builder().bucket(bucketName).build());
    }
    log.trace("New S3 Client created");

    AwsSessionCredentials v2Credentials =
        AwsSessionCredentials.create(
            awsCredentials.accessKeyId(),
            awsCredentials.secretAccessKey(),
            awsCredentials.sessionToken());
    s3Client.refreshS3Client(v2Credentials, newS3Client, v2Credentials);
  }

  private SessionCredentials getBasicSessionCredentials() throws IOException {
    log.trace("Creating sts client");
    try (StsClient stsClient = createStsClient(awsRegion)) {
      log.trace("Sts client created");

      log.trace("assuming role with web identity");
      // Call STS to assume the role
      var roleRequest = getCredentialFromWebIdentity();
      AssumeRoleWithWebIdentityResponse roleResponse =
          stsClient.assumeRoleWithWebIdentity(roleRequest);
      log.trace("Assumed role with web identity");
      var credentials = roleResponse.credentials();

      // Extract the session credentials
      return SessionCredentials.builder()
          .accessKeyId(credentials.accessKeyId())
          .secretAccessKey(credentials.secretAccessKey())
          .sessionToken(credentials.sessionToken())
          .build();
    }
  }

  private static StsClient createStsClient(Region awsRegion) {
    final var stsClientBuilder = StsClient.builder().region(awsRegion);
    return stsClientBuilder.build();
  }

  private AssumeRoleWithWebIdentityRequest getCredentialFromWebIdentity() throws IOException {
    String roleArn = System.getenv(AmazonS3Client.AWS_ROLE_ARN);
    String token = getWebIdentityToken();

    // Obtain credentials for the IAM role. Note that you cannot assume the role of
    // an AWS root account;
    // Amazon S3 will deny access. You must use credentials for an IAM user or an
    // IAM role.
    return AssumeRoleWithWebIdentityRequest.builder()
        .durationSeconds(durationSeconds) /*900 seconds (15 minutes)*/
        .roleArn(roleArn)
        .webIdentityToken(token)
        .roleSessionName("model_db_" + UUID.randomUUID())
        .build();
  }

  private static String getWebIdentityToken() throws IOException {
    return new String(
        Files.readAllBytes(Paths.get(System.getenv(AmazonS3Client.AWS_WEB_IDENTITY_TOKEN_FILE))));
  }
}
