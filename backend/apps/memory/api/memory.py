from typing import Optional

from fastapi import APIRouter, Query

from apps.memory.crud.memory import (
    create_memory,
    delete_memory,
    get_memory,
    list_memories,
    set_memory_status,
    update_memory,
)
from apps.memory.schemas.memory import MemoryCreate, MemoryStatusUpdate, MemoryUpdate
from common.core.deps import CurrentUser, SessionDep

router = APIRouter(tags=["Adaptive Memory"], prefix="/system/memories")


@router.get("/page/{current_page}/{page_size}")
async def page(
    session: SessionDep,
    current_user: CurrentUser,
    current_page: int,
    page_size: int,
    keyword: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    scope: str = Query(default="personal"),
    datasource_id: Optional[int] = Query(default=None),
):
    return list_memories(
        session,
        current_user,
        current_page,
        page_size,
        keyword=keyword,
        status=status,
        scope=scope,
        datasource_id=datasource_id,
    )


@router.post("")
async def create(session: SessionDep, current_user: CurrentUser, payload: MemoryCreate):
    memory, _ = create_memory(session, payload, current_user)
    return memory


@router.get("/{memory_id}")
async def detail(session: SessionDep, current_user: CurrentUser, memory_id: int):
    return get_memory(session, memory_id, current_user)


@router.put("/{memory_id}")
async def edit(
    session: SessionDep,
    current_user: CurrentUser,
    memory_id: int,
    payload: MemoryUpdate,
):
    return update_memory(session, memory_id, payload, current_user)


@router.post("/{memory_id}/status")
async def change_status(
    session: SessionDep,
    current_user: CurrentUser,
    memory_id: int,
    payload: MemoryStatusUpdate,
):
    return set_memory_status(session, memory_id, payload.status, current_user)


@router.delete("/{memory_id}")
async def remove(session: SessionDep, current_user: CurrentUser, memory_id: int):
    return delete_memory(session, memory_id, current_user)
