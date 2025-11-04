# core/fortschritt_service.py
"""
Fachlogik (Application Layer) für das Studium-Dashboard.
- Aggregiert Daten aus den Repositories
- Berechnet Notenschnitt/ECTS und liefert UI-freundliche DTOs
- Optionales Onboarding: create_student(...) schreibt auch Studienziele (Einschreibung)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean
from typing import Iterable, Optional

# Domain
from models import Student, Bearbeitung, StatusBearbeitung, Pruefung, Kurs
from models.einschreibung import Einschreibung, StatusEinschreibung

# Ports (Interfaces)
from db.repositories.student_repository import StudentRepository
from db.repositories.bearbeitung_repository import BearbeitungRepository
from db.repositories.kurs_repository import KursRepository
from db.repositories.pruefung_repository import PruefungRepository
from db.repositories.einschreibung_repository import EinschreibungRepository


# ---------------- Hilfsfunktionen ----------------

def _mean_or_none(values: Iterable[float]) -> Optional[float]:
    vals = list(values)
    return None if not vals else round(mean(vals), 2)

def _tage_zwischen(start: date, ende: Optional[date]) -> Optional[int]:
    return None if ende is None else (ende - start).days


# ---------------- DTOs ----------------

@dataclass(frozen=True)
class KursFortschrittDTO:
    kurs_id: int
    kurs_name: str
    ects: int
    bestanden: Optional[bool]
    note: Optional[float]
    versuch_nr: Optional[int]
    letzter_versuch: Optional[bool]

@dataclass(frozen=True)
class BearbeitungFortschrittDTO:
    bearbeitung_id: int
    kurs_id: int
    status: StatusBearbeitung
    thema: Optional[str]
    tage_bearbeitung: Optional[int]
    pruefung_bestehen: Optional[bool]
    pruefung_note: Optional[float]
    pruefung_versuch: Optional[int]
    pruefung_letzter_versuch: Optional[bool]

@dataclass(frozen=True)
class GesamtFortschrittDTO:
    student_id: int
    student_name: str
    ects_bestanden: int
    ects_gesamt_bekannt: int
    notenschnitt: Optional[float]
    anzahl_bearbeitungen_offen: int
    anzahl_bearbeitungen_abgeschlossen: int
    kurse: list[KursFortschrittDTO]
    bearbeitungen: list[BearbeitungFortschrittDTO]


# ---------------- Service ----------------

class FortschrittService:
    def __init__(
        self,
        student_repo: StudentRepository,
        bearbeitung_repo: BearbeitungRepository,
        kurs_repo: KursRepository,
        pruefung_repo: PruefungRepository,
        einschreibung_repo: EinschreibungRepository,   # wichtig!
    ) -> None:
        self._students = student_repo
        self._bearb = bearbeitung_repo
        self._kurse = kurs_repo
        self._pruef = pruefung_repo
        self._einschreibungen = einschreibung_repo

    # ---- Onboarding: Student + (optional) Ziele anlegen ----
    def create_student(
        self,
        *,
        name: str,
        matrikelnummer: str,
        email: Optional[str] = None,
        uni_email: Optional[str] = None,
        ziel_notenschnitt: Optional[float] = None,
        ziel_enddatum: Optional[date] = None,
        start_datum: Optional[date] = None,
    ) -> int:
        """
        Legt einen Studenten an (idempotent per Matrikelnummer, siehe Repo) und legt
        optional eine aktive Einschreibung mit Zielen an, falls ziel_* übergeben wurden.
        """
        s = Student(id=0, name=name, matrikelnummer=matrikelnummer, email=email, uni_email=uni_email)
        student_id = self._students.create(s)  # dein create() macht Upsert per matrikelnummer

        if ziel_notenschnitt is not None and ziel_enddatum is not None:
            e = Einschreibung(
                student=s,
                studiengang=None,                      # später verknüpfbar
                start_datum=start_datum or date.today(),
                ziel_enddatum=ziel_enddatum,
                ziel_notenschnitt=ziel_notenschnitt,
                status=StatusEinschreibung.AKTIV,
            )
            self._einschreibungen.create(e)

        return student_id

    # ---- Fachliche Auswertungen ----
    def lade_student(self, student_id: int) -> Student:
        st = self._students.get_by_id(student_id)
        if st is None:
            raise ValueError(f"Student mit ID {student_id} nicht gefunden.")
        return st

    def berechne_notenschnitt(self, student_id: int) -> Optional[float]:
        noten: list[float] = []
        for b in self._bearb.all_for_student(student_id):
            p = self._pruefung_fuer_bearbeitung(b.id)
            if p and p.note is not None:
                noten.append(p.note)
        return _mean_or_none(noten)

    def ects_summe_bestanden(self, student_id: int) -> int:
        total = 0
        for b in self._bearb.all_for_student(student_id):
            if self._ist_bearbeitung_bestanden(b):
                total += self._kurs(b.kurs_id).ects
        return total

    def gesamtuebersicht(self, student_id: int) -> GesamtFortschrittDTO:
        student = self.lade_student(student_id)
        bearbeitungen = list(self._bearb.all_for_student(student_id))

        kurse_dtos = self._build_kurs_dtos(bearbeitungen)
        bearb_dtos = self._build_bearbeitung_dtos(bearbeitungen)

        ects_gesamt_bekannt = sum(self._kurs(b.kurs_id).ects for b in bearbeitungen)
        ects_bestanden = self.ects_summe_bestanden(student_id)
        abgeschlossen = sum(1 for b in bearbeitungen if b.status == StatusBearbeitung.ABGESCHLOSSEN)
        offen = len(bearbeitungen) - abgeschlossen

        noten_gen = (
            p.note
            for b in bearbeitungen
            if (p := self._pruefung_fuer_bearbeitung(b.id)) is not None and p.note is not None
        )
        schnitt = _mean_or_none(noten_gen)

        return GesamtFortschrittDTO(
            student_id=student.id,
            student_name=getattr(student, "name", f"Student #{student.id}"),
            ects_bestanden=ects_bestanden,
            ects_gesamt_bekannt=ects_gesamt_bekannt,
            notenschnitt=schnitt,
            anzahl_bearbeitungen_offen=offen,
            anzahl_bearbeitungen_abgeschlossen=abgeschlossen,
            kurse=kurse_dtos,
            bearbeitungen=bearb_dtos,
        )

    def trage_note_ein(self, bearbeitung_id: int, note: float) -> Pruefung:
        b = self._bearbeitung(bearbeitung_id)
        p = self._pruefung_fuer_bearbeitung(bearbeitung_id)
        if p is None:
            from models.pruefung import Pruefung, Pruefungsform
            p = Pruefung(id=0, bearbeitung=b, pruefungsform=Pruefungsform.KLAUSUR)
            p.id = self._pruef.create(p)
        p.note_eintragen(note)
        self._pruef.update(p)
        return p

    # ---- Helpers ----
    def _kurs(self, kurs_id: int) -> Kurs:
        k = self._kurse.get_by_id(kurs_id)
        if k is None:
            raise ValueError(f"Kurs mit ID {kurs_id} nicht gefunden.")
        return k

    def _bearbeitung(self, bearbeitung_id: int) -> Bearbeitung:
        b = self._bearb.get_by_id(bearbeitung_id)
        if b is None:
            raise ValueError(f"Bearbeitung mit ID {bearbeitung_id} nicht gefunden.")
        return b

    def _pruefung_fuer_bearbeitung(self, bearbeitung_id: int) -> Optional[Pruefung]:
        if not hasattr(self._pruef, "get_by_bearbeitung_id"):
            raise AttributeError("PruefungRepository benötigt get_by_bearbeitung_id(bearbeitung_id:int).")
        return self._pruef.get_by_bearbeitung_id(bearbeitung_id)  # type: ignore[attr-defined]

    def _ist_bearbeitung_bestanden(self, b: Bearbeitung) -> bool:
        p = self._pruefung_fuer_bearbeitung(b.id)
        if p is not None and p.bestanden is not None:
            return bool(p.bestanden)
        return b.status == StatusBearbeitung.ABGESCHLOSSEN

    def _build_kurs_dtos(self, bearbeitungen: list[Bearbeitung]) -> list[KursFortschrittDTO]:
        result: list[KursFortschrittDTO] = []
        for b in bearbeitungen:
            kurs = self._kurs(b.kurs_id)
            p = self._pruefung_fuer_bearbeitung(b.id)
            result.append(
                KursFortschrittDTO(
                    kurs_id=b.kurs_id,
                    kurs_name=kurs.name,
                    ects=kurs.ects,
                    bestanden=None if p is None else p.bestanden,
                    note=None if p is None else p.note,
                    versuch_nr=None if p is None else p.versuch_nr,
                    letzter_versuch=None if p is None else p.letzter_versuch,
                )
            )
        return result

    def _build_bearbeitung_dtos(self, bearbeitungen: list[Bearbeitung]) -> list[BearbeitungFortschrittDTO]:
        result: list[BearbeitungFortschrittDTO] = []
        for b in bearbeitungen:
            p = self._pruefung_fuer_bearbeitung(b.id)
            result.append(
                BearbeitungFortschrittDTO(
                    bearbeitung_id=b.id,
                    kurs_id=b.kurs_id,
                    status=b.status,
                    thema=getattr(b, "thema", None),
                    tage_bearbeitung=_tage_zwischen(b.start_datum, b.abgabe_datum),
                    pruefung_bestehen=None if p is None else p.bestanden,
                    pruefung_note=None if p is None else p.note,
                    pruefung_versuch=None if p is None else p.versuch_nr,
                    pruefung_letzter_versuch=None if p is None else p.letzter_versuch,
                )
            )
        return result
