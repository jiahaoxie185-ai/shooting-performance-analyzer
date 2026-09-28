# 定义业务层使用的事务接口。
from abc import ABC, abstractmethod


from domain.users.repositories import UserRepository, AuthSessionRepository
from domain.shooting.repositories import ShootingRepository


# 工作单元接口，具体会话和事务操作由基础设施层实现
class UnitOfWork(ABC):
    # 仅声明属性；实现类负责创建共用同一事务的两个 Repository
    user_repository: UserRepository
    shooting_repository: ShootingRepository
    auth_session_repository: AuthSessionRepository

    @abstractmethod
    # 进入 with 时准备会话和 Repository，并返回工作单元
    def __enter__(self) -> "UnitOfWork":
        pass

    @abstractmethod
    # 约定退出时回滚未提交操作并关闭会话，不自动提交或吞掉异常
    def  __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    @abstractmethod
    # 由服务在业务操作完成后显式调用，提交当前事务
    def commit(self) -> None:
        pass

    @abstractmethod
    # 撤销当前事务中尚未提交的修改
    def rollback(self) -> None:
        pass




        