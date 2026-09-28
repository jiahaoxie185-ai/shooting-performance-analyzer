# 组装接口使用的业务服务、工作单元和密码哈希组件。
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