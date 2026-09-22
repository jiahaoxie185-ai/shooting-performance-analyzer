from uuid import UUID, uuid4
from datetime import datetime

from application.ports import PasswordHasher

from domain.users.entities import User
from application.unit_of_work import UnitOfWork


# 组织用户注册和查询流程，当前由外部管理事务
class UserService:
    # 保存传入的用户 Repository 和密码哈希组件
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