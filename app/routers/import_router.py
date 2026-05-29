from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_factory
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.import_job import ImportSyncResponse, ImportStatusResponse
from app.services.import_service import import_from_drive, get_last_status

router = APIRouter(prefix="/api/import", tags=["Import"])


async def _run_import_in_background(user_id):
    """Run the import in a background task with its own DB session."""
    async with async_session_factory() as db:
        try:
            await import_from_drive(db, user_id)
            await db.commit()
        except Exception:
            await db.rollback()


@router.post("/drive/sync", response_model=ImportSyncResponse)
async def trigger_drive_sync(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Trigger a manual Drive import for the current user.

    Runs in the background and returns immediately.
    """
    background_tasks.add_task(_run_import_in_background, user.id)

    return ImportSyncResponse(job_id="pending", status="running")


@router.get("/status", response_model=ImportStatusResponse)
async def get_import_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent import job status."""
    job = await get_last_status(db)

    if not job:
        return ImportStatusResponse(
            status="never",
            files_found=0,
            files_imported=0,
            files_skipped=0,
            last_sync=None,
        )

    return ImportStatusResponse(
        status=job.status,
        files_found=job.files_found,
        files_imported=job.files_imported,
        files_skipped=job.files_skipped,
        last_sync=job.started_at,
    )
