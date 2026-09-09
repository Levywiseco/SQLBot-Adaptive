"""End-to-end smoke test for the adaptive APIs against the local development database."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import requests
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from apps.chat.models.chat_model import Chat, ChatRecord  # noqa: E402
from apps.feedback.models.feedback import FeedbackEvent  # noqa: E402
from apps.learning.models.learning import LearningCandidate, LearningJob  # noqa: E402
from apps.memory.crud.memory import (  # noqa: E402
    get_memory_prompt,
    looks_like_follow_up,
    save_metric_context,
)
from apps.memory.models.memory import MemoryEntry  # noqa: E402
from apps.metrics.crud.metric import (  # noqa: E402
    get_metric_prompt,
    get_metric_prompt_by_refs,
)
from common.core.db import engine  # noqa: E402
from common.core.security import create_access_token  # noqa: E402

BASE_URL = "http://127.0.0.1:8000/api/v1"
RUN_KEY = uuid4().hex[:10]
USER = SimpleNamespace(id=1, oid=1, isAdmin=True, weight=1)


def http_request(method: str, path: str, *, token: str, **kwargs):
    return requests.request(
        method,
        f"{BASE_URL}{path}",
        headers={"X-SQLBOT-TOKEN": f"Bearer {token}"},
        timeout=30,
        **kwargs,
    )


def request(method: str, path: str, *, token: str, **kwargs):
    response = http_request(method, path, token=token, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {response.status_code}: {response.text}")
    payload = response.json()
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def main() -> None:
    token = create_access_token(
        {"account": "admin", "id": 1, "oid": 1},
        expires_delta=timedelta(minutes=15),
    )
    created_memory_ids: set[int] = set()

    with Session(engine) as session:
        chat = Chat(
            oid=1,
            create_time=datetime.now(),
            create_by=1,
            brief=f"adaptive-smoke-{RUN_KEY}",
            chat_type="chat",
            datasource=1,
            engine_type="pg",
        )
        session.add(chat)
        session.flush()
        record = ChatRecord(
            chat_id=chat.id,
            create_time=datetime.now(),
            finish_time=datetime.now(),
            create_by=1,
            datasource=1,
            engine_type="pg",
            question="按区域统计净销售额",
            sql="SELECT region, SUM(amount - discount_amount) FROM adaptive_demo_sales WHERE status = 'paid' GROUP BY region",
            finish=True,
        )
        session.add(record)
        session.commit()
        chat_id = int(chat.id)
        record_id = int(record.id)

    try:
        manual = request(
            "POST",
            "/system/memories",
            token=token,
            json={
                "title": f"金额单位 {RUN_KEY}",
                "content": "金额默认用万元显示",
                "memory_type": "preference",
                "scope": "personal",
                "keywords": ["金额"],
                "datasource_id": 1,
            },
        )
        created_memory_ids.add(int(manual["id"]))
        secret_rejection = http_request(
            "POST",
            "/system/memories",
            token=token,
            json={
                "title": f"unsafe-{RUN_KEY}",
                "content": "api_key=do-not-store-this",
                "memory_type": "preference",
                "scope": "personal",
            },
        )
        assert secret_rejection.status_code == 422
        dependency_rejection = http_request(
            "POST",
            "/system/memories",
            token=token,
            json={
                "title": f"unsafe-example-{RUN_KEY}",
                "content": "Reference SQL: SELECT * FROM adaptive_demo_sales",
                "memory_type": "confirmed_example",
                "scope": "workspace",
            },
        )
        assert dependency_rejection.status_code == 422
        expiry_rejection = http_request(
            "PUT",
            f"/system/memories/{manual['id']}",
            token=token,
            json={"expires_at": "2000-01-01T00:00:00+00:00"},
        )
        assert expiry_rejection.status_code == 422
        page = request(
            "GET",
            "/system/memories/page/1/100",
            token=token,
            params={"scope": "personal", "keyword": RUN_KEY},
        )
        assert page["total_count"] == 1
        paused = request(
            "POST",
            f"/system/memories/{manual['id']}/status",
            token=token,
            json={"status": "paused"},
        )
        assert paused["status"] == "paused"
        request(
            "POST",
            f"/system/memories/{manual['id']}/status",
            token=token,
            json={"status": "active"},
        )

        preference_key = f"smoke-pref-{RUN_KEY}"
        remembered = request(
            "POST",
            "/feedback",
            token=token,
            json={
                "chat_record_id": record_id,
                "feedback_type": "remember_preference",
                "memory_title": f"图表偏好 {RUN_KEY}",
                "memory_content": "图表默认按月份升序展示",
                "memory_keywords": ["图表", "月份"],
                "idempotency_key": preference_key,
            },
        )
        assert remembered["candidate"]["status"] == "active"
        created_memory_ids.add(int(remembered["candidate"]["activated_memory_id"]))
        duplicate = request(
            "POST",
            "/feedback",
            token=token,
            json={
                "chat_record_id": record_id,
                "feedback_type": "remember_preference",
                "memory_title": f"图表偏好 {RUN_KEY}",
                "memory_content": "图表默认按月份升序展示",
                "memory_keywords": ["图表", "月份"],
                "idempotency_key": preference_key,
            },
        )
        assert duplicate["duplicate"] is True

        correction = request(
            "POST",
            "/feedback",
            token=token,
            json={
                "chat_record_id": record_id,
                "feedback_type": "result_wrong",
                "correction_text": f"{RUN_KEY}：净销售额必须排除未支付订单",
                "idempotency_key": f"smoke-correction-{RUN_KEY}",
            },
        )
        candidate_id = int(correction["candidate"]["id"])
        assert correction["candidate"]["status"] == "candidate"
        approved = request(
            "POST",
            f"/system/learning/{candidate_id}/approve",
            token=token,
            json={"review_note": "合成数据口径核对通过"},
        )
        assert approved["status"] == "active"
        created_memory_ids.add(int(approved["activated_memory_id"]))

        with Session(engine) as session:
            prompt, refs = get_memory_prompt(
                session,
                "请做图表并统计净销售额",
                1,
                USER,
                1,
            )
            assert "图表默认按月份升序展示" in prompt
            assert any(ref["scope"] == "personal" for ref in refs)

            metric_prompt, metric_refs, _tables = get_metric_prompt(
                session,
                "按区域统计净销售额",
                1,
                1,
                current_user=USER,
            )
            assert metric_prompt and metric_refs
            save_metric_context(
                session,
                chat_id=chat_id,
                oid=1,
                user_id=1,
                datasource_id=1,
                record_id=record_id,
                metric_refs=metric_refs,
            )
            assert looks_like_follow_up("那 7 月呢？")
            inherited_prompt, inherited_refs, inherited_tables = get_metric_prompt_by_refs(
                session,
                metric_refs,
                1,
                1,
                current_user=USER,
            )
            assert inherited_prompt
            assert inherited_refs[0]["version_id"] == metric_refs[0]["version_id"]
            assert inherited_refs[0]["inherited"] is True
            assert "adaptive_demo_sales" in inherited_tables
            session.rollback()

        revoked = request(
            "POST",
            f"/system/learning/{candidate_id}/revoke",
            token=token,
            json={"review_note": "烟雾测试完成后撤销"},
        )
        assert revoked["status"] == "revoked"
        print("Adaptive API smoke test passed: memory, feedback, review, revocation, and follow-up context")
    finally:
        with Session(engine) as session:
            jobs = session.exec(
                select(LearningJob).where(LearningJob.oid == 1)
            ).all()
            smoke_feedback_ids = {
                event.id
                for event in session.exec(select(FeedbackEvent).where(FeedbackEvent.oid == 1)).all()
                if RUN_KEY in (event.idempotency_key or "")
            }
            smoke_candidate_ids = {
                candidate.id
                for candidate in session.exec(select(LearningCandidate).where(LearningCandidate.oid == 1)).all()
                if candidate.feedback_event_id in smoke_feedback_ids
            }
            for job in jobs:
                if job.feedback_event_id in smoke_feedback_ids:
                    session.delete(job)
            for candidate in session.exec(select(LearningCandidate)).all():
                if candidate.id in smoke_candidate_ids:
                    session.delete(candidate)
            for event in session.exec(select(FeedbackEvent)).all():
                if event.id in smoke_feedback_ids:
                    session.delete(event)
            for memory in session.exec(select(MemoryEntry)).all():
                if memory.id in created_memory_ids or RUN_KEY in memory.title:
                    session.delete(memory)
            chat = session.get(Chat, chat_id)
            if chat:
                session.delete(chat)
            session.commit()


if __name__ == "__main__":
    main()
