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

import com.cloudera.cai.util.db.DatabaseConfig;
import com.cloudera.cai.util.db.JdbiUtils;
import com.cloudera.cai.util.db.RdbConfig;
import com.cloudera.cai.util.db.migration.Migrator;
import java.sql.SQLException;
import javax.sql.DataSource;
import lombok.extern.slf4j.Slf4j;
import org.jdbi.v3.core.HandleCallback;
import org.jdbi.v3.core.HandleConsumer;
import org.jdbi.v3.core.Jdbi;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
public class JdbiConfiguration {
  private static volatile Jdbi jdbi;
  private static final Object LOCK = new Object();

  @Bean
  public DatabaseOperations databaseOperations() {
    return new DatabaseOperations(createJdbi());
  }

  private static Jdbi createJdbi() {
    if (jdbi == null) {
      synchronized (LOCK) {
        if (jdbi == null) {
          log.info("Initializing new Jdbi instance");
          jdbi = Jdbi.create(createDataSource());
        }
      }
    }
    return jdbi;
  }

  private static DataSource createDataSource() {
    try {
      DatabaseConfig databaseConfig = createDatabaseConfig();
      DataSource dataSource = dataSource(databaseConfig);
      Migrator migrator = migrator(dataSource, rdbConfig(databaseConfig));
      migrator.performMigration();
      return dataSource;
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  private static Migrator migrator(DataSource dataSource, RdbConfig dbConfig) {
    return new Migrator(dataSource, "migrations", dbConfig);
  }

  private static DatabaseConfig createDatabaseConfig() {
    String dbUrl = System.getenv().getOrDefault("DB_URL", "jdbc:h2:mem:rag");
    String rdbType = System.getenv().getOrDefault("DB_TYPE", RdbConfig.H2_DB_TYPE);
    String password = System.getenv().get("DB_PASSWORD");
    String username = System.getenv().get("DB_USERNAME");
    RdbConfig rdbConfiguration =
        RdbConfig.builder()
            .rdbUrl(dbUrl)
            .rdbType(rdbType)
            .rdbDatabaseName("rag")
            .rdbUsername(username)
            .rdbPassword(password)
            .build();
    if (rdbConfiguration.isPostgres()) {
      rdbConfiguration =
          rdbConfiguration.toBuilder().rdbUsername("postgres").rdbDatabaseName(null).build();
    }
    return DatabaseConfig.builder().RdbConfiguration(rdbConfiguration).build();
  }

  private static RdbConfig rdbConfig(DatabaseConfig dbConfig) {
    return dbConfig.getRdbConfiguration();
  }

  private static DataSource dataSource(DatabaseConfig databaseConfig) throws SQLException {
    JdbiUtils.createDBIfNotExists(databaseConfig.getRdbConfiguration());
    return JdbiUtils.initializeDataSource(databaseConfig, "ragDB");
  }

  // nullables below here
  public static DatabaseOperations createNull(RuntimeException... exceptions) {
    return new DatabaseOperationsStub(createJdbi(), exceptions);
  }

  /**
   * Test implementation of DatabaseOperations that can inject failures for testing. This allows us
   * to test error scenarios without using Mockito.
   */
  private static class DatabaseOperationsStub extends DatabaseOperations {
    private final RuntimeException[] exceptions;
    private int exceptionIndex = 0;

    private DatabaseOperationsStub(Jdbi jdbi, RuntimeException[] exceptions) {
      super(jdbi);
      this.exceptions = exceptions;
    }

    private void checkForException() {
      if (exceptionIndex < exceptions.length) {
        throw exceptions[exceptionIndex++];
      }
    }

    @Override
    public <X extends Exception> void useHandle(HandleConsumer<X> handleConsumer) throws X {
      checkForException();
      super.useHandle(handleConsumer);
    }

    @Override
    public <X extends Exception> void useTransaction(HandleConsumer<X> handleConsumer) throws X {
      checkForException();
      super.useTransaction(handleConsumer);
    }

    @Override
    public <T, X extends Exception> T inTransaction(HandleCallback<T, X> handleCallback) throws X {
      checkForException();
      return super.inTransaction(handleCallback);
    }

    @Override
    public <T, X extends Exception> T withHandle(HandleCallback<T, X> handleCallback) throws X {
      checkForException();
      return super.withHandle(handleCallback);
    }
  }
}
