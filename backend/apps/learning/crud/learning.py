from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import sqlglot
from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlglot import exp
from sqlmodel import Session, select

from apps.feedback.models.feedback import FeedbackEvent
from apps.learning.models.learning import LearningCandidate, LearningJob
from apps.memory.crud.memory import create_memory, delete_memory
from apps.memory.models.memory import MemoryEntry
from apps.memory.schemas.memory import MemoryCreate

BLOCKED_SQL_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,
    exp.Merge,
)


def _now() -> datetime:
    return datetime.now()


def _error(status_code: int, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=message)


def sql_is_read_only(sql: str) -> bool:
    if (
        not sql
        or ";" in sql.strip().rstrip(";")
        or "--" in sql
        or "/*" in sql
        or "*/" in sql
    ):
        return False
    try:
        statements = sqlglot.parse(sql)
    except Exception:
        return False
    if len(statements) != 1 or not isinstance(statements[0], exp.Query):
        return False
    return not any(statements[0].find(node_type) is not None for node_type in BLOCKED_SQL_NODES)


def sql_dependencies(sql: str) -> list[str]:
    """Extract conservative table and field dependencies from one reviewed query."""
    if not sql_is_read_only(sql):
        return []
    statement = sqlglot.parse_one(sql)
    cte_sources: dict[str, Optional[str]] = {}
    for cte in statement.find_all(exp.CTE):
        source_names = list(
            dict.fromkeys(
                table.name
                for table in cte.this.find_all(exp.Table)
                if table.name and table.name.casefold() not in cte_sources
            )
        )
        cte_sources[cte.alias_or_name.casefold()] = (
            source_names[0] if len(source_names) == 1 else None
        )

    all_tables = list(statement.find_all(exp.Table))
    tables = [
        table
        for table in all_tables
        if table.name and table.name.casefold() not in cte_sources
    ]
    alias_to_table: dict[str, str] = {}
    ignored_qualifiers: set[str] = set()
    table_names: list[str] = []
    for table in tables:
        name = table.name
        if not name:
            continue
        table_names.append(name)
        alias_to_table[name.casefold()] = name
        if table.alias:
            alias_to_table[table.alias.casefold()] = name
    for table in all_tables:
        cte_name = table.name.casefold() if table.name else ""
        if cte_name not in cte_sources:
            continue
        qualifier = table.alias.casefold() if table.alias else cte_name
        source_name = cte_sources[cte_name]
        if source_name:
            alias_to_table[qualifier] = source_name
            alias_to_table[cte_name] = source_name
        else:
            ignored_qualifiers.update({qualifier, cte_name})
    dependencies: list[str] = list(dict.fromkeys(table_names))
    unique_tables = list(dict.fromkeys(table_names))
    for column in statement.find_all(exp.Column):
        if not column.name or column.name == "*":
            continue
        if column.table:
            if column.table.casefold() in ignored_qualifiers:
                continue
            table_name = alias_to_table.get(column.table.casefold(), column.table)
        elif len(unique_tables) == 1:
            table_name = unique_tables[0]
        else:
            table_name = "*"
        dependencies.append(f"{table_name}.{column.name}")
    return list(dict.fromkeys(dependencies))


def _get_candidate(session: Session, candidate_id: int, oid: int) -> LearningCandidate:
    candidate = session.exec(
        select(LearningCandidate).where(
            and_(LearningCandidate.id == candidate_id, LearningCandidate.oid == oid)
        )
    ).first()
    if not candidate:
        raise _error(404, "Learning candidate was not found")
    return candidate


def _serialize(session: Session, candidate: LearningCandidate) -> dict[str, Any]:
    data = candidate.model_dump()
    feedback = session.get(FeedbackEvent, candidate.feedback_event_id)
    data["feedback"] = (
        {
            "id": feedback.id,
            "feedback_type": feedback.feedback_type,
            "correction_text": feedback.correction_text,
            "chat_record_id": feedback.chat_record_id,
            "answer_snapshot": feedback.answer_snapshot,
            "created_at": feedback.created_at,
        }
        if feedback
        else None
    )
    return data


