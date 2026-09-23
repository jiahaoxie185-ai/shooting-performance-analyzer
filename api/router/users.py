from fastapi import APIRouter, status, Depends, HTTPException
from api.dependencies import get_user_service
from api.schemas.users import UserCreate, UserResponse
from application.user_services import UserService
from uuid import UUID


router = APIRouter(prefix="/users", tags=["users"])


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


