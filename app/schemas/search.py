import uuid
from pydantic import BaseModel

from app.schemas.document import DocumentResponse
from app.schemas.workspace import WorkspaceResponse


class SearchRequest(BaseModel):
    query: str
    workspace_id: uuid.UUID | None = None


class SearchResultItem(BaseModel):
    document: DocumentResponse
    match_percent: int
    reason: str
    workspace: WorkspaceResponse


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
