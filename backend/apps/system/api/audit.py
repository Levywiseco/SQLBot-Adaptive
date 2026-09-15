from datetime import datetime
from io import BytesIO
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import String, cast, func, or_
from sqlmodel import select

from apps.system.models.system_model import WorkspaceModel
from apps.system.schemas.permission import SqlbotPermission, require_permissions
from common.audit.models.log_model import OperationType, SystemLog
from common.core.deps import SessionDep, Trans


router = APIRouter(tags=['system_audit'], prefix='/system/audit')


def _split(value: Optional[str]) -> list[str]:
    return [item for item in (value or '').split('__') if item]


def _label(trans: Trans, value: Optional[str]) -> str:
    if not value:
        return '-'
    return trans(f'i18n_audit.{value}')


def _filtered_query(
    name: Optional[str],
    opt_type_list: Optional[str],
    uid_list: Optional[str],
    oid_list: Optional[str],
    log_status: Optional[str],
    time_range: Optional[str],
):
    stmt = select(SystemLog)
    if name:
        pattern = f'%{name}%'
        stmt = stmt.where(
            or_(
                SystemLog.user_name.ilike(pattern),
                SystemLog.operation_detail.ilike(pattern),
                SystemLog.resource_name.ilike(pattern),
                SystemLog.ip_address.ilike(pattern),
                cast(SystemLog.resource_id, String).ilike(pattern),
            )
        )
    operation_types = _split(opt_type_list)
    if operation_types:
        stmt = stmt.where(SystemLog.operation_type.in_(operation_types))
    user_ids = [int(item) for item in _split(uid_list) if item.isdigit()]
    if user_ids:
        stmt = stmt.where(SystemLog.user_id.in_(user_ids))
    workspace_ids = [int(item) for item in _split(oid_list) if item.lstrip('-').isdigit()]
    if workspace_ids:
        stmt = stmt.where(SystemLog.oid.in_(workspace_ids))
    statuses = _split(log_status)
    if statuses:
        stmt = stmt.where(SystemLog.operation_status.in_(statuses))
    timestamps = [int(item) for item in _split(time_range) if item.isdigit()]
    if timestamps:
        stmt = stmt.where(SystemLog.create_time >= datetime.fromtimestamp(timestamps[0] / 1000))
    if len(timestamps) > 1:
        stmt = stmt.where(SystemLog.create_time <= datetime.fromtimestamp(timestamps[1] / 1000))
    return stmt


def _serialize(log: SystemLog, workspace_names: dict[int, str], trans: Trans) -> dict:
    operation_name = _label(trans, log.operation_type)
    module_name = _label(trans, log.module)
    detail = log.operation_detail or f'{module_name} - {operation_name}'
    return {
        'id': str(log.id),
        'operation_type_name': operation_name,
        'operation_detail_info': detail,
        'user_name': log.user_name or '-',
        'resource_name': log.resource_name or '-',
        'operation_status': log.operation_status,
        'operation_status_name': _label(trans, log.operation_status),
        'ip_address': log.ip_address or '-',
        'create_time': log.create_time,
        'oid_name': workspace_names.get(log.oid, '-') if log.oid not in (None, -1) else '-',
        'oid': str(log.oid) if log.oid is not None else '-1',
        'error_message': log.error_message or '',
        'remark': log.remark or '',
    }


def _workspace_names(session: SessionDep, logs: list[SystemLog]) -> dict[int, str]:
    workspace_ids = {log.oid for log in logs if log.oid not in (None, -1)}
    if not workspace_ids:
        return {}
    rows = session.exec(
        select(WorkspaceModel.id, WorkspaceModel.name).where(WorkspaceModel.id.in_(workspace_ids))
    ).all()
    return {row[0]: row[1] for row in rows}


@router.get('/page/{page_num}/{page_size}')
@require_permissions(permission=SqlbotPermission(role=['admin']))
async def page(
    session: SessionDep,
    trans: Trans,
    page_num: int,
    page_size: int,
    name: Optional[str] = Query(None),
    opt_type_list: Optional[str] = Query(None),
    uid_list: Optional[str] = Query(None),
    oid_list: Optional[str] = Query(None),
    log_status: Optional[str] = Query(None),
    time_range: Optional[str] = Query(None),
):
    stmt = _filtered_query(name, opt_type_list, uid_list, oid_list, log_status, time_range)
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    logs = session.exec(
        stmt.order_by(SystemLog.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size)
    ).all()
    workspace_names = _workspace_names(session, logs)
    return {
        'items': [_serialize(log, workspace_names, trans) for log in logs],
        'total': total,
        'page': page_num,
        'size': page_size,
    }


@router.get('/get_options')
@require_permissions(permission=SqlbotPermission(role=['admin']))
async def get_options(trans: Trans):
    return [
        {'id': operation.value, 'name': _label(trans, operation.value)}
        for operation in OperationType
    ]


@router.get('/export')
@require_permissions(permission=SqlbotPermission(role=['admin']))
async def export(
    session: SessionDep,
    trans: Trans,
    name: Optional[str] = Query(None),
    opt_type_list: Optional[str] = Query(None),
    uid_list: Optional[str] = Query(None),
    oid_list: Optional[str] = Query(None),
    log_status: Optional[str] = Query(None),
    time_range: Optional[str] = Query(None),
):
    stmt = _filtered_query(name, opt_type_list, uid_list, oid_list, log_status, time_range)
    logs = session.exec(stmt.order_by(SystemLog.create_time.desc())).all()
    workspace_names = _workspace_names(session, logs)
    rows = [_serialize(log, workspace_names, trans) for log in logs]

    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet(title=trans('i18n_audit.system_log'))
    sheet.append([
        trans('i18n_audit.operation_type_name'),
        trans('i18n_audit.operation_detail_info'),
        trans('i18n_audit.user_name'),
        trans('i18n_audit.oid_name'),
        trans('i18n_audit.operation_status_name'),
        trans('i18n_audit.ip_address'),
        trans('i18n_audit.create_time'),
        trans('i18n_audit.error_message'),
    ])
    for row in rows:
        sheet.append([
            row['operation_type_name'], row['operation_detail_info'], row['user_name'],
            row['oid_name'], row['operation_status_name'], row['ip_address'],
            row['create_time'], row['error_message'],
        ])
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    filename = quote(f"{trans('i18n_audit.system_log')}.xlsx")
    return StreamingResponse(
        stream,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{filename}"},
    )
