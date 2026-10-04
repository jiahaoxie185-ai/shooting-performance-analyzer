"""允许进行中的空组没有点位，保留已有组的全部数据。"""
from datetime import datetime
import sqlite3

from sqlalchemy import MetaData, inspect, text

from infrastructure.database import DATABASE_PATH, engine
from infrastructure.models import ShotGroupModel


def migrate(target_engine=engine) -> None:
    if target_engine.dialect.name != "sqlite":
        raise ValueError("此迁移仅用于 SQLite")
    with target_engine.connect() as connection:
        # SQLite 修改非空约束需要复制表；显式事务保证失败时回滚。
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            inspector = inspect(connection)
            if not inspector.has_table("shot_groups"):
                ShotGroupModel.__table__.create(connection)
                connection.commit()
                return
            columns = inspector.get_columns("shot_groups")
            if next(column for column in columns if column["name"] == "zone")["nullable"]:
                connection.commit()
                return
            if {column["name"] for column in columns} != set(ShotGroupModel.__table__.columns.keys()):
                raise ValueError("组表结构与预期不一致，请先完成 shots 字段迁移")
            # 避免未来新增引用表时，替换组表意外影响关联数据。
            for table in inspector.get_table_names():
                if any(fk["referred_table"] == "shot_groups" for fk in inspector.get_foreign_keys(table)):
                    raise ValueError("已有其他表引用投篮组，需要单独制定迁移方案")
            extras = connection.execute(text(
                "SELECT sql FROM sqlite_master WHERE tbl_name = 'shot_groups' "
                "AND type IN ('index', 'trigger') AND sql IS NOT NULL"
            )).scalars().all()
            metadata = MetaData()
            for table in ShotGroupModel.metadata.tables.values():
                table.to_metadata(metadata)
            replacement = ShotGroupModel.__table__.to_metadata(metadata, name="shot_groups_new")
            replacement.create(connection)
            connection.exec_driver_sql(
                "INSERT INTO shot_groups_new (id, session_id, zone, started_at, ended_at, shots) "
                "SELECT id, session_id, zone, started_at, ended_at, shots FROM shot_groups"
            )
            connection.exec_driver_sql("DROP TABLE shot_groups")
            connection.exec_driver_sql("ALTER TABLE shot_groups_new RENAME TO shot_groups")
            for statement in extras:
                connection.exec_driver_sql(statement)
            if connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
                raise ValueError("迁移后的外键检查未通过")
            connection.commit()
        except Exception:
            connection.rollback()
            raise


if __name__ == "__main__":
    # 实际数据库迁移前备份，备份文件仍保留在本地。
    backup = DATABASE_PATH.with_name(
        f"basketball-before-nullable-zone-{datetime.now():%Y%m%d-%H%M%S-%f}.db"
    )
    with sqlite3.connect(DATABASE_PATH) as source, sqlite3.connect(backup) as destination:
        source.backup(destination)
    migrate()
    print("Shot group nullable zone migration complete; local backup created")
