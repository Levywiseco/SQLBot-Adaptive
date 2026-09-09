from fastapi import APIRouter, HTTPException

from apps.feedback.crud.feedback import create_feedback, list_feedback
from apps.feedback.schemas.feedback import FeedbackCreate
from common.core.config import settings
from common.core.deps import CurrentUser, SessionDep

router = APIRouter(tags=["Adaptive Feedback"], prefix="/feedback")


@router.post("")
async def create(session: SessionDep, current_user: CurrentUser, payload: FeedbackCreate):
    if not settings.ADAPTIVE_FEEDBACK_WRITES_ENABLED:
        raise HTTPException(status_code=503, detail="Adaptive feedback writes are paused")
    return create_feedback(session, payload, current_user)


@router.get("/page/{current_page}/{page_size}")
async def page(
    session: SessionDep,
    current_user: CurrentUser,
    current_page: int,
    page_size: int,
):
    return list_feedback(session, current_user, current_page, page_size)
