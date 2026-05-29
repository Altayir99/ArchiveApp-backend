from datetime import datetime
from pydantic import BaseModel


class ImportSyncResponse(BaseModel):
    job_id: str
    status: str


class ImportStatusResponse(BaseModel):
    last_sync: datetime | None = None
    status: str = "never"
    files_found: int = 0
    files_imported: int = 0
    files_skipped: int = 0
