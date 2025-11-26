"""
core/__init__.py
Dieses Paket bündelt die fachliche Logik (Application/Services).
Nach außen exportieren wir den FortschrittService und seine DTOs.
"""
from __future__ import annotations
from datetime import date

# DTOs für die UI
from .dtos import (
    StudienzieleDTO,
    ZielStatusDTO,
    KursFortschrittDTO,
    BearbeitungFortschrittDTO,
    GesamtFortschrittDTO,
)

# Sub-Services
from .progress_service import ProgressService
from .goals_service import GoalsService
from .workflow_service import WorkflowService


# --------------------------------------------------------
# Fassade: öffentliche API für die UI
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
    ) -> None:
        # Sub-Services instanzieren (Repos werden NUR hier verdrahtet)
        self._progress = ProgressService(
            student_repo=student_repo,
            bearbeitung_repo=bearbeitung_repo,
            kurs_repo=kurs_repo,
            pruefung_repo=pruefung_repo,
            einschreibung_repo=einschreibung_repo,
            # workflow=workflow,
        )
 
        workflow = WorkflowService(
            student_repo=student_repo,
            bearbeitung_repo=bearbeitung_repo,
            kurs_repo=kurs_repo,
            pruefung_repo=pruefung_repo,
            einschreibung_repo=einschreibung_repo,
            studiengang_repo=studiengang_repo,
            ects_summe_bestanden_fn=self._progress.ects_summe_bestanden,
            notenschnitt_fn=self._progress.berechne_notenschnitt,
        )
        self._workflow = workflow
        self._progress.set_workflow(workflow)

        self._goals = GoalsService(
            bearbeitung_repo=bearbeitung_repo,
            kurs_repo=kurs_repo,
            pruefung_repo=pruefung_repo,
            einschreibung_repo=einschreibung_repo,
            notenschnitt_fn=self._progress.berechne_notenschnitt,
        )





    # ---------------- CRUD/Workflows (Delegationen) ------------
    # ---------------- Student ------------
    def create_student(self, **kwargs) -> int:
        return self._workflow.create_student(**kwargs)
    
    def student_by_id(self, student_id: int):
        return self._workflow.student_by_id(student_id)
    
    def student_all(self):
        return self._workflow.student_all()
    


    # ---------------- Studiengang ------------
    def studiengang_by_id(self, studiengang_id: int):
        return self._workflow.studiengang_by_id(studiengang_id)
    
    def studiengang_by_name(self, name: str):
        return self._workflow.studiengang_by_name(name)
    
    def studiengaenge_fuer_student(self, student_id: int):
        return self._workflow.studiengaenge_fuer_student(student_id)
    
    def studiengang_all(self):
        return self._workflow.studiengang_all()
    


    # ---------------- Einschreibungen ----------------
    def einschreibungen_fuer_student(self, student_id: int):
        return self._workflow.einschreibungen_fuer_student(student_id)
    
    def aktive_einschreibung(self, student_id: int):
        return self._workflow.aktive_einschreibung(student_id)
    


    # ---------------- Kurse ----------------
    def kurse_all(self):
        return self._workflow.kurse_all()

    def kurs_by_id(self, kurs_id: int):
        return self._workflow.kurs_by_id(kurs_id)

    def kurs_name_exists(self, name: str) -> bool:
        return self._workflow.kurs_name_exists(name)

    def kurs_kuerzel_exists(self, kz: str) -> bool:
        return self._workflow.kurs_kuerzel_exists(kz)
    
    def kurse_fuer_pruefungsabgabe(self, student_id: int, studiengang_id: int | None = None):
        return self._workflow.kurse_fuer_pruefungsabgabe(student_id, studiengang_id)
    

    
    # ---------------- Bearbeitungen der Kurse ----------------
    def bearbeitungen_fuer_student(self, student_id: int):
        return self._workflow.bearbeitungen_fuer_student(student_id)

    def pruefungen_fuer_student(self, student_id: int):
        return self._workflow.pruefungen_fuer_student(student_id)
    


    # ---------------- Action Bar Acktionen ------------
    def add_kurs_mit_bearbeitung_und_pruefung(self, **kwargs):
        return self._workflow.add_kurs_mit_bearbeitung_und_pruefung(**kwargs)
    
    def bearbeitung_starten(self, bearbeitung_id: int, start_datum: date) -> None:
        return self._workflow.bearbeitung_starten(bearbeitung_id=bearbeitung_id, start_datum=start_datum)

    def pruefung_abgeben(self, **kwargs):
        return self._workflow.pruefung_abgeben(**kwargs)

    def note_fuer_kurs_eintragen(self, **kwargs):
        return self._workflow.note_fuer_kurs_eintragen(**kwargs)
    
    def offene_kurse_fuer_bewertung(self, student_id: int):
        return self._workflow.offene_kurse_fuer_bewertung(student_id)

    def studium_abschliessen(self, **kwargs):
        return self._workflow.studium_abschliessen(**kwargs)
    


    # ---------------- KPIs / Fortschritt ------------
    def hole_studienziele(self, student_id: int) -> StudienzieleDTO:
        return self._goals.hole_studienziele(student_id)
    
    def ziel_ects(self, student_id: int, studiengang_id: int | None = None) -> int:
        return self._workflow.ziel_ects(student_id, studiengang_id)
    
    def berechne_ziel_status(self, student_id: int) -> ZielStatusDTO:
        return self._goals.berechne_ziel_status(student_id)

    def berechne_notenschnitt(self, student_id: int):
        return self._progress.berechne_notenschnitt(student_id)

    def ects_summe_bestanden(self, student_id: int):
        return self._progress.ects_summe_bestanden(student_id)

    def gesamtuebersicht(self, student_id: int):
        return self._progress.gesamtuebersicht(student_id)
    
    def berechne_bearbeitungszeit(self, student_id: int) -> int:
        return self._progress.berechne_bearbeitungszeit(student_id)
    
    def bearbeitungsdauer_in_tagen(self, student_id: int):
        return self._progress.bearbeitungsdauer_in_tagen(student_id)
    
    def verlauf_bearbeitungszeiten(self, student_id: int):
        return self._progress.verlauf_bearbeitungszeiten(student_id)
    


__all__ = [
    "FortschrittService",
    "StudienzieleDTO",
    "ZielStatusDTO",
    "KursFortschrittDTO",
    "BearbeitungFortschrittDTO",
    "GesamtFortschrittDTO",
]
