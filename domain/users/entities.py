from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional


# 用户领域实体，只保存业务数据，不依赖数据库
@dataclass
class User:
    id: UUID
    username:str
    name:str
    password_hash:str
    created_at:datetime
    height:Optional[float] = None
    position:Optional[str] = None