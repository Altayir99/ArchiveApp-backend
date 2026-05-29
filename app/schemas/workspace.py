import uuid
from datetime import datetime
from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str
    initials: str
    color: str
    text_color: str


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    initials: str | None = None
    color: str | None = None
    text_color: str | None = None


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    initials: str
    color: str
    text_color: str
    document_count: int = 0
    last_document_title: str | None = None
    last_document_date: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
