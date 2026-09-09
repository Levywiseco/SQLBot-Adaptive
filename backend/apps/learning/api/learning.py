from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from apps.learning.crud.learning import (
    approve_candidate,
    get_candidate,
    learning_stats,
    list_candidates,
    reject_candidate,
    revoke_candidate,
)
from apps.learning.schemas.learning import CandidateReview
from apps.system.schemas.permission import SqlbotPermission, require_permissions
from common.core.config import settings
from common.core.deps import CurrentUser, SessionDep

router = APIRouter(tags=["Adaptive Learning"], prefix="/system/learning")


@router.get("/page/{current_page}/{page_size}")
@require_permissions(permission=SqlbotPermission(role=["ws_admin"]))
async def page(
    session: SessionDep,
    current_user: CurrentUser,
    current_page: int,
    page_size: int,
    status: Optional[str] = Query(default=None),
    candidate_type: Optional[str] = Query(default=None),
):
    return list_candidates(
        session,
        current_user.oid,
        current_page,
        page_size,
        status=status,
        candidate_type=candidate_type,
    )


@router.get("/stats")
@require_permissions(permission=SqlbotPermission(role=["ws_admin"]))
async def stats(session: SessionDep, current_user: CurrentUser):
    return learning_stats(session, current_user.oid)


@router.get("/{candidate_id}")
@require_permissions(permission=SqlbotPermission(role=["ws_admin"]))
async def detail(session: SessionDep, current_user: CurrentUser, candidate_id: int):
    return get_candidate(session, candidate_id, current_user.oid)


@router.post("/{candidate_id}/approve")
@require_permissions(permission=SqlbotPermission(role=["ws_admin"]))
async def approve(
    session: SessionDep,
    current_user: CurrentUser,
    candidate_id: int,
    payload: CandidateReview,
):
    if not settings.ADAPTIVE_SHARED_LEARNING_ACTIVATION_ENABLED:
        raise HTTPException(status_code=503, detail="Shared learning activation is paused")
    return approve_candidate(session, candidate_id, payload.review_note, current_user)


@router.post("/{candidate_id}/reject")
@require_permissions(permission=SqlbotPermission(role=["ws_admin"]))
async def reject(
    session: SessionDep,
    current_user: CurrentUser,
    candidate_id: int,
    payload: CandidateReview,
):
    return reject_candidate(session, candidate_id, payload.review_note, current_user)


@router.post("/{candidate_id}/revoke")
@require_permissions(permission=SqlbotPermission(role=["ws_admin"]))
async def revoke(
    session: SessionDep,
    current_user: CurrentUser,
    candidate_id: int,
    payload: CandidateReview,
):
    return revoke_candidate(session, candidate_id, payload.review_note, current_user)
