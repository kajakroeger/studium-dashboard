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
    
    def studiengaenge_by_student_id(self, student_id: int):
        return self._workflow.studiengaenge_by_student_id(student_id)
    


    # ---------------- Einschreibungen ----------------
    def einschreibungen_fuer_student(self, student_id: int):
        return self._workflow.einschreibungen_fuer_student(student_id)
    
    def aktive_einschreibung(self, student_id: int):
        return self._workflow.aktive_einschreibung(student_id)
    


    # ---------------- Kurse ----------------

    def kurse_fuer_student(self, student_id: int):
        return self._workflow.kurse_fuer_student(student_id)

    def kurs_by_id(self, kurs_id: int):
        return self._workflow.kurs_by_id(kurs_id)

    def kurs_name_exists(self, name: str) -> bool:
        return self._workflow.kurs_name_exists(name)

    def kurs_kuerzel_exists(self, kz: str) -> bool:
        return self._workflow.kurs_kuerzel_exists(kz)
    
    def kurse_fuer_pruefungsabgabe(self, student_id: int, studiengang_id: int | None = None):
        return self._workflow.kurse_fuer_pruefungsabgabe(student_id, studiengang_id)
    

    
    # ---------------- Bearbeitungen ----------------

    def bearbeitungen_fuer_student(self, student_id: int):
        return self._workflow.bearbeitungen_fuer_student(student_id)
    

    
    # ---------------- Prüfungen ----------------

    def pruefung_fuer_bearbeitung(self, bearbeitung_id: int):
        return self._workflow.pruefung_fuer_bearbeitung(bearbeitung_id)
    


    # ---------------- Action Bar Aktionen ------------

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

    def berechne_notenschnitt(self, student_id: int):
        return self._progress.berechne_notenschnitt(student_id)

    def ects_summe_bestanden(self, student_id: int):
        return self._progress.ects_summe_bestanden(student_id)

    # def gesamtuebersicht(self, student_id: int):
    #     return self._progress.gesamtuebersicht(student_id)
    
    def berechne_bearbeitungszeit(self, student_id: int) -> int:
        return self._progress.berechne_bearbeitungszeit(student_id)
    
    def alle_bestandenen_noten(self, student_id: int):
        return self._progress.alle_bestandenen_noten(student_id)
    
    def benoetigte_note_naechster_kurs(self, student_id: int):
        return self._progress.benoetigte_note_naechster_kurs(student_id)
    


__all__ = [
    "FortschrittService",
    "StudienzieleDTO",
    "ZielStatusDTO",
    "KursFortschrittDTO",
    "BearbeitungFortschrittDTO",
    "GesamtFortschrittDTO",
]
