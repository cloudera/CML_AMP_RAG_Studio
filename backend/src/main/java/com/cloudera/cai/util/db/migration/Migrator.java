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

import com.cloudera.cai.util.ResourceUtils;
import com.cloudera.cai.util.db.RdbConfig;
import java.io.IOException;
import java.sql.*;
import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;
import javax.sql.DataSource;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class Migrator {
  private final DataSource dataSource;
  private final String resourcesDirectory;
  private final RdbConfig rdbConfig;

  public Migrator(
      DataSource dataSource, String resourcesDirectory, RdbConfig databaseConfiguration) {
    this.dataSource = dataSource;
    this.resourcesDirectory = findResourcesDirectory(resourcesDirectory, databaseConfiguration);
    this.rdbConfig = databaseConfiguration;
  }

  private static String findResourcesDirectory(String rootDirectory, RdbConfig rdbConfiguration) {
    if (rdbConfiguration.isMysql()) {
      return rootDirectory + "/mysql";
    }
    if (rdbConfiguration.isMssql()) {
      return rootDirectory + "/sqlsvr";
    }
    if (rdbConfiguration.isPostgres()) {
      return rootDirectory + "/postgres";
    }
    if (rdbConfiguration.isH2()) {
      return rootDirectory + "/h2";
    }
    throw new IllegalArgumentException("Unsupported database type for migrations");
  }

  /** Assumes that the underlying database has already been created. */
  public void performMigration() throws SQLException, MigrationException {
    log.info("Starting database migration process");
    performMigration(null);
    log.info("Finished database migration process");
  }

  public void performMigration(Integer desiredVersion) throws SQLException, MigrationException {
    MigrationDatastore migrationDatastore;
    try (Connection connection = dataSource.getConnection()) {
      migrationDatastore = setupDatastore(connection);
      MigrationTools.lockDatabase(migrationDatastore);
      try {
        MigrationState currentState = findCurrentState(connection);
        if (currentState == null) {
          throw new IllegalStateException(
              "The schema_migrations table contains no records. Migration process cannot start.");
        }
        if (currentState.dirty()) {
          currentState = cleanUpDirtyDatabase(currentState, connection);
        }
        int versionToTarget = findVersionToTarget(desiredVersion);
        log.info("Starting database migration process to version: " + versionToTarget);

        if (currentState.version() == versionToTarget) {
          log.info("No migrations to perform. Database is already at version " + versionToTarget);
          return;
        }
        SortedSet<Migration> migrationsToPerform =
            gatherMigrationsToPerform(currentState, versionToTarget);
        runMigrations(migrationsToPerform, connection);
      } catch (SQLException | MigrationException e) {
        log.error("Migration process failed", e);
        throw e;
      } finally {
        migrationDatastore.unlock();
      }
    }
  }

  private MigrationState cleanUpDirtyDatabase(MigrationState currentState, Connection connection)
      throws MigrationException, SQLException {
    if (currentState.version() <= 1) {
      throw new MigrationException(
          "Database is in a dirty state at version "
              + currentState.version()
              + ". Bailing out until dropping the database is implemented.");
    }
    // We assume if a migration failed, that it wasn't applied, so it should be safe
    // to simply revert the number and unset the dirty flag.
    int revertedVersion = currentState.version() - 1;
    updateVersion(false, revertedVersion, currentState.version(), true, connection);
    return new MigrationState(revertedVersion, false);
  }

  private int findVersionToTarget(Integer desiredVersion) throws MigrationException {
    return desiredVersion != null
        ? desiredVersion
        : gatherMigrations(migration -> true, migration -> true).stream()
            .map(Migration::getNumber)
            .max(Integer::compareTo)
            .orElse(0);
  }

  private SortedSet<Migration> gatherMigrationsToPerform(
      MigrationState currentState, int versionToTarget) throws MigrationException {
    // if we're currently below the targeted version, we want up migrations in the
    // right range,
    // otherwise the down ones.
    if (currentState.version() < versionToTarget) {
      return gatherMigrations(
          Migration::isUp,
          migration -> migrationLessThanTargetedVersion(currentState, versionToTarget, migration));
    }
    return gatherMigrations(
            Migration::isDown,
            migration ->
                migrationGreaterThanTargetedVersion(currentState, versionToTarget, migration))
        .descendingSet();
  }

  /**
   * Returns whether the current migration is greater than targeted version, and less than or equal
   * to the current state's version.
   */
  private static boolean migrationGreaterThanTargetedVersion(
      MigrationState currentState, int versionToTarget, Migration migration) {
    return migration.getNumber() > versionToTarget
        && migration.getNumber() <= currentState.version();
  }

  /**
   * Returns whether the current migration is less than or equal to the targeted version, and
   * greater than to the current state's version.
   */
  private static boolean migrationLessThanTargetedVersion(
      MigrationState currentState, int versionToTarget, Migration migration) {
    return (migration.getNumber() > currentState.version())
        && (migration.getNumber() <= versionToTarget);
  }

  private MigrationDatastore setupDatastore(Connection connection) throws SQLException {
    MigrationDatastore migrationDatastore = MigrationDatastore.create(rdbConfig, connection);
    migrationDatastore.ensureMigrationTableExists();
    MigrationState currentState = findCurrentState(connection);
    if (currentState == null) {
      try (PreparedStatement ps =
          connection.prepareStatement(
              "INSERT INTO schema_migrations (version, dirty) values (?, ?) ")) {
        ps.setInt(1, 0);
        ps.setBoolean(2, false);
        int rowsInserted = ps.executeUpdate();
        if (rowsInserted != 1) {
          throw new IllegalStateException(
              "Failed to insert initial row into the schema_migrations table. rowsInserted: "
                  + rowsInserted);
        }
      }
    }
    return migrationDatastore;
  }

  private void runMigrations(SortedSet<Migration> migrationsToPerform, Connection connection)
      throws MigrationException {
    for (Migration migration : migrationsToPerform) {
      try {
        updateVersion(
            migration,
            true,
            migration.isUp() ? migration.getNumber() - 1 : migration.getNumber(),
            connection);
        executeSingleMigration(migration, connection);
        updateVersion(
            migration,
            false,
            migration.isUp() ? migration.getNumber() : migration.getNumber() - 1,
            connection);
      } catch (IOException | SQLException e) {
        throw new MigrationException("failed migration " + migration + "", e);
      }
    }
  }

  private void updateVersion(
      Migration pendingMigration, boolean dirty, int expectedCurrentVersion, Connection connection)
      throws SQLException {
    int newVersion =
        pendingMigration.isUp() ? pendingMigration.getNumber() : pendingMigration.getNumber() - 1;

    updateVersion(dirty, newVersion, expectedCurrentVersion, !dirty, connection);
  }

  private void updateVersion(
      boolean dirty,
      int newVersion,
      int expectedCurrentVersion,
      boolean expectedCurrentDirtyState,
      Connection connection)
      throws SQLException {
    try (PreparedStatement ps =
        connection.prepareStatement(
            "UPDATE schema_migrations set version = ?, dirty = ? WHERE version = ? and dirty = ?")) {
      ps.setInt(1, newVersion);
      ps.setBoolean(2, dirty);
      ps.setInt(3, expectedCurrentVersion);
      ps.setBoolean(4, expectedCurrentDirtyState);
      int rowsUpdated = ps.executeUpdate();
      connection.commit();
      if (rowsUpdated != 1) {
        throw new IllegalStateException(
            "Failed to update schema_migrations table to '"
                + newVersion
                + "' from '"
                + expectedCurrentVersion
                + "'. rowsUpdated: "
                + rowsUpdated);
      }
    }
  }

  private NavigableSet<Migration> gatherMigrations(
      Predicate<Migration> migrationDirectionFilter, Predicate<Migration> migrationVersionFilter)
      throws MigrationException {
    try {
      log.debug(
          "Attempting to read migration file list from resources directory: {}",
          resourcesDirectory);
      var migrationsRoot =
          resourcesDirectory.substring(0, resourcesDirectory.lastIndexOf("/")) + "/migrations.txt";

      log.debug("Attempting to read files from resources file list: {}", migrationsRoot);
      var fileContents = ResourceUtils.getFileContents(migrationsRoot);
      log.debug("Found migration files: {}", fileContents);
      List<String> fileNames = fileContents.lines().toList();
      log.debug("Found migration files: {}", fileNames);
      return fileNames.stream()
          .filter(fileName -> fileName.endsWith(".sql"))
          .map(Migration::new)
          .filter(migrationDirectionFilter)
          .filter(migrationVersionFilter)
          .collect(Collectors.toCollection(TreeSet::new));
    } catch (Exception e) {
      throw new MigrationException("Failed to read migration files.", e);
    }
  }

  private MigrationState findCurrentState(Connection connection) throws SQLException {
    try (PreparedStatement ps =
        connection.prepareStatement(
            "select version, dirty from " + MigrationDatastore.SCHEMA_MIGRATIONS_TABLE)) {
      ResultSet resultSet = ps.executeQuery();
      if (!resultSet.next()) {
        return null;
      }
      return new MigrationState(resultSet.getInt("version"), resultSet.getBoolean("dirty"));
    }
  }

  public void executeSingleMigration(Migration migration, Connection connection)
      throws IOException, SQLException {
    log.info("executing migration: {}", migration);
    String sql = ResourceUtils.getFileContents(resourcesDirectory + "/" + migration.getFilename());
    if (sql.trim().isEmpty()) {
      log.info("Skipping empty migration : {}", migration.getFilename());
      return;
    }
    try (Statement statement = connection.createStatement()) {
      statement.executeUpdate(sql);
    }
  }

  /**
   * Pre-initializes the schema migrations table, in cases where the database is being converted
   * from a legacy migration tool (i.e. liquibase).
   *
   * <p>_If and only if_ ALL the following conditions are met, then the <code>schema_migrations
   * </code> table will be initialized with the value of <code>assumedCurrentVersion</code>:
   *
   * <ul>
   *   <li>there are legacy migrations present
   *   <li>there is no existing <code>schema_migrations</code> table
   *   <li>an <code>assumedCurrentVersion</code> value is provided
   * </ul>
   *
   * <p>If legacy migrations are in place, and you do not provide an assumed current version, this
   * method will throw an {@link IllegalStateException}.
   *
   * @param legacyMigrationsInPlace Whether legacy migrations have already been applied to this
   *     database.
   * @param assumedCurrentVersion The version that the legacy migrations should correspond to.
   */
  public void preInitializeIfRequired(
      boolean legacyMigrationsInPlace, Optional<Integer> assumedCurrentVersion)
      throws SQLException {
    try (Connection connection = dataSource.getConnection()) {
      if (!legacyMigrationsInPlace) {
        return;
      }
      if (assumedCurrentVersion.isEmpty()) {
        throw new IllegalStateException(
            "If legacy migrations are in place, you *must* provide a version to initialize the schema migrations to.");
      }
      try {
        MigrationState currentState = findCurrentState(connection);
        log.info(
            "schema_versions table already exists. Skipping pre-initialization step. current state: "
                + currentState);
      } catch (SQLException e) {
        log.info(
            "No schema_versions table found. Initializing to version "
                + assumedCurrentVersion.get());
        setupDatastore(connection);
        updateVersion(false, assumedCurrentVersion.get(), 0, false, connection);
      }
    }
  }

  private record MigrationState(int version, boolean dirty) {}
}
