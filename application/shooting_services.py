from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.shooting.entities import ShootingSession,ShootingZone,ShotAttempt
from application.unit_of_work import UnitOfWork
from domain.shooting.rules import calculate_shooting_summary, calculate_zone_statistics


# 组织训练业务，复用领域规则；当前由外部管理事务
class ShootingService:
    # 保存外部传入的 Repository，实现类在组装时确定
    def __init__(
        self,
        uow: UnitOfWork
    ):
        self.uow = uow

    # 确认用户存在，创建训练并交给 Repository 保存
    def start_session(
            self,
            user_id:UUID,
            note:Optional[str] = None
        ) -> ShootingSession:

        with self.uow:
            user = self.uow.user_repository.get_user_by_id(user_id)

            if user is None:
                raise ValueError("用户不存在")

            training = ShootingSession(
                id=uuid4(),
                user_id=user_id,
                started_at=datetime.now(),
                note=note
            )

            self.uow.shooting_repository.save_session(training)
            self.uow.commit()

        return training

    # 查询训练，由实体检查状态并创建投篮，再单独保存投篮
    def add_shot(
            self,
            session_id:UUID,
            zone:ShootingZone,
            made:bool 
    ) -> ShotAttempt:

        with self.uow:
            training = self.uow.shooting_repository.get_session_by_id(session_id)

            if training is None:
                raise ValueError("训练不存在")

            shot = training.add_shot(zone, made)

            self.uow.shooting_repository.add_shot(shot)
            self.uow.commit()

        return shot

    # 由实体记录结束时间，再保存训练状态的变化
    def finish_session(
            self,
            session_id:UUID
    ) -> ShootingSession:

        with self.uow:
            training = self.uow.shooting_repository.get_session_by_id(session_id)

            if training is None:
                raise ValueError("训练不存在")

            training.finish()

            self.uow.shooting_repository.save_session(training)
            self.uow.commit()

        return training

    # 取得包含投篮记录的训练，不存在时抛出异常
    def get_session(self,session_id:UUID) -> ShootingSession:
        with self.uow:
            training = self.uow.shooting_repository.get_session_by_id(session_id)

            if training is None:
                raise ValueError("该训练不存在")

        return training

    # 确认用户存在，再查询其全部训练；没有训练时返回空列表
    def list_sessions(self, user_id:UUID) -> list[ShootingSession]:
        with self.uow:
            user = self.uow.user_repository.get_user_by_id(user_id)

            if user is None:
                raise ValueError("用户不存在")

            trainings = self.uow.shooting_repository.list_by_user_id(user_id)
        return trainings

    # 取得单次训练的投篮，计算总体及各区域统计
    def get_session_summary(self, session_id: UUID) -> dict:
        training = self.get_session(session_id)

        summary = calculate_shooting_summary(training.shots)

        # 将区域统计字典嵌入总体统计结果
        summary["zones"] = calculate_zone_statistics(training.shots)

        return summary

    # 合并用户所有训练的投篮后计算，不能直接平均各场命中率
    def get_user_summary(self, user_id:UUID) -> dict:
        trainings = self.list_sessions(user_id)

        all_shots = []

        for training in trainings:

            # 逐条合并完整投篮对象，区域、结果和时间等信息仍保留
            all_shots.extend(training.shots)

        summary = calculate_shooting_summary(all_shots)
        # 将区域统计字典嵌入总体统计结果
        summary["zones"] = calculate_zone_statistics(all_shots)

        return summary