from application.unit_of_work import UnitOfWork
from infrastructure.database import SessionLocal
from infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from infrastructure.repositories.shooting_repository import SqlAlchemyShootingRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.db = self.session_factory()

        try:
            self.user_repository = SqlAlchemyUserRepository(self.db)
            self.shooting_repository = SqlAlchemyShootingRepository(self.db)
        except Exception:
            self.db.close()
            raise

        return self

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
        
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            self.rollback()
        finally:
            self.db.close()