# 配置 SQLite 数据库、会话和模型基类。
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 使用当前文件位置确定数据库路径，避免受运行目录影响
BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "basketball.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 管理数据库连接；创建引擎本身不会立即建表
engine = create_engine(DATABASE_URL)

# 为此引擎创建的每个新连接开启 SQLite 外键检查
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()

# 数据库会话工厂；由调用方管理会话的提交、回滚和关闭
SessionLocal =  sessionmaker(bind=engine)

# 所有 ORM 模型的共同基类，metadata 收集表结构定义
class Base(DeclarativeBase):
    pass
