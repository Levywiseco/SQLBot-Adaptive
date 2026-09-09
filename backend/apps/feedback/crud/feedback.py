from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlmodel import Session, select

from apps.chat.models.chat_model import Chat, ChatRecord
from apps.feedback.models.feedback import FeedbackEvent
from apps.feedback.schemas.feedback import FeedbackCreate
from apps.learning.models.learning import LearningCandidate, LearningJob
from apps.memory.crud.memory import create_memory
from apps.memory.models.memory import RetrievalTrace
from apps.memory.schemas.memory import MemoryCreate

CANDIDATE_TYPES = {
    "correct": "confirmed_answer",
    "result_wrong": "correction_rule",
    "metric_wrong": "metric_change",
    "remember_preference": "personal_preference",
    "save_example": "shared_example",
}


def _now() -> datetime:
    return datetime.now()


def _error(status_code: int, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=message)


def _get_owned_record(session: Session, record_id: int, user: Any) -> tuple[ChatRecord, Chat]:
    record = session.get(ChatRecord, record_id)
    if not record or record.create_by != user.id:
        raise _error(404, "Chat answer was not found")
    chat = session.get(Chat, record.chat_id)
    if not chat or chat.oid != int(user.oid or 1) or chat.create_by != user.id:
        raise _error(404, "Chat answer was not found")
    return record, chat


def _snapshot(session: Session, record: ChatRecord) -> dict[str, Any]:
    trace = session.exec(
        select(RetrievalTrace).where(RetrievalTrace.chat_record_id == record.id)
    ).first()
    return {
        "question": record.question,
        "sql": record.sql,
        "datasource_id": record.datasource,
        "finished": bool(record.finish),
        "error": record.error,
        "metric_refs": trace.metric_refs if trace else [],
        "memory_refs": trace.memory_refs if trace else [],
        "inherited_metric": bool(trace.inherited_metric) if trace else False,
        "retrieval_trace_id": trace.id if trace else None,
    }


def _serialize_candidate(candidate: Optional[LearningCandidate]) -> Optional[dict[str, Any]]:
    return candidate.model_dump() if candidate else None


def _result(
    event: FeedbackEvent,
    candidate: Optional[LearningCandidate],
    job: Optional[LearningJob],
    *,
    duplicate: bool,
) -> dict[str, Any]:
    return {
        "feedback": event.model_dump(),
        "candidate": _serialize_candidate(candidate),
        "job": job.model_dump() if job else None,
        "duplicate": duplicate,
    }


def _existing_result(session: Session, event: FeedbackEvent) -> dict[str, Any]:
    candidate = session.exec(
        select(LearningCandidate).where(LearningCandidate.feedback_event_id == event.id)
    ).first()
    job = session.exec(
        select(LearningJob).where(LearningJob.feedback_event_id == event.id)
    ).first()
    return _result(event, candidate, job, duplicate=True)


