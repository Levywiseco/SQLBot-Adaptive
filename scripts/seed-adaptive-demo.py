#!/usr/bin/env python3
"""Seed a small, synthetic and fully queryable datasource for local development."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import text
from sqlmodel import Session

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from apps.datasource.utils.utils import aes_encrypt  # noqa: E402
from common.core.config import settings  # noqa: E402
from common.core.db import engine  # noqa: E402

DATASOURCE_NAME = "Adaptive Demo Sales (synthetic)"
TABLE_NAME = "adaptive_demo_sales"


ROWS = [
    {"id": 1, "paid_at": "2026-08-03 10:00:00", "region": "华东", "customer_id": 101, "amount": 1000, "discount": 50, "status": "paid"},
    {"id": 2, "paid_at": "2026-08-05 12:30:00", "region": "华南", "customer_id": 102, "amount": 800, "discount": 20, "status": "paid"},
    {"id": 3, "paid_at": "2026-08-09 09:15:00", "region": "华东", "customer_id": 103, "amount": 450, "discount": 0, "status": "paid"},
    {"id": 4, "paid_at": "2026-08-12 18:40:00", "region": "华北", "customer_id": 104, "amount": 2500, "discount": 100, "status": "paid"},
    {"id": 5, "paid_at": "2026-08-17 08:20:00", "region": "华东", "customer_id": 105, "amount": 700, "discount": 0, "status": "cancelled"},
    {"id": 6, "paid_at": "2026-08-22 15:10:00", "region": "华南", "customer_id": 106, "amount": 300, "discount": 0, "status": "paid"},
    {"id": 7, "paid_at": "2026-07-28 11:00:00", "region": "华东", "customer_id": 107, "amount": 900, "discount": 30, "status": "paid"},
    {"id": 8, "paid_at": "2026-09-01 16:00:00", "region": "华北", "customer_id": 108, "amount": 1200, "discount": 0, "status": "paid"},
]


FIELDS = [
    ("id", "bigint", "订单主键"),
    ("paid_at", "timestamp", "支付时间；指标按此字段归属月份"),
    ("region", "varchar", "销售区域"),
    ("customer_id", "bigint", "客户标识"),
    ("amount", "numeric", "订单原始金额"),
    ("discount_amount", "numeric", "订单优惠金额"),
    ("status", "varchar", "订单状态；paid 表示已支付"),
]


def datasource_configuration() -> str:
    config = {
        "host": "127.0.0.1",
        "port": settings.POSTGRES_PORT,
        "username": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD,
        "database": settings.POSTGRES_DB,
        "driver": "",
        "extraJdbc": "",
        "dbSchema": "public",
        "filename": "",
        "sheets": [],
        "mode": "",
        "timeout": 30,
        "lowVersion": False,
        "ssl": False,
        "poolSize": 5,
    }
    return aes_encrypt(json.dumps(config, ensure_ascii=False)).decode("ascii")


def main() -> int:
    with Session(engine) as session:
        session.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id BIGINT PRIMARY KEY,
                    paid_at TIMESTAMP NOT NULL,
                    region VARCHAR(32) NOT NULL,
                    customer_id BIGINT NOT NULL,
                    amount NUMERIC(18, 2) NOT NULL,
                    discount_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
                    status VARCHAR(32) NOT NULL
                )
                """
            )
        )
        session.execute(text(f"TRUNCATE TABLE {TABLE_NAME}"))
        session.execute(
            text(
                f"""
                INSERT INTO {TABLE_NAME}
                    (id, paid_at, region, customer_id, amount, discount_amount, status)
                VALUES
                    (:id, :paid_at, :region, :customer_id, :amount, :discount, :status)
                """
            ),
            ROWS,
        )

        datasource_id = session.execute(
            text("SELECT id FROM core_datasource WHERE oid = 1 AND name = :name"),
            {"name": DATASOURCE_NAME},
        ).scalar_one_or_none()
        values = {
            "name": DATASOURCE_NAME,
            "description": "SQLBot Adaptive 本地演示数据，全部记录均为虚构数据。",
            "configuration": datasource_configuration(),
        }
        if datasource_id is None:
            datasource_id = session.execute(
                text(
                    """
                    INSERT INTO core_datasource
                        (name, description, type, type_name, configuration, create_time,
                         create_by, status, num, oid, table_relation, embedding, recommended_config)
                    VALUES
                        (:name, :description, 'pg', 'PostgreSQL', :configuration, CURRENT_TIMESTAMP,
                         1, 'Success', '1/1', 1, '[]'::jsonb, NULL, 1)
                    RETURNING id
                    """
                ),
                values,
            ).scalar_one()
        else:
            session.execute(
                text(
                    """
                    UPDATE core_datasource
                    SET description = :description,
                        configuration = :configuration,
                        status = 'Success',
                        num = '1/1'
                    WHERE id = :id
                    """
                ),
                {**values, "id": datasource_id},
            )

        table_id = session.execute(
            text("SELECT id FROM core_table WHERE ds_id = :ds_id AND table_name = :table_name"),
            {"ds_id": datasource_id, "table_name": TABLE_NAME},
        ).scalar_one_or_none()
        if table_id is None:
            table_id = session.execute(
                text(
                    """
                    INSERT INTO core_table
                        (ds_id, checked, table_name, table_comment, custom_comment, embedding)
                    VALUES
                        (:ds_id, TRUE, :table_name, :comment, :comment, NULL)
                    RETURNING id
                    """
                ),
                {
                    "ds_id": datasource_id,
                    "table_name": TABLE_NAME,
                    "comment": "虚构销售订单，用于指标、记忆和评测开发",
                },
            ).scalar_one()
        else:
            session.execute(
                text("UPDATE core_table SET checked = TRUE WHERE id = :id"),
                {"id": table_id},
            )

        for index, (name, field_type, comment) in enumerate(FIELDS):
            field_id = session.execute(
                text("SELECT id FROM core_field WHERE table_id = :table_id AND field_name = :name"),
                {"table_id": table_id, "name": name},
            ).scalar_one_or_none()
            field_values = {
                "ds_id": datasource_id,
                "table_id": table_id,
                "name": name,
                "field_type": field_type,
                "comment": comment,
                "field_index": index,
            }
            if field_id is None:
                session.execute(
                    text(
                        """
                        INSERT INTO core_field
                            (ds_id, table_id, checked, field_name, field_type,
                             field_comment, custom_comment, field_index)
                        VALUES
                            (:ds_id, :table_id, TRUE, :name, :field_type,
                             :comment, :comment, :field_index)
                        """
                    ),
                    field_values,
                )
            else:
                session.execute(
                    text(
                        """
                        UPDATE core_field
                        SET checked = TRUE, field_type = :field_type,
                            field_comment = :comment, custom_comment = :comment,
                            field_index = :field_index
                        WHERE id = :id
                        """
                    ),
                    {**field_values, "id": field_id},
                )

        session.commit()
        print(json.dumps({"datasource_id": datasource_id, "table": TABLE_NAME, "rows": len(ROWS)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
