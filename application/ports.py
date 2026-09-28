# 定义业务层需要的密码哈希能力。
from typing import Protocol


# 密码哈希接口，约定能力，具体算法由外部组件提供
class PasswordHasher(Protocol):
    # 输入原始密码，返回可存储的密码哈希字符串
    def hash(self, password: str) -> str:
        pass

    def verify(self, password_hash: str, password: str) -> bool:
        pass