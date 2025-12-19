# core/__init__.py
"""
 📋 KÜCHENPLAN
- koordiniert zwischen Lagerregale (Repositories), Schlüssel zum Lager, Küchenkoordination (WorkflowService) und Koch (ProgressService) 

Technisch
- verdrahtet die Infrastruktur (SQLite + Repositories) mit den Domänen-Services
- entscheidet, welche konkrete Technik (z. B. SQLite) verwendet wird
- stellt fertig konfigurierte Services für die UI bereit

- Enthält KEINE Fachlogik
- Enthält KEINE SQL-Queries
- UI kennt nur Services, keine Repositories, keine DB-Technik
"""

from __future__ import annotations
from typing import Optional, Tuple

from .workflow_service import WorkflowService
from .progress_service import ProgressService

from db import SQLiteConnectionProvider

from db.repositories.sqlite_student_repository import SQLiteStudentRepository
from db.repositories.sqlite_bearbeitung_repository import SQLiteBearbeitungRepository
from db.repositories.sqlite_kurs_repository import SQLiteKursRepository
from db.repositories.sqlite_pruefung_repository import SQLitePruefungRepository
from db.repositories.sqlite_einschreibung_repository import SQLiteEinschreibungRepository
from db.repositories.sqlite_studiengang_repository import SQLiteStudiengangRepository

# Globale Service-Instanzen 
# - Services müssen nicht bei jeder Page/bei jedem Re-Run neu gebaut werden.
# - Repositories/Provider werden konsistent nur einmal initialisiert.
_workflow_service: Optional[WorkflowService] = None
_progress_service: Optional[ProgressService] = None

# TODO: Wenn die Datenbank-Technologie ausgetauscht werden sollte (z.B. PostgreSQL statt SQLite), 
# dann hier die Verdrahtung anpassen.
def create_services(db_path: str = "data/studium.db") -> Tuple[WorkflowService, ProgressService]:
    """    
    Erzeugt und initialisiert die Service-Layer-Instanzen.

    Parameter:
    - db_path: Pfad zur SQLite DB. Default zeigt auf die produktive lokale DB.

    Rückgabe:
    - (WorkflowService, ProgressService)

    Ablauf:
    1) Connection-Provider erzeugen
    2) Repositories auf SQLite-Basis erstellen
    3) WorkflowService bekommt alle Repositories (Single Source of Truth für Fachlogik)
    4) ProgressService bekommt nur WorkflowService (keine DB-Abhängigkeiten)
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

    # 3) WorkflowService – mit allen Repositories
    _workflow_service = WorkflowService(
        student_repo=student_repo,
        bearbeitung_repo=bearbeitung_repo,
        kurs_repo=kurs_repo,
        pruefung_repo=pruefung_repo,
        einschreibung_repo=einschreibung_repo,
        studiengang_repo=studiengang_repo,
    )

    # 4) ProgressService: für Kennzahlen für die UI auf Basis des Workflows, ist damit unabhängig von der DB
    _progress_service = ProgressService(workflow=_workflow_service)

    return _workflow_service, _progress_service


def get_services() -> Tuple[WorkflowService, ProgressService]:
    """Liefert WorkflowService und ProgressService."""
    global _workflow_service, _progress_service

    if _workflow_service is None or _progress_service is None:
        return create_services()

    return _workflow_service, _progress_service


def get_workflow_service() -> WorkflowService:
    """
    Liefert nur den WorkflowService.
    Praktisch für Pages/Komponenten, die nur CRUD/Fachlogik brauchen
    (z. B. Anlegen von Kursen, Eintragen von Prüfungen).
    """
    return get_services()[0]


def get_progress_service() -> ProgressService:
    """
    Liefert nur den ProgressService.
    Praktisch für Dashboard/Reports (Charts, KPIs), ohne direkt DB-Repos anzufassen.
    """
    return get_services()[1]
