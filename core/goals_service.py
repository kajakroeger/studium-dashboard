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

    # ---------- Public API ----------
    def hole_studienziele(self, student_id: int) -> StudienzieleDTO:
        ziel_noten = None
        ziel_end = None
        if hasattr(self._einschreibungen, "get_aktive_fuer_student"):
            e = self._einschreibungen.get_aktive_fuer_student(student_id)  # type: ignore[attr-defined]
            if e:
                ziel_noten = getattr(e, "ziel_notenschnitt", None)
                ziel_end = getattr(e, "ziel_enddatum", None)

        return StudienzieleDTO(
            ziel_notenschnitt=ziel_noten,
            ziel_enddatum=ziel_end,
            aktueller_notenschnitt=self._notenschnitt_fn(student_id),
            heutiges_datum=date.today(),
        )

    def berechne_ziel_status(self, student_id: int) -> ZielStatusDTO:
        ziele = self.hole_studienziele(student_id)
        noten = self._noten_liste(student_id)
        n_bekannt = len(noten)
        offen = self._anzahl_offen(student_id)

        kommentar_note = "Keine Noten vorhanden."
        notenziel_erreicht: Optional[bool] = None
        erforderlicher_rest: Optional[float] = None

        if ziele.ziel_notenschnitt is not None and (n_bekannt + offen) > 0:
            ziel = ziele.ziel_notenschnitt
            aktueller = ziele.aktueller_notenschnitt
            if aktueller is not None and offen == 0:
                notenziel_erreicht = aktueller <= ziel
                kommentar_note = "Ziel-Notenschnitt erreicht. 🎉" if notenziel_erreicht else "Ziel-Notenschnitt noch nicht erreicht."
            else:
                sum_bekannt = sum(noten)
                m = offen if offen > 0 else 1
                erforderlicher_rest = (ziel * (n_bekannt + offen) - sum_bekannt) / m
                erforderlicher_rest = max(1.0, min(5.0, erforderlicher_rest))
                kommentar_note = (
                    f"Du liegst derzeit {'unter' if (aktueller is not None and aktueller <= ziel) else 'über'} dem Ziel. "
                    f"Verbleibende Prüfungen: {offen}. "
                    f"Um das Ziel zu erreichen, bräuchtest du im Schnitt ≈ {erforderlicher_rest:.2f}."
                )
        elif ziele.ziel_notenschnitt is None:
            kommentar_note = "Kein Ziel-Notenschnitt hinterlegt."
        else:
            kommentar_note = "Keine offenen Prüfungen."

        kommentar_zeit = "Keine Verlaufsdaten vorhanden."
        prognose = None
        avg_tage = self._durchschnitt_bearbeitungszeit_tage(student_id)
        if avg_tage is not None and offen > 0:
            prognose = date.today() + timedelta(days=int(avg_tage * offen))
            kommentar_zeit = (
                f"Mit deiner aktuellen Bearbeitungszeit (~{avg_tage:.0f} Tage/Kurs) "
                f"wärest du voraussichtlich am {prognose:%d.%m.%Y} fertig."
            )
            if ziele.ziel_enddatum:
                kommentar_zeit += " Das liegt im Plan. ✅" if prognose <= ziele.ziel_enddatum \
                                  else f" Das ist **nach** deinem Zieltermin ({ziele.ziel_enddatum:%d.%m.%Y}). ⚠️"
        elif offen == 0:
            kommentar_zeit = "Keine offenen Bearbeitungen – fast geschafft! 🎉"

        return ZielStatusDTO(
            notenziel_erreicht=notenziel_erreicht,
            verbleibende_pruefungen=offen,
            erforderlicher_rest_schnitt=erforderlicher_rest,
            kommentar_note=kommentar_note,
            prognose_abschluss=prognose,
            kommentar_zeit=kommentar_zeit,
        )

    # ---------- private Helfer ----------
    def _noten_liste(self, student_id: int) -> list[float]:
        noten: list[float] = []
        for b in self._bearb.all_for_student(student_id):
            p = self._pruef.get_by_bearbeitung_id(b.id)
            if p and p.note is not None:
                noten.append(p.note)
        return noten

    def _anzahl_offen(self, student_id: int) -> int:
        offen = 0
        for b in self._bearb.all_for_student(student_id):
            p = self._pruef.get_by_bearbeitung_id(b.id)
            if not p or not p.bestanden:
                offen += 1
        return offen

    def _durchschnitt_bearbeitungszeit_tage(self, student_id: int) -> Optional[float]:
        zeiten: list[int] = []
        for b in self._bearb.all_for_student(student_id):
            if b.abgabe_datum and b.start_datum:
                zeiten.append((b.abgabe_datum - b.start_datum).days)
        if not zeiten:
            return None
        return sum(zeiten) / len(zeiten)
