import uuid

from sqlalchemy import select, func, desc, text, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.workspace import Workspace
from app.schemas.search import SearchResultItem, SearchResponse
from app.schemas.document import DocumentResponse
from app.schemas.workspace import WorkspaceResponse


class SearchService:
    @staticmethod
    async def search(
        db: AsyncSession,
        owner_id: uuid.UUID,
        query: str,
        workspace_id: uuid.UUID | None = None,
    ) -> SearchResponse:
        ts_query = func.plainto_tsquery("german", query)

        rank_expr = func.ts_rank(Document.search_vector, ts_query)

        stmt = (
            select(Document, Workspace, rank_expr.label("rank"))
            .join(Workspace)
            .where(
                Workspace.owner_id == owner_id,
                Document.search_vector.op("@@")(ts_query),
            )
            .order_by(desc("rank"))
            .limit(20)
        )

        if workspace_id:
            stmt = stmt.where(Document.workspace_id == workspace_id)

        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            return SearchResponse(query=query, results=[])

        max_rank = max(r.rank for r in rows) if rows else 1.0
        if max_rank == 0:
            max_rank = 1.0

        items = []
        for row in rows:
            doc = row.Document
            ws = row.Workspace
            rank = row.rank

            raw_percent = (rank / max_rank) * 100
            match_percent = max(40, min(100, int(raw_percent * 0.6 + 40)))

            if match_percent >= 80:
                reason = f"Hohe Uebereinstimmung mit '{query}' in Titel und Inhalt."
            elif match_percent >= 60:
                reason = f"Teilweise Uebereinstimmung mit '{query}'."
            else:
                reason = f"Schwache Uebereinstimmung mit '{query}'."

            items.append(
                SearchResultItem(
                    document=DocumentResponse.model_validate(doc),
                    match_percent=match_percent,
                    reason=reason,
                    workspace=WorkspaceResponse(
                        id=ws.id,
                        name=ws.name,
                        initials=ws.initials,
                        color=ws.color,
                        text_color=ws.text_color,
                        created_at=ws.created_at,
                    ),
                )
            )

        return SearchResponse(query=query, results=items)
