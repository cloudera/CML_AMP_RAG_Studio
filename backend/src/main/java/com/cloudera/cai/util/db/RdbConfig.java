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

import java.util.regex.Pattern;
import java.util.stream.Collectors;
import lombok.*;
import lombok.extern.slf4j.Slf4j;

@Data
@Builder(toBuilder = true)
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter(AccessLevel.NONE)
@Slf4j
public class RdbConfig {

  public static final String H2_DB_TYPE = "H2";
  private static final String POSTGRES_DB_TYPE = "PostgreSQL";
  private static final String MYSQL_DB_TYPE = "MySQL5";
  private static final String SQL_SERVER_DB_TYPE = "SQLServer2008";
  public static final String REQUIRED_FIELD_IS_MISSING = "required field is missing";

  private String rdbDatabaseName;
  private String rdbDriver;
  private String rdbType;
  private String rdbUrl;
  private String rdbUsername;
  private String rdbPassword;
  @Builder.Default private String sslMode = "DISABLED";
  @Builder.Default private Boolean sslEnabled = false;
  private String dbConnectionUrl;

  public void validate(String base) throws InvalidDbConfigException {
    if (rdbDriver == null || rdbDriver.isEmpty()) {
      throw new InvalidDbConfigException(base + ".rdbDriver", REQUIRED_FIELD_IS_MISSING);
    }
    if (rdbType == null || rdbType.isEmpty()) {
      throw new InvalidDbConfigException(base + ".rdbDialect", REQUIRED_FIELD_IS_MISSING);
    }
    if (rdbUsername == null || rdbUsername.isEmpty()) {
      throw new InvalidDbConfigException(base + ".rdbUsername", REQUIRED_FIELD_IS_MISSING);
    }
    if (!isMysql() && !isMssql() && !isH2()) {
      throw new InvalidDbConfigException(base + ".rdbDialect", "Unknown or unsupported dialect.");
    }

    if (dbConnectionUrl == null) {
      if (rdbDatabaseName == null || rdbDatabaseName.isEmpty()) {
        throw new InvalidDbConfigException(base + ".rdbDatabaseName", REQUIRED_FIELD_IS_MISSING);
      }
      if (rdbUrl == null || rdbUrl.isEmpty()) {
        throw new InvalidDbConfigException(base + ".rdbUrl", REQUIRED_FIELD_IS_MISSING);
      }
      if (sslMode == null || sslMode.isEmpty()) {
        throw new InvalidDbConfigException(base + ".sslMode", REQUIRED_FIELD_IS_MISSING);
      }
    }
  }

  public boolean isMysql() {
    return rdbType.equals(MYSQL_DB_TYPE);
  }

  public boolean isPostgres() {
    return rdbType.equals(POSTGRES_DB_TYPE);
  }

  public boolean isMssql() {
    return rdbType.equals(SQL_SERVER_DB_TYPE);
  }

  public boolean isH2() {
    return rdbType.equals(H2_DB_TYPE);
  }

  public static String buildDatabaseConnectionString(RdbConfig rdb) {
    if (rdb.isH2()) {
      return buildDatabaseServerConnectionString(rdb);
    }
    if (rdb.dbConnectionUrl != null) {
      return rdb.dbConnectionUrl;
    }

    if (rdb.isMssql()) {
      return adjustMsSqlRdbUrl(rdb.rdbUrl) + ";databaseName=" + rdb.getRdbDatabaseName();
    }
    if (rdb.isPostgres()) {
      return rdb.rdbUrl;
    }

    final var url =
        rdb.rdbUrl
            + "/"
            + rdb.getRdbDatabaseName()
            + "?createDatabaseIfNotExist=true&useUnicode=yes&characterEncoding=UTF-8&allowMultiQueries=true&allowPublicKeyRetrieval=true"
            + "&sslEnabled="
            + rdb.sslEnabled
            + "&sslMode="
            + rdb.sslMode;
    log.trace("Using db URL: {}", url);
    return url;
  }

  public static String buildDatabaseServerConnectionString(RdbConfig rdb) {
    if (rdb.dbConnectionUrl != null) {
      return rdb.dbConnectionUrl;
    }

    if (rdb.isH2()) {
      return rdb.rdbUrl + ";DB_CLOSE_DELAY=-1;CASE_INSENSITIVE_IDENTIFIERS=TRUE";
    }

    if (rdb.isMssql()) {
      return adjustMsSqlRdbUrl(rdb.rdbUrl);
    }

    if (rdb.isPostgres()) {
      return rdb.rdbUrl;
    }
    final var url =
        rdb.rdbUrl
            + "?createDatabaseIfNotExist=true&useUnicode=yes&characterEncoding=UTF-8&allowMultiQueries=true&allowPublicKeyRetrieval=true"
            + "&sslEnabled="
            + rdb.sslEnabled
            + "&sslMode="
            + rdb.sslMode;
    log.info("Using db URL: {}", url);
    return url;
  }

  private static String adjustMsSqlRdbUrl(String rdbUrl) {
    // turn on TLS, and turn off server cert validation, if not already configured
    String tlsOptions = "";
    if (!rdbUrl.contains("encrypt=")) {
      tlsOptions += ";encrypt=true";
    }
    if (!rdbUrl.contains("trustServerCertificate=")) {
      tlsOptions += ";trustServerCertificate=true";
    }
    return rdbUrl + tlsOptions;
  }

  public static String buildDatabaseName(RdbConfig rdb) {
    String dbName = rdb.getRdbDatabaseName();
    if (rdb.getDbConnectionUrl() != null) {
      dbName = getDBNameFromDBConnectionURL(rdb, rdb.dbConnectionUrl);
    }

    if (dbName == null) {
      dbName = getDBNameFromDBConnectionURL(rdb, rdb.rdbUrl);
    }

    if (dbName.contains("-")) {
      if (rdb.isMysql()) {
        return String.format("`%s`", dbName);
      }
      if (rdb.isMssql()) {
        return String.format("\"%s\"", dbName);
      }
    }
    return dbName;
  }

  private static String getDBNameFromDBConnectionURL(RdbConfig rdb, String url) {
    String regex;
    if (rdb.isMssql()) {
      // Regex reference: https://regex101.com/r/yaU0DY/1
      regex = ";databaseName=([^;]*)";
    } else if (rdb.isMysql()) {
      regex = "^jdbc:mysql:(?://[^/]+/)?(\\w+)";
    } else if (rdb.isPostgres()) {
      regex = "^jdbc:postgresql:(?://[^/]+/)?(\\w+)";
    } else {
      throw new IllegalStateException("database url parsing not supported for db type: " + rdb.rdbType);
    }
    Pattern pattern = Pattern.compile(regex, Pattern.CASE_INSENSITIVE);
    var dbName =
        pattern
            .matcher(url)
            .results()
            .map(mr -> mr.group(1))
            .collect(Collectors.joining());

    if (dbName.isEmpty()) {
      throw new InvalidDbConfigException(
              url, "Database name not found in the database connection URL");
    }
    return dbName;
  }
}
