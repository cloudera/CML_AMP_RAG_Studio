import logging
from sqlite3 import Connection
from typing import List, Optional

from src.migration.datastore import Datastore, MigrationContent, MigrationState

logger = logging.getLogger(__name__)


class Migrator:
    def __init__(self, datastore: Datastore) -> None:
        self.datastore = datastore
        datastore.ensure_migration_content_table_exists()
        datastore.ensure_migration_state_table_exists()

    def perform_migration(self, desired_version: Optional[int] = None) -> None:
        self._update_migrations()

        state = self.datastore.get_migration_state()
        logger.info("Current migration state version: %s", state.version)
        if state.dirty:
            logger.warning("Database is in a dirty state. Cleaning up.")
            state = self._clean_up_dirty_database(state)

        last_migration_in_disk = max(
            map(lambda x: x.id, self.datastore.get_migrations_from_disk())
        )
        logger.info("Last migration in disk: %s", last_migration_in_disk)

        if desired_version is None:
            desired_version = last_migration_in_disk

        logger.info("Desired migration version: %s", desired_version)

        if desired_version != state.version:
            migrations_to_perform = self._gather_migrations_to_perform(
                state.version, desired_version
            )
            logger.debug("Migrations to perform: %s", migrations_to_perform)
            for migration in migrations_to_perform:
                # Ensure we do one migration step at a time
                assert migration.up == (state.version < migration.id)
                assert abs(migration.id - state.version) <= 1

                logger.info("Executing migration: %s", migration.name)

                state.version = migration.id if migration.up else migration.id - 1
                state.dirty = True
                self.datastore.update_migration_state(state)
                logger.debug("Migration state updated: %s", state)

                self.datastore.execute_migration(migration)
                logger.debug("Migration executed: %s", migration.name)

                state.dirty = False
                self.datastore.update_migration_state(state)
                logger.debug("Migration state updated: %s", state)

        logger.info("Database migrations completed successfully.")

    def _update_migrations(self) -> None:
        migrations = self.datastore.get_migrations_from_disk()
        self.datastore.update_migrations(migrations)

    def _clean_up_dirty_database(self, state: MigrationState) -> MigrationState:
        if state.version <= 1:
            raise RuntimeError(
                "Database is in a dirty state at version "
                + str(state.version)
                + ". Bailing out until dropping the database is implemented."
            )
        # We assume if a migration failed, that it wasn't applied, so it should be safe
        # to simply revert the number and unset the dirty flag.
        new_state = MigrationState(state.version - 1, False)
        self.datastore.update_migration_state(new_state)
        return new_state

    def _gather_migrations_to_perform(
        self, from_version: int, to_version: int
    ) -> List[MigrationContent]:
        # Load migrations from db since we might need to do a rollback from a future version
        migrations_from_db = self.datastore.get_migrations_from_db()
        if from_version < to_version:
            # We need to perform the update migrations
            return list(
                sorted(
                    filter(
                        lambda x: x.id > from_version and x.id <= to_version and x.up,
                        migrations_from_db,
                    ),
                    key=lambda x: x.id,
                )
            )
        else:
            # We need to perform the rollback migrations
            return list(
                sorted(
                    filter(
                        lambda x: x.id <= from_version
                        and x.id > to_version
                        and not x.up,
                        migrations_from_db,
                    ),
                    key=lambda x: -x.id,
                )
            )
