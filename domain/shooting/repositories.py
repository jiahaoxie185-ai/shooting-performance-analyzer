from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .entities import ShootingSession, ShotAttempt

# 训练数据的存取接口，不在这里编写数据库操作
class ShootingRepository(ABC):
    # 保存新训练或更新已有训练，仅保存训练信息；投篮由 add_shot 单独保存
    @abstractmethod
    def save_session(self, session: ShootingSession) ->None:
        pass

    @abstractmethod
    # 单独新增一条投篮记录，训练必须已经存在于数据库事务中
    def add_shot(self, shot: ShotAttempt) ->None:
        pass

    # 根据训练 ID 返回训练及投篮记录；找不到时返回 None
    @abstractmethod
    def get_session_by_id(self, session_id: UUID) -> Optional[ShootingSession]:
        pass

    # 返回用户的所有训练及投篮记录；没有记录时返回空列表
    @abstractmethod
    def list_by_user_id(self,user_id: UUID) ->list[ShootingSession]:
        pass