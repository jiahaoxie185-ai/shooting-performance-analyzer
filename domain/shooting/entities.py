# 定义投篮区域、投篮记录和训练实体。
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from typing import Optional


# 固定的投篮区域，枚举值用于数据存储和传输
class ShootingZone(str, Enum):
    PAINT = "paint"
    LEFT_MIDRANGE = "left_midrange"
    RIGHT_MIDRANGE = "right_midrange"
    TOP_MIDRANGE = "top_midrange"
    LEFT_CORNER = "left_corner"
    RIGHT_CORNER = "right_corner"
    TOP_THREE = "top_three"

# 单次投篮记录；dataclass 自动生成初始化等方法
@dataclass
class ShotAttempt:
    id: UUID
    session_id: UUID
    zone: ShootingZone
    made: bool
    attempted_at: datetime

# 一次训练，保存所属用户、时间及投篮记录
@dataclass
class ShootingSession:
    id: UUID
    user_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    note: Optional[str] = None
    # 每次训练拥有独立的空列表，避免不同训练共享记录
    shots: list[ShotAttempt] = field(default_factory=list)

    # 检查训练状态，创建投篮并加入列表，返回该记录供后续保存
    def add_shot(self,zone: ShootingZone, made: bool) -> ShotAttempt:
        # 已结束的训练不允许继续添加投篮
        if self.ended_at is not None:
            raise ValueError("Training is over, cant add a shot")
        shot = ShotAttempt(
            id = uuid4(),
            session_id=self.id,
            zone= zone,
            made= made,
            attempted_at= datetime.now()
        )
        self.shots.append(shot)
        # 返回新投篮对象，供 Application 调用 Repository 单独保存
        return shot

    # 记录结束时间；重复调用时保留第一次的结束时间
    def finish(self) -> None:
        if self.ended_at is not None:
            return
        self.ended_at = datetime.now()
        




    