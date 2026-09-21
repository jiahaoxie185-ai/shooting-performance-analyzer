from datetime import datetime
from typing import Optional
from uuid import UUID


from pydantic import BaseModel, ConfigDict, Field

# 注册请求，校验用户名、姓名和密码长度
class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)


# 用户响应，仅公开这些字段，不包含原始密码和密码哈希
class UserResponse(BaseModel):
    # 允许从领域 User 对象的属性读取响应数据
    model_config = ConfigDict(from_attributes=True)

    id:UUID
    username: str
    name: str
    created_at: datetime
    height: Optional[float] = None
    position: Optional[str] = None


    