from fastapi import APIRouter, Depends, HTTPException, status, Response

from api.dependencies import get_user_service
from api.schemas.users import LoginRequest, UserResponse
from application.user_services import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


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

    response.set_cookie(
        key="session_token",
        value=token,
        max_age=7*24*60*60,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return user

