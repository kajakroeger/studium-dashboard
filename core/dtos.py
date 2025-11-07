"""
core/dtos.py
Gemeinsame Datenklassen/DTOs, die von mehreren Services genutzt werden.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional
from models.bearbeitung import StatusBearbeitung



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

@dataclass
class StudienzieleDTO:
    ziel_notenschnitt: Optional[float]
    ziel_enddatum: Optional[date]
    aktueller_notenschnitt: Optional[float]
    heutiges_datum: date

@dataclass
class ZielStatusDTO:
    # Noten-Ziel
    notenziel_erreicht: Optional[bool]
    verbleibende_pruefungen: int
    erforderlicher_rest_schnitt: Optional[float]  # benötigter Schnitt für die restlichen Prüfungen
    kommentar_note: str

    # Zeit-Ziel
    prognose_abschluss: Optional[date]
    kommentar_zeit: str
