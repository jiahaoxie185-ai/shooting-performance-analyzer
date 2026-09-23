from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_shooting_service
from api.schemas.shooting import ShootingSessionCreate, ShootingSessionResponse, ShotAttemptCreate, ShootingAttemptResponse,ShootingSummaryResponse

from application.shooting_services import ShootingService

from uuid import UUID


router = APIRouter(prefix="/sessions", tags=["shooting"])


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