def create_feedback(
    session: Session,
    payload: FeedbackCreate,
    user: Any,
) -> dict[str, Any]:
    workspace_id = int(user.oid or 1)
    existing = session.exec(
        select(FeedbackEvent).where(
            and_(
                FeedbackEvent.oid == workspace_id,
                FeedbackEvent.user_id == user.id,
                FeedbackEvent.idempotency_key == payload.idempotency_key,
            )
        )
    ).first()
    if existing:
        return _existing_result(session, existing)

    record, _chat = _get_owned_record(session, payload.chat_record_id, user)
    snapshot = _snapshot(session, record)
    event = FeedbackEvent(
        oid=workspace_id,
        user_id=user.id,
        chat_record_id=payload.chat_record_id,
        feedback_type=payload.feedback_type,
        correction_text=payload.correction_text,
        memory_title=payload.memory_title,
        memory_content=payload.memory_content,
        memory_keywords=payload.memory_keywords,
        idempotency_key=payload.idempotency_key,
        answer_snapshot=snapshot,
        status="recorded",
        created_at=_now(),
    )
    session.add(event)
    session.flush()
    session.refresh(event)

    candidate_type = CANDIDATE_TYPES[payload.feedback_type]
    proposed_content = {
        "question": record.question,
        "sql": record.sql,
        "correction": payload.correction_text,
        "metric_refs": snapshot["metric_refs"],
        "memory_refs": snapshot["memory_refs"],
        "memory_title": payload.memory_title,
        "memory_content": payload.memory_content,
        "memory_keywords": payload.memory_keywords,
    }
    candidate = LearningCandidate(
        oid=workspace_id,
        feedback_event_id=int(event.id),
        candidate_type=candidate_type,
        scope="personal" if payload.feedback_type == "remember_preference" else "workspace",
        target_user_id=user.id if payload.feedback_type == "remember_preference" else None,
        datasource_id=record.datasource,
        proposed_content=proposed_content,
        status="candidate",
        validation_status="pending",
        created_at=_now(),
    )
    session.add(candidate)
    session.flush()
    session.refresh(candidate)

    job = LearningJob(
        oid=workspace_id,
        feedback_event_id=int(event.id),
        candidate_id=int(candidate.id),
        idempotency_key=f"feedback:{event.id}:extract:v1",
        payload={"candidate_type": candidate_type},
        status="running",
        attempts=1,
        created_at=_now(),
        updated_at=_now(),
    )
    session.add(job)
    session.flush()

    if payload.feedback_type == "remember_preference":
        title = payload.memory_title or (payload.memory_content or "")[:40]
        memory_payload = MemoryCreate(
            title=title or "Confirmed preference",
            content=payload.memory_content or "",
            memory_type="preference",
            scope="personal",
            keywords=payload.memory_keywords,
            datasource_id=record.datasource,
        )
        memory, duplicate = create_memory(
            session,
            memory_payload,
            user,
            source_type="explicit_feedback",
            source_reference_id=str(event.id),
            allow_duplicate=True,
        )
        candidate.status = "active"
        candidate.validation_status = "approved"
        candidate.validation_message = (
            "Equivalent personal memory already existed"
            if duplicate
            else "Explicit user preference passed deterministic checks"
        )
        candidate.activated_memory_id = memory["id"]
        candidate.reviewed_by = user.id
        candidate.review_note = "Explicit request to remember this personal preference"
        candidate.reviewed_at = _now()
        candidate.activated_at = _now()
        session.add(candidate)
    else:
        candidate.validation_status = "awaiting_review"
        candidate.validation_message = "Shared knowledge requires workspace administrator review"
        session.add(candidate)

    job.status = "succeeded"
    job.updated_at = _now()
    session.add(job)
    event.status = "processed"
    event.processed_at = _now()
    session.add(event)
    session.flush()
    session.refresh(event)
    session.refresh(candidate)
    session.refresh(job)
    return _result(event, candidate, job, duplicate=False)


def list_feedback(
    session: Session,
    user: Any,
    current_page: int,
    page_size: int,
) -> dict[str, Any]:
    page = max(current_page, 1)
    size = min(max(page_size, 1), 100)
    conditions = and_(FeedbackEvent.oid == int(user.oid or 1), FeedbackEvent.user_id == user.id)
    total = int(
        session.execute(
            select(func.count()).select_from(FeedbackEvent).where(conditions)
        ).scalar_one()
    )
    rows = session.exec(
        select(FeedbackEvent)
        .where(conditions)
        .order_by(FeedbackEvent.created_at.desc(), FeedbackEvent.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    items = []
    for event in rows:
        candidate = session.exec(
            select(LearningCandidate).where(LearningCandidate.feedback_event_id == event.id)
        ).first()
        items.append({**event.model_dump(), "candidate": _serialize_candidate(candidate)})
    return {
        "current_page": page,
        "page_size": size,
        "total_count": total,
        "total_pages": (total + size - 1) // size,
        "data": items,
    }
