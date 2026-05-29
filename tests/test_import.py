"""Test-Skript: Import Service end-to-end Test.

Testet den kompletten Import-Flow:
1. Dateien im Drive-Ordner finden
2. Dokumente importieren
3. Deduplizierung prüfen (2. Lauf = 0 neue Imports)

Voraussetzungen:
- .env korrekt konfiguriert
- Service Account hat Zugriff auf den freigegebenen Ordner
- Mindestens eine Datei im Drive-Ordner

Aufruf: python -m tests.test_import
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session_factory
from app.models.user import User
from app.services.import_service import import_from_drive, get_last_status
from sqlalchemy import select


async def main():
    print("=" * 50)
    print("DocuAgent — Import Service Test")
    print("=" * 50)

    async with async_session_factory() as db:
        try:
            # Find the first user (system owner)
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()

            if not user:
                print("FEHLER: Kein Benutzer in der Datenbank.")
                print("Registriere zuerst einen Benutzer über POST /api/auth/register")
                return

            print(f"Benutzer: {user.name} ({user.email})")
            print()

            # Run 1: Import
            print("--- Erster Import ---")
            result1 = import_from_drive(db, user.id)
            if asyncio.iscoroutine(result1):
                result1 = await result1
            await db.commit()

            print(f"  Job-ID:     {result1['job_id']}")
            print(f"  Gefunden:   {result1['files_found']}")
            print(f"  Importiert: {result1['files_imported']}")
            print(f"  Übersprungen: {result1['files_skipped']}")
            print()

            # Run 2: Dedup test
            print("--- Zweiter Import (Deduplizierung) ---")
            result2 = import_from_drive(db, user.id)
            if asyncio.iscoroutine(result2):
                result2 = await result2
            await db.commit()

            print(f"  Job-ID:     {result2['job_id']}")
            print(f"  Gefunden:   {result2['files_found']}")
            print(f"  Importiert: {result2['files_imported']}")
            print(f"  Übersprungen: {result2['files_skipped']}")
            print()

            if result2["files_imported"] == 0:
                print("✅ Deduplizierung funktioniert! Keine Dateien doppelt importiert.")
            else:
                print("⚠️  WARNUNG: Es wurden beim 2. Lauf Dateien importiert!")
                print("     Deduplizierung prüfen!")
            print()

            # Check last status
            print("--- Letzter Sync-Status ---")
            status = await get_last_status(db)
            if status:
                print(f"  Status:     {status.status}")
                print(f"  Gestartet:  {status.started_at}")
                print(f"  Beendet:    {status.finished_at}")
                print(f"  Gefunden:   {status.files_found}")
                print(f"  Importiert: {status.files_imported}")
                print(f"  Übersprungen: {status.files_skipped}")
            print()

            print("Test abgeschlossen! ✅")

        except Exception as e:
            await db.rollback()
            print(f"FEHLER: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
