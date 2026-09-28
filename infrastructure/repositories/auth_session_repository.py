from uuid import UUID

from sqlalchemy.orm import Session

from domain.users.repositories import AuthSessionRepository
from infrastructure.models import AuthSession


class SqlAlchemyAuthSessionRepository(AuthSessionRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, token_hash: str, user_id: UUID, expires_at: int) -> None:
        self.db.add(AuthSession(
            token_hash = token_hash,
            user_id = user_id,
            expires_at = expires_at
        ))
        
