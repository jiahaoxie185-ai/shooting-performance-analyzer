# 处理训练、投篮和统计的业务流程。
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from domain.shooting.entities import ShootingSession,ShootingZone,ShotAttempt,ShotGroup
from application.unit_of_work import UnitOfWork
from domain.shooting.rules import calculate_shooting_summary, calculate_zone_statistics


class ShootingSessionNotFoundError(ValueError):
    """指定的训练不存在。"""


class ShotGroupNotFoundError(ValueError):
    """指定的投篮组不存在。"""


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

    # 在指定训练中创建空投篮组，保存后返回该组
    def add_shot_group(self, session_id: UUID, zone: Optional[ShootingZone] = None) -> ShotGroup:
        with self.uow:
            training = self.uow.shooting_repository.get_session_by_id(session_id)
            if training is None:
                raise ShootingSessionNotFoundError("训练不存在")

            group = training.add_shot_group(zone)
            self.uow.shooting_repository.add_shot_group(group)
            self.uow.commit()

        return group

    # 根据组 ID 读取完整投篮组，不存在时明确报错
    def get_shot_group_by_id(self, group_id: UUID) -> ShotGroup:
        with self.uow:
            group = self.uow.shooting_repository.get_shot_group_by_id(group_id)
            if group is None:
                raise ShotGroupNotFoundError("投篮组不存在")
        return group

    # 查询一场训练中的组列表，不存在的训练不当作空列表
    def list_shot_groups(self, session_id: UUID) -> list[ShotGroup]:
        with self.uow:
            if self.uow.shooting_repository.get_session_by_id(session_id) is None:
                raise ShootingSessionNotFoundError("训练不存在")
            return self.uow.shooting_repository.list_shot_groups(session_id)

    # 单组统计由后端计算，前端直接展示返回结果
    def get_shot_group_summary(self, group_id: UUID) -> dict:
        group = self.get_shot_group_by_id(group_id)
        return calculate_shooting_summary(group.shots)

    # 按数量生成逐球记录，结束本组并整体保存
    def finish_shot_group(self, group_id: UUID, zone: ShootingZone, attempts: int, made: int) -> ShotGroup:
        # 点位必须有效，不能把未选择的空值保存为结束组。
        try:
            zone = ShootingZone(zone)
        except (ValueError, TypeError) as exc:
            raise ValueError("请选择有效的投篮点位") from exc
        if type(attempts) is not int or type(made) is not int:
            raise ValueError("出手数和命中数必须为整数")
        if attempts <= 0 or made < 0 or made > attempts:
            raise ValueError("出手数必须大于零，命中数必须在零和出手数之间")
        with self.uow:
            group = self.uow.shooting_repository.get_shot_group_by_id(group_id)
            if group is None:
                raise ShotGroupNotFoundError("投篮组不存在")

            # 已结束组只允许相同点位和数量重试，不修改原记录。
            if group.ended_at is not None:
                if (group.zone != zone or len(group.shots) != attempts
                        or sum(shot.made for shot in group.shots) != made):
                    raise ValueError("投篮组已结束，不能修改投篮数据")
                return group

            training = self.uow.shooting_repository.get_session_by_id(group.session_id)
            if training is None:
                raise ShootingSessionNotFoundError("训练不存在")
            if training.ended_at is not None:
                raise ValueError("训练已结束，不能提交投篮组")
            if group.shots:
                raise ValueError("投篮组已有记录，不能重复提交")

            # 先设置最终点位，组内每个球使用同一地点。
            group.zone = zone
            # 汇总输入无法还原真实出手顺序；生成顺序仅用于记录命中数量。
            for index in range(attempts):
                group.add_shot(made=index < made)
            group.finish()
            self.uow.shooting_repository.finish_shot_group(group)
            self.uow.commit()

        return group

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

            # 旧接口暂时将一次提交作为一组，仍按原结构保存逐球记录。
            group = training.add_shot_group(zone)
            shot = group.add_shot(made)
            group.finish()
            training.shots.append(shot)

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
