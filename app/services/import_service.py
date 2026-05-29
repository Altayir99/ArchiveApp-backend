import os
import uuid
import logging
from datetime import datetime

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document
from app.models.workspace import Workspace
from app.models.import_job import ImportJob
from app.services.google_drive_service import (
    list_subfolders,
    list_files_in_folder,
    is_supported_file,
    download_file,
    file_type_from_name,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _generate_initials(name: str) -> str:
    """Generate 2-letter initials from a workspace name.

    If name has multiple words, take first letter of first 2 words.
    Otherwise take first 2 uppercase letters.
    """
    words = name.strip().split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    return name[:2].upper()


def _category_from_filename(name: str) -> str:
    """Determine document category based on filename keywords."""
    lower = name.lower()
    if any(kw in lower for kw in ("rechnung", "invoice", "beleg")):
        return "Rechnung"
    if any(kw in lower for kw in ("vertrag", "contract")):
        return "Vertrag"
    if any(kw in lower for kw in ("angebot", "offer")):
        return "Angebot"
    if any(kw in lower for kw in ("projekt", "plan")):
        return "Projekt"
    return "Sonstiges"


async def _get_or_create_workspace(
    db: AsyncSession, name: str, owner_id: uuid.UUID
) -> Workspace:
    """Look up a workspace by name + owner, create if not found."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.name == name,
            Workspace.owner_id == owner_id,
        )
    )
    ws = result.scalar_one_or_none()
    if ws:
        return ws

    ws = Workspace(
        name=name,
        initials=_generate_initials(name),
        color="#E6F1FB",
        text_color="#0C447C",
        owner_id=owner_id,
    )
    db.add(ws)
    await db.flush()
    logger.info(f"Workspace '{name}' automatisch erstellt.")
    return ws


async def _is_already_imported(db: AsyncSession, drive_file_id: str) -> bool:
    """Check if a document with this drive_file_id already exists (dedup)."""
    result = await db.execute(
        select(Document.id).where(Document.drive_file_id == drive_file_id)
    )
    return result.scalar_one_or_none() is not None


async def _process_files(
    db: AsyncSession,
    files: list[dict],
    workspace: Workspace,
    owner_id: uuid.UUID,
    counters: dict,
) -> None:
    """Process a list of Drive files: filter, dedup, download, create records."""
    for f in files:
        counters["files_found"] += 1
        file_name = f["name"]
        file_id = f["id"]
        mime_type = f.get("mimeType", "")

        # Check supported type
        if not is_supported_file(file_name, mime_type):
            counters["files_skipped"] += 1
            logger.debug(f"Übersprungen (nicht unterstützt): {file_name}")
            continue

        # Dedup check
        if await _is_already_imported(db, file_id):
            counters["files_skipped"] += 1
            logger.debug(f"Übersprungen (bereits importiert): {file_name}")
            continue

        # Download
        dest_dir = os.path.join(
            settings.UPLOAD_DIR, str(owner_id), str(workspace.id)
        )
        dest_path = os.path.join(dest_dir, f"{file_id}_{file_name}")

        try:
            file_size = download_file(file_id, dest_path)
        except Exception as e:
            logger.error(f"Download fehlgeschlagen für {file_name}: {e}")
            counters["files_skipped"] += 1
            continue

        # Create document record
        doc = Document(
            workspace_id=workspace.id,
            title=file_name,
            file_type=file_type_from_name(file_name),
            source="Google Drive",
            category=_category_from_filename(file_name),
            file_path=dest_path,
            file_size=file_size,
            drive_file_id=file_id,
            summary=None,
        )
        db.add(doc)
        await db.flush()
        counters["files_imported"] += 1
        logger.info(f"Importiert: {file_name} → Workspace '{workspace.name}'")


async def import_from_drive(db: AsyncSession, owner_id: uuid.UUID) -> dict:
    """Main import function: scan Drive inbox, dedup, download, create documents.

    Returns dict with job_id, files_found, files_imported, files_skipped.
    """
    # Create ImportJob
    job = ImportJob(
        source="google_drive",
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(job)
    await db.flush()

    counters = {"files_found": 0, "files_imported": 0, "files_skipped": 0}

    try:
        folder_id = settings.DRIVE_INBOX_FOLDER_ID
        if not folder_id:
            raise ValueError("DRIVE_INBOX_FOLDER_ID ist nicht konfiguriert.")

        # 1. Process subfolders → each subfolder name = workspace name
        subfolders = list_subfolders(folder_id)
        for sf in subfolders:
            workspace = await _get_or_create_workspace(db, sf["name"], owner_id)
            files = list_files_in_folder(sf["id"])
            await _process_files(db, files, workspace, owner_id, counters)

        # 2. Process files directly in the root inbox folder → default workspace
        default_ws = await _get_or_create_workspace(
            db, settings.DRIVE_DEFAULT_WORKSPACE_NAME, owner_id
        )
        root_files = list_files_in_folder(folder_id)
        await _process_files(db, root_files, default_ws, owner_id, counters)

        # Update job: success
        job.status = "success"
        job.files_found = counters["files_found"]
        job.files_imported = counters["files_imported"]
        job.files_skipped = counters["files_skipped"]
        job.finished_at = datetime.utcnow()
        await db.flush()

        logger.info(
            f"Drive-Import abgeschlossen: "
            f"{counters['files_found']} gefunden, "
            f"{counters['files_imported']} importiert, "
            f"{counters['files_skipped']} übersprungen."
        )

    except Exception as e:
        job.status = "error"
        job.error_message = str(e)
        job.files_found = counters["files_found"]
        job.files_imported = counters["files_imported"]
        job.files_skipped = counters["files_skipped"]
        job.finished_at = datetime.utcnow()
        await db.flush()
        logger.error(f"Drive-Import fehlgeschlagen: {e}")
        raise

    return {
        "job_id": str(job.id),
        "files_found": counters["files_found"],
        "files_imported": counters["files_imported"],
        "files_skipped": counters["files_skipped"],
    }


async def get_last_status(db: AsyncSession) -> ImportJob | None:
    """Return the most recent ImportJob."""
    result = await db.execute(
        select(ImportJob).order_by(desc(ImportJob.started_at)).limit(1)
    )
    return result.scalar_one_or_none()
