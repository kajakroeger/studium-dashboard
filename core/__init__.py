"""
core/__init__.py
Dieses Paket bündelt die fachliche Logik (Application/Services).
Nach außen exportieren wir den FortschrittService und seine DTOs.
"""

from __future__ import annotations

# Importiere DTOs, die du im UI brauchst (z. B. für KPI- oder Zielanzeigen)
from .dtos import StudienzieleDTO, ZielStatusDTO, KursFortschrittDTO, BearbeitungFortschrittDTO, GesamtFortschrittDTO

# Importiere den neuen zusammengesetzten FortschrittService
from .progress_service import ProgressService
from .goals_service import GoalsService
from .workflow_service import WorkflowService

# --------------------------------------------------------
# Fassade, die alles zusammenhält 
# --------------------------------------------------------
class FortschrittService:
    def __init__(
        self,
        *,
        student_repo,
        bearbeitung_repo,
        kurs_repo,
        pruefung_repo,
        einschreibung_repo,
        studiengang_repo,
    ):
        # Speichert Repositories für spätere Nutzung
        self._kurs_repo = kurs_repo         
        self._student_repo = student_repo
        self._bearbeitung_repo = bearbeitung_repo
        self._pruefung_repo = pruefung_repo
        self._einschreibung_repo = einschreibung_repo
        self._studiengang_repo = studiengang_repo

        self._kurs_repository = kurs_repo  


        # Sub-Services instanzieren
        self._progress = ProgressService(
            student_repo=student_repo,
            bearbeitung_repo=bearbeitung_repo,
            kurs_repo=kurs_repo,
            pruefung_repo=pruefung_repo,
            einschreibung_repo=einschreibung_repo,
        )

        self._goals = GoalsService(
            bearbeitung_repo=bearbeitung_repo,
            kurs_repo=kurs_repo,
            pruefung_repo=pruefung_repo,
            einschreibung_repo=einschreibung_repo,
            notenschnitt_fn=self._progress.berechne_notenschnitt,
        )

        self._workflow = WorkflowService(
            student_repo=student_repo,
            bearbeitung_repo=bearbeitung_repo,
            kurs_repo=kurs_repo,
            pruefung_repo=pruefung_repo,
            einschreibung_repo=einschreibung_repo,
            studiengang_repo=studiengang_repo,
            ects_summe_bestanden_fn=self._progress.ects_summe_bestanden,
        )

    # --------------------------------------------------------
    # Delegationen (Public API beibehalten)
    # --------------------------------------------------------

    def create_student(self, **kwargs) -> int:
        return self._workflow.create_student(**kwargs)

    # KPI-/Fortschrittsfunktionen
    def berechne_notenschnitt(self, student_id: int):
        return self._progress.berechne_notenschnitt(student_id)

    def ects_summe_bestanden(self, student_id: int):
        return self._progress.ects_summe_bestanden(student_id)

    # Falls vorhanden:
    def gesamtuebersicht(self, student_id: int):
        return self._progress.gesamtuebersicht(student_id)

    # Ziel- und Prognosefunktionen
    def hole_studienziele(self, student_id: int) -> StudienzieleDTO:
        return self._goals.hole_studienziele(student_id)

    def berechne_ziel_status(self, student_id: int) -> ZielStatusDTO:
        return self._goals.berechne_ziel_status(student_id)

    # Workflows
    def add_kurs_mit_bearbeitung_und_pruefung(self, **kwargs):
        return self._workflow.add_kurs_mit_bearbeitung_und_pruefung(**kwargs)

    def pruefung_abgeben(self, **kwargs):
        return self._workflow.pruefung_abgeben(**kwargs)

    def note_fuer_kurs_eintragen(self, **kwargs):
        return self._workflow.note_fuer_kurs_eintragen(**kwargs)

    def studium_abschliessen(self, **kwargs):
        return self._workflow.studium_abschliessen(**kwargs)
    
    def kurs_name_exists(self, name: str) -> bool:
        return self._kurs_repo.exists_by_name((name or "").strip())

    def kurs_kuerzel_exists(self, kz: str) -> bool:
        return self._kurs_repo.exists_by_kuerzel((kz or "").strip())
    

# --------------------------------------------------------
# Öffentliche Exporte für andere Module
# --------------------------------------------------------
__all__ = [
    "FortschrittService",
    "StudienzieleDTO",
    "ZielStatusDTO",
    "KursFortschrittDTO",
    "BearbeitungFortschrittDTO",
    "GesamtFortschrittDTO",
]
