import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/workspaces", tags=["Workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceService.get_all(db, user.id)


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await WorkspaceService.create(
        db, user.id, data.name, data.initials, data.color, data.text_color
    )
    return WorkspaceResponse(
        id=ws.id, name=ws.name, initials=ws.initials,
        color=ws.color, text_color=ws.text_color,
        document_count=0, created_at=ws.created_at,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await WorkspaceService.get_one(db, workspace_id, user.id)
    responses = await WorkspaceService.get_all(db, user.id)
    return next(r for r in responses if r.id == workspace_id)


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await WorkspaceService.update(
        db, workspace_id, user.id,
        name=data.name, initials=data.initials,
        color=data.color, text_color=data.text_color,
    )
    responses = await WorkspaceService.get_all(db, user.id)
    return next(r for r in responses if r.id == workspace_id)


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService.delete(db, workspace_id, user.id)
