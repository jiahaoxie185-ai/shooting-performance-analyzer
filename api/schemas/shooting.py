# 定义训练接口的请求、响应和统计数据格式。
from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, model_validator

from domain.shooting.entities import ShootingZone

# 开始训练的请求数据：用户 ID 和可选备注
class ShootingSessionCreate(BaseModel):
    user_id: UUID
    note: Optional[str] = Field(default=None, max_length=500)


# 新增投篮的请求数据，训练 ID 由请求路径提供
class ShotAttemptCreate(BaseModel):
    zone: ShootingZone
    made: bool


# 批量录入的数量必须是整数，并且命中数不能超过出手数。
class ShotBatchCreate(BaseModel):
    attempts: int = Field(strict=True, gt=0)
    made: int = Field(strict=True, ge=0)
    zone: ShootingZone

    @model_validator(mode="after")
    def validate_counts(self) -> "ShotBatchCreate":
        if self.made > self.attempts:
            raise ValueError("命中数不能超过出手数")
        return self


# 单次投篮的响应格式，从领域对象读取属性
class ShootingAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    zone: ShootingZone
    made: bool
    attempted_at: datetime

# 训练详情的响应格式，包含嵌套的投篮列表
class ShootingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    note: Optional[str] = None
    shots: list[ShootingAttemptResponse] = Field(default_factory=list)

# 总体或单个区域的基础统计，命中率用 0～1 表示
class ShootingStatistics(BaseModel):
    attempts: int
    made: int
    field_goals: float

# 完整统计响应，在基础统计上增加各区域的统计字典
class ShootingSummaryResponse(ShootingStatistics):
    zones: dict[str, ShootingStatistics]

