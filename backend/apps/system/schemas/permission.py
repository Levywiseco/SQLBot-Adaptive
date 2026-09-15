from contextvars import ContextVar
from functools import wraps
from inspect import signature
from typing import Optional
from fastapi import HTTPException, Request
from sqlalchemy import or_
from pydantic import BaseModel
import re
from starlette.middleware.base import BaseHTTPMiddleware
from sqlmodel import Session, select
from apps.chat.models.chat_model import Chat
from apps.datasource.crud.datasource import get_ws_ds
from apps.datasource.models.datasource import CoreDatasource
from common.core.db import engine
from apps.system.models.system_model import UserDatasourceModel
from apps.system.schemas.system_schema import UserInfoDTO

from common.utils.locale import I18n
i18n = I18n()

class SqlbotPermission(BaseModel):
    role: Optional[list[str]] = None
    type: Optional[str] = None
    keyExpression: Optional[str] = None

async def get_ws_resource(oid, type) -> list:
    with Session(engine) as session:
        stmt = None
        if type == 'ds' or type == 'datasource':
            return await get_ws_ds(session, oid)
        if type == 'chat':
            stmt = select(Chat.id).where(Chat.oid == oid) 
        if stmt is not None:
            db_list = session.exec(stmt).all()
            return db_list
        return []     
            

async def check_ws_permission(current_user: UserInfoDTO, type, resource) -> bool:
    if not resource or (isinstance(resource, list) and len(resource) == 0):
        return True
    
    resource_id_list = await get_ws_resource(current_user.oid, type)
    if type in ('ds', 'datasource') and not current_user.isAdmin and current_user.weight <= 0:
        with Session(engine) as session:
            resource_id_list = session.exec(
                select(UserDatasourceModel.datasource_id).where(
                    UserDatasourceModel.uid == current_user.id,
                    UserDatasourceModel.datasource_id.in_(resource_id_list),
                )
            ).all()
    if type == 'chat' and not current_user.isAdmin and current_user.weight <= 0:
        with Session(engine) as session:
            assigned_ds = select(UserDatasourceModel.datasource_id).where(
                UserDatasourceModel.uid == current_user.id
            )
            resource_id_list = session.exec(
                select(Chat.id).where(
                    Chat.oid == current_user.oid,
                    or_(Chat.origin != 0, Chat.datasource.is_(None), Chat.datasource.in_(assigned_ds)),
                )
            ).all()
    if not resource_id_list:
        return False
    if isinstance(resource, list):
        return set(resource).issubset(set(resource_id_list))
    return resource in resource_id_list
        
 
def require_permissions(permission: SqlbotPermission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = RequestContext.get_request()
            
            current_user: UserInfoDTO = getattr(request.state, 'current_user', None)
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="用户未认证"
                )
            trans = i18n(request)
            
            if current_user.isAdmin and not permission.type:
                return await func(*args, **kwargs)
            role_list = permission.role
            keyExpression = permission.keyExpression
            resource_type = permission.type
            
            if role_list:
                if 'admin' in role_list and not current_user.isAdmin:
                    #raise Exception('no permission to execute, only for admin')
                    raise Exception(trans('i18n_permission.only_admin'))
                if 'ws_admin' in role_list and current_user.weight <= 0 and not current_user.isAdmin:
                    #raise Exception('no permission to execute, only for workspace admin')
                    raise Exception(trans('i18n_permission.only_ws_admin'))
            if not resource_type:
                return await func(*args, **kwargs)
            if keyExpression:
                sig = signature(func)
                bound_args = sig.bind_partial(*args, **kwargs)
                bound_args.apply_defaults()
                
                if keyExpression.startswith("args["):
                    if match := re.match(r"args\[(\d+)\]", keyExpression):
                        index = int(match.group(1))
                        value = bound_args.args[index]
                        if await check_ws_permission(current_user, resource_type, value):
                            return await func(*args, **kwargs)
                        #raise Exception('no permission to execute or resource do not exist!')
                        raise Exception(trans('i18n_permission.permission_resource_limit'))
                            
                parts = keyExpression.split('.')
                if not bound_args.arguments.get(parts[0]):
                    return await func(*args, **kwargs)
                value = bound_args.arguments[parts[0]]
                for part in parts[1:]:
                    value = getattr(value, part)
                if await check_ws_permission(current_user, resource_type, value):
                    return await func(*args, **kwargs)
                raise Exception(trans('i18n_permission.permission_resource_limit'))
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

class RequestContext:
    
    _current_request: ContextVar[Request] = ContextVar("_current_request")
    @classmethod
    def set_request(cls, request: Request):
        return cls._current_request.set(request)
    
    @classmethod
    def get_request(cls) -> Request:
        try:
            return cls._current_request.get()
        except LookupError:
            raise RuntimeError(
                "No request context found. "
                "Make sure RequestContextMiddleware is installed."
            )
    
    @classmethod
    def reset(cls, token):
        cls._current_request.reset(token)

class RequestContextMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        token = RequestContext.set_request(request)
        try:
            response = await call_next(request)
            return response
        finally:
            RequestContext.reset(token)
