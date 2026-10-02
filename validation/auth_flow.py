"""独立认证验收：直接调用 ASGI，使用临时 SQLite，不读取现有 test/。"""
import asyncio
import hashlib
import json
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from http.cookies import SimpleCookie
from pathlib import Path
from uuid import UUID

from argon2 import PasswordHasher
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from api.dependencies import get_user_service
from application.user_services import UserService
from infrastructure.database import Base, enable_foreign_keys
from infrastructure.models import AuthSession, UserModel
from infrastructure.security import Argon2PasswordService
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from main import app


async def request(method, path, body=None, cookie=None):
    payload = json.dumps(body).encode() if body is not None else b""
    headers = [(b"content-type", b"application/json")]
    if cookie:
        headers.append((b"cookie", cookie.encode()))
    messages = []

    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}

    async def send(message):
        messages.append(message)

    await app({
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
        "query_string": b"", "headers": headers, "root_path": "",
        "server": ("localhost", 8000), "client": ("127.0.0.1", 12345),
    }, receive, send)
    start = next(item for item in messages if item["type"] == "http.response.start")
    data = b"".join(item.get("body", b"") for item in messages if item["type"] == "http.response.body")
    return start["status"], dict(start["headers"]), json.loads(data)


class AuthFlow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.temp.name) / 'auth.db'}", connect_args={"check_same_thread": False})
        event.listen(self.engine, "connect", enable_foreign_keys)
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine)
        self.overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_user_service] = lambda: UserService(
            SqlAlchemyUnitOfWork(self.factory), Argon2PasswordService())

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.overrides)
        self.engine.dispose()
        self.temp.cleanup()

    def call(self, method, path, body=None, cookie=None):
        return asyncio.run(request(method, path, body, cookie))

    def register(self, username="player_a"):
        status, _, user = self.call("POST", "/users", {
            "username": username, "name": username + "姓名", "password": "password-123"})
        self.assertEqual(status, 201)
        self.assertNotIn("password", user)
        self.assertNotIn("password_hash", user)
        return user

    def login(self, username="player_a"):
        status, headers, user = self.call("POST", "/auth/login", {
            "username": username, "password": "password-123"})
        self.assertEqual(status, 200)
        cookie = SimpleCookie()
        cookie.load(headers[b"set-cookie"].decode())
        value = cookie["session_token"]
        self.assertTrue(value["httponly"])
        self.assertEqual(value["path"], "/")
        self.assertEqual(value["max-age"], "604800")
        self.assertEqual(value["samesite"], "lax")
        return user, "session_token=" + value.value, value.value

    def test_registration_persists_password_hash_and_survives_new_connections(self):
        user = self.register()
        with self.factory() as db:
            row = db.get(UserModel, UUID(user["id"]))
            self.assertEqual(row.username, user["username"])
            self.assertNotEqual(row.password_hash, "password-123")
            self.assertTrue(PasswordHasher().verify(row.password_hash, "password-123"))
        self.engine.dispose()
        logged_in, _, _ = self.login()
        self.assertEqual(logged_in["id"], user["id"])

    def test_registration_survives_backend_process_restart(self):
        script = """
import asyncio, sys
from validation.auth_flow import request
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from infrastructure.database import enable_foreign_keys
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from infrastructure.security import Argon2PasswordService
from application.user_services import UserService
from api.dependencies import get_user_service
from main import app
engine = create_engine(sys.argv[1], connect_args={'check_same_thread': False})
event.listen(engine, 'connect', enable_foreign_keys)
factory = sessionmaker(bind=engine)
app.dependency_overrides[get_user_service] = lambda: UserService(SqlAlchemyUnitOfWork(factory), Argon2PasswordService())
body = {'username': 'restart_player', 'password': 'password-123'}
if sys.argv[2] == 'register':
    body['name'] = '持久化用户'
    status, _, user = asyncio.run(request('POST', '/users', body))
    assert status == 201
else:
    status, _, user = asyncio.run(request('POST', '/auth/login', body))
    assert status == 200
print(user['id'])
engine.dispose()
"""
        ids = []
        for mode in ("register", "login"):
            result = subprocess.run(
                [sys.executable, "-B", "-c", script, str(self.engine.url), mode],
                cwd=Path(__file__).resolve().parent.parent,
                capture_output=True, text=True, check=True,
            )
            ids.append(result.stdout.strip())
        self.assertEqual(ids[0], ids[1])

    def test_duplicate_and_invalid_registration_do_not_create_users(self):
        self.register()
        for body, expected in [
            ({"username": "player_a", "name": "重复", "password": "password-123"}, 409),
            ({"username": "player_b", "name": "玩家", "password": "short"}, 422),
            ({"username": "", "name": "玩家", "password": "password-123"}, 422),
        ]:
            self.assertEqual(self.call("POST", "/users", body)[0], expected)
        with self.factory() as db:
            self.assertEqual(len(db.scalars(select(UserModel)).all()), 1)

    def test_two_accounts_receive_their_own_user_and_session(self):
        for username in ("player_a", "player_b"):
            registered = self.register(username)
            logged_in, cookie, token = self.login(username)
            self.assertEqual(logged_in, registered)
            status, _, restored = self.call("GET", "/auth/me", cookie=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(restored, registered)
            with self.factory() as db:
                row = db.get(AuthSession, hashlib.sha3_256(token.encode()).hexdigest())
                self.assertEqual(str(row.user_id), registered["id"])
                self.assertNotEqual(row.token_hash, token)
                self.assertGreater(row.expires_at, int(time.time()))

    def test_bad_credentials_do_not_create_sessions(self):
        self.register()
        for username in ("player_a", "missing"):
            status, headers, _ = self.call("POST", "/auth/login", {
                "username": username, "password": "wrong-password"})
            self.assertEqual(status, 401)
            self.assertNotIn(b"set-cookie", headers)
        with self.factory() as db:
            self.assertEqual(db.scalars(select(AuthSession)).all(), [])

    def test_missing_invalid_and_expired_session(self):
        self.assertEqual(self.call("GET", "/auth/me")[0], 401)
        self.assertEqual(self.call("GET", "/auth/me", cookie="session_token=invalid")[0], 401)
        self.register()
        _, cookie, token = self.login()
        with self.factory() as db:
            row = db.get(AuthSession, hashlib.sha3_256(token.encode()).hexdigest())
            row.expires_at = int(time.time()) - 1
            db.commit()
        self.assertEqual(self.call("GET", "/auth/me", cookie=cookie)[0], 401)

    def test_logout_revokes_cookie_and_original_session(self):
        self.register()
        _, cookie, _ = self.login()
        status, headers, data = self.call("POST", "/auth/logout", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(data, {"message": "已退出登录"})
        self.assertIn(b"Max-Age=0", headers[b"set-cookie"])
        self.assertEqual(self.call("GET", "/auth/me", cookie=cookie)[0], 401)
        self.assertEqual(self.call("POST", "/auth/logout")[0], 200)
        with self.factory() as db:
            self.assertEqual(db.scalars(select(AuthSession)).all(), [])

    def test_secure_cookie_configuration_and_no_store(self):
        self.register()
        for setting, expected in (("false", False), ("true", True)):
            with patch.dict("os.environ", {"COOKIE_SECURE": setting}):
                status, headers, _ = self.call("POST", "/auth/login", {
                    "username": "player_a", "password": "password-123"})
                self.assertEqual(status, 200)
                cookie = SimpleCookie()
                cookie.load(headers[b"set-cookie"].decode())
                self.assertEqual(bool(cookie["session_token"]["secure"]), expected)
                self.assertEqual(headers[b"cache-control"], b"no-store")
                pair = "session_token=" + cookie["session_token"].value
                status, headers, _ = self.call("GET", "/auth/me", cookie=pair)
                self.assertEqual(status, 200)
                self.assertEqual(headers[b"cache-control"], b"no-store")
                status, headers, _ = self.call("POST", "/auth/logout", cookie=pair)
                self.assertEqual(status, 200)
                cleared = SimpleCookie()
                cleared.load(headers[b"set-cookie"].decode())
                self.assertEqual(bool(cleared["session_token"]["secure"]), expected)
                self.assertEqual(cleared["session_token"]["path"], "/")
                self.assertEqual(headers[b"cache-control"], b"no-store")

    def test_session_without_associated_user_is_rejected(self):
        self.register()
        _, cookie, _ = self.login()
        # 模拟遗失关联用户，保留真实有效会话；不关闭数据库外键约束。
        with patch("infrastructure.repositories.user_repository.SqlAlchemyUserRepository.get_user_by_id", return_value=None):
            status, headers, data = self.call("GET", "/auth/me", cookie=cookie)
        self.assertEqual(status, 401)
        self.assertEqual(data["detail"], "登录已失效")
        self.assertEqual(headers[b"cache-control"], b"no-store")


if __name__ == "__main__":
    unittest.main()
