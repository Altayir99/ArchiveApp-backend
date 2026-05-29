import os
import io
import logging
from pathlib import Path
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".jpg", ".jpeg", ".png"}
GOOGLE_NATIVE_MIMETYPES = {
    "application/vnd.google-apps.document",
    "application/vnd.google-apps.spreadsheet",
    "application/vnd.google-apps.presentation",
    "application/vnd.google-apps.form",
    "application/vnd.google-apps.drawing",
    "application/vnd.google-apps.site",
    "application/vnd.google-apps.folder",
}

_drive_client = None


def _get_drive_client():
    """Build and cache the Google Drive v3 service object."""
    global _drive_client
    if _drive_client is not None:
        return _drive_client

    settings = get_settings()
    sa_file = settings.GOOGLE_SERVICE_ACCOUNT_FILE

    if not sa_file or not os.path.exists(sa_file):
        raise FileNotFoundError(
            f"Service-Account-Datei nicht gefunden: {sa_file}. "
            "Bitte GOOGLE_SERVICE_ACCOUNT_FILE in .env setzen."
        )

    credentials = service_account.Credentials.from_service_account_file(
        sa_file, scopes=SCOPES
    )
    _drive_client = build("drive", "v3", credentials=credentials, cache_discovery=False)
    logger.info("Google Drive Client erfolgreich initialisiert.")
    return _drive_client


def list_subfolders(folder_id: str) -> list[dict]:
    """List all subfolders inside a given Drive folder.

    Returns list of {id, name}.
    """
    try:
        service = _get_drive_client()
        results = []
        page_token = None

        while True:
            response = service.files().list(
                q=(
                    f"'{folder_id}' in parents "
                    "and mimeType = 'application/vnd.google-apps.folder' "
                    "and trashed = false"
                ),
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
            ).execute()

            results.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        logger.info(f"{len(results)} Unterordner in Ordner {folder_id} gefunden.")
        return results

    except HttpError as e:
        logger.error(f"Drive API Fehler beim Auflisten der Unterordner: {e}")
        raise RuntimeError(f"Drive API Fehler: {e}") from e


def list_files_in_folder(folder_id: str) -> list[dict]:
    """List all non-folder files in a Drive folder.

    Returns list of {id, name, mimeType, size}.
    Handles pagination to return ALL files.
    """
    try:
        service = _get_drive_client()
        results = []
        page_token = None

        while True:
            response = service.files().list(
                q=(
                    f"'{folder_id}' in parents "
                    "and mimeType != 'application/vnd.google-apps.folder' "
                    "and trashed = false"
                ),
                fields="nextPageToken, files(id, name, mimeType, size)",
                pageToken=page_token,
            ).execute()

            results.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        logger.info(f"{len(results)} Dateien in Ordner {folder_id} gefunden.")
        return results

    except HttpError as e:
        logger.error(f"Drive API Fehler beim Auflisten der Dateien: {e}")
        raise RuntimeError(f"Drive API Fehler: {e}") from e


def is_supported_file(name: str, mime_type: str) -> bool:
    """Check if a file is a supported type for import.

    Rejects Google-native formats and unsupported extensions.
    """
    if mime_type in GOOGLE_NATIVE_MIMETYPES:
        return False

    ext = Path(name).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def download_file(file_id: str, dest_path: str) -> int:
    """Download a file from Drive to a local path.

    Creates parent directories if needed.
    Returns file size in bytes.
    """
    try:
        service = _get_drive_client()

        # Create parent dirs
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        request = service.files().get_media(fileId=file_id)
        with open(dest_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {file_id}: {int(status.progress() * 100)}%")

        file_size = os.path.getsize(dest_path)
        logger.info(f"Datei {file_id} heruntergeladen: {dest_path} ({file_size} Bytes)")
        return file_size

    except HttpError as e:
        logger.error(f"Drive API Fehler beim Herunterladen von {file_id}: {e}")
        raise RuntimeError(f"Drive Download Fehler: {e}") from e


def file_type_from_name(name: str) -> str:
    """Extract normalized file type from filename.

    .jpeg maps to 'jpg'.
    """
    ext = Path(name).suffix.lower().lstrip(".")
    if ext == "jpeg":
        return "jpg"
    return ext
