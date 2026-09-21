from uuid import UUID

from sqlalchemy import String, Uuid, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime
from typing import Optional

from .database import Base


# 用户表模型；与领域 User 对象通过 Repository 转换
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable= False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable= False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
    height: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable= True
    )
    position: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable= True
    )

# 训练表模型，通过 user_id 关联用户；投篮记录保存在独立表中
class ShootingSessionModel(Base):
    __tablename__ = "shooting_sessions"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key= True,
        nullable= False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable= False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable= False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable= True
    )
    note: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable= True
    )

# 投篮表模型，通过 session_id 关联训练；区域保存为字符串
class ShotAttemptModel(Base):
    __tablename__ = "shot_attempts"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key= True,
        nullable= False
    )
    session_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("shooting_sessions.id"),
        nullable= False
    )
    zone: Mapped[str] = mapped_column(
        String(50),
        nullable= False
    )
    made: Mapped[bool] = mapped_column(
        Boolean,
        nullable= False
    )
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable= False
    )

