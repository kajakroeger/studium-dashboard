# core/workflow_service.py
"""

"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional

from core.dtos import AbgeschlosseneBearbeitung
from db.repositories.student_repository import StudentRepository
from db.repositories.bearbeitung_repository import BearbeitungRepository
from db.repositories.kurs_repository import KursRepository
from db.repositories.pruefung_repository import PruefungRepository
from db.repositories.einschreibung_repository import EinschreibungRepository
from db.repositories.studiengang_repository import StudiengangRepository

from models import Student, Kurs, Bearbeitung, Pruefung, Einschreibung, Studiengang
from models.bearbeitung import StatusBearbeitung


class WorkflowService:
    """
    Reine Domänenlogik & Datenzugriff. Kennt nur die Repositories. 
    Bietet Read-/Workflow-Methoden, aber keine Auswertungen (kein Notenschnitt, keine ECTS-Analysen usw.).
    Ist zentrale Quelle für: Studenten, Kurse, Bearbeitungen, Prüfungen, Einschreibungen, Studiengänge.
    
    Verantwortlich für:
    - Zugriff auf Stammdaten (Student, Kurs, Studiengang, Einschreibung)
    - Zugriff auf Bearbeitungen & Prüfungen
    - einfache Workflow-Operationen (z. B. Kurs starten, Prüfung anlegen, etc.)
    """

    def __init__(
        self,
        *,
        student_repo: StudentRepository,
        bearbeitung_repo: BearbeitungRepository,
        kurs_repo: KursRepository,
        pruefung_repo: PruefungRepository,
        einschreibung_repo: EinschreibungRepository,
        studiengang_repo: StudiengangRepository,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo
        self._studiengaenge = studiengang_repo

    # ---------------------------------------------------------------------
    # Studenten
    # ---------------------------------------------------------------------

    def student_all(self) -> Iterable[Student]:
        """Liefert alle Studenten."""
        return self._students.all()

    def student_by_id(self, student_id: int) -> Optional[Student]:
        """Liefert einen Studenten per ID oder None."""
        return self._students.get_by_id(student_id)

    # ---------------------------------------------------------------------
    # Studiengang & Einschreibung
    # ---------------------------------------------------------------------

    def studiengaenge_by_student_id(self, student_id: int) -> List[Studiengang]:
        """
        Liefert alle Studiengänge, in die der Student eingeschrieben ist.
        (über Einschreibungen verknüpft)
        """
        einschreibungen = self._einschreibungen.list_by_student(student_id)
        ids = [e.studiengang_id for e in einschreibungen]
        result: List[Studiengang] = []
        for sg_id in ids:
            sg = self._studiengaenge.get_by_id(sg_id)
            if sg:
                result.append(sg)
        return result

    def studiengang_by_id(self, studiengang_id: int) -> Optional[Studiengang]:
        return self._studiengaenge.get_by_id(studiengang_id)

    def einschreibungen_fuer_student(self, student_id: int) -> List[Einschreibung]:
        """Alle Einschreibungen eines Studenten."""
        return self._einschreibungen.list_by_student(student_id)

    def aktive_einschreibung(self, student_id: int) -> Optional[Einschreibung]:
        """
        Liefert die aktive Einschreibung (falls vorhanden).
        Logik: erstes Einschreibungsobjekt mit ist_aktiv=True,
        sonst None.
        """
        einschreibungen = self._einschreibungen.list_by_student(student_id)
        aktive = [e for e in einschreibungen if getattr(e, "ist_aktiv", False)]
        return aktive[0] if aktive else None

    # ---------------------------------------------------------------------
    # Kurse, Bearbeitungen, Prüfungen
    # ---------------------------------------------------------------------

    def kurs_by_id(self, kurs_id: int) -> Optional[Kurs]:
        """Liefert einen Kurs per ID oder None."""
        return self._kurse.get_by_id(kurs_id)

    def bearbeitungen_fuer_student(self, student_id: int) -> List[Bearbeitung]:
        """Alle Bearbeitungen eines Studenten (unabhängig vom Status)."""
        return list(self._bearb.list_by_student(student_id))

    def pruefung_fuer_bearbeitung(self, bearbeitung_id: int) -> Optional[Pruefung]:
        """Prüfung zu einer Bearbeitung, falls angelegt."""
        return self._pruef.get_by_bearbeitung_id(bearbeitung_id)

    # ---------------------------------------------------------------------
    # Hilfsfunktionen für Analysen
    # ---------------------------------------------------------------------

    def abgeschlossene_bearbeitungen(self, student_id: int) -> List[AbgeschlosseneBearbeitung]:
        """
        Liefert eine Liste von AbgeschlosseneBearbeitung für alle
        abgeschlossenen Bearbeitungen eines Studenten.
        (wird von ProgressService für Analysen genutzt)
        """
        result: List[AbgeschlosseneBearbeitung] = []

        for b in self.bearbeitungen_fuer_student(student_id):
            if b.status != StatusBearbeitung.ABGESCHLOSSEN:
                continue

            kurs = self.kurs_by_id(b.kurs_id)
            if not kurs:
                continue

            pruefung = self.pruefung_fuer_bearbeitung(b.id)
            result.append(
                AbgeschlosseneBearbeitung(
                    bearbeitung=b,
                    kurs=kurs,
                    pruefung=pruefung,
                )
            )

        return result

    def bearbeitungszeit_in_tagen(self, b: Bearbeitung) -> Optional[int]:
        """
        Gibt die Bearbeitungszeit in Tagen zurück (start_datum → abgabe_datum).
        """
        start = b.start_datum
        ende = b.abgabe_datum

        if not start or not ende:
            return None

        tage = (ende - start).days
        if tage < 0:
            return None
        return tage