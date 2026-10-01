# 将用户注册和查询请求交给用户服务处理。
from fastapi import APIRouter, status, Depends, HTTPException
from api.dependencies import get_user_service
from api.schemas.users import UserCreate, UserResponse
from application.user_services import UserService
from uuid import UUID



router = APIRouter(prefix="/users", tags=["users"])


# 注册用户；用户名重复时返回 409。
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def sign_up(
    request: UserCreate,
    service:UserService = Depends(get_user_service)
):
    try:
        user = service.sign_up(
            username=request.username,
            name=request.name,
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        ) from exc
    return user

# 按用户名查询；找不到时返回 404。
@router.get("", response_model=UserResponse)
def get_user_by_username(
    username:str,
    service: UserService = Depends(get_user_service)
):
    try:
        return service.get_user_by_username(username)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc

# 按用户 ID 查询；找不到时返回 404。
@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: UUID,
    service: UserService = Depends(get_user_service)
):
    try:
        return service.get_user_by_id(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc

