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

package com.cloudera.cai.util.db;

import com.zaxxer.hikari.HikariDataSource;
import java.sql.*;
import javax.sql.DataSource;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class JdbiUtils {

  public static DataSource initializeDataSource(DatabaseConfig databaseConfig, String poolName) {
    var hikariDataSource = new HikariDataSource();
    var dbUrl = RdbConfig.buildDatabaseConnectionString(databaseConfig.getRdbConfiguration());
    hikariDataSource.setJdbcUrl(dbUrl);
    hikariDataSource.setUsername(databaseConfig.getRdbConfiguration().getRdbUsername());
    hikariDataSource.setPassword(databaseConfig.getRdbConfiguration().getRdbPassword());
    hikariDataSource.setMinimumIdle(Integer.parseInt(databaseConfig.getMinConnectionPoolSize()));
    hikariDataSource.setMaximumPoolSize(
        Integer.parseInt(databaseConfig.getMaxConnectionPoolSize()));
    hikariDataSource.setRegisterMbeans(true);
    //    hikariDataSource.setMetricsTrackerFactory(new PrometheusMetricsTrackerFactory());
    hikariDataSource.setPoolName(poolName);
    hikariDataSource.setLeakDetectionThreshold(databaseConfig.getLeakDetectionThresholdMs());
    hikariDataSource.setConnectionTimeout(databaseConfig.getConnectionTimeoutMillis());
    return hikariDataSource;
  }

  public static void createDBIfNotExists(RdbConfig rdbConfig) throws SQLException {
    log.info("Creating database if not exists: rdbConfig: {}", rdbConfig);

    var databaseName = RdbConfig.buildDatabaseName(rdbConfig);
    log.info("Creating database if not exists: databaseName: {}", databaseName);
    var dbUrl =
        RdbConfig.buildDatabaseServerConnectionString(
            rdbConfig.toBuilder().rdbDatabaseName("postgres").build());

    log.info("Connecting to DB URL to verify database exists {}", dbUrl);
    try (Connection connection =
        DriverManager.getConnection(
            dbUrl, rdbConfig.getRdbUsername(), rdbConfig.getRdbPassword())) {
      if (rdbConfig.isH2()) {
        log.debug("database driver is H2...skipping creation");
        return;
      }
      ResultSet resultSet = connection.getMetaData().getCatalogs();

      while (resultSet.next()) {
        String databaseNameRes = resultSet.getString(1);
        if (databaseName.equals(databaseNameRes)) {
          log.info("the database {} exists", databaseName);
          return;
        }
      }

      log.info("the database {} does not exist", databaseName);
      try (Statement statement = connection.createStatement()) {
        statement.executeUpdate("CREATE DATABASE " + databaseName);
        log.info("the database {} was created successfully", databaseName);
      }
    }
  }
}