def list_candidates(
    session: Session,
    oid: int,
    current_page: int,
    page_size: int,
    *,
    status: Optional[str] = None,
    candidate_type: Optional[str] = None,
) -> dict[str, Any]:
    page = max(current_page, 1)
    size = min(max(page_size, 1), 100)
    conditions = [LearningCandidate.oid == int(oid or 1)]
    if status:
        conditions.append(LearningCandidate.status == status)
    if candidate_type:
        conditions.append(LearningCandidate.candidate_type == candidate_type)
    total = int(
        session.execute(
            select(func.count()).select_from(LearningCandidate).where(and_(*conditions))
        ).scalar_one()
    )
    rows = session.exec(
        select(LearningCandidate)
        .where(and_(*conditions))
        .order_by(LearningCandidate.created_at.desc(), LearningCandidate.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return {
        "current_page": page,
        "page_size": size,
        "total_count": total,
        "total_pages": (total + size - 1) // size,
        "data": [_serialize(session, item) for item in rows],
    }


def get_candidate(session: Session, candidate_id: int, oid: int) -> dict[str, Any]:
    return _serialize(session, _get_candidate(session, candidate_id, int(oid or 1)))


def _candidate_memory_payload(candidate: LearningCandidate) -> MemoryCreate:
    proposed = candidate.proposed_content
    question = str(proposed.get("question") or "").strip()
    correction = str(proposed.get("correction") or "").strip()
    sql = str(proposed.get("sql") or "").strip()
    keyword_values = proposed.get("memory_keywords") or []
    keywords = [str(item) for item in keyword_values if str(item).strip()]
    dependencies = list(
        dict.fromkeys(
            table
            for metric in proposed.get("metric_refs") or []
            for table in metric.get("required_tables") or []
        )
    )

    if candidate.candidate_type in {"confirmed_answer", "shared_example"}:
        if not sql_is_read_only(sql):
            raise _error(422, "The answer SQL must be a single read-only query before it can be approved")
        title = question[:255] or "Reviewed SQL example"
        detail = f"Reviewed question: {question}\nReference SQL: {sql}"
        if correction:
            detail += f"\nReviewer guidance: {correction}"
        dependencies = list(dict.fromkeys([*dependencies, *sql_dependencies(sql)]))
        return MemoryCreate(
            title=title,
            content=detail,
            memory_type="confirmed_example",
            scope="workspace",
            keywords=keywords,
            dependencies=dependencies,
            datasource_id=candidate.datasource_id,
            priority=2,
        )

    if candidate.candidate_type == "correction_rule":
        if len(correction) < 3:
            raise _error(422, "A correction is required before this candidate can be approved")
        return MemoryCreate(
            title=(question[:200] or "Reviewed correction"),
            content=correction,
            memory_type="business_rule",
            scope="workspace",
            keywords=keywords,
            dependencies=dependencies,
            datasource_id=candidate.datasource_id,
            priority=3,
        )
    raise _error(409, "This candidate type cannot be activated as memory")


def approve_candidate(
    session: Session,
    candidate_id: int,
    review_note: str,
    user: Any,
) -> dict[str, Any]:
    candidate = _get_candidate(session, candidate_id, int(user.oid or 1))
    if candidate.status != "candidate":
        raise _error(409, "Only a pending candidate can be approved")
    now = _now()

    if candidate.candidate_type == "metric_change":
        candidate.status = "approved"
        candidate.validation_status = "requires_metric_version"
        candidate.validation_message = (
            "Review accepted. Create and publish a new metric version before this lesson can affect answers."
        )
        candidate.reviewed_by = user.id
        candidate.review_note = review_note
        candidate.reviewed_at = now
        session.add(candidate)
        session.flush()
        return _serialize(session, candidate)

    payload = _candidate_memory_payload(candidate)
    existing_same_title = session.exec(
        select(MemoryEntry).where(
            and_(
                MemoryEntry.oid == int(user.oid or 1),
                MemoryEntry.scope == "workspace",
                MemoryEntry.datasource_id == payload.datasource_id,
                MemoryEntry.memory_type == payload.memory_type,
                MemoryEntry.title == payload.title,
                MemoryEntry.status == "active",
            )
        )
    ).all()
    memory, duplicate = create_memory(
        session,
        payload,
        user,
        source_type="approved_feedback",
        source_reference_id=str(candidate.id),
        allow_duplicate=True,
    )
    for old in existing_same_title:
        if old.id != memory["id"]:
            old.status = "paused"
            old.updated_at = now
            session.add(old)

    candidate.status = "active"
    candidate.validation_status = "approved"
    candidate.validation_message = (
        "Equivalent reviewed memory was already active"
        if duplicate
        else "Read-only and governance checks passed"
    )
    candidate.activated_memory_id = memory["id"]
    candidate.reviewed_by = user.id
    candidate.review_note = review_note
    candidate.reviewed_at = now
    candidate.activated_at = now
    session.add(candidate)
    session.flush()
    return _serialize(session, candidate)


def reject_candidate(
    session: Session,
    candidate_id: int,
    review_note: str,
    user: Any,
) -> dict[str, Any]:
    candidate = _get_candidate(session, candidate_id, int(user.oid or 1))
    if candidate.status != "candidate":
        raise _error(409, "Only a pending candidate can be rejected")
    candidate.status = "rejected"
    candidate.validation_status = "rejected"
    candidate.validation_message = "Rejected by a workspace administrator"
    candidate.reviewed_by = user.id
    candidate.review_note = review_note
    candidate.reviewed_at = _now()
    session.add(candidate)
    session.flush()
    return _serialize(session, candidate)


def revoke_candidate(
    session: Session,
    candidate_id: int,
    review_note: str,
    user: Any,
) -> dict[str, Any]:
    candidate = _get_candidate(session, candidate_id, int(user.oid or 1))
    if candidate.status not in {"active", "approved"}:
        raise _error(409, "Only an active or approved candidate can be revoked")
    if candidate.activated_memory_id:
        delete_memory(session, candidate.activated_memory_id, user)
    candidate.status = "revoked"
    candidate.validation_status = "revoked"
    candidate.validation_message = "Removed from retrieval by a workspace administrator"
    candidate.reviewed_by = user.id
    candidate.review_note = review_note
    candidate.reviewed_at = _now()
    session.add(candidate)
    session.flush()
    return _serialize(session, candidate)


def learning_stats(session: Session, oid: int) -> dict[str, Any]:
    rows = session.execute(
        select(LearningCandidate.status, func.count())
        .where(LearningCandidate.oid == int(oid or 1))
        .group_by(LearningCandidate.status)
    ).all()
    pending_jobs = int(
        session.execute(
            select(func.count())
            .select_from(LearningJob)
            .where(and_(LearningJob.oid == int(oid or 1), LearningJob.status.in_(["pending", "running"])))
        ).scalar_one()
    )
    return {"by_status": {status: int(count) for status, count in rows}, "pending_jobs": pending_jobs}
