"""
core/goals_service.py
Studienziele & „Aktueller Status der Ziele“.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional

from core.dtos import StudienzieleDTO, ZielStatusDTO
from models import Bearbeitung, Pruefung
from db.repositories.bearbeitung_repository import BearbeitungRepository
from db.repositories.kurs_repository import KursRepository
from db.repositories.pruefung_repository import PruefungRepository
from db.repositories.einschreibung_repository import EinschreibungRepository

class GoalsService:
    def __init__(
        self,
        *,
        bearbeitung_repo: BearbeitungRepository,
        kurs_repo: KursRepository,
        pruefung_repo: PruefungRepository,
        einschreibung_repo: EinschreibungRepository,
        notenschnitt_fn,  # callable: (student_id:int) -> Optional[float]
    ) -> None:
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo
        self._notenschnitt_fn = notenschnitt_fn



    # ---------- private Helfer ----------
    def _noten_liste(self, student_id: int) -> list[float]:
        noten: list[float] = []
        for b in self._bearb.list_by_student(student_id):
            p = self._pruef.get_by_bearbeitung_id(b.id)
            if p and p.note is not None:
                noten.append(p.note)
        return noten

    def _anzahl_offen(self, student_id: int) -> int:
        offen = 0
        for b in self._bearb.list_by_student(student_id):
            p = self._pruef.get_by_bearbeitung_id(b.id)
            if not p or not p.bestanden:
                offen += 1
        return offen

    def _durchschnitt_bearbeitungszeit_tage(self, student_id: int) -> Optional[float]:
        zeiten: list[int] = []
        for b in self._bearb.list_by_student(student_id):
            if b.abgabe_datum and b.start_datum:
                zeiten.append((b.abgabe_datum - b.start_datum).days)
        if not zeiten:
            return None
        return sum(zeiten) / len(zeiten)
