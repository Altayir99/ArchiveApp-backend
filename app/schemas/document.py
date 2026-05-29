import uuid
from datetime import datetime
from pydantic import BaseModel


class DocumentCreate(BaseModel):
    workspace_id: uuid.UUID
    title: str
    file_type: str
    source: str
    category: str
    summary: str | None = None


class DocumentUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    source: str | None = None
    summary: str | None = None


class DocumentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    file_type: str
    source: str
    category: str
    summary: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
