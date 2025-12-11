# core/__init__.py
"""
Services und deren Factory-Funktion.
Initialisierung der globalen Service-Instanzen.
"""

from __future__ import annotations
from typing import Optional, Tuple

from .workflow_service import WorkflowService
from .progress_service import ProgressService

from db.sqlite_connection_provider import SQLiteConnectionProvider

from db.repositories.sqlite_student_repository import SQLiteStudentRepository
from db.repositories.sqlite_bearbeitung_repository import SQLiteBearbeitungRepository
from db.repositories.sqlite_kurs_repository import SQLiteKursRepository
from db.repositories.sqlite_pruefung_repository import SQLitePruefungRepository
from db.repositories.sqlite_einschreibung_repository import SQLiteEinschreibungRepository
from db.repositories.sqlite_studiengang_repository import SQLiteStudiengangRepository

# Globale Service-Instanzen (Singleton-Pattern)
_workflow_service: Optional[WorkflowService] = None
_progress_service: Optional[ProgressService] = None


def create_services(db_path: str = "data/studium.db") -> Tuple[WorkflowService, ProgressService]:
    """
    Factory-Funktion für alle Services.

    Dependency-Flow:
    Repositories → WorkflowService → ProgressService
    """
    global _workflow_service, _progress_service

    # Wenn schon initialisiert, einfach zurückgeben
    if _workflow_service is not None and _progress_service is not None:
        return _workflow_service, _progress_service

    # 1) Connection-Provider
    provider = SQLiteConnectionProvider(db_path)

    # 2) Konkrete SQLite-Repositories
    student_repo = SQLiteStudentRepository(provider)
    bearbeitung_repo = SQLiteBearbeitungRepository(provider)
    kurs_repo = SQLiteKursRepository(provider)
    pruefung_repo = SQLitePruefungRepository(provider)
    einschreibung_repo = SQLiteEinschreibungRepository(provider)
    studiengang_repo = SQLiteStudiengangRepository(provider)

    # 3) WorkflowService – bekommt alle Repositories
    _workflow_service = WorkflowService(
        student_repo=student_repo,
        bearbeitung_repo=bearbeitung_repo,
        kurs_repo=kurs_repo,
        pruefung_repo=pruefung_repo,
        einschreibung_repo=einschreibung_repo,
        studiengang_repo=studiengang_repo,
    )

    # 4) ProgressService – bekommt NUR den Workflow
    _progress_service = ProgressService(workflow=_workflow_service)

    return _workflow_service, _progress_service


def get_services() -> Tuple[WorkflowService, ProgressService]:
    """
    Liefert die globalen Service-Instanzen.
    Lazy Initialization beim ersten Aufruf.
    """
    global _workflow_service, _progress_service

    if _workflow_service is None or _progress_service is None:
        return create_services()

    return _workflow_service, _progress_service


def get_workflow_service() -> WorkflowService:
    """Convenience: nur den WorkflowService holen."""
    return get_services()[0]


def get_progress_service() -> ProgressService:
    """Convenience: nur den ProgressService holen."""
    return get_services()[1]
