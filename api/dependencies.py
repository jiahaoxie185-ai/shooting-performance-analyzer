# 预留 API 依赖组装：提供工作单元、密码组件和服务；具体实现尚未编写
from application.user_services import UserService
from application.shooting_services import ShootingService
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from infrastructure.security import Argon2PasswordService


def get_user_service() -> UserService:
    return UserService(
        uow = SqlAlchemyUnitOfWork(),
        password_hasher = Argon2PasswordService()
    )

def get_shooting_service() -> ShootingService:
    return ShootingService(
        uow = SqlAlchemyUnitOfWork()
    )