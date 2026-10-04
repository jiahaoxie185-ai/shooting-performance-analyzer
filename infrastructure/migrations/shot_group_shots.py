"""为已有 SQLite 组表添加逐球 JSON 字段，保留原有表和数据。"""
from sqlalchemy import inspect, text
from infrastructure.database import engine


def migrate(target_engine=engine) -> None:
    with target_engine.begin() as connection:
        columns = inspect(connection).get_columns("shot_groups")
        if not any(column["name"] == "shots" for column in columns):
            connection.execute(text(
                "ALTER TABLE shot_groups ADD COLUMN shots JSON NOT NULL DEFAULT '[]'"
            ))


if __name__ == "__main__":
    migrate()
    print("Shot group shots migration complete")
