# 处理用户注册、查询和登录会话的业务流程。
from uuid import UUID, uuid4
from datetime import datetime

from application.ports import PasswordHasher

from domain.users.entities import User
from application.unit_of_work import UnitOfWork
import hashlib
import secrets
import time


# 组织用户注册、查询和登录流程，事务由工作单元管理
class UserService:
    # 保存传入的工作单元和密码哈希组件
    def __init__(self, uow: UnitOfWork, password_hasher: PasswordHasher):
        self.uow = uow
        self.password_hasher = password_hasher

    # 检查用户名重复、计算密码哈希，然后创建并保存用户
    def sign_up(
            self,
            username: str,
            name: str,
            password: str,
    ) -> User:

        with self.uow:
            existing_user = self.uow.user_repository.get_user_by_username(username)

            if existing_user is not None:
                raise ValueError("该用户已存在")

            # 只把哈希结果存入实体，不保存原始密码

            if len(password) < 8:
                raise ValueError("密码最低长度为8")

            password_hash = self.password_hasher.hash(password)
            
            user = User(
                id= uuid4(),
                username=username,
                name=name,
                password_hash=password_hash,
                created_at=datetime.now()
            )

            self.uow.user_repository.save_user(user)
            self.uow.commit()

        return user

    # 按 ID 查询用户，不存在时抛出业务异常
    def get_user_by_id(self, user_id: UUID) -> User:
        with self.uow:
            user = self.uow.user_repository.get_user_by_id(user_id)

            if user is None:
                raise ValueError("用户不存在")

        return user

    # 按用户名查询用户，不存在时抛出业务异常
    def get_user_by_username(self, username: str) -> User:
        with self.uow:
            user = self.uow.user_repository.get_user_by_username(username)

            if user is None:
                raise ValueError("用户不存在")

        return user

    # 校验用户名和密码，成功时返回用户，失败时抛出业务异常
    def authenticate(self, username: str, password: str) -> User:
        with self.uow:
            user = self.uow.user_repository.get_user_by_username(username)

            if user is None or not self.password_hasher.verify(user.password_hash, password):
                raise ValueError("用户名或密码错误")


        return user

    # 校验密码后生成随机令牌，只把令牌摘要存入数据库，返回用户和原始令牌
    def login(self, username: str, password: str):
        with self.uow:
            user = self.uow.user_repository.get_user_by_username(username)
            if user is None or not self.password_hasher.verify(
                user.password_hash, password
            ):
                raise ValueError("用户名或密码错误")

            token = secrets.token_urlsafe(32)
            digest = hashlib.sha3_256(token.encode("utf-8")).hexdigest()

            self.uow.auth_session_repository.save(
                token_hash=digest,
                user_id=user.id,
                expires_at=int(time.time())+7*24*60*60
            )

            self.uow.commit()

        return user, token

    # 用与登录相同的算法计算令牌摘要，查询未过期会话对应的用户
    def current_user(self, token: str) -> User:
        digest = hashlib.sha3_256(token.encode("utf-8")).hexdigest()
        with self.uow:
            user_id = self.uow.auth_session_repository.get_user_id(
                digest, int(time.time())
            )
            if user_id is None:
                raise ValueError("登录已失效")
            
            user = self.uow.user_repository.get_user_by_id(user_id)
            if user is None:
                raise ValueError("登录已失效")

        return user

    # 计算令牌摘要并删除对应会话，使该令牌失效
    def logout(self, token: str) -> None:
        digest = hashlib.sha3_256(token.encode("utf-8")).hexdigest()
        with self.uow:
            self.uow.auth_session_repository.delete(digest)
            self.uow.commit()

            