# 用一个数据库会话管理两个仓储和事务。
from application.unit_of_work import UnitOfWork
from infrastructure.database import SessionLocal
from infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from infrastructure.repositories.shooting_repository import SqlAlchemyShootingRepository
from infrastructure.repositories.auth_session_repository import SqlAlchemyAuthSessionRepository

# 在同一事务内操作用户仓储和训练仓储。
class SqlAlchemyUnitOfWork(UnitOfWork):
    # 允许测试传入独立的会话工厂。
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    # 进入 with 时创建会话，并让两个仓储共用它。
    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.db = self.session_factory()

        try:
            self.user_repository = SqlAlchemyUserRepository(self.db)
            self.shooting_repository = SqlAlchemyShootingRepository(self.db)
            self.auth_session_repository = SqlAlchemyAuthSessionRepository(self.db)
        # 仓储创建失败时关闭已打开的会话。
        except Exception:
            self.db.close()
            raise

        return self

    # 显式提交当前事务。
    def commit(self) -> None:
        self.db.commit()

    # 撤销尚未提交的操作。
    def rollback(self) -> None:
        self.db.rollback()
        
    # 离开 with 时回滚未提交操作，并关闭会话。
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            self.rollback()
        finally:
            self.db.close()