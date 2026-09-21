from sqlalchemy.orm import Session
from sqlalchemy import select

from uuid import UUID
from typing import Optional

from domain.users.repositories import UserRepository
from domain.users.entities import User
from infrastructure.models import UserModel


# 用户接口的 SQLAlchemy 实现，使用外部传入的数据库会话
class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    # 将领域用户转换成 ORM 对象，仅新增用户；提交由外部负责
    def save_user(self, user: User) ->None:
        model = UserModel(
            id=user.id,
            username=user.username,
            name=user.name,
            password_hash=user.password_hash,
            created_at=user.created_at,
            height=user.height,
            position=user.position
        )
        self.db.add(model)

    # 通过主键查询，并转换为领域 User；不存在时返回 None
    def get_user_by_id(self, user_id: UUID) ->Optional[User]:
        model = self.db.get(UserModel,user_id)
        if model is None:
            return None

        return User(
            id=model.id,
            username=model.username,
            name=model.name,
            password_hash=model.password_hash,
            created_at=model.created_at,
            height=model.height,
            position=model.position
        )

    # 通过用户名条件查询，并转换为领域 User
    def get_user_by_username(self, username: str) ->Optional[User]:
        statement = select(UserModel).where(
            UserModel.username == username
        )
        model = self.db.scalar(statement)

        if model is None:
            return None

        return User(
            id=model.id,
            username=model.username,
            name=model.name,
            password_hash=model.password_hash,
            created_at=model.created_at,
            height=model.height,
            position=model.position
        )