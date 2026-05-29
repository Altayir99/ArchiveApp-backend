import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    workspace_id: uuid.UUID | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.get_all(db, user.id, workspace_id)


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    data: DocumentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await DocumentService.create(
        db, user.id, data.workspace_id, data.title,
        data.file_type, data.source, data.category, data.summary,
    )
    return doc


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.get_one(db, doc_id, user.id)


@router.put("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: uuid.UUID,
    data: DocumentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.update(
        db, doc_id, user.id,
        title=data.title, category=data.category,
        source=data.source, summary=data.summary,
    )


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await DocumentService.delete(db, doc_id, user.id)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: uuid.UUID = Form(...),
    category: str = Form("Sonstiges"),
    source: str = Form("Manuell"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.upload(
        db, user.id, workspace_id, file, category, source
    )


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await DocumentService.get_one(db, doc_id, user.id)
    if not doc.file_path:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keine Datei vorhanden.",
        )
    return FileResponse(doc.file_path, filename=doc.title)
