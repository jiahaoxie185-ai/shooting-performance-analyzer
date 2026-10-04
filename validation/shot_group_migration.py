"""验证点位迁移保留历史数据，重复执行及失败回滚。"""
import unittest

from sqlalchemy import create_engine, event, inspect

from infrastructure.database import Base, enable_foreign_keys
from infrastructure.migrations.shot_group_nullable_zone import migrate


class ShotGroupMigrationValidation(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        event.listen(self.engine, "connect", enable_foreign_keys)
        Base.metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE shot_groups")
            connection.exec_driver_sql(
                "CREATE TABLE shot_groups (id CHAR(32) PRIMARY KEY NOT NULL, "
                "session_id CHAR(32) NOT NULL REFERENCES shooting_sessions(id), "
                "zone VARCHAR(50) NOT NULL, started_at DATETIME NOT NULL, "
                "ended_at DATETIME, shots JSON NOT NULL DEFAULT '[]')"
            )
            connection.exec_driver_sql(
                "INSERT INTO users (id, username, name, password_hash, created_at) "
                "VALUES ('user', 'demo', 'Demo', 'test-only', '2026-10-04')"
            )
            connection.exec_driver_sql(
                "INSERT INTO shooting_sessions (id, user_id, started_at) "
                "VALUES ('session', 'user', '2026-10-04')"
            )
            connection.exec_driver_sql(
                "INSERT INTO shot_groups VALUES (?, ?, ?, ?, ?, ?)",
                ("group", "session", "paint", "2026-10-04", "2026-10-04",
                 '[{"id":"preserved","made":true}]'),
            )
            self.original = connection.exec_driver_sql("SELECT * FROM shot_groups").fetchall()

    def tearDown(self):
        self.engine.dispose()

    def test_preserve_data_and_repeat(self):
        migrate(self.engine)
        migrate(self.engine)
        with self.engine.begin() as connection:
            self.assertEqual(connection.exec_driver_sql("SELECT * FROM shot_groups").fetchall(), self.original)
            connection.exec_driver_sql(
                "INSERT INTO shot_groups (id, session_id, started_at, shots) "
                "VALUES ('empty', 'session', '2026-10-04', '[]')"
            )
            self.assertIsNone(connection.exec_driver_sql(
                "SELECT zone FROM shot_groups WHERE id = 'empty'"
            ).scalar())
            self.assertEqual(connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall(), [])
            self.assertTrue(inspect(connection).get_foreign_keys("shot_groups"))

    def test_failed_replacement_rolls_back(self):
        def fail(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith("ALTER TABLE"):
                raise RuntimeError("simulated migration failure")

        event.listen(self.engine, "before_cursor_execute", fail)
        with self.assertRaises(RuntimeError):
            migrate(self.engine)
        event.remove(self.engine, "before_cursor_execute", fail)
        with self.engine.connect() as connection:
            self.assertEqual(connection.exec_driver_sql("SELECT * FROM shot_groups").fetchall(), self.original)
            zone = next(column for column in inspect(connection).get_columns("shot_groups")
                        if column["name"] == "zone")
            self.assertFalse(zone["nullable"])
            self.assertFalse(inspect(connection).has_table("shot_groups_new"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
