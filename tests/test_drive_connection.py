"""Test-Skript: Prüft ob der Service Account den freigegebenen Drive-Ordner lesen kann.

Voraussetzungen:
1. service_account.json unter secrets/ oder Pfad in GOOGLE_SERVICE_ACCOUNT_FILE
2. DRIVE_INBOX_FOLDER_ID in .env gesetzt
3. Der Ordner muss mit der Service-Account-E-Mail geteilt sein

Aufruf: python -m tests.test_drive_connection
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.services.google_drive_service import (
    list_subfolders,
    list_files_in_folder,
    is_supported_file,
    file_type_from_name,
)


def main():
    settings = get_settings()

    print("=" * 50)
    print("DocuAgent — Drive Connection Test")
    print("=" * 50)
    print(f"Service Account File: {settings.GOOGLE_SERVICE_ACCOUNT_FILE}")
    print(f"Inbox Folder ID: {settings.DRIVE_INBOX_FOLDER_ID}")
    print()

    if not settings.DRIVE_INBOX_FOLDER_ID:
        print("FEHLER: DRIVE_INBOX_FOLDER_ID ist nicht gesetzt.")
        sys.exit(1)

    folder_id = settings.DRIVE_INBOX_FOLDER_ID

    # Test 1: List subfolders
    print("--- Unterordner ---")
    subfolders = list_subfolders(folder_id)
    if subfolders:
        for sf in subfolders:
            print(f"  📁 {sf['name']} (ID: {sf['id']})")
    else:
        print("  (keine Unterordner gefunden)")
    print()

    # Test 2: List files in root inbox
    print("--- Dateien im Hauptordner ---")
    root_files = list_files_in_folder(folder_id)
    if root_files:
        for f in root_files:
            supported = is_supported_file(f["name"], f.get("mimeType", ""))
            ftype = file_type_from_name(f["name"]) if supported else "—"
            status = "✅" if supported else "⏭️ übersprungen"
            size = f.get("size", "?")
            print(f"  {status} {f['name']} ({ftype}, {size} B)")
    else:
        print("  (keine Dateien im Hauptordner)")
    print()

    # Test 3: List files in each subfolder
    for sf in subfolders:
        print(f"--- Dateien in '{sf['name']}' ---")
        files = list_files_in_folder(sf["id"])
        if files:
            for f in files:
                supported = is_supported_file(f["name"], f.get("mimeType", ""))
                ftype = file_type_from_name(f["name"]) if supported else "—"
                status = "✅" if supported else "⏭️ übersprungen"
                size = f.get("size", "?")
                print(f"  {status} {f['name']} ({ftype}, {size} B)")
        else:
            print("  (leer)")
        print()

    total_files = len(root_files) + sum(
        len(list_files_in_folder(sf["id"])) for sf in subfolders
    )
    print(f"Gesamt: {len(subfolders)} Unterordner, {total_files} Dateien")
    print("Verbindung erfolgreich! ✅")


if __name__ == "__main__":
    main()
