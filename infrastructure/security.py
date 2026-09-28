# 使用 Argon2 生成密码哈希。
from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError


# 密码哈希接口的实际实现，封装 Argon2 第三方库
class Argon2PasswordService:
    # 创建 Argon2 哈希组件，采用库的默认配置
    def __init__(self):
        self.hasher = Argon2PasswordHasher()

    # 由 Argon2 生成随机盐和密码哈希，返回可存储的字符串
    def hash(self, password: str) -> str:
        return self.hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self.hasher.verify(password_hash, password)
        except (InvalidHashError, VerificationError):
            return False

    