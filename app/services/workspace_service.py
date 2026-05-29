import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.models.document import Document
from app.schemas.workspace import WorkspaceResponse


class WorkspaceService:
    @staticmethod
    async def get_all(db: AsyncSession, owner_id: uuid.UUID) -> list[WorkspaceResponse]:
        result = await db.execute(
            select(Workspace).where(Workspace.owner_id == owner_id)
        )
        workspaces = result.scalars().all()

        responses = []
        for ws in workspaces:
            count_result = await db.execute(
                select(func.count(Document.id)).where(Document.workspace_id == ws.id)
            )
            doc_count = count_result.scalar() or 0

            last_doc_result = await db.execute(
                select(Document)
                .where(Document.workspace_id == ws.id)
                .order_by(desc(Document.created_at))
                .limit(1)
            )
            last_doc = last_doc_result.scalar_one_or_none()

            responses.append(
                WorkspaceResponse(
                    id=ws.id,
                    name=ws.name,
                    initials=ws.initials,
                    color=ws.color,
                    text_color=ws.text_color,
                    document_count=doc_count,
                    last_document_title=last_doc.title if last_doc else None,
                    last_document_date=(
                        last_doc.created_at.strftime("%d.%m.%Y") if last_doc else None
                    ),
                    created_at=ws.created_at,
                )
            )
        return responses

    @staticmethod
    async def create(db: AsyncSession, owner_id: uuid.UUID, name: str, initials: str, color: str, text_color: str) -> Workspace:
        ws = Workspace(
            name=name,
            initials=initials,
            color=color,
            text_color=text_color,
            owner_id=owner_id,
        )
        db.add(ws)
        await db.flush()
        return ws

    @staticmethod
    async def get_one(db: AsyncSession, workspace_id: uuid.UUID, owner_id: uuid.UUID) -> Workspace:
        result = await db.execute(
            select(Workspace).where(
                Workspace.id == workspace_id,
                Workspace.owner_id == owner_id,
            )
        )
        ws = result.scalar_one_or_none()
        if not ws:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace nicht gefunden.")
        return ws

    @staticmethod
    async def update(db: AsyncSession, workspace_id: uuid.UUID, owner_id: uuid.UUID, **kwargs) -> Workspace:
        ws = await WorkspaceService.get_one(db, workspace_id, owner_id)
        for key, value in kwargs.items():
            if value is not None:
                setattr(ws, key, value)
        await db.flush()
        return ws

    @staticmethod
    async def delete(db: AsyncSession, workspace_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        ws = await WorkspaceService.get_one(db, workspace_id, owner_id)
        await db.delete(ws)
        await db.flush()
