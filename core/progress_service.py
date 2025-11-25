"""
core/progress_service.py
Aggregation/Lesen (KPI, ECTS, Notenschnitt, Gesamtübersicht).
"""

from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Iterable
from typing import Optional

from core.workflow_service import WorkflowService
from models import Bearbeitung, Pruefung
from db.repositories.student_repository import StudentRepository
from db.repositories.bearbeitung_repository import BearbeitungRepository
from db.repositories.kurs_repository import KursRepository
from db.repositories.pruefung_repository import PruefungRepository
from db.repositories.einschreibung_repository import EinschreibungRepository


class ProgressService:
    def __init__(
        self,
        *,
        student_repo: StudentRepository,
        bearbeitung_repo: BearbeitungRepository,
        kurs_repo: KursRepository,
        pruefung_repo: PruefungRepository,
        einschreibung_repo: EinschreibungRepository,
        # workflow,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo

        # Workflow wird später gesetzt
        self._workflow = None

    def set_workflow(self, workflow) -> None:
        """Wird vom FortschrittService nachträglich aufgerufen"""
        self._workflow = workflow


    def berechne_notenschnitt(self, student_id: int) -> Optional[float]:
        """
        Berechnet den Notenschnitt aller bestandenen Prüfungen
        eines Studenten. Gibt None zurück, wenn es keine
        bestandenen Prüfungen gibt.
        """

        if self._workflow is None or not hasattr(self._workflow, "bearbeitungen_fuer_student"):
            print("DEBUG: Abbruch, weil _workflow fehlt oder keine bearbeitungen_fuer_student-Methode hat")
            return None

        # Sicherstellen, dass der Workflow gesetz wurde
        if self._workflow is None or not hasattr(self._workflow, "bearbeitungen_fuer_student"):
            return None

        # 1) Bearbeitungen über den Workflow holen
        #    -> hier liegt deine Methode bearbeitungen_fuer_student
        if not hasattr(self._workflow, "bearbeitungen_fuer_student"):
            # Falls der Workflow falsch oder nicht gesetzt ist
            return None

        # list() macht aus einem evtl. Iterator eine Liste
        bearbeitungen = list(self._workflow.bearbeitungen_fuer_student(student_id) or [])

        if not bearbeitungen:
            # Keine Bearbeitungen → kein Notenschnitt
            return None

        # 2) Prüfungs-Repository über den Workflow holen
        pruef_repo = getattr(self._workflow, "_pruef", None)
        if pruef_repo is None or not hasattr(pruef_repo, "get_by_bearbeitung_id"):
            return None

        get_pruefung = pruef_repo.get_by_bearbeitung_id

        # 3) Noten einsammeln (nur bestandene Prüfungen)
        noten: list[float] = []

        for b in bearbeitungen:
            b_id = getattr(b, "id", None)
            if not b_id:
                continue

            # Prüfung zu dieser Bearbeitung holen
            p = get_pruefung(int(b_id))
            if not p:
                continue

            note = getattr(p, "note", None)
            bestanden_raw = getattr(p, "bestanden", 0)  # 0/1, False/True oder None

            # Nur bestandene Prüfungen mit Note berücksichtigen
            if note is None or not bool(bestanden_raw):
                continue

            try:
                noten.append(float(note))
            except (TypeError, ValueError):
                # Falls note kein Zahlentyp ist → überspringen
                continue

        # 4) Durchschnitt berechnen
        if not noten:
            return None

        return round(sum(noten) / len(noten), 2)

    

    def ects_summe_bestanden(self, student_id: int) -> int:
        """Summe der ECTS für bestandene Prüfungen."""
        total = 0
        for b in self._bearb.einschreibungen_fuer_student(student_id):
            p = self._pruefung_fuer_bearbeitung(b.id)
            if p and getattr(p, "bestanden", False):
                kurs = self._kurse.get_by_id(b.kurs_id)
                total += getattr(kurs, "ects", 0)
        return total



    # Hilfsfunktion wie bisher
    def _pruefung_fuer_bearbeitung(self, bearbeitung_id: int) -> Optional[Pruefung]:
        return self._pruef.get_by_bearbeitung_id(bearbeitung_id)
    


    def _to_date(self, value) -> Optional[date]:
        """Hilfsfunktion: str/datetime/date -> date."""
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    def bearbeitungsdauer_in_tagen(self, b):
        """Gibt Bearbeitungsdauer einer Bearbeitung in Tagen zurück."""
        start = self._to_date(getattr(b, "start_datum", None))
        ende = self._to_date(getattr(b, "abgabe_datum", None))

        if not start or not ende:
            return None
        
        days = (ende - start).days
        return days if days >= 0 else None


    def verlauf_bearbeitungszeiten(self, student_id: int):
        """Liefert eine Liste der durchschnittlichen Bearbeitungszeiten nach jedem Abschluss."""
        if self._workflow is None:
            return []

        bearbeitungen = list(self._workflow.bearbeitungen_fuer_student(student_id) or [])

        # nur abgeschlossene + sortiert nach Abgabe
        fertige = [
            b for b in bearbeitungen
            if str(getattr(b.status, "value", b.status)).lower() == "abgeschlossen"
            and self._to_date(b.abgabe_datum)
        ]
        fertige.sort(key=lambda b: self._to_date(b.abgabe_datum))

        Verlauf = []
        summen = 0
        count = 0

        for b in fertige:
            tage = self.bearbeitungsdauer_in_tagen(b)
            if tage is None:
                continue
            
            summen += tage
            count += 1
            Verlauf.append(round(summen / count, 1))

        return Verlauf