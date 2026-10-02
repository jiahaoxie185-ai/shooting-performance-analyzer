"""验证新增接口及事务回滚；从 TLJH 运行 python -m validation.shooting_batch。"""
import asyncio
import json
import unittest
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.dependencies import get_shooting_service
from application.shooting_services import ShootingService
from infrastructure.database import Base, enable_foreign_keys
from infrastructure.models import UserModel
from infrastructure.repositories.shooting_repository import SqlAlchemyShootingRepository
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


class ShootingBatchValidation(unittest.TestCase):
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

    def batch(self, attempts=20, made=14, zone="top_three"):
        return self.call("POST", self.path + "/shots/batch", {
            "attempts": attempts, "made": made, "zone": zone,
        })

    def test_append_and_existing_interfaces(self):
        status, data = self.call("GET", self.path)
        self.assertEqual(status, 200)
        self.assertEqual(data["shots"], [])
        status, data = self.batch()
        self.assertEqual(status, 201)
        self.assertEqual(len(data["shots"]), 20)
        self.assertEqual(sum(shot["made"] for shot in data["shots"]), 14)
        self.assertTrue(all(shot["zone"] == "top_three" for shot in data["shots"]))
        ids = {shot["id"] for shot in data["shots"]}
        self.assertEqual(len(ids), 20)
        status, data = self.batch(10, 6)
        self.assertEqual(status, 201)
        self.assertEqual(len(data["shots"]), 30)
        self.assertTrue(ids.issubset({shot["id"] for shot in data["shots"]}))
        status, data = self.call("GET", self.path + "/summary")
        self.assertEqual(status, 200)
        self.assertEqual((data["attempts"], data["made"]), (30, 20))
        self.assertAlmostEqual(data["field_goals"], 20 / 30)
        status, data = self.call("GET", f"/sessions/users/{self.user_id}")
        self.assertEqual(status, 200)
        self.assertEqual(len(data[0]["shots"]), 30)
        status, data = self.call("GET", f"/sessions/users/{self.user_id}/summary")
        self.assertEqual(status, 200)
        self.assertEqual(data["attempts"], 30)
        status, _ = self.call("POST", self.path + "/shots", {"zone": "paint", "made": True})
        self.assertEqual(status, 201)
        self.assertEqual(len(self.call("GET", self.path)[1]["shots"]), 31)

    def test_zero_and_all_made(self):
        self.assertEqual(self.batch(3, 0)[0], 201)
        status, data = self.batch(3, 3)
        self.assertEqual(status, 201)
        self.assertEqual(len(data["shots"]), 6)
        self.assertEqual(sum(shot["made"] for shot in data["shots"]), 3)

    def test_invalid_inputs_leave_no_records(self):
        invalid_counts = [(0, 0), (-1, 0), (2, -1), (2, 3), (2.5, 1), (2, 1.5),
                          (True, 0), (2, False), ("2", 1), (2, "1"), (None, 1)]
        for attempts, made in invalid_counts:
            with self.subTest(attempts=attempts, made=made):
                self.assertEqual(self.batch(attempts, made)[0], 422)
        self.assertEqual(self.batch(zone="invalid")[0], 422)
        self.assertEqual(self.call("POST", self.path + "/shots/batch", {"attempts": 2, "made": 1})[0], 422)
        self.assertEqual(self.call("GET", "/sessions/invalid")[0], 422)
        self.assertEqual(self.call("POST", "/sessions/invalid/shots/batch", {
            "attempts": 2, "made": 1, "zone": "paint",
        })[0], 422)
        self.assertEqual(self.call("GET", self.path)[1]["shots"], [])

    def test_missing_and_finished_session(self):
        missing = f"/sessions/{uuid4()}"
        self.assertEqual(self.call("GET", missing)[0], 404)
        self.assertEqual(self.call("POST", missing + "/shots/batch", {
            "attempts": 2, "made": 1, "zone": "paint",
        })[0], 404)
        status, data = self.call("POST", self.path + "/finish")
        self.assertEqual(status, 200)
        ended_at = data["ended_at"]
        self.assertEqual(self.batch()[0], 400)
        status, data = self.call("GET", self.path)
        self.assertEqual(status, 200)
        self.assertEqual(data["shots"], [])
        self.assertEqual(data["ended_at"], ended_at)
        self.assertEqual(self.call("POST", self.path + "/finish")[1]["ended_at"], ended_at)

    def test_failure_rolls_back_flushed_records(self):
        self.batch(2, 1)
        original = SqlAlchemyShootingRepository.add_shot
        count = 0

        def failing_add(repository, shot):
            nonlocal count
            count += 1
            if count == 3:
                raise RuntimeError("simulated storage failure")
            original(repository, shot)
            repository.db.flush()

        with patch.object(SqlAlchemyShootingRepository, "add_shot", failing_add):
            with self.assertRaisesRegex(RuntimeError, "simulated storage failure"):
                self.batch()
        data = self.call("GET", self.path)[1]
        self.assertEqual(len(data["shots"]), 2)
        self.assertEqual(sum(shot["made"] for shot in data["shots"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
