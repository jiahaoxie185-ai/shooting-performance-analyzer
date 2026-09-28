# 实现训练和投篮记录的数据库存取。
from sqlalchemy.orm import Session
from sqlalchemy import select

from typing import Optional
from uuid import UUID

from domain.shooting.repositories import ShootingRepository
from domain.shooting.entities import ShootingSession, ShotAttempt, ShootingZone
from infrastructure.models import ShootingSessionModel, ShotAttemptModel


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


    

