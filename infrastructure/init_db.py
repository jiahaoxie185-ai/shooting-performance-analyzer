# 初始化数据库中尚不存在的表。
from .database import Base, engine
# 导入模型以注册数据库表，即使没有直接使用 models 变量也不能省略
from. import models


# 创建不存在的表；不会自动更新已有表结构，也不会清空数据
def init_db() ->None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database table initialization complete")
