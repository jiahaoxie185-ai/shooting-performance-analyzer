# 实现登录会话的数据库存取。
from uuid import UUID

from sqlalchemy.orm import Session

from domain.users.repositories import AuthSessionRepository
from infrastructure.models import AuthSession
from typing import Optional


# 登录会话接口的 SQLAlchemy 实现；提交、回滚和关闭由外部负责
class SqlAlchemyAuthSessionRepository(AuthSessionRepository):
    def __init__(self, db: Session):
        self.db = db

    # 新增一条会话记录，只保存令牌摘要，不保存原始令牌
    def save(self, token_hash: str, user_id: UUID, expires_at: int) -> None:
        self.db.add(AuthSession(
            token_hash = token_hash,
            user_id = user_id,
            expires_at = expires_at
        ))

    # 按令牌摘要查询会话；不存在或已过期时返回 None
    def get_user_id(self, token_hash: str, now: int) -> Optional[UUID]:
        session = self.db.get(AuthSession, token_hash)
        if session is None or session.expires_at <= now:
            return None
        return session.user_id

    # 删除指定会话；会话不存在时不做任何操作
    def delete(self, token_hash: str) -> None:
        session = self.db.get(AuthSession, token_hash)
        if session is not None:
            self.db.delete(session)
