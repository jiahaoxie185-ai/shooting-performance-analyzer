# 测试用户服务的注册、查询和错误处理。
import unittest
from uuid import uuid4

from argon2 import PasswordHasher
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from application.user_services import UserService
from infrastructure.database import Base
from infrastructure import models  # 导入模型，注册表结构
from infrastructure.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from infrastructure.security import Argon2PasswordService


# 验证注册、查询和错误处理。
class TestUserService(unittest.TestCase):
    def setUp(self):
        # 每个测试使用独立的内存数据库
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    # 测试结束后释放内存数据库。
    def tearDown(self):
        self.engine.dispose()

    # 注册后分别按 ID 和用户名读取，并检查密码哈希。
    def test_sign_up_and_find_user(self):
        password = "test-password-123"

        # 注册并提交到数据库
        with Session(self.engine) as db:
            repository = SqlAlchemyUserRepository(db)
            service = UserService(
                user_repository=repository,
                password_hasher=Argon2PasswordService(),
            )

            user = service.sign_up(
                username="player_23",
                name="James",
                password=password,
            )
            db.commit()

        # 使用新会话，验证用户确实已保存
        with Session(self.engine) as db:
            repository = SqlAlchemyUserRepository(db)
            service = UserService(
                user_repository=repository,
                password_hasher=Argon2PasswordService(),
            )

            by_id = service.get_user_by_id(user.id)
            by_username = service.get_user_by_username("player_23")

            self.assertEqual(by_id, user)
            self.assertEqual(by_username, user)
            self.assertEqual(by_id.username, "player_23")
            self.assertEqual(by_id.name, "James")

            # 数据库保存的是哈希，而且能够验证原密码
            self.assertNotEqual(by_id.password_hash, password)
            self.assertTrue(
                PasswordHasher().verify(by_id.password_hash, password)
            )

    # 相同用户名不能重复注册。
    def test_duplicate_username_is_rejected(self):
        with Session(self.engine) as db:
            repository = SqlAlchemyUserRepository(db)
            service = UserService(
                user_repository=repository,
                password_hasher=Argon2PasswordService(),
            )

            service.sign_up(
                username="player_23",
                name="James",
                password="first-password-123",
            )
            db.commit()

            # 第二次注册相同用户名，应抛出异常
            with self.assertRaisesRegex(ValueError, "该用户已存在"):
                service.sign_up(
                    username="player_23",
                    name="Another Player",
                    password="second-password-456",
                )

    # 查询不存在的用户时抛出业务异常。
    def test_missing_user_raises_error(self):
        with Session(self.engine) as db:
            repository = SqlAlchemyUserRepository(db)
            service = UserService(
                user_repository=repository,
                password_hasher=Argon2PasswordService(),
            )

            with self.assertRaisesRegex(ValueError, "用户不存在"):
                service.get_user_by_id(uuid4())

            with self.assertRaisesRegex(ValueError, "用户不存在"):
                service.get_user_by_username("missing")


if __name__ == "__main__":
    unittest.main()