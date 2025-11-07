"""
ui/bootstrap.py
Baut SQLite-Repos + Service zusammen. Kein UI/Business-Code.
"""

from core import FortschrittService
from db import SQLiteConnectionProvider
from db.repositories.student_repository import StudentRepository
from db.repositories.sqlite_student_repository import SQLiteStudentRepository
from db.repositories.sqlite_bearbeitung_repository import SQLiteBearbeitungRepository
from db.repositories.sqlite_kurs_repository import SQLiteKursRepository
from db.repositories.sqlite_pruefung_repository import SQLitePruefungRepository
from db.repositories.sqlite_einschreibung_repository import SQLiteEinschreibungRepository
from db.repositories.sqlite_studiengang_repository import SQLiteStudiengangRepository


def build_service(db_path: str = "studium.db") -> tuple[FortschrittService, StudentRepository]:
    provider = SQLiteConnectionProvider(db_path)
    student_repo = SQLiteStudentRepository(provider)
    bearb_repo = SQLiteBearbeitungRepository(provider)
    kurs_repo = SQLiteKursRepository(provider)
    pruefung_repo = SQLitePruefungRepository(provider)
    einschreibung_repo = SQLiteEinschreibungRepository(provider)
    studiengang_repo = SQLiteStudiengangRepository(provider)

    service = FortschrittService(
        student_repo=student_repo,
        bearbeitung_repo=bearb_repo,
        kurs_repo=kurs_repo,
        pruefung_repo=pruefung_repo,
        einschreibung_repo=einschreibung_repo,
        studiengang_repo=studiengang_repo,
    )
    return service, student_repo
