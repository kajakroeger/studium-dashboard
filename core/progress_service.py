"""
core/progress_service.py
Aggregation/Lesen (KPI, ECTS, Notenschnitt, Gesamtübersicht).
"""

from __future__ import annotations
from typing import Optional, Iterable

from models import Bearbeitung, Pruefung
from db.repositories.student_repository import StudentRepository
from db.repositories.bearbeitung_repository import BearbeitungRepository
from db.repositories.kurs_repository import KursRepository
from db.repositories.pruefung_repository import PruefungRepository
from db.repositories.einschreibung_repository import EinschreibungRepository

# Falls du DTOs für die Übersicht hast, importiere sie hier:
# from core.dtos import ...

class ProgressService:
    def __init__(
        self,
        *,
        student_repo: StudentRepository,
        bearbeitung_repo: BearbeitungRepository,
        kurs_repo: KursRepository,
        pruefung_repo: PruefungRepository,
        einschreibung_repo: EinschreibungRepository,
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo

    # --------- Lese-/Aggregations-Methoden (Beispiele) ---------

    def berechne_notenschnitt(self, student_id: int) -> Optional[float]:
        """Einfacher Durchschnitt über vorhandene Noten (ohne ECTS-Gewichtung)."""
        noten: list[float] = []
        for b in self._bearb.all_for_student(student_id):
            p = self._pruefung_fuer_bearbeitung(b.id)
            if p and p.note is not None:
                noten.append(p.note)
        if not noten:
            return None
        return sum(noten) / len(noten)

    def ects_summe_bestanden(self, student_id: int) -> int:
        """Summe der ECTS für bestandene Prüfungen."""
        total = 0
        for b in self._bearb.all_for_student(student_id):
            p = self._pruefung_fuer_bearbeitung(b.id)
            if p and getattr(p, "bestanden", False):
                kurs = self._kurse.get_by_id(b.kurs_id)
                total += getattr(kurs, "ects", 0)
        return total

    # Hilfsfunktion wie bisher
    def _pruefung_fuer_bearbeitung(self, bearbeitung_id: int) -> Optional[Pruefung]:
        return self._pruef.get_by_bearbeitung_id(bearbeitung_id)
    

    def kurs_name_exists(self, name: str) -> bool:
        """Prüft, ob ein Kurs mit dem gegebenen Namen existiert (case-insensitive)."""
        return self._kurse.exists_by_name(name)
    
    def kurs_kuerzel_exists(self, kurs_kuerzel: str) -> bool:
        """Prüft, ob ein Kurs mit dem gegebenen Kürzel existiert (case-insensitive)."""
        return self._kurse.exists_by_kuerzel(kurs_kuerzel)

    # hier würden auch Methoden wie "gesamtuebersicht(...)" liegen,
    # die deine KPI-DTOs befüllen.
