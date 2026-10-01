# 处理登录、恢复登录状态和退出登录请求。
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from typing import Optional

from api.dependencies import get_user_service
from api.schemas.users import LoginRequest, UserResponse
from application.user_services import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


# 校验用户名和密码；成功后把会话令牌写入 HttpOnly Cookie，失败时返回 401。
@router.post("/login", response_model=UserResponse)
def login(
    request: LoginRequest,
    response: Response,
    service:UserService = Depends(get_user_service)
):
    try:
        user, token = service.login(request.username, request.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或者密码错误"
        ) from exc

    # Cookie 有效期与数据库会话保持一致，均为 7 天
    response.set_cookie(
        key="session_token",
        value=token,
        max_age=7*24*60*60,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return user

# 从 Cookie 读取令牌并返回当前用户；未登录或会话失效时返回 401。
@router.get("/me", response_model=UserResponse)
def me(
        session_token: Optional[str] = Cookie(default=None),
        service: UserService = Depends(get_user_service)
):
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        return service.current_user(session_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效"
        ) from exc

# 撤销数据库中的会话并清除 Cookie；没有 Cookie 时也视为退出成功。
@router.post("/logout")
def logout(
    response: Response,
    session_token: Optional[str] = Cookie(default=None),
    service: UserService = Depends(get_user_service)
):
    if session_token:
        service.logout(session_token)

    response.delete_cookie("session_token", path="/")
    return {"message":"已退出登录"}