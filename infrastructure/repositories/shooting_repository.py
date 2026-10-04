# 实现训练和投篮记录的数据库存取。
from sqlalchemy.orm import Session
from sqlalchemy import select

from typing import Optional
from uuid import UUID
from datetime import datetime

from domain.shooting.repositories import ShootingRepository
from domain.shooting.entities import ShootingSession, ShotAttempt, ShotGroup, ShootingZone
from infrastructure.models import ShootingSessionModel, ShotAttemptModel, ShotGroupModel


# 训练存取接口的 SQLAlchemy 实现；提交、回滚和关闭由外部负责
class SqlAlchemyShootingRepository(ShootingRepository):
    def __init__(self, db: Session):
        self.db = db

    # 新增或更新训练信息，不保存 shots；投篮由 add_shot 单独新增
    def save_session(self, session: ShootingSession) ->None:
        model = self.db.get(ShootingSessionModel, session.id)

        # 未找到训练则新增，已存在则更新 ORM 对象的字段
        if model is None:
            model = ShootingSessionModel(
                id=session.id,
                user_id=session.user_id,
                started_at= session.started_at,
                ended_at= session.ended_at,
                note= session.note
            )
            self.db.add(model)      
        else:
            model.user_id = session.user_id
            model.started_at = session.started_at
            model.ended_at = session.ended_at
            model.note = session.note

    # 将领域投篮转换成 ORM 对象，枚举区域通过 value 转成字符串
    def add_shot(self, shot: ShotAttempt) ->None:
        model = ShotAttemptModel(
            id=shot.id,
            session_id=shot.session_id,
            zone=shot.zone.value,
            made=shot.made,
            attempted_at=shot.attempted_at
        )
        self.db.add(model)

    # 转换成 JSON 字段，不丢失逐球 ID 和时间
    @staticmethod
    def _serialize_group_shots(group: ShotGroup) -> list[dict]:
        return [
            {"id": str(shot.id), "session_id": str(shot.session_id),
             "zone": shot.zone.value, "made": shot.made,
             "attempted_at": shot.attempted_at.isoformat()}
            for shot in group.shots
        ]

    @staticmethod
    def _restore_group_shots(records: list[dict]) -> list[ShotAttempt]:
        return [
            ShotAttempt(id=UUID(record["id"]), session_id=UUID(record["session_id"]),
                        zone=ShootingZone(record["zone"]), made=record["made"],
                        attempted_at=datetime.fromisoformat(record["attempted_at"]))
            for record in records
        ]

    # 新增组和组内记录，提交仍由服务负责
    def add_shot_group(self, group: ShotGroup) -> None:
        model = ShotGroupModel(
            id=group.id,
            session_id=group.session_id,
            zone=group.zone.value if group.zone is not None else None,
            started_at=group.started_at,
            ended_at=group.ended_at,
            shots=self._serialize_group_shots(group)
        )
        self.db.add(model)

    # 读取组信息，交给领域实体判断结束状态
    def get_shot_group_by_id(self, group_id: UUID) -> Optional[ShotGroup]:
        model = self.db.get(ShotGroupModel, group_id)
        if model is None:
            return None
        return ShotGroup(
            id=model.id,
            session_id=model.session_id,
            zone=ShootingZone(model.zone) if model.zone is not None else None,
            started_at=model.started_at,
            ended_at=model.ended_at,
            shots=self._restore_group_shots(model.shots)
        )

    # 按创建时间和 ID 排序，列表只包含本场训练的组
    def list_shot_groups(self, session_id: UUID) -> list[ShotGroup]:
        models = self.db.scalars(
            select(ShotGroupModel)
            .where(ShotGroupModel.session_id == session_id)
            .order_by(ShotGroupModel.started_at, ShotGroupModel.id)
        ).all()
        return [
            ShotGroup(id=model.id, session_id=model.session_id,
                      zone=ShootingZone(model.zone) if model.zone is not None else None, started_at=model.started_at,
                      ended_at=model.ended_at, shots=self._restore_group_shots(model.shots))
            for model in models
        ]

    # 第一次结束保存完整逐球记录；已结束组不覆盖原数据
    def finish_shot_group(self, group: ShotGroup) -> None:
        model = self.db.get(ShotGroupModel, group.id)
        if model is None:
            raise ValueError("投篮组不存在")
        if group.ended_at is None:
            raise ValueError("投篮组尚未结束")
        if group.zone is None:
            raise ValueError("结束投篮组必须有点位")
        if model.ended_at is None:
            if (group.session_id != model.session_id
                    or group.started_at != model.started_at):
                raise ValueError("投篮组信息与已保存数据不一致")
            if any(shot.session_id != group.session_id or shot.zone != group.zone for shot in group.shots):
                raise ValueError("组内投篮必须属于本场训练和本组点位")
            # 点位在结束时确定，与逐球记录一起保存。
            model.zone = group.zone.value
            model.shots = self._serialize_group_shots(group)
            model.ended_at = group.ended_at
        else:
            group.zone = ShootingZone(model.zone)
            group.ended_at = model.ended_at
            group.shots = self._restore_group_shots(model.shots)

    # 读取训练及其全部投篮，组装成完整的领域训练对象
    def get_session_by_id(self, session_id: UUID) ->Optional[ShootingSession]:
        model = self.db.get(ShootingSessionModel, session_id)

        if model is None:
            return None


        statement = (
            select(ShotAttemptModel)
            .where(ShotAttemptModel.session_id == session_id)
            .order_by(ShotAttemptModel.attempted_at, ShotAttemptModel.id)
        )
        # 取得所有匹配的投篮 ORM 对象，顺序由前面的 order_by 确定
        shot_models = self.db.scalars(statement).all()

        shots = []

        # 还原历史投篮及区域枚举，保留原来的 ID 和时间
        for shot_model in shot_models:
            shot = ShotAttempt(
                id=shot_model.id,
                session_id=shot_model.session_id,
                zone = ShootingZone(shot_model.zone),
                made = shot_model.made,
                attempted_at = shot_model.attempted_at
            )
            shots.append(shot)

        # 将训练字段与转换后的投篮列表组合成领域对象
        return ShootingSession(
            id= model.id,
            user_id=model.user_id,
            started_at=model.started_at,
            ended_at= model.ended_at,
            note=model.note,
            shots=shots
        )

    # 查询该用户的训练 ID，再逐个读取完整训练；无记录时返回空列表
    def list_by_user_id(self, user_id:UUID) -> list[ShootingSession]:
        statement = (
            select(ShootingSessionModel.id)
            .where(ShootingSessionModel.user_id == user_id)
            .order_by(
                ShootingSessionModel.started_at,
                ShootingSessionModel.id
            )
        )

        session_ids = self.db.scalars(statement).all()

        sessions = []

        # 复用单次查询；训练较多时可改用批量查询减少数据库访问
        for session_id in session_ids:
            session = self.get_session_by_id(session_id)

            if session is not None:
                sessions.append(session)

        return sessions


    
