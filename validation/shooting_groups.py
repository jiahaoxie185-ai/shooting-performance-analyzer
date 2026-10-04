"""验证投篮组接口、保存和事务回滚。"""
import asyncio
import json
import unittest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.dependencies import get_shooting_service
from application.shooting_services import ShootingService
from infrastructure.database import Base, enable_foreign_keys
from infrastructure.models import UserModel, ShotGroupModel
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from main import app


async def request(method, path, payload=None):
    """直接调用 ASGI 应用，验证真实路由、请求校验及响应序列化。"""
    body = json.dumps(payload).encode() if payload is not None else b""
    messages = []

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await app(
        {
            "type": "http", "asgi": {"version": "3.0"},
            "http_version": "1.1", "method": method, "scheme": "http",
            "path": path, "raw_path": path.encode(), "query_string": b"",
            "root_path": "", "headers": [(b"content-type", b"application/json")],
            "client": ("127.0.0.1", 1234), "server": ("test", 80),
        },
        receive,
        send,
    )
    status = next(item["status"] for item in messages if item["type"] == "http.response.start")
    response = b"".join(item.get("body", b"") for item in messages if item["type"] == "http.response.body")
    return status, json.loads(response)


class ShootingGroupValidation(unittest.TestCase):
    # 为每个用例创建独立内存数据库，并替换接口使用的服务。
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        event.listen(self.engine, "connect", enable_foreign_keys)
        Base.metadata.create_all(self.engine)
        factory = sessionmaker(bind=self.engine)
        self.service = ShootingService(SqlAlchemyUnitOfWork(factory))
        app.dependency_overrides[get_shooting_service] = lambda: self.service
        self.user_id = uuid4()
        with factory() as db:
            db.add(UserModel(
                id=self.user_id, username="demo", name="Demo",
                password_hash="validation-only", created_at=datetime.now(),
            ))
            db.commit()
        status, data = self.call("POST", "/sessions", {"user_id": str(self.user_id)})
        self.assertEqual(status, 201)
        self.path = f"/sessions/{data['id']}"

    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    def call(self, method, path, payload=None):
        return asyncio.run(request(method, path, payload))

    # 新组返回独立 ID，空记录与未结束状态，并实际保存到数据库。
    def test_create_shot_group(self):
        from uuid import UUID
        from sqlalchemy.orm import Session
        status, data = self.call("POST", self.path + "/shot-groups", {})
        self.assertEqual(status, 201)
        self.assertEqual(data["session_id"], self.path.split("/")[-1])
        self.assertEqual(data["shots"], [])
        self.assertIsNone(data["ended_at"])
        self.assertIsNone(data["zone"])
        with Session(self.engine) as db:
            stored = db.get(ShotGroupModel, UUID(data["id"]))
            self.assertIsNotNone(stored)
            self.assertIsNone(stored.zone)
        status, second = self.call("POST", self.path + "/shot-groups")
        self.assertEqual(status, 201)
        self.assertNotEqual(second["id"], data["id"])

    # 按 ID 获取正确组，已结束记录完整还原，不影响其他组。
    def test_get_shot_group_by_id(self):
        _, first = self.call("POST", self.path + "/shot-groups", {})
        _, second = self.call("POST", self.path + "/shot-groups", {"zone": "top_three"})
        path = f"/sessions/shot-groups/{first['id']}"
        status, result = self.call("GET", path)
        self.assertEqual(status, 200)
        self.assertEqual(result, first)
        self.assertEqual(self.call("GET", path + "/summary")[1],
                         {"attempts": 0, "made": 0, "field_goals": 0.0})
        _, finished = self.call("POST", path + "/finish", {"zone": "paint", "attempts": 20, "made": 14})
        status, result = self.call("GET", path)
        self.assertEqual(status, 200)
        self.assertEqual(result, finished)
        self.assertEqual(self.call("GET", path + "/summary")[1],
                         {"attempts": 20, "made": 14, "field_goals": 0.7})
        self.assertEqual(self.call("GET", f"/sessions/shot-groups/{uuid4()}/summary")[0], 404)
        self.assertEqual(self.call("GET", f"/sessions/shot-groups/{second['id']}")[1], second)
        self.assertEqual(self.call("GET", f"/sessions/shot-groups/{uuid4()}")[0], 404)
        self.assertEqual(self.call("GET", "/sessions/shot-groups/invalid")[0], 422)

    # 列表只返回本场组，保留进行中与已结束状态。
    def test_list_shot_groups(self):
        path = self.path + "/shot-groups"
        self.assertEqual(self.call("GET", path), (200, []))
        _, first = self.call("POST", path, {"zone": "paint"})
        _, second = self.call("POST", path, {})
        _, finished = self.call("POST", f"/sessions/shot-groups/{first['id']}/finish",
                                {"zone": "paint", "attempts": 20, "made": 14})
        _, other = self.call("POST", "/sessions", {"user_id": str(self.user_id)})
        self.call("POST", f"/sessions/{other['id']}/shot-groups", {"zone": "paint"})
        status, groups = self.call("GET", path)
        self.assertEqual(status, 200)
        self.assertEqual(groups, [finished, second])
        self.assertEqual(self.call("GET", f"/sessions/{uuid4()}/shot-groups")[0], 404)

    # 不存在或已结束的训练、无效点位不能创建组。
    def test_create_shot_group_rejections(self):
        status, _ = self.call("POST", f"/sessions/{uuid4()}/shot-groups", {"zone": "paint"})
        self.assertEqual(status, 404)
        status, _ = self.call("POST", self.path + "/shot-groups", {"zone": "invalid"})
        self.assertEqual(status, 422)
        self.call("POST", self.path + "/finish")
        status, _ = self.call("POST", self.path + "/shot-groups", {"zone": "paint"})
        self.assertEqual(status, 400)

    # 结束组实际落库、重复结束不变，且不结束所属训练。
    def test_finish_shot_group(self):
        from uuid import UUID
        from sqlalchemy.orm import Session
        _, group = self.call("POST", self.path + "/shot-groups", {})
        finish_path = f"/sessions/shot-groups/{group['id']}/finish"
        status, finished = self.call("POST", finish_path, {"zone": "top_three", "attempts": 20, "made": 14})
        self.assertEqual(status, 200)
        self.assertIsNotNone(finished["ended_at"])
        self.assertEqual(len(finished["shots"]), 20)
        self.assertEqual(sum(shot["made"] for shot in finished["shots"]), 14)
        self.assertEqual(len({shot["id"] for shot in finished["shots"]}), 20)
        self.assertEqual(finished["zone"], "top_three")
        self.assertTrue(all(shot["zone"] == "top_three" for shot in finished["shots"]))
        self.assertEqual(self.call("POST", finish_path, {"zone": "paint", "attempts": 20, "made": 14})[0], 400)
        self.assertEqual(finished["started_at"], group["started_at"])
        status, repeated = self.call("POST", finish_path, {"zone": "top_three", "attempts": 20, "made": 14})
        self.assertEqual(status, 200)
        self.assertEqual(repeated, finished)
        self.assertEqual(self.call("POST", finish_path, {"zone": "top_three", "attempts": 21, "made": 14})[0], 400)
        with Session(self.engine) as db:
            self.assertEqual(db.get(ShotGroupModel, UUID(group["id"])).ended_at.isoformat(), finished["ended_at"])
        with self.service.uow:
            stored = self.service.uow.shooting_repository.get_shot_group_by_id(UUID(group["id"]))
            with self.assertRaises(ValueError):
                stored.add_shot(True)
        _, training = self.call("GET", self.path)
        self.assertIsNone(training["ended_at"])
        status, _ = self.call("POST", f"/sessions/shot-groups/{uuid4()}/finish", {"zone": "top_three", "attempts": 20, "made": 14})
        self.assertEqual(status, 404)

    # 组内记录以 JSON 完整保存，已结束组的记录不能覆盖。
    def test_finish_group_preserves_shots(self):
        from uuid import UUID
        _, data = self.call("POST", self.path + "/shot-groups", {"zone": "paint"})
        with self.service.uow:
            repo = self.service.uow.shooting_repository
            group = repo.get_shot_group_by_id(UUID(data["id"]))
            shots = [group.add_shot(True), group.add_shot(False)]
            group.finish()
            repo.finish_shot_group(group)
            self.service.uow.commit()
        with self.service.uow:
            repo = self.service.uow.shooting_repository
            restored = repo.get_shot_group_by_id(group.id)
            self.assertEqual(restored.shots, shots)
            self.assertEqual(restored.ended_at, group.ended_at)
            restored.shots.clear()
            repo.finish_shot_group(restored)
            self.service.uow.commit()
        with self.service.uow:
            self.assertEqual(self.service.uow.shooting_repository.get_shot_group_by_id(group.id).shots, shots)
        status, response = self.call("POST", f"/sessions/shot-groups/{group.id}/finish", {"zone": "paint", "attempts": 2, "made": 1})
        self.assertEqual(status, 200)
        self.assertEqual([shot["id"] for shot in response["shots"]], [str(shot.id) for shot in shots])

    # 未提交的组结束和 JSON 数据应一起回滚。
    def test_finish_group_rollback(self):
        from uuid import UUID
        _, data = self.call("POST", self.path + "/shot-groups", {"zone": "paint"})
        with self.service.uow:
            repo = self.service.uow.shooting_repository
            group = repo.get_shot_group_by_id(UUID(data["id"]))
            group.add_shot(True)
            group.finish()
            repo.finish_shot_group(group)
            self.service.uow.db.flush()
        with self.service.uow:
            restored = self.service.uow.shooting_repository.get_shot_group_by_id(group.id)
            self.assertIsNone(restored.ended_at)
            self.assertEqual(restored.shots, [])

    # 无效数量不结束组，不留下记录；整场结束后不能再提交本组。
    def test_finish_group_invalid_counts(self):
        from uuid import UUID
        _, group = self.call("POST", self.path + "/shot-groups", {"zone": "paint"})
        path = f"/sessions/shot-groups/{group['id']}/finish"
        for payload in [None, {}, {"attempts": 2, "made": 1},
                        {"zone": None, "attempts": 2, "made": 1},
                        {"zone": "invalid", "attempts": 2, "made": 1}, {"zone": "paint", "attempts": 2}, {"zone": "paint", "attempts": 0, "made": 0},
                        {"zone": "paint", "attempts": 2, "made": -1}, {"zone": "paint", "attempts": 2, "made": 3},
                        {"zone": "paint", "attempts": True, "made": 1}, {"zone": "paint", "attempts": 2, "made": False},
                        {"zone": "paint", "attempts": "2", "made": 1}, {"zone": "paint", "attempts": 2.5, "made": 1}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.call("POST", path, payload)[0], 422)
        with self.service.uow:
            stored = self.service.uow.shooting_repository.get_shot_group_by_id(UUID(group["id"]))
            self.assertIsNone(stored.ended_at)
            self.assertEqual(stored.shots, [])
        self.call("POST", self.path + "/finish")
        self.assertEqual(self.call("POST", path, {"zone": "paint", "attempts": 2, "made": 1})[0], 400)

    def test_finish_group_count_boundaries(self):
        for made in [0, 3]:
            _, group = self.call("POST", self.path + "/shot-groups", {"zone": "paint"})
            status, result = self.call("POST", f"/sessions/shot-groups/{group['id']}/finish",
                                       {"zone": "paint", "attempts": 3, "made": made})
            self.assertEqual(status, 200)
            self.assertEqual(len(result["shots"]), 3)
            self.assertEqual(sum(shot["made"] for shot in result["shots"]), made)

    # 保存中途失败时，生成的记录和结束状态整体回滚。
    def test_finish_group_storage_failure(self):
        from uuid import UUID
        from unittest.mock import patch
        from infrastructure.repositories.shooting_repository import SqlAlchemyShootingRepository
        _, group = self.call("POST", self.path + "/shot-groups", {})
        original = SqlAlchemyShootingRepository.finish_shot_group

        def fail(repository, value):
            original(repository, value)
            repository.db.flush()
            raise RuntimeError("simulated storage failure")

        with patch.object(SqlAlchemyShootingRepository, "finish_shot_group", fail):
            with self.assertRaisesRegex(RuntimeError, "simulated storage failure"):
                self.call("POST", f"/sessions/shot-groups/{group['id']}/finish",
                          {"zone": "paint", "attempts": 20, "made": 14})
        with self.service.uow:
            stored = self.service.uow.shooting_repository.get_shot_group_by_id(UUID(group["id"]))
            self.assertIsNone(stored.ended_at)
            self.assertIsNone(stored.zone)
            self.assertEqual(stored.shots, [])

    # 空组不能直接生成投篮或结束，必须先选择点位。
    def test_empty_group_requires_zone(self):
        from domain.shooting.entities import ShotGroup
        group = ShotGroup(id=uuid4(), session_id=uuid4(), started_at=datetime.now())
        with self.assertRaises(ValueError):
            group.add_shot(True)
        with self.assertRaises(ValueError):
            group.finish()
        self.assertEqual(group.shots, [])
        self.assertIsNone(group.ended_at)

    # 旧批量接口已经移除，单球接口和统计仍能正常工作。
    def test_removed_batch_and_single_shot(self):
        self.assertEqual(self.call("POST", self.path + "/shots/batch", {
            "attempts": 20, "made": 14, "zone": "paint",
        })[0], 404)
        self.assertFalse(hasattr(self.service, "add_shots"))
        self.assertEqual(self.call("POST", self.path + "/shots", {
            "zone": "paint", "made": True,
        })[0], 201)
        status, summary = self.call("GET", self.path + "/summary")
        self.assertEqual(status, 200)
        self.assertEqual((summary["attempts"], summary["made"]), (1, 1))
        self.assertEqual(summary["field_goals"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
