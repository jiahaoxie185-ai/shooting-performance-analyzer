from fastapi import FastAPI

from api.router.users import router as users_router
from api.router.shooting import router as shooting_router


app = FastAPI(title="投篮训练 API")

app.include_router(users_router)
app.include_router(shooting_router)