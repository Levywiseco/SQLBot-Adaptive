"""Seed idempotent synthetic memory and feedback records for the adaptive UI demo."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from apps.chat.models.chat_model import Chat, ChatRecord  # noqa: E402
from apps.feedback.crud.feedback import create_feedback  # noqa: E402
from apps.feedback.schemas.feedback import FeedbackCreate  # noqa: E402
from apps.memory.crud.memory import create_memory, update_retrieval_trace  # noqa: E402
from apps.memory.schemas.memory import MemoryCreate  # noqa: E402
from apps.metrics.crud.metric import get_metric_prompt  # noqa: E402
from common.core.db import engine  # noqa: E402

USER = SimpleNamespace(id=1, oid=1, isAdmin=True, weight=1)
DEMO_CHAT_BRIEF = "Adaptive learning demo (synthetic)"


def main() -> None:
    with Session(engine) as session:
        memory, memory_existed = create_memory(
            session,
            MemoryCreate(
                title="金额展示单位",
                content="金额默认用万元展示，并保留两位小数",
                memory_type="preference",
                scope="personal",
                keywords=["金额", "销售额", "收入"],
                datasource_id=1,
                priority=1,
            ),
            USER,
            source_type="manual",
            source_reference_id="adaptive-demo-v1",
            allow_duplicate=True,
        )

        chat = session.exec(select(Chat).where(Chat.brief == DEMO_CHAT_BRIEF)).first()
        if not chat:
            chat = Chat(
                oid=1,
                create_time=datetime.now(),
                create_by=1,
                brief=DEMO_CHAT_BRIEF,
                chat_type="chat",
                datasource=1,
                engine_type="pg",
            )
            session.add(chat)
            session.flush()

        record = session.exec(
            select(ChatRecord).where(
                ChatRecord.chat_id == chat.id,
                ChatRecord.question == "按区域统计净销售额",
            )
        ).first()
        if not record:
            record = ChatRecord(
                chat_id=chat.id,
                create_time=datetime.now(),
                finish_time=datetime.now(),
                create_by=1,
                datasource=1,
                engine_type="pg",
                question="按区域统计净销售额",
                sql="SELECT region, SUM(amount - discount_amount) AS net_sales FROM adaptive_demo_sales WHERE status = 'paid' GROUP BY region",
                sql_answer="已命中已发布指标“净销售额 v1”，并按指标口径排除未支付订单。",
                data=json.dumps(
                    {
                        "fields": ["region", "net_sales"],
                        "fields_info": [
                            {"name": "region", "is_numeric": False},
                            {"name": "net_sales", "is_numeric": True},
                        ],
                        "data": [
                            {"region": "华北", "net_sales": 3600.0},
                            {"region": "华东", "net_sales": 2270.0},
                            {"region": "华南", "net_sales": 1080.0},
                        ],
                    },
                    ensure_ascii=False,
                ),
                chart=json.dumps(
                    {
                        "type": "table",
                        "title": "按区域统计净销售额（演示数据）",
                        "axis": {
                            "x": {"name": "区域", "value": "region"},
                            "y": {"name": "净销售额", "value": "net_sales"},
                        },
                        "columns": [
                            {"name": "区域", "value": "region"},
                            {"name": "净销售额", "value": "net_sales"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                finish=True,
            )
            session.add(record)
            session.flush()
        else:
            record.sql_answer = "已命中已发布指标“净销售额 v1”，并按指标口径排除未支付订单。"
            record.data = json.dumps(
                {
                    "fields": ["region", "net_sales"],
                    "fields_info": [
                        {"name": "region", "is_numeric": False},
                        {"name": "net_sales", "is_numeric": True},
                    ],
                    "data": [
                        {"region": "华北", "net_sales": 3600.0},
                        {"region": "华东", "net_sales": 2270.0},
                        {"region": "华南", "net_sales": 1080.0},
                    ],
                },
                ensure_ascii=False,
            )
            record.chart = json.dumps(
                {
                    "type": "table",
                    "title": "按区域统计净销售额（演示数据）",
                    "axis": {
                        "x": {"name": "区域", "value": "region"},
                        "y": {"name": "净销售额", "value": "net_sales"},
                    },
                    "columns": [
                        {"name": "区域", "value": "region"},
                        {"name": "净销售额", "value": "net_sales"},
                    ],
                },
                ensure_ascii=False,
            )
            session.add(record)
            session.flush()

        _prompt, metric_refs, _tables = get_metric_prompt(
            session,
            record.question,
            1,
            1,
            current_user=USER,
        )
        update_retrieval_trace(
            session,
            record_id=int(record.id),
            oid=1,
            user_id=1,
            datasource_id=1,
            question=record.question,
            metric_refs=metric_refs,
            memory_refs=[],
        )
        feedback = create_feedback(
            session,
            FeedbackCreate(
                chat_record_id=int(record.id),
                feedback_type="result_wrong",
                correction_text="净销售额必须排除未支付订单，并按支付日期归属月份",
                idempotency_key="adaptive-demo-result-correction-v1",
            ),
            USER,
        )
        chat_id = int(chat.id)
        record_id = int(record.id)
        candidate_id = int(feedback["candidate"]["id"])
        candidate_status = feedback["candidate"]["status"]
        session.commit()

    print(
        {
            "memory_id": memory["id"],
            "memory_already_existed": memory_existed,
            "chat_id": chat_id,
            "chat_record_id": record_id,
            "candidate_id": candidate_id,
            "candidate_status": candidate_status,
        }
    )


if __name__ == "__main__":
    main()
