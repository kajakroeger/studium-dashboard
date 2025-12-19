# db/repositories/__init__.py
"""
📦📋 LAGERKATALOG 
- sammelt alle verfügbaren Lagerverwalter (Repositories) an einem Ort
- listet sowohl:
  - die LAGERVERWALTUNG (Interface) → Was kann mit den Lager-Items gemacht werden
  - die konkreten REGALMANAGER (SQLite-Implementierungen) → konkrete Ausführung der Aktionen

Technisch:
- zentraler Exportpunkt für alle Repository-Typen
- ermöglicht saubere Imports wie:
    from db.repositories import KursRepository
    from db import * → importiert das ganze Lager
"""
from .bearbeitung_repository import BearbeitungRepository
from .sqlite_bearbeitung_repository import SQLiteBearbeitungRepository

from .einschreibung_repository import EinschreibungRepository
from .sqlite_einschreibung_repository import SQLiteEinschreibungRepository

from .kurs_repository import KursRepository
from .sqlite_kurs_repository import SQLiteKursRepository

from .student_repository import StudentRepository
from .sqlite_student_repository import SQLiteStudentRepository

from .pruefung_repository import PruefungRepository
from .sqlite_pruefung_repository import SQLitePruefungRepository

from .studiengang_repository import StudiengangRepository
from .sqlite_studiengang_repository import SQLiteStudiengangRepository

__all__ = [
    "BearbeitungRepository", "SQLiteBearbeitungRepository",
    "EinschreibungRepository", "SQLiteEinschreibungRepository",
    "KursRepository", "SQLiteKursRepository",
    "StudentRepository", "SQLiteStudentRepository",
    "PruefungRepository", "SQLitePruefungRepository",
    "StudiengangRepository", "SQLiteStudiengangRepository",
]
