# 定义用户数据的存取接口。
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from .entities import User

# 用户存取接口，具体数据库操作由基础设施层实现
class UserRepository(ABC):
    @abstractmethod
    # 保存新用户，事务提交由调用方负责
    def save_user(self, user: User) ->None:
        pass

    @abstractmethod
    # 按用户 ID 查询，找不到时返回 None
    def get_user_by_id(self, user_id:UUID) -> Optional[User]:
        pass

    @abstractmethod
    # 按唯一用户名查询，找不到时返回 None
    def get_user_by_username(self, username: str) -> Optional[User]:
        pass 

# 登录会话存取接口，具体数据库操作由基础设施层实现
class AuthSessionRepository(ABC):
    @abstractmethod
    # 保存令牌摘要、所属用户和过期时间，事务提交由调用方负责
    def save(self, token_hash: str, user_id: UUID, expires_at: int) -> None:
        pass

    @abstractmethod
    # 按令牌摘要查询未过期会话的用户 ID，找不到或已过期时返回 None
    def get_user_id(self, token_hash: str, now: int) -> Optional[UUID]:
        pass

    @abstractmethod
    # 删除指定会话，事务提交由调用方负责
    def delete(self, token_hash: str) -> None:
        pass
    