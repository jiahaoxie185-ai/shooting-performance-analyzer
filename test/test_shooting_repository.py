# 测试训练仓储的保存与读取。
import unittest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from domain.users.entities import User
from domain.shooting.entities import ShootingSession,ShootingZone
from infrastructure.database import Base, enable_foreign_keys
# 导入模型以注册表结构，供测试建表使用
from infrastructure import models
from infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from infrastructure.repositories.shooting_repository import SqlAlchemyShootingRepository


# 验证训练与投篮的保存、重复保存和查询还原
class TestShootingRepository(unittest.TestCase):
    # 每个测试创建独立内存数据库，并先保存训练所属的用户
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")

        # 测试引擎单独开启外键检查，模拟实际数据库约束
        event.listen(self.engine, "connect", enable_foreign_keys)
        Base.metadata.create_all(self.engine)

        self.user = User(
            id=uuid4(),
            username="player_23",
            name="James",
            password_hash="test_hash",
            created_at=datetime(2026,9,19,10,0)
        )

        with Session(self.engine) as db:
            repo = SqlAlchemyUserRepository(db)
            repo.save_user(self.user)
            db.commit()

    # 每个测试结束后释放数据库连接
    def tearDown(self):
        self.engine.dispose()

    # 保存含两条投篮的训练，再用新会话验证完整领域对象
    def test_save_and_find_session(self):
        training = ShootingSession(
            id= uuid4(),
            user_id=self.user.id,
            started_at=datetime(2026,9,19,11,0),
            shots= [],
            note="篮下训练"
        )

        first_shot = training.add_shot(ShootingZone.PAINT, True)
        second_shot = training.add_shot(ShootingZone.LEFT_CORNER, False)

        # 固定不同的投篮时间，确保查询顺序可预测
        first_shot.attempted_at = datetime(2026,9,19,11,1)
        second_shot.attempted_at = datetime(2026,9,19,11,2)

        with Session(self.engine) as db:
            repo = SqlAlchemyShootingRepository(db)
            repo.save_session(training)
            # 先将训练写入当前事务，满足投篮外键；此时尚未提交
            db.flush()

            # 训练与投篮分开保存，最后统一提交
            repo.add_shot(first_shot)
            repo.add_shot(second_shot)
            db.commit()

        # 不修改训练再次保存，检查不会重复插入或丢失已有投篮
        with Session(self.engine) as db:
            repo = SqlAlchemyShootingRepository(db)
            repo.save_session(training)
            db.commit()

        with Session(self.engine) as db:
            repo = SqlAlchemyShootingRepository(db)
            # 从新会话读取，验证数据库持久化及模型转换
            res_by_id = repo.get_session_by_id(training.id)
            res_list_by_user_id = repo.list_by_user_id(self.user.id)

            self.assertIsNotNone(res_by_id)

            # dataclass 比较包含各个训练字段以及投篮列表
            self.assertEqual(res_by_id, training)
            self.assertEqual(res_list_by_user_id, [training])
            self.assertEqual(len(res_by_id.shots),2)
            self.assertEqual(res_by_id.shots, training.shots)

            

            
