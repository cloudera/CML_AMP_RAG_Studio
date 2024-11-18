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

package com.cloudera.cai.util.db.migration;

import java.sql.*;
import lombok.extern.slf4j.Slf4j;

@Slf4j
class SqlServerMigrationDatastore implements MigrationDatastore {
  private final Connection connection;

  public SqlServerMigrationDatastore(Connection connection) {
    this.connection = connection;
  }

  @Override
  public void lock() throws SQLException {
    String lockId = generateLockId();

    try (CallableStatement cs = connection.prepareCall("{? = call sp_getapplock( ?, ?, ?, ? )}")) {
      cs.registerOutParameter(1, Types.INTEGER);
      cs.setString(2, lockId);
      cs.setString(3, "Update"); // lock mode
      cs.setString(4, "Session"); // lock owner
      cs.setInt(5, 0);
      cs.execute();
      int outValue = cs.getInt(1);
      if (outValue != 0) {
        throw new SQLException(
            "Failed to lock the database for migration. Result code: " + outValue);
      }
    }
  }

  @Override
  public void unlock() throws SQLException {
    String lockId = generateLockId();

    try (CallableStatement cs = connection.prepareCall("{? = call sp_releaseapplock( ?, ? )}")) {
      cs.registerOutParameter(1, Types.INTEGER);
      cs.setString(2, lockId);
      cs.setString(3, "Session"); // lock owner
      cs.executeUpdate();
      int outValue = cs.getInt(1);
      if (outValue != 0) {
        throw new SQLException(
            "Failed to unlock the database post-migration. Result code: " + outValue);
      }
    }
  }

  @Override
  public void ensureMigrationTableExists() throws SQLException {
    // the simplest way in sql server to see if a table exists is just to try to query it.
    try (PreparedStatement ps =
        connection.prepareStatement("select count(*) from " + SCHEMA_MIGRATIONS_TABLE)) {
      ps.executeQuery().close();
      return;
    } catch (SQLException e) {
      log.info(SCHEMA_MIGRATIONS_TABLE + " does not exist. Creating");
      // this means the table doesn't already exist, so go ahead and created it below...
    }

    String sql =
        "CREATE TABLE "
            + SCHEMA_MIGRATIONS_TABLE
            + " ( version BIGINT PRIMARY KEY NOT NULL, dirty BIT NOT NULL );";
    try (PreparedStatement ps = connection.prepareStatement(sql)) {
      ps.execute();
    }
  }

  private String generateLockId() throws SQLException {
    String schema = connection.getSchema();
    return MigrationTools.generateLockId(schema, "schema_migrations");
  }
}
