import unittest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from domain.users.entities import User
from infrastructure.database import Base
from infrastructure import models
from infrastructure.repositories.user_repository import SqlAlchemyUserRepository


# 验证用户保存、读取和查不到用户时的返回值
class TestUserRepositoy(unittest.TestCase):
    # 每个测试使用独立的内存数据库，避免影响正式数据库和其他测试
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    # 测试结束后释放数据库连接
    def tearDown(self):
        self.engine.dispose()

    # 先提交用户，再用新会话查询；dataclass 比较会检查所有字段
    def test_save_and_find_user(self):
        user = User(
            id=uuid4(),
            username="player_23",
            name="james",
            password_hash="test_hash",
            created_at=datetime(2026,9,18,10,0),
            height=185.0,
            position="pointguard",
        )

        with Session(self.engine) as db:
            repo = SqlAlchemyUserRepository(db)
            repo.save_user(user)
            db.commit()

        with Session(self.engine) as db:
            repo = SqlAlchemyUserRepository(db)
            by_id = repo.get_user_by_id(user.id)
            by_username = repo.get_user_by_username(username=user.username)


            self.assertEqual(by_id,user)
            self.assertEqual(by_username,user)

    # 用不存在的 ID 和用户名查询，验证返回 None
    def test_missing_user_returns_none(self):
        with Session(self.engine) as db:
            repo = SqlAlchemyUserRepository(db)

            self.assertIsNone(repo.get_user_by_id(uuid4()))
            self.assertIsNone(repo.get_user_by_username(username="missing"))


if __name__ == "__main__":
    unittest.main()