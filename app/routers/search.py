from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search(
    data: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SearchService.search(db, user.id, data.query, data.workspace_id)
