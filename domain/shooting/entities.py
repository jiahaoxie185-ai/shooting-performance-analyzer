# 定义投篮区域、投篮记录、投篮组和训练实体。
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

# 一组投篮，保存所属训练、点位和组内投篮记录
@dataclass
class ShotGroup:
    id: UUID
    session_id: UUID
    started_at: datetime
    # 空组暂时没有点位，结束前必须选择
    zone: Optional[ShootingZone] = None
    ended_at: Optional[datetime] = None
    # 每组拥有独立列表；没有结束时间表示本组进行中
    shots: list[ShotAttempt] = field(default_factory=list)

    # 检查本组状态，创建投篮并加入组内列表
    def add_shot(self, made: bool) -> ShotAttempt:
        if self.ended_at is not None:
            raise ValueError("Shot group is over, can't add a shot")
        if self.zone is None:
            raise ValueError("请先选择投篮点位")
        shot = ShotAttempt(
            id=uuid4(),
            session_id=self.session_id,
            zone=self.zone,
            made=made,
            attempted_at=datetime.now()
        )
        self.shots.append(shot)
        return shot

    # 结束本组；重复结束保留第一次的时间
    def finish(self) -> None:
        if self.ended_at is not None:
            return
        if self.zone is None:
            raise ValueError("结束投篮组前必须选择点位")
        self.ended_at = datetime.now()

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
    # 保存本场的投篮组；现有 shots 暂时保留，等待仓储和接口适配
    groups: list[ShotGroup] = field(default_factory=list)

    # 已结束的训练不能创建组；逐球添加由组负责
    def add_shot_group(self, zone: Optional[ShootingZone] = None) -> ShotGroup:
        if self.ended_at is not None:
            raise ValueError("Training is over, can't add a shot group")
        group = ShotGroup(
            id=uuid4(),
            session_id=self.id,
            zone=zone,
            started_at=datetime.now()
        )
        self.groups.append(group)
        return group

    # 记录结束时间；重复调用时保留第一次的结束时间
    def finish(self) -> None:
        if self.ended_at is not None:
            return
        self.ended_at = datetime.now()
