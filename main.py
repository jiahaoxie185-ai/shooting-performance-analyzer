# 创建 FastAPI 应用，并注册用户和投篮训练接口。
from fastapi import FastAPI

from api.router.users import router as users_router
from api.router.shooting import router as shooting_router
from api.router.auth import router as auth_router


app = FastAPI(title="投篮训练 API")

# 注册用户接口。
app.include_router(users_router)
# 注册训练和投篮接口。
app.include_router(shooting_router)

app.include_router(auth_router)