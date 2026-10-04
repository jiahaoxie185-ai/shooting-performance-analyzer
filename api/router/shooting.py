# 将训练、投篮和统计请求交给训练服务处理。
from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_shooting_service
from api.schemas.shooting import ShootingSessionCreate, ShootingSessionResponse, ShotAttemptCreate, ShootingAttemptResponse,ShootingSummaryResponse
from api.schemas.shooting import ShotGroupCreate, ShotGroupFinish, ShotGroupResponse, ShootingStatistics

from application.shooting_services import ShootingService, ShootingSessionNotFoundError, ShotGroupNotFoundError

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

# 在指定训练中创建投篮组；已结束训练不能创建组。
@router.post(
    "/{session_id}/shot-groups",
    response_model=ShotGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_shot_group(
    session_id: UUID,
    request: ShotGroupCreate = ShotGroupCreate(),
    service: ShootingService = Depends(get_shooting_service),
):
    try:
        return service.add_shot_group(session_id=session_id, zone=request.zone)
    except ShootingSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# 查询本场训练的所有投篮组。
@router.get("/{session_id}/shot-groups", response_model=list[ShotGroupResponse])
def list_shot_groups(
    session_id: UUID,
    service: ShootingService = Depends(get_shooting_service),
):
    try:
        return service.list_shot_groups(session_id)
    except ShootingSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# 查询指定投篮组，包含状态、点位及逐球记录。
@router.get(
    "/shot-groups/{group_id}",
    response_model=ShotGroupResponse,
    status_code=status.HTTP_200_OK,
)
def get_shot_group_by_id(
    group_id: UUID,
    service: ShootingService = Depends(get_shooting_service),
):
    try:
        return service.get_shot_group_by_id(group_id=group_id)
    except ShotGroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# 查询本组统计，前端不根据逐球记录重新计算。
@router.get("/shot-groups/{group_id}/summary", response_model=ShootingStatistics)
def get_shot_group_summary(
    group_id: UUID,
    service: ShootingService = Depends(get_shooting_service),
):
    try:
        return service.get_shot_group_summary(group_id)
    except ShotGroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# 提交点位和数量并结束，相同数据重试不重复生成投篮。
@router.post(
    "/shot-groups/{group_id}/finish",
    response_model=ShotGroupResponse,
    status_code=status.HTTP_200_OK,
)
def finish_shot_group(
    group_id: UUID,
    request: ShotGroupFinish,
    service: ShootingService = Depends(get_shooting_service),
):
    try:
        return service.finish_shot_group(
            group_id=group_id, zone=request.zone, attempts=request.attempts, made=request.made
        )
    except ShotGroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


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
