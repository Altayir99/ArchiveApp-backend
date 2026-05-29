import os
import uuid
from datetime import datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.workspace import Workspace
from app.core.config import get_settings

settings = get_settings()

ALLOWED_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
    "image/jpeg": "JPG",
    "image/png": "PNG",
}


class DocumentService:
    @staticmethod
    async def get_all(
        db: AsyncSession, owner_id: uuid.UUID, workspace_id: uuid.UUID | None = None
    ) -> list[Document]:
        query = (
            select(Document)
            .join(Workspace)
            .where(Workspace.owner_id == owner_id)
        )
        if workspace_id:
            query = query.where(Document.workspace_id == workspace_id)
        query = query.order_by(desc(Document.created_at))
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_one(
        db: AsyncSession, doc_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Document:
        result = await db.execute(
            select(Document)
            .join(Workspace)
            .where(Document.id == doc_id, Workspace.owner_id == owner_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dokument nicht gefunden.",
            )
        return doc

    @staticmethod
    async def create(
        db: AsyncSession,
        owner_id: uuid.UUID,
        workspace_id: uuid.UUID,
        title: str,
        file_type: str,
        source: str,
        category: str,
        summary: str | None = None,
    ) -> Document:
        ws_result = await db.execute(
            select(Workspace).where(
                Workspace.id == workspace_id, Workspace.owner_id == owner_id
            )
        )
        if not ws_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace nicht gefunden.",
            )

        doc = Document(
            workspace_id=workspace_id,
            title=title,
            file_type=file_type,
            source=source,
            category=category,
            summary=summary,
        )
        db.add(doc)
        await db.flush()
        return doc

    @staticmethod
    async def upload(
        db: AsyncSession,
        owner_id: uuid.UUID,
        workspace_id: uuid.UUID,
        file: UploadFile,
        category: str,
        source: str = "Manuell",
    ) -> Document:
        content_type = file.content_type or ""
        file_type = ALLOWED_TYPES.get(content_type)
        if not file_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dateityp '{content_type}' nicht erlaubt.",
            )

        content = await file.read()
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Datei zu gross. Max {settings.MAX_UPLOAD_SIZE_MB}MB.",
            )

        ws_result = await db.execute(
            select(Workspace).where(
                Workspace.id == workspace_id, Workspace.owner_id == owner_id
            )
        )
        if not ws_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace nicht gefunden.",
            )

        upload_dir = os.path.join(
            settings.UPLOAD_DIR, str(owner_id), str(workspace_id)
        )
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"{uuid.uuid4()}.{file_type.lower()}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            workspace_id=workspace_id,
            title=file.filename or filename,
            file_type=file_type,
            source=source,
            category=category,
            file_path=file_path,
            file_size=len(content),
        )
        db.add(doc)
        await db.flush()
        return doc

    @staticmethod
    async def update(
        db: AsyncSession, doc_id: uuid.UUID, owner_id: uuid.UUID, **kwargs
    ) -> Document:
        doc = await DocumentService.get_one(db, doc_id, owner_id)
        for key, value in kwargs.items():
            if value is not None:
                setattr(doc, key, value)
        await db.flush()
        return doc

    @staticmethod
    async def delete(
        db: AsyncSession, doc_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        doc = await DocumentService.get_one(db, doc_id, owner_id)
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        await db.delete(doc)
        await db.flush()
