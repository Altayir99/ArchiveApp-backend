"""Background worker: periodically syncs Google Drive inbox.

Uses APScheduler AsyncIOScheduler to run import_from_drive
every DRIVE_SYNC_INTERVAL_MINUTES minutes.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import get_settings
from app.database import async_session_factory
from app.models.user import User
from app.services.import_service import import_from_drive

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler: AsyncIOScheduler | None = None


async def _drive_sync_job():
    """Scheduled job: import files from Google Drive for the first registered user."""
    try:
        async with async_session_factory() as db:
            try:
                # Find the first registered user (system owner)
                result = await db.execute(select(User).limit(1))
                user = result.scalar_one_or_none()

                if not user:
                    logger.info("Drive-Sync übersprungen: Keine Benutzer registriert.")
                    return

                logger.info(f"Drive-Sync gestartet für Benutzer: {user.email}")
                result = await import_from_drive(db, user.id)
                await db.commit()

                logger.info(
                    f"Drive-Sync abgeschlossen: "
                    f"{result['files_imported']} importiert, "
                    f"{result['files_skipped']} übersprungen."
                )
            except Exception as e:
                await db.rollback()
                logger.error(f"Drive-Sync fehlgeschlagen: {e}")

    except Exception as e:
        # Outer catch: DB connection issues etc. — never crash the scheduler
        logger.error(f"Drive-Sync kritischer Fehler: {e}")


def start_scheduler():
    """Start the background scheduler for Drive sync."""
    global _scheduler

    if not settings.DRIVE_INBOX_FOLDER_ID:
        logger.warning(
            "Drive-Sync nicht aktiviert: DRIVE_INBOX_FOLDER_ID ist nicht gesetzt."
        )
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _drive_sync_job,
        "interval",
        minutes=settings.DRIVE_SYNC_INTERVAL_MINUTES,
        id="drive_sync",
        name="Google Drive Inbox Sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        f"Drive-Sync geplant: alle {settings.DRIVE_SYNC_INTERVAL_MINUTES} Minuten."
    )


def shutdown_scheduler():
    """Shutdown the background scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Drive-Sync Scheduler gestoppt.")
        _scheduler = None
