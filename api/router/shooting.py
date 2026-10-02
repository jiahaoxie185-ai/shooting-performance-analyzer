# 将训练、投篮和统计请求交给训练服务处理。
from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_shooting_service
from api.schemas.shooting import ShootingSessionCreate, ShootingSessionResponse, ShotAttemptCreate, ShotBatchCreate, ShootingAttemptResponse,ShootingSummaryResponse

from application.shooting_services import ShootingService, ShootingSessionNotFoundError

from uuid import UUID


router = APIRouter(prefix="/sessions", tags=["shooting"])


# 创建训练；用户不存在时返回 404。
@router.post(
    "",
    response_model= ShootingSessionResponse,
    status_code=status.HTTP_201_CREATED
)
def start_shooting_session(
    request: ShootingSessionCreate,
    service: ShootingService = Depends(get_shooting_service)
):
    try:
        return service.start_session(
            user_id=request.user_id,
            note=request.note
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc

# 记录一球；训练状态不允许时返回 400。
@router.post(
    "/{session_id}/shots",
    response_model= ShootingAttemptResponse,
    status_code=status.HTTP_201_CREATED
)
def add_shot(
    session_id: UUID,
    request: ShotAttemptCreate,
    service: ShootingService = Depends(get_shooting_service)
):
    try:
        return service.add_shot(
            session_id=session_id,
            zone=request.zone,
            made=request.made
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

# 批量添加投篮；整批由服务统一提交。
@router.post(
    "/{session_id}/shots/batch",
    response_model=ShootingSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_shots(
    session_id: UUID,
    request: ShotBatchCreate,
    service: ShootingService = Depends(get_shooting_service),
):
    try:
        return service.add_shots(
            session_id=session_id,
            attempts=request.attempts,
            made=request.made,
            zone=request.zone,
        )
    except ShootingSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# 查询单场详情，复用包含投篮列表的训练响应。
@router.get(
    "/{session_id}",
    response_model=ShootingSessionResponse,
    status_code=status.HTTP_200_OK,
)
def get_session(
    session_id: UUID,
    service: ShootingService = Depends(get_shooting_service),
):
    try:
        return service.get_session(session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# 结束指定训练；找不到训练时返回 404。
@router.post(
    "/{session_id}/finish",
    response_model=ShootingSessionResponse,
    status_code=status.HTTP_200_OK,
)
def finish_session(
    session_id:UUID,
    service:ShootingService = Depends(get_shooting_service)
):
    try:
        return service.finish_session(
            session_id=session_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc

# 查询一场训练的总体和分区统计。
@router.get(
    "/{session_id}/summary",
    response_model=ShootingSummaryResponse,
    status_code=status.HTTP_200_OK
)
def get_session_summary(
    session_id:UUID,
    service:ShootingService = Depends(get_shooting_service)
):
    try:
        return service.get_session_summary(session_id=session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc

# 查询用户全部训练的累计统计。
@router.get(
    "/users/{user_id}/summary",
    response_model=ShootingSummaryResponse,
    status_code=status.HTTP_200_OK
)
def get_user_summary(
    user_id:UUID,
    service:ShootingService = Depends(get_shooting_service)
):
    try:
        return service.get_user_summary(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc

# 查询用户全部训练场次；用户不存在时返回 404。
@router.get(
    "/users/{user_id}",
    response_model=list[ShootingSessionResponse],
    status_code=status.HTTP_200_OK
)
def list_user_sessions(
    user_id:UUID,
    service:ShootingService = Depends(get_shooting_service)
):
    try:
        return service.list_sessions(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        ) from exc
